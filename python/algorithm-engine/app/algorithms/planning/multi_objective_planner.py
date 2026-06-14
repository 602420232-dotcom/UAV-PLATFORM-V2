"""多目标路径规划算法。

支持加权求和、帕累托前沿和约束优化三种模式的路径规划器，
可同时优化距离、风险、能耗、时间等多个目标。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class MultiObjectivePlanner:
    """多目标路径规划器。

    支持三种优化模式：
    - weighted_sum: 加权求和模式，将多目标线性加权为单目标
    - pareto: 帕累托模式，生成帕累托最优解集
    - constrained: 约束优化模式，以主目标优化同时约束其他目标

    Args:
        config: 配置字典，支持以下参数：
            - mode: 优化模式，默认"weighted_sum"
            - objectives: 目标列表，每个目标含name/weight/function
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.mode: str = self.config.get("mode", "weighted_sum")
        self.default_objectives = [
            {"name": "distance", "weight": 1.0, "function": "distance"},
            {"name": "risk", "weight": 0.3, "function": "risk"},
            {"name": "energy", "weight": 0.2, "function": "energy"},
        ]

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行多目标路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 [x, y]
                - goal: 终点坐标 [x, y]
                - grid_size: 网格尺寸 [rows, cols]
                - obstacles: 障碍物列表 list[list[int]]
                - objectives: 目标列表 list[dict]，每个dict含：
                    - name: 目标名称
                    - weight: 权重
                    - function: 目标函数类型（distance/risk/energy/smoothness）
                - mode: 优化模式（weighted_sum/pareto/constrained）

        Returns:
            包含以下键的字典：
                - path: 最优路径
                - objective_values: 各目标值
                - pareto_solutions: 帕累托解集
                - tradeoff_analysis: 权衡分析
        """
        np.random.seed(42)

        start = params.get("start", [0, 0])
        goal = params.get("goal", [10, 10])
        grid_size = params.get("grid_size", [50, 50])
        obstacles = set(map(tuple, params.get("obstacles", [])))
        objectives = params.get("objectives", self.default_objectives)
        mode = params.get("mode", self.mode)

        rows, cols = grid_size

        logger.info(
            "多目标规划: 起点=%s, 终点=%s, 模式=%s, 目标数=%d",
            start,
            goal,
            mode,
            len(objectives),
        )

        start_grid = self._world_to_grid(start, rows, cols)
        goal_grid = self._world_to_grid(goal, rows, cols)

        if mode == "weighted_sum":
            result = self._plan_weighted_sum(
                start_grid,
                goal_grid,
                rows,
                cols,
                obstacles,
                objectives,
            )
        elif mode == "pareto":
            result = self._plan_pareto(
                start_grid,
                goal_grid,
                rows,
                cols,
                obstacles,
                objectives,
            )
        elif mode == "constrained":
            result = self._plan_constrained(
                start_grid,
                goal_grid,
                rows,
                cols,
                obstacles,
                objectives,
            )
        else:
            logger.warning("未知优化模式: %s，回退到加权求和", mode)
            result = self._plan_weighted_sum(
                start_grid,
                goal_grid,
                rows,
                cols,
                obstacles,
                objectives,
            )

        # 权衡分析
        tradeoff_analysis = self._analyze_tradeoffs(result, objectives)

        logger.info("多目标规划完成: 模式=%s", mode)
        return result | {"tradeoff_analysis": tradeoff_analysis}

    def _plan_weighted_sum(
        self,
        start_grid: tuple[int, int],
        goal_grid: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
        objectives: list[dict],
    ) -> dict[str, Any]:
        """加权求和模式：将多目标线性加权为单目标A*搜索。"""
        open_set: list[tuple[float, tuple[int, int]]] = []
        heapq.heappush(open_set, (0.0, start_grid))
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], dict[str, float]] = {start_grid: {obj["name"]: 0.0 for obj in objectives}}
        g_total: dict[tuple[int, int], float] = {start_grid: 0.0}

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal_grid:
                path = self._reconstruct_path(came_from, current, rows, cols)
                obj_values = g_score[current]
                total_cost = g_total[current]
                return {
                    "path": path,
                    "objective_values": obj_values,
                    "cost": total_cost,
                    "pareto_solutions": [],
                }

            for neighbor in self._get_neighbors(current, rows, cols, obstacles):
                new_obj_values = {}
                total_step = 0.0
                for obj in objectives:
                    step_cost = self._compute_objective_cost(
                        current,
                        neighbor,
                        obj,
                        rows,
                        cols,
                    )
                    new_obj_values[obj["name"]] = g_score[current][obj["name"]] + step_cost
                    total_step += obj.get("weight", 1.0) * step_cost

                tentative_total = g_total[current] + total_step

                if tentative_total < g_total.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = new_obj_values
                    g_total[neighbor] = tentative_total
                    h = float(abs(neighbor[0] - goal_grid[0]) + abs(neighbor[1] - goal_grid[1]))
                    f_score = tentative_total + h
                    heapq.heappush(open_set, (f_score, neighbor))

        return {
            "path": [],
            "objective_values": {},
            "cost": float("inf"),
            "pareto_solutions": [],
        }

    def _plan_pareto(
        self,
        start_grid: tuple[int, int],
        goal_grid: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
        objectives: list[dict],
    ) -> dict[str, Any]:
        """帕累托模式：通过不同权重组合生成帕累托最优解集。"""
        pareto_solutions = []
        n_weights = len(objectives)

        if n_weights < 2:
            return self._plan_weighted_sum(
                start_grid,
                goal_grid,
                rows,
                cols,
                obstacles,
                objectives,
            )

        # 生成不同的权重组合
        weight_combinations = self._generate_weight_combinations(n_weights, n=20)

        for weights in weight_combinations:
            weighted_objectives = []
            for i, obj in enumerate(objectives):
                weighted_objectives.append(
                    {
                        "name": obj["name"],
                        "weight": weights[i],
                        "function": obj.get("function", "distance"),
                    }
                )

            result = self._plan_weighted_sum(
                start_grid,
                goal_grid,
                rows,
                cols,
                obstacles,
                weighted_objectives,
            )

            if result["path"]:
                pareto_solutions.append(
                    {
                        "path": result["path"],
                        "objective_values": result["objective_values"],
                        "weights": weights,
                        "cost": result["cost"],
                    }
                )

        # 从帕累托解集中选择折中解
        if pareto_solutions:
            # 选择距离帕累托前沿中心最近的解
            obj_arrays = np.array([list(sol["objective_values"].values()) for sol in pareto_solutions])
            # 归一化
            mins = obj_arrays.min(axis=0)
            maxs = obj_arrays.max(axis=0)
            ranges = maxs - mins
            ranges[ranges < 1e-6] = 1.0
            normalized = (obj_arrays - mins) / ranges
            # 到理想点的距离
            distances = np.linalg.norm(normalized, axis=1)
            best_idx = int(np.argmin(distances))
            best_solution = pareto_solutions[best_idx]
        else:
            best_solution = {
                "path": [],
                "objective_values": {},
                "cost": float("inf"),
            }

        return {
            "path": best_solution["path"],
            "objective_values": best_solution.get("objective_values", {}),
            "cost": best_solution.get("cost", float("inf")),
            "pareto_solutions": pareto_solutions,
        }

    def _plan_constrained(
        self,
        start_grid: tuple[int, int],
        goal_grid: tuple[int, int],
        rows: int,
        cols: int,
        obstacles: set,
        objectives: list[dict],
    ) -> dict[str, Any]:
        """约束优化模式：以第一个目标为主目标，其余为约束。"""
        if not objectives:
            return {
                "path": [],
                "objective_values": {},
                "cost": float("inf"),
                "pareto_solutions": [],
            }

        # 主目标
        primary = objectives[0]
        # 约束目标
        constraints = objectives[1:]

        # 使用主目标进行A*搜索，同时检查约束
        open_set: list[tuple[float, tuple[int, int]]] = []
        heapq.heappush(open_set, (0.0, start_grid))
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = {start_grid: 0.0}
        g_multi: dict[tuple[int, int], dict[str, float]] = {start_grid: {obj["name"]: 0.0 for obj in objectives}}

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal_grid:
                path = self._reconstruct_path(came_from, current, rows, cols)
                return {
                    "path": path,
                    "objective_values": g_multi[current],
                    "cost": g_score[current],
                    "pareto_solutions": [],
                }

            for neighbor in self._get_neighbors(current, rows, cols, obstacles):
                step_cost = self._compute_objective_cost(
                    current,
                    neighbor,
                    primary,
                    rows,
                    cols,
                )
                tentative_g = g_score[current] + step_cost

                # 检查约束
                constraint_violated = False
                new_multi = {}
                for obj in objectives:
                    cost = self._compute_objective_cost(
                        current,
                        neighbor,
                        obj,
                        rows,
                        cols,
                    )
                    new_multi[obj["name"]] = g_multi[current][obj["name"]] + cost
                    # 约束检查（阈值设为网格对角线长度）
                    if obj in constraints and new_multi[obj["name"]] > rows + cols:
                        constraint_violated = True
                        break

                if constraint_violated:
                    continue

                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    g_multi[neighbor] = new_multi
                    h = float(abs(neighbor[0] - goal_grid[0]) + abs(neighbor[1] - goal_grid[1]))
                    f_score = tentative_g + h
                    heapq.heappush(open_set, (f_score, neighbor))

        return {
            "path": [],
            "objective_values": {},
            "cost": float("inf"),
            "pareto_solutions": [],
        }

    def _compute_objective_cost(
        self,
        current: tuple[int, int],
        neighbor: tuple[int, int],
        objective: dict,
        rows: int,
        cols: int,
    ) -> float:
        """计算单步的目标代价。"""
        func_type = objective.get("function", "distance")

        if func_type == "distance":
            return 1.0
        elif func_type == "risk":
            # 使用网格位置模拟风险值
            nx, ny = neighbor
            risk_val = (nx * ny) / max(rows * cols, 1) * 0.1
            return risk_val
        elif func_type == "energy":
            # 能耗与高度变化相关（模拟）
            return 1.0 + abs(neighbor[0] - current[0]) * 0.1
        elif func_type == "smoothness":
            return 0.0  # 需要前驱信息，此处简化
        else:
            return 1.0

    def _generate_weight_combinations(
        self,
        n_objectives: int,
        n: int = 20,
    ) -> list[list[float]]:
        """生成权重组合（均匀分布在单纯形上）。"""
        combinations = []
        for _ in range(n):
            weights = np.random.dirichlet(np.ones(n_objectives))
            combinations.append(weights.tolist())
        return combinations

    def _analyze_tradeoffs(
        self,
        result: dict[str, Any],
        objectives: list[dict],
    ) -> dict[str, Any]:
        """分析目标间的权衡关系。"""
        obj_values = result.get("objective_values", {})
        if not obj_values:
            return {"analysis": "无有效目标值", "dominant_objective": None}

        values = np.array(list(obj_values.values()))
        names = list(obj_values.keys())
        total = float(np.sum(values))

        # 各目标占比
        proportions = {name: float(values[i] / total) if total > 1e-6 else 0.0 for i, name in enumerate(names)}

        # 主导目标
        dominant = names[int(np.argmax(values))] if len(values) > 0 else None

        return {
            "analysis": f"路径代价分布: {dict(zip(names, values.tolist()))}",
            "proportions": proportions,
            "dominant_objective": dominant,
            "total_cost": total,
        }

    def _world_to_grid(
        self,
        pos: list,
        rows: int,
        cols: int,
    ) -> tuple[int, int]:
        """世界坐标转网格坐标。"""
        gx = int(pos[0] + rows / 2)
        gy = int(pos[1] + cols / 2)
        return (max(0, min(gx, rows - 1)), max(0, min(gy, cols - 1)))

    def _grid_to_world(
        self,
        pos: tuple[int, int],
        rows: int,
        cols: int,
    ) -> list[int]:
        """网格坐标转世界坐标。"""
        return [pos[0] - rows // 2, pos[1] - cols // 2]

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
