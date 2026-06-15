"""边界搜索（Fringe Search）路径规划算法。

介于Dijkstra和A*之间的高效搜索算法。使用类似BFS的FIFO队列
替代优先队列，通过延迟节点更新策略避免重复处理。
时间复杂度与A*相当，但避免了堆操作开销，实际运行更快。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class FringeSearchPlanner:
    """边界搜索路径规划器。

    使用FIFO容器和延迟更新策略的图搜索算法。
    节点仅在从容器中取出时才更新g值，避免重复处理。
    在均匀代价网格上效率接近BFS，在加权图上效率接近Dijkstra。

    Args:
        config: 配置字典，支持以下参数：
            - allow_diagonal: 是否允许对角移动，默认True
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.allow_diagonal: bool = self.config.get("allow_diagonal", True)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行边界搜索路径规划。

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
            "边界搜索: 起点=%s, 终点=%s, 网格=%s",
            start,
            goal,
            grid_size,
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

        # Fringe Search核心数据结构
        # 使用列表模拟FIFO容器，配合containing集合实现延迟更新
        g_score: dict[tuple[int, int], float] = {start: 0.0}
        parent: dict[tuple[int, int], tuple[int, int] | None] = {start: None}
        containing: set[tuple[int, int]] = {start}
        fringe: list[tuple[int, int]] = [start]
        nodes_explored = 0

        # Fringe边界值：用于判断节点是否需要延迟处理
        fringe_boundary = 0.0

        while fringe:
            current = fringe.pop(0)
            containing.discard(current)

            # 延迟更新：如果当前g值大于记录值，跳过
            if g_score[current] > fringe_boundary:
                continue

            nodes_explored += 1

            if current == goal:
                path = self._reconstruct_path(parent, current)
                cost = g_score[current]
                logger.info(
                    "边界搜索完成: 代价=%.2f, 探索节点=%d",
                    cost,
                    nodes_explored,
                )
                return {
                    "path": path,
                    "cost": cost,
                    "nodes_explored": nodes_explored,
                }

            for neighbor in self._get_neighbors(current):
                edge_cost = self._edge_cost(current, neighbor)
                new_g = g_score[current] + edge_cost

                if new_g < g_score.get(neighbor, float("inf")):
                    g_score[neighbor] = new_g
                    parent[neighbor] = current

                    if neighbor not in containing:
                        containing.add(neighbor)
                        fringe.append(neighbor)

        logger.warning("边界搜索未找到路径")
        return {
            "path": [],
            "cost": float("inf"),
            "nodes_explored": nodes_explored,
        }

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
        parent: dict,
        current: tuple[int, int],
    ) -> list[list[int]]:
        """重建路径。"""
        path = [list(current)]
        while parent.get(current) is not None:
            current = parent[current]
            path.append(list(current))
        path.reverse()
        return path
