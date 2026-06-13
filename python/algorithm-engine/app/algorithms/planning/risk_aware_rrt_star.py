"""风险感知RRT*路径规划算法。

在RRT*算法基础上融入风险约束，节点扩展时主动避开高风险区域，
在保证路径最优性的同时降低飞行风险。
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class RiskAwareRRTStar:
    """风险感知RRT*路径规划器。

    在RRT*采样树扩展过程中引入风险场评估，对高风险区域的节点
    施加额外代价惩罚，并在重连线时考虑风险因素。通过风险阈值
    机制，直接拒绝扩展到超高风险区域的节点。

    Args:
        config: 配置字典，支持以下参数：
            - max_iterations: 最大迭代次数，默认1000
            - step_size: 扩展步长，默认1.0
            - goal_radius: 目标判定半径，默认1.0
            - rewire_radius: 重连线半径，默认3.0
            - risk_threshold: 风险阈值（超过此值的区域禁止进入），默认0.9
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.max_iterations: int = self.config.get("max_iterations", 1000)
        self.step_size: float = self.config.get("step_size", 1.0)
        self.goal_radius: float = self.config.get("goal_radius", 1.0)
        self.rewire_radius: float = self.config.get("rewire_radius", 3.0)
        self.risk_threshold: float = self.config.get("risk_threshold", 0.9)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行风险感知RRT*路径规划。

        Args:
            params: 规划参数字典，包含：
                - start: 起点坐标 [x, y]
                - goal: 终点坐标 [x, y]
                - obstacles: 障碍物列表 list[list[int]]
                - risk_field: 风险场矩阵（二维数组，值域[0,1]）
                - max_iterations: 最大迭代次数，可选
                - risk_threshold: 风险阈值，可选

        Returns:
            包含以下键的字典：
                - path: 路径点列表
                - cost: 路径总代价
                - risk_exposure: 路径风险暴露值
                - tree_size: 搜索树节点数
        """
        np.random.seed(42)

        start = tuple(params.get("start", [0, 0]))
        goal = tuple(params.get("goal", [10, 10]))
        obstacles = params.get("obstacles", [])
        risk_field_input = params.get("risk_field", None)
        max_iterations = params.get("max_iterations", self.max_iterations)
        risk_threshold = params.get("risk_threshold", self.risk_threshold)

        # 构建风险场
        if risk_field_input is not None:
            risk_field = np.array(risk_field_input, dtype=float)
        else:
            risk_field = None

        logger.info(
            "风险感知RRT*规划: 起点=%s, 终点=%s, 迭代=%d, 风险阈值=%.2f",
            start,
            goal,
            max_iterations,
            risk_threshold,
        )

        nodes = [start]
        parents: dict[int, int | None] = {0: None}
        costs: dict[int, float] = {0: 0.0}

        for iteration in range(max_iterations):
            # 采样随机点（10%概率采样目标点）
            if np.random.random() < 0.1:
                rand_point = goal
            else:
                x_min = min(start[0], goal[0]) - 5
                x_max = max(start[0], goal[0]) + 5
                y_min = min(start[1], goal[1]) - 5
                y_max = max(start[1], goal[1]) + 5
                rand_point = (
                    np.random.uniform(x_min, x_max),
                    np.random.uniform(y_min, y_max),
                )

            # 找到最近节点
            nearest_idx = min(
                range(len(nodes)),
                key=lambda i: self._distance(nodes[i], rand_point),
            )
            nearest = np.array(nodes[nearest_idx])
            rand_arr = np.array(rand_point)
            diff = rand_arr - nearest
            dist = np.linalg.norm(diff)

            if dist < 1e-6:
                continue

            # 扩展新节点
            new_point = nearest + diff / dist * min(float(self.step_size), float(dist))

            # 碰撞检测
            if self._check_collision(tuple(new_point), obstacles):
                continue

            # 风险阈值检测
            if risk_field is not None:
                risk_val = self._get_risk_at(tuple(new_point), risk_field)
                if risk_val > risk_threshold:
                    continue

            new_idx = len(nodes)
            nodes.append(tuple(new_point))

            # 选择最优父节点（考虑风险代价）
            best_parent = nearest_idx
            best_cost = costs[nearest_idx] + self._distance(
                nodes[nearest_idx],
                tuple(new_point),
            )
            if risk_field is not None:
                best_cost += self._get_risk_at(tuple(new_point), risk_field)

            for i in range(len(nodes) - 1):
                d = self._distance(nodes[i], tuple(new_point))
                if d < self.rewire_radius:
                    c = costs[i] + d
                    if risk_field is not None:
                        c += self._get_risk_at(tuple(new_point), risk_field)
                    if c < best_cost and not self._check_line_collision(
                        nodes[i],
                        tuple(new_point),
                        obstacles,
                    ):
                        best_parent = i
                        best_cost = c

            parents[new_idx] = best_parent
            costs[new_idx] = best_cost

            # 重连线（考虑风险）
            for i in range(len(nodes) - 1):
                d = self._distance(nodes[i], tuple(new_point))
                if d < self.rewire_radius:
                    new_cost = costs[new_idx] + d
                    if risk_field is not None:
                        new_cost += self._get_risk_at(nodes[i], risk_field) * 0.1
                    if new_cost < costs[i] and not self._check_line_collision(
                        nodes[i],
                        tuple(new_point),
                        obstacles,
                    ):
                        parents[i] = new_idx
                        costs[i] = new_cost

            # 检查是否到达目标
            if self._distance(tuple(new_point), goal) < self.goal_radius:
                path = self._extract_path(new_idx, nodes, parents)
                risk_exposure = self._compute_risk_exposure(path, risk_field)
                logger.info(
                    "风险感知RRT*完成: 代价=%.2f, 风险暴露=%.4f, 树大小=%d",
                    best_cost,
                    risk_exposure,
                    len(nodes),
                )
                return {
                    "path": path,
                    "cost": float(best_cost),
                    "risk_exposure": risk_exposure,
                    "tree_size": len(nodes),
                }

        logger.warning("风险感知RRT*未找到路径")
        return {
            "path": [],
            "cost": float("inf"),
            "risk_exposure": 0.0,
            "tree_size": len(nodes),
        }

    def _distance(self, p1: tuple, p2: tuple) -> float:
        """计算两点间欧氏距离。"""
        return float(np.linalg.norm(np.array(p1) - np.array(p2)))

    def _get_risk_at(self, point: tuple, risk_field: np.ndarray) -> float:
        """获取某点在风险场中的风险值。"""
        rows, cols = risk_field.shape
        gx = int(point[0] + rows / 2)
        gy = int(point[1] + cols / 2)
        gx = max(0, min(gx, rows - 1))
        gy = max(0, min(gy, cols - 1))
        return float(risk_field[gx, gy])

    def _check_collision(self, point: tuple, obstacles: list) -> bool:
        """检测点是否与障碍物碰撞。"""
        for obs in obstacles:
            r = obs[2] if len(obs) > 2 else 1.0
            if self._distance(point, (obs[0], obs[1])) < r:
                return True
        return False

    def _check_line_collision(
        self,
        p1: tuple,
        p2: tuple,
        obstacles: list,
    ) -> bool:
        """检测线段是否与障碍物碰撞。"""
        for t in np.linspace(0, 1, 10):
            mid = (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))
            if self._check_collision(mid, obstacles):
                return True
        return False

    def _extract_path(
        self,
        idx: int | None,
        nodes: list,
        parents: dict[int, int | None],
    ) -> list[list[float]]:
        """从搜索树中提取路径。"""
        path = []
        while idx is not None:
            path.append(list(nodes[idx]))
            idx = parents.get(idx)
        path.reverse()
        return path

    def _compute_risk_exposure(
        self,
        path: list,
        risk_field: np.ndarray | None,
    ) -> float:
        """计算路径的平均风险暴露值。"""
        if risk_field is None or not path:
            return 0.0
        risk_values = [self._get_risk_at(tuple(p), risk_field) for p in path]
        return float(np.mean(risk_values))
