"""社会力模型（Social Force Model）路径规划算法。

基于社会力学的多智能体运动模型。每个智能体受到以下力的作用：
- 目标吸引力：驱动智能体向目标移动
- 智能体间排斥力：避免与其他智能体碰撞
- 障碍物排斥力：避免与障碍物碰撞
通过牛顿第二定律更新速度和位置。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class SocialForcePlanner:
    """社会力模型路径规划器。

    基于Helbing等人提出的社会力模型，模拟多智能体
    在共享空间中的运动行为。每个智能体受到目标引力、
    其他智能体斥力和障碍物斥力的综合作用。

    Args:
        config: 配置字典，支持以下参数：
            - desired_speed: 期望速度，默认1.5
            - relaxation_time: 松弛时间，默认0.5
            - agent_radius: 智能体半径，默认0.5
            - social_force_strength: 智能体间排斥力强度，默认2.0
            - obstacle_force_strength: 障碍物排斥力强度，默认10.0
            - force_range: 力的作用范围，默认5.0
            - max_iterations: 最大仿真步数，默认300
            - dt: 时间步长，默认0.1
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.desired_speed: float = self.config.get("desired_speed", 1.5)
        self.relaxation_time: float = self.config.get("relaxation_time", 0.5)
        self.agent_radius: float = self.config.get("agent_radius", 0.5)
        self.social_strength: float = self.config.get("social_force_strength", 2.0)
        self.obstacle_strength: float = self.config.get("obstacle_force_strength", 10.0)
        self.force_range: float = self.config.get("force_range", 5.0)
        self.max_iterations: int = self.config.get("max_iterations", 300)
        self.dt: float = self.config.get("dt", 0.1)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行社会力模型路径规划。

        Args:
            params: 规划参数字典，包含：
                - agents: 智能体列表，每个智能体为字典，含 start 和 goal
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
            logger.warning("社会力模型: 无智能体输入")
            return {"paths": [], "cost": 0.0}

        logger.info(
            "社会力模型规划: 智能体数=%d, 网格=%s",
            len(agents),
            grid_size,
        )

        rows, cols = grid_size
        n_agents = len(agents)

        # 初始化状态
        positions = np.array([a.get("start", [0, 0]) for a in agents], dtype=float)
        goals = np.array([a.get("goal", [10, 10]) for a in agents], dtype=float)
        velocities = np.zeros((n_agents, 2))

        paths: list[list] = [[] for _ in range(n_agents)]
        total_cost = 0.0

        for step in range(self.max_iterations):
            # 记录当前位置
            for i in range(n_agents):
                paths[i].append(positions[i].copy().tolist())

            # 检查是否所有智能体到达目标
            all_reached = True
            for i in range(n_agents):
                if np.linalg.norm(positions[i] - goals[i]) > self.agent_radius:
                    all_reached = False
                    break

            if all_reached:
                logger.info("社会力模型完成: 所有智能体到达目标, 步数=%d", step + 1)
                break

            # 计算每个智能体受到的合力
            forces = np.zeros((n_agents, 2))

            for i in range(n_agents):
                # 1. 目标驱动力
                desired_dir = goals[i] - positions[i]
                dist_to_goal = np.linalg.norm(desired_dir)
                if dist_to_goal > 1e-6:
                    desired_vel = desired_dir / dist_to_goal * self.desired_speed
                else:
                    desired_vel = np.zeros(2)

                f_drive = (desired_vel - velocities[i]) / self.relaxation_time
                forces[i] += f_drive

                # 2. 智能体间排斥力
                for j in range(n_agents):
                    if i == j:
                        continue
                    f_social = self._social_force(
                        positions[i], velocities[i],
                        positions[j], velocities[j],
                    )
                    forces[i] += f_social

                # 3. 障碍物排斥力
                for obs in obstacles:
                    f_obs = self._obstacle_force(positions[i], obs)
                    forces[i] += f_obs

            # 更新速度和位置（牛顿第二定律，质量=1）
            velocities += forces * self.dt

            # 速度限制
            speeds = np.linalg.norm(velocities, axis=1, keepdims=True)
            mask = speeds.flatten() > self.desired_speed * 2
            velocities[mask] = velocities[mask] / speeds[mask] * self.desired_speed * 2

            positions += velocities * self.dt

            # 边界约束
            positions[:, 0] = np.clip(positions[:, 0], 0, rows - 1)
            positions[:, 1] = np.clip(positions[:, 1], 0, cols - 1)

            total_cost += float(np.sum(np.linalg.norm(forces, axis=1))) * self.dt

        return {
            "paths": [[int(round(p[0])), int(round(p[1]))] for path in paths for p in path],
            "cost": total_cost,
            "steps": self.max_iterations,
        }

    def _social_force(
        self,
        pos_i: np.ndarray,
        vel_i: np.ndarray,
        pos_j: np.ndarray,
        vel_j: np.ndarray,
    ) -> np.ndarray:
        """计算两个智能体之间的社会排斥力。"""
        diff = pos_i - pos_j
        dist = float(np.linalg.norm(diff))

        if dist > self.force_range or dist < 1e-6:
            return np.zeros(2)

        # 指数衰减的排斥力
        direction = diff / dist
        # 考虑相对速度的排斥力增强
        relative_vel = vel_i - vel_j
        approaching = float(-np.dot(relative_vel, direction))

        force_magnitude = self.social_strength * np.exp(
            (2 * self.agent_radius - dist) / self.force_range
        )

        # 如果正在接近，增强排斥力
        if approaching > 0:
            force_magnitude += self.social_strength * approaching / dist

        return force_magnitude * direction

    def _obstacle_force(
        self,
        pos: np.ndarray,
        obs: np.ndarray,
    ) -> np.ndarray:
        """计算障碍物排斥力。"""
        diff = pos - obs
        dist = float(np.linalg.norm(diff))

        if dist > self.force_range or dist < 1e-6:
            return np.zeros(2)

        direction = diff / dist
        force_magnitude = self.obstacle_strength * (
            1.0 / dist - 1.0 / self.force_range
        ) * (1.0 / dist**2)

        return force_magnitude * direction
