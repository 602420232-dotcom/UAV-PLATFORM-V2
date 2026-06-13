"""DE-RRT* (Differential Evolution RRT*).

TODO: Migrate full implementation from
    path-planning-service/planners/informed_rrt_star.py.
"""
from __future__ import annotations

import logging
import random
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class DERRTStarPlanner:
    """Differential Evolution enhanced RRT* for complex environments."""

    def __init__(self, params: dict[str, Any] | None = None):
        self.params = params or {}
        self.start = tuple(self.params.get("start", [0, 0]))
        self.goal = tuple(self.params.get("goal", [10, 10]))
        self.obstacles = self.params.get("obstacles", [])
        self.max_iterations = self.params.get("max_iterations", 1000)
        self.step_size = self.params.get("step_size", 1.0)
        self.goal_radius = self.params.get("goal_radius", 1.0)

    def solve(self) -> dict[str, Any]:
        nodes = [self.start]
        parents: dict[int, int | None] = {0: None}
        costs: dict[int, float] = {0: 0.0}
        for i_iter in range(self.max_iterations):
            if random.random() < 0.1:
                rand_point = self.goal
            else:
                rand_point = (
                    random.uniform(
                        min(self.start[0], self.goal[0]) - 5,
                        max(self.start[0], self.goal[0]) + 5,
                    ),
                    random.uniform(
                        min(self.start[1], self.goal[1]) - 5,
                        max(self.start[1], self.goal[1]) + 5,
                    ),
                )
            nearest_idx = min(
                range(len(nodes)),
                key=lambda i: float(
                    np.linalg.norm(
                        np.array(nodes[i]) - np.array(rand_point),
                    ),
                ),
            )
            nearest = np.array(nodes[nearest_idx])
            rand_arr = np.array(rand_point)
            direction = rand_arr - nearest
            dist = float(np.linalg.norm(direction))
            if dist > 0:
                new_point = nearest + (
                    direction / dist * min(self.step_size, dist)
                )
            else:
                continue
            new_point_tuple = tuple(new_point)
            if self._check_collision(new_point_tuple):
                continue
            new_idx = len(nodes)
            nodes.append(new_point_tuple)
            best_parent = nearest_idx
            best_cost = costs[nearest_idx] + float(
                np.linalg.norm(
                    np.array(nodes[nearest_idx]) - new_point,
                ),
            )
            for i, node in enumerate(nodes[:-1]):
                c = costs[i] + float(
                    np.linalg.norm(np.array(node) - new_point),
                )
                if c < best_cost and not self._check_line_collision(
                    node, new_point_tuple,
                ):
                    best_parent = i
                    best_cost = c
            parents[new_idx] = best_parent
            costs[new_idx] = best_cost
            if (
                float(np.linalg.norm(new_point - np.array(self.goal)))
                < self.goal_radius
            ):
                path = self._extract_path(new_idx, nodes, parents)
                return {
                    "path": path,
                    "cost": float(best_cost),
                    "iterations": i_iter + 1,
                }
        return {
            "path": [],
            "cost": float("inf"),
            "iterations": self.max_iterations,
        }

    def _check_collision(self, point):
        for obs in self.obstacles:
            r = obs[2] if len(obs) > 2 else 1.0
            if float(
                np.linalg.norm(
                    np.array(point) - np.array([obs[0], obs[1]]),
                ),
            ) < r:
                return True
        return False

    def _check_line_collision(self, p1, p2):
        for t in np.linspace(0, 1, 10):
            mid = (
                p1[0] + t * (p2[0] - p1[0]),
                p1[1] + t * (p2[1] - p1[1]),
            )
            if self._check_collision(mid):
                return True
        return False

    def _extract_path(self, idx, nodes, parents):
        path = []
        while idx is not None:
            path.append(nodes[idx])
            idx = parents[idx]
        path.reverse()
        return path
