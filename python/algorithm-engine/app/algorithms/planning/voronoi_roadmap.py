"""Voronoi图路径规划算法。

基于Voronoi图构建安全路径的规划方法。
Voronoi图的边是距离所有障碍物等距的位置，天然提供了
最大化与障碍物距离的安全路径骨架。
"""

from __future__ import annotations

import heapq
import logging
from typing import Any, Optional

import numpy as np
from scipy.spatial import Voronoi

logger = logging.getLogger(__name__)


class VoronoiRoadmapPlanner:
    """Voronoi图路径规划器。

    利用障碍物生成Voronoi图，在Voronoi边上搜索最短路径。
    Voronoi边上的点等距于最近的障碍物，提供最大安全裕度。

    Args:
        config: 配置字典，支持以下参数：
            - buffer_points: 添加缓冲点数量，默认4
            - resolution: 路径插值分辨率，默认0.5
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.buffer_points: int = self.config.get("buffer_points", 4)
        self.resolution: float = self.config.get("resolution", 0.5)

    def plan(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行Voronoi图路径规划。

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
        obstacles = [np.array(obs[:2], dtype=float) for obs in params.get("obstacles", [])]

        logger.info(
            "Voronoi图规划: 起点=%s, 终点=%s, 障碍物=%d",
            tuple(start.astype(int)), tuple(goal.astype(int)), len(obstacles),
        )

        rows, cols = grid_size

        if len(obstacles) < 3:
            logger.warning("障碍物数量不足，无法构建Voronoi图，退化为直线")
            path = self._straight_line(start, goal)
            cost = float(np.linalg.norm(goal - start))
            return {"path": path, "cost": cost}

        # 构建Voronoi图
        obs_array = np.array(obstacles)

        # 添加边界点确保Voronoi图覆盖整个空间
        boundary_points = np.array([
            [-10, -10], [rows + 10, -10],
            [-10, cols + 10], [rows + 10, cols + 10],
        ])
        all_points = np.vstack([obs_array, boundary_points])

        try:
            vor = Voronoi(all_points)
        except Exception as e:
            logger.warning("Voronoi图构建失败: %s, 退化为直线", e)
            path = self._straight_line(start, goal)
            cost = float(np.linalg.norm(goal - start))
            return {"path": path, "cost": cost}

        # 提取有限Voronoi顶点作为路网节点
        vertices = []
        for v in vor.vertices:
            if 0 <= v[0] <= rows and 0 <= v[1] <= cols:
                vertices.append(v)

        if not vertices:
            logger.warning("无有效Voronoi顶点，退化为直线")
            path = self._straight_line(start, goal)
            cost = float(np.linalg.norm(goal - start))
            return {"path": path, "cost": cost}

        # 添加起点和终点到路网
        vertices.append(start)
        vertices.append(goal)
        start_idx = len(vertices) - 2
        goal_idx = len(vertices) - 1

        vertices = np.array(vertices)

        # 构建邻接图（基于Voronoi边和Delaunay三角剖分）
        edges = self._build_edges(vertices, vor, start_idx, goal_idx, rows, cols)

        # Dijkstra搜索最短路径
        path_indices = self._dijkstra(vertices, edges, start_idx, goal_idx)

        if not path_indices:
            logger.warning("Voronoi路网中未找到路径")
            return {"path": [], "cost": float("inf")}

        # 提取路径点
        path_points = vertices[path_indices]
        path = [[int(round(p[0])), int(round(p[1]))] for p in path_points]
        cost = self._path_cost(path_points)

        logger.info("Voronoi图规划完成: 代价=%.2f, 路径点=%d", cost, len(path))
        return {
            "path": path,
            "cost": cost,
            "vertices": len(vertices),
        }

    def _build_edges(
        self,
        vertices: np.ndarray,
        vor: Voronoi,
        start_idx: int,
        goal_idx: int,
        rows: int,
        cols: int,
    ) -> dict[int, list[tuple[int, float]]]:
        """构建路网邻接表。"""
        edges: dict[int, list[tuple[int, float]]] = {i: [] for i in range(len(vertices))}

        # 从Voronoi边构建连接
        for ridge_idx, (p1, p2) in enumerate(vor.ridge_vertices):
            if p1 >= 0 and p2 >= 0:
                v1 = vor.vertices[p1]
                v2 = vor.vertices[p2]
                if (0 <= v1[0] <= rows and 0 <= v1[1] <= cols
                        and 0 <= v2[0] <= rows and 0 <= v2[1] <= cols):
                    # 找到最近的顶点索引
                    idx1 = self._find_nearest_vertex(vertices, v1)
                    idx2 = self._find_nearest_vertex(vertices, v2)
                    if idx1 != idx2:
                        dist = float(np.linalg.norm(vertices[idx1] - vertices[idx2]))
                        edges[idx1].append((idx2, dist))
                        edges[idx2].append((idx1, dist))

        # 连接起点和终点到最近的多个顶点
        for special_idx in [start_idx, goal_idx]:
            dists = np.linalg.norm(vertices - vertices[special_idx], axis=1)
            nearest_indices = np.argsort(dists)[1:self.buffer_points + 1]
            for ni in nearest_indices:
                dist = float(dists[ni])
                edges[special_idx].append((int(ni), dist))
                edges[int(ni)].append((special_idx, dist))

        return edges

    def _find_nearest_vertex(self, vertices: np.ndarray, point: np.ndarray) -> int:
        """找到最近的顶点索引。"""
        dists = np.linalg.norm(vertices - point, axis=1)
        return int(np.argmin(dists))

    def _dijkstra(
        self,
        vertices: np.ndarray,
        edges: dict,
        start_idx: int,
        goal_idx: int,
    ) -> list[int]:
        """Dijkstra最短路径搜索。"""
        dist = {start_idx: 0.0}
        prev: dict[int, int | None] = {start_idx: None}
        pq = [(0.0, start_idx)]

        while pq:
            d, current = heapq.heappop(pq)
            if current == goal_idx:
                path = []
                while current is not None:
                    path.append(current)
                    current = prev[current]
                path.reverse()
                return path
            if d > dist.get(current, float("inf")):
                continue
            for neighbor, cost in edges.get(current, []):
                new_dist = d + cost
                if new_dist < dist.get(neighbor, float("inf")):
                    dist[neighbor] = new_dist
                    prev[neighbor] = current
                    heapq.heappush(pq, (new_dist, neighbor))

        return []

    def _straight_line(self, start: np.ndarray, goal: np.ndarray) -> list[list[int]]:
        """生成直线路径。"""
        dist = np.linalg.norm(goal - start)
        n_points = max(int(dist / self.resolution), 2)
        points = np.linspace(start, goal, n_points)
        return [[int(round(p[0])), int(round(p[1]))] for p in points]

    def _path_cost(self, points: np.ndarray) -> float:
        """计算路径代价。"""
        if len(points) < 2:
            return 0.0
        diffs = np.diff(points, axis=0)
        return float(np.sum(np.sqrt(np.sum(diffs ** 2, axis=1))))
