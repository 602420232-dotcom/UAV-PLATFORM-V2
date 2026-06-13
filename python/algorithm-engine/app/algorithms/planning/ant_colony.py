"""蚁群优化路径规划算法。

基于蚂蚁觅食行为的群体智能算法，通过信息素引导搜索最优路径。
蚂蚁在路径上释放信息素，较短的路径上信息素浓度更高，
后续蚂蚁倾向于选择信息素浓度高的路径，从而逐步收敛到最优解。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class AntColonyOptimizer:
    """蚁群优化路径规划器。

    使用信息素和启发式信息引导蚂蚁在网格中搜索从起点到终点的最优路径。
    每只蚂蚁根据转移概率选择下一个节点，迭代更新信息素矩阵。

    Args:
        config: 配置字典，支持以下参数：
            - num_ants: 蚂蚁数量，默认20
            - max_iterations: 最大迭代次数，默认100
            - alpha: 信息素重要性因子，默认1.0
            - beta: 启发式信息重要性因子，默认2.0
            - evaporation_rate: 信息素蒸发率，默认0.1
            - q: 信息素增强常数，默认100.0
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.num_ants: int = self.config.get("num_ants", 20)
        self.max_iterations: int = self.config.get("max_iterations", 100)
        self.alpha: float = self.config.get("alpha", 1.0)
        self.beta: float = self.config.get("beta", 2.0)
        self.evaporation_rate: float = self.config.get("evaporation_rate", 0.1)
        self.q: float = self.config.get("q", 100.0)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行蚁群优化路径规划。

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

        raw_start = params.get("start", (0, 0))
        raw_goal = params.get("goal", (10, 10))
        start: tuple[int, int] = (int(raw_start[0]), int(raw_start[1]))
        goal: tuple[int, int] = (int(raw_goal[0]), int(raw_goal[1]))
        grid_size = tuple(params.get("grid_size", (50, 50)))
        obstacles = set(map(tuple, params.get("obstacles", [])))

        logger.info(
            "蚁群优化规划: 起点=%s, 终点=%s, 网格=%s, 障碍物=%d",
            start,
            goal,
            grid_size,
            len(obstacles),
        )

        rows, cols = grid_size
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

        # 初始化信息素矩阵
        pheromone = np.ones((rows, cols)) * 0.1

        best_path: list[list[int]] = []
        best_cost = float("inf")

        for iteration in range(self.max_iterations):
            all_paths: list[list[tuple[int, int]]] = []
            all_costs: list[float] = []

            for ant in range(self.num_ants):
                path = self._construct_path(
                    start,
                    goal,
                    rows,
                    cols,
                    obstacles,
                    pheromone,
                    directions,
                )
                if path and path[-1] == goal:
                    cost = self._path_cost(path, directions)
                    all_paths.append(path)
                    all_costs.append(cost)
                    if cost < best_cost:
                        best_cost = cost
                        best_path = [[int(p[0]), int(p[1])] for p in path]

            # 更新信息素
            pheromone *= 1.0 - self.evaporation_rate

            for path, cost in zip(all_paths, all_costs):
                deposit = self.q / cost
                for node in path:
                    pheromone[node[0], node[1]] += deposit

            if iteration % 20 == 0:
                logger.debug(
                    "迭代 %d: 最优代价=%.2f, 找到路径的蚂蚁=%d",
                    iteration,
                    best_cost,
                    len(all_paths),
                )

        if not best_path:
            logger.warning("蚁群优化未找到可行路径")
            return {"path": [], "cost": float("inf"), "iterations": self.max_iterations}

        logger.info("蚁群优化完成: 代价=%.2f, 迭代=%d", best_cost, self.max_iterations)
        return {
            "path": best_path,
            "cost": best_cost,
            "iterations": self.max_iterations,
        }

    def _construct_path(
        self,
        start: tuple[int, int],
        goal: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
        pheromone: np.ndarray,
        directions: list,
    ) -> list[tuple[int, int]]:
        """单只蚂蚁构建路径。"""
        path = [start]
        visited = {start}
        current = start
        max_steps = rows * cols

        for _ in range(max_steps):
            if current == goal:
                break

            neighbors = []
            for dx, dy in directions:
                nx, ny = current[0] + dx, current[1] + dy
                if 0 <= nx < rows and 0 <= ny < cols and (nx, ny) not in obstacles and (nx, ny) not in visited:
                    neighbors.append((nx, ny))

            if not neighbors:
                break

            # 计算转移概率
            probabilities = []
            for nb in neighbors:
                dist_to_goal = abs(nb[0] - goal[0]) + abs(nb[1] - goal[1])
                heuristic = 1.0 / (dist_to_goal + 1.0)
                tau = pheromone[nb[0], nb[1]] ** self.alpha
                eta = heuristic**self.beta
                probabilities.append(tau * eta)

            total = sum(probabilities)
            if total < 1e-12:
                break

            probabilities = [p / total for p in probabilities]
            idx = np.random.choice(len(neighbors), p=probabilities)
            current = neighbors[idx]
            path.append(current)
            visited.add(current)

        return path

    def _path_cost(self, path: list[tuple[int, int]], directions: list) -> float:
        """计算路径总代价。"""
        cost = 0.0
        for i in range(len(path) - 1):
            dx = abs(path[i + 1][0] - path[i][0])
            dy = abs(path[i + 1][1] - path[i][1])
            cost += 1.414 if dx + dy == 2 else 1.0
        return cost
