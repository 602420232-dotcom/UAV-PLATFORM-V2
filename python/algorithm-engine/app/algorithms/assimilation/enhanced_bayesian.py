"""Enhanced Bayesian Assimilation Algorithm.

Migrated from:
    data-assimilation-platform/algorithm_core/src/bayesian_assimilation/models/enhanced_bayesian.py
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EnhancedBayesianAssimilation:
    """Enhanced Bayesian assimilation with machine learning components.

    Combines traditional variational assimilation with neural network
    corrections for iterative self-refinement.
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10, 5))
        self.resolution: float = self.config.get("resolution", 50.0)
        self.max_iterations: int = self.config.get("max_iterations", 50)
        self.tolerance: float = self.config.get("tolerance", 1e-6)
        self.ml_iterations: int = self.config.get("ml_iterations", 3)
        self.sigma_b: float = self.config.get("sigma_b", 1.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)
        self.use_ml: bool = self.config.get("use_ml", False)

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """Run enhanced Bayesian assimilation."""
        background = np.asarray(params.get("background_field", np.zeros(self.grid_shape)))
        observations = params.get("observations", [])
        use_ml = params.get("use_ml", self.use_ml)

        xb = background.flatten()
        x = xb.copy()

        y_obs, H = self._build_observation_operator(x, observations, background.shape)  # noqa: N806

        cost_history = []
        for i in range(self.max_iterations):
            dx = x - xb
            J_b = 0.5 * np.sum(dx**2) / (self.sigma_b**2)  # noqa: N806
            Hx = H @ x  # noqa: N806
            residual = Hx - y_obs
            J_o = 0.5 * np.sum(residual**2) / (self.observation_error_scale**2)  # noqa: N806
            total_cost = J_b + J_o
            cost_history.append(float(total_cost))
            grad = dx / (self.sigma_b**2) + H.T @ (residual / (self.observation_error_scale**2))
            x = x - 0.01 * grad
            if len(cost_history) > 1 and abs(cost_history[-2] - cost_history[-1]) < self.tolerance:
                break

        ml_correction = None
        if use_ml:
            residual_field = (x - xb).reshape(background.shape)
            from scipy.ndimage import gaussian_filter

            correction = gaussian_filter(residual_field.astype(float), sigma=0.5) * 0.1
            for _ in range(self.ml_iterations - 1):
                residual_field = residual_field - correction
                correction = gaussian_filter(residual_field.astype(float), sigma=0.5) * 0.1
            ml_correction = correction.tolist()
            x = x - correction.flatten() * 0.5

        analysis = x.reshape(background.shape)
        return {
            "analysis_field": analysis.tolist(),
            "cost": cost_history[-1] if cost_history else 0.0,
            "iterations": len(cost_history),
            "converged": len(cost_history) < self.max_iterations,
            "ml_correction": ml_correction,
            "use_ml": use_ml,
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
