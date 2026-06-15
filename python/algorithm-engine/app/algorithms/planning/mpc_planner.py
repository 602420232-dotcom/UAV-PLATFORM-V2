"""增强型模型预测控制（MPC）路径规划算法。

基于滚动优化的实时路径规划方法。在每个时间步求解有限时域内
的最优控制序列，仅执行第一步控制，然后滚动更新。
考虑UAV动力学约束、障碍物回避和目标追踪。

与基础MPC的区别：支持完整的动力学模型、约束处理和
多目标优化。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class MPCPlannerEnhanced:
    """增强型MPC路径规划器。

    在预测时域内求解最优控制序列，考虑：
    - UAV二阶动力学模型（位置+速度）
    - 控制输入约束（加速度限制）
    - 状态约束（速度限制、边界限制）
    - 障碍物回避约束
    - 目标追踪代价

    Args:
        config: 配置字典，支持以下参数：
            - horizon: 预测时域长度，默认15
            - dt: 时间步长，默认0.5
            - max_accel: 最大加速度，默认1.0
            - max_speed: 最大速度，默认3.0
            - goal_weight: 目标追踪权重，默认10.0
            - control_weight: 控制平滑权重，默认1.0
            - obstacle_weight: 障碍物回避权重，默认20.0
            - obstacle_margin: 障碍物安全距离，默认2.0
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.horizon: int = self.config.get("horizon", 15)
        self.dt: float = self.config.get("dt", 0.5)
        self.max_accel: float = self.config.get("max_accel", 1.0)
        self.max_speed: float = self.config.get("max_speed", 3.0)
        self.goal_weight: float = self.config.get("goal_weight", 10.0)
        self.control_weight: float = self.config.get("control_weight", 1.0)
        self.obstacle_weight: float = self.config.get("obstacle_weight", 20.0)
        self.obstacle_margin: float = self.config.get("obstacle_margin", 2.0)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行MPC路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]
                - current_vel: 当前速度（可选），默认[0, 0]

        Returns:
            包含 path（轨迹点列表）和 cost（轨迹代价）的字典。
        """
        np.random.seed(42)

        start = np.array(params.get("start", (0, 0)), dtype=float)
        goal = np.array(params.get("goal", (10, 10)), dtype=float)
        grid_size = params.get("grid_size", (50, 50))
        obstacles = [np.array(obs[:2], dtype=float) for obs in params.get("obstacles", [])]
        current_vel = np.array(params.get("current_vel", [0, 0]), dtype=float)

        logger.info(
            "MPC规划: 起点=%s, 终点=%s, 时域=%d",
            tuple(start.astype(int)),
            tuple(goal.astype(int)),
            self.horizon,
        )

        rows, cols = grid_size

        # 状态: [x, y, vx, vy]
        state = np.array([start[0], start[1], current_vel[0], current_vel[1]])
        path = [state[:2].copy().tolist()]
        control_sequence = []
        total_cost = 0.0

        max_steps = int(np.linalg.norm(goal - start) / (self.max_speed * self.dt)) + self.horizon * 2

        for step in range(max_steps):
            # 求解当前时域内的最优控制序列
            controls, cost = self._solve_optimal_control(state, goal, obstacles)

            # 执行第一步控制
            accel = controls[0]
            control_sequence.append(accel.tolist())

            # 更新状态（二阶动力学模型）
            state[2] += accel[0] * self.dt  # vx
            state[3] += accel[1] * self.dt  # vy

            # 速度约束
            speed = np.sqrt(state[2] ** 2 + state[3] ** 2)
            if speed > self.max_speed:
                state[2] *= self.max_speed / speed
                state[3] *= self.max_speed / speed

            state[0] += state[2] * self.dt
            state[1] += state[3] * self.dt

            # 边界约束
            state[0] = np.clip(state[0], 0, rows - 1)
            state[1] = np.clip(state[1], 0, cols - 1)

            total_cost += cost
            path.append(state[:2].copy().tolist())

            # 检查是否到达目标
            if np.linalg.norm(state[:2] - goal) < 1.0:
                logger.info(
                    "MPC完成: 步数=%d, 总代价=%.2f",
                    step + 1,
                    total_cost,
                )
                break

        return {
            "path": [[int(round(p[0])), int(round(p[1]))] for p in path],
            "cost": total_cost,
            "control_sequence": control_sequence,
            "steps": len(path) - 1,
        }

    def _solve_optimal_control(
        self,
        state: np.ndarray,
        goal: np.ndarray,
        obstacles: list[np.ndarray],
    ) -> tuple[np.ndarray, float]:
        """求解预测时域内的最优控制序列。

        使用迭代优化方法搜索最优加速度序列。
        """
        n_controls = 4  # 候选控制方向数
        best_controls = np.zeros((self.horizon, 2))
        best_cost = float("inf")

        # 多轮优化
        for round_idx in range(3):
            # 生成候选控制序列
            candidates = self._generate_candidates(best_controls, round_idx)

            for controls in candidates:
                cost = self._evaluate_control_sequence(state, controls, goal, obstacles)
                if cost < best_cost:
                    best_cost = cost
                    best_controls = controls.copy()

        return best_controls, best_cost

    def _generate_candidates(
        self,
        current_best: np.ndarray,
        round_idx: int,
    ) -> list[np.ndarray]:
        """生成候选控制序列。"""
        candidates = [current_best.copy()]

        # 添加扰动
        perturbation_scale = self.max_accel * (0.5 ** round_idx)
        n_perturbations = 8

        for _ in range(n_perturbations):
            perturbed = current_best.copy()
            # 随机选择几个时间步添加扰动
            n_perturb_steps = max(1, self.horizon // 3)
            indices = np.random.choice(self.horizon, n_perturb_steps, replace=False)
            for idx in indices:
                perturbed[idx] += np.random.randn(2) * perturbation_scale
                # 加速度约束
                perturbed[idx] = np.clip(
                    perturbed[idx], -self.max_accel, self.max_accel
                )
            candidates.append(perturbed)

        return candidates

    def _evaluate_control_sequence(
        self,
        state: np.ndarray,
        controls: np.ndarray,
        goal: np.ndarray,
        obstacles: list[np.ndarray],
    ) -> float:
        """评估控制序列的代价。"""
        cost = 0.0
        s = state.copy()

        for t in range(self.horizon):
            # 目标追踪代价
            dist_to_goal = float(np.linalg.norm(s[:2] - goal))
            cost += self.goal_weight * dist_to_goal

            # 控制平滑代价
            cost += self.control_weight * float(np.sum(controls[t] ** 2))

            # 障碍物回避代价
            for obs in obstacles:
                dist = float(np.linalg.norm(s[:2] - obs))
                if dist < self.obstacle_margin:
                    cost += self.obstacle_weight * (self.obstacle_margin - dist) ** 2

            # 前向仿真
            s[2] += controls[t][0] * self.dt
            s[3] += controls[t][1] * self.dt
            speed = np.sqrt(s[2] ** 2 + s[3] ** 2)
            if speed > self.max_speed:
                s[2] *= self.max_speed / speed
                s[3] *= self.max_speed / speed
            s[0] += s[2] * self.dt
            s[1] += s[3] * self.dt

        # 终端代价
        cost += self.goal_weight * 2.0 * float(np.linalg.norm(s[:2] - goal))

        return cost
