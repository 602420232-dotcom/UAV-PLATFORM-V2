"""Particle Filter (粒子滤波) 数据同化算法.

粒子滤波是一种序贯蒙特卡洛方法，适用于非高斯、非线性
系统的数据同化。通过加权粒子（样本）近似后验概率分布。

算法原理:
  预测步（Predict）:
    x_k^(i) = M(x_{k-1}^(i)),  i = 1, ..., N_p
    p(x_k | y_{1:k-1}) = sum_i w_{k-1}^(i) delta(x_k - x_k^(i))

  更新步（Update）:
    w_k^(i) = w_{k-1}^(i) * p(y_k | x_k^(i))
    w_k^(i) = w_k^(i) / sum_j w_k^(j)  (归一化)

  重采样（Resample）:
    当有效粒子数 N_eff < N_threshold 时执行重采样:
    - 系统重采样 (Systematic Resampling)
    - 残差重采样 (Residual Resampling)
    - 分层重采样 (Stratified Resampling)

  有效粒子数:
    N_eff = 1 / sum_i (w_i)^2

参考文献:
  van Leeuwen (2009), Ocean Dynamics, 59, 285-303
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ParticleFilter:
    """粒子滤波 (Particle Filter) 数据同化算法.

    特点:
    1. 适用于非高斯、非线性系统
    2. 通过重采样避免粒子退化
    3. 支持多种重采样方法
    4. 支持序贯蒙特卡洛方法
    5. 提供有效粒子数监控

    配置参数:
        n_particles: 粒子数
        resampling_method: 重采样方法
        resampling_threshold: 重采样阈值（有效粒子数比例）
        observation_error_scale: 观测误差标准差
        prior_inflation: 先验膨胀因子
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        # 网格配置
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10, 5))
        self.resolution: float = self.config.get("resolution", 50.0)

        # 粒子配置
        self.n_particles: int = self.config.get("n_particles", 100)
        self.background_error_scale: float = self.config.get("background_error_scale", 1.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)

        # 重采样配置
        self.resampling_method: str = self.config.get("resampling_method", "systematic")
        self.resampling_threshold: float = self.config.get("resampling_threshold", 0.5)

        # 先验膨胀
        self.prior_inflation: float = self.config.get("prior_inflation", 1.0)

        # 随机种子
        self.seed: int = self.config.get("seed", 42)

    # ================================================================
    # 公共接口
    # ================================================================

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行粒子滤波同化.

        Args:
            params: 分析参数字典，包含:
                - background_field: 背景场 (numpy.ndarray)
                - observations: 观测数据列表，每个元素包含:
                    - position: 观测位置
                    - value: 观测值
                    - error: 观测误差（可选）
                - n_particles: 粒子数（可选）
                - particles: 预报粒子集合（可选）

        Returns:
            包含分析场、粒子权重、有效粒子数等信息的字典
        """
        background = np.asarray(
            params.get("background_field", np.zeros(self.grid_shape)),
            dtype=float,
        )
        observations = params.get("observations", [])
        n_particles = params.get("n_particles", self.n_particles)

        n_state = background.size
        xb = background.flatten()

        # 初始化粒子
        particles, weights = self._initialize_particles(xb, n_particles, params)

        # 构建观测算子
        y_obs, H = self._build_observation_operator(  # noqa: N806
            xb, observations, background.shape
        )
        m = len(y_obs)

        # 构建观测误差协方差
        R = self._build_observation_error_matrix(observations, m)  # noqa: N806

        # 似然计算和权重更新
        particles, weights, n_eff = self._update_weights(
            particles, weights, y_obs, H, R
        )

        # 重采样
        resampled, n_resampled = self._resample_if_needed(
            particles, weights, n_eff, n_particles
        )

        # 计算分析结果（加权平均）
        analysis = np.average(resampled, weights=weights, axis=0)

        # 粒子统计
        particle_spread = float(np.std(resampled, axis=0).mean())
        weight_entropy = self._compute_weight_entropy(weights)

        # 诊断统计
        diagnostics = self._compute_diagnostics(
            xb, analysis, particles, resampled,
            observations, background.shape, y_obs, H,
            weights, n_eff
        )

        return {
            "analysis_field": analysis.reshape(background.shape).tolist(),
            "particle_spread": particle_spread,
            "n_particles": n_particles,
            "n_effective_particles": n_eff,
            "n_resampled": n_resampled,
            "weight_entropy": weight_entropy,
            "grid_shape": list(background.shape),
            "resampling_method": self.resampling_method,
            "diagnostics": diagnostics,
        }

    # ================================================================
    # 粒子初始化
    # ================================================================

    def _initialize_particles(
        self,
        xb: np.ndarray,
        n_particles: int,
        params: dict[str, Any],
    ) -> tuple[np.ndarray, np.ndarray]:
        """初始化粒子和权重.

        如果提供了预报粒子集合则使用预报粒子，
        否则围绕背景场生成高斯分布粒子。

        Returns:
            (particles, weights) - 粒子矩阵和权重向量
        """
        provided_particles = params.get("particles", None)
        if provided_particles is not None:
            particles = np.asarray(provided_particles, dtype=float)
            if particles.ndim == 1:
                particles = particles.reshape(1, -1)
            weights = np.ones(particles.shape[0]) / particles.shape[0]
            return particles, weights

        n_state = len(xb)
        np.random.seed(self.seed)
        particles = xb[np.newaxis, :] + np.random.randn(
            n_particles, n_state
        ) * self.background_error_scale
        weights = np.ones(n_particles) / n_particles
        return particles, weights

    # ================================================================
    # 权重更新
    # ================================================================

    def _update_weights(
        self,
        particles: np.ndarray,
        weights: np.ndarray,
        y_obs: np.ndarray,
        H: np.ndarray,  # noqa: N806
        R: np.ndarray,  # noqa: N806
    ) -> tuple[np.ndarray, np.ndarray, float]:
        """根据观测似然更新粒子权重.

        似然函数（高斯假设）:
        w_i = w_i * exp(-0.5 * (H x_i - y)^T R^{-1} (H x_i - y))

        Args:
            particles: 粒子矩阵 (n_particles x n_state)
            weights: 当前权重 (n_particles,)
            y_obs: 观测向量 (m,)
            H: 观测算子 (m x n_state)
            R: 观测误差协方差 (m x m)

        Returns:
            (particles, weights, n_eff)
        """
        n_particles = particles.shape[0]
        m = len(y_obs)

        if m == 0:
            return particles, weights, float(n_particles)

        # 计算观测误差协方差逆
        try:
            R_inv = np.linalg.inv(R)  # noqa: N806
        except np.linalg.LinAlgError:
            R_inv = np.linalg.pinv(R)  # noqa: N806

        # 计算每个粒子的似然
        log_likelihoods = np.zeros(n_particles)
        for i in range(n_particles):
            Hx = H @ particles[i]  # noqa: N806
            innovation = Hx - y_obs
            # 马氏距离的平方
            mahalanobis_sq = float(innovation @ R_inv @ innovation)
            log_likelihoods[i] = -0.5 * mahalanobis_sq

        # 对数空间更新权重（数值稳定）
        log_weights = np.log(np.maximum(weights, 1e-300)) + log_likelihoods

        # 归一化（对数求和技巧）
        max_log_w = np.max(log_weights)
        log_weights_shifted = log_weights - max_log_w
        weights = np.exp(log_weights_shifted)
        weights = weights / np.sum(weights)

        # 计算有效粒子数
        n_eff = float(1.0 / np.sum(weights ** 2))

        return particles, weights, n_eff

    # ================================================================
    # 重采样
    # ================================================================

    def _resample_if_needed(
        self,
        particles: np.ndarray,
        weights: np.ndarray,
        n_eff: float,
        n_particles: int,
    ) -> tuple[np.ndarray, int]:
        """根据有效粒子数决定是否重采样.

        当 N_eff < threshold * N_particles 时执行重采样。

        Returns:
            (resampled_particles, n_resampled)
        """
        threshold = self.resampling_threshold * n_particles

        if n_eff >= threshold:
            logger.info(
                "有效粒子数 %.1f >= 阈值 %d，无需重采样",
                n_eff, int(threshold),
            )
            return particles, 0

        logger.info(
            "有效粒子数 %.1f < 阈值 %d，执行%s重采样",
            n_eff, int(threshold), self.resampling_method,
        )

        method = self.resampling_method.lower()
        if method == "systematic":
            indices = self._systematic_resampling(weights, n_particles)
        elif method == "residual":
            indices = self._residual_resampling(weights, n_particles)
        elif method == "stratified":
            indices = self._stratified_resampling(weights, n_particles)
        else:
            indices = self._systematic_resampling(weights, n_particles)

        resampled = particles[indices].copy()

        # 重置权重为均匀分布
        return resampled, len(indices)

    def _systematic_resampling(
        self, weights: np.ndarray, n_particles: int
    ) -> list[int]:
        """系统重采样.

        生成均匀分布的随机偏移，按累积权重确定重采样索引。
        """
        np.random.seed(None)
        positions = (np.arange(n_particles) + np.random.uniform()) / n_particles

        cumulative_sum = np.cumsum(weights)
        cumulative_sum[-1] = 1.0  # 确保数值稳定

        indices: list[int] = []
        i = 0
        for j in range(n_particles):
            while positions[j] > cumulative_sum[i]:
                i += 1
            indices.append(i)

        return indices

    def _residual_resampling(
        self, weights: np.ndarray, n_particles: int
    ) -> list[int]:
        """残差重采样.

        先确定性地复制 floor(N * w_i) 次，再对剩余权重进行系统重采样。
        """
        np.random.seed(None)
        indices: list[int] = []

        # 确定性部分
        residuals = np.floor(weights * n_particles).astype(int)
        for i in range(n_particles):
            indices.extend([i] * int(residuals[i]))

        # 随机部分
        remaining = n_particles - len(indices)
        if remaining > 0:
            residual_weights = weights * n_particles - residuals
            residual_weights = residual_weights / np.sum(residual_weights)
            random_indices = self._systematic_resampling(residual_weights, remaining)
            indices.extend(random_indices)

        return indices[:n_particles]

    def _stratified_resampling(
        self, weights: np.ndarray, n_particles: int
    ) -> list[int]:
        """分层重采样.

        将[0,1]区间分为N层，每层独立采样。
        """
        np.random.seed(None)
        positions = (np.arange(n_particles) + np.random.uniform(size=n_particles)) / n_particles

        cumulative_sum = np.cumsum(weights)
        cumulative_sum[-1] = 1.0

        indices: list[int] = []
        i = 0
        for j in range(n_particles):
            while positions[j] > cumulative_sum[i]:
                i += 1
            indices.append(i)

        return indices

    # ================================================================
    # 权重统计
    # ================================================================

    def _compute_weight_entropy(self, weights: np.ndarray) -> float:
        """计算权重熵（衡量权重分布的均匀程度）.

        H = -sum_i w_i * log(w_i)

        均匀分布时 H = log(N)，完全退化时 H = 0。
        """
        log_weights = np.log(np.maximum(weights, 1e-300))
        entropy = -float(np.sum(weights * log_weights))
        return entropy

    # ================================================================
    # 观测算子构建
    # ================================================================

    def _build_observation_operator(
        self,
        xb: np.ndarray,
        observations: list[dict[str, Any]],
        shape: tuple[int, ...],
    ) -> tuple[np.ndarray, np.ndarray]:
        """构建观测算子矩阵 H 和观测向量 y."""
        n = len(xb)
        m = len(observations)
        y_obs = np.zeros(m)
        H = np.zeros((m, n))  # noqa: N806
        for j, obs in enumerate(observations):
            pos = obs.get("position", [0] * len(shape))
            y_obs[j] = obs.get("value", 0.0)
            idx = self._position_to_index(pos, shape)
            if 0 <= idx < n:
                H[j, idx] = 1.0  # noqa: N806
        return y_obs, H

    def _build_observation_error_matrix(
        self,
        observations: list[dict[str, Any]],
        m: int,
    ) -> np.ndarray:
        """构建观测误差协方差矩阵 R."""
        R = np.eye(m) * self.observation_error_scale**2  # noqa: N806
        for j, obs in enumerate(observations):
            obs_err = obs.get("error", self.observation_error_scale)
            R[j, j] = max(obs_err**2, 1e-10)  # noqa: N806
        return R

    # ================================================================
    # 诊断统计
    # ================================================================

    def _compute_diagnostics(
        self,
        xb: np.ndarray,
        xa: np.ndarray,
        bg_particles: np.ndarray,
        an_particles: np.ndarray,
        observations: list[dict[str, Any]],
        shape: tuple[int, ...],
        y_obs: np.ndarray,
        H: np.ndarray,  # noqa: N806
        weights: np.ndarray,
        n_eff: float,
    ) -> dict[str, Any]:
        """计算分析诊断统计."""
        increment = xa - xb
        increment_norm = float(np.linalg.norm(increment))
        increment_rms = float(np.sqrt(np.mean(increment**2)))

        # 拟合度统计
        if len(y_obs) > 0:
            Hxa = H @ xa  # noqa: N806
            Hxb = H @ xb  # noqa: N806
            residuals_analysis = Hxa - y_obs
            residuals_background = Hxb - y_obs

            rmse_analysis = float(np.sqrt(np.mean(residuals_analysis**2)))
            rmse_background = float(np.sqrt(np.mean(residuals_background**2)))
            improvement_ratio = (rmse_background - rmse_analysis) / max(rmse_background, 1e-10)
        else:
            rmse_analysis = 0.0
            rmse_background = 0.0
            improvement_ratio = 0.0

        # 粒子统计
        bg_spread = float(np.std(bg_particles, axis=0).mean())
        an_spread = float(np.std(an_particles, axis=0).mean())
        max_weight = float(np.max(weights))
        min_weight = float(np.min(weights))

        return {
            "increment": {
                "norm": increment_norm,
                "rms": increment_rms,
            },
            "fit": {
                "rmse_analysis": rmse_analysis,
                "rmse_background": rmse_background,
                "improvement_ratio": improvement_ratio,
            },
            "particles": {
                "background_spread": bg_spread,
                "analysis_spread": an_spread,
                "n_effective": n_eff,
                "max_weight": max_weight,
                "min_weight": min_weight,
                "weight_entropy": self._compute_weight_entropy(weights),
            },
        }

    # ================================================================
    # 工具方法
    # ================================================================

    @staticmethod
    def _position_to_index(pos: list[int], shape: tuple[int, ...]) -> int:
        """将多维位置索引转换为一维平坦索引."""
        idx = 0
        stride = 1
        for i in range(len(shape) - 1, -1, -1):
            idx += int(pos[i]) * stride
            stride *= shape[i]
        return idx
