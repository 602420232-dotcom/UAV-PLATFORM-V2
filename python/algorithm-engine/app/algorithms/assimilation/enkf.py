"""EnKF (Ensemble Kalman Filter) 数据同化算法.

集合卡尔曼滤波使用蒙特卡罗方法生成集合成员，通过集合统计量
估计流依赖的背景误差协方差，适用于非线性系统的数据同化。

算法原理:
  预报步（Forecast）:
    x_k^f(i) = M(x_{k-1}^a(i)),  i = 1, ..., N
    x_bar^f = (1/N) * sum_i x_k^f(i)
    P^f = (1/(N-1)) * sum_i (x_k^f(i) - x_bar^f)(x_k^f(i) - x_bar^f)^T

  分析步（Analysis）:
    K = P^f H^T (H P^f H^T + R)^{-1}
    x_k^a(i) = x_k^f(i) + K(y(i) - H x_k^f(i))

  其中:
    - N: 集合成员数
    - M: 非线性预报模式
    - H: 观测算子
    - R: 观测误差协方差
    - K: 卡尔曼增益矩阵
    - y(i): 带扰动的观测（随机扰动版本）

参考文献:
  Evensen (1994), J. Geophys. Res., 99(C5), 10143-10162
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EnKF:
    """集合卡尔曼滤波 (EnKF) 数据同化算法.

    特点:
    1. 使用蒙特卡罗集合方法估计背景误差协方差
    2. 分析步通过卡尔曼增益更新每个集合成员
    3. 支持随机扰动观测方案（Stochastic EnKF）
    4. 支持多变量同化（联合更新多个物理量）
    5. 自动估计流依赖的误差统计特征

    配置参数:
        ensemble_size: 集合成员数
        background_error_scale: 背景误差标准差
        observation_error_scale: 观测误差标准差
        localization: 是否使用协方差局地化
        inflation_factor: 集合膨胀因子
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        # 网格配置
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10, 5))
        self.resolution: float = self.config.get("resolution", 50.0)

        # 集合配置
        self.ensemble_size: int = self.config.get("ensemble_size", 30)
        self.background_error_scale: float = self.config.get("background_error_scale", 1.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)

        # 局地化配置
        self.localization: bool = self.config.get("localization", False)
        self.localization_radius: float = self.config.get("localization_radius", 3.0)

        # 膨胀配置
        self.inflation_factor: float = self.config.get("inflation_factor", 1.0)
        self.adaptive_inflation: bool = self.config.get("adaptive_inflation", False)

        # 多变量配置
        self.n_variables: int = self.config.get("n_variables", 1)

        # 随机种子
        self.seed: int = self.config.get("seed", 42)

    # ================================================================
    # 公共接口
    # ================================================================

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行EnKF集合卡尔曼滤波同化.

        Args:
            params: 分析参数字典，包含:
                - background_field: 背景场 (numpy.ndarray)
                - observations: 观测数据列表，每个元素包含:
                    - position: 观测位置
                    - value: 观测值
                    - error: 观测误差（可选）
                - ensemble: 预报集合成员（可选）
                - ensemble_size: 集合成员数（可选）
                - n_variables: 变量数（可选，用于多变量同化）

        Returns:
            包含分析场、集合展开度、卡尔曼增益统计等信息的字典
        """
        background = np.asarray(
            params.get("background_field", np.zeros(self.grid_shape)),
            dtype=float,
        )
        observations = params.get("observations", [])
        n_ens = params.get("ensemble_size", self.ensemble_size)
        self.n_variables = params.get("n_variables", self.n_variables)

        n_state = background.size
        xb = background.flatten()

        # 初始化集合
        ensemble = self._initialize_ensemble(xb, n_ens, params)

        # 构建观测算子
        y_obs, H = self._build_observation_operator(  # noqa: N806
            xb, observations, background.shape
        )
        m = len(y_obs)

        # 构建观测误差协方差
        R = self._build_observation_error_matrix(observations, m)  # noqa: N806

        # 预报步统计
        x_mean = ensemble.mean(axis=0)
        X_pert = ensemble - x_mean[np.newaxis, :]  # noqa: N806

        # 估计背景误差协方差 P^f = (1/(N-1)) X' X'^T
        Pf = (X_pert.T @ X_pert) / (n_ens - 1)  # noqa: N806

        # 计算卡尔曼增益 K = P^f H^T (H P^f H^T + R)^{-1}
        HPHT = H @ Pf @ H.T  # noqa: N806
        HPHT_plus_R = HPHT + R  # noqa: N806

        # 正则化防止奇异
        HPHT_plus_R += np.eye(m) * 1e-10

        try:
            K = Pf @ H.T @ np.linalg.inv(HPHT_plus_R)  # noqa: N806
        except np.linalg.LinAlgError:
            logger.warning("卡尔曼增益矩阵求解失败，使用零矩阵")
            K = np.zeros((n_state, m))  # noqa: N806

        # 分析步: 使用随机扰动观测方案
        np.random.seed(self.seed)
        obs_perturbation = np.random.randn(n_ens, m) * self.observation_error_scale
        obs_ensemble = y_obs[np.newaxis, :] + obs_perturbation

        # 更新每个集合成员
        for i in range(n_ens):
            innovation = obs_ensemble[i] - H @ ensemble[i]
            ensemble[i] = ensemble[i] + K @ innovation

        # 应用膨胀
        if self.inflation_factor != 1.0:
            ensemble = self._apply_inflation(ensemble, self.inflation_factor)

        # 分析结果
        analysis_mean = ensemble.mean(axis=0)
        analysis_spread = float(np.std(ensemble, axis=0).mean())
        bg_spread = float(np.std(X_pert, axis=0).mean())

        # 诊断统计
        diagnostics = self._compute_diagnostics(
            xb, analysis_mean, X_pert, ensemble - analysis_mean[np.newaxis, :],
            observations, background.shape, y_obs, H, K
        )

        return {
            "analysis_field": analysis_mean.reshape(background.shape).tolist(),
            "spread": analysis_spread,
            "background_spread": bg_spread,
            "ensemble_size": n_ens,
            "grid_shape": list(background.shape),
            "n_variables": self.n_variables,
            "kalman_gain_norm": float(np.linalg.norm(K)),
            "innovation_variance": float(np.var(obs_ensemble - H @ ensemble)),
            "diagnostics": diagnostics,
        }

    # ================================================================
    # 集合初始化
    # ================================================================

    def _initialize_ensemble(
        self,
        xb: np.ndarray,
        n_ens: int,
        params: dict[str, Any],
    ) -> np.ndarray:
        """初始化集合成员.

        如果提供了预报集合则使用预报集合，
        否则围绕背景场生成高斯扰动集合。
        """
        provided_ensemble = params.get("ensemble", None)
        if provided_ensemble is not None:
            ensemble = np.asarray(provided_ensemble, dtype=float)
            if ensemble.ndim == 1:
                ensemble = ensemble.reshape(1, -1)
            return ensemble

        n_state = len(xb)
        np.random.seed(self.seed)
        perturbation = np.random.randn(n_ens, n_state) * self.background_error_scale
        ensemble = xb[np.newaxis, :] + perturbation
        return ensemble

    # ================================================================
    # 膨胀处理
    # ================================================================

    def _apply_inflation(
        self,
        ensemble: np.ndarray,
        factor: float,
    ) -> np.ndarray:
        """应用集合膨胀，防止滤波发散.

        膨胀方法: 将集合扰动乘以膨胀因子
        x_a(i) = x_bar_a + factor * (x_a(i) - x_bar_a)
        """
        mean = ensemble.mean(axis=0)
        perturbations = ensemble - mean[np.newaxis, :]
        inflated = mean[np.newaxis, :] + factor * perturbations
        return inflated

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
        bg_pert: np.ndarray,
        an_pert: np.ndarray,
        observations: list[dict[str, Any]],
        shape: tuple[int, ...],
        y_obs: np.ndarray,
        H: np.ndarray,  # noqa: N806
        K: np.ndarray,  # noqa: N806
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

        # 集合统计
        bg_spread = float(np.std(bg_pert, axis=0).mean())
        an_spread = float(np.std(an_pert, axis=0).mean())

        # 卡尔曼增益统计
        K_max = float(np.max(np.abs(K)))  # noqa: N806
        K_mean = float(np.mean(np.abs(K)))  # noqa: N806

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
            "ensemble": {
                "background_spread": bg_spread,
                "analysis_spread": an_spread,
                "spread_ratio": an_spread / max(bg_spread, 1e-10),
            },
            "kalman_gain": {
                "max": K_max,
                "mean": K_mean,
                "norm": float(np.linalg.norm(K)),
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
