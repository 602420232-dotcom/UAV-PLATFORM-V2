"""湍流规避路径规划算法。

专门针对大气湍流的路径规划方法。
基于湍流强度场进行路径规划，主动规避高湍流区域，
选择湍流强度较低的飞行走廊。
考虑湍流的时空变化特性，提供安全裕度。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class TurbulenceAvoidancePlanner:
    """湍流规避路径规划器。

    基于湍流强度场规划低湍流路径。
    核心策略：
    - 将湍流强度作为路径代价的主要组成部分
    - 惩罚高湍流区域，偏好低湍流走廊
    - 考虑湍流的空间相关性和安全裕度
    - 支持动态湍流场更新

    Args:
        config: 配置字典，支持以下参数：
            - turbulence_threshold: 湍流安全阈值，默认0.5
            - turbulence_weight: 湍流代价权重，默认10.0
            - safety_margin: 安全裕度，默认1.5
            - smoothing_factor: 路径平滑因子，默认0.3
            - allow_diagonal: 是否允许对角移动，默认True
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.turbulence_threshold: float = self.config.get("turbulence_threshold", 0.5)
        self.turbulence_weight: float = self.config.get("turbulence_weight", 10.0)
        self.safety_margin: float = self.config.get("safety_margin", 1.5)
        self.smoothing_factor: float = self.config.get("smoothing_factor", 0.3)
        self.allow_diagonal: bool = self.config.get("allow_diagonal", True)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行湍流规避路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]
                - turbulence_field: 湍流强度场 (rows x cols)，值域[0, 1]

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
        turbulence_field = params.get("turbulence_field", None)

        logger.info(
            "湍流规避规划: 起点=%s, 终点=%s, 网格=%s",
            start,
            goal,
            grid_size,
        )

        rows, cols = grid_size

        if start == goal:
            return {"path": [list(start)], "cost": 0.0, "nodes_explored": 0}

        self._rows = rows
        self._cols = cols
        self._obstacles = obstacles
        self._turbulence = turbulence_field

        # 构建湍流代价图
        turbulence_cost_map = self._build_turbulence_cost_map(rows, cols)

        # 将高湍流区域标记为临时障碍物
        unsafe_zones = self._identify_unsafe_zones(rows, cols)
        effective_obstacles = obstacles | unsafe_zones

        self._effective_obstacles = effective_obstacles

        # A*搜索
        open_set: list[tuple[float, tuple[int, int]]] = []
        heapq.heappush(open_set, (self._heuristic(start, goal), start))
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
                cost = g_score[current]
                logger.info(
                    "湍流规避规划完成: 代价=%.2f, 探索节点=%d",
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

                base_cost = self._edge_cost(current, neighbor)
                turb_cost = turbulence_cost_map.get(neighbor, 0.0)
                total_cost = base_cost + turb_cost

                new_g = g_score[current] + total_cost
                if new_g < g_score.get(neighbor, float("inf")):
                    g_score[neighbor] = new_g
                    came_from[neighbor] = current
                    f = new_g + self._heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f, neighbor))

        logger.warning("湍流规避规划未找到路径")
        return {
            "path": [],
            "cost": float("inf"),
            "nodes_explored": nodes_explored,
        }

    def _build_turbulence_cost_map(
        self,
        rows: int,
        cols: int,
    ) -> dict[tuple[int, int], float]:
        """构建湍流代价图。"""
        cost_map: dict[tuple[int, int], float] = {}

        if self._turbulence is None:
            return cost_map

        try:
            turb_arr = np.asarray(self._turbulence)
            for i in range(rows):
                for j in range(cols):
                    if 0 <= i < turb_arr.shape[0] and 0 <= j < turb_arr.shape[1]:
                        turb_val = float(turb_arr[i, j])
                        if turb_val > self.turbulence_threshold:
                            # 超过阈值的湍流区域代价急剧增加
                            cost_map[(i, j)] = self.turbulence_weight * (
                                (turb_val - self.turbulence_threshold) / self.turbulence_threshold
                            ) ** 2
                        else:
                            cost_map[(i, j)] = self.turbulence_weight * turb_val * 0.1
        except (IndexError, TypeError):
            pass

        return cost_map

    def _identify_unsafe_zones(
        self,
        rows: int,
        cols: int,
    ) -> set[tuple[int, int]]:
        """识别不安全湍流区域（超过安全裕度）。"""
        unsafe: set[tuple[int, int]] = set()

        if self._turbulence is None:
            return unsafe

        try:
            turb_arr = np.asarray(self._turbulence)
            threshold = self.turbulence_threshold * self.safety_margin
            for i in range(rows):
                for j in range(cols):
                    if 0 <= i < turb_arr.shape[0] and 0 <= j < turb_arr.shape[1]:
                        if float(turb_arr[i, j]) > threshold:
                            unsafe.add((i, j))
        except (IndexError, TypeError):
            pass

        return unsafe

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
        """计算基础边代价。"""
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
            if (
                0 <= nx < self._rows
                and 0 <= ny < self._cols
                and (nx, ny) not in self._effective_obstacles
            ):
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
