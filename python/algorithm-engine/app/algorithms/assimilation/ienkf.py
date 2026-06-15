"""IENKF (Iterative Ensemble Kalman Filter) 数据同化算法.

迭代集合卡尔曼滤波通过多次迭代改进分析解，每次迭代更新
集合均值和集合成员，逐步逼近最优分析解。

算法原理:
  第k次迭代:
    1. 计算当前迭代的集合均值和扰动:
       x_bar^(k) = (1/N) * sum_i x_i^(k)
       X'^(k) = [x_1^(k) - x_bar^(k), ..., x_N^(k) - x_bar^(k)]

    2. 计算迭代卡尔曼增益:
       K^(k) = X'^(k) Y'^(k)^T (Y'^(k) Y'^(k)^T + R)^{-1}

    3. 更新集合均值:
       x_bar^(k+1) = x_bar^(k) + K^(k) (y - H x_bar^(k))

    4. 更新集合扰动:
       X'^(k+1) = X'^(k) (I - K^(k) H) / sqrt(N-1)

    5. 收敛判断: ||x_bar^(k+1) - x_bar^(k)|| < tolerance

  优势: 通过迭代可以处理非线性观测算子，获得更精确的分析解。

参考文献:
  Sakov et al. (2012), Ocean Modelling, 55-56, 1-11
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class IENKF:
    """迭代集合卡尔曼滤波 (IENKF) 数据同化算法.

    特点:
    1. 通过迭代改进分析解的精度
    2. 每次迭代更新集合均值和集合成员
    3. 支持非线性观测算子
    4. 内置收敛判断机制
    5. 支持阻尼迭代防止发散

    配置参数:
        ensemble_size: 集合成员数
        max_iterations: 最大迭代次数
        tolerance: 收敛阈值
        damping_factor: 阻尼因子（0-1）
        background_error_scale: 背景误差标准差
        observation_error_scale: 观测误差标准差
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

        # 迭代配置
        self.max_iterations: int = self.config.get("max_iterations", 10)
        self.tolerance: float = self.config.get("tolerance", 1e-4)
        self.damping_factor: float = self.config.get("damping_factor", 0.5)

        # 膨胀配置
        self.inflation_factor: float = self.config.get("inflation_factor", 1.0)

        # 随机种子
        self.seed: int = self.config.get("seed", 42)

    # ================================================================
    # 公共接口
    # ================================================================

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行IENKF迭代集合卡尔曼滤波同化.

        Args:
            params: 分析参数字典，包含:
                - background_field: 背景场 (numpy.ndarray)
                - observations: 观测数据列表，每个元素包含:
                    - position: 观测位置
                    - value: 观测值
                    - error: 观测误差（可选）
                - ensemble: 预报集合成员（可选）
                - ensemble_size: 集合成员数（可选）
                - max_iterations: 最大迭代次数（可选）

        Returns:
            包含分析场、迭代历史、收敛信息等的字典
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

        # 迭代求解
        iteration_history: list[dict[str, Any]] = []

        for iter_idx in range(self.max_iterations):
            # 执行单次迭代
            iter_result = self._single_iteration(
                ensemble, y_obs, H, R, iter_idx
            )

            ensemble = iter_result["updated_ensemble"]
            iteration_history.append(iter_result)

            # 收敛判断
            if iter_idx > 0:
                prev_mean = np.array(iteration_history[-2]["ensemble_mean"])
                curr_mean = np.array(iter_result["ensemble_mean"])
                mean_change = float(np.linalg.norm(curr_mean - prev_mean))

                if mean_change < self.tolerance:
                    logger.info("IENKF 收敛于迭代 %d, 均值变化=%.6e", iter_idx, mean_change)
                    break

        # 最终分析结果
        analysis_mean = ensemble.mean(axis=0)
        analysis_spread = float(np.std(ensemble, axis=0).mean())

        # 诊断统计
        diagnostics = self._compute_diagnostics(
            xb, analysis_mean, observations, background.shape,
            y_obs, H, iteration_history
        )

        return {
            "analysis_field": analysis_mean.reshape(background.shape).tolist(),
            "spread": analysis_spread,
            "ensemble_size": n_ens,
            "grid_shape": list(background.shape),
            "iterations": len(iteration_history),
            "converged": len(iteration_history) < self.max_iterations,
            "iteration_history": iteration_history,
            "diagnostics": diagnostics,
        }

    # ================================================================
    # 单次迭代
    # ================================================================

    def _single_iteration(
        self,
        ensemble: np.ndarray,
        y_obs: np.ndarray,
        H: np.ndarray,  # noqa: N806
        R: np.ndarray,  # noqa: N806
        iter_idx: int,
    ) -> dict[str, Any]:
        """执行单次IENKF迭代.

        步骤:
        1. 计算集合均值和扰动
        2. 计算卡尔曼增益
        3. 更新集合均值
        4. 更新集合扰动
        5. 应用阻尼因子

        Args:
            ensemble: 当前集合 (n_ens x n_state)
            y_obs: 观测向量 (m,)
            H: 观测算子 (m x n_state)
            R: 观测误差协方差 (m x m)
            iter_idx: 当前迭代索引

        Returns:
            包含更新后集合和统计信息的字典
        """
        n_ens = ensemble.shape[0]

        # 1. 集合均值和扰动
        x_mean = ensemble.mean(axis=0)
        X_pert = ensemble - x_mean[np.newaxis, :]  # (n_ens, n_state)

        # 2. 估计背景误差协方差
        Pf = (X_pert.T @ X_pert) / (n_ens - 1)  # (n_state, n_state)

        # 3. 计算卡尔曼增益
        HPHT = H @ Pf @ H.T  # (m, m)
        HPHT_plus_R = HPHT + R  # (m, m)
        HPHT_plus_R += np.eye(len(y_obs)) * 1e-10  # 正则化

        try:
            K = Pf @ H.T @ np.linalg.inv(HPHT_plus_R)  # (n_state, m)
        except np.linalg.LinAlgError:
            logger.warning("迭代 %d: 卡尔曼增益求解失败", iter_idx)
            K = np.zeros((ensemble.shape[1], len(y_obs)))

        # 4. 更新集合均值
        innovation = y_obs - H @ x_mean
        mean_increment = K @ innovation

        # 应用阻尼: 只应用部分增量
        new_mean = x_mean + self.damping_factor * mean_increment

        # 5. 更新集合扰动
        # X'^a = X' (I - K H) / sqrt(N-1)
        KH = K @ H  # (n_state, n_state)
        I_minus_KH = np.eye(ensemble.shape[1]) - KH
        new_pert = X_pert @ I_minus_KH.T

        # 6. 构建更新后的集合
        new_ensemble = new_mean[np.newaxis, :] + new_pert

        # 7. 应用膨胀
        if self.inflation_factor != 1.0:
            ens_mean = new_ensemble.mean(axis=0)
            ens_pert = new_ensemble - ens_mean[np.newaxis, :]
            new_ensemble = ens_mean[np.newaxis, :] + ens_pert * self.inflation_factor

        # 统计
        old_spread = float(np.std(ensemble, axis=0).mean())
        new_spread = float(np.std(new_ensemble, axis=0).mean())
        increment_norm = float(np.linalg.norm(mean_increment))
        innovation_norm = float(np.linalg.norm(innovation))

        return {
            "iteration": iter_idx,
            "ensemble_mean": new_mean.tolist(),
            "updated_ensemble": new_ensemble,
            "increment_norm": increment_norm,
            "innovation_norm": innovation_norm,
            "old_spread": old_spread,
            "new_spread": new_spread,
            "spread_change": (new_spread - old_spread) / max(old_spread, 1e-10),
            "kalman_gain_norm": float(np.linalg.norm(K)),
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
        observations: list[dict[str, Any]],
        shape: tuple[int, ...],
        y_obs: np.ndarray,
        H: np.ndarray,  # noqa: N806
        iteration_history: list[dict[str, Any]],
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

        # 迭代收敛统计
        increment_norms = [h["increment_norm"] for h in iteration_history]
        spread_changes = [h["spread_change"] for h in iteration_history]

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
            "iteration": {
                "n_iterations": len(iteration_history),
                "increment_norms": increment_norms,
                "spread_changes": spread_changes,
                "final_increment_norm": increment_norms[-1] if increment_norms else 0.0,
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
