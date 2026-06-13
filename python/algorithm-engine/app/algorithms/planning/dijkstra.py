"""Dijkstra path planning algorithm.

Migrated from: path-planning-service/src/main/python/planners/dijkstra.py
"""
from __future__ import annotations

import heapq
import logging
from typing import Any

logger = logging.getLogger(__name__)


class DijkstraPlanner:
    """Dijkstra shortest path algorithm for grid-based planning."""

    def __init__(self, params: dict[str, Any] | None = None):
        self.params = params or {}
        self.start = self.params.get("start", [0, 0])
        self.goal = self.params.get("goal", [10, 10])
        self.grid_size = self.params.get("grid_size", [100, 100])
        self.obstacles = self.params.get("obstacles", [])

    def solve(self) -> dict[str, Any]:
        start_grid = self._world_to_grid(self.start)
        goal_grid = self._world_to_grid(self.goal)
        dist = {start_grid: 0}
        prev: dict[tuple[int, int], tuple[int, int] | None] = {
            start_grid: None,
        }
        pq = [(0, start_grid)]
        while pq:
            d, current = heapq.heappop(pq)
            if current == goal_grid:
                path = self._reconstruct_path(prev, current)
                return {"path": path, "cost": float(d), "nodes_explored": len(dist)}
            if d > dist.get(current, float("inf")):
                continue
            for neighbor in self._get_neighbors(current):
                new_dist = d + 1
                if new_dist < dist.get(neighbor, float("inf")):
                    dist[neighbor] = new_dist
                    prev[neighbor] = current
                    heapq.heappush(pq, (new_dist, neighbor))
        return {"path": [], "cost": float("inf"), "nodes_explored": len(dist)}

    def _world_to_grid(self, pos):
        return (int(pos[0] + self.grid_size[0] / 2), int(pos[1] + self.grid_size[1] / 2))

    def _grid_to_world(self, pos):
        return [pos[0] - self.grid_size[0] / 2, pos[1] - self.grid_size[1] / 2]

    def _get_neighbors(self, pos):
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = pos[0] + dx, pos[1] + dy
            if 0 <= nx < self.grid_size[0] and 0 <= ny < self.grid_size[1]:
                neighbors.append((nx, ny))
        return neighbors

    def _reconstruct_path(self, prev, current):
        path = [self._grid_to_world(current)]
        while prev.get(current) is not None:
            current = prev[current]
            path.append(self._grid_to_world(current))
        path.reverse()
        return path
