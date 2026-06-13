"""GP路径规划器 — 基于高斯过程回归的不确定性感知路径规划.

在代价函数中融入GP预测的不确定性，通过A*搜索在网格上寻找
兼顾路径长度与安全性的最优路径。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class GPRPathPlanner:
    """基于高斯过程回归的不确定性感知路径规划器.

    利用GP均值场作为环境代价估计，GP方差场作为不确定性度量，
    在A*搜索的代价函数中同时考虑路径长度与不确定性，实现安全
    可靠的路径规划。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.default_uncertainty_weight = self.config.get(
            "uncertainty_weight",
            0.5,
        )
        self.default_grid_size = self.config.get("grid_size", 50)
        self.diagonal_cost = self.config.get("diagonal_cost", 1.414)
        self.max_iterations = self.config.get("max_iterations", 50000)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行不确定性感知路径规划.

        Args:
            params: 规划参数字典，包含:
                - start: 起点坐标 [x, y]
                - goal: 终点坐标 [x, y]
                - grid_size: 网格尺寸 (默认50)
                - gp_mean: GP均值场 (2D numpy数组)
                - gp_variance: GP方差场 (2D numpy数组)
                - uncertainty_weight: 不确定性权重 (默认0.5)

        Returns:
            包含规划结果的字典:
                - path: 规划路径点列表
                - cost: 路径总代价
                - uncertainty_along_path: 路径上各点的不确定性值
                - safety_margin: 安全裕度
        """
        np.random.seed(42)

        start = np.asarray(params.get("start", [0, 0]), dtype=float)
        goal = np.asarray(params.get("goal", [49, 49]), dtype=float)
        grid_size = params.get("grid_size", self.default_grid_size)
        gp_mean = np.asarray(
            params.get("gp_mean", np.zeros((grid_size, grid_size))),
            dtype=float,
        )
        gp_variance = np.asarray(
            params.get("gp_variance", np.ones((grid_size, grid_size)) * 0.1),
            dtype=float,
        )
        uncertainty_weight = params.get(
            "uncertainty_weight",
            self.default_uncertainty_weight,
        )

        logger.info(
            "开始GP路径规划: start=%s, goal=%s, grid_size=%d, uncertainty_weight=%.2f",
            start,
            goal,
            grid_size,
            uncertainty_weight,
        )

        start_cell = tuple(np.clip(start.astype(int), 0, grid_size - 1))
        goal_cell = tuple(np.clip(goal.astype(int), 0, grid_size - 1))

        path = self._a_star_search(
            start_cell,
            goal_cell,
            gp_mean,
            gp_variance,
            uncertainty_weight,
            grid_size,
        )

        if path is None:
            logger.warning("未找到可行路径，使用直线回退")
            path = self._straight_line_path(start_cell, goal_cell)

        cost = self._compute_path_cost(
            path,
            gp_mean,
            gp_variance,
            uncertainty_weight,
        )
        uncertainty_along_path = self._extract_uncertainty(
            path,
            gp_variance,
        )
        safety_margin = self._compute_safety_margin(
            uncertainty_along_path,
        )

        logger.info(
            "路径规划完成: 路径长度=%d, 总代价=%.4f, 安全裕度=%.4f",
            len(path),
            cost,
            safety_margin,
        )

        return {
            "path": [list(p) for p in path],
            "cost": float(cost),
            "uncertainty_along_path": uncertainty_along_path,
            "safety_margin": float(safety_margin),
        }

    def _a_star_search(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        gp_mean: np.ndarray,
        gp_variance: np.ndarray,
        uncertainty_weight: float,
        grid_size: int,
    ) -> Optional[list[tuple[int, int]]]:
        """A*搜索算法，代价函数融合GP均值与方差."""
        import heapq

        open_set: list[tuple[float, int, tuple[int, int]]] = []
        counter = 0
        heapq.heappush(open_set, (0.0, counter, start))

        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = {start: 0.0}

        neighbors_8 = [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        ]

        iterations = 0
        while open_set and iterations < self.max_iterations:
            iterations += 1
            _, _, current = heapq.heappop(open_set)

            if current == goal:
                return self._reconstruct_path(came_from, current)

            for di, dj in neighbors_8:
                ni, nj = current[0] + di, current[1] + dj
                neighbor = (ni, nj)

                if not (0 <= ni < grid_size and 0 <= nj < grid_size):
                    continue

                move_cost = self.diagonal_cost if abs(di) + abs(dj) == 2 else 1.0
                mean_cost = float(gp_mean[ni, nj])
                var_cost = float(gp_variance[ni, nj])
                edge_cost = move_cost + uncertainty_weight * var_cost + 0.1 * mean_cost

                tentative_g = g_score[current] + edge_cost

                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = np.sqrt(
                        (ni - goal[0]) ** 2 + (nj - goal[1]) ** 2,
                    )
                    f = tentative_g + h
                    counter += 1
                    heapq.heappush(open_set, (f, counter, neighbor))

        return None

    def _reconstruct_path(
        self,
        came_from: dict[tuple[int, int], tuple[int, int]],
        current: tuple[int, int],
    ) -> list[tuple[int, int]]:
        """从came_from字典重建路径."""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def _straight_line_path(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
    ) -> list[tuple[int, int]]:
        """直线回退路径生成."""
        n_steps = max(abs(goal[0] - start[0]), abs(goal[1] - start[1]), 1)
        path = []
        for i in range(n_steps + 1):
            t = i / n_steps
            x = int(round(start[0] + t * (goal[0] - start[0])))
            y = int(round(start[1] + t * (goal[1] - start[1])))
            path.append((x, y))
        return path

    def _compute_path_cost(
        self,
        path: list[tuple[int, int]],
        gp_mean: np.ndarray,
        gp_variance: np.ndarray,
        uncertainty_weight: float,
    ) -> float:
        """计算路径总代价."""
        total_cost = 0.0
        for i in range(len(path)):
            r, c = path[i]
            r = min(r, gp_mean.shape[0] - 1)
            c = min(c, gp_mean.shape[1] - 1)
            mean_val = float(gp_mean[r, c])
            var_val = float(gp_variance[r, c])
            total_cost += 0.1 * mean_val + uncertainty_weight * var_val
            if i > 0:
                dr = abs(path[i][0] - path[i - 1][0])
                dc = abs(path[i][1] - path[i - 1][1])
                total_cost += self.diagonal_cost if dr + dc == 2 else 1.0
        return total_cost

    def _extract_uncertainty(
        self,
        path: list[tuple[int, int]],
        gp_variance: np.ndarray,
    ) -> list[float]:
        """提取路径上各点的不确定性值."""
        uncertainties = []
        for r, c in path:
            r = min(r, gp_variance.shape[0] - 1)
            c = min(c, gp_variance.shape[1] - 1)
            uncertainties.append(float(gp_variance[r, c]))
        return uncertainties

    def _compute_safety_margin(
        self,
        uncertainty_along_path: list[float],
    ) -> float:
        """计算安全裕度，基于路径上最大不确定性的倒数."""
        if not uncertainty_along_path:
            return 1.0
        max_uncertainty = max(uncertainty_along_path)
        mean_uncertainty = float(np.mean(uncertainty_along_path))
        safety = 1.0 / (1.0 + max_uncertainty + 0.5 * mean_uncertainty)
        return float(np.clip(safety, 0.0, 1.0))
