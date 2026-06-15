"""多项式轨迹优化算法。

基于多项式参数化的轨迹优化方法。
将轨迹表示为分段多项式，通过最小化包含时间、能量、
障碍物距离等项的代价函数，求解最优轨迹参数。
适用于需要生成平滑、动力学可行轨迹的场景。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class TrajectoryOptimizationPlanner:
    """多项式轨迹优化规划器。

    将路径表示为分段多项式轨迹，通过优化多项式系数
    生成满足边界条件的最优平滑轨迹。

    代价函数包含：
    - 最小化轨迹能量（加加速度积分）
    - 满足起终点位置和速度约束
    - 障碍物回避软约束

    Args:
        config: 配置字典，支持以下参数：
            - polynomial_order: 多项式阶数，默认5
            - n_segments: 轨迹分段数，默认4
            - max_iterations: 优化迭代次数，默认100
            - learning_rate: 优化学习率，默认0.001
            - energy_weight: 能量权重，默认1.0
            - obstacle_weight: 障碍物权重，默认5.0
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.polynomial_order: int = self.config.get("polynomial_order", 5)
        self.n_segments: int = self.config.get("n_segments", 4)
        self.max_iterations: int = self.config.get("max_iterations", 100)
        self.learning_rate: float = self.config.get("learning_rate", 0.001)
        self.energy_weight: float = self.config.get("energy_weight", 1.0)
        self.obstacle_weight: float = self.config.get("obstacle_weight", 5.0)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行多项式轨迹优化。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]
                - start_vel: 起始速度（可选），默认[0, 0]
                - goal_vel: 终止速度（可选），默认[0, 0]

        Returns:
            包含 path（轨迹点列表）和 cost（轨迹代价）的字典。
        """
        np.random.seed(42)

        start = np.array(params.get("start", (0, 0)), dtype=float)
        goal = np.array(params.get("goal", (10, 10)), dtype=float)
        grid_size = params.get("grid_size", (50, 50))
        obstacles = [np.array(obs[:2], dtype=float) for obs in params.get("obstacles", [])]
        start_vel = np.array(params.get("start_vel", [0, 0]), dtype=float)
        goal_vel = np.array(params.get("goal_vel", [0, 0]), dtype=float)

        logger.info(
            "多项式轨迹优化: 起点=%s, 终点=%s, 阶数=%d, 分段=%d",
            tuple(start.astype(int)),
            tuple(goal.astype(int)),
            self.polynomial_order,
            self.n_segments,
        )

        rows, cols = grid_size

        # 构建边界条件矩阵
        n_coeffs = self.polynomial_order + 1
        n_total_coeffs = n_coeffs * self.n_segments * 2  # x和y方向

        # 初始化多项式系数（使用最小二乘法求解初始解）
        coeffs_x = self._solve_minimum_snap(start[0], goal[0], start_vel[0], goal_vel[0])
        coeffs_y = self._solve_minimum_snap(start[1], goal[1], start_vel[1], goal_vel[1])

        # 梯度下降优化
        for iteration in range(self.max_iterations):
            grad_x = self._compute_snap_gradient(coeffs_x)
            grad_y = self._compute_snap_gradient(coeffs_y)

            # 障碍物梯度
            obs_grad_x, obs_grad_y = self._obstacle_gradient(
                coeffs_x, coeffs_y, obstacles
            )

            # 更新系数（固定边界条件对应的系数）
            coeffs_x[2:] -= self.learning_rate * (
                self.energy_weight * grad_x[2:]
                + self.obstacle_weight * obs_grad_x[2:]
            )
            coeffs_y[2:] -= self.learning_rate * (
                self.energy_weight * grad_y[2:]
                + self.obstacle_weight * obs_grad_y[2:]
            )

        # 采样轨迹点
        path = self._sample_trajectory(coeffs_x, coeffs_y)
        cost = self._compute_trajectory_cost(coeffs_x, coeffs_y, obstacles)

        logger.info(
            "多项式轨迹优化完成: 代价=%.4f, 路径点=%d",
            cost,
            len(path),
        )
        return {
            "path": path,
            "cost": cost,
            "polynomial_order": self.polynomial_order,
            "n_segments": self.n_segments,
        }

    def _solve_minimum_snap(
        self,
        start_pos: float,
        goal_pos: float,
        start_vel: float,
        goal_vel: float,
    ) -> np.ndarray:
        """求解最小加加速度多项式系数。"""
        n = self.polynomial_order + 1

        # 边界条件：位置和速度
        # p(0) = start_pos, p'(0) = start_vel
        # p(T) = goal_pos, p'(T) = goal_vel
        T = 1.0 / self.n_segments

        # 构建约束矩阵
        A = np.zeros((4, n))
        b = np.zeros(4)

        # 起点位置约束
        A[0, 0] = 1.0
        b[0] = start_pos

        # 起点速度约束
        A[1, 1] = 1.0
        b[1] = start_vel

        # 终点位置约束
        for j in range(n):
            A[2, j] = T**j
        b[2] = goal_pos

        # 终点速度约束
        for j in range(1, n):
            A[3, j] = j * T ** (j - 1)
        b[3] = goal_vel

        # 最小二乘求解
        coeffs, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
        return coeffs

    def _compute_snap_gradient(self, coeffs: np.ndarray) -> np.ndarray:
        """计算加加速度代价的梯度。"""
        n = len(coeffs)
        gradient = np.zeros(n)

        # 加加速度是四阶导数，对系数的梯度
        for i in range(4, n):
            # d^4/dt^4 (c_i * t^i) = c_i * i*(i-1)*(i-2)*(i-3) * t^(i-4)
            gradient[i] = coeffs[i] * (i * (i - 1) * (i - 2) * (i - 3)) ** 2

        return gradient

    def _obstacle_gradient(
        self,
        coeffs_x: np.ndarray,
        coeffs_y: np.ndarray,
        obstacles: list[np.ndarray],
    ) -> tuple[np.ndarray, np.ndarray]:
        """计算障碍物代价的梯度。"""
        grad_x = np.zeros_like(coeffs_x)
        grad_y = np.zeros_like(coeffs_y)

        n_samples = 20
        for t in np.linspace(0, 1, n_samples):
            # 计算轨迹点
            px = sum(coeffs_x[j] * t**j for j in range(len(coeffs_x)))
            py = sum(coeffs_y[j] * t**j for j in range(len(coeffs_y)))

            for obs in obstacles:
                diff_x = px - obs[0]
                diff_y = py - obs[1]
                dist = np.sqrt(diff_x**2 + diff_y**2)

                if dist < 3.0 and dist > 1e-6:
                    # 障碍物惩罚梯度
                    penalty = 2.0 * (3.0 - dist) / dist
                    for j in range(2, len(coeffs_x)):
                        grad_x[j] -= penalty * diff_x * t**j
                        grad_y[j] -= penalty * diff_y * t**j

        return grad_x, grad_y

    def _sample_trajectory(
        self,
        coeffs_x: np.ndarray,
        coeffs_y: np.ndarray,
    ) -> list[list[int]]:
        """从多项式系数采样轨迹点。"""
        n_points = 50
        path = []
        for t in np.linspace(0, 1, n_points):
            px = sum(coeffs_x[j] * t**j for j in range(len(coeffs_x)))
            py = sum(coeffs_y[j] * t**j for j in range(len(coeffs_y)))
            path.append([int(round(px)), int(round(py))])
        return path

    def _compute_trajectory_cost(
        self,
        coeffs_x: np.ndarray,
        coeffs_y: np.ndarray,
        obstacles: list[np.ndarray],
    ) -> float:
        """计算轨迹总代价。"""
        # 加加速度代价
        snap_cost = float(np.sum(self._compute_snap_gradient(coeffs_x) ** 2))
        snap_cost += float(np.sum(self._compute_snap_gradient(coeffs_y) ** 2))

        # 障碍物代价
        obs_cost = 0.0
        for t in np.linspace(0, 1, 20):
            px = sum(coeffs_x[j] * t**j for j in range(len(coeffs_x)))
            py = sum(coeffs_y[j] * t**j for j in range(len(coeffs_y)))
            for obs in obstacles:
                dist = np.sqrt((px - obs[0]) ** 2 + (py - obs[1]) ** 2)
                if dist < 3.0:
                    obs_cost += (3.0 - dist) ** 2

        return self.energy_weight * snap_cost + self.obstacle_weight * obs_cost
