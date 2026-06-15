"""最优互惠碰撞避免（ORCA，Optimal Reciprocal Collision Avoidance）算法。

多智能体实时局部碰撞避免方法。每个智能体假设其他智能体
也采取类似的避碰策略，通过线性规划求解最优速度。
保证在有限时间内无碰撞，适用于密集多智能体环境。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ORCAPlanner:
    """ORCA最优互惠碰撞避免规划器。

    每个智能体计算与其他智能体的ORCA半平面约束，
    在约束内选择最接近期望速度的最优速度。
    基于互惠性假设：每个智能体承担一半的避碰责任。

    Args:
        config: 配置字典，支持以下参数：
            - max_speed: 最大速度，默认2.0
            - agent_radius: 智能体半径，默认0.5
            - time_horizon: 时间视界，默认5.0
            - time_horizon_obstacle: 障碍物时间视界，默认3.0
            - max_iterations: 最大仿真步数，默认200
            - dt: 时间步长，默认0.5
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.max_speed: float = self.config.get("max_speed", 2.0)
        self.agent_radius: float = self.config.get("agent_radius", 0.5)
        self.time_horizon: float = self.config.get("time_horizon", 5.0)
        self.time_horizon_obs: float = self.config.get("time_horizon_obstacle", 3.0)
        self.max_iterations: int = self.config.get("max_iterations", 200)
        self.dt: float = self.config.get("dt", 0.5)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行ORCA多智能体碰撞避免规划。

        Args:
            params: 规划参数字典，包含：
                - agents: 智能体列表，每个智能体为字典，含：
                    - start: 起始位置
                    - goal: 目标位置
                    - velocity: 当前速度（可选）
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]

        Returns:
            包含以下键的字典：
                - paths: 每个智能体的路径列表
                - cost: 总代价
        """
        np.random.seed(42)

        agents = params.get("agents", [])
        grid_size = params.get("grid_size", (50, 50))
        obstacles = [np.array(obs[:2], dtype=float) for obs in params.get("obstacles", [])]

        if not agents:
            logger.warning("ORCA规划: 无智能体输入")
            return {"paths": [], "cost": 0.0}

        logger.info(
            "ORCA规划: 智能体数=%d, 网格=%s",
            len(agents),
            grid_size,
        )

        rows, cols = grid_size
        n_agents = len(agents)

        # 初始化智能体状态
        positions = np.array([a.get("start", [0, 0]) for a in agents], dtype=float)
        goals = np.array([a.get("goal", [10, 10]) for a in agents], dtype=float)
        velocities = np.array(
            [a.get("velocity", [0.0, 0.0]) for a in agents], dtype=float
        )

        paths: list[list] = [[] for _ in range(n_agents)]
        total_cost = 0.0

        for step in range(self.max_iterations):
            # 记录当前位置
            for i in range(n_agents):
                paths[i].append(positions[i].copy().tolist())

            # 检查是否所有智能体到达目标
            all_reached = True
            for i in range(n_agents):
                if np.linalg.norm(positions[i] - goals[i]) > 1.0:
                    all_reached = False
                    break

            if all_reached:
                logger.info("ORCA规划完成: 所有智能体到达目标, 步数=%d", step + 1)
                break

            # 为每个智能体计算ORCA速度
            new_velocities = np.zeros_like(velocities)

            for i in range(n_agents):
                # 期望速度：指向目标
                pref_vel = goals[i] - positions[i]
                dist_to_goal = np.linalg.norm(pref_vel)
                if dist_to_goal > 1e-6:
                    pref_vel = pref_vel / dist_to_goal * min(self.max_speed, dist_to_goal)
                else:
                    pref_vel = np.zeros(2)

                # 计算ORCA约束
                orca_planes = []

                # 与其他智能体的ORCA约束
                for j in range(n_agents):
                    if i == j:
                        continue
                    orca_plane = self._compute_orca_plane(
                        positions[i], velocities[i],
                        positions[j], velocities[j],
                    )
                    if orca_plane is not None:
                        orca_planes.append(orca_plane)

                # 与障碍物的ORCA约束
                for obs in obstacles:
                    orca_plane = self._compute_orca_obstacle(
                        positions[i], velocities[i], obs
                    )
                    if orca_plane is not None:
                        orca_planes.append(orca_plane)

                # 在ORCA约束内求解最优速度
                new_vel = self._solve_orca_velocity(pref_vel, orca_planes)
                new_velocities[i] = new_vel

            velocities = new_velocities

            # 更新位置
            positions = positions + velocities * self.dt

            # 边界约束
            positions[:, 0] = np.clip(positions[:, 0], 0, rows - 1)
            positions[:, 1] = np.clip(positions[:, 1], 0, cols - 1)

            total_cost += float(np.sum(np.linalg.norm(velocities, axis=1))) * self.dt

        return {
            "paths": [[int(round(p[0])), int(round(p[1]))] for path in paths for p in path],
            "cost": total_cost,
            "steps": self.max_iterations,
        }

    def _compute_orca_plane(
        self,
        pos_i: np.ndarray,
        vel_i: np.ndarray,
        pos_j: np.ndarray,
        vel_j: np.ndarray,
    ) -> tuple[np.ndarray, float] | None:
        """计算两个智能体之间的ORCA半平面。"""
        relative_pos = pos_j - pos_i
        relative_vel = vel_i - vel_j
        dist = float(np.linalg.norm(relative_pos))
        combined_radius = 2 * self.agent_radius

        if dist < 1e-6:
            # 重叠，选择随机方向
            relative_pos = np.random.randn(2)
            relative_pos = relative_pos / np.linalg.norm(relative_pos) * 0.01

        if dist > combined_radius + self.max_speed * self.time_horizon:
            return None

        # 计算ORCA速度
        w = relative_pos / dist * (dist - combined_radius)
        u = w / self.time_horizon - relative_vel

        if np.linalg.norm(u) < 1e-6:
            return None

        # ORCA半平面法向量
        normal = u / np.linalg.norm(u)
        point = vel_i + 0.5 * u

        return (normal, float(np.dot(normal, point)))

    def _compute_orca_obstacle(
        self,
        pos: np.ndarray,
        vel: np.ndarray,
        obs: np.ndarray,
    ) -> tuple[np.ndarray, float] | None:
        """计算与障碍物的ORCA半平面。"""
        diff = pos - obs
        dist = float(np.linalg.norm(diff))

        safe_dist = self.agent_radius + 1.0  # 障碍物半径设为1.0

        if dist > safe_dist + self.max_speed * self.time_horizon_obs:
            return None

        if dist < 1e-6:
            diff = np.random.randn(2) * 0.01

        w = diff / dist * (dist - safe_dist)
        u = w / self.time_horizon_obs - vel

        if np.linalg.norm(u) < 1e-6:
            return None

        normal = u / np.linalg.norm(u)
        point = vel + u

        return (normal, float(np.dot(normal, point)))

    def _solve_orca_velocity(
        self,
        pref_vel: np.ndarray,
        orca_planes: list[tuple[np.ndarray, float]],
    ) -> np.ndarray:
        """在ORCA半平面约束内求解最优速度。"""
        velocity = pref_vel.copy()

        for normal, offset in orca_planes:
            # 检查速度是否违反约束
            if np.dot(normal, velocity) < offset:
                # 将速度投影到约束半平面上
                velocity = velocity + (offset - np.dot(normal, velocity)) * normal

        # 速度限制
        speed = np.linalg.norm(velocity)
        if speed > self.max_speed:
            velocity = velocity / speed * self.max_speed

        return velocity
