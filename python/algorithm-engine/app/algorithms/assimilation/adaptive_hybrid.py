"""自适应混合同化算法。

根据观测密度动态调整 3D-VAR 和 EnKF 的权重：
- 观测密集区域偏向 EnKF（利用集合流依赖信息）
- 观测稀疏区域偏向 3D-VAR（利用静态背景误差协方差）
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class AdaptiveHybridAssimilation:
    """自适应混合同化算法。

    根据每个网格点周围的观测密度，动态调整 3D-VAR 与 EnKF 的混合权重。
    观测密集时赋予 EnKF 更高权重，观测稀疏时赋予 3D-VAR 更高权重。

    参数:
        weight_threshold: 权重阈值，用于判断密度高低（默认 0.5）
        density_radius: 计算观测密度时的搜索半径（网格单位，默认 5）
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.weight_threshold: float = self.config.get("weight_threshold", 0.5)
        self.density_radius: int = self.config.get("density_radius", 5)
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10, 5))
        self.ensemble_size: int = self.config.get("ensemble_size", 30)
        self.background_error_scale: float = self.config.get("background_error_scale", 1.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)
        self.sigma_b: float = self.config.get("sigma_b", 1.0)
        self.max_iterations: int = self.config.get("max_iterations", 50)

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行自适应混合同化。

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

        xb = background.flatten()
        shape = background.shape

        logger.info("开始自适应混合同化，网格大小: %s，观测数量: %d", shape, len(observations))

        # 构建观测算子
        y_obs, H = self._build_observation_operator(xb, observations, shape)  # noqa: N806
        m = len(y_obs)

        # ---- 3D-VAR 分析 ----
        x_3dvar = self._run_3dvar(xb, H, y_obs)

        # ---- EnKF 分析 ----
        x_enkf = self._run_enkf(xb, H, y_obs, m)

        # ---- 计算每个网格点的观测密度 ----
        density_map = self._compute_observation_density(observations, shape)

        # ---- 归一化密度到 [0, 1] ----
        max_density = density_map.max()
        if max_density > 0:
            density_map = density_map / max_density

        # ---- 根据密度计算 EnKF 权重（密度高 -> EnKF 权重大）----
        enkf_weight_flat = density_map.flatten()
        var_weight_flat = 1.0 - enkf_weight_flat

        # ---- 混合分析场 ----
        x_analysis = enkf_weight_flat * x_enkf + var_weight_flat * x_3dvar

        analysis = x_analysis.reshape(shape)

        # 诊断统计
        avg_enkf_weight = float(enkf_weight_flat.mean())
        avg_var_weight = float(var_weight_flat.mean())

        logger.info(
            "自适应混合同化完成，平均 EnKF 权重: %.3f，平均 3D-VAR 权重: %.3f",
            avg_enkf_weight,
            avg_var_weight,
        )

        return {
            "analysis_field": analysis.tolist(),
            "avg_enkf_weight": avg_enkf_weight,
            "avg_var_weight": avg_var_weight,
            "weight_threshold": self.weight_threshold,
            "density_radius": self.density_radius,
            "grid_shape": list(shape),
            "num_observations": m,
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

    def _compute_observation_density(self, observations, shape):
        """计算每个网格点的观测密度。

        对于每个网格点，统计在其 density_radius 范围内的观测数量。
        """
        density = np.zeros(shape)
        obs_positions = []
        for obs in observations:
            pos = obs.get("position", [0] * len(shape))
            obs_positions.append(np.array(pos))

        if len(obs_positions) == 0:
            return density

        obs_arr = np.array(obs_positions)

        # 遍历所有网格点
        it = np.nditer(density, flags=["multi_index"])
        while not it.finished:
            idx = np.array(it.multi_index, dtype=float)
            distances = np.sqrt(np.sum((obs_arr - idx) ** 2, axis=1))
            count = np.sum(distances <= self.density_radius)
            it[0] = count
            it.iternext()

        logger.debug("观测密度计算完成，最大密度: %.1f", density.max())
        return density

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
