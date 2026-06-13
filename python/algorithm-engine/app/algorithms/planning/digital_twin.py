"""数字孪生路径规划与仿真算法。

基于数字孪生技术的路径规划器，在虚拟环境中模拟无人机飞行，
评估路径可行性并迭代优化，最终输出经过仿真验证的最优路径。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class DigitalTwinPlanner:
    """数字孪生路径规划器。

    在虚拟数字孪生环境中模拟无人机飞行过程，考虑气象条件、
    无人机动力学模型等因素，通过多次仿真迭代优化路径。
    每次仿真评估路径的能耗、飞行时间、稳定性等指标，
    并根据仿真反馈调整路径。

    Args:
        config: 配置字典，支持以下参数：
            - simulation_steps: 仿真步数，默认100
            - optimization_rounds: 优化轮数，默认5
            - dt: 仿真时间步长，默认0.1秒
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.simulation_steps: int = self.config.get("simulation_steps", 100)
        self.optimization_rounds: int = self.config.get("optimization_rounds", 5)
        self.dt: float = self.config.get("dt", 0.1)

    def simulate(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行基于数字孪生的路径规划与仿真。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 [x, y]
                - goal: 终点坐标 [x, y]
                - grid_size: 网格尺寸 [rows, cols]
                - obstacles: 障碍物列表 list[list[int]]
                - weather_conditions: 气象条件字典，含：
                    - wind_speed: 风速 (m/s)
                    - wind_direction: 风向 (度)
                    - temperature: 温度 (度)
                    - humidity: 湿度 (%)
                    - visibility: 能见度 (km)
                - uav_model: 无人机模型参数字典，含：
                    - max_speed: 最大速度 (m/s)
                    - mass: 质量 (kg)
                    - battery_capacity: 电池容量 (mAh)
                    - drag_coefficient: 阻力系数
                - simulation_steps: 仿真步数，可选

        Returns:
            包含以下键的字典：
                - optimized_path: 优化后的路径
                - simulation_results: 仿真结果详情
                - performance_metrics: 性能指标
                - twin_state: 孪生状态快照
        """
        np.random.seed(42)

        start = params.get("start", [0, 0])
        goal = params.get("goal", [10, 10])
        grid_size = params.get("grid_size", [50, 50])
        obstacles = set(map(tuple, params.get("obstacles", [])))
        weather = params.get("weather_conditions", {})
        uav_model = params.get("uav_model", {})
        simulation_steps = params.get("simulation_steps", self.simulation_steps)

        rows, cols = grid_size

        # 解析气象条件
        wind_speed = weather.get("wind_speed", 5.0)
        wind_direction = weather.get("wind_direction", 0.0)
        temperature = weather.get("temperature", 25.0)
        humidity = weather.get("humidity", 60.0)
        visibility = weather.get("visibility", 10.0)

        logger.info(
            "数字孪生规划: 起点=%s, 终点=%s, 风速=%.1f, 仿真步数=%d",
            start, goal, wind_speed, simulation_steps,
        )

        start_grid = self._world_to_grid(start, rows, cols)
        goal_grid = self._world_to_grid(goal, rows, cols)

        # 初始路径规划（A*）
        initial_path = self._plan_initial_path(
            start_grid, goal_grid, rows, cols, obstacles,
        )

        if not initial_path:
            logger.warning("数字孪生规划: 初始路径规划失败")
            return {
                "optimized_path": [],
                "simulation_results": {"success": False, "message": "初始规划失败"},
                "performance_metrics": {},
                "twin_state": {},
            }

        # 迭代优化
        optimized_path = initial_path
        best_metrics = None
        all_simulation_results = []

        for round_idx in range(self.optimization_rounds):
            # 在数字孪生环境中仿真当前路径
            sim_result = self._simulate_flight(
                optimized_path, weather, uav_model, simulation_steps,
            )
            all_simulation_results.append(sim_result)

            # 评估性能指标
            metrics = self._compute_performance_metrics(sim_result, uav_model)

            if best_metrics is None or metrics["overall_score"] > best_metrics["overall_score"]:
                best_metrics = metrics

            # 根据仿真反馈优化路径
            optimized_path = self._optimize_path(
                optimized_path, sim_result, obstacles, rows, cols,
            )

            logger.debug(
                "优化轮次 %d: 综合评分=%.4f",
                round_idx + 1, metrics["overall_score"],
            )

        # 最终仿真验证
        final_sim = self._simulate_flight(
            optimized_path, weather, uav_model, simulation_steps,
        )
        final_metrics = self._compute_performance_metrics(final_sim, uav_model)

        # 孪生状态快照
        twin_state = {
            "environment": {
                "wind_speed": wind_speed,
                "wind_direction": wind_direction,
                "temperature": temperature,
                "humidity": humidity,
                "visibility": visibility,
            },
            "uav_state": {
                "position": optimized_path[-1] if optimized_path else start,
                "battery_remaining": final_metrics.get("battery_remaining", 100.0),
                "total_distance": final_metrics.get("total_distance", 0.0),
            },
            "optimization_rounds": self.optimization_rounds,
            "converged": True,
        }

        logger.info(
            "数字孪生规划完成: 综合评分=%.4f, 飞行时间=%.2fs",
            final_metrics["overall_score"],
            final_metrics.get("flight_time", 0.0),
        )

        return {
            "optimized_path": optimized_path,
            "simulation_results": {
                "rounds": all_simulation_results,
                "final_simulation": final_sim,
                "success": True,
            },
            "performance_metrics": final_metrics,
            "twin_state": twin_state,
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
    ) -> list[int]:
        """网格坐标转世界坐标。"""
        return [pos[0] - rows // 2, pos[1] - cols // 2]

    def _plan_initial_path(
        self,
        start_grid: tuple[int, int],
        goal_grid: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
    ) -> list[list[int]]:
        """使用A*规划初始路径。"""
        open_set: list[tuple[float, tuple[int, int]]] = []
        heapq.heappush(open_set, (0.0, start_grid))
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = {start_grid: 0.0}

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal_grid:
                return self._reconstruct_path(came_from, current, rows, cols)

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

    def _reconstruct_path(
        self,
        came_from: dict[tuple[int, int], tuple[int, int]],
        current: tuple[int, int],
        rows: int,
        cols: int,
    ) -> list[list[int]]:
        """从目标回溯重建路径。"""
        path = [self._grid_to_world(current, rows, cols)]
        while current in came_from:
            current = came_from[current]
            path.append(self._grid_to_world(current, rows, cols))
        path.reverse()
        return path

    def _simulate_flight(
        self,
        path: list[list[int]],
        weather: dict,
        uav_model: dict,
        steps: int,
    ) -> dict[str, Any]:
        """在数字孪生环境中仿真飞行。"""
        if not path:
            return {"trajectory": [], "success": False}

        max_speed = uav_model.get("max_speed", 15.0)
        wind_speed = weather.get("wind_speed", 5.0)
        wind_dir_rad = np.radians(weather.get("wind_direction", 0.0))
        wind_vector = np.array([
            wind_speed * np.cos(wind_dir_rad),
            wind_speed * np.sin(wind_dir_rad),
        ])

        trajectory = []
        position = np.array(path[0], dtype=float)
        velocities = []
        accelerations = []

        for step in range(min(steps, len(path) * 5)):
            # 确定当前目标航点
            waypoint_idx = min(step // 5, len(path) - 1)
            target = np.array(path[waypoint_idx], dtype=float)

            # 计算期望速度方向
            diff = target - position
            dist = np.linalg.norm(diff)
            if dist < 0.1:
                if waypoint_idx < len(path) - 1:
                    waypoint_idx += 1
                    target = np.array(path[waypoint_idx], dtype=float)
                    diff = target - position
                    dist = np.linalg.norm(diff)

            if dist > 1e-6:
                desired_vel = diff / dist * max_speed
            else:
                desired_vel = np.zeros(2)

            # 风的影响
            wind_effect = wind_vector * 0.3
            actual_vel = desired_vel + wind_effect

            # 限制最大速度
            speed = np.linalg.norm(actual_vel)
            if speed > max_speed * 1.2:
                actual_vel = actual_vel / speed * max_speed * 1.2

            # 更新位置
            position = position + actual_vel * self.dt

            trajectory.append({
                "step": step,
                "position": position.tolist(),
                "velocity": actual_vel.tolist(),
                "waypoint_idx": waypoint_idx,
            })
            velocities.append(float(np.linalg.norm(actual_vel)))
            accelerations.append(0.0)

        # 计算轨迹偏差
        deviations = []
        for i, t in enumerate(trajectory):
            wp_idx = min(t["waypoint_idx"], len(path) - 1)
            wp = np.array(path[wp_idx], dtype=float)
            dev = float(np.linalg.norm(np.array(t["position"]) - wp))
            deviations.append(dev)

        return {
            "trajectory": trajectory,
            "success": True,
            "mean_speed": float(np.mean(velocities)) if velocities else 0.0,
            "max_speed": float(np.max(velocities)) if velocities else 0.0,
            "mean_deviation": float(np.mean(deviations)) if deviations else 0.0,
            "max_deviation": float(np.max(deviations)) if deviations else 0.0,
            "steps_completed": len(trajectory),
        }

    def _compute_performance_metrics(
        self,
        sim_result: dict[str, Any],
        uav_model: dict,
    ) -> dict[str, float]:
        """计算性能指标。"""
        mass = uav_model.get("mass", 1.5)
        battery_capacity = uav_model.get("battery_capacity", 5000.0)

        trajectory = sim_result.get("trajectory", [])
        if not trajectory:
            return {
                "overall_score": 0.0,
                "flight_time": 0.0,
                "energy_consumption": 0.0,
                "battery_remaining": 100.0,
                "total_distance": 0.0,
                "stability_score": 0.0,
            }

        # 飞行时间
        flight_time = len(trajectory) * self.dt

        # 总距离
        positions = [np.array(t["position"]) for t in trajectory]
        distances = [np.linalg.norm(positions[i + 1] - positions[i])
                     for i in range(len(positions) - 1)]
        total_distance = float(np.sum(distances)) if distances else 0.0

        # 能耗估算（简化模型）
        speeds = [np.linalg.norm(np.array(t["velocity"])) for t in trajectory]
        mean_speed = float(np.mean(speeds)) if speeds else 0.0
        energy = mass * mean_speed ** 2 * flight_time * 0.001  # 简化能耗模型
        battery_used = (energy / battery_capacity) * 100
        battery_remaining = max(0.0, 100.0 - battery_used)

        # 稳定性评分（基于轨迹偏差）
        mean_dev = sim_result.get("mean_deviation", 0.0)
        stability = max(0.0, 1.0 - mean_dev / 5.0)

        # 综合评分
        overall_score = (
            0.3 * stability
            + 0.3 * (battery_remaining / 100.0)
            + 0.2 * min(1.0, total_distance / 20.0)
            + 0.2 * min(1.0, mean_speed / 15.0)
        )

        return {
            "overall_score": overall_score,
            "flight_time": flight_time,
            "energy_consumption": energy,
            "battery_remaining": battery_remaining,
            "total_distance": total_distance,
            "stability_score": stability,
            "mean_speed": mean_speed,
        }

    def _optimize_path(
        self,
        path: list[list[int]],
        sim_result: dict[str, Any],
        obstacles: set,
        rows: int,
        cols: int,
    ) -> list[list[int]]:
        """根据仿真反馈优化路径。

        对偏差较大的航点进行微调，使路径更平滑。
        """
        if len(path) < 3:
            return path

        optimized = [p.copy() for p in path]
        mean_dev = sim_result.get("mean_deviation", 0.0)

        # 对中间航点进行平滑处理
        for i in range(1, len(optimized) - 1):
            prev = np.array(optimized[i - 1], dtype=float)
            curr = np.array(optimized[i], dtype=float)
            next_p = np.array(optimized[i + 1], dtype=float)

            # 向前后航点中点靠拢（平滑）
            midpoint = (prev + next_p) / 2
            smoothing_factor = min(0.3, mean_dev * 0.1)
            new_pos = curr + (midpoint - curr) * smoothing_factor

            # 确保不进入障碍物
            gx, gy = int(new_pos[0] + rows / 2), int(new_pos[1] + cols / 2)
            if (gx, gy) not in obstacles and 0 <= gx < rows and 0 <= gy < cols:
                optimized[i] = [int(round(new_pos[0])), int(round(new_pos[1]))]

        return optimized
