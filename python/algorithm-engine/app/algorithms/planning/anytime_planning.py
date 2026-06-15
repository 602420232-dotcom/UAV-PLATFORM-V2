"""任意时间规划（Anytime Planning）算法。

一种可以在任意时刻中断并返回当前最优解的规划方法。
随着计算时间的增加，解的质量逐步提高。
适用于计算资源有限或需要快速响应的场景。
"""

from __future__ import annotations

import heapq
import logging
import time
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class AnytimePlanner:
    """任意时间路径规划器。

    基于ARA*（Anytime Repairing A*）的任意时间规划算法。
    初始使用较大权重快速获得次优解，然后逐步减小权重
    重规划，不断提高解的质量。可在任意时刻返回当前最优解。

    Args:
        config: 配置字典，支持以下参数：
            - initial_weight: 初始启发式权重，默认5.0
            - weight_decrement: 每轮权重减少量，默认0.5
            - min_weight: 最小权重，默认1.0
            - max_time: 最大计算时间（秒），默认10.0
            - allow_diagonal: 是否允许对角移动，默认True
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.initial_weight: float = self.config.get("initial_weight", 5.0)
        self.weight_decrement: float = self.config.get("weight_decrement", 0.5)
        self.min_weight: float = self.config.get("min_weight", 1.0)
        self.max_time: float = self.config.get("max_time", 10.0)
        self.allow_diagonal: bool = self.config.get("allow_diagonal", True)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行任意时间路径规划。

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
            "任意时间规划: 起点=%s, 终点=%s, 初始权重=%.1f",
            start,
            goal,
            self.initial_weight,
        )

        rows, cols = grid_size

        if start == goal:
            return {"path": [list(start)], "cost": 0.0, "nodes_explored": 0}

        self._rows = rows
        self._cols = cols
        self._obstacles = obstacles

        start_time = time.time()
        weight = self.initial_weight
        best_path = []
        best_cost = float("inf")
        total_explored = 0
        rounds = 0

        while weight >= self.min_weight:
            # 检查时间限制
            if time.time() - start_time > self.max_time:
                logger.info("任意时间规划: 达到时间限制")
                break

            rounds += 1
            # 加权A*搜索
            result = self._weighted_astar(start, goal, weight)

            if result["path"]:
                new_cost = result["cost"]
                total_explored += result["nodes_explored"]

                if new_cost < best_cost:
                    best_cost = new_cost
                    best_path = result["path"]
                    logger.debug(
                        "轮次 %d: 权重=%.1f, 代价=%.2f, 探索=%d",
                        rounds,
                        weight,
                        new_cost,
                        result["nodes_explored"],
                    )

            # 减小权重
            weight -= self.weight_decrement

        elapsed = time.time() - start_time

        if best_path:
            logger.info(
                "任意时间规划完成: 代价=%.2f, 轮次=%d, 探索=%d, 耗时=%.3fs",
                best_cost,
                rounds,
                total_explored,
                elapsed,
            )
        else:
            logger.warning("任意时间规划未找到路径")

        return {
            "path": best_path,
            "cost": best_cost,
            "nodes_explored": total_explored,
            "rounds": rounds,
            "elapsed_time": elapsed,
            "final_weight": weight + self.weight_decrement,
        }

    def _weighted_astar(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        weight: float,
    ) -> dict[str, Any]:
        """加权A*搜索。"""
        open_set: list[tuple[float, tuple[int, int]]] = []
        h0 = self._heuristic(start, goal) * weight
        heapq.heappush(open_set, (h0, start))
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
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
                return {
                    "path": path,
                    "cost": g_score[current],
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
                    f = new_g + weight * self._heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f, neighbor))

        return {"path": [], "cost": float("inf"), "nodes_explored": nodes_explored}

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
        while current in came_from:
            current = came_from[current]
            path.append(list(current))
        path.reverse()
        return path
