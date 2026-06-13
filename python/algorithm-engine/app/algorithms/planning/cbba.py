"""基于一致性捆绑算法的多UAV任务分配规划（CBBA）。

Consensus-Based Bundle Algorithm是一种分布式多UAV任务分配算法。
每架UAV独立构建任务捆绑并通过一致性协议与邻居通信，
逐步收敛到全局最优或近优的任务分配方案。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class CBBAPlanner:
    """基于一致性捆绑算法的多机任务分配规划器。

    多架UAV通过分布式一致性协议协同分配任务。
    每架UAV构建自己的任务捆绑列表，通过信息交换达成一致。

    Args:
        config: 配置字典，支持以下参数：
            - num_uavs: UAV数量，默认3
            - max_iterations: 最大一致性迭代次数，默认50
            - max_tasks_per_uav: 每架UAV最大任务数，默认5
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.num_uavs: int = self.config.get("num_uavs", 3)
        self.max_iterations: int = self.config.get("max_iterations", 50)
        self.max_tasks_per_uav: int = self.config.get("max_tasks_per_uav", 5)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行CBBA多机任务分配规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)（主UAV起点）
                - goal: 终点坐标 (int, int)（主UAV终点）
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]
                - tasks: 任务点列表 list[tuple[int, int]]（可选）
                - uav_starts: 各UAV起点列表（可选）

        Returns:
            包含 path（路径点列表）和 cost（路径代价）的字典，
            以及多机分配方案 assignments。
        """
        np.random.seed(42)

        goal = np.array(params.get("goal", (10, 10)), dtype=float)
        grid_size = params.get("grid_size", (50, 50))
        obstacles = set(map(tuple, params.get("obstacles", [])))

        # 任务点：使用障碍物附近的点或随机生成
        tasks_input = params.get("tasks", [])
        if tasks_input:
            tasks = [np.array(t[:2], dtype=float) for t in tasks_input]
        else:
            # 生成默认任务点
            rows, cols = grid_size
            tasks = []
            for _ in range(self.num_uavs * self.max_tasks_per_uav):
                tx = np.random.uniform(0, rows - 1)
                ty = np.random.uniform(0, cols - 1)
                while (int(round(tx)), int(round(ty))) in obstacles:
                    tx = np.random.uniform(0, rows - 1)
                    ty = np.random.uniform(0, cols - 1)
                tasks.append(np.array([tx, ty]))

        # UAV起点
        uav_starts_input = params.get("uav_starts", [])
        if uav_starts_input and len(uav_starts_input) >= self.num_uavs:
            uav_starts = [np.array(s[:2], dtype=float) for s in uav_starts_input[: self.num_uavs]]
        else:
            rows, cols = grid_size
            uav_starts = []
            for i in range(self.num_uavs):
                sx = np.random.uniform(0, rows - 1)
                sy = np.random.uniform(0, cols - 1)
                uav_starts.append(np.array([sx, sy]))

        logger.info(
            "CBBA规划: UAV数=%d, 任务数=%d, 最大迭代=%d",
            self.num_uavs,
            len(tasks),
            self.max_iterations,
        )

        num_tasks = len(tasks)

        # CBBA核心数据结构
        # 每架UAV的任务捆绑列表
        bundles: list[list[int]] = [[] for _ in range(self.num_uavs)]
        # 任务出价（哪个UAV以什么代价竞标该任务）
        bids: dict[int, tuple[int, float]] = {}  # task_idx -> (uav_idx, bid_value)
        # 每架UAV的路径
        uav_paths: list[list[np.ndarray]] = [[uav_starts[i].copy()] for i in range(self.num_uavs)]
        # 每架UAV的路径代价
        uav_costs: list[float] = [0.0] * self.num_uavs

        for iteration in range(self.max_iterations):
            changed = False

            for uav in range(self.num_uavs):
                # 阶段1：构建捆绑（贪心添加最高价值任务）
                for task_idx in range(num_tasks):
                    if task_idx in bundles[uav]:
                        continue
                    if len(bundles[uav]) >= self.max_tasks_per_uav:
                        break

                    # 计算将此任务插入当前路径的最佳位置及其增量代价
                    best_insert_cost, best_pos = self._best_insertion(
                        uav_paths[uav],
                        tasks[task_idx],
                    )
                    bid_value = -best_insert_cost  # 最大化价值（最小化代价）

                    # 检查是否可以赢得竞标
                    if task_idx not in bids or bid_value > bids[task_idx][1]:
                        bids[task_idx] = (uav, bid_value)
                        bundles[uav].append(task_idx)
                        # 插入路径
                        uav_paths[uav].insert(best_pos, tasks[task_idx].copy())
                        uav_costs[uav] += best_insert_cost
                        changed = True

            # 阶段2：一致性（解决冲突）
            for task_idx in list(bids.keys()):
                uav_winner, _ = bids[task_idx]
                # 检查是否有多个UAV声称同一任务
                claim_count = sum(1 for b in bundles if task_idx in b)
                if claim_count > 1:
                    # 只保留赢家的捆绑
                    for uav in range(self.num_uavs):
                        if uav != uav_winner and task_idx in bundles[uav]:
                            bundles[uav].remove(task_idx)
                            # 从路径中移除
                            uav_paths[uav] = [
                                p for p in uav_paths[uav] if not any(np.allclose(p, tasks[task_idx]) for _ in [1])
                            ]
                            # 重建路径
                            uav_paths[uav] = [uav_starts[uav].copy()]
                            for t_idx in bundles[uav]:
                                uav_paths[uav].append(tasks[t_idx].copy())
                            uav_costs[uav] = self._path_cost(uav_paths[uav])
                            changed = True

            if not changed:
                logger.debug("CBBA在第 %d 次迭代收敛", iteration)
                break

        # 构建主UAV的路径（UAV 0）
        main_path = uav_paths[0] if uav_paths[0] else [uav_starts[0].copy()]
        # 添加目标点
        main_path.append(goal.copy())
        total_cost = self._path_cost(main_path)

        # 构建分配方案
        assignments = {}
        for uav in range(self.num_uavs):
            assignments[f"uav_{uav}"] = {
                "tasks": bundles[uav],
                "path": [[int(round(p[0])), int(round(p[1]))] for p in uav_paths[uav]],
                "cost": uav_costs[uav],
            }

        logger.info(
            "CBBA完成: 总代价=%.2f, 迭代=%d, 分配任务=%d",
            total_cost,
            self.max_iterations,
            sum(len(b) for b in bundles),
        )
        return {
            "path": [[int(round(p[0])), int(round(p[1]))] for p in main_path],
            "cost": total_cost,
            "iterations": self.max_iterations,
            "assignments": assignments,
        }

    def _best_insertion(
        self,
        path: list[np.ndarray],
        task: np.ndarray,
    ) -> tuple[float, int]:
        """找到将任务插入路径的最佳位置和增量代价。"""
        best_cost = float("inf")
        best_pos = len(path)

        for pos in range(1, len(path) + 1):
            new_path = path[:pos] + [task.copy()] + path[pos:]
            cost = self._path_cost(new_path)
            if cost < best_cost:
                best_cost = cost
                best_pos = pos

        base_cost = self._path_cost(path)
        return best_cost - base_cost, best_pos

    def _path_cost(self, path: list) -> float:
        """计算路径总代价。"""
        if len(path) < 2:
            return 0.0
        cost = 0.0
        for i in range(len(path) - 1):
            cost += float(np.linalg.norm(np.array(path[i + 1]) - np.array(path[i])))
        return cost
