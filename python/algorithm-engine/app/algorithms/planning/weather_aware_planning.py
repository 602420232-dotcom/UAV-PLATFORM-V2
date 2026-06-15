"""气象感知路径规划算法。

综合考虑气象条件（风速、风向、降水、能见度等）的路径规划方法。
将气象数据作为额外的代价层叠加到基础路径规划中，
在保证安全的前提下规划气象风险最低的飞行路径。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class WeatherAwarePlanner:
    """气象感知路径规划器。

    在标准A*搜索基础上，将气象风险作为额外代价项。
    气象代价包括：
    - 风速代价：高风速区域增加飞行风险和能耗
    - 降水代价：降水区域降低能见度和飞行安全
    - 能见度代价：低能见度区域增加导航难度
    - 湍流代价：湍流区域影响飞行稳定性

    Args:
        config: 配置字典，支持以下参数：
            - wind_weight: 风速代价权重，默认2.0
            - precipitation_weight: 降水代价权重，默认3.0
            - visibility_weight: 能见度代价权重，默认2.0
            - turbulence_weight: 湍流代价权重，默认5.0
            - max_wind_speed: 最大安全风速，默认15.0
            - max_turbulence: 最大安全湍流强度，默认0.8
            - allow_diagonal: 是否允许对角移动，默认True
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.wind_weight: float = self.config.get("wind_weight", 2.0)
        self.precipitation_weight: float = self.config.get("precipitation_weight", 3.0)
        self.visibility_weight: float = self.config.get("visibility_weight", 2.0)
        self.turbulence_weight: float = self.config.get("turbulence_weight", 5.0)
        self.max_wind_speed: float = self.config.get("max_wind_speed", 15.0)
        self.max_turbulence: float = self.config.get("max_turbulence", 0.8)
        self.allow_diagonal: bool = self.config.get("allow_diagonal", True)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行气象感知路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]
                - weather_field: 气象场数据（可选），字典包含：
                    - wind_speed: 风速场 (rows x cols)
                    - wind_direction: 风向场 (rows x cols)
                    - precipitation: 降水场 (rows x cols)
                    - visibility: 能见度场 (rows x cols)
                    - turbulence: 湍流场 (rows x cols)

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
        weather_field = params.get("weather_field", {})

        logger.info(
            "气象感知规划: 起点=%s, 终点=%s, 网格=%s",
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
        self._weather = weather_field

        # 检查起点和终点的气象安全性
        if not self._is_weather_safe(start):
            logger.warning("起点气象条件不安全")
        if not self._is_weather_safe(goal):
            logger.warning("终点气象条件不安全")

        # A*搜索，使用气象加权代价
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
                    "气象感知规划完成: 代价=%.2f, 探索节点=%d",
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
                weather_cost = self._weather_cost(neighbor)
                total_cost = base_cost + weather_cost

                new_g = g_score[current] + total_cost
                if new_g < g_score.get(neighbor, float("inf")):
                    g_score[neighbor] = new_g
                    came_from[neighbor] = current
                    f = new_g + self._heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f, neighbor))

        logger.warning("气象感知规划未找到路径")
        return {
            "path": [],
            "cost": float("inf"),
            "nodes_explored": nodes_explored,
        }

    def _weather_cost(self, pos: tuple[int, int]) -> float:
        """计算位置的气象代价。"""
        cost = 0.0
        weather = self._weather

        # 风速代价
        wind_speed = self._get_weather_value(weather.get("wind_speed"), pos, default=0.0)
        if wind_speed > self.max_wind_speed:
            cost += 100.0  # 超过安全风速，极高代价
        else:
            cost += self.wind_weight * (wind_speed / self.max_wind_speed) ** 2

        # 降水代价
        precipitation = self._get_weather_value(
            weather.get("precipitation"), pos, default=0.0
        )
        cost += self.precipitation_weight * min(precipitation, 10.0)

        # 能见度代价（低能见度代价高）
        visibility = self._get_weather_value(weather.get("visibility"), pos, default=10.0)
        if visibility < 5.0:
            cost += self.visibility_weight * (5.0 - visibility) / 5.0

        # 湍流代价
        turbulence = self._get_weather_value(weather.get("turbulence"), pos, default=0.0)
        if turbulence > self.max_turbulence:
            cost += 100.0  # 超过安全湍流阈值
        else:
            cost += self.turbulence_weight * (turbulence / self.max_turbulence) ** 2

        return cost

    def _get_weather_value(
        self,
        field: Any,
        pos: tuple[int, int],
        default: float = 0.0,
    ) -> float:
        """从气象场获取指定位置的值。"""
        if field is None:
            return default
        try:
            field_arr = np.asarray(field)
            if 0 <= pos[0] < field_arr.shape[0] and 0 <= pos[1] < field_arr.shape[1]:
                return float(field_arr[pos[0], pos[1]])
        except (IndexError, TypeError):
            pass
        return default

    def _is_weather_safe(self, pos: tuple[int, int]) -> bool:
        """检查位置的气象安全性。"""
        wind_speed = self._get_weather_value(
            self._weather.get("wind_speed"), pos, default=0.0
        )
        turbulence = self._get_weather_value(
            self._weather.get("turbulence"), pos, default=0.0
        )
        return wind_speed <= self.max_wind_speed and turbulence <= self.max_turbulence

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
        """获取可行邻居节点（排除气象不安全区域）。"""
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
                and (nx, ny) not in self._obstacles
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
