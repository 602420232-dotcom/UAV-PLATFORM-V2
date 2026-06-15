"""速度障碍法（Velocity Obstacle）路径规划算法。

基于速度空间的碰撞避免方法。
将障碍物的运动映射到速度空间中，形成速度障碍区域，
UAV选择不在任何速度障碍区域内的最优速度。
适用于动态障碍物环境下的实时避碰。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class VelocityObstaclePlanner:
    """速度障碍法路径规划器。

    在速度空间中构建速度障碍区域，选择避开所有
    速度障碍且最接近期望速度的最优速度。

    速度障碍（VO）的定义：
    对于障碍物B相对于智能体A的运动，VO是使A和B
    在未来某个时刻发生碰撞的所有相对速度的集合。

    Args:
        config: 配置字典，支持以下参数：
            - max_speed: 最大速度，默认3.0
            - agent_radius: 智能体半径，默认0.5
            - obstacle_radius: 障碍物半径，默认0.5
            - time_horizon: 时间视界，默认5.0
            - safety_factor: 安全系数，默认1.2
            - max_iterations: 最大仿真步数，默认200
            - dt: 时间步长，默认0.5
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.max_speed: float = self.config.get("max_speed", 3.0)
        self.agent_radius: float = self.config.get("agent_radius", 0.5)
        self.obstacle_radius: float = self.config.get("obstacle_radius", 0.5)
        self.time_horizon: float = self.config.get("time_horizon", 5.0)
        self.safety_factor: float = self.config.get("safety_factor", 1.2)
        self.max_iterations: int = self.config.get("max_iterations", 200)
        self.dt: float = self.config.get("dt", 0.5)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行速度障碍法路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 [x, y]
                - goal: 终点坐标 [x, y]
                - obstacles: 障碍物列表 list[tuple]
                    每个障碍物可包含速度信息: [x, y, vx, vy]
                - grid_size: 网格尺寸 (int, int)

        Returns:
            包含 path（路径点列表）和 cost（路径代价）的字典。
        """
        np.random.seed(42)

        start = np.array(params.get("start", [0, 0]), dtype=float)
        goal = np.array(params.get("goal", [10, 10]), dtype=float)
        grid_size = params.get("grid_size", (50, 50))
        obstacles_raw = params.get("obstacles", [])

        logger.info(
            "速度障碍法规划: 起点=%s, 终点=%s, 障碍物=%d",
            tuple(start.astype(int)),
            tuple(goal.astype(int)),
            len(obstacles_raw),
        )

        rows, cols = grid_size

        # 解析障碍物（位置+速度）
        obstacles = []
        for obs in obstacles_raw:
            obs_dict = {
                "pos": np.array(obs[:2], dtype=float),
                "vel": np.array(obs[2:4], dtype=float) if len(obs) > 3 else np.zeros(2),
            }
            obstacles.append(obs_dict)

        # 仿真循环
        position = start.copy()
        velocity = np.zeros(2)
        path = [position.copy().tolist()]
        total_cost = 0.0

        for step in range(self.max_iterations):
            # 检查是否到达目标
            if np.linalg.norm(position - goal) < 1.0:
                logger.info("速度障碍法完成: 到达目标, 步数=%d", step + 1)
                break

            # 计算期望速度
            desired_vel = goal - position
            dist = np.linalg.norm(desired_vel)
            if dist > 1e-6:
                desired_vel = desired_vel / dist * min(self.max_speed, dist)
            else:
                desired_vel = np.zeros(2)

            # 计算速度障碍
            vo_constraints = []
            for obs in obstacles:
                vo = self._compute_velocity_obstacle(position, velocity, obs)
                if vo is not None:
                    vo_constraints.append(vo)

            # 在速度障碍约束外选择最优速度
            optimal_vel = self._find_optimal_velocity(desired_vel, vo_constraints)

            # 更新状态
            velocity = optimal_vel
            position = position + velocity * self.dt

            # 边界约束
            position[0] = np.clip(position[0], 0, rows - 1)
            position[1] = np.clip(position[1], 0, cols - 1)

            total_cost += float(np.linalg.norm(velocity)) * self.dt
            path.append(position.copy().tolist())

        return {
            "path": [[int(round(p[0])), int(round(p[1]))] for p in path],
            "cost": total_cost,
            "steps": len(path) - 1,
        }

    def _compute_velocity_obstacle(
        self,
        agent_pos: np.ndarray,
        agent_vel: np.ndarray,
        obstacle: dict,
    ) -> dict[str, Any] | None:
        """计算速度障碍。"""
        obs_pos = obstacle["pos"]
        obs_vel = obstacle["vel"]

        # 相对位置
        rel_pos = obs_pos - agent_pos
        dist = float(np.linalg.norm(rel_pos))

        combined_radius = (self.agent_radius + self.obstacle_radius) * self.safety_factor

        if dist < 1e-6:
            return None

        if dist > combined_radius + self.max_speed * self.time_horizon * 2:
            return None

        # 速度障碍是一个以相对位置为中心的锥形区域
        # 锥的半角由碰撞半径决定
        half_angle = np.arcsin(min(combined_radius / dist, 1.0))
        center_angle = np.arctan2(rel_pos[1], rel_pos[0])

        return {
            "center_angle": center_angle,
            "half_angle": half_angle,
            "dist": dist,
            "obs_vel": obs_vel,
        }

    def _find_optimal_velocity(
        self,
        desired_vel: np.ndarray,
        vo_constraints: list[dict],
    ) -> np.ndarray:
        """在速度障碍约束外寻找最优速度。"""
        # 候选速度采样
        n_candidates = 36
        candidates = []

        # 原始期望速度
        candidates.append(desired_vel.copy())

        # 不同角度和速度的候选
        for i in range(n_candidates):
            angle = 2 * np.pi * i / n_candidates
            for speed_factor in [0.5, 0.75, 1.0]:
                speed = self.max_speed * speed_factor
                vel = np.array([speed * np.cos(angle), speed * np.sin(angle)])
                candidates.append(vel)

        best_vel = desired_vel.copy()
        best_score = -float("inf")

        for vel in candidates:
            # 检查是否在速度障碍内
            in_vo = False
            for vo in vo_constraints:
                if self._is_in_velocity_obstacle(vel, vo):
                    in_vo = True
                    break

            if in_vo:
                continue

            # 评价：越接近期望速度越好
            score = -float(np.linalg.norm(vel - desired_vel))

            if score > best_score:
                best_score = score
                best_vel = vel.copy()

        # 如果所有候选都在VO内，选择最安全的
        if best_score == -float("inf"):
            best_vel = self._find_safest_velocity(desired_vel, vo_constraints)

        # 速度限制
        speed = np.linalg.norm(best_vel)
        if speed > self.max_speed:
            best_vel = best_vel / speed * self.max_speed

        return best_vel

    def _is_in_velocity_obstacle(
        self,
        vel: np.ndarray,
        vo: dict,
    ) -> bool:
        """检查速度是否在速度障碍内。"""
        # 相对于障碍物速度的速度
        rel_vel = vel - vo["obs_vel"]

        if np.linalg.norm(rel_vel) < 1e-6:
            return True

        # 检查相对速度方向是否在锥形内
        vel_angle = np.arctan2(rel_vel[1], rel_vel[0])
        angle_diff = abs(vel_angle - vo["center_angle"])

        # 归一化角度差到[0, pi]
        if angle_diff > np.pi:
            angle_diff = 2 * np.pi - angle_diff

        return angle_diff < vo["half_angle"]

    def _find_safest_velocity(
        self,
        desired_vel: np.ndarray,
        vo_constraints: list[dict],
    ) -> np.ndarray:
        """当所有候选都在VO内时，选择最安全的速度。"""
        best_vel = desired_vel.copy()
        min_penalty = float("inf")

        n_candidates = 36
        for i in range(n_candidates):
            angle = 2 * np.pi * i / n_candidates
            vel = np.array([self.max_speed * np.cos(angle), self.max_speed * np.sin(angle)])

            penalty = 0.0
            for vo in vo_constraints:
                if self._is_in_velocity_obstacle(vel, vo):
                    rel_vel = vel - vo["obs_vel"]
                    vel_angle = np.arctan2(rel_vel[1], rel_vel[0])
                    angle_diff = abs(vel_angle - vo["center_angle"])
                    if angle_diff > np.pi:
                        angle_diff = 2 * np.pi - angle_diff
                    # 距离VO边界的距离作为惩罚
                    margin = vo["half_angle"] - angle_diff
                    penalty += 1.0 / (margin + 0.01)

            if penalty < min_penalty:
                min_penalty = penalty
                best_vel = vel.copy()

        return best_vel
