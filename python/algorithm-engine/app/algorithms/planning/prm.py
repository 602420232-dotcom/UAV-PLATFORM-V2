"""概率路线图（PRM，Probabilistic Roadmap）路径规划算法。

基于多查询的随机采样路径规划方法。分为两个阶段：
1. 学习阶段：在自由空间中随机采样点，连接邻近点构建路线图
2. 查询阶段：在路线图上搜索起点到终点的最短路径
适用于多次查询同一环境的场景。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class PRMPlanner:
    """概率路线图路径规划器。

    在配置空间中随机采样自由点，构建邻接路线图，
    然后在图上执行Dijkstra搜索获取最短路径。

    Args:
        config: 配置字典，支持以下参数：
            - num_samples: 采样点数量，默认500
            - k_neighbors: 每个点连接的最近邻居数，默认10
            - max_edge_length: 最大边长度，默认5.0
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.num_samples: int = self.config.get("num_samples", 500)
        self.k_neighbors: int = self.config.get("k_neighbors", 10)
        self.max_edge_length: float = self.config.get("max_edge_length", 5.0)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行PRM路径规划。

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
            "PRM规划: 起点=%s, 终点=%s, 采样数=%d",
            tuple(start.astype(int)),
            tuple(goal.astype(int)),
            self.num_samples,
        )

        rows, cols = grid_size

        # 阶段1：构建路线图
        samples = self._sample_free_space(rows, cols, obstacles)
        nodes = np.vstack([start.reshape(1, 2), goal.reshape(1, 2), samples])
        start_idx, goal_idx = 0, 1

        # 构建邻接图
        adj = self._build_roadmap(nodes, obstacles)

        # 阶段2：在路线图上搜索最短路径
        path_indices = self._dijkstra(adj, start_idx, goal_idx)

        if not path_indices:
            logger.warning("PRM路线图中未找到路径")
            return {"path": [], "cost": float("inf")}

        path_points = nodes[path_indices]
        path = [[int(round(p[0])), int(round(p[1]))] for p in path_points]
        cost = self._path_cost(path_points)

        logger.info("PRM规划完成: 代价=%.2f, 路线图节点=%d", cost, len(nodes))
        return {
            "path": path,
            "cost": cost,
            "roadmap_nodes": len(nodes),
            "roadmap_edges": sum(len(v) for v in adj.values()) // 2,
        }

    def _sample_free_space(
        self,
        rows: int,
        cols: int,
        obstacles: set,
    ) -> np.ndarray:
        """在自由空间中随机采样点。"""
        samples = []
        while len(samples) < self.num_samples:
            point = np.array([np.random.uniform(0, rows), np.random.uniform(0, cols)])
            px, py = int(round(point[0])), int(round(point[1]))
            if (px, py) not in obstacles:
                samples.append(point)
        return np.array(samples)

    def _build_roadmap(
        self,
        nodes: np.ndarray,
        obstacles: set,
    ) -> dict[int, list[tuple[int, float]]]:
        """构建路线图邻接表。"""
        n = len(nodes)
        adj: dict[int, list[tuple[int, float]]] = {i: [] for i in range(n)}

        for i in range(n):
            # 计算到所有其他节点的距离
            dists = np.linalg.norm(nodes - nodes[i], axis=1)
            # 取k个最近邻居
            nearest_indices = np.argsort(dists)[1 : self.k_neighbors + 1]

            for j in nearest_indices:
                j = int(j)
                if dists[j] > self.max_edge_length:
                    continue
                # 碰撞检查
                if not self._check_line_collision(nodes[i], nodes[j], obstacles):
                    dist = float(dists[j])
                    adj[i].append((j, dist))
                    adj[j].append((i, dist))

        return adj

    def _check_line_collision(
        self,
        a: np.ndarray,
        b: np.ndarray,
        obstacles: set,
    ) -> bool:
        """检查两点之间的线段是否与障碍物碰撞。"""
        n_checks = max(int(np.linalg.norm(b - a) * 2), 2)
        for t in np.linspace(0, 1, n_checks):
            point = a + t * (b - a)
            px, py = int(round(point[0])), int(round(point[1]))
            if (px, py) in obstacles:
                return True
        return False

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
