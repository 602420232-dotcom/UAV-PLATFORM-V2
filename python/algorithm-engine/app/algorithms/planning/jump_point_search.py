"""跳点搜索路径规划算法（Jump Point Search）。

A*算法的网格优化变体，通过对称性剪枝大幅减少搜索节点数。
在无障碍物的开放区域中，只保留"跳点"（强制邻居和自然邻居的交点），
从而加速搜索过程。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class JumpPointSearchPlanner:
    """跳点搜索路径规划器。

    通过识别网格中的对称路径并跳过冗余节点，仅扩展跳点，
    在无障碍区域中搜索效率远高于标准A*。

    Args:
        config: 配置字典，支持以下参数：
            - allow_diagonal: 是否允许对角移动，默认True
    """

    CARDINAL = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    DIAGONAL = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    ALL_DIRS = CARDINAL + DIAGONAL

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.allow_diagonal: bool = self.config.get("allow_diagonal", True)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行跳点搜索路径规划。

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
            "跳点搜索: 起点=%s, 终点=%s, 网格=%s",
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
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = {start: 0.0}
        nodes_explored = 0

        while open_set:
            _, current = heapq.heappop(open_set)
            nodes_explored += 1

            if current == goal:
                path = self._reconstruct_path(came_from, current)
                cost = g_score[current]
                logger.info(
                    "跳点搜索完成: 代价=%.2f, 探索节点=%d",
                    cost, nodes_explored,
                )
                return {
                    "path": path,
                    "cost": cost,
                    "nodes_explored": nodes_explored,
                }

            # 识别邻居方向
            for dx, dy in self.ALL_DIRS:
                jump_point = self._jump(current, (dx, dy), goal)
                if jump_point is not None:
                    new_g = g_score[current] + self._jump_cost(current, jump_point)
                    if new_g < g_score.get(jump_point, float("inf")):
                        g_score[jump_point] = new_g
                        came_from[jump_point] = current
                        f = new_g + self._heuristic(jump_point, goal)
                        heapq.heappush(open_set, (f, jump_point))

        logger.warning("跳点搜索未找到路径")
        return {
            "path": [],
            "cost": float("inf"),
            "nodes_explored": nodes_explored,
        }

    def _jump(
        self,
        current: tuple[int, int],
        direction: tuple[int, int],
        goal: tuple[int, int],
    ) -> tuple[int, int] | None:
        """沿方向跳转，返回下一个跳点或None。"""
        dx, dy = direction
        nx, ny = current[0] + dx, current[1] + dy

        # 边界和障碍物检查
        if not (0 <= nx < self._rows and 0 <= ny < self._cols):
            return None
        if (nx, ny) in self._obstacles:
            return None

        # 到达目标
        if (nx, ny) == goal:
            return (nx, ny)

        # 对角移动的特殊处理
        if abs(dx) + abs(dy) == 2:
            # 检查是否有强制邻居（对角方向两侧被阻挡）
            if (self._is_blocked((nx, ny), (dx, 0))
                    or self._is_blocked((nx, ny), (0, dy))):
                return (nx, ny)

            # 递归检查正交方向
            for ortho_dx, ortho_dy in [(dx, 0), (0, dy)]:
                result = self._jump((nx, ny), (ortho_dx, ortho_dy), goal)
                if result is not None:
                    return (nx, ny)
        else:
            # 正交移动：检查是否有强制邻居
            if dx != 0:
                if (self._is_blocked((nx, ny), (dx, -1))
                        or self._is_blocked((nx, ny), (dx, 1))):
                    return (nx, ny)
            else:
                if (self._is_blocked((nx, ny), (-1, dy))
                        or self._is_blocked((nx, ny), (1, dy))):
                    return (nx, ny)

        # 继续跳转
        return self._jump((nx, ny), direction, goal)

    def _is_blocked(
        self,
        pos: tuple[int, int],
        direction: tuple[int, int],
    ) -> bool:
        """检查某方向是否被障碍物阻挡。"""
        nx, ny = pos[0] + direction[0], pos[1] + direction[1]
        if not (0 <= nx < self._rows and 0 <= ny < self._cols):
            return True
        return (nx, ny) in self._obstacles

    def _jump_cost(
        self,
        a: tuple[int, int],
        b: tuple[int, int],
    ) -> float:
        """计算跳转代价。"""
        dx = abs(b[0] - a[0])
        dy = abs(b[1] - a[1])
        if dx + dy == 2:
            return 1.414
        return float(max(dx, dy))

    def _heuristic(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        """八方向切比雪夫/对角距离启发式。"""
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return max(dx, dy) + (1.414 - 1.0) * min(dx, dy)

    def _reconstruct_path(
        self,
        came_from: dict,
        current: tuple[int, int],
    ) -> list[list[int]]:
        """重建路径，并在跳点之间插值。"""
        path_nodes = [current]
        while current in came_from:
            current = came_from[current]
            path_nodes.append(current)
        path_nodes.reverse()

        # 在跳点之间进行直线插值
        full_path = [list(path_nodes[0])]
        for i in range(1, len(path_nodes)):
            full_path.extend(self._interpolate(path_nodes[i - 1], path_nodes[i])[1:])
        return full_path

    def _interpolate(
        self,
        a: tuple[int, int],
        b: tuple[int, int],
    ) -> list[list[int]]:
        """在两点之间进行直线插值。"""
        points = [list(a)]
        dx = int(np.sign(b[0] - a[0]))
        dy = int(np.sign(b[1] - a[1]))
        x, y = a
        while (x, y) != b:
            x += dx
            y += dy
            points.append([x, y])
        return points
