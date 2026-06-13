"""Theta* 任意角度路径规划算法。

A*算法的变体，允许路径沿任意角度行进而不仅限于网格方向。
通过视线检查（Line-of-Sight）跳过中间节点，生成更短更平滑的路径。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ThetaStarPlanner:
    """Theta* 任意角度路径规划器。

    在A*基础上，当扩展邻居节点时检查从当前节点的父节点到邻居的
    直线是否无障碍。如果可行则直接连接，跳过当前节点，从而
    生成任意角度的更短路径。

    Args:
        config: 配置字典，支持以下参数：
            - allow_diagonal: 是否允许对角移动，默认True
            - line_of_sight_resolution: 视线检查分辨率，默认0.5
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.allow_diagonal: bool = self.config.get("allow_diagonal", True)
        self.los_resolution: float = self.config.get("line_of_sight_resolution", 0.5)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行Theta*路径规划。

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

        start = tuple(params.get("start", (0, 0)))
        goal = tuple(params.get("goal", (10, 10)))
        grid_size = params.get("grid_size", (50, 50))
        obstacles = set(map(tuple, params.get("obstacles", [])))

        logger.info(
            "Theta*规划: 起点=%s, 终点=%s, 网格=%s",
            start, goal, grid_size,
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

        open_set: list[tuple[float, tuple[int, int]]] = []
        heapq.heappush(open_set, (self._heuristic(start, goal), start))
        came_from: dict[tuple[int, int], tuple[int, int]] = {start: start}
        g_score: dict[tuple[int, int], float] = {start: 0.0}
        closed: set[tuple[int, int]] = set()
        nodes_explored = 0

        while open_set:
            _, current = heapq.heappop(open_set)

            if current in closed:
                continue
            closed.add(current)
            nodes_explored += 1

            if current == goal:
                path = self._reconstruct_path(came_from, current)
                cost = g_score[current]
                logger.info(
                    "Theta*完成: 代价=%.2f, 探索节点=%d",
                    cost, nodes_explored,
                )
                return {
                    "path": path,
                    "cost": cost,
                    "nodes_explored": nodes_explored,
                }

            parent = came_from[current]
            for neighbor in self._get_neighbors(current):
                if neighbor in closed:
                    continue

                # Theta*核心：检查parent到neighbor的视线
                if self._line_of_sight(parent, neighbor):
                    new_g = g_score[parent] + self._distance(parent, neighbor)
                    new_parent = parent
                else:
                    new_g = g_score[current] + self._distance(current, neighbor)
                    new_parent = current

                if new_g < g_score.get(neighbor, float("inf")):
                    g_score[neighbor] = new_g
                    came_from[neighbor] = new_parent
                    f = new_g + self._heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f, neighbor))

        logger.warning("Theta*未找到路径")
        return {
            "path": [],
            "cost": float("inf"),
            "nodes_explored": nodes_explored,
        }

    def _line_of_sight(
        self,
        a: tuple[int, int],
        b: tuple[int, int],
    ) -> bool:
        """Bresenham视线检查：判断两点之间是否有障碍物阻挡。"""
        x0, y0 = a
        x1, y1 = b
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            if (x0, y0) in self._obstacles:
                return False
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

        return True

    def _distance(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        """欧几里得距离。"""
        return float(np.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2))

    def _heuristic(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        """欧几里得距离启发式。"""
        return self._distance(a, b)

    def _get_neighbors(
        self, pos: tuple[int, int],
    ) -> list[tuple[int, int]]:
        """获取可行邻居节点。"""
        if self.allow_diagonal:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                          (-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        neighbors = []
        for dx, dy in directions:
            nx, ny = pos[0] + dx, pos[1] + dy
            if (0 <= nx < self._rows and 0 <= ny < self._cols
                    and (nx, ny) not in self._obstacles):
                neighbors.append((nx, ny))
        return neighbors

    def _reconstruct_path(
        self,
        came_from: dict,
        current: tuple[int, int],
    ) -> list[list[int]]:
        """重建路径。"""
        path = [list(current)]
        while came_from.get(current) != current:
            current = came_from[current]
            path.append(list(current))
        path.reverse()
        return path
