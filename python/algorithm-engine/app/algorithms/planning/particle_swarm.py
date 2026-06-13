"""粒子群优化路径规划算法。

基于鸟群觅食行为的群体智能算法，通过个体最优和全局最优引导搜索。
将路径表示为粒子位置，通过速度更新公式迭代优化路径质量。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ParticleSwarmOptimizer:
    """粒子群优化路径规划器。

    将路径编码为粒子，每个粒子代表一条候选路径。
    通过惯性权重、个体最优和全局最优引导粒子向更优解移动。

    Args:
        config: 配置字典，支持以下参数：
            - num_particles: 粒子数量，默认30
            - max_iterations: 最大迭代次数，默认100
            - w: 惯性权重，默认0.7
            - c1: 个体学习因子，默认1.5
            - c2: 社会学习因子，默认1.5
            - num_waypoints: 路径中间航点数量，默认10
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.num_particles: int = self.config.get("num_particles", 30)
        self.max_iterations: int = self.config.get("max_iterations", 100)
        self.w: float = self.config.get("w", 0.7)
        self.c1: float = self.config.get("c1", 1.5)
        self.c2: float = self.config.get("c2", 1.5)
        self.num_waypoints: int = self.config.get("num_waypoints", 10)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行粒子群优化路径规划。

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
            "粒子群优化规划: 起点=%s, 终点=%s, 粒子数=%d",
            tuple(start.astype(int)),
            tuple(goal.astype(int)),
            self.num_particles,
        )

        rows, cols = grid_size
        dim = self.num_waypoints * 2  # 每个航点有x,y两个维度

        # 初始化粒子群
        positions = np.random.rand(self.num_particles, dim)
        positions[:, 0::2] = positions[:, 0::2] * (rows - 1)
        positions[:, 1::2] = positions[:, 1::2] * (cols - 1)

        velocities = np.random.randn(self.num_particles, dim) * 0.5

        # 评估初始适应度
        fitness = np.array(
            [self._fitness(positions[i], start, goal, obstacles, rows, cols) for i in range(self.num_particles)]
        )

        pbest_positions = positions.copy()
        pbest_fitness = fitness.copy()
        gbest_idx = np.argmin(fitness)
        gbest_position = positions[gbest_idx].copy()
        gbest_fitness = fitness[gbest_idx]

        for iteration in range(self.max_iterations):
            r1 = np.random.rand(self.num_particles, dim)
            r2 = np.random.rand(self.num_particles, dim)

            # 速度更新
            velocities = (
                self.w * velocities
                + self.c1 * r1 * (pbest_positions - positions)
                + self.c2 * r2 * (gbest_position - positions)
            )

            # 位置更新
            positions = positions + velocities

            # 边界约束
            positions[:, 0::2] = np.clip(positions[:, 0::2], 0, rows - 1)
            positions[:, 1::2] = np.clip(positions[:, 1::2], 0, cols - 1)

            # 评估适应度
            fitness = np.array(
                [self._fitness(positions[i], start, goal, obstacles, rows, cols) for i in range(self.num_particles)]
            )

            # 更新个体最优
            improved = fitness < pbest_fitness
            pbest_positions[improved] = positions[improved]
            pbest_fitness[improved] = fitness[improved]

            # 更新全局最优
            current_best_idx = np.argmin(fitness)
            if fitness[current_best_idx] < gbest_fitness:
                gbest_fitness = fitness[current_best_idx]
                gbest_position = positions[current_best_idx].copy()

            if iteration % 20 == 0:
                logger.debug("迭代 %d: 全局最优适应度=%.4f", iteration, gbest_fitness)

        # 从最优粒子提取路径
        path = self._decode_path(gbest_position, start, goal)
        cost = self._compute_path_cost(path)

        logger.info("粒子群优化完成: 代价=%.2f, 迭代=%d", cost, self.max_iterations)
        return {
            "path": [[int(round(p[0])), int(round(p[1]))] for p in path],
            "cost": cost,
            "iterations": self.max_iterations,
        }

    def _fitness(
        self,
        particle: np.ndarray,
        start: np.ndarray,
        goal: np.ndarray,
        obstacles: set,
        rows: int,
        cols: int,
    ) -> float:
        """计算粒子适应度值（越小越好）。"""
        waypoints = particle.reshape(-1, 2)
        full_path = np.vstack([start, waypoints, goal])

        # 路径长度
        diffs = np.diff(full_path, axis=0)
        segment_lengths = np.sqrt(np.sum(diffs**2, axis=1))
        path_length = np.sum(segment_lengths)

        # 障碍物惩罚
        obstacle_penalty = 0.0
        for wp in waypoints:
            wx, wy = int(round(wp[0])), int(round(wp[1]))
            if (wx, wy) in obstacles:
                obstacle_penalty += 100.0
            else:
                # 检查邻近障碍物
                for ox, oy in obstacles:
                    dist = np.sqrt((wx - ox) ** 2 + (wy - oy) ** 2)
                    if dist < 2.0:
                        obstacle_penalty += 10.0 / (dist + 0.1)

        return path_length + obstacle_penalty

    def _decode_path(
        self,
        particle: np.ndarray,
        start: np.ndarray,
        goal: np.ndarray,
    ) -> list[np.ndarray]:
        """从粒子编码解码为路径点序列。"""
        waypoints = particle.reshape(-1, 2)
        return [start] + [wp.copy() for wp in waypoints] + [goal]

    def _compute_path_cost(self, path: list) -> float:
        """计算路径总代价。"""
        cost = 0.0
        for i in range(len(path) - 1):
            cost += float(np.linalg.norm(np.array(path[i + 1]) - np.array(path[i])))
        return cost
