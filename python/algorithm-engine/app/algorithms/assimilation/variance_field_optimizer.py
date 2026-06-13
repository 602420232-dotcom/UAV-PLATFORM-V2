"""方差场优化器算法。

迭代优化背景误差方差场，使用观测增量统计（Desroziers 诊断）。
通过迭代调整 B 矩阵的缩放因子，使得背景误差方差与观测增量统计一致。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class VarianceFieldOptimizer:
    """方差场优化器。

    基于 Desroziers 诊断方法迭代优化背景误差方差场。
    在每次迭代中：
    1. 使用当前方差场执行同化分析
    2. 计算观测增量（观测减背景）的统计量
    3. 根据统计量调整方差场的缩放因子
    4. 使用松弛因子平滑更新

    参数:
        max_iterations: 最大迭代次数（默认 5）
        relaxation_factor: 松弛因子，控制更新步长（默认 0.3）
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.max_iterations: int = self.config.get("max_iterations", 5)
        self.relaxation_factor: float = self.config.get("relaxation_factor", 0.3)
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10, 5))
        self.ensemble_size: int = self.config.get("ensemble_size", 30)
        self.background_error_scale: float = self.config.get("background_error_scale", 1.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)
        self.sigma_b: float = self.config.get("sigma_b", 1.0)
        self.max_var_iterations: int = self.config.get("max_var_iterations", 50)

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行方差场优化同化。

        Args:
            params: 包含以下键的字典：
                - background_field: 背景场（numpy array）
                - observations: 观测列表，每个元素为含 position/value 的字典

        Returns:
            包含 analysis_field（分析场列表格式）及方差场优化诊断信息的字典。
        """
        background = np.asarray(params.get("background_field", np.zeros(self.grid_shape)))
        observations = params.get("observations", [])

        if background.ndim == 0:
            background = background.reshape(1)

        shape = background.shape
        n = background.size
        xb = background.flatten()

        # 构建观测算子
        y_obs, H = self._build_observation_operator(xb, observations, shape)  # noqa: N806
        m = len(y_obs)

        logger.info(
            "开始方差场优化，网格大小: %s，最大迭代: %d，松弛因子: %.2f",
            shape,
            self.max_iterations,
            self.relaxation_factor,
        )

        # ---- 初始化方差场（均匀方差）----
        variance_field = np.ones(n) * self.sigma_b**2

        # ---- 迭代优化方差场 ----
        scale_history = []
        x_analysis = xb.copy()

        for iteration in range(self.max_iterations):
            sigma_b_current = np.sqrt(variance_field)

            # 使用当前方差场执行同化
            x_analysis = self._run_analysis_with_variance(xb, H, y_obs, sigma_b_current, m)

            # 计算 Desroziers 诊断统计量
            Hxb = H @ xb  # noqa: N806
            Hxa = H @ x_analysis  # noqa: N806
            innovation = y_obs - Hxb  # d = y - H(xb)
            analysis_increment = Hxa - Hxb  # H(xa) - H(xb)

            # Desroziers 诊断：E[d^2] ≈ sigma_b^2 + R，E[d * incr] ≈ sigma_b^2
            innovation_var = float(np.mean(innovation**2))
            cross_term = float(np.mean(innovation * analysis_increment))

            # 计算缩放因子
            if cross_term > 1e-10:
                current_scale = cross_term / (self.sigma_b**2)
            else:
                current_scale = 1.0

            scale_history.append(current_scale)

            # 使用松弛因子更新方差场
            new_variance = variance_field * (1.0 + self.relaxation_factor * (current_scale - 1.0))
            # 确保方差非负
            new_variance = np.maximum(new_variance, 1e-6)
            variance_field = new_variance

            logger.info(
                "迭代 %d/%d：缩放因子=%.4f，创新方差=%.4f，交叉项=%.4f",
                iteration + 1,
                self.max_iterations,
                current_scale,
                innovation_var,
                cross_term,
            )

        analysis = x_analysis.reshape(shape)

        logger.info("方差场优化完成，最终缩放因子: %.4f", scale_history[-1] if scale_history else 1.0)

        return {
            "analysis_field": analysis.tolist(),
            "scale_history": scale_history,
            "final_scale": scale_history[-1] if scale_history else 1.0,
            "max_iterations": self.max_iterations,
            "relaxation_factor": self.relaxation_factor,
            "grid_shape": list(shape),
            "num_observations": m,
        }

    def _run_analysis_with_variance(self, xb, H, y_obs, sigma_b_field, m):  # noqa: N803, N806
        """使用给定的方差场运行变分分析。"""
        x = xb.copy()
        lr = 0.01
        for _ in range(self.max_var_iterations):
            dx = x - xb
            # 使用逐点方差而非均匀方差
            grad_b = dx / (sigma_b_field**2)
            Hx = H @ x  # noqa: N806
            dy = Hx - y_obs
            grad_o = H.T @ (dy / self.observation_error_scale**2)
            grad = grad_b + grad_o
            x = x - lr * grad
        return x

    def _build_observation_operator(self, xb, observations, shape):  # noqa: N806
        """构建观测算子矩阵 H 和观测向量 y。"""
        n = len(xb)
        m = len(observations)
        y_obs = np.zeros(m)
        H = np.zeros((m, n))  # noqa: N806
        for j, obs in enumerate(observations):
            pos = obs.get("position", [0] * len(shape))
            y_obs[j] = obs.get("value", 0.0)
            idx = 0
            stride = 1
            for i in range(len(shape) - 1, -1, -1):
                idx += int(pos[i]) * stride
                stride *= shape[i]
            if 0 <= idx < n:
                H[j, idx] = 1.0
        return y_obs, H
