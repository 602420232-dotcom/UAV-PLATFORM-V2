"""兼容同化器算法。

确保分析场与背景场的差异在合理范围内（兼容性约束）：
- 在标准同化结果基础上施加兼容性修正
- 限制分析增量的大小，防止过度拟合观测
- 通过兼容性权重在分析场和背景场之间进行平衡
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class CompatibleAssimilator:
    """兼容同化器。

    先执行标准同化分析，然后对分析增量施加兼容性约束：
    1. 计算分析增量 d = xa - xb
    2. 如果增量超过阈值，进行截断/缩放
    3. 使用兼容性权重在原始分析场和修正后分析场之间平衡

    参数:
        max_analysis_increment: 最大允许分析增量（默认 3.0）
        compatibility_weight: 兼容性修正的权重（默认 0.7）
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.max_analysis_increment: float = self.config.get("max_analysis_increment", 3.0)
        self.compatibility_weight: float = self.config.get("compatibility_weight", 0.7)
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10, 5))
        self.ensemble_size: int = self.config.get("ensemble_size", 30)
        self.background_error_scale: float = self.config.get("background_error_scale", 1.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)
        self.sigma_b: float = self.config.get("sigma_b", 1.0)
        self.max_iterations: int = self.config.get("max_iterations", 50)

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行兼容同化。

        Args:
            params: 包含以下键的字典：
                - background_field: 背景场（numpy array）
                - observations: 观测列表，每个元素为含 position/value 的字典

        Returns:
            包含 analysis_field（分析场列表格式）及兼容性诊断信息的字典。
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
            "开始兼容同化，网格大小: %s，最大增量: %.2f，兼容性权重: %.2f",
            shape,
            self.max_analysis_increment,
            self.compatibility_weight,
        )

        # ---- 第一步：执行标准 EnKF 同化 ----
        x_enkf = self._run_enkf(xb, H, y_obs, m)

        # ---- 第二步：计算分析增量 ----
        increment = x_enkf - xb
        raw_max_increment = float(np.max(np.abs(increment)))
        raw_mean_increment = float(np.mean(np.abs(increment)))

        logger.info(
            "原始分析增量 - 最大值: %.4f，平均值: %.4f",
            raw_max_increment,
            raw_mean_increment,
        )

        # ---- 第三步：施加兼容性约束 ----
        constrained_increment = self._apply_compatibility_constraint(increment)

        constrained_max_increment = float(np.max(np.abs(constrained_increment)))
        constrained_mean_increment = float(np.mean(np.abs(constrained_increment)))

        logger.info(
            "约束后分析增量 - 最大值: %.4f，平均值: %.4f",
            constrained_max_increment,
            constrained_mean_increment,
        )

        # ---- 第四步：混合原始分析和约束后分析 ----
        # fmt: off
        x_compatible = (
            self.compatibility_weight * (xb + constrained_increment)
            + (1.0 - self.compatibility_weight) * x_enkf
        )
        # fmt: on

        analysis = x_compatible.reshape(shape)

        # 诊断统计
        num_clipped = int(np.sum(np.abs(increment) > self.max_analysis_increment))
        clip_ratio = num_clipped / max(n, 1)

        logger.info(
            "兼容同化完成，截断点数: %d/%d（%.1f%%）",
            num_clipped,
            n,
            clip_ratio * 100,
        )

        return {
            "analysis_field": analysis.tolist(),
            "raw_max_increment": raw_max_increment,
            "raw_mean_increment": raw_mean_increment,
            "constrained_max_increment": constrained_max_increment,
            "constrained_mean_increment": constrained_mean_increment,
            "num_clipped_points": num_clipped,
            "clip_ratio": float(clip_ratio),
            "max_analysis_increment": self.max_analysis_increment,
            "compatibility_weight": self.compatibility_weight,
            "grid_shape": list(shape),
            "num_observations": m,
        }

    def _apply_compatibility_constraint(self, increment):
        """施加兼容性约束，限制分析增量的大小。

        使用 tanh 函数平滑截断，避免硬截断导致的梯度不连续。
        """
        max_inc = self.max_analysis_increment

        # 使用 tanh 平滑截断
        # 当 |d| < max_inc 时，基本保持不变
        # 当 |d| > max_inc 时，平滑衰减到 max_inc
        abs_inc = np.abs(increment)
        scale = np.where(
            abs_inc <= max_inc,
            1.0,
            max_inc / abs_inc * np.tanh(abs_inc / max_inc),
        )

        constrained = increment * scale

        logger.debug(
            "兼容性约束：原始增量范围 [%.4f, %.4f]，约束后范围 [%.4f, %.4f]",
            float(increment.min()),
            float(increment.max()),
            float(constrained.min()),
            float(constrained.max()),
        )

        return constrained

    def _run_enkf(self, xb, H, y_obs, m):  # noqa: N803, N806
        """运行 EnKF 集合卡尔曼滤波分析。"""
        np.random.seed(42)
        n_ens = self.ensemble_size
        n = len(xb)

        perturbation = np.random.randn(n_ens, n) * self.background_error_scale
        ensemble = xb[np.newaxis, :] + perturbation

        obs_perturbation = np.random.randn(n_ens, m) * self.observation_error_scale
        obs_ensemble = y_obs[np.newaxis, :] + obs_perturbation

        x_mean = ensemble.mean(axis=0)
        X_pert = ensemble - x_mean[np.newaxis, :]  # noqa: N806

        HX = H @ X_pert.T  # noqa: N806
        HPHT = (HX @ HX.T) / (n_ens - 1)  # noqa: N806
        R = np.eye(m) * self.observation_error_scale**2  # noqa: N806
        HPHT_plus_R = HPHT + R  # noqa: N806

        try:
            K = (X_pert.T @ HX.T) @ np.linalg.inv(HPHT_plus_R) / (n_ens - 1)  # noqa: N806
        except np.linalg.LinAlgError:
            K = np.zeros((n, m))  # noqa: N806

        for i in range(n_ens):
            innovation = obs_ensemble[i] - H @ ensemble[i]
            ensemble[i] = ensemble[i] + K @ innovation

        return ensemble.mean(axis=0)

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
