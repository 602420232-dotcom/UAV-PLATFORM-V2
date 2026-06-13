"""Information Gain based observation optimization.

Migrated from: model-engine/active_obs/bayesian_observer.py
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class InformationGainOptimizer:
    """Information gain based optimal observation placement."""

    def __init__(self, params: dict[str, Any] | None = None):
        self.params = params or {}
        self.budget = self.params.get("budget", 5)

    def optimize(self) -> dict[str, Any]:
        uncertainty_field = np.asarray(self.params.get("uncertainty_field", np.ones((10, 10))))
        budget = self.params.get("budget", self.budget)
        flat = uncertainty_field.flatten()
        n_select = min(budget, len(flat))
        top_indices = np.argsort(flat)[-n_select:][::-1]
        shape = uncertainty_field.shape
        selected_positions = []
        for idx in top_indices:
            pos = np.unravel_index(idx, shape)
            selected_positions.append([int(p) for p in pos])
        expected_gain = float(np.sum(flat[top_indices]))
        return {
            "selected_positions": selected_positions,
            "expected_gain": expected_gain,
            "budget_used": len(selected_positions),
        }
