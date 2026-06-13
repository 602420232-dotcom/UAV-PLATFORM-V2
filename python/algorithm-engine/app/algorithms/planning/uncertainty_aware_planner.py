"""不确定性感知路径规划算法。

考虑气象预报不确定性的路径规划器，基于蒙特卡洛采样生成多条
候选路径并评估鲁棒性，选择在不确定性条件下表现最稳定的路径。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class UncertaintyAwarePlanner:
    """不确定性感知路径规划器。

    在气象预报存在不确定性的场景下，通过蒙特卡洛方法对不确定性场
    进行多次采样，为每次采样实例规划路径，最终从候选路径集中选择
    鲁棒性最优的路径。鲁棒性评估基于路径在所有采样场景下的平均
    表现和最差表现。

    Args:
        config: 配置字典，支持以下参数：
            - n_samples: 蒙特卡洛采样数，默认30
            - confidence_level: 置信水平，默认0.95
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.n_samples: int = self.config.get("n_samples", 30)
        self.confidence_level: float = self.config.get("confidence_level", 0.95)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行不确定性感知路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 [x, y]
                - goal: 终点坐标 [x, y]
                - grid_size: 网格尺寸 [rows, cols]
                - obstacles: 障碍物列表 list[list[int]]
                - uncertainty_field: 不确定性场矩阵（二维数组，值域[0,1]）
                - n_samples: 蒙特卡洛采样数，可选
                - confidence_level: 置信水平，可选

        Returns:
            包含以下键的字典：
                - robust_path: 鲁棒路径
                - candidate_paths: 候选路径集
                - robustness_score: 鲁棒性评分
                - uncertainty_analysis: 不确定性分析结果
        """
        np.random.seed(42)

        start = params.get("start", [0, 0])
        goal = params.get("goal", [10, 10])
        grid_size = params.get("grid_size", [50, 50])
        obstacles = set(map(tuple, params.get("obstacles", [])))
        uncertainty_field_input = params.get("uncertainty_field", None)
        n_samples = params.get("n_samples", self.n_samples)
        confidence_level = params.get("confidence_level", self.confidence_level)

        rows, cols = grid_size

        # 构建不确定性场
        if uncertainty_field_input is not None:
            uncertainty_field = np.array(uncertainty_field_input, dtype=float)
        else:
            uncertainty_field = np.random.rand(rows, cols) * 0.3

        if uncertainty_field.shape != (rows, cols):
            uncertainty_field = np.random.rand(rows, cols) * 0.3

        logger.info(
            "不确定性感知规划: 起点=%s, 终点=%s, 采样数=%d, 置信水平=%.2f",
            start, goal, n_samples, confidence_level,
        )

        start_grid = self._world_to_grid(start, rows, cols)
        goal_grid = self._world_to_grid(goal, rows, cols)

        # 蒙特卡洛采样：为每个采样实例规划路径
        candidate_paths: list[list[list[int]]] = []
        candidate_costs: list[float] = []
        sample_risk_profiles: list[list[float]] = []

        for sample_idx in range(n_samples):
            # 根据不确定性场生成扰动后的风险场景
            perturbed_field = self._sample_scenario(
                uncertainty_field, rows, cols,
            )

            # 在扰动场景下执行A*规划
            path, cost = self._plan_on_scenario(
                start_grid, goal_grid, rows, cols,
                obstacles, perturbed_field,
            )

            if path:
                candidate_paths.append(path)
                candidate_costs.append(cost)
                # 记录路径上各点的风险值
                risk_profile = self._get_path_risk_profile(
                    path, perturbed_field, rows, cols,
                )
                sample_risk_profiles.append(risk_profile)

        if not candidate_paths:
            logger.warning("不确定性感知规划未找到可行路径")
            return {
                "robust_path": [],
                "candidate_paths": [],
                "robustness_score": 0.0,
                "uncertainty_analysis": {
                    "mean_cost": 0.0,
                    "std_cost": 0.0,
                    "worst_case_cost": 0.0,
                    "confidence_interval": [0.0, 0.0],
                    "n_valid_samples": 0,
                },
            }

        # 评估每条候选路径的鲁棒性
        robustness_scores = self._evaluate_robustness(
            candidate_paths, uncertainty_field, rows, cols, n_samples,
        )

        # 选择鲁棒性最优的路径
        best_idx = int(np.argmax(robustness_scores))
        robust_path = candidate_paths[best_idx]

        # 不确定性分析
        costs_arr = np.array(candidate_costs)
        uncertainty_analysis = {
            "mean_cost": float(np.mean(costs_arr)),
            "std_cost": float(np.std(costs_arr)),
            "worst_case_cost": float(np.max(costs_arr)),
            "best_case_cost": float(np.min(costs_arr)),
            "confidence_interval": [
                float(np.percentile(costs_arr, (1 - confidence_level) * 100 / 2)),
                float(np.percentile(costs_arr, (1 + confidence_level) * 100 / 2)),
            ],
            "n_valid_samples": len(candidate_paths),
            "n_total_samples": n_samples,
        }

        logger.info(
            "不确定性感知规划完成: 鲁棒性=%.4f, 候选路径数=%d",
            robustness_scores[best_idx], len(candidate_paths),
        )

        return {
            "robust_path": robust_path,
            "candidate_paths": candidate_paths,
            "robustness_score": float(robustness_scores[best_idx]),
            "uncertainty_analysis": uncertainty_analysis,
        }

    def _world_to_grid(
        self, pos: list, rows: int, cols: int,
    ) -> tuple[int, int]:
        """世界坐标转网格坐标。"""
        gx = int(pos[0] + rows / 2)
        gy = int(pos[1] + cols / 2)
        return (max(0, min(gx, rows - 1)), max(0, min(gy, cols - 1)))

    def _grid_to_world(
        self, pos: tuple[int, int], rows: int, cols: int,
    ) -> list[int]:
        """网格坐标转世界坐标。"""
        return [pos[0] - rows // 2, pos[1] - cols // 2]

    def _sample_scenario(
        self,
        uncertainty_field: np.ndarray,
        rows: int,
        cols: int,
    ) -> np.ndarray:
        """根据不确定性场生成一个采样场景。

        使用不确定性场作为标准差，生成高斯扰动。
        """
        perturbation = np.random.randn(rows, cols) * uncertainty_field
        scenario = np.clip(uncertainty_field + perturbation, 0.0, 1.0)
        return scenario

    def _plan_on_scenario(
        self,
        start_grid: tuple[int, int],
        goal_grid: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
        risk_field: np.ndarray,
    ) -> tuple[list[list[int]], float]:
        """在给定风险场景下执行A*规划。"""
        open_set: list[tuple[float, tuple[int, int]]] = []
        heapq.heappush(open_set, (0.0, start_grid))
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = {start_grid: 0.0}

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal_grid:
                path = self._reconstruct_path(came_from, current, rows, cols)
                return path, g_score[current]

            for neighbor in self._get_neighbors(current, rows, cols, obstacles):
                dist_cost = 1.0
                nx, ny = neighbor
                risk_cost = float(risk_field[nx, ny])
                step_cost = dist_cost + 0.3 * risk_cost
                tentative_g = g_score[current] + step_cost

                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = float(abs(neighbor[0] - goal_grid[0]) + abs(neighbor[1] - goal_grid[1]))
                    f_score = tentative_g + h
                    heapq.heappush(open_set, (f_score, neighbor))

        return [], float("inf")

    def _get_neighbors(
        self,
        pos: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
    ) -> list[tuple[int, int]]:
        """获取有效邻居节点（4连通）。"""
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = pos[0] + dx, pos[1] + dy
            if 0 <= nx < rows and 0 <= ny < cols and (nx, ny) not in obstacles:
                neighbors.append((nx, ny))
        return neighbors

    def _reconstruct_path(
        self,
        came_from: dict[tuple[int, int], tuple[int, int]],
        current: tuple[int, int],
        rows: int,
        cols: int,
    ) -> list[list[int]]:
        """从目标回溯重建路径。"""
        path = [self._grid_to_world(current, rows, cols)]
        while current in came_from:
            current = came_from[current]
            path.append(self._grid_to_world(current, rows, cols))
        path.reverse()
        return path

    def _get_path_risk_profile(
        self,
        path: list[list[int]],
        risk_field: np.ndarray,
        rows: int,
        cols: int,
    ) -> list[float]:
        """获取路径上各点的风险值。"""
        profile = []
        for p in path:
            gx, gy = self._world_to_grid(p, rows, cols)
            gx = max(0, min(gx, rows - 1))
            gy = max(0, min(gy, cols - 1))
            profile.append(float(risk_field[gx, gy]))
        return profile

    def _evaluate_robustness(
        self,
        candidate_paths: list[list[list[int]]],
        uncertainty_field: np.ndarray,
        rows: int,
        cols: int,
        n_eval_samples: int,
    ) -> list[float]:
        """评估候选路径的鲁棒性。

        对每条候选路径在多个采样场景下评估代价，鲁棒性评分基于
        平均代价和方差（越低越好）。
        """
        scores = []
        for path in candidate_paths:
            path_costs = []
            for _ in range(min(n_eval_samples, 10)):
                scenario = self._sample_scenario(uncertainty_field, rows, cols)
                cost = 0.0
                for p in path:
                    gx, gy = self._world_to_grid(p, rows, cols)
                    gx = max(0, min(gx, rows - 1))
                    gy = max(0, min(gy, cols - 1))
                    cost += float(scenario[gx, gy])
                path_costs.append(cost)

            mean_cost = np.mean(path_costs)
            std_cost = np.std(path_costs)
            # 鲁棒性评分：均值越低、方差越小，评分越高
            if mean_cost > 1e-6:
                score = 1.0 / (mean_cost + std_cost)
            else:
                score = 1.0
            scores.append(score)

        return scores
