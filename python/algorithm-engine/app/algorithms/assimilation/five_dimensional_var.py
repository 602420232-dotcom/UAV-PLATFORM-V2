"""5D-VAR Data Assimilation Algorithm.

Migrated from:
    data-assimilation-platform/algorithm_core/src/bayesian_assimilation/models/five_dimensional_var.py

Original: FiveDimensionalVar extending FourDimensionalVar with risk, drone perturbation,
and AI parameterization dimensions.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
from scipy.ndimage import gaussian_filter

logger = logging.getLogger(__name__)


class FiveDimensionalVAR:
    """5D-VAR Data Assimilation with extended dimensions.

    Dimensions beyond standard 4D-VAR:
    1. Risk Dimension: flight risk cost in the cost function
    2. Dynamic Perturbation: UAV swarm observations as ensemble perturbations
    3. AI Parameterization: AI model corrections as control variables

    Cost function: J(x, alpha) = J_b(x) + J_o(x) + J_risk(x) + J_param(alpha)
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10, 5))
        self.resolution: float = self.config.get("resolution", 50.0)
        self.max_iterations: int = self.config.get("max_iterations", 30)
        self.tolerance: float = self.config.get("tolerance", 1e-6)
        self.risk_weight: float = self.config.get("risk_weight", 0.5)
        self.ai_param_weight: float = self.config.get("ai_param_weight", 0.1)
        self.sigma_b: float = self.config.get("sigma_b", 1.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """Run 5D-VAR assimilation."""
        background = np.asarray(params.get("background_field", np.zeros(self.grid_shape)))
        observations = params.get("observations", [])
        risk_weight = params.get("risk_weight", self.risk_weight)
        ai_correction = np.asarray(params.get("ai_correction", np.zeros_like(background)))

        xb = background.flatten()
        x = xb.copy()

        y_obs, H = self._build_observation_operator(x, observations, background.shape)  # noqa: N806

        cost_history = []
        J_b = J_o = J_risk = J_param = 0.0  # noqa: N806
        for i in range(self.max_iterations):
            dx = x - xb
            J_b = 0.5 * np.sum(dx**2) / (self.sigma_b**2)  # noqa: N806
            Hx = H @ x  # noqa: N806
            residual = Hx - y_obs
            J_o = 0.5 * np.sum(residual**2) / (self.observation_error_scale**2)  # noqa: N806
            field = x.reshape(background.shape)
            smoothed = gaussian_filter(field.astype(float), sigma=1.0)
            J_risk = risk_weight * np.var(smoothed)  # noqa: N806
            J_param = (  # noqa: N806
                self.ai_param_weight * np.sum((x - ai_correction.flatten()) ** 2)
            )
            total_cost = J_b + J_o + J_risk + J_param
            cost_history.append(float(total_cost))

            grad_b = dx / (self.sigma_b**2)
            grad_o = H.T @ (residual / (self.observation_error_scale**2))
            grad_param = self.ai_param_weight * 2.0 * (x - ai_correction.flatten())
            grad = grad_b + grad_o + grad_param
            x = x - 0.01 * grad

            if len(cost_history) > 1 and abs(cost_history[-2] - cost_history[-1]) < self.tolerance:
                logger.info("5D-VAR converged at iteration %d", i)
                break

        analysis = x.reshape(background.shape)
        return {
            "analysis_field": analysis.tolist(),
            "cost": cost_history[-1] if cost_history else 0.0,
            "cost_breakdown": {
                "J_b": float(J_b),
                "J_o": float(J_o),
                "J_risk": float(J_risk),
                "J_param": float(J_param),
            },
            "iterations": len(cost_history),
            "converged": len(cost_history) < self.max_iterations,
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
