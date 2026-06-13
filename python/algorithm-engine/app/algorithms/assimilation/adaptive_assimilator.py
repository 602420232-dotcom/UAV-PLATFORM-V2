"""自适应同化器算法。

根据背景误差和观测误差的相对大小自动选择最优同化策略：
- 当背景误差 > 观测误差时使用 EnKF（集合方法更适合大不确定性场景）
- 当背景误差 <= 观测误差时使用 3D-VAR（变分方法更适合小不确定性场景）
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class AdaptiveAssimilator:
    """自适应同化器。

    通过比较背景误差与观测误差的比值，自动选择 EnKF 或 3D-VAR 进行同化。
    当背景误差显著大于观测误差时，集合方法能更好地捕捉流依赖的不确定性；
    当观测误差较大时，变分方法提供的平滑分析更为稳健。

    参数:
        error_ratio_threshold: 背景误差与观测误差的比值阈值（默认 2.0）
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.error_ratio_threshold: float = self.config.get("error_ratio_threshold", 2.0)
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10, 5))
        self.ensemble_size: int = self.config.get("ensemble_size", 30)
        self.background_error_scale: float = self.config.get("background_error_scale", 1.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)
        self.sigma_b: float = self.config.get("sigma_b", 1.0)
        self.max_iterations: int = self.config.get("max_iterations", 50)

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行自适应同化。

        Args:
            params: 包含以下键的字典：
                - background_field: 背景场（numpy array）
                - observations: 观测列表，每个元素为含 position/value 的字典

        Returns:
            包含 analysis_field（分析场列表格式）及诊断信息的字典。
        """
        background = np.asarray(params.get("background_field", np.zeros(self.grid_shape)))
        observations = params.get("observations", [])

        if background.ndim == 0:
            background = background.reshape(1)

        shape = background.shape
        xb = background.flatten()

        # 构建观测算子
        y_obs, H = self._build_observation_operator(xb, observations, shape)  # noqa: N806
        m = len(y_obs)

        # ---- 估计背景误差和观测误差 ----
        bg_error_estimate = self._estimate_background_error(background, observations)
        obs_error_estimate = self.observation_error_scale

        error_ratio = bg_error_estimate / max(obs_error_estimate, 1e-10)

        logger.info(
            "背景误差估计: %.4f，观测误差: %.4f，比值: %.2f，阈值: %.2f",
            bg_error_estimate,
            obs_error_estimate,
            error_ratio,
            self.error_ratio_threshold,
        )

        # ---- 根据误差比值选择算法 ----
        if error_ratio > self.error_ratio_threshold:
            algorithm_chosen = "EnKF"
            x_analysis = self._run_enkf(xb, H, y_obs, m)
            logger.info("选择 EnKF 算法（背景误差显著大于观测误差）")
        else:
            algorithm_chosen = "3D-VAR"
            x_analysis = self._run_3dvar(xb, H, y_obs)
            logger.info("选择 3D-VAR 算法（背景误差与观测误差相当或更小）")

        analysis = x_analysis.reshape(shape)

        return {
            "analysis_field": analysis.tolist(),
            "algorithm_chosen": algorithm_chosen,
            "error_ratio": float(error_ratio),
            "error_ratio_threshold": self.error_ratio_threshold,
            "background_error_estimate": float(bg_error_estimate),
            "observation_error_estimate": float(obs_error_estimate),
            "grid_shape": list(shape),
            "num_observations": m,
        }

    def _estimate_background_error(self, background, observations):
        """估计背景误差大小。

        使用背景场的局部梯度方差作为背景误差的度量。
        如果没有观测，则使用背景场的全局标准差。
        """
        if len(observations) == 0:
            return float(np.std(background))

        # 计算背景场在观测点处的值与观测值的差异
        shape = background.shape
        diffs = []
        for obs in observations:
            pos = obs.get("position", [0] * len(shape))
            idx = 0
            stride = 1
            for i in range(len(shape) - 1, -1, -1):
                idx += int(pos[i]) * stride
                stride *= shape[i]
            if 0 <= idx < background.size:
                bg_val = background.flatten()[idx]
                obs_val = obs.get("value", 0.0)
                diffs.append(abs(bg_val - obs_val))

        if len(diffs) == 0:
            return float(np.std(background))

        return float(np.mean(diffs))

    def _run_3dvar(self, xb, H, y_obs):  # noqa: N803, N806
        """运行 3D-VAR 变分分析。"""
        x = xb.copy()
        lr = 0.01
        for _ in range(self.max_iterations):
            dx = x - xb
            grad_b = dx / (self.sigma_b ** 2)
            Hx = H @ x  # noqa: N806
            dy = Hx - y_obs
            grad_o = H.T @ (dy / self.observation_error_scale ** 2)
            grad = grad_b + grad_o
            x = x - lr * grad
        return x

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
        R = np.eye(m) * self.observation_error_scale ** 2  # noqa: N806
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
