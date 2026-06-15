"""风场路径规划算法。

考虑风场对UAV飞行影响的路径规划方法。
利用风场信息进行顺风/逆风代价建模，
在保证安全的前提下规划能耗最优的飞行路径。
支持利用顺风减少能耗或规避强逆风区域。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class WindFieldPlanner:
    """风场路径规划器。

    在A*搜索基础上，将风场对飞行的影响建模为代价。
    顺风飞行减少能耗（负代价），逆风飞行增加能耗（正代价），
    侧风增加飞行难度。

    代价模型：
    - 基础移动代价
    - 风阻代价：与飞行方向和风向的夹角相关
    - 湍流代价：高湍流区域额外惩罚

    Args:
        config: 配置字典，支持以下参数：
            - wind_weight: 风场代价权重，默认3.0
            - max_wind_speed: 最大安全风速，默认20.0
            - uav_air_speed: UAV空速，默认5.0
            - allow_diagonal: 是否允许对角移动，默认True
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.wind_weight: float = self.config.get("wind_weight", 3.0)
        self.max_wind_speed: float = self.config.get("max_wind_speed", 20.0)
        self.uav_air_speed: float = self.config.get("uav_air_speed", 5.0)
        self.allow_diagonal: bool = self.config.get("allow_diagonal", True)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行风场路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]
                - wind_field: 风场数据（可选），字典包含：
                    - wind_u: 东西方向风速分量 (rows x cols)
                    - wind_v: 南北方向风速分量 (rows x cols)
                    - turbulence: 湍流强度场 (rows x cols)

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
        wind_field = params.get("wind_field", {})

        logger.info(
            "风场规划: 起点=%s, 终点=%s, 网格=%s",
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
        self._wind = wind_field

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
                    "风场规划完成: 代价=%.2f, 探索节点=%d",
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

                # 计算飞行方向
                flight_dir = np.array(
                    [neighbor[0] - current[0], neighbor[1] - current[1]],
                    dtype=float,
                )
                flight_dist = np.linalg.norm(flight_dir)
                if flight_dist > 1e-6:
                    flight_dir = flight_dir / flight_dist

                # 基础移动代价
                base_cost = self._edge_cost(current, neighbor)

                # 风场代价
                wind_cost = self._wind_cost(current, flight_dir)

                total_cost = base_cost + wind_cost
                new_g = g_score[current] + total_cost

                if new_g < g_score.get(neighbor, float("inf")):
                    g_score[neighbor] = new_g
                    came_from[neighbor] = current
                    f = new_g + self._heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f, neighbor))

        logger.warning("风场规划未找到路径")
        return {
            "path": [],
            "cost": float("inf"),
            "nodes_explored": nodes_explored,
        }

    def _wind_cost(
        self,
        pos: tuple[int, int],
        flight_dir: np.ndarray,
    ) -> float:
        """计算风场代价。"""
        wind_u = self._get_wind_value("wind_u", pos)
        wind_v = self._get_wind_value("wind_v", pos)
        turbulence = self._get_wind_value("turbulence", pos)

        wind_vec = np.array([wind_u, wind_v])
        wind_speed = float(np.linalg.norm(wind_vec))

        # 风速超过安全阈值
        if wind_speed > self.max_wind_speed:
            return 100.0

        if wind_speed < 1e-6:
            return 0.0

        # 计算风向与飞行方向的夹角
        wind_dir = wind_vec / wind_speed
        cos_angle = float(np.dot(flight_dir, wind_dir))

        # 顺风（cos_angle > 0）减少代价，逆风增加代价
        # 侧风（cos_angle ≈ 0）增加中等代价
        headwind_factor = -cos_angle  # 正值表示逆风

        wind_cost = self.wind_weight * (
            1.0 + headwind_factor * (wind_speed / self.uav_air_speed)
        )

        # 湍流额外代价
        wind_cost += 2.0 * turbulence

        return max(wind_cost, 0.0)

    def _get_wind_value(
        self,
        field_name: str,
        pos: tuple[int, int],
    ) -> float:
        """从风场获取指定位置的值。"""
        field = self._wind.get(field_name)
        if field is None:
            return 0.0
        try:
            field_arr = np.asarray(field)
            if 0 <= pos[0] < field_arr.shape[0] and 0 <= pos[1] < field_arr.shape[1]:
                return float(field_arr[pos[0], pos[1]])
        except (IndexError, TypeError):
            pass
        return 0.0

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
