"""梯度下降路径优化算法。

对初始路径进行梯度下降优化的方法。
通过定义包含路径长度、平滑度、障碍物距离等项的代价函数，
沿梯度方向迭代优化路径点位置，生成更短更平滑的路径。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class GradientDescentPlanner:
    """梯度下降路径优化器。

    对初始路径进行梯度下降优化，使路径更短、更平滑、
    更远离障碍物。代价函数由以下几项组成：
    - 路径长度代价
    - 平滑度代价（曲率惩罚）
    - 障碍物距离惩罚

    Args:
        config: 配置字典，支持以下参数：
            - learning_rate: 学习率，默认0.01
            - max_iterations: 最大迭代次数，默认200
            - smoothness_weight: 平滑度权重，默认0.5
            - obstacle_weight: 障碍物惩罚权重，默认10.0
            - obstacle_margin: 障碍物安全距离，默认2.0
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.learning_rate: float = self.config.get("learning_rate", 0.01)
        self.max_iterations: int = self.config.get("max_iterations", 200)
        self.smoothness_weight: float = self.config.get("smoothness_weight", 0.5)
        self.obstacle_weight: float = self.config.get("obstacle_weight", 10.0)
        self.obstacle_margin: float = self.config.get("obstacle_margin", 2.0)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行梯度下降路径优化。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]
                - initial_path: 初始路径（可选），如不提供则生成直线

        Returns:
            包含 path（优化后路径点列表）和 cost（路径代价）的字典。
        """
        np.random.seed(42)

        start = np.array(params.get("start", (0, 0)), dtype=float)
        goal = np.array(params.get("goal", (10, 10)), dtype=float)
        grid_size = params.get("grid_size", (50, 50))
        obstacles = [np.array(obs[:2], dtype=float) for obs in params.get("obstacles", [])]
        initial_path = params.get("initial_path", None)

        logger.info(
            "梯度下降路径优化: 起点=%s, 终点=%s, 学习率=%.4f",
            tuple(start.astype(int)),
            tuple(goal.astype(int)),
            self.learning_rate,
        )

        rows, cols = grid_size

        # 初始化路径
        if initial_path is not None and len(initial_path) > 1:
            path = np.array(initial_path, dtype=float)
        else:
            # 生成直线初始路径
            n_waypoints = max(int(np.linalg.norm(goal - start) / 2), 5)
            path = np.linspace(start, goal, n_waypoints)

        # 固定起点和终点
        initial_cost = self._compute_total_cost(path, obstacles)

        # 梯度下降迭代
        for iteration in range(self.max_iterations):
            # 计算梯度
            gradient = self._compute_gradient(path, obstacles)

            # 更新路径点（固定起点和终点）
            path[1:-1] -= self.learning_rate * gradient[1:-1]

            # 边界约束
            path[1:-1, 0] = np.clip(path[1:-1, 0], 0, rows - 1)
            path[1:-1, 1] = np.clip(path[1:-1, 1], 0, cols - 1)

            if iteration % 50 == 0:
                current_cost = self._compute_total_cost(path, obstacles)
                logger.debug(
                    "迭代 %d: 代价=%.4f, 梯度范数=%.6f",
                    iteration,
                    current_cost,
                    float(np.linalg.norm(gradient)),
                )

        final_cost = self._compute_total_cost(path, obstacles)
        optimized_path = [[int(round(p[0])), int(round(p[1]))] for p in path]

        logger.info(
            "梯度下降优化完成: 初始代价=%.2f, 最终代价=%.2f, 迭代=%d",
            initial_cost,
            final_cost,
            self.max_iterations,
        )
        return {
            "path": optimized_path,
            "cost": final_cost,
            "initial_cost": initial_cost,
            "iterations": self.max_iterations,
        }

    def _compute_total_cost(
        self,
        path: np.ndarray,
        obstacles: list[np.ndarray],
    ) -> float:
        """计算路径总代价。"""
        cost = self._length_cost(path)
        cost += self.smoothness_weight * self._smoothness_cost(path)
        cost += self.obstacle_weight * self._obstacle_cost(path, obstacles)
        return float(cost)

    def _length_cost(self, path: np.ndarray) -> float:
        """路径长度代价。"""
        diffs = np.diff(path, axis=0)
        return float(np.sum(np.sqrt(np.sum(diffs**2, axis=1))))

    def _smoothness_cost(self, path: np.ndarray) -> float:
        """平滑度代价（曲率惩罚）。"""
        if len(path) < 3:
            return 0.0
        # 二阶差分作为曲率近似
        second_deriv = path[:-2] - 2 * path[1:-1] + path[2:]
        return float(np.sum(second_deriv**2))

    def _obstacle_cost(
        self,
        path: np.ndarray,
        obstacles: list[np.ndarray],
    ) -> float:
        """障碍物距离惩罚代价。"""
        cost = 0.0
        for point in path:
            for obs in obstacles:
                dist = float(np.linalg.norm(point - obs))
                if dist < self.obstacle_margin:
                    cost += (self.obstacle_margin - dist) ** 2
        return cost

    def _compute_gradient(
        self,
        path: np.ndarray,
        obstacles: list[np.ndarray],
    ) -> np.ndarray:
        """计算代价函数关于路径点的梯度。"""
        n = len(path)
        gradient = np.zeros_like(path)

        # 长度代价梯度
        for i in range(n - 1):
            diff = path[i + 1] - path[i]
            dist = np.linalg.norm(diff)
            if dist > 1e-6:
                direction = diff / dist
                if i > 0:
                    gradient[i] += direction
                if i + 1 < n - 1:
                    gradient[i + 1] -= direction

        # 平滑度代价梯度
        if n >= 3:
            second_deriv = path[:-2] - 2 * path[1:-1] + path[2:]
            for i in range(1, n - 1):
                gradient[i] += 2.0 * self.smoothness_weight * (
                    path[i - 1] - 2 * path[i] + path[min(i + 1, n - 1)]
                )

        # 障碍物代价梯度
        for i in range(1, n - 1):
            for obs in obstacles:
                diff = path[i] - obs
                dist = np.linalg.norm(diff)
                if dist < self.obstacle_margin and dist > 1e-6:
                    gradient[i] += (
                        2.0 * self.obstacle_weight * (self.obstacle_margin - dist) * (-diff / dist)
                    )

        return gradient
