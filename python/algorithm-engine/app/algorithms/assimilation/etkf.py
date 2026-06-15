"""ETKF (Ensemble Transform Kalman Filter) 数据同化算法.

集合变换卡尔曼滤波是EnKF的确定性版本，通过变换矩阵方法
更新集合成员，无需对观测进行随机扰动。

算法原理:
  1. 计算集合均值和扰动矩阵:
     x_bar = (1/N) * sum_i x_i
     X' = [x_1 - x_bar, ..., x_N - x_bar] / sqrt(N-1)

  2. 在观测空间计算:
     Y' = H X'
     S = Y'^T R^{-1} Y'

  3. 求解变换矩阵:
     T = (I + S)^{-1}
     T^{1/2} = V diag(sqrt(1/lambda_i)) V^T

  4. 更新集合:
     x_bar^a = x_bar + X' Y'^T (Y' Y'^T + R)^{-1} (y - H x_bar)
     X'^a = X' T^{1/2}

  优势: 确定性方法，结果不依赖随机数种子，分析更稳定。

参考文献:
  Bishop et al. (2001), Mon. Wea. Rev., 129, 420-436
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ETKF:
    """集合变换卡尔曼滤波 (ETKF) 数据同化算法.

    特点:
    1. EnKF的确定性版本，无需扰动观测
    2. 使用变换矩阵方法更新集合成员
    3. 保持集合均值和展开度的最优平衡
    4. 分析结果可重复（不依赖随机种子）
    5. 支持多变量同化

    配置参数:
        ensemble_size: 集合成员数
        background_error_scale: 背景误差标准差
        observation_error_scale: 观测误差标准差
        inflation_factor: 膨胀因子
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

        # 膨胀配置
        self.inflation_factor: float = self.config.get("inflation_factor", 1.0)

        # 多变量配置
        self.n_variables: int = self.config.get("n_variables", 1)

        # 随机种子（仅用于集合初始化）
        self.seed: int = self.config.get("seed", 42)

    # ================================================================
    # 公共接口
    # ================================================================

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行ETKF集合变换卡尔曼滤波同化.

        Args:
            params: 分析参数字典，包含:
                - background_field: 背景场 (numpy.ndarray)
                - observations: 观测数据列表，每个元素包含:
                    - position: 观测位置
                    - value: 观测值
                    - error: 观测误差（可选）
                - ensemble: 预报集合成员（可选）
                - ensemble_size: 集合成员数（可选）

        Returns:
            包含分析场、变换矩阵信息、集合统计等信息的字典
        """
        background = np.asarray(
            params.get("background_field", np.zeros(self.grid_shape)),
            dtype=float,
        )
        observations = params.get("observations", [])
        n_ens = params.get("ensemble_size", self.ensemble_size)

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

        # ETKF分析
        result = self._etkf_analysis(ensemble, y_obs, H, R, xb)

        # 诊断统计
        diagnostics = self._compute_diagnostics(
            xb, result["analysis_mean"], ensemble,
            result["analysis_ensemble"], observations,
            background.shape, y_obs, H
        )

        return {
            "analysis_field": result["analysis_mean"].reshape(background.shape).tolist(),
            "ensemble_spread": result["analysis_spread"],
            "background_spread": result["background_spread"],
            "ensemble_size": n_ens,
            "grid_shape": list(background.shape),
            "transform_matrix_condition": result["transform_condition"],
            "n_observations": m,
            "diagnostics": diagnostics,
        }

    # ================================================================
    # ETKF分析核心
    # ================================================================

    def _etkf_analysis(
        self,
        ensemble: np.ndarray,
        y_obs: np.ndarray,
        H: np.ndarray,  # noqa: N806
        R: np.ndarray,  # noqa: N806
        xb: np.ndarray,
    ) -> dict[str, Any]:
        """执行ETKF核心分析步骤.

        步骤:
        1. 计算集合均值和扰动矩阵
        2. 在观测空间投影集合扰动
        3. 构建并求解变换矩阵
        4. 更新集合均值和扰动

        Args:
            ensemble: 集合矩阵 (n_ens x n_state)
            y_obs: 观测向量 (m,)
            H: 观测算子 (m x n_state)
            R: 观测误差协方差 (m x m)
            xb: 背景场向量 (n_state,)

        Returns:
            包含分析集合和统计信息的字典
        """
        n_ens = ensemble.shape[0]
        n_state = ensemble.shape[1]
        m = len(y_obs)

        # 1. 集合均值和扰动
        x_mean = ensemble.mean(axis=0)
        X_pert = ensemble - x_mean[np.newaxis, :]  # (n_ens, n_state)
        X_pert_scaled = X_pert / np.sqrt(n_ens - 1)  # (n_ens, n_state)

        # 2. 观测空间投影
        # Y' = H X' (m x n_ens)
        Yb = H @ X_pert_scaled.T  # (m, n_ens)

        # 3. 计算 S = Y'^T R^{-1} Y' (n_ens x n_ens)
        try:
            R_inv = np.linalg.inv(R)  # noqa: N806
        except np.linalg.LinAlgError:
            R_inv = np.linalg.pinv(R)  # noqa: N806

        YbT_Rinv = Yb.T @ R_inv  # (n_ens, m)
        S = YbT_Rinv @ Yb  # (n_ens, n_ens)

        # 4. 求解变换矩阵 T = (I + S)^{-1}
        I_plus_S = np.eye(n_ens) + S

        # 正则化
        I_plus_S += np.eye(n_ens) * 1e-10

        try:
            T = np.linalg.inv(I_plus_S)  # (n_ens, n_ens)
            transform_condition = float(np.linalg.cond(I_plus_S))
        except np.linalg.LinAlgError:
            logger.warning("变换矩阵求解失败，使用单位矩阵近似")
            T = np.eye(n_ens) / (1.0 + n_ens)
            transform_condition = float("inf")

        # 5. T^{1/2} 用于更新集合扰动
        try:
            eigenvalues, eigenvectors = np.linalg.eigh(T)
            eigenvalues = np.maximum(eigenvalues, 1e-10)
            T_sqrt = eigenvectors @ np.diag(np.sqrt(eigenvalues)) @ eigenvectors.T
        except np.linalg.LinAlgError:
            T_sqrt = np.eye(n_ens) / np.sqrt(n_ens)

        # 6. 更新集合均值
        # K = X' Y'^T (Y' Y'^T + R)^{-1}
        # 简化: K = X' Y'^T R^{-1} T
        K = X_pert_scaled.T @ YbT_Rinv @ T  # (n_state, m)

        innovation = y_obs - H @ x_mean
        analysis_mean = x_mean + K @ innovation

        # 7. 更新集合扰动
        # X'^a = X' T^{1/2}
        analysis_pert = X_pert_scaled @ T_sqrt.T  # (n_ens, n_state)
        analysis_pert = analysis_pert * np.sqrt(n_ens - 1)

        # 8. 构建分析集合
        analysis_ensemble = analysis_mean[np.newaxis, :] + analysis_pert

        # 9. 应用膨胀
        if self.inflation_factor != 1.0:
            analysis_ensemble = self._apply_inflation(
                analysis_ensemble, self.inflation_factor
            )

        # 统计
        analysis_spread = float(np.std(analysis_ensemble, axis=0).mean())
        background_spread = float(np.std(ensemble, axis=0).mean())

        return {
            "analysis_mean": analysis_mean,
            "analysis_ensemble": analysis_ensemble,
            "analysis_spread": analysis_spread,
            "background_spread": background_spread,
            "transform_condition": transform_condition,
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
        """初始化集合成员."""
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
        """应用集合膨胀."""
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
        bg_ensemble: np.ndarray,
        an_ensemble: np.ndarray,
        observations: list[dict[str, Any]],
        shape: tuple[int, ...],
        y_obs: np.ndarray,
        H: np.ndarray,  # noqa: N806
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
        bg_spread = float(np.std(bg_ensemble, axis=0).mean())
        an_spread = float(np.std(an_ensemble, axis=0).mean())

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
