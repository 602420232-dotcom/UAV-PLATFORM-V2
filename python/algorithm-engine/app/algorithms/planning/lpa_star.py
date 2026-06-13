"""LPA* 增量A*路径规划算法（Lifelong Planning A*）。

A*算法的增量版本，当起点/终点或地图代价发生变化时，
利用之前的搜索结果进行增量更新，避免从头搜索。
适用于需要多次重规划的场景。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class LPAStarPlanner:
    """LPA*增量A*路径规划器。

    维护每个节点的g值和rhs值，当图发生变化时仅更新受影响节点的
    一致性状态，实现高效的增量重规划。

    Args:
        config: 配置字典，支持以下参数：
            - allow_diagonal: 是否允许对角移动，默认True
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.allow_diagonal: bool = self.config.get("allow_diagonal", True)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行LPA*路径规划。

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
            "LPA*规划: 起点=%s, 终点=%s, 网格=%s",
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
        self._start = start
        self._goal = goal

        # LPA*数据结构
        self._g: dict[tuple[int, int], float] = {}
        self._rhs: dict[tuple[int, int], float] = {goal: 0.0}
        self._U: list[tuple[float, float, tuple[int, int]]] = []

        k = self._calculate_key(goal)
        heapq.heappush(self._U, (k[0], k[1], goal))

        nodes_explored = 0

        while self._U:
            k_old = (self._U[0][0], self._U[0][1])
            u = self._U[0][2]
            k_new = self._calculate_key(u)

            if k_old >= k_new:
                if self._g.get(u, float("inf")) == self._rhs.get(u, float("inf")):
                    heapq.heappop(self._U)
                    continue

                heapq.heappop(self._U)
                self._g[u] = self._rhs.get(u, float("inf"))
                nodes_explored += 1

                for pred in self._get_neighbors(u):
                    self._update_vertex(pred)
            else:
                # 更新key
                heapq.heappop(self._U)
                heapq.heappush(self._U, (k_new[0], k_new[1], u))

            # 终止条件
            start_g = self._g.get(start, float("inf"))
            start_rhs = self._rhs.get(start, float("inf"))
            if start_g == start_rhs:
                if not self._U or self._top_key() >= self._calculate_key(start):
                    break

        cost = self._g.get(start, float("inf"))
        if cost >= float("inf"):
            logger.warning("LPA*未找到路径")
            return {
                "path": [],
                "cost": float("inf"),
                "nodes_explored": nodes_explored,
            }

        path = self._extract_path(start, goal)

        logger.info(
            "LPA*完成: 代价=%.2f, 探索节点=%d",
            cost, nodes_explored,
        )
        return {
            "path": path,
            "cost": cost,
            "nodes_explored": nodes_explored,
        }

    def _calculate_key(self, s: tuple[int, int]) -> tuple[float, float]:
        """计算节点优先级键值。"""
        g = self._g.get(s, float("inf"))
        rhs = self._rhs.get(s, float("inf"))
        h = self._heuristic(s, self._start)
        return (min(g, rhs) + h, min(g, rhs))

    def _top_key(self) -> tuple[float, float]:
        """获取优先队列顶部键值。"""
        if self._U:
            return (self._U[0][0], self._U[0][1])
        return (float("inf"), float("inf"))

    def _update_vertex(self, u: tuple[int, int]) -> None:
        """更新节点的rhs值和队列状态。"""
        if u != self._goal:
            min_rhs = float("inf")
            for succ in self._get_neighbors(u):
                cost = self._edge_cost(u, succ) + self._g.get(succ, float("inf"))
                if cost < min_rhs:
                    min_rhs = cost
            self._rhs[u] = min_rhs

        # 移除旧条目
        self._U = [(k1, k2, s) for k1, k2, s in self._U if s != u]
        heapq.heapify(self._U)

        g = self._g.get(u, float("inf"))
        rhs = self._rhs.get(u, float("inf"))
        if g != rhs:
            k = self._calculate_key(u)
            heapq.heappush(self._U, (k[0], k[1], u))

    def _edge_cost(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        """计算边代价。"""
        dx = abs(b[0] - a[0])
        dy = abs(b[1] - a[1])
        return 1.414 if dx + dy == 2 else 1.0

    def _heuristic(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        """曼哈顿距离启发式。"""
        return float(abs(a[0] - b[0]) + abs(a[1] - b[1]))

    def _get_neighbors(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
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

    def _extract_path(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
    ) -> list[list[int]]:
        """从g值提取路径。"""
        path = [list(start)]
        current = start
        visited = {current}
        max_steps = self._rows * self._cols

        for _ in range(max_steps):
            if current == goal:
                break

            best_neighbor = None
            best_cost = float("inf")
            for neighbor in self._get_neighbors(current):
                if neighbor not in visited:
                    cost = self._g.get(neighbor, float("inf"))
                    if cost < best_cost:
                        best_cost = cost
                        best_neighbor = neighbor

            if best_neighbor is None:
                break

            path.append(list(best_neighbor))
            visited.add(best_neighbor)
            current = best_neighbor

        return path
