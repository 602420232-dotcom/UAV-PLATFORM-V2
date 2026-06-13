"""遗传算法路径规划算法。

模拟自然选择和遗传机制的进化算法，通过选择、交叉和变异操作
迭代优化路径种群，逐步找到最优路径。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class GeneticAlgorithmPlanner:
    """遗传算法路径规划器。

    将路径编码为染色体，通过选择、交叉、变异等遗传操作
    在种群中迭代搜索最优路径。

    Args:
        config: 配置字典，支持以下参数：
            - population_size: 种群大小，默认50
            - max_generations: 最大进化代数，默认100
            - mutation_rate: 变异概率，默认0.1
            - crossover_rate: 交叉概率，默认0.8
            - tournament_size: 锦标赛选择大小，默认5
            - num_waypoints: 路径中间航点数量，默认8
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.population_size: int = self.config.get("population_size", 50)
        self.max_generations: int = self.config.get("max_generations", 100)
        self.mutation_rate: float = self.config.get("mutation_rate", 0.1)
        self.crossover_rate: float = self.config.get("crossover_rate", 0.8)
        self.tournament_size: int = self.config.get("tournament_size", 5)
        self.num_waypoints: int = self.config.get("num_waypoints", 8)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行遗传算法路径规划。

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
            "遗传算法规划: 起点=%s, 终点=%s, 种群=%d, 代数=%d",
            tuple(start.astype(int)), tuple(goal.astype(int)),
            self.population_size, self.max_generations,
        )

        rows, cols = grid_size
        chrom_length = self.num_waypoints * 2

        # 初始化种群
        population = np.random.rand(self.population_size, chrom_length)
        population[:, 0::2] *= (rows - 1)
        population[:, 1::2] *= (cols - 1)

        best_chromosome = None
        best_fitness = float("inf")

        for gen in range(self.max_generations):
            # 评估适应度
            fitness = np.array([
                self._evaluate(population[i], start, goal, obstacles)
                for i in range(self.population_size)
            ])

            # 记录最优个体
            best_idx = np.argmin(fitness)
            if fitness[best_idx] < best_fitness:
                best_fitness = fitness[best_idx]
                best_chromosome = population[best_idx].copy()

            # 选择
            selected = self._selection(population, fitness)

            # 交叉
            offspring = self._crossover(selected)

            # 变异
            offspring = self._mutation(offspring, rows, cols)

            # 精英保留
            worst_idx = np.argmax([
                self._evaluate(offspring[i], start, goal, obstacles)
                for i in range(self.population_size)
            ])
            offspring[worst_idx] = best_chromosome

            population = offspring

            if gen % 20 == 0:
                logger.debug("第 %d 代: 最优适应度=%.4f", gen, best_fitness)

        # 解码最优路径
        assert best_chromosome is not None
        path = self._decode(best_chromosome, start, goal)
        cost = self._path_cost(path)

        logger.info("遗传算法完成: 代价=%.2f, 代数=%d", cost, self.max_generations)
        return {
            "path": [[int(round(p[0])), int(round(p[1]))] for p in path],
            "cost": cost,
            "generations": self.max_generations,
        }

    def _evaluate(
        self,
        chromosome: np.ndarray,
        start: np.ndarray,
        goal: np.ndarray,
        obstacles: set,
    ) -> float:
        """评估染色体适应度（越小越好）。"""
        waypoints = chromosome.reshape(-1, 2)
        full_path = np.vstack([start, waypoints, goal])

        diffs = np.diff(full_path, axis=0)
        segment_lengths = np.sqrt(np.sum(diffs ** 2, axis=1))
        path_length = np.sum(segment_lengths)

        # 平滑度惩罚（路径转角）
        smoothness = 0.0
        for i in range(1, len(diffs)):
            if np.linalg.norm(diffs[i]) > 1e-6 and np.linalg.norm(diffs[i - 1]) > 1e-6:
                cos_angle = np.dot(diffs[i], diffs[i - 1]) / (
                    np.linalg.norm(diffs[i]) * np.linalg.norm(diffs[i - 1])
                )
                cos_angle = np.clip(cos_angle, -1.0, 1.0)
                smoothness += (1.0 - cos_angle)

        # 障碍物惩罚
        obstacle_penalty = 0.0
        for wp in waypoints:
            wx, wy = int(round(wp[0])), int(round(wp[1]))
            if (wx, wy) in obstacles:
                obstacle_penalty += 200.0

        return path_length + smoothness * 2.0 + obstacle_penalty

    def _selection(
        self, population: np.ndarray, fitness: np.ndarray,
    ) -> np.ndarray:
        """锦标赛选择。"""
        selected = np.zeros_like(population)
        for i in range(self.population_size):
            candidates = np.random.choice(
                self.population_size, self.tournament_size, replace=False,
            )
            winner = candidates[np.argmin(fitness[candidates])]
            selected[i] = population[winner].copy()
        return selected

    def _crossover(self, population: np.ndarray) -> np.ndarray:
        """均匀交叉操作。"""
        offspring = population.copy()
        for i in range(0, self.population_size - 1, 2):
            if np.random.rand() < self.crossover_rate:
                mask = np.random.rand(len(population[i])) < 0.5
                offspring[i][mask], offspring[i + 1][mask] = (
                    offspring[i + 1][mask].copy(),
                    offspring[i][mask].copy(),
                )
        return offspring

    def _mutation(
        self, population: np.ndarray, rows: int, cols: int,
    ) -> np.ndarray:
        """高斯变异操作。"""
        for i in range(self.population_size):
            for j in range(len(population[i])):
                if np.random.rand() < self.mutation_rate:
                    population[i][j] += np.random.randn() * 3.0
                    if j % 2 == 0:
                        population[i][j] = np.clip(population[i][j], 0, rows - 1)
                    else:
                        population[i][j] = np.clip(population[i][j], 0, cols - 1)
        return population

    def _decode(
        self, chromosome: np.ndarray, start: np.ndarray, goal: np.ndarray,
    ) -> list[np.ndarray]:
        """解码染色体为路径。"""
        waypoints = chromosome.reshape(-1, 2)
        return [start] + [wp.copy() for wp in waypoints] + [goal]

    def _path_cost(self, path: list) -> float:
        """计算路径代价。"""
        cost = 0.0
        for i in range(len(path) - 1):
            cost += float(np.linalg.norm(np.array(path[i + 1]) - np.array(path[i])))
        return cost
