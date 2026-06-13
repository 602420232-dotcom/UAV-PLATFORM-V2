"""A* path planning algorithm.

Migrated from: path-planning-service/src/main/python/planners/
"""

from __future__ import annotations

import heapq
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AStarPlanner:
    """A* search algorithm for grid-based path planning."""

    def __init__(self, params: dict[str, Any] | None = None):
        self.params = params or {}
        self.start = self.params.get("start", [0, 0])
        self.goal = self.params.get("goal", [10, 10])
        self.grid_size = self.params.get("grid_size", [100, 100])
        self.obstacles = self.params.get("obstacles", [])

    def solve(self) -> dict[str, Any]:
        start_grid = self._world_to_grid(self.start)
        goal_grid = self._world_to_grid(self.goal)
        open_set = [(0, start_grid)]
        came_from = {}
        g_score = {start_grid: 0}
        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal_grid:
                path = self._reconstruct_path(came_from, current)
                return {
                    "path": path,
                    "cost": float(g_score[current]),
                    "nodes_explored": len(g_score),
                }
            for neighbor in self._get_neighbors(current):
                tentative_g = g_score[current] + 1
                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + self._heuristic(neighbor, goal_grid)
                    heapq.heappush(open_set, (f_score, neighbor))
        return {"path": [], "cost": float("inf"), "nodes_explored": len(g_score)}

    def _world_to_grid(self, pos):
        return (int(pos[0] + self.grid_size[0] / 2), int(pos[1] + self.grid_size[1] / 2))

    def _grid_to_world(self, pos):
        return [pos[0] - self.grid_size[0] / 2, pos[1] - self.grid_size[1] / 2]

    def _heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _get_neighbors(self, pos):
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = pos[0] + dx, pos[1] + dy
            if 0 <= nx < self.grid_size[0] and 0 <= ny < self.grid_size[1]:
                neighbors.append((nx, ny))
        return neighbors

    def _reconstruct_path(self, came_from, current):
        path = [self._grid_to_world(current)]
        while current in came_from:
            current = came_from[current]
            path.append(self._grid_to_world(current))
        path.reverse()
        return path
