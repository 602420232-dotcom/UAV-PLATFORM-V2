"""集合卡尔曼滤波同化模型 — 基于蒙特卡洛方法的数据同化.

使用集合卡尔曼滤波（EnKF）方法进行数据同化，通过蒙特卡洛集合
估计背景误差协方差，将观测信息融入分析场。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EnsembleKalmanFilterModel:
    """集合卡尔曼滤波同化模型.

    通过维护一个状态集合来估计背景误差协方差，避免显式计算和存储
    大型协方差矩阵。支持观测算子的线性化应用和协方差膨胀以防止
    滤波发散。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.default_inflation = self.config.get("inflation", 1.05)
        self.default_ensemble_size = self.config.get("ensemble_size", 50)
        self.localization_radius = self.config.get("localization_radius", 5.0)
        self.min_spread = self.config.get("min_spread", 1e-6)

    def analyze(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行集合卡尔曼滤波分析步.

        Args:
            params: 分析参数字典，包含:
                - background_ensemble: 背景场集合 (n_members x n_state)
                - observations: 观测数据 (n_obs,) 或 (n_obs, n_obs_cov)
                - observation_operator: 观测算子矩阵 H (n_obs x n_state)
                  或可调用函数
                - inflation: 膨胀系数 (默认1.05)

        Returns:
            包含分析结果的字典:
                - analysis_ensemble: 分析场集合
                - analysis_mean: 分析均值
                - spread: 分析场离散度
                - innovation: 新息统计
        """
        np.random.seed(42)

        background_ensemble = np.asarray(
            params.get("background_ensemble", np.zeros((50, 100))),
            dtype=float,
        )
        observations = np.asarray(
            params.get("observations", np.zeros(20)),
            dtype=float,
        )
        observation_operator = params.get("observation_operator", None)
        inflation = params.get("inflation", self.default_inflation)

        n_members, n_state = background_ensemble.shape
        logger.info(
            "开始EnKF分析: 集合成员数=%d, 状态维度=%d, 观测数=%d, 膨胀系数=%.3f",
            n_members,
            n_state,
            len(observations),
            inflation,
        )

        H = self._get_observation_operator(
            observation_operator,
            len(observations),
            n_state,
        )

        xb_mean = background_ensemble.mean(axis=0)
        Xb_prime = background_ensemble - xb_mean

        Xb_prime_inflated = Xb_prime * np.sqrt(inflation)
        background_ensemble_inflated = Xb_prime_inflated + xb_mean

        Pb_h = Xb_prime_inflated.T @ Xb_prime_inflated / (n_members - 1)

        HXb = (H @ background_ensemble_inflated.T).T
        yb_mean = HXb.mean(axis=0)
        innovation = observations - yb_mean

        Y_prime = HXb - yb_mean
        HPb_ht = Y_prime.T @ Y_prime / (n_members - 1)

        R = self._estimate_observation_error(observations)

        HPb_ht_R = HPb_ht + R

        try:
            Kalman_gain = (
                Pb_h
                @ H.T
                @ np.linalg.solve(
                    HPb_ht_R,
                    np.eye(HPb_ht_R.shape[0]),
                )
            )
        except np.linalg.LinAlgError:
            logger.warning("矩阵求解失败，使用伪逆")
            Kalman_gain = Pb_h @ H.T @ np.linalg.pinv(HPb_ht_R)

        analysis_ensemble = np.zeros_like(background_ensemble_inflated)
        for i in range(n_members):
            analysis_ensemble[i] = (
                background_ensemble_inflated[i]
                + Kalman_gain @ (observations - HXb[i])
            )

        xa_mean = analysis_ensemble.mean(axis=0)
        Xa_prime = analysis_ensemble - xa_mean
        spread = np.sqrt(np.mean(Xa_prime**2, axis=0))

        innovation_stats = self._compute_innovation_stats(
            innovation,
            HPb_ht_R,
        )

        logger.info(
            "EnKF分析完成: 分析均值范数=%.4f, 平均离散度=%.6f",
            float(np.linalg.norm(xa_mean)),
            float(np.mean(spread)),
        )

        return {
            "analysis_ensemble": analysis_ensemble.tolist(),
            "analysis_mean": xa_mean.tolist(),
            "spread": spread.tolist(),
            "innovation": innovation_stats,
        }

    def _get_observation_operator(
        self,
        obs_operator: Any,
        n_obs: int,
        n_state: int,
    ) -> np.ndarray:
        """获取观测算子矩阵.

        支持直接传入矩阵或可调用函数。
        """
        if obs_operator is None:
            logger.info("未提供观测算子，使用随机降采样算子")
            np.random.seed(42)
            H = np.zeros((n_obs, n_state))
            indices = np.random.choice(n_state, n_obs, replace=False)
            for i, idx in enumerate(indices):
                H[i, idx] = 1.0
            return H

        if callable(obs_operator):
            identity = np.eye(n_state)
            H = np.array([obs_operator(identity[i]) for i in range(n_state)]).T
            return H

        return np.asarray(obs_operator, dtype=float)

    def _estimate_observation_error(
        self,
        observations: np.ndarray,
    ) -> np.ndarray:
        """估计观测误差协方差矩阵.

        使用观测方差的百分比作为对角线元素。
        """
        n_obs = len(observations)
        obs_var = np.var(observations) if len(observations) > 1 else 1.0
        error_ratio = self.config.get("observation_error_ratio", 0.1)
        R = np.eye(n_obs) * max(obs_var * error_ratio, 1e-8)
        return R

    def _compute_innovation_stats(
        self,
        innovation: np.ndarray,
        HPb_ht_R: np.ndarray,
    ) -> dict[str, Any]:
        """计算新息（innovation）统计量."""
        innovation_norm = float(np.linalg.norm(innovation))
        innovation_mean = float(np.mean(innovation))
        innovation_std = float(np.std(innovation))
        innovation_max = float(np.max(np.abs(innovation)))

        n_obs = len(innovation)
        if HPb_ht_R.shape[0] == n_obs:
            try:
                chi2 = float(
                    innovation @ np.linalg.solve(HPb_ht_R, innovation),
                )
            except np.linalg.LinAlgError:
                chi2 = float("nan")
        else:
            chi2 = float("nan")

        return {
            "innovation_norm": innovation_norm,
            "innovation_mean": innovation_mean,
            "innovation_std": innovation_std,
            "innovation_max_abs": innovation_max,
            "chi_squared": chi2,
            "n_observations": n_obs,
        }
