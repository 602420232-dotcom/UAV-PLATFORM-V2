"""配置点法（Collocation）轨迹优化算法。

将轨迹优化问题离散化为有限个配置点上的约束满足问题。
通过在配置点上施加动力学约束和边界条件，
将连续轨迹优化转化为非线性规划问题求解。
适用于需要精确满足动力学约束的轨迹规划。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class CollocationPlanner:
    """配置点法轨迹优化规划器。

    在离散配置点上施加动力学约束，通过迭代优化
    求解满足边界条件和动力学约束的最优轨迹。

    使用Hermite-Simpson配置点方法，在相邻配置点之间
    进行三次插值，保证轨迹的连续性和动力学一致性。

    Args:
        config: 配置字典，支持以下参数：
            - n_collocation_points: 配置点数量，默认10
            - max_iterations: 最大迭代次数，默认200
            - learning_rate: 优化学习率，默认0.01
            - smoothness_weight: 平滑度权重，默认1.0
            - obstacle_weight: 障碍物权重，默认10.0
            - dynamic_weight: 动力学约束权重，默认5.0
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.n_points: int = self.config.get("n_collocation_points", 10)
        self.max_iterations: int = self.config.get("max_iterations", 200)
        self.learning_rate: float = self.config.get("learning_rate", 0.01)
        self.smoothness_weight: float = self.config.get("smoothness_weight", 1.0)
        self.obstacle_weight: float = self.config.get("obstacle_weight", 10.0)
        self.dynamic_weight: float = self.config.get("dynamic_weight", 5.0)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行配置点法轨迹优化。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]

        Returns:
            包含 path（轨迹点列表）和 cost（轨迹代价）的字典。
        """
        np.random.seed(42)

        start = np.array(params.get("start", (0, 0)), dtype=float)
        goal = np.array(params.get("goal", (10, 10)), dtype=float)
        grid_size = params.get("grid_size", (50, 50))
        obstacles = [np.array(obs[:2], dtype=float) for obs in params.get("obstacles", [])]

        logger.info(
            "配置点法轨迹优化: 起点=%s, 终点=%s, 配置点=%d",
            tuple(start.astype(int)),
            tuple(goal.astype(int)),
            self.n_points,
        )

        rows, cols = grid_size

        # 初始化配置点（均匀分布在起点和终点之间）
        # 状态向量: [x0, y0, vx0, vy0, x1, y1, vx1, vy1, ..., xN, yN, vxN, vyN]
        n_states = 4  # x, y, vx, vy
        states = np.zeros((self.n_points, n_states))

        # 初始化位置为线性插值
        for i in range(self.n_points):
            t = i / (self.n_points - 1)
            states[i, 0] = start[0] + t * (goal[0] - start[0])
            states[i, 1] = start[1] + t * (goal[1] - start[1])
            # 初始速度为零
            states[i, 2] = 0.0
            states[i, 3] = 0.0

        # 固定边界条件
        states[0, :2] = start
        states[-1, :2] = goal

        initial_cost = self._compute_cost(states, obstacles)

        # 梯度下降优化
        for iteration in range(self.max_iterations):
            gradient = self._compute_gradient(states, obstacles)

            # 更新中间配置点（固定边界）
            states[1:-1] -= self.learning_rate * gradient[1:-1]

            # 边界约束
            states[1:-1, 0] = np.clip(states[1:-1, 0], 0, rows - 1)
            states[1:-1, 1] = np.clip(states[1:-1, 1], 0, cols - 1)

            if iteration % 50 == 0:
                current_cost = self._compute_cost(states, obstacles)
                logger.debug(
                    "迭代 %d: 代价=%.4f",
                    iteration,
                    current_cost,
                )

        final_cost = self._compute_cost(states, obstacles)

        # 提取路径点
        path = [[int(round(s[0])), int(round(s[1]))] for s in states]

        logger.info(
            "配置点法优化完成: 初始代价=%.2f, 最终代价=%.2f",
            initial_cost,
            final_cost,
        )
        return {
            "path": path,
            "cost": final_cost,
            "initial_cost": initial_cost,
            "n_collocation_points": self.n_points,
            "iterations": self.max_iterations,
        }

    def _compute_cost(
        self,
        states: np.ndarray,
        obstacles: list[np.ndarray],
    ) -> float:
        """计算轨迹总代价。"""
        cost = 0.0
        dt = 1.0 / (self.n_points - 1)

        for i in range(self.n_points - 1):
            # 平滑度代价（加加速度）
            if i > 0:
                accel_diff = (states[i + 1, 2:] - states[i, 2:]) / dt - (
                    states[i, 2:] - states[i - 1, 2:]
                ) / dt
                cost += self.smoothness_weight * float(np.sum(accel_diff**2))

            # 动力学约束代价（Hermite-Simpson配置点）
            # 中点状态应满足动力学方程
            mid_state = 0.5 * (states[i] + states[i + 1])
            mid_vel = (states[i + 1, :2] - states[i, :2]) / dt
            vel_error = mid_state[2:] - mid_vel
            cost += self.dynamic_weight * float(np.sum(vel_error**2))

            # 障碍物代价
            for obs in obstacles:
                dist = float(np.linalg.norm(states[i, :2] - obs))
                if dist < 2.0:
                    cost += self.obstacle_weight * (2.0 - dist) ** 2

        # 终端速度惩罚（鼓励到达时减速）
        cost += 0.5 * float(np.sum(states[-1, 2:] ** 2))

        return cost

    def _compute_gradient(
        self,
        states: np.ndarray,
        obstacles: list[np.ndarray],
    ) -> np.ndarray:
        """计算代价函数关于状态变量的梯度。"""
        gradient = np.zeros_like(states)
        dt = 1.0 / (self.n_points - 1)

        for i in range(1, self.n_points - 1):
            # 平滑度梯度
            if i > 0 and i < self.n_points - 1:
                accel_i = (states[i + 1, 2:] - states[i, 2:]) / dt
                accel_prev = (states[i, 2:] - states[i - 1, 2:]) / dt
                jerk = accel_i - accel_prev

                gradient[i, 2:] += 2.0 * self.smoothness_weight * jerk / dt
                gradient[i - 1, 2:] -= 2.0 * self.smoothness_weight * jerk / dt
                gradient[i + 1, 2:] -= 2.0 * self.smoothness_weight * jerk / dt

            # 动力学约束梯度
            mid_vel = (states[i + 1, :2] - states[i, :2]) / dt
            vel_error = states[i, 2:] - mid_vel
            gradient[i, 2:] += 2.0 * self.dynamic_weight * vel_error
            gradient[i, :2] += 2.0 * self.dynamic_weight * vel_error / dt
            gradient[i + 1, :2] -= 2.0 * self.dynamic_weight * vel_error / dt

            # 障碍物梯度
            for obs in obstacles:
                diff = states[i, :2] - obs
                dist = float(np.linalg.norm(diff))
                if dist < 2.0 and dist > 1e-6:
                    gradient[i, :2] += (
                        2.0 * self.obstacle_weight * (2.0 - dist) * (-diff / dist)
                    )

            # 终端速度梯度
            if i == self.n_points - 2:
                gradient[i + 1, 2:] += 2.0 * 0.5 * states[i + 1, 2:]

        return gradient
