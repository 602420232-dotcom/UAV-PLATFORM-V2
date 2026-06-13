"""模拟退火路径规划算法。

基于金属退火过程的随机优化算法，通过接受劣解的概率随温度降低而减小，
从而在搜索初期允许探索较差的解，后期逐步收敛到最优解。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class SimulatedAnnealingPlanner:
    """模拟退火路径规划器。

    从初始路径出发，通过随机扰动生成邻域解，根据Metropolis准则
    决定是否接受新解，温度逐步降低直至收敛。

    Args:
        config: 配置字典，支持以下参数：
            - max_iterations: 最大迭代次数，默认500
            - initial_temperature: 初始温度，默认1000.0
            - cooling_rate: 冷却系数，默认0.99
            - num_waypoints: 路径中间航点数量，默认10
            - perturbation_scale: 扰动幅度，默认2.0
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.max_iterations: int = self.config.get("max_iterations", 500)
        self.initial_temperature: float = self.config.get("initial_temperature", 1000.0)
        self.cooling_rate: float = self.config.get("cooling_rate", 0.99)
        self.num_waypoints: int = self.config.get("num_waypoints", 10)
        self.perturbation_scale: float = self.config.get("perturbation_scale", 2.0)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行模拟退火路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]

        Returns:
            包含 path（路径点列表）和 cost（路径代价）的字典。
        """
        np.random.seed(42)

        start = np.array(params.get("start", (0, 0)), dtype=float)
        goal = np.array(params.get("goal", (10, 10)), dtype=float)
        grid_size = params.get("grid_size", (50, 50))
        obstacles = set(map(tuple, params.get("obstacles", [])))

        logger.info(
            "模拟退火规划: 起点=%s, 终点=%s, 初始温度=%.1f",
            tuple(start.astype(int)),
            tuple(goal.astype(int)),
            self.initial_temperature,
        )

        rows, cols = grid_size

        # 初始化路径：在起点和终点之间均匀分布航点
        current_path = np.zeros((self.num_waypoints, 2))
        for i in range(self.num_waypoints):
            t = (i + 1) / (self.num_waypoints + 1)
            current_path[i] = start + t * (goal - start)
            current_path[i] += np.random.randn(2) * 2.0
        current_path[:, 0] = np.clip(current_path[:, 0], 0, rows - 1)
        current_path[:, 1] = np.clip(current_path[:, 1], 0, cols - 1)

        current_cost = self._evaluate_path(current_path, start, goal, obstacles)
        best_path = current_path.copy()
        best_cost = current_cost
        temperature = self.initial_temperature

        for iteration in range(self.max_iterations):
            # 生成邻域解：随机扰动一个航点
            new_path = current_path.copy()
            wp_idx = np.random.randint(self.num_waypoints)
            new_path[wp_idx] += np.random.randn(2) * self.perturbation_scale
            new_path[wp_idx, 0] = np.clip(new_path[wp_idx, 0], 0, rows - 1)
            new_path[wp_idx, 1] = np.clip(new_path[wp_idx, 1], 0, cols - 1)

            new_cost = self._evaluate_path(new_path, start, goal, obstacles)

            # Metropolis准则
            delta = new_cost - current_cost
            if delta < 0 or np.random.rand() < np.exp(-delta / temperature):
                current_path = new_path
                current_cost = new_cost

                if current_cost < best_cost:
                    best_cost = current_cost
                    best_path = current_path.copy()

            temperature *= self.cooling_rate

            if iteration % 50 == 0:
                logger.debug(
                    "迭代 %d: 温度=%.4f, 当前代价=%.2f, 最优代价=%.2f",
                    iteration,
                    temperature,
                    current_cost,
                    best_cost,
                )

        # 构建最终路径
        full_path = [start] + [wp.copy() for wp in best_path] + [goal]
        cost = self._compute_cost(full_path)

        logger.info("模拟退火完成: 代价=%.2f, 迭代=%d", cost, self.max_iterations)
        return {
            "path": [[int(round(p[0])), int(round(p[1]))] for p in full_path],
            "cost": cost,
            "iterations": self.max_iterations,
        }

    def _evaluate_path(
        self,
        waypoints: np.ndarray,
        start: np.ndarray,
        goal: np.ndarray,
        obstacles: set,
    ) -> float:
        """评估路径代价。"""
        full_path = np.vstack([start, waypoints, goal])
        diffs = np.diff(full_path, axis=0)
        segment_lengths = np.sqrt(np.sum(diffs**2, axis=1))
        path_length = np.sum(segment_lengths)

        obstacle_penalty = 0.0
        for wp in waypoints:
            wx, wy = int(round(wp[0])), int(round(wp[1]))
            if (wx, wy) in obstacles:
                obstacle_penalty += 200.0

        return path_length + obstacle_penalty

    def _compute_cost(self, path: list) -> float:
        """计算路径总代价。"""
        cost = 0.0
        for i in range(len(path) - 1):
            cost += float(np.linalg.norm(np.array(path[i + 1]) - np.array(path[i])))
        return cost
