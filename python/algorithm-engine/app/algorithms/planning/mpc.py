"""MPC (Model Predictive Control) path planning.

Migrated from: model-engine/control/mpc.py
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class MPCPlanner:
    """Model Predictive Control for dynamic re-planning under uncertainty."""

    def __init__(self, params: dict[str, Any] | None = None):
        self.params = params or {}
        self.start = self.params.get("start", [0, 0])
        self.goal = self.params.get("goal", [10, 10])
        self.horizon = self.params.get("horizon", 10)
        self.risk_field = self.params.get("risk_field", None)
        self.dt = self.params.get("dt", 1.0)
        self.max_speed = self.params.get("max_speed", 2.0)

    def solve(self) -> dict[str, Any]:
        current = np.array(self.start, dtype=float)
        goal = np.array(self.goal, dtype=float)
        path = [current.tolist()]
        control_sequence = []
        for step in range(self.horizon):
            direction = goal - current
            dist = np.linalg.norm(direction)
            if dist < 0.5:
                break
            velocity = direction / dist * min(self.max_speed, dist)
            control_sequence.append(velocity.tolist())
            if self.risk_field is not None:
                velocity = self._avoid_risk(current, velocity, np.asarray(self.risk_field))
            current = current + velocity * self.dt
            path.append(current.tolist())
        return {
            "path": path,
            "control_sequence": control_sequence,
            "steps": len(path) - 1,
            "final_distance": float(np.linalg.norm(current - goal)),
        }

    def _avoid_risk(self, position, velocity, risk_field):
        shape = risk_field.shape
        pos_idx = [int(p) for p in position]
        if all(0 <= p < s for p, s in zip(pos_idx, shape)):
            risk_val = risk_field[tuple(pos_idx)]
            if risk_val > 0.5:
                velocity = velocity * (1.0 - risk_val * 0.5)
        return velocity
