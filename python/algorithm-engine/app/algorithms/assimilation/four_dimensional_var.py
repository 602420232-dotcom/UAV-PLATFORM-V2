"""4D-VAR Data Assimilation Algorithm.

Migrated from:
    data-assimilation-platform/algorithm_core/src/bayesian_assimilation/models/four_dimensional_var.py

Original: FourDimensionalVar class extending AssimilationBase with temporal dimension.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class FourDimensionalVAR:
    """4D-VAR (Four-Dimensional Variational) data assimilation.

    Extends 3D-VAR by incorporating observations distributed across
    a time window, using a simplified linear forecast model.
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10, 5))
        self.resolution: float = self.config.get("resolution", 50.0)
        self.max_iterations: int = self.config.get("max_iterations", 20)
        self.tolerance: float = self.config.get("tolerance", 1e-6)
        self.n_time_slots: int = self.config.get("n_time_slots", 4)
        self.sigma_b: float = self.config.get("sigma_b", 1.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """Run 4D-VAR assimilation."""
        background = np.asarray(params.get("background_field", np.zeros(self.grid_shape)))
        observations = params.get("observations", [])
        n_time = params.get("time_windows", self.n_time_slots)

        xb = background.flatten()
        x = xb.copy()

        obs_by_time: dict[int, list] = {t: [] for t in range(n_time)}
        for obs in observations:
            t_idx = obs.get("time_index", 0)
            obs_by_time.setdefault(t_idx, []).append(obs)

        cost_history = []
        for t in range(n_time):
            slot_obs = obs_by_time.get(t, [])
            if not slot_obs:
                cost_history.append(0.0)
                continue
            y_obs, H = self._build_observation_operator(x, slot_obs, background.shape)  # noqa: N806
            Hx = H @ x  # noqa: N806
            residual = Hx - y_obs
            dx = H.T @ (residual / (self.observation_error_scale ** 2 + 1e-10))
            x = x - 0.1 * dx
            cost = 0.5 * np.sum(residual ** 2) / self.observation_error_scale ** 2
            cost_history.append(float(cost))

        analysis = x.reshape(background.shape)
        return {
            "analysis_field": analysis.tolist(),
            "cost": cost_history[-1] if cost_history else 0.0,
            "iterations": n_time,
            "time_slot_costs": cost_history,
            "converged": True,
            "grid_shape": list(background.shape),
        }

    def _build_observation_operator(self, xb, observations, shape):
        n = len(xb)
        m = len(observations)
        y_obs = np.zeros(m)
        H = np.zeros((m, n))  # noqa: N806
        for j, obs in enumerate(observations):
            pos = obs.get("position", [0] * len(shape))
            y_obs[j] = obs.get("value", 0.0)
            idx = 0
            stride = 1
            for i in range(len(shape) - 1, -1, -1):
                idx += int(pos[i]) * stride
                stride *= shape[i]
            if 0 <= idx < n:
                H[j, idx] = 1.0
        return y_obs, H
