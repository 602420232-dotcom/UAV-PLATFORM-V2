"""EnKF (Ensemble Kalman Filter) Data Assimilation Algorithm.

Migrated from: data-assimilation-platform/algorithm_core/src/bayesian_assimilation/models/enkf.py
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EnKF:
    """Ensemble Kalman Filter (EnKF) data assimilation.

    Uses an ensemble of model states to estimate flow-dependent
    background error covariance, suitable for nonlinear systems.
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.grid_shape: tuple[int, ...] = self.config.get("grid_shape", (10, 10, 5))
        self.resolution: float = self.config.get("resolution", 50.0)
        self.ensemble_size: int = self.config.get("ensemble_size", 30)
        self.background_error_scale: float = self.config.get("background_error_scale", 1.0)
        self.observation_error_scale: float = self.config.get("observation_error_scale", 0.1)

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """Run EnKF assimilation."""
        background = np.asarray(params.get("background_field", np.zeros(self.grid_shape)))
        observations = params.get("observations", [])
        n_ens = params.get("ensemble_size", self.ensemble_size)

        n = background.size
        xb = background.flatten()

        np.random.seed(42)
        perturbation = np.random.randn(n_ens, n) * self.background_error_scale
        ensemble = xb[np.newaxis, :] + perturbation

        y_obs, H = self._build_observation_operator(xb, observations, background.shape)
        m = len(y_obs)

        obs_perturbation = np.random.randn(n_ens, m) * self.observation_error_scale
        obs_ensemble = y_obs[np.newaxis, :] + obs_perturbation

        x_mean = ensemble.mean(axis=0)
        X_pert = ensemble - x_mean[np.newaxis, :]

        HX = H @ X_pert.T
        HPHT = (HX @ HX.T) / (n_ens - 1)
        R = np.eye(m) * self.observation_error_scale ** 2
        HPHT_plus_R = HPHT + R

        try:
            K = (X_pert.T @ HX.T) @ np.linalg.inv(HPHT_plus_R) / (n_ens - 1)
        except np.linalg.LinAlgError:
            K = np.zeros((n, m))

        for i in range(n_ens):
            innovation = obs_ensemble[i] - H @ ensemble[i]
            ensemble[i] = ensemble[i] + K @ innovation

        analysis_mean = ensemble.mean(axis=0)
        spread = float(np.std(ensemble, axis=0).mean())

        return {
            "analysis_field": analysis_mean.reshape(background.shape).tolist(),
            "spread": spread,
            "ensemble_size": n_ens,
            "grid_shape": list(background.shape),
            "innovation_variance": float(np.var(obs_ensemble - H @ ensemble)),
        }

    def _build_observation_operator(self, xb, observations, shape):
        n = len(xb)
        m = len(observations)
        y_obs = np.zeros(m)
        H = np.zeros((m, n))
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
