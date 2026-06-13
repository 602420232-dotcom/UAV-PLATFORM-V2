"""GP 风险估计器.

基于高斯过程的风险概率估计模型，用于无人机航线安全评估。
通过已知风险区域数据训练高斯过程，对查询位置输出风险概率分布和不确定性。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
from scipy.spatial.distance import cdist

logger = logging.getLogger(__name__)


class GPRiskEstimator:
    """基于高斯过程的风险概率估计器.

    利用高斯过程回归对空间风险概率进行建模和估计，
    输出各查询位置的风险概率、风险分布图和不确定性度量。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        self.config = config or {}
        self.length_scale = self.config.get("length_scale", 5.0)
        self.signal_variance = self.config.get("signal_variance", 1.0)
        self.noise_variance = self.config.get("noise_variance", 0.05)
        self.threshold = self.config.get("threshold", 0.5)
        np.random.seed(42)

    def estimate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行基于 GP 的风险概率估计.

        Args:
            params: 包含以下键的字典:
                - location_data: 已知位置数据，形状 (n, d)，每行为坐标
                - risk_labels: 对应位置的风险标签，形状 (n,)，0 或 1
                - query_locations: 查询位置，形状 (m, d)
                - threshold: 风险判定阈值，默认 0.5

        Returns:
            包含风险概率、风险分布图和不确定性的字典。
        """
        np.random.seed(42)

        location_data = np.asarray(params.get("location_data", np.zeros((20, 2))))
        risk_labels = np.asarray(params.get("risk_labels", np.zeros(20)))
        query_locations = np.asarray(params.get("query_locations", np.zeros((10, 2))))
        threshold = params.get("threshold", self.threshold)

        n_train = len(location_data)
        n_query = len(query_locations)

        # 使用 GP 回归估计风险概率
        K = (  # noqa: N806
            self._rbf_kernel(location_data, location_data) + self.noise_variance * np.eye(n_train)
        )
        K_s = self._rbf_kernel(location_data, query_locations)  # noqa: N806
        K_ss = self._rbf_kernel(query_locations, query_locations)  # noqa: N806

        try:
            L = np.linalg.cholesky(K)  # noqa: N806
            alpha = np.linalg.solve(L.T, np.linalg.solve(L, risk_labels))
            mean = K_s.T @ alpha
            v = np.linalg.solve(L, K_s)
            cov = K_ss - v.T @ v
            var = np.diag(cov)
            var = np.maximum(var, 1e-10)
        except np.linalg.LinAlgError:
            logger.warning("GP 风险估计 Cholesky 分解失败，使用默认值")
            mean = np.full(n_query, 0.5)
            var = np.ones(n_query) * self.signal_variance
            cov = np.eye(n_query) * self.signal_variance

        std = np.sqrt(var)

        # 将均值映射到 [0, 1] 概率范围（sigmoid 变换）
        risk_probabilities = 1.0 / (1.0 + np.exp(-mean))
        risk_probabilities = np.clip(risk_probabilities, 0.0, 1.0)

        # 生成风险分布图（网格化）
        risk_map = self._generate_risk_map(query_locations, risk_probabilities)

        # 不确定性度量（基于标准差）
        uncertainty = std / (std.max() + 1e-10)

        # 风险分类
        risk_levels = np.where(risk_probabilities >= threshold, 1, 0)

        return {
            "risk_probabilities": risk_probabilities.tolist(),
            "risk_map": risk_map,
            "uncertainty": uncertainty.tolist(),
            "risk_levels": risk_levels.tolist(),
            "threshold": float(threshold),
            "n_train": n_train,
            "n_query": n_query,
        }

    def _rbf_kernel(self, x1: np.ndarray, x2: np.ndarray) -> np.ndarray:
        """RBF 核函数.

        Args:
            x1: 第一组输入点.
            x2: 第二组输入点.

        Returns:
            RBF 核矩阵.
        """
        dists = cdist(x1, x2, metric="sqeuclidean")
        return self.signal_variance * np.exp(-0.5 * dists / self.length_scale**2)

    @staticmethod
    def _generate_risk_map(
        query_locations: np.ndarray,
        risk_probabilities: np.ndarray,
    ) -> list[list[float]]:
        """生成风险分布图.

        将查询位置的风险概率映射到二维网格。

        Args:
            query_locations: 查询位置坐标，形状 (m, 2).
            risk_probabilities: 各位置风险概率，形状 (m,).

        Returns:
            二维风险分布图（网格化）。
        """
        n = len(query_locations)
        if n == 0:
            return [[0.0]]

        # 确定网格大小
        grid_size = max(int(np.ceil(np.sqrt(n))), 2)

        # 将坐标映射到网格索引
        x_min, x_max = query_locations[:, 0].min(), query_locations[:, 0].max()
        y_min, y_max = query_locations[:, 1].min(), query_locations[:, 1].max()

        x_range = x_max - x_min + 1e-10
        y_range = y_max - y_min + 1e-10

        grid = np.zeros((grid_size, grid_size))

        for i in range(n):
            xi = int((query_locations[i, 0] - x_min) / x_range * (grid_size - 1))
            yi = int((query_locations[i, 1] - y_min) / y_range * (grid_size - 1))
            xi = min(max(xi, 0), grid_size - 1)
            yi = min(max(yi, 0), grid_size - 1)
            grid[yi, xi] = risk_probabilities[i]

        return grid.tolist()
