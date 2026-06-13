"""风险感知A*路径规划算法。

在经典A*搜索算法基础上融入风险场评估，代价函数综合考虑
距离代价与风险代价加权，生成在风险环境中更安全的路径。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class RiskAwareAStar:
    """风险感知A*路径规划器。

    在A*算法的基础上引入风险场评估，节点扩展时代价函数为：
        f(n) = g(n) + h(n) + risk_weight * risk(n)
    其中 risk(n) 为该节点在风险场中的风险值，risk_weight 控制风险
    在总代价中的权重。规划完成后输出路径的风险暴露分析。

    Args:
        config: 配置字典，支持以下参数：
            - risk_weight: 风险权重系数，默认0.3
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.risk_weight: float = self.config.get("risk_weight", 0.3)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行风险感知A*路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 [x, y]
                - goal: 终点坐标 [x, y]
                - grid_size: 网格尺寸 [rows, cols]
                - obstacles: 障碍物列表 list[list[int]]
                - risk_field: 风险场矩阵（二维数组，值域[0,1]），可选
                - risk_weight: 风险权重，默认0.3

        Returns:
            包含以下键的字典：
                - path: 路径点列表
                - cost: 路径总代价
                - risk_exposure: 路径风险暴露值
                - risk_map: 路径上各点的风险分布
        """
        np.random.seed(42)

        start = params.get("start", [0, 0])
        goal = params.get("goal", [10, 10])
        grid_size = params.get("grid_size", [50, 50])
        obstacles = set(map(tuple, params.get("obstacles", [])))
        risk_weight = params.get("risk_weight", self.risk_weight)

        rows, cols = grid_size

        # 构建风险场，默认全零
        risk_field_input = params.get("risk_field", None)
        if risk_field_input is not None:
            risk_field = np.array(risk_field_input, dtype=float)
        else:
            risk_field = np.zeros((rows, cols), dtype=float)

        # 确保风险场尺寸匹配
        if risk_field.shape != (rows, cols):
            risk_field = np.zeros((rows, cols), dtype=float)

        logger.info(
            "风险感知A*规划: 起点=%s, 终点=%s, 网格=%s, 风险权重=%.2f",
            start,
            goal,
            grid_size,
            risk_weight,
        )

        start_grid = self._world_to_grid(start, rows, cols)
        goal_grid = self._world_to_grid(goal, rows, cols)

        # A*搜索
        open_set: list[tuple[float, tuple[int, int]]] = []
        heapq.heappush(open_set, (0.0, start_grid))
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = {start_grid: 0.0}

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal_grid:
                path = self._reconstruct_path(came_from, current, rows, cols)
                risk_exposure, risk_map = self._compute_risk_exposure(
                    path,
                    risk_field,
                    rows,
                    cols,
                )
                total_cost = g_score[current]
                logger.info(
                    "风险感知A*完成: 代价=%.2f, 风险暴露=%.4f",
                    total_cost,
                    risk_exposure,
                )
                return {
                    "path": path,
                    "cost": total_cost,
                    "risk_exposure": risk_exposure,
                    "risk_map": risk_map,
                }

            for neighbor in self._get_neighbors(current, rows, cols, obstacles):
                # 距离代价
                dist_cost = 1.0
                # 风险代价
                nx, ny = neighbor
                risk_cost = float(risk_field[nx, ny]) if 0 <= nx < rows and 0 <= ny < cols else 0.0
                # 综合代价
                step_cost = dist_cost + risk_weight * risk_cost
                tentative_g = g_score[current] + step_cost

                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = self._heuristic(neighbor, goal_grid)
                    risk_h = (
                        float(risk_field[goal_grid[0], goal_grid[1]])
                        if 0 <= goal_grid[0] < rows and 0 <= goal_grid[1] < cols
                        else 0.0
                    )
                    f_score = tentative_g + h + risk_weight * risk_h
                    heapq.heappush(open_set, (f_score, neighbor))

        logger.warning("风险感知A*未找到路径")
        return {
            "path": [],
            "cost": float("inf"),
            "risk_exposure": 0.0,
            "risk_map": [],
        }

    def _world_to_grid(
        self,
        pos: list,
        rows: int,
        cols: int,
    ) -> tuple[int, int]:
        """世界坐标转网格坐标。"""
        gx = int(pos[0] + rows / 2)
        gy = int(pos[1] + cols / 2)
        return (max(0, min(gx, rows - 1)), max(0, min(gy, cols - 1)))

    def _grid_to_world(
        self,
        pos: tuple[int, int],
        rows: int,
        cols: int,
    ) -> list[int]:
        """网格坐标转世界坐标。"""
        return [pos[0] - rows // 2, pos[1] - cols // 2]

    def _heuristic(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        """曼哈顿距离启发函数。"""
        return float(abs(a[0] - b[0]) + abs(a[1] - b[1]))

    def _get_neighbors(
        self,
        pos: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
    ) -> list[tuple[int, int]]:
        """获取有效邻居节点（4连通）。"""
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = pos[0] + dx, pos[1] + dy
            if 0 <= nx < rows and 0 <= ny < cols and (nx, ny) not in obstacles:
                neighbors.append((nx, ny))
        return neighbors

    def _reconstruct_path(
        self,
        came_from: dict[tuple[int, int], tuple[int, int]],
        current: tuple[int, int],
        rows: int,
        cols: int,
    ) -> list[list[int]]:
        """从目标回溯重建路径。"""
        path = [self._grid_to_world(current, rows, cols)]
        while current in came_from:
            current = came_from[current]
            path.append(self._grid_to_world(current, rows, cols))
        path.reverse()
        return path

    def _compute_risk_exposure(
        self,
        path: list[list[int]],
        risk_field: np.ndarray,
        rows: int,
        cols: int,
    ) -> tuple[float, list[float]]:
        """计算路径的风险暴露值和各点风险分布。"""
        risk_values = []
        for p in path:
            gx, gy = self._world_to_grid(p, rows, cols)
            gx = max(0, min(gx, rows - 1))
            gy = max(0, min(gy, cols - 1))
            risk_values.append(float(risk_field[gx, gy]))
        risk_exposure = float(np.mean(risk_values)) if risk_values else 0.0
        return risk_exposure, risk_values
