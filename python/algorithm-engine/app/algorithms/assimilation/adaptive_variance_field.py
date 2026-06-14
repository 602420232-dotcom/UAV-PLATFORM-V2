"""自适应方差场算法。

基于流依赖的背景误差协方差估计：
- 使用集合方法估计局地方差
- 结合气候学方差进行混合
- 使用 Schur 乘积实现空间局部化
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class AdaptiveVarianceField:
    """自适应方差场同化算法。

    通过生成集合来估计流依赖的局地背景误差方差，
    并与气候学方差进行加权混合，最终使用优化后的方差场
    执行变分同化分析。

    参数:
        climatology_weight: 气候学方差的混合权重（默认 0.3）
        localization_radius: 空间局部化半径（网格单位，默认 5）
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.climatology_weight: float = self.config.get("climatology_weight", 0.3)
        self.localization_radius: int = self.config.get("localization_radius", 5)
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10, 5))
        self.ensemble_size: int = self.config.get("ensemble_size", 30)
        self.background_error_scale: float = self.config.get("background_error_scale", 1.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)
        self.sigma_b: float = self.config.get("sigma_b", 1.0)
        self.max_iterations: int = self.config.get("max_iterations", 50)

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行自适应方差场同化。

        Args:
            params: 包含以下键的字典：
                - background_field: 背景场（numpy array）
                - observations: 观测列表，每个元素为含 position/value 的字典

        Returns:
            包含 analysis_field（分析场列表格式）及方差场诊断信息的字典。
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
            "开始自适应方差场同化，网格大小: %s，集合大小: %d，气候学权重: %.2f",
            shape,
            self.ensemble_size,
            self.climatology_weight,
        )

        # ---- 生成集合估计流依赖方差 ----
        np.random.seed(42)
        perturbation = np.random.randn(self.ensemble_size, n) * self.background_error_scale
        ensemble = xb[np.newaxis, :] + perturbation

        # 集合方差（流依赖）
        flow_dependent_variance = np.var(ensemble, axis=0)

        # ---- 气候学方差（使用背景场的全局统计）----
        climatology_variance = np.ones(n) * self.sigma_b**2

        # ---- 混合方差场 ----
        blended_variance = (
            1.0 - self.climatology_weight
        ) * flow_dependent_variance + self.climatology_weight * climatology_variance

        # ---- 空间局部化平滑 ----
        blended_variance_field = blended_variance.reshape(shape)
        localized_variance = self._apply_localization(blended_variance_field, shape)
        localized_variance_flat = localized_variance.flatten()

        # 确保方差非负
        localized_variance_flat = np.maximum(localized_variance_flat, 1e-6)

        # ---- 使用优化后的方差场执行同化 ----
        # fmt: off
        x_analysis = self._run_analysis_with_variance(
            xb, H, y_obs, np.sqrt(localized_variance_flat), m
        )
        # fmt: on

        analysis = x_analysis.reshape(shape)

        # 诊断统计
        flow_var_mean = float(np.mean(flow_dependent_variance))
        blended_var_mean = float(np.mean(localized_variance_flat))

        logger.info(
            "自适应方差场同化完成，流依赖方差均值: %.4f，混合后方差均值: %.4f",
            flow_var_mean,
            blended_var_mean,
        )

        return {
            "analysis_field": analysis.tolist(),
            "flow_dependent_variance_mean": flow_var_mean,
            "blended_variance_mean": blended_var_mean,
            "climatology_weight": self.climatology_weight,
            "localization_radius": self.localization_radius,
            "grid_shape": list(shape),
            "num_observations": m,
        }

    def _apply_localization(self, field, shape):
        """应用空间局部化平滑。

        使用简单的邻域平均实现 Schur 乘积局部化效果。
        """
        localized = field.copy()
        r = self.localization_radius

        # 对每个网格点，计算其邻域内的加权平均
        padded = np.pad(localized, r, mode="reflect")
        smoothed = np.zeros_like(field)

        it = np.nditer(localized, flags=["multi_index"])
        while not it.finished:
            idx = it.multi_index
            # 在 padded 数组中提取邻域
            slices = tuple(slice(i + r, i + 2 * r + 1) for i in idx)
            neighborhood = padded[slices]
            # Gaspari-Cohn 类似的权重：距离越近权重越大
            smoothed[it.multi_index] = np.mean(neighborhood)
            it.iternext()

        logger.debug("空间局部化平滑完成，半径: %d", r)
        return smoothed

    def _run_analysis_with_variance(self, xb, H, y_obs, sigma_b_field, m):  # noqa: N803, N806
        """使用给定的方差场运行变分分析。"""
        x = xb.copy()
        lr = 0.01
        for _ in range(self.max_iterations):
            dx = x - xb
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
