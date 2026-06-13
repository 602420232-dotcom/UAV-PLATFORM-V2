"""快速扩展随机树路径规划算法（RRT）。

基于随机采样的路径规划方法，通过在空间中随机采样点并
向最近树节点扩展来构建搜索树。适用于高维空间和复杂障碍物环境。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class RapidlyExploringTreePlanner:
    """基础RRT路径规划器。

    从起点开始构建随机树，每次迭代采样随机点并向最近节点
   扩展固定步长。当树到达目标附近时提取路径。
    不保证最优性，但适用于复杂环境和高维空间。

    Args:
        config: 配置字典，支持以下参数：
            - max_iterations: 最大迭代次数，默认2000
            - step_size: 扩展步长，默认1.0
            - goal_bias: 目标采样概率，默认0.1
            - goal_radius: 到达目标的距离阈值，默认1.5
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.max_iterations: int = self.config.get("max_iterations", 2000)
        self.step_size: float = self.config.get("step_size", 1.0)
        self.goal_bias: float = self.config.get("goal_bias", 0.1)
        self.goal_radius: float = self.config.get("goal_radius", 1.5)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行RRT路径规划。

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

        _start = params.get("start", (0, 0))
        start: tuple[float, float] = (float(_start[0]), float(_start[1]))
        _goal = params.get("goal", (10, 10))
        goal: tuple[float, float] = (float(_goal[0]), float(_goal[1]))
        grid_size = params.get("grid_size", (50, 50))
        obstacles = set(map(tuple, params.get("obstacles", [])))

        logger.info(
            "RRT规划: 起点=%s, 终点=%s, 最大迭代=%d",
            start, goal, self.max_iterations,
        )

        rows, cols = grid_size

        # 树节点和父节点
        nodes: list[tuple[float, float]] = [start]
        parents: dict[int, int | None] = {0: None}

        # 采样范围
        x_min = min(start[0], goal[0]) - 5
        x_max = max(start[0], goal[0]) + 5
        y_min = min(start[1], goal[1]) - 5
        y_max = max(start[1], goal[1]) + 5

        for iteration in range(self.max_iterations):
            # 采样随机点（带目标偏向）
            if np.random.rand() < self.goal_bias:
                rand_point = np.array(goal, dtype=float)
            else:
                rand_point = np.array([
                    np.random.uniform(x_min, x_max),
                    np.random.uniform(y_min, y_max),
                ])

            # 找到最近节点
            nearest_idx = self._find_nearest(nodes, rand_point)
            nearest = np.array(nodes[nearest_idx])

            # 向随机点方向扩展
            diff = rand_point - nearest
            dist = np.linalg.norm(diff)
            if dist < 1e-6:
                continue

            step = min(self.step_size, float(dist))
            new_point = nearest + (diff / dist) * step

            # 碰撞检查
            if self._check_collision(tuple(new_point), obstacles):
                continue

            # 检查路径是否无碰撞
            if self._check_line_collision(nodes[nearest_idx], tuple(new_point), obstacles):
                continue

            # 添加新节点
            new_idx = len(nodes)
            nodes.append(tuple(new_point))
            parents[new_idx] = nearest_idx

            # 检查是否到达目标
            if np.linalg.norm(np.array(new_point) - np.array(goal)) < self.goal_radius:
                # 连接到目标
                if not self._check_line_collision(tuple(new_point), goal, obstacles):
                    goal_idx = len(nodes)
                    nodes.append(goal)
                    parents[goal_idx] = new_idx

                    path = self._extract_path(goal_idx, nodes, parents)
                    cost = self._compute_cost(path)
                    logger.info(
                        "RRT完成: 代价=%.2f, 迭代=%d, 树节点=%d",
                        cost, iteration + 1, len(nodes),
                    )
                    return {
                        "path": path,
                        "cost": cost,
                        "iterations": iteration + 1,
                        "tree_size": len(nodes),
                    }

        logger.warning("RRT未在最大迭代内找到路径")
        return {
            "path": [],
            "cost": float("inf"),
            "iterations": self.max_iterations,
            "tree_size": len(nodes),
        }

    def _find_nearest(
        self,
        nodes: list,
        point: np.ndarray,
    ) -> int:
        """找到距离point最近的节点索引。"""
        return int(
            min(
                range(len(nodes)),
                key=lambda i: float(np.linalg.norm(np.array(nodes[i]) - point)),
            )
        )

    def _check_collision(
        self,
        point: tuple,
        obstacles: set,
    ) -> bool:
        """检查点是否在障碍物上。"""
        px, py = int(round(point[0])), int(round(point[1]))
        return (px, py) in obstacles

    def _check_line_collision(
        self,
        p1: tuple,
        p2: tuple,
        obstacles: set,
    ) -> bool:
        """检查两点之间的线段是否与障碍物碰撞。"""
        n_checks = max(int(np.linalg.norm(np.array(p2) - np.array(p1)) * 2), 2)
        for t in np.linspace(0, 1, n_checks):
            px = int(round(p1[0] + t * (p2[0] - p1[0])))
            py = int(round(p1[1] + t * (p2[1] - p1[1])))
            if (px, py) in obstacles:
                return True
        return False

    def _extract_path(
        self,
        idx: int | None,
        nodes: list,
        parents: dict,
    ) -> list[list[int]]:
        """从树中提取路径。"""
        path = []
        while idx is not None:
            path.append([int(round(nodes[idx][0])), int(round(nodes[idx][1]))])
            idx = parents.get(idx)
        path.reverse()
        return path

    def _compute_cost(self, path: list) -> float:
        """计算路径代价。"""
        cost = 0.0
        for i in range(len(path) - 1):
            cost += float(np.linalg.norm(
                np.array(path[i + 1]) - np.array(path[i])
            ))
        return cost
