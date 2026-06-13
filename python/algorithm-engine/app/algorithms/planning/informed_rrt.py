"""Informed RRT 路径规划算法。

RRT的改进版本，一旦找到初始路径后，利用椭圆采样策略
在以起点和终点为焦点的椭圆内进行有偏向的采样，
逐步优化路径质量直至收敛。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class InformedRRTPlanner:
    """Informed RRT路径规划器。

    在找到初始解后，构建以起点和终点为焦点的椭圆采样区域，
    通过有偏向的采样逐步缩短路径，实现渐近最优性。

    Args:
        config: 配置字典，支持以下参数：
            - max_iterations: 最大迭代次数，默认2000
            - step_size: 扩展步长，默认1.0
            - goal_bias: 目标采样概率，默认0.05
            - goal_radius: 到达目标的距离阈值，默认1.5
            - rewire_radius: 重连半径，默认3.0
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.max_iterations: int = self.config.get("max_iterations", 2000)
        self.step_size: float = self.config.get("step_size", 1.0)
        self.goal_bias: float = self.config.get("goal_bias", 0.05)
        self.goal_radius: float = self.config.get("goal_radius", 1.5)
        self.rewire_radius: float = self.config.get("rewire_radius", 3.0)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行Informed RRT路径规划。

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
            "Informed RRT规划: 起点=%s, 终点=%s, 最大迭代=%d",
            tuple(start.astype(int)),
            tuple(goal.astype(int)),
            self.max_iterations,
        )

        rows, cols = grid_size

        # 树结构
        nodes: list[np.ndarray] = [start.copy()]
        parents: dict[int, int | None] = {0: None}
        costs: dict[int, float] = {0: 0.0}

        # 采样范围
        x_min = min(start[0], goal[0]) - 5
        x_max = max(start[0], goal[0]) + 5
        y_min = min(start[1], goal[1]) - 5
        y_max = max(start[1], goal[1]) + 5

        best_cost = float("inf")
        best_goal_idx: int | None = None

        for iteration in range(self.max_iterations):
            # 采样策略：找到解后使用椭圆采样
            if best_goal_idx is not None:
                rand_point = self._elliptical_sample(start, goal, float(best_cost))
            elif np.random.rand() < self.goal_bias:
                rand_point = goal.copy()
            else:
                rand_point = np.array(
                    [
                        np.random.uniform(x_min, x_max),
                        np.random.uniform(y_min, y_max),
                    ]
                )

            # 找最近节点
            nearest_idx = self._find_nearest(nodes, rand_point)
            nearest = nodes[nearest_idx]

            # 扩展
            diff = rand_point - nearest
            dist = np.linalg.norm(diff)
            if dist < 1e-6:
                continue

            step = min(self.step_size, float(dist))
            new_point = nearest + (diff / dist) * step

            # 碰撞检查
            if self._check_collision(new_point, obstacles):
                continue
            if self._check_line_collision(nearest, new_point, obstacles):
                continue

            # 选择最优父节点
            new_idx = len(nodes)
            best_parent = nearest_idx
            best_new_cost = costs[nearest_idx] + np.linalg.norm(nearest - new_point)

            for i in range(len(nodes)):
                d = np.linalg.norm(nodes[i] - new_point)
                if d < self.rewire_radius:
                    c = costs[i] + d
                    if c < best_new_cost and not self._check_line_collision(nodes[i], new_point, obstacles):
                        best_parent = i
                        best_new_cost = c

            nodes.append(new_point)
            parents[new_idx] = best_parent
            costs[new_idx] = float(best_new_cost)

            # 重连
            for i in range(len(nodes) - 1):
                d = np.linalg.norm(nodes[i] - new_point)
                if d < self.rewire_radius:
                    new_cost = costs[new_idx] + d
                    if new_cost < costs[i] and not self._check_line_collision(nodes[i], new_point, obstacles):
                        parents[i] = new_idx
                        costs[i] = float(new_cost)

            # 检查是否到达目标
            if np.linalg.norm(new_point - goal) < self.goal_radius:
                if not self._check_line_collision(new_point, goal, obstacles):
                    goal_idx = len(nodes)
                    nodes.append(goal.copy())
                    goal_cost = best_new_cost + np.linalg.norm(new_point - goal)
                    parents[goal_idx] = new_idx
                    costs[goal_idx] = float(goal_cost)

                    if goal_cost < best_cost:
                        best_cost = goal_cost
                        best_goal_idx = goal_idx

        if best_goal_idx is None:
            logger.warning("Informed RRT未找到路径")
            return {
                "path": [],
                "cost": float("inf"),
                "iterations": self.max_iterations,
            }

        path = self._extract_path(best_goal_idx, nodes, parents)
        logger.info(
            "Informed RRT完成: 代价=%.2f, 迭代=%d, 树节点=%d",
            best_cost,
            self.max_iterations,
            len(nodes),
        )
        return {
            "path": path,
            "cost": best_cost,
            "iterations": self.max_iterations,
            "tree_size": len(nodes),
        }

    def _elliptical_sample(
        self,
        c1: np.ndarray,
        c2: np.ndarray,
        best_cost: float,
    ) -> np.ndarray:
        """在以c1和c2为焦点的椭圆内采样。"""
        center = (c1 + c2) / 2.0
        dist_to_center = float(np.linalg.norm(c2 - c1)) / 2.0

        # 椭圆半长轴
        a = best_cost / 2.0
        if a < dist_to_center:
            return np.random.uniform(
                min(c1[0], c2[0]) - 5,
                max(c1[0], c2[0]) + 5,
                size=2,
            )

        # 椭圆半短轴
        b = np.sqrt(max(float(a) ** 2 - dist_to_center**2, 0.0))

        # 在单位圆内均匀采样
        while True:
            x = np.random.uniform(-1, 1)
            y = np.random.uniform(-1, 1)
            if x**2 + y**2 <= 1.0:
                break

        # 旋转到椭圆坐标系
        angle = np.arctan2(c2[1] - c1[1], c2[0] - c1[0])
        cos_a, sin_a = np.cos(angle), np.sin(angle)

        # 椭圆上的点
        px = a * x
        py = b * y

        # 旋转回世界坐标
        wx = center[0] + px * cos_a - py * sin_a
        wy = center[1] + px * sin_a + py * cos_a

        return np.array([wx, wy])

    def _find_nearest(self, nodes: list, point: np.ndarray) -> int:
        """找到最近节点索引。"""
        return int(min(range(len(nodes)), key=lambda i: float(np.linalg.norm(nodes[i] - point))))

    def _check_collision(self, point: np.ndarray, obstacles: set) -> bool:
        """检查点是否在障碍物上。"""
        px, py = int(round(point[0])), int(round(point[1]))
        return (px, py) in obstacles

    def _check_line_collision(self, p1: np.ndarray, p2: np.ndarray, obstacles: set) -> bool:
        """检查线段是否与障碍物碰撞。"""
        n_checks = max(int(np.linalg.norm(p2 - p1) * 2), 2)
        for t in np.linspace(0, 1, n_checks):
            px = int(round(p1[0] + t * (p2[0] - p1[0])))
            py = int(round(p1[1] + t * (p2[1] - p1[1])))
            if (px, py) in obstacles:
                return True
        return False

    def _extract_path(self, idx: int | None, nodes: list, parents: dict) -> list[list[int]]:
        """提取路径。"""
        path = []
        while idx is not None:
            path.append([int(round(nodes[idx][0])), int(round(nodes[idx][1]))])
            idx = parents.get(idx)
        path.reverse()
        return path
