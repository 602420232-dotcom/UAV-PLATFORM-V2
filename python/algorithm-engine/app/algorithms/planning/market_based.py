"""基于市场拍卖的多UAV任务分配规划算法。

将任务分配建模为拍卖市场，UAV作为买家竞标任务，
通过多轮拍卖机制实现任务分配的全局优化。
支持多种拍卖策略和价格更新规则。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class MarketBasedPlanner:
    """基于市场拍卖的多机任务分配规划器。

    模拟拍卖市场机制，任务作为商品被拍卖，UAV作为买家竞标。
    通过多轮迭代的价格更新和竞标策略，实现任务的最优分配。

    Args:
        config: 配置字典，支持以下参数：
            - num_uavs: UAV数量，默认3
            - max_rounds: 最大拍卖轮数，默认30
            - price_increment: 价格增量系数，默认1.1
            - max_tasks_per_uav: 每架UAV最大任务数，默认5
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.num_uavs: int = self.config.get("num_uavs", 3)
        self.max_rounds: int = self.config.get("max_rounds", 30)
        self.price_increment: float = self.config.get("price_increment", 1.1)
        self.max_tasks_per_uav: int = self.config.get("max_tasks_per_uav", 5)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行基于市场拍卖的多机任务分配规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 (int, int)
                - goal: 终点坐标 (int, int)
                - grid_size: 网格尺寸 (int, int)
                - obstacles: 障碍物列表 list[tuple[int, int]]
                - tasks: 任务点列表 list[tuple[int, int]]（可选）
                - uav_starts: 各UAV起点列表（可选）

        Returns:
            包含 path（路径点列表）和 cost（路径代价）的字典，
            以及拍卖结果 auction_result。
        """
        np.random.seed(42)

        start = np.array(params.get("start", (0, 0)), dtype=float)
        goal = np.array(params.get("goal", (10, 10)), dtype=float)
        grid_size = params.get("grid_size", (50, 50))
        obstacles = set(map(tuple, params.get("obstacles", [])))

        rows, cols = grid_size

        # 任务点
        tasks_input = params.get("tasks", [])
        if tasks_input:
            tasks = [np.array(t[:2], dtype=float) for t in tasks_input]
        else:
            tasks = []
            for _ in range(self.num_uavs * 3):
                tx = np.random.uniform(0, rows - 1)
                ty = np.random.uniform(0, cols - 1)
                while (int(round(tx)), int(round(ty))) in obstacles:
                    tx = np.random.uniform(0, rows - 1)
                    ty = np.random.uniform(0, cols - 1)
                tasks.append(np.array([tx, ty]))

        # UAV起点
        uav_starts_input = params.get("uav_starts", [])
        if uav_starts_input and len(uav_starts_input) >= self.num_uavs:
            uav_starts = [np.array(s[:2], dtype=float) for s in uav_starts_input[:self.num_uavs]]
        else:
            uav_starts = []
            for i in range(self.num_uavs):
                sx = np.random.uniform(0, rows - 1)
                sy = np.random.uniform(0, cols - 1)
                uav_starts.append(np.array([sx, sy]))

        logger.info(
            "市场拍卖规划: UAV数=%d, 任务数=%d, 最大轮数=%d",
            self.num_uavs, len(tasks), self.max_rounds,
        )

        num_tasks = len(tasks)

        # 拍卖状态
        # 任务价格（初始为距离起点的距离）
        prices = np.zeros(num_tasks)
        for t in range(num_tasks):
            min_dist = float("inf")
            for u in range(self.num_uavs):
                d = float(np.linalg.norm(tasks[t] - uav_starts[u]))
                min_dist = min(min_dist, d)
            prices[t] = min_dist

        # 任务分配：task_idx -> uav_idx
        assignment: dict[int, int] = {}
        # UAV已分配任务数
        uav_task_count = np.zeros(self.num_uavs, dtype=int)

        for round_num in range(self.max_rounds):
            all_assigned = True

            for t in range(num_tasks):
                if t in assignment:
                    continue
                all_assigned = False

                # 计算每架UAV对此任务的估值
                values = np.zeros(self.num_uavs)
                for u in range(self.num_uavs):
                    if uav_task_count[u] >= self.max_tasks_per_uav:
                        values[u] = -float("inf")
                    else:
                        # 估值 = 任务价值 - 价格
                        dist = float(np.linalg.norm(tasks[t] - uav_starts[u]))
                        values[u] = dist - prices[t]

                # UAV竞标（选择估值最高的）
                valid_uavs = np.where(values > -float("inf"))[0]
                if len(valid_uavs) == 0:
                    continue

                winner = int(np.argmax(values))
                if values[winner] >= 0:
                    assignment[t] = winner
                    uav_task_count[winner] += 1
                    # 提高价格
                    prices[t] *= self.price_increment

            if all_assigned:
                logger.debug("市场拍卖在第 %d 轮完成所有分配", round_num)
                break

        # 构建各UAV路径
        uav_paths: dict[int, list[list[int]]] = {}
        total_cost = 0.0

        for u in range(self.num_uavs):
            uav_tasks = [t for t, assigned_uav in assignment.items() if assigned_uav == u]
            path = [list(uav_starts[u].astype(int))]
            for t in uav_tasks:
                path.append([int(round(tasks[t][0])), int(round(tasks[t][1]))])
            uav_paths[u] = path
            total_cost += self._path_cost(path)

        # 主UAV路径（UAV 0）
        main_path = uav_paths.get(0, [list(start.astype(int))])
        main_path.append(list(goal.astype(int)))
        main_cost = self._path_cost(main_path)

        # 拍卖结果
        auction_result = {
            "assignment": {f"task_{t}": f"uav_{u}" for t, u in assignment.items()},
            "prices": {f"task_{t}": float(prices[t]) for t in range(num_tasks)},
            "rounds": self.max_rounds,
            "uav_paths": {f"uav_{u}": p for u, p in uav_paths.items()},
        }

        logger.info(
            "市场拍卖完成: 总代价=%.2f, 分配任务=%d/%d, 轮数=%d",
            total_cost, len(assignment), num_tasks, self.max_rounds,
        )
        return {
            "path": main_path,
            "cost": main_cost,
            "auction_result": auction_result,
        }

    def _path_cost(self, path: list[list[int]]) -> float:
        """计算路径代价。"""
        if len(path) < 2:
            return 0.0
        cost = 0.0
        for i in range(len(path) - 1):
            cost += float(np.linalg.norm(
                np.array(path[i + 1]) - np.array(path[i])
            ))
        return cost
