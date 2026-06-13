"""双向A*搜索路径规划算法。

从起点和终点同时进行A*搜索，当两个搜索树相遇时合并路径。
相比单向A*，通常能显著减少搜索空间和计算时间。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class BidirectionalAStarPlanner:
    """双向A*搜索路径规划器。

    同时从起点和终点执行A*搜索，当两个搜索前沿在某个节点相遇时，
    合并两条路径得到完整解。搜索空间约为单向A*的一半。

    Args:
        config: 配置字典，支持以下参数：
            - allow_diagonal: 是否允许对角移动，默认True
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.allow_diagonal: bool = self.config.get("allow_diagonal", True)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行双向A*搜索路径规划。

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

        raw_start = params.get("start", (0, 0))
        raw_goal = params.get("goal", (10, 10))
        start: tuple[int, int] = (int(raw_start[0]), int(raw_start[1]))
        goal: tuple[int, int] = (int(raw_goal[0]), int(raw_goal[1]))
        grid_size = params.get("grid_size", (50, 50))
        obstacles = set(map(tuple, params.get("obstacles", [])))

        logger.info(
            "双向A*搜索: 起点=%s, 终点=%s, 网格=%s",
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

        # 前向搜索（从起点出发）
        fwd_open: list[tuple[float, tuple[int, int]]] = []
        heapq.heappush(fwd_open, (self._heuristic(start, goal), start))
        fwd_g: dict[tuple[int, int], float] = {start: 0.0}
        fwd_parent: dict[tuple[int, int], tuple[int, int]] = {}

        # 反向搜索（从终点出发）
        bwd_open: list[tuple[float, tuple[int, int]]] = []
        heapq.heappush(bwd_open, (self._heuristic(goal, start), goal))
        bwd_g: dict[tuple[int, int], float] = {goal: 0.0}
        bwd_parent: dict[tuple[int, int], tuple[int, int]] = {}

        fwd_visited: set[tuple[int, int]] = set()
        bwd_visited: set[tuple[int, int]] = set()
        nodes_explored = 0

        meeting_node: tuple[int, int] | None = None
        best_cost = float("inf")

        while fwd_open and bwd_open:
            # 前向搜索一步
            if fwd_open:
                _, fwd_current = heapq.heappop(fwd_open)
                if fwd_current not in fwd_visited:
                    fwd_visited.add(fwd_current)
                    nodes_explored += 1

                    if fwd_current in bwd_visited:
                        total_cost = fwd_g[fwd_current] + bwd_g[fwd_current]
                        if total_cost < best_cost:
                            best_cost = total_cost
                            meeting_node = fwd_current

                    for neighbor in self._get_neighbors(fwd_current, rows, cols, obstacles):
                        tentative_g = fwd_g[fwd_current] + self._edge_cost(fwd_current, neighbor)
                        if tentative_g < fwd_g.get(neighbor, float("inf")):
                            fwd_g[neighbor] = tentative_g
                            fwd_parent[neighbor] = fwd_current
                            f = tentative_g + self._heuristic(neighbor, goal)
                            heapq.heappush(fwd_open, (f, neighbor))

            # 反向搜索一步
            if bwd_open:
                _, bwd_current = heapq.heappop(bwd_open)
                if bwd_current not in bwd_visited:
                    bwd_visited.add(bwd_current)
                    nodes_explored += 1

                    if bwd_current in fwd_visited:
                        total_cost = fwd_g[bwd_current] + bwd_g[bwd_current]
                        if total_cost < best_cost:
                            best_cost = total_cost
                            meeting_node = bwd_current

                    for neighbor in self._get_neighbors(bwd_current, rows, cols, obstacles):
                        tentative_g = bwd_g[bwd_current] + self._edge_cost(bwd_current, neighbor)
                        if tentative_g < bwd_g.get(neighbor, float("inf")):
                            bwd_g[neighbor] = tentative_g
                            bwd_parent[neighbor] = bwd_current
                            f = tentative_g + self._heuristic(neighbor, start)
                            heapq.heappush(bwd_open, (f, neighbor))

            # 如果找到会合点且最优代价已确定
            if meeting_node is not None:
                min_fwd_f = fwd_open[0][0] if fwd_open else float("inf")
                min_bwd_f = bwd_open[0][0] if bwd_open else float("inf")
                if min_fwd_f + min_bwd_f >= best_cost:
                    break

        if meeting_node is None:
            logger.warning("双向A*搜索未找到路径")
            return {
                "path": [],
                "cost": float("inf"),
                "nodes_explored": nodes_explored,
            }

        # 合并路径
        fwd_path = self._reconstruct_path(fwd_parent, meeting_node, start)
        bwd_path = self._reconstruct_path(bwd_parent, meeting_node, goal)
        bwd_path.reverse()
        full_path = fwd_path + bwd_path[1:]  # 去掉重复的会合点

        logger.info(
            "双向A*搜索完成: 代价=%.2f, 探索节点=%d",
            best_cost,
            nodes_explored,
        )
        return {
            "path": full_path,
            "cost": best_cost,
            "nodes_explored": nodes_explored,
        }

    def _heuristic(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        """曼哈顿距离启发式。"""
        return float(abs(a[0] - b[0]) + abs(a[1] - b[1]))

    def _edge_cost(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        """计算边代价。"""
        dx = abs(b[0] - a[0])
        dy = abs(b[1] - a[1])
        return 1.414 if dx + dy == 2 else 1.0

    def _get_neighbors(
        self,
        pos: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
    ) -> list[tuple[int, int]]:
        """获取可行邻居节点。"""
        if self.allow_diagonal:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        neighbors = []
        for dx, dy in directions:
            nx, ny = pos[0] + dx, pos[1] + dy
            if 0 <= nx < rows and 0 <= ny < cols and (nx, ny) not in obstacles:
                neighbors.append((nx, ny))
        return neighbors

    def _reconstruct_path(
        self,
        parent: dict,
        current: tuple[int, int],
        origin: tuple[int, int],
    ) -> list[list[int]]:
        """重建从origin到current的路径。"""
        path = [list(current)]
        while current in parent:
            current = parent[current]
            path.append(list(current))
        path.reverse()
        return path
