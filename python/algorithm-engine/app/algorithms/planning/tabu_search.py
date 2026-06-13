"""禁忌搜索路径规划算法。

基于记忆机制的元启发式搜索算法，通过禁忌表避免重复搜索，
使用特赦规则在特定条件下允许访问禁忌解，从而跳出局部最优。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class TabuSearchPlanner:
    """禁忌搜索路径规划器。

    从初始路径出发，在邻域中搜索更优解，使用禁忌表记录
    最近访问过的解以避免循环，通过特赦规则保留历史最优解。

    Args:
        config: 配置字典，支持以下参数：
            - max_iterations: 最大迭代次数，默认300
            - tabu_tenure: 禁忌表长度，默认20
            - num_neighbors: 每次迭代的邻域解数量，默认10
            - num_waypoints: 路径中间航点数量，默认10
            - perturbation_scale: 扰动幅度，默认3.0
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.max_iterations: int = self.config.get("max_iterations", 300)
        self.tabu_tenure: int = self.config.get("tabu_tenure", 20)
        self.num_neighbors: int = self.config.get("num_neighbors", 10)
        self.num_waypoints: int = self.config.get("num_waypoints", 10)
        self.perturbation_scale: float = self.config.get("perturbation_scale", 3.0)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行禁忌搜索路径规划。

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
            "禁忌搜索规划: 起点=%s, 终点=%s, 禁忌长度=%d",
            tuple(start.astype(int)),
            tuple(goal.astype(int)),
            self.tabu_tenure,
        )

        rows, cols = grid_size

        # 初始化路径
        current_path = np.zeros((self.num_waypoints, 2))
        for i in range(self.num_waypoints):
            t = (i + 1) / (self.num_waypoints + 1)
            current_path[i] = start + t * (goal - start)
            current_path[i] += np.random.randn(2) * 2.0
        current_path[:, 0] = np.clip(current_path[:, 0], 0, rows - 1)
        current_path[:, 1] = np.clip(current_path[:, 1], 0, cols - 1)

        current_cost = self._evaluate(current_path, start, goal, obstacles)
        best_path = current_path.copy()
        best_cost = current_cost

        tabu_list: list[int] = []  # 存储被修改的航点索引

        for iteration in range(self.max_iterations):
            # 生成邻域解
            neighbors = []
            neighbor_costs = []
            neighbor_moves = []

            for _ in range(self.num_neighbors):
                neighbor = current_path.copy()
                wp_idx = np.random.randint(self.num_waypoints)
                neighbor[wp_idx] += np.random.randn(2) * self.perturbation_scale
                neighbor[wp_idx, 0] = np.clip(neighbor[wp_idx, 0], 0, rows - 1)
                neighbor[wp_idx, 1] = np.clip(neighbor[wp_idx, 1], 0, cols - 1)
                cost = self._evaluate(neighbor, start, goal, obstacles)
                neighbors.append(neighbor)
                neighbor_costs.append(cost)
                neighbor_moves.append(wp_idx)

            # 选择最优的非禁忌解（或满足特赦规则的禁忌解）
            best_neighbor_idx = -1
            best_neighbor_cost = float("inf")

            for i, (cost, move) in enumerate(zip(neighbor_costs, neighbor_moves)):
                is_tabu = move in tabu_list

                # 特赦规则：如果解优于历史最优，允许访问
                if is_tabu and cost < best_cost:
                    best_neighbor_idx = i
                    best_neighbor_cost = cost
                    break
                elif not is_tabu and cost < best_neighbor_cost:
                    best_neighbor_idx = i
                    best_neighbor_cost = cost

            if best_neighbor_idx >= 0:
                current_path = neighbors[best_neighbor_idx]
                current_cost = best_neighbor_cost

                # 更新禁忌表
                move = neighbor_moves[best_neighbor_idx]
                if move in tabu_list:
                    tabu_list.remove(move)
                tabu_list.append(move)
                if len(tabu_list) > self.tabu_tenure:
                    tabu_list.pop(0)

                if current_cost < best_cost:
                    best_cost = current_cost
                    best_path = current_path.copy()

            if iteration % 50 == 0:
                logger.debug(
                    "迭代 %d: 当前代价=%.2f, 最优代价=%.2f, 禁忌表长度=%d",
                    iteration,
                    current_cost,
                    best_cost,
                    len(tabu_list),
                )

        full_path = [start] + [wp.copy() for wp in best_path] + [goal]
        cost = self._compute_cost(full_path)

        logger.info("禁忌搜索完成: 代价=%.2f, 迭代=%d", cost, self.max_iterations)
        return {
            "path": [[int(round(p[0])), int(round(p[1]))] for p in full_path],
            "cost": cost,
            "iterations": self.max_iterations,
        }

    def _evaluate(
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
