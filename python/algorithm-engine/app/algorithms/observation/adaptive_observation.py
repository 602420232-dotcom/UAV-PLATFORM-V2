"""Adaptive Observation Strategy.

Migrated from: model-engine/active_obs/bayesian_observer.py
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class AdaptiveObservationPlanner:
    """Adaptive observation strategy that adjusts based on real-time uncertainty."""

    def __init__(self, params: dict[str, Any] | None = None):
        self.params = params or {}

    def plan(self) -> dict[str, Any]:
        uncertainty_field = np.asarray(self.params.get("uncertainty_field", np.ones((10, 10))))
        history = self.params.get("history", [])
        available_sensors = self.params.get("available_sensors", [])
        flat = uncertainty_field.flatten()
        n_sensors = len(available_sensors) if available_sensors else 3
        top_indices = np.argsort(flat)[-n_sensors:][::-1]
        shape = uncertainty_field.shape
        positions = []
        for idx in top_indices:
            pos = np.unravel_index(idx, shape)
            positions.append([int(p) for p in pos])
        if history:
            recent = set()
            for h in history[-5:]:
                for p in h.get("positions", []):
                    recent.add(tuple(p))
            filtered = [p for p in positions if tuple(p) not in recent]
            if len(filtered) < n_sensors:
                all_indices = np.argsort(flat)[::-1]
                for idx in all_indices:
                    pos = tuple(int(p) for p in np.unravel_index(idx, shape))
                    if pos not in recent and pos not in [tuple(p) for p in filtered]:
                        filtered.append(list(pos))
                        if len(filtered) >= n_sensors:
                            break
                positions = filtered[:n_sensors]
        return {
            "strategy": {
                "method": "adaptive_uncertainty",
                "history_weight": 0.3,
                "n_positions": len(positions),
            },
            "positions": positions,
        }
