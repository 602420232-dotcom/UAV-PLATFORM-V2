"""轨道分解多UAV协同路径规划算法。

将任务区域划分为多个轨道（orbit），每架UAV负责一条轨道，
通过轨道间的协调实现区域全覆盖和任务分配的平衡。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class OrbitalDecompositionPlanner:
    """轨道分解多UAV协同规划器。

    将搜索区域分解为同心轨道或平行轨道，分配给不同UAV执行。
    每架UAV沿分配的轨道运动，实现协同覆盖和任务分配。

    Args:
        config: 配置字典，支持以下参数：
            - num_uavs: UAV数量，默认3
            - orbit_spacing: 轨道间距，默认5.0
            - orbit_type: 轨道类型 "concentric" 或 "parallel"，默认"concentric"
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.num_uavs: int = self.config.get("num_uavs", 3)
        self.orbit_spacing: float = self.config.get("orbit_spacing", 5.0)
        self.orbit_type: str = self.config.get("orbit_type", "concentric")

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行轨道分解多UAV协同规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]
                - center: 轨道中心点（可选，默认网格中心）

        Returns:
            包含 path（路径点列表）和 cost（路径代价）的字典，
            以及各UAV的轨道分配 orbits。
        """
        np.random.seed(42)

        start = np.array(params.get("start", (0, 0)), dtype=float)
        goal = np.array(params.get("goal", (10, 10)), dtype=float)
        grid_size = params.get("grid_size", (50, 50))
        obstacles = set(map(tuple, params.get("obstacles", [])))

        rows, cols = grid_size
        center_input = params.get("center")
        if center_input:
            center = np.array(center_input[:2], dtype=float)
        else:
            center = np.array([rows / 2.0, cols / 2.0])

        logger.info(
            "轨道分解规划: UAV数=%d, 中心=%s, 轨道类型=%s",
            self.num_uavs,
            tuple(center.astype(int)),
            self.orbit_type,
        )

        # 生成轨道
        orbits: list[list[list[int]]] = []
        orbit_costs: list[float] = []

        if self.orbit_type == "concentric":
            # 同心圆轨道
            max_radius = min(rows, cols) / 2.0
            for uav in range(self.num_uavs):
                radius = self.orbit_spacing * (uav + 1)
                if radius > max_radius:
                    radius = max_radius

                orbit_points = self._generate_concentric_orbit(
                    center,
                    radius,
                    obstacles,
                    rows,
                    cols,
                )
                orbits.append(orbit_points)
                orbit_costs.append(self._orbit_cost(orbit_points))
        else:
            # 平行轨道
            for uav in range(self.num_uavs):
                y_offset = self.orbit_spacing * uav + self.orbit_spacing
                orbit_points = self._generate_parallel_orbit(
                    y_offset,
                    obstacles,
                    rows,
                    cols,
                )
                orbits.append(orbit_points)
                orbit_costs.append(self._orbit_cost(orbit_points))

        # 主UAV（UAV 0）的路径：从起点到轨道起点，沿轨道运动，到终点
        if orbits:
            main_orbit = orbits[0]
            # 构建完整路径：start -> orbit -> goal
            full_path = [list(start.astype(int))]
            full_path.extend(main_orbit)
            full_path.append(list(goal.astype(int)))
            total_cost = self._path_cost_from_points(full_path)
        else:
            full_path = [
                list(start.astype(int)),
                list(goal.astype(int)),
            ]
            total_cost = float(np.linalg.norm(goal - start))

        # 构建分配方案
        orbit_assignments = {}
        for uav in range(self.num_uavs):
            orbit_assignments[f"uav_{uav}"] = {
                "orbit": orbits[uav] if uav < len(orbits) else [],
                "cost": orbit_costs[uav] if uav < len(orbit_costs) else 0.0,
            }

        logger.info(
            "轨道分解完成: 主路径代价=%.2f, 轨道数=%d",
            total_cost,
            len(orbits),
        )
        return {
            "path": full_path,
            "cost": total_cost,
            "orbits": orbit_assignments,
            "num_uavs": self.num_uavs,
        }

    def _generate_concentric_orbit(
        self,
        center: np.ndarray,
        radius: float,
        obstacles: set,
        rows: int,
        cols: int,
    ) -> list[list[int]]:
        """生成同心圆轨道点。"""
        points = []
        n_points = max(int(2 * np.pi * radius), 12)
        for i in range(n_points):
            angle = 2 * np.pi * i / n_points
            x = center[0] + radius * np.cos(angle)
            y = center[1] + radius * np.sin(angle)
            ix, iy = int(round(x)), int(round(y))
            if 0 <= ix < rows and 0 <= iy < cols and (ix, iy) not in obstacles:
                points.append([ix, iy])
        return points

    def _generate_parallel_orbit(
        self,
        y_offset: float,
        obstacles: set,
        rows: int,
        cols: int,
    ) -> list[list[int]]:
        """生成平行轨道点。"""
        points = []
        iy = int(round(y_offset))
        if iy >= cols:
            iy = cols - 1
        for ix in range(rows):
            if (ix, iy) not in obstacles:
                points.append([ix, iy])
        return points

    def _orbit_cost(self, orbit: list[list[int]]) -> float:
        """计算轨道代价。"""
        if len(orbit) < 2:
            return 0.0
        cost = 0.0
        for i in range(len(orbit) - 1):
            cost += float(np.linalg.norm(np.array(orbit[i + 1]) - np.array(orbit[i])))
        return cost

    def _path_cost_from_points(self, path: list[list[int]]) -> float:
        """计算路径总代价。"""
        if len(path) < 2:
            return 0.0
        cost = 0.0
        for i in range(len(path) - 1):
            cost += float(np.linalg.norm(np.array(path[i + 1]) - np.array(path[i])))
        return cost
