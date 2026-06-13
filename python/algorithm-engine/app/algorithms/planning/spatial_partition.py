"""空间分区多UAV协同路径规划算法。

将任务区域划分为多个子区域，每架UAV负责一个子区域，
在各自区域内独立规划路径，同时考虑区域间的协调约束。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class SpatialPartitionPlanner:
    """空间分区多UAV协同规划器。

    将规划空间划分为多个子区域，分配给不同UAV。
    每架UAV在分配的子区域内独立执行路径规划，
    通过区域边界协调避免冲突。

    Args:
        config: 配置字典，支持以下参数：
            - num_uavs: UAV数量，默认3
            - partition_method: 分区方法 "grid" 或 "voronoi"，默认"grid"
            - sub_planner: 子区域规划器类型，默认"a_star"
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.num_uavs: int = self.config.get("num_uavs", 3)
        self.partition_method: str = self.config.get("partition_method", "grid")
        self.sub_planner: str = self.config.get("sub_planner", "a_star")

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行空间分区多UAV协同规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]
                - uav_starts: 各UAV起点列表（可选）
                - uav_goals: 各UAV目标列表（可选）

        Returns:
            包含 path（路径点列表）和 cost（路径代价）的字典，
            以及分区方案 partitions。
        """
        np.random.seed(42)

        start = np.array(params.get("start", (0, 0)), dtype=float)
        goal = np.array(params.get("goal", (10, 10)), dtype=float)
        grid_size = params.get("grid_size", (50, 50))
        obstacles = set(map(tuple, params.get("obstacles", [])))

        rows, cols = grid_size

        logger.info(
            "空间分区规划: UAV数=%d, 网格=%s, 分区方法=%s",
            self.num_uavs,
            grid_size,
            self.partition_method,
        )

        # UAV起点和目标
        uav_starts_input = params.get("uav_starts", [])
        if uav_starts_input and len(uav_starts_input) >= self.num_uavs:
            uav_starts = [np.array(s[:2], dtype=float) for s in uav_starts_input[: self.num_uavs]]
        else:
            uav_starts = [start.copy() for _ in range(self.num_uavs)]

        uav_goals_input = params.get("uav_goals", [])
        if uav_goals_input and len(uav_goals_input) >= self.num_uavs:
            uav_goals = [np.array(g[:2], dtype=float) for g in uav_goals_input[: self.num_uavs]]
        else:
            uav_goals = [goal.copy() for _ in range(self.num_uavs)]

        # 空间分区
        partitions = self._partition_space(rows, cols, self.num_uavs)

        # 为每架UAV在其分配区域内规划路径
        uav_paths: dict[int, list[list[int]]] = {}
        uav_costs: dict[int, float] = {}
        total_cost = 0.0

        for uav in range(self.num_uavs):
            region = partitions[uav]
            uav_start = uav_starts[uav]
            uav_goal = uav_goals[uav]

            # 将起点和目标限制在区域内
            uav_start = self._clamp_to_region(uav_start, region)
            uav_goal = self._clamp_to_region(uav_goal, region)

            # 在区域内执行路径规划
            path = self._plan_in_region(
                uav_start,
                uav_goal,
                region,
                obstacles,
                rows,
                cols,
            )
            uav_paths[uav] = path
            cost = self._path_cost(path)
            uav_costs[uav] = cost
            total_cost += cost

        # 主UAV路径
        main_path = uav_paths.get(0, [list(start.astype(int)), list(goal.astype(int))])

        # 分区方案
        partition_info = {}
        for uav in range(self.num_uavs):
            region = partitions[uav]
            partition_info[f"uav_{uav}"] = {
                "region": {
                    "x_min": int(region[0]),
                    "y_min": int(region[1]),
                    "x_max": int(region[2]),
                    "y_max": int(region[3]),
                },
                "path": uav_paths[uav],
                "cost": uav_costs[uav],
            }

        logger.info(
            "空间分区完成: 总代价=%.2f, 分区数=%d",
            total_cost,
            self.num_uavs,
        )
        return {
            "path": main_path,
            "cost": uav_costs.get(0, 0.0),
            "total_cost": total_cost,
            "partitions": partition_info,
            "num_uavs": self.num_uavs,
        }

    def _partition_space(
        self,
        rows: int,
        cols: int,
        num_uavs: int,
    ) -> list[tuple[float, float, float, float]]:
        """将空间划分为子区域。

        返回每个区域的 (x_min, y_min, x_max, y_max)。
        """
        partitions = []

        if self.partition_method == "grid":
            # 网格分区：尽量均匀划分
            # 选择划分方向
            if rows >= cols:
                # 按行划分
                rows_per_uav = rows / num_uavs
                for i in range(num_uavs):
                    x_min = i * rows_per_uav
                    x_max = (i + 1) * rows_per_uav
                    partitions.append((x_min, 0, x_max, cols))
            else:
                # 按列划分
                cols_per_uav = cols / num_uavs
                for i in range(num_uavs):
                    y_min = i * cols_per_uav
                    y_max = (i + 1) * cols_per_uav
                    partitions.append((0, y_min, rows, y_max))
        else:
            # Voronoi风格分区（简化版：基于均匀分布的中心点）
            centers = []
            for i in range(num_uavs):
                cx = (i + 0.5) * rows / num_uavs
                cy = cols / 2.0
                centers.append(np.array([cx, cy]))

            for i in range(num_uavs):
                # 计算Voronoi区域边界
                if i == 0:
                    x_min = 0
                else:
                    x_min = (centers[i - 1][0] + centers[i][0]) / 2.0

                if i == num_uavs - 1:
                    x_max = rows
                else:
                    x_max = (centers[i][0] + centers[i + 1][0]) / 2.0

                partitions.append((x_min, 0, x_max, cols))

        return partitions

    def _clamp_to_region(
        self,
        point: np.ndarray,
        region: tuple,
    ) -> np.ndarray:
        """将点限制在区域内。"""
        x_min, y_min, x_max, y_max = region
        return np.array(
            [
                np.clip(point[0], x_min, x_max),
                np.clip(point[1], y_min, y_max),
            ]
        )

    def _plan_in_region(
        self,
        start: np.ndarray,
        goal: np.ndarray,
        region: tuple,
        obstacles: set,
        rows: int,
        cols: int,
    ) -> list[list[int]]:
        """在子区域内使用A*规划路径。"""
        x_min, y_min, x_max, y_max = region

        # 区域内的障碍物
        region_obstacles = set()
        for obs in obstacles:
            if x_min <= obs[0] <= x_max and y_min <= obs[1] <= y_max:
                region_obstacles.add(obs)

        start_grid = (int(round(start[0])), int(round(start[1])))
        goal_grid = (int(round(goal[0])), int(round(goal[1])))

        # 简化A*搜索
        import heapq

        open_set: list[tuple[float, tuple[int, int]]] = []
        heapq.heappush(open_set, (self._heuristic(start_grid, goal_grid), start_grid))
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = {start_grid: 0.0}

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal_grid:
                path = [list(current)]
                while current in came_from:
                    current = came_from[current]
                    path.append(list(current))
                path.reverse()
                return path

            for dx, dy in directions:
                nx, ny = current[0] + dx, current[1] + dy
                neighbor = (nx, ny)

                if not (x_min <= nx <= x_max and y_min <= ny <= y_max):
                    continue
                if not (0 <= nx < rows and 0 <= ny < cols):
                    continue
                if neighbor in region_obstacles:
                    continue

                edge_cost = 1.414 if abs(dx) + abs(dy) == 2 else 1.0
                new_g = g_score[current] + edge_cost

                if new_g < g_score.get(neighbor, float("inf")):
                    g_score[neighbor] = new_g
                    came_from[neighbor] = current
                    f = new_g + self._heuristic(neighbor, goal_grid)
                    heapq.heappush(open_set, (f, neighbor))

        # A*失败，返回直线路径
        return [
            [int(round(start[0])), int(round(start[1]))],
            [int(round(goal[0])), int(round(goal[1]))],
        ]

    def _heuristic(self, a: tuple[int, int], b: tuple[int, int]) -> float:
        """曼哈顿距离启发式。"""
        return float(abs(a[0] - b[0]) + abs(a[1] - b[1]))

    def _path_cost(self, path: list[list[int]]) -> float:
        """计算路径代价。"""
        if len(path) < 2:
            return 0.0
        cost = 0.0
        for i in range(len(path) - 1):
            cost += float(np.linalg.norm(np.array(path[i + 1]) - np.array(path[i])))
        return cost
