"""3D-VAR Data Assimilation Algorithm.

Migrated from: data-assimilation-platform/algorithm_core/src/bayesian_assimilation/models/three_dimensional_var.py

Original: ThreeDimensionalVAR class with spatial covariance, variational optimization.
Standalone version suitable for the algorithm engine.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ThreeDimensionalVAR:
    """3D-VAR (Three-Dimensional Variational) data assimilation.

    Minimizes the cost function:
        J(x) = 0.5 * (x - xb)^T B^{-1} (x - xb)
             + 0.5 * (Hx - y)^T R^{-1} (Hx - y)
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10, 5))
        self.resolution: float = self.config.get("resolution", 50.0)
        self.max_iterations: int = self.config.get("max_iterations", 50)
        self.tolerance: float = self.config.get("tolerance", 1e-6)
        self.sigma_b: float = self.config.get("sigma_b", 1.0)
        self.correlation_length: float = self.config.get("correlation_length", 100.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """Run 3D-VAR assimilation.

        Args:
            params: Dictionary containing:
                - background_field: np.ndarray, the background state
                - observations: list of dicts with 'position' and 'value'
                - grid_shape: optional, tuple of grid dimensions
                - resolution: optional, grid resolution in km

        Returns:
            Dictionary with analysis_field, cost, iterations, and convergence info.
        """
        background = np.asarray(params.get("background_field", np.zeros(self.grid_shape)))
        observations = params.get("observations", [])

        if background.ndim == 0:
            background = background.reshape(1)

        n = background.size
        xb = background.flatten()

        y_obs, H = self._build_observation_operator(xb, observations, background.shape)

        def cost_gradient(x):
            dx = x - xb
            grad_b = dx / (self.sigma_b ** 2)
            Hx = H @ x
            dy = Hx - y_obs
            grad_o = H.T @ (dy / self.observation_error_scale**2)
            return grad_b + grad_o

        x = xb.copy()
        lr = 0.01
        cost_history = []
        for i in range(self.max_iterations):
            grad = cost_gradient(x)
            cost = 0.5 * np.dot(x - xb, (x - xb) / (self.sigma_b ** 2))
            cost += 0.5 * np.sum(((H @ x - y_obs) / self.observation_error_scale) ** 2)
            cost_history.append(float(cost))
            x = x - lr * grad
            if len(cost_history) > 1 and abs(cost_history[-2] - cost_history[-1]) < self.tolerance:
                logger.info("3D-VAR converged at iteration %d", i)
                break

        analysis = x.reshape(background.shape)
        return {
            "analysis_field": analysis.tolist(),
            "cost": cost_history[-1] if cost_history else 0.0,
            "iterations": len(cost_history),
            "converged": len(cost_history) < self.max_iterations,
            "grid_shape": list(background.shape),
        }

    def _build_observation_operator(self, xb, observations, shape):
        n = len(xb)
        m = len(observations)
        y_obs = np.zeros(m)
        H = np.zeros((m, n))
        for j, obs in enumerate(observations):
            pos = obs.get("position", [0] * len(shape))
            value = obs.get("value", 0.0)
            y_obs[j] = value
            idx = self._position_to_index(pos, shape)
            if 0 <= idx < n:
                H[j, idx] = 1.0
        return y_obs, H

    def _position_to_index(self, pos, shape):
        idx = 0
        stride = 1
        for i in range(len(shape) - 1, -1, -1):
            idx += int(pos[i]) * stride
            stride *= shape[i]
        return idx
