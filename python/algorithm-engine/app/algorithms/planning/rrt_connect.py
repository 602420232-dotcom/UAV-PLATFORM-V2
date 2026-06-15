"""双向RRT连接（RRT-Connect）路径规划算法。

RRT的改进版本，同时从起点和终点生长两棵随机树，
并在每次扩展后尝试将两棵树的最新节点连接。
收敛速度远快于单树RRT，适用于有狭窄通道的环境。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class RRTConnectPlanner:
    """双向RRT连接路径规划器。

    从起点和终点同时构建两棵随机树，交替扩展，
    每次扩展后尝试连接两棵树。相比单树RRT，
    在复杂环境中收敛更快。

    Args:
        config: 配置字典，支持以下参数：
            - max_iterations: 最大迭代次数，默认2000
            - step_size: 扩展步长，默认1.0
            - goal_bias: 目标采样概率，默认0.05
            - connect_attempts: 连接尝试次数，默认5
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.max_iterations: int = self.config.get("max_iterations", 2000)
        self.step_size: float = self.config.get("step_size", 1.0)
        self.goal_bias: float = self.config.get("goal_bias", 0.05)
        self.connect_attempts: int = self.config.get("connect_attempts", 5)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行RRT-Connect路径规划。

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
            "RRT-Connect规划: 起点=%s, 终点=%s, 最大迭代=%d",
            start,
            goal,
            self.max_iterations,
        )

        rows, cols = grid_size

        # 两棵树的数据结构
        tree_a_nodes: list[tuple[float, float]] = [start]
        tree_a_parents: dict[int, int | None] = {0: None}

        tree_b_nodes: list[tuple[float, float]] = [goal]
        tree_b_parents: dict[int, int | None] = {0: None}

        # 采样范围
        x_min = min(start[0], goal[0]) - 5
        x_max = max(start[0], goal[0]) + 5
        y_min = min(start[1], goal[1]) - 5
        y_max = max(start[1], goal[1]) + 5

        for iteration in range(self.max_iterations):
            # 采样随机点
            if np.random.rand() < self.goal_bias:
                rand_point = np.array(goal, dtype=float)
            else:
                rand_point = np.array(
                    [np.random.uniform(x_min, x_max), np.random.uniform(y_min, y_max)]
                )

            # 树A向随机点扩展
            new_idx_a = self._extend(
                tree_a_nodes, tree_a_parents, rand_point, obstacles
            )

            if new_idx_a is not None:
                # 树B向树A的新节点尝试连接
                new_idx_b = self._connect(
                    tree_b_nodes, tree_b_parents, tree_a_nodes[new_idx_a], obstacles
                )

                if new_idx_b is not None:
                    # 两棵树成功连接，提取完整路径
                    path_a = self._extract_path(new_idx_a, tree_a_nodes, tree_a_parents)
                    path_b = self._extract_path(new_idx_b, tree_b_nodes, tree_b_parents)
                    path_b.reverse()

                    full_path = path_a + path_b
                    cost = self._compute_cost(full_path)

                    logger.info(
                        "RRT-Connect完成: 代价=%.2f, 迭代=%d, 树A=%d, 树B=%d",
                        cost,
                        iteration + 1,
                        len(tree_a_nodes),
                        len(tree_b_nodes),
                    )
                    return {
                        "path": full_path,
                        "cost": cost,
                        "iterations": iteration + 1,
                        "tree_a_size": len(tree_a_nodes),
                        "tree_b_size": len(tree_b_nodes),
                    }

            # 交换两棵树的角色
            tree_a_nodes, tree_b_nodes = tree_b_nodes, tree_a_nodes
            tree_a_parents, tree_b_parents = tree_b_parents, tree_a_parents

        logger.warning("RRT-Connect未在最大迭代内找到路径")
        return {
            "path": [],
            "cost": float("inf"),
            "iterations": self.max_iterations,
        }

    def _extend(
        self,
        nodes: list[tuple[float, float]],
        parents: dict[int, int | None],
        target: np.ndarray,
        obstacles: set,
    ) -> int | None:
        """向目标方向扩展树一步。"""
        nearest_idx = self._find_nearest(nodes, target)
        nearest = np.array(nodes[nearest_idx])

        diff = target - nearest
        dist = np.linalg.norm(diff)
        if dist < 1e-6:
            return None

        step = min(self.step_size, float(dist))
        new_point = nearest + (diff / dist) * step

        if self._check_collision(tuple(new_point), obstacles):
            return None
        if self._check_line_collision(nodes[nearest_idx], tuple(new_point), obstacles):
            return None

        new_idx = len(nodes)
        nodes.append(tuple(new_point))
        parents[new_idx] = nearest_idx
        return new_idx

    def _connect(
        self,
        nodes: list[tuple[float, float]],
        parents: dict[int, int | None],
        target: tuple[float, float],
        obstacles: set,
    ) -> int | None:
        """向目标方向持续扩展直到无法前进或到达目标。"""
        last_idx = None
        for _ in range(self.connect_attempts):
            new_idx = self._extend(
                nodes, parents, np.array(target, dtype=float), obstacles
            )
            if new_idx is None:
                break
            last_idx = new_idx

            # 检查是否到达目标附近
            if np.linalg.norm(np.array(nodes[new_idx]) - np.array(target)) < self.step_size:
                return new_idx

        return last_idx

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
        return path

    def _compute_cost(self, path: list) -> float:
        """计算路径代价。"""
        cost = 0.0
        for i in range(len(path) - 1):
            cost += float(np.linalg.norm(np.array(path[i + 1]) - np.array(path[i])))
        return cost
