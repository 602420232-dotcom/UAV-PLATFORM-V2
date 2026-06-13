"""多尺度混合同化算法。

在不同空间分辨率上分别执行同化，然后融合结果：
- 粗网格使用 3D-VAR（捕获大尺度特征）
- 细网格使用 EnKF（捕获小尺度细节）
- 最后将粗网格分析场上采样与细网格分析场加权融合
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
from scipy.ndimage import zoom

logger = logging.getLogger(__name__)


class MultiScaleHybridAssimilation:
    """多尺度混合同化算法。

    在粗分辨率网格上执行 3D-VAR 同化获取大尺度分析，
    在原始细分辨率网格上执行 EnKF 同化获取小尺度分析，
    最后将两者融合得到最终分析场。

    参数:
        coarse_factor: 粗网格降采样因子（默认 4）
        fusion_weight: 细网格（EnKF）分析场的融合权重（默认 0.6）
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.coarse_factor: int = self.config.get("coarse_factor", 4)
        self.fusion_weight: float = self.config.get("fusion_weight", 0.6)
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10, 5))
        self.ensemble_size: int = self.config.get("ensemble_size", 30)
        self.background_error_scale: float = self.config.get("background_error_scale", 1.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)
        self.sigma_b: float = self.config.get("sigma_b", 1.0)
        self.max_iterations: int = self.config.get("max_iterations", 50)

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行多尺度混合同化。

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
        logger.info(
            "开始多尺度混合同化，网格大小: %s，粗化因子: %d，融合权重: %.2f",
            shape,
            self.coarse_factor,
            self.fusion_weight,
        )

        # ---- 细网格 EnKF 同化 ----
        xb_fine = background.flatten()
        y_obs_fine, H_fine = self._build_observation_operator(  # noqa: N806
            xb_fine, observations, shape
        )
        x_enkf_fine = self._run_enkf(xb_fine, H_fine, y_obs_fine, len(y_obs_fine))
        enkf_field = x_enkf_fine.reshape(shape)

        # ---- 粗网格 3D-VAR 同化 ----
        coarse_shape = self._compute_coarse_shape(shape)
        background_coarse = self._downsample(background, coarse_shape)
        xb_coarse = np.asarray(background_coarse).flatten()

        # 将观测映射到粗网格
        obs_coarse = self._map_observations_to_coarse(observations, shape, coarse_shape)
        y_obs_coarse, H_coarse = self._build_observation_operator(  # noqa: N806
            xb_coarse, obs_coarse, coarse_shape
        )
        x_3dvar_coarse = self._run_3dvar(xb_coarse, H_coarse, y_obs_coarse)
        var_field_coarse = x_3dvar_coarse.reshape(coarse_shape)

        # ---- 上采样粗网格分析场到原始分辨率 ----
        var_field_upsampled = self._upsample(var_field_coarse, shape)

        # ---- 融合 ----
        var_weight = 1.0 - self.fusion_weight
        analysis = self.fusion_weight * enkf_field + var_weight * var_field_upsampled

        logger.info("多尺度混合同化完成，粗网格形状: %s", list(coarse_shape))

        return {
            "analysis_field": analysis.tolist(),
            "coarse_shape": list(coarse_shape),
            "coarse_factor": self.coarse_factor,
            "fusion_weight": self.fusion_weight,
            "grid_shape": list(shape),
            "num_observations": len(observations),
        }

    def _run_3dvar(self, xb, H, y_obs):  # noqa: N803, N806
        """运行 3D-VAR 变分分析。"""
        x = xb.copy()
        lr = 0.01
        for _ in range(self.max_iterations):
            dx = x - xb
            grad_b = dx / (self.sigma_b ** 2)
            Hx = H @ x  # noqa: N803, N806
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

    def _compute_coarse_shape(self, shape):
        """计算粗网格形状。"""
        coarse_shape = []
        for dim in shape:
            coarse_dim = max(1, dim // self.coarse_factor)
            coarse_shape.append(coarse_dim)
        return tuple(coarse_shape)

    def _downsample(self, field, target_shape):
        """将场降采样到目标形状（均值池化）。"""
        zoom_factors = [t / s for t, s in zip(target_shape, field.shape)]
        return zoom(field, zoom_factors, order=1)

    def _upsample(self, field, target_shape):
        """将场上采样到目标形状（双线性插值）。"""
        zoom_factors = [t / s for t, s in zip(target_shape, field.shape)]
        return zoom(field, zoom_factors, order=1)

    def _map_observations_to_coarse(self, observations, fine_shape, coarse_shape):
        """将观测位置从细网格映射到粗网格。"""
        obs_coarse = []
        for obs in observations:
            pos = obs.get("position", [0] * len(fine_shape))
            coarse_pos = [int(p // self.coarse_factor) for p in pos]
            # 确保位置在粗网格范围内
            for i in range(len(coarse_pos)):
                coarse_pos[i] = min(coarse_pos[i], coarse_shape[i] - 1)
                coarse_pos[i] = max(coarse_pos[i], 0)
            obs_coarse.append({"position": coarse_pos, "value": obs.get("value", 0.0)})
        return obs_coarse

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
