"""束搜索（Beam Search）路径规划算法。

限制搜索宽度的启发式搜索算法。在每一步仅保留代价最优的
beam_width个候选节点进行扩展，大幅减少搜索空间。
牺牲完备性换取计算效率，适用于实时规划场景。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class BeamSearchPlanner:
    """束搜索路径规划器。

    在每轮扩展中仅保留beam_width个最优候选节点，
    通过限制搜索宽度来控制计算量。适用于需要快速获得
    近似最优解的实时规划场景。

    Args:
        config: 配置字典，支持以下参数：
            - beam_width: 束宽度，每轮保留的候选节点数，默认20
            - allow_diagonal: 是否允许对角移动，默认True
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.beam_width: int = self.config.get("beam_width", 20)
        self.allow_diagonal: bool = self.config.get("allow_diagonal", True)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行束搜索路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]

        Returns:
            包含 path（路径点列表）和 cost（路径代价）的字典。
        """
        np.random.seed(42)

        _start = params.get("start", (0, 0))
        start: tuple[int, int] = (int(_start[0]), int(_start[1]))
        _goal = params.get("goal", (10, 10))
        goal: tuple[int, int] = (int(_goal[0]), int(_goal[1]))
        grid_size = params.get("grid_size", (50, 50))
        obstacles = set(map(tuple, params.get("obstacles", [])))

        logger.info(
            "束搜索: 起点=%s, 终点=%s, 束宽度=%d",
            start,
            goal,
            self.beam_width,
        )

        rows, cols = grid_size

        if start == goal:
            return {"path": [list(start)], "cost": 0.0, "nodes_explored": 0}

        if start in obstacles or goal in obstacles:
            logger.warning("起点或终点在障碍物上")
            return {"path": [], "cost": float("inf"), "nodes_explored": 0}

        self._rows = rows
        self._cols = cols
        self._obstacles = obstacles

        # 束搜索核心：使用优先队列，但限制每轮扩展的节点数
        g_score: dict[tuple[int, int], float] = {start: 0.0}
        came_from: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
        closed: set[tuple[int, int]] = set()
        nodes_explored = 0

        # 初始候选集
        candidates: list[tuple[float, tuple[int, int]]] = [
            (self._heuristic(start, goal), start)
        ]

        while candidates:
            # 按f值排序，取前beam_width个
            candidates.sort(key=lambda x: x[0])
            candidates = candidates[: self.beam_width]

            # 生成所有候选节点的邻居
            next_candidates: list[tuple[float, tuple[int, int]]] = []
            current_batch = list(candidates)
            candidates = []

            for _, current in current_batch:
                if current in closed:
                    continue

                closed.add(current)
                nodes_explored += 1

                if current == goal:
                    path = self._reconstruct_path(came_from, current)
                    cost = g_score[current]
                    logger.info(
                        "束搜索完成: 代价=%.2f, 探索节点=%d",
                        cost,
                        nodes_explored,
                    )
                    return {
                        "path": path,
                        "cost": cost,
                        "nodes_explored": nodes_explored,
                    }

                for neighbor in self._get_neighbors(current):
                    if neighbor in closed:
                        continue

                    edge_cost = self._edge_cost(current, neighbor)
                    new_g = g_score[current] + edge_cost

                    if new_g < g_score.get(neighbor, float("inf")):
                        g_score[neighbor] = new_g
                        came_from[neighbor] = current
                        f = new_g + self._heuristic(neighbor, goal)
                        next_candidates.append((f, neighbor))

            # 合并新候选节点
            candidates = next_candidates

        logger.warning("束搜索未找到路径")
        return {
            "path": [],
            "cost": float("inf"),
            "nodes_explored": nodes_explored,
        }

    def _heuristic(
        self,
        a: tuple[int, int],
        b: tuple[int, int],
    ) -> float:
        """欧几里得距离启发式。"""
        return float(np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))

    def _edge_cost(
        self,
        a: tuple[int, int],
        b: tuple[int, int],
    ) -> float:
        """计算边代价。"""
        dx = abs(b[0] - a[0])
        dy = abs(b[1] - a[1])
        return 1.414 if dx + dy == 2 else 1.0

    def _get_neighbors(
        self,
        pos: tuple[int, int],
    ) -> list[tuple[int, int]]:
        """获取可行邻居节点。"""
        if self.allow_diagonal:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        neighbors = []
        for dx, dy in directions:
            nx, ny = pos[0] + dx, pos[1] + dy
            if 0 <= nx < self._rows and 0 <= ny < self._cols and (nx, ny) not in self._obstacles:
                neighbors.append((nx, ny))
        return neighbors

    def _reconstruct_path(
        self,
        came_from: dict,
        current: tuple[int, int],
    ) -> list[list[int]]:
        """重建路径。"""
        path = [list(current)]
        while came_from.get(current) is not None:
            current = came_from[current]
            path.append(list(current))
        path.reverse()
        return path
