"""四维轨迹规划算法（3D空间+时间）。

在三维空间基础上引入时间维度，进行四维轨迹规划，
综合考虑风速影响、能耗约束和时间窗口要求。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class Trajectory4DPlanner:
    """四维轨迹规划器。

    在三维空间坐标(x, y, z)基础上加入时间维度t，生成四维
    轨迹 (x, y, z, t)。规划时考虑风场对飞行的影响、电池能耗
    约束以及到达时间要求，输出包含详细航点信息的4D轨迹。

    Args:
        config: 配置字典，支持以下参数：
            - default_altitude: 默认飞行高度(m)，默认50
            - max_altitude: 最大飞行高度(m)，默认120
            - min_altitude: 最小飞行高度(m)，默认10
            - time_step: 时间步长(s)，默认1.0
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.default_altitude: float = self.config.get("default_altitude", 50.0)
        self.max_altitude: float = self.config.get("max_altitude", 120.0)
        self.min_altitude: float = self.config.get("min_altitude", 10.0)
        self.time_step: float = self.config.get("time_step", 1.0)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行四维轨迹规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 [x, y, z]（z可选，默认default_altitude）
                - goal: 终点坐标 [x, y, z]（z可选，默认default_altitude）
                - obstacles: 障碍物列表 list[list[int]]，每个障碍物含
                  [x, y, z, radius] 或 [x, y, radius]
                - wind_field: 风场数据字典，含：
                    - base_speed: 基础风速 (m/s)
                    - direction: 风向 (度)
                    - gust_factor: 阵风因子
                    - layers: 分层风场数据 list[dict]
                - time_constraints: 时间约束字典，含：
                    - earliest_arrival: 最早到达时间 (s)
                    - latest_arrival: 最晚到达时间 (s)
                    - max_flight_time: 最大飞行时间 (s)
                - uav_params: 无人机参数字典，含：
                    - cruise_speed: 巡航速度 (m/s)
                    - max_speed: 最大速度 (m/s)
                    - mass: 质量 (kg)
                    - battery_capacity: 电池容量 (Wh)
                    - power_consumption: 功耗 (W)

        Returns:
            包含以下键的字典：
                - trajectory_4d: 4D轨迹点列表 [[x, y, z, t], ...]
                - energy_consumption: 总能耗 (Wh)
                - flight_time: 飞行时间 (s)
                - waypoints_detail: 航点详情列表
        """
        np.random.seed(42)

        start = params.get("start", [0, 0])
        goal = params.get("goal", [10, 10])
        obstacles = params.get("obstacles", [])
        wind_field = params.get("wind_field", {})
        time_constraints = params.get("time_constraints", {})
        uav_params = params.get("uav_params", {})

        # 解析起点终点（支持2D和3D）
        start_3d = [
            float(start[0]),
            float(start[1]),
            float(start[2]) if len(start) > 2 else self.default_altitude,
        ]
        goal_3d = [
            float(goal[0]),
            float(goal[1]),
            float(goal[2]) if len(goal) > 2 else self.default_altitude,
        ]

        # 解析无人机参数
        cruise_speed = uav_params.get("cruise_speed", 10.0)
        max_speed = uav_params.get("max_speed", 15.0)
        mass = uav_params.get("mass", 1.5)
        power_consumption = uav_params.get("power_consumption", 50.0)

        # 解析风场
        wind_base_speed = wind_field.get("base_speed", 3.0)
        wind_direction = wind_field.get("direction", 0.0)
        wind_dir_rad = np.radians(wind_direction)
        gust_factor = wind_field.get("gust_factor", 0.2)

        # 解析时间约束
        earliest_arrival = time_constraints.get("earliest_arrival", 0.0)

        logger.info(
            "4D轨迹规划: 起点=%s, 终点=%s, 巡航速度=%.1f, 风速=%.1f",
            start_3d, goal_3d, cruise_speed, wind_base_speed,
        )

        # 2D路径规划（A*）
        grid_size = [50, 50]
        obstacle_set = set()
        for obs in obstacles:
            obstacle_set.add((int(obs[0]), int(obs[1])))

        start_grid = self._world_to_grid(start_3d[:2], grid_size[0], grid_size[1])
        goal_grid = self._world_to_grid(goal_3d[:2], grid_size[0], grid_size[1])

        path_2d = self._plan_2d_path(
            start_grid, goal_grid, grid_size[0], grid_size[1], obstacle_set,
        )

        if not path_2d:
            logger.warning("4D轨迹规划: 2D路径规划失败")
            return {
                "trajectory_4d": [],
                "energy_consumption": 0.0,
                "flight_time": 0.0,
                "waypoints_detail": [],
            }

        # 3D路径生成（高度规划）
        path_3d = self._plan_altitude(
            path_2d, start_3d[2], goal_3d[2], obstacles,
        )

        # 4D轨迹生成（时间分配）
        trajectory_4d = self._assign_time(
            path_3d, cruise_speed, max_speed, wind_base_speed,
            wind_dir_rad, gust_factor, earliest_arrival,
        )

        # 计算能耗
        energy_consumption = self._compute_energy(
            trajectory_4d, mass, power_consumption, wind_base_speed,
            wind_dir_rad, gust_factor,
        )

        # 计算飞行时间
        flight_time = 0.0
        if len(trajectory_4d) >= 2:
            flight_time = trajectory_4d[-1][3] - trajectory_4d[0][3]

        # 生成航点详情
        waypoints_detail = self._generate_waypoint_details(
            trajectory_4d, wind_base_speed, wind_dir_rad, gust_factor,
        )

        logger.info(
            "4D轨迹规划完成: 飞行时间=%.2fs, 能耗=%.2fWh, 航点数=%d",
            flight_time, energy_consumption, len(trajectory_4d),
        )

        return {
            "trajectory_4d": trajectory_4d,
            "energy_consumption": energy_consumption,
            "flight_time": flight_time,
            "waypoints_detail": waypoints_detail,
        }

    def _world_to_grid(
        self, pos: list, rows: int, cols: int,
    ) -> tuple[int, int]:
        """世界坐标转网格坐标。"""
        gx = int(pos[0] + rows / 2)
        gy = int(pos[1] + cols / 2)
        return (max(0, min(gx, rows - 1)), max(0, min(gy, cols - 1)))

    def _grid_to_world(
        self, pos: tuple[int, int], rows: int, cols: int,
    ) -> list[float]:
        """网格坐标转世界坐标。"""
        return [float(pos[0] - rows // 2), float(pos[1] - cols // 2)]

    def _plan_2d_path(
        self,
        start_grid: tuple[int, int],
        goal_grid: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
    ) -> list[list[float]]:
        """2D A*路径规划。"""
        open_set: list[tuple[float, tuple[int, int]]] = []
        heapq.heappush(open_set, (0.0, start_grid))
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = {start_grid: 0.0}

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal_grid:
                return self._reconstruct_path_2d(came_from, current, rows, cols)

            for neighbor in self._get_neighbors(current, rows, cols, obstacles):
                tentative_g = g_score[current] + 1.0
                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = float(abs(neighbor[0] - goal_grid[0]) + abs(neighbor[1] - goal_grid[1]))
                    heapq.heappush(open_set, (tentative_g + h, neighbor))

        return []

    def _get_neighbors(
        self,
        pos: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
    ) -> list[tuple[int, int]]:
        """获取有效邻居节点（4连通）。"""
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = pos[0] + dx, pos[1] + dy
            if 0 <= nx < rows and 0 <= ny < cols and (nx, ny) not in obstacles:
                neighbors.append((nx, ny))
        return neighbors

    def _reconstruct_path_2d(
        self,
        came_from: dict[tuple[int, int], tuple[int, int]],
        current: tuple[int, int],
        rows: int,
        cols: int,
    ) -> list[list[float]]:
        """从目标回溯重建2D路径。"""
        path = [self._grid_to_world(current, rows, cols)]
        while current in came_from:
            current = came_from[current]
            path.append(self._grid_to_world(current, rows, cols))
        path.reverse()
        return path

    def _plan_altitude(
        self,
        path_2d: list[list[float]],
        start_alt: float,
        goal_alt: float,
        obstacles: list,
    ) -> list[list[float]]:
        """为2D路径规划高度剖面。

        采用平滑的高度过渡策略，在起点和终点之间线性插值，
        中间段保持巡航高度，并避开障碍物高度。
        """
        if not path_2d:
            return []

        path_3d = []
        n = len(path_2d)
        cruise_alt = max(start_alt, goal_alt, self.default_altitude)

        # 爬升段（前20%）
        climb_end = max(1, int(n * 0.2))
        # 巡航段（20%-80%）
        cruise_end = max(climb_end + 1, int(n * 0.8))
        # 下降段（后20%）

        for i in range(n):
            x, y = path_2d[i]

            if i <= climb_end:
                # 爬升段：从起始高度线性爬升到巡航高度
                t = i / max(climb_end, 1)
                alt = start_alt + (cruise_alt - start_alt) * t
            elif i <= cruise_end:
                # 巡航段：保持巡航高度
                alt = cruise_alt
            else:
                # 下降段：从巡航高度线性下降到目标高度
                t = (i - cruise_end) / max(n - 1 - cruise_end, 1)
                alt = cruise_alt + (goal_alt - cruise_alt) * t

            # 检查障碍物高度约束
            for obs in obstacles:
                ox, oy = obs[0], obs[1]
                if len(obs) > 2:
                    oz = obs[2] if len(obs) > 3 else 0.0
                    oradius = obs[3] if len(obs) > 3 else obs[2]
                else:
                    oz = 0.0
                    oradius = obs[2] if len(obs) > 2 else 1.0
                dist = np.sqrt((x - ox) ** 2 + (y - oy) ** 2)
                if dist < oradius * 2:
                    alt = max(alt, oz + 10.0)  # 在障碍物上方至少10m

            alt = np.clip(alt, self.min_altitude, self.max_altitude)
            path_3d.append([x, y, float(alt)])

        return path_3d

    def _assign_time(
        self,
        path_3d: list[list[float]],
        cruise_speed: float,
        max_speed: float,
        wind_speed: float,
        wind_dir_rad: float,
        gust_factor: float,
        earliest_arrival: float,
    ) -> list[list[float]]:
        """为3D路径分配时间戳，生成4D轨迹。"""
        if not path_3d:
            return []

        trajectory = []
        current_time = earliest_arrival

        for i, point in enumerate(path_3d):
            if i == 0:
                trajectory.append([point[0], point[1], point[2], current_time])
                continue

            prev = path_3d[i - 1]
            # 计算段距离
            dx = point[0] - prev[0]
            dy = point[1] - prev[1]
            dz = point[2] - prev[2]
            segment_dist = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

            # 计算飞行方向
            if segment_dist > 1e-6:
                flight_dir = np.arctan2(dy, dx)
            else:
                flight_dir = 0.0

            # 风的影响（顺风/逆风）
            wind_component = wind_speed * np.cos(flight_dir - wind_dir_rad)
            gust = wind_speed * gust_factor * np.random.randn() * 0.1

            # 有效地速
            effective_speed = cruise_speed - wind_component + gust
            effective_speed = np.clip(effective_speed, cruise_speed * 0.5, max_speed)

            # 飞行时间
            segment_time = segment_dist / effective_speed
            current_time += segment_time

            trajectory.append([
                round(point[0], 4),
                round(point[1], 4),
                round(point[2], 4),
                round(current_time, 4),
            ])

        return trajectory

    def _compute_energy(
        self,
        trajectory: list[list[float]],
        mass: float,
        power_consumption: float,
        wind_speed: float,
        wind_dir_rad: float,
        gust_factor: float,
    ) -> float:
        """计算4D轨迹的总能耗。"""
        if len(trajectory) < 2:
            return 0.0

        total_energy = 0.0

        for i in range(1, len(trajectory)):
            prev = trajectory[i - 1]
            curr = trajectory[i]

            # 时间差
            dt = curr[3] - prev[3]
            if dt <= 0:
                continue

            # 速度
            dx = curr[0] - prev[0]
            dy = curr[1] - prev[1]
            dz = curr[2] - prev[2]
            dist = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
            speed = dist / dt if dt > 0 else 0.0

            # 风的影响
            if dist > 1e-6:
                flight_dir = np.arctan2(dy, dx)
                wind_effect = wind_speed * np.cos(flight_dir - wind_dir_rad)
            else:
                wind_effect = 0.0

            # 功率模型（简化）
            # P = P_hover + k * v^2 + wind_correction
            p_hover = power_consumption * 0.6  # 悬停功率
            p_cruise = power_consumption * 0.3 * (speed / 10.0) ** 2  # 巡航功率
            p_climb = power_consumption * 0.1 * max(0, dz / dt) if dt > 0 else 0.0  # 爬升功率
            p_wind = abs(wind_effect) * mass * 0.5  # 风阻功率

            segment_power = p_hover + p_cruise + p_climb + p_wind
            segment_energy = segment_power * dt / 3600.0  # Wh
            total_energy += segment_energy

        return round(total_energy, 4)

    def _generate_waypoint_details(
        self,
        trajectory: list[list[float]],
        wind_speed: float,
        wind_dir_rad: float,
        gust_factor: float,
    ) -> list[dict[str, Any]]:
        """生成航点详情列表。"""
        details = []

        for i, point in enumerate(trajectory):
            x, y, z, t = point

            # 计算速度
            speed = 0.0
            heading = 0.0
            vertical_speed = 0.0

            if i > 0:
                prev = trajectory[i - 1]
                dt = t - prev[3]
                if dt > 0:
                    dx = x - prev[0]
                    dy = y - prev[1]
                    dz = z - prev[2]
                    dist = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
                    speed = dist / dt
                    heading = float(np.degrees(np.arctan2(dy, dx))) % 360
                    vertical_speed = dz / dt

            # 风信息
            wind_at_point = wind_speed * (1.0 + gust_factor * np.random.randn() * 0.05)

            detail = {
                "index": i,
                "position": {"x": x, "y": y, "z": z},
                "time": t,
                "speed": round(speed, 4),
                "heading": round(heading, 2),
                "vertical_speed": round(vertical_speed, 4),
                "wind_speed": round(wind_at_point, 4),
                "type": "start" if i == 0 else ("end" if i == len(trajectory) - 1 else "waypoint"),
            }
            details.append(detail)

        return details
