"""B样条曲线路径规划算法。

使用B样条函数对路径控制点进行平滑逼近。
B样条具有局部支撑性、凸包性和变差缩减性等优点，
适用于需要局部修改和光滑曲线的路径规划场景。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class BSplinePlanner:
    """B样条曲线路径规划器。

    给定一组路径控制点，使用B样条函数生成平滑逼近曲线。
    相比三次样条，B样条不强制通过所有控制点，
    但具有更好的局部控制性和光滑性。

    Args:
        config: 配置字典，支持以下参数：
            - degree: B样条阶数，默认3（三次B样条）
            - n_samples: 采样点数量，默认100
            - n_control_refinement: 控制点细化迭代次数，默认0
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.degree: int = self.config.get("degree", 3)
        self.n_samples: int = self.config.get("n_samples", 100)
        self.n_refinement: int = self.config.get("n_control_refinement", 0)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行B样条曲线路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - grid_size: 网格尺寸 (int, int)
                - waypoints: 中间路径控制点列表（可选）

        Returns:
            包含 path（平滑路径点列表）和 cost（路径长度）的字典。
        """
        np.random.seed(42)

        start = np.array(params.get("start", (0, 0)), dtype=float)
        goal = np.array(params.get("goal", (10, 10)), dtype=float)
        grid_size = params.get("grid_size", (50, 50))
        waypoints = params.get("waypoints", [])

        logger.info(
            "B样条规划: 起点=%s, 终点=%s, 阶数=%d",
            tuple(start.astype(int)),
            tuple(goal.astype(int)),
            self.degree,
        )

        rows, cols = grid_size

        # 构建控制点序列
        if waypoints and len(waypoints) > 0:
            wp_array = np.array(waypoints, dtype=float)
            control_points = np.vstack([start.reshape(1, 2), wp_array, goal.reshape(1, 2)])
        else:
            control_points = np.array([start, goal], dtype=float)

        n = len(control_points)

        if n < 2:
            return {"path": [start.tolist()], "cost": 0.0}

        # 确保控制点数量足够
        if n <= self.degree:
            # 控制点不足，在起点和终点之间添加中间点
            n_add = self.degree - n + 2
            t_values = np.linspace(0, 1, n_add + 2)[1:-1]
            mid_points = np.outer(1 - t_values, start) + np.outer(t_values, goal)
            control_points = np.vstack([start.reshape(1, 2), mid_points, goal.reshape(1, 2)])
            n = len(control_points)

        # 计算节点向量
        knot_vector = self._compute_knot_vector(n, self.degree)

        # 采样B样条曲线
        curve_points = self._sample_bspline(control_points, knot_vector)

        # 边界约束
        curve_points[:, 0] = np.clip(curve_points[:, 0], 0, rows - 1)
        curve_points[:, 1] = np.clip(curve_points[:, 1], 0, cols - 1)

        path = [[int(round(p[0])), int(round(p[1]))] for p in curve_points]
        cost = self._path_cost(curve_points)

        logger.info(
            "B样条规划完成: 代价=%.2f, 路径点=%d, 控制点=%d",
            cost,
            len(path),
            n,
        )
        return {
            "path": path,
            "cost": cost,
            "n_control_points": n,
            "degree": self.degree,
        }

    def _compute_knot_vector(self, n_points: int, degree: int) -> np.ndarray:
        """计算均匀B样条节点向量。

        使用Clamped（夹持）节点向量，确保曲线通过首尾控制点。
        """
        n_knots = n_points + degree + 1
        knot_vector = np.zeros(n_knots)

        # 前degree+1个节点为0
        for i in range(degree + 1):
            knot_vector[i] = 0.0

        # 中间节点均匀分布
        n_inner = n_knots - 2 * (degree + 1)
        for i in range(n_inner):
            knot_vector[degree + 1 + i] = (i + 1) / (n_inner + 1)

        # 后degree+1个节点为1
        for i in range(degree + 1):
            knot_vector[n_knots - degree - 1 + i] = 1.0

        return knot_vector

    def _basis_function(
        self,
        i: int,
        k: int,
        t: float,
        knot_vector: np.ndarray,
    ) -> float:
        """计算B样条基函数 N_{i,k}(t)。

        使用Cox-de Boor递推公式。
        """
        if k == 0:
            if knot_vector[i] <= t < knot_vector[i + 1]:
                return 1.0
            # 处理右端点特殊情况
            if i == len(knot_vector) - 2 and abs(t - knot_vector[i + 1]) < 1e-10:
                return 1.0
            return 0.0

        denom1 = knot_vector[i + k] - knot_vector[i]
        denom2 = knot_vector[i + k + 1] - knot_vector[i + 1]

        term1 = 0.0
        if abs(denom1) > 1e-10:
            term1 = (t - knot_vector[i]) / denom1 * self._basis_function(i, k - 1, t, knot_vector)

        term2 = 0.0
        if abs(denom2) > 1e-10:
            term2 = (knot_vector[i + k + 1] - t) / denom2 * self._basis_function(i + 1, k - 1, t, knot_vector)

        return term1 + term2

    def _sample_bspline(
        self,
        control_points: np.ndarray,
        knot_vector: np.ndarray,
    ) -> np.ndarray:
        """采样B样条曲线。"""
        n_points = len(control_points)
        curve_points = []

        for sample_idx in range(self.n_samples):
            t = sample_idx / (self.n_samples - 1)

            point = np.zeros(2)
            for i in range(n_points):
                basis = self._basis_function(i, self.degree, t, knot_vector)
                point += basis * control_points[i]

            curve_points.append(point)

        return np.array(curve_points)

    def _path_cost(self, points: np.ndarray) -> float:
        """计算路径代价。"""
        if len(points) < 2:
            return 0.0
        diffs = np.diff(points, axis=0)
        return float(np.sum(np.sqrt(np.sum(diffs**2, axis=1))))
