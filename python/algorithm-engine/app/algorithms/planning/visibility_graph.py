"""可见性图路径规划算法。

基于可见性图（Visibility Graph）的最短路径规划方法。
将障碍物顶点、起点和终点作为图节点，仅连接相互可见的节点对，
然后在图上搜索最短路径，保证路径长度最优。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class VisibilityGraphPlanner:
    """可见性图路径规划器。

    构建由障碍物顶点、起点和终点组成的可见性图，
    仅保留无障碍物阻挡的边，在图上执行Dijkstra搜索
    获得最短路径。

    Args:
        config: 配置字典，支持以下参数：
            - obstacle_radius: 障碍物膨胀半径，默认0.5
            - line_check_resolution: 视线检查采样密度，默认0.5
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.obstacle_radius: float = self.config.get("obstacle_radius", 0.5)
        self.line_check_resolution: float = self.config.get("line_check_resolution", 0.5)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行可见性图路径规划。

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
            "可见性图规划: 起点=%s, 终点=%s, 障碍物=%d",
            tuple(start.astype(int)),
            tuple(goal.astype(int)),
            len(obstacles),
        )

        rows, cols = grid_size

        if start == goal:
            return {"path": [list(start.astype(int))], "cost": 0.0}

        # 构建可见性图节点：起点 + 终点 + 障碍物边界点
        nodes = [start.copy(), goal.copy()]
        node_labels = ["start", "goal"]

        # 从障碍物生成边界点（每个障碍物周围的角点）
        for obs in obstacles:
            ox, oy = obs[0], obs[1]
            r = self.obstacle_radius
            corner_offsets = [(-r, -r), (-r, r), (r, -r), (r, r)]
            for dx, dy in corner_offsets:
                px, py = ox + dx, oy + dy
                if 0 <= px <= rows and 0 <= py <= cols:
                    nodes.append(np.array([px, py]))
                    node_labels.append(f"obs_{ox}_{oy}")

        if len(nodes) < 2:
            logger.warning("可见性图节点不足")
            return {"path": [], "cost": float("inf")}

        nodes = np.array(nodes)
        n = len(nodes)

        # 构建邻接表
        adj: dict[int, list[tuple[int, float]]] = {i: [] for i in range(n)}

        for i in range(n):
            for j in range(i + 1, n):
                if self._is_visible(nodes[i], nodes[j], obstacles, rows, cols):
                    dist = float(np.linalg.norm(nodes[i] - nodes[j]))
                    adj[i].append((j, dist))
                    adj[j].append((i, dist))

        # Dijkstra搜索
        start_idx, goal_idx = 0, 1
        path_indices = self._dijkstra(adj, start_idx, goal_idx)

        if not path_indices:
            logger.warning("可见性图中未找到路径")
            return {"path": [], "cost": float("inf")}

        path_points = nodes[path_indices]
        path = [[int(round(p[0])), int(round(p[1]))] for p in path_points]
        cost = self._path_cost(path_points)

        logger.info("可见性图规划完成: 代价=%.2f, 路径点=%d", cost, len(path))
        return {
            "path": path,
            "cost": cost,
            "graph_nodes": n,
        }

    def _is_visible(
        self,
        a: np.ndarray,
        b: np.ndarray,
        obstacles: set,
        rows: int,
        cols: int,
    ) -> bool:
        """检查两点之间是否可见（无障碍物阻挡）。"""
        dist = np.linalg.norm(b - a)
        n_samples = max(int(dist / self.line_check_resolution), 2)

        for t in np.linspace(0, 1, n_samples):
            point = a + t * (b - a)
            px, py = int(round(point[0])), int(round(point[1]))
            if (px, py) in obstacles:
                return False
            if not (0 <= px <= rows and 0 <= py <= cols):
                return False
        return True

    def _dijkstra(
        self,
        adj: dict,
        start: int,
        goal: int,
    ) -> list[int]:
        """Dijkstra最短路径搜索。"""
        dist = {start: 0.0}
        prev: dict[int, int | None] = {start: None}
        pq = [(0.0, start)]

        while pq:
            d, current = heapq.heappop(pq)
            if current == goal:
                path = []
                while current is not None:
                    path.append(current)
                    current = prev[current]
                path.reverse()
                return path
            if d > dist.get(current, float("inf")):
                continue
            for neighbor, cost in adj.get(current, []):
                new_dist = d + cost
                if new_dist < dist.get(neighbor, float("inf")):
                    dist[neighbor] = new_dist
                    prev[neighbor] = current
                    heapq.heappush(pq, (new_dist, neighbor))

        return []

    def _path_cost(self, points: np.ndarray) -> float:
        """计算路径代价。"""
        if len(points) < 2:
            return 0.0
        diffs = np.diff(points, axis=0)
        return float(np.sum(np.sqrt(np.sum(diffs**2, axis=1))))
