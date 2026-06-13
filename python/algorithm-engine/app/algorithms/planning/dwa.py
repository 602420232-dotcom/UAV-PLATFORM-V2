"""DWA (Dynamic Window Approach) local planning.

TODO: Migrate full implementation.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class DWAPlanner:
    """Dynamic Window Approach for local obstacle avoidance."""

    def __init__(self, params: dict[str, Any] | None = None):
        self.params = params or {}
        self.start = self.params.get("start", [0, 0])
        self.goal = self.params.get("goal", [10, 10])
        self.obstacles = self.params.get("obstacles", [])
        self.velocity = self.params.get("velocity", [0, 0])
        self.max_speed = self.params.get("max_speed", 2.0)
        self.predict_time = self.params.get("predict_time", 2.0)

    def solve(self) -> dict[str, Any]:
        current = np.array(self.start, dtype=float)
        goal = np.array(self.goal, dtype=float)
        best_velocity = [0.0, 0.0]
        best_score = -float("inf")
        for v_x in np.linspace(-self.max_speed, self.max_speed, 20):
            for v_y in np.linspace(-self.max_speed, self.max_speed, 20):
                predicted = current + np.array([v_x, v_y]) * self.predict_time
                heading = np.linalg.norm(predicted - goal)
                min_dist = min(
                    float(
                        np.linalg.norm(
                            predicted - np.array(obs[:2]),
                        )
                        - (obs[2] if len(obs) > 2 else 1.0),
                    )
                    for obs in self.obstacles
                ) if self.obstacles else 10.0
                speed = np.sqrt(v_x**2 + v_y**2)
                score = -heading + min_dist * 0.5 + speed * 0.1
                if score > best_score:
                    best_score = score
                    best_velocity = [float(v_x), float(v_y)]
        trajectory = [
            self.start,
            [
                current[0] + best_velocity[0] * self.predict_time,
                current[1] + best_velocity[1] * self.predict_time,
            ],
        ]
        return {
            "trajectory": trajectory,
            "velocity": best_velocity,
            "score": float(best_score),
        }
