"""RRT* (Rapidly-exploring Random Tree Star) path planning.

Migrated from: path-planning-service/src/main/python/planners/rrt_star.py
"""
from __future__ import annotations

import logging
import random
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class RRTStarPlanner:
    """RRT* optimal path planning algorithm."""

    def __init__(self, params: dict[str, Any] | None = None):
        self.params = params or {}
        self.start = tuple(self.params.get("start", [0, 0]))
        self.goal = tuple(self.params.get("goal", [10, 10]))
        self.obstacles = self.params.get("obstacles", [])
        self.max_iterations = self.params.get("max_iterations", 1000)
        self.step_size = self.params.get("step_size", 1.0)
        self.goal_radius = self.params.get("goal_radius", 1.0)
        self.rewire_radius = self.params.get("rewire_radius", 3.0)

    def solve(self) -> dict[str, Any]:
        nodes = [self.start]
        parents: dict[int, int | None] = {0: None}
        costs: dict[int, float] = {0: 0.0}
        for iteration in range(self.max_iterations):
            if random.random() < 0.1:
                rand_point = self.goal
            else:
                x_range = (
                    min(self.start[0], self.goal[0]) - 5,
                    max(self.start[0], self.goal[0]) + 5,
                )
                y_range = (
                    min(self.start[1], self.goal[1]) - 5,
                    max(self.start[1], self.goal[1]) + 5,
                )
                rand_point = (random.uniform(*x_range), random.uniform(*y_range))
            nearest_idx = min(range(len(nodes)), key=lambda i: self._distance(nodes[i], rand_point))
            nearest = np.array(nodes[nearest_idx])
            rand_arr = np.array(rand_point)
            diff = rand_arr - nearest
            dist = np.linalg.norm(diff)
            if dist < 1e-6:
                continue
            new_point = nearest + diff / dist * min(self.step_size, dist)
            if self._check_collision(tuple(new_point)):
                continue
            new_idx = len(nodes)
            nodes.append(tuple(new_point))
            best_parent = nearest_idx
            best_cost = costs[nearest_idx] + self._distance(nodes[nearest_idx], tuple(new_point))
            for i in range(len(nodes) - 1):
                d = self._distance(nodes[i], tuple(new_point))
                if d < self.rewire_radius:
                    c = costs[i] + d
                    if c < best_cost and not self._check_line_collision(nodes[i], tuple(new_point)):
                        best_parent = i
                        best_cost = c
            parents[new_idx] = best_parent
            costs[new_idx] = best_cost
            for i in range(len(nodes) - 1):
                d = self._distance(nodes[i], tuple(new_point))
                if d < self.rewire_radius:
                    new_cost = costs[new_idx] + d
                    if new_cost < costs[i] and not self._check_line_collision(
                        nodes[i], tuple(new_point),
                    ):
                        parents[i] = new_idx
                        costs[i] = new_cost
            if self._distance(tuple(new_point), self.goal) < self.goal_radius:
                path = self._extract_path(new_idx, nodes, parents)
                return {"path": path, "cost": float(best_cost), "iterations": iteration + 1}
        return {"path": [], "cost": float("inf"), "iterations": self.max_iterations}

    def _distance(self, p1, p2):
        return float(np.linalg.norm(np.array(p1) - np.array(p2)))

    def _check_collision(self, point):
        for obs in self.obstacles:
            r = obs[2] if len(obs) > 2 else 1.0
            if self._distance(point, (obs[0], obs[1])) < r:
                return True
        return False

    def _check_line_collision(self, p1, p2):
        for t in np.linspace(0, 1, 10):
            mid = (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))
            if self._check_collision(mid):
                return True
        return False

    def _extract_path(self, idx, nodes, parents):
        path = []
        while idx is not None:
            path.append(list(nodes[idx]))
            idx = parents.get(idx)
        path.reverse()
        return path
