"""懒Theta* 路径规划算法（Lazy Theta*）。

Theta*的优化变体，延迟视线检查到节点从开放列表取出时才执行，
而非在扩展时立即检查。减少了不必要的视线计算，提高效率。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class LazyThetaStarPlanner:
    """懒Theta*路径规划器。

    与Theta*的区别在于：在节点扩展时假设parent到neighbor的视线
    可行并更新代价，仅在节点从open_set弹出时才验证视线。
    如果视线不通过则回退到标准A*的代价。

    Args:
        config: 配置字典，支持以下参数：
            - allow_diagonal: 是否允许对角移动，默认True
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.allow_diagonal: bool = self.config.get("allow_diagonal", True)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行懒Theta*路径规划。

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
            "懒Theta*规划: 起点=%s, 终点=%s, 网格=%s",
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
                    "懒Theta*完成: 代价=%.2f, 探索节点=%d",
                    cost,
                    nodes_explored,
                )
                return {
                    "path": path,
                    "cost": cost,
                    "nodes_explored": nodes_explored,
                }

            parent = came_from[current]

            # 懒检查：弹出时才验证视线
            if not self._line_of_sight(parent, current):
                # 视线不通过，回退到A*方式
                # 找到current在came_from中记录的parent的邻居中最优的
                best_g = float("inf")
                best_parent = current
                for neighbor in self._get_neighbors(parent):
                    if neighbor in g_score:
                        ng = g_score[neighbor] + self._distance(neighbor, current)
                        if ng < best_g:
                            best_g = ng
                            best_parent = neighbor
                came_from[current] = best_parent
                g_score[current] = best_g

            for neighbor in self._get_neighbors(current):
                if neighbor in closed:
                    continue

                # 假设视线可行（懒检查）
                new_g = g_score[parent] + self._distance(parent, neighbor)
                new_parent = parent

                # 同时计算A*方式的代价
                a_star_g = g_score[current] + self._distance(current, neighbor)
                if a_star_g < new_g:
                    new_g = a_star_g
                    new_parent = current

                if new_g < g_score.get(neighbor, float("inf")):
                    g_score[neighbor] = new_g
                    came_from[neighbor] = new_parent
                    f = new_g + self._heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f, neighbor))

        logger.warning("懒Theta*未找到路径")
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
        """Bresenham视线检查。"""
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
        while came_from.get(current) != current:
            current = came_from[current]
            path.append(list(current))
        path.reverse()
        return path
