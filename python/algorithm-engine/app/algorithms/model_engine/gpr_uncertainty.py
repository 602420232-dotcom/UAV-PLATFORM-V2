"""GPR (Gaussian Process Regression) Uncertainty Quantification.

Migrated from: model-engine/gpr_risk/model.py

Original: GPRegressionModel using GPyTorch. Standalone numpy/scipy implementation.
"""
from __future__ import annotations
import logging
from typing import Any, Optional
import numpy as np
from scipy.spatial.distance import cdist

logger = logging.getLogger(__name__)

class GPRUncertaintyQuantifier:
    """Gaussian Process Regression for uncertainty quantification."""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.length_scale = self.config.get("length_scale", 1.0)
        self.signal_variance = self.config.get("signal_variance", 1.0)
        self.noise_variance = self.config.get("noise_variance", 0.1)

    def predict(self, params: dict[str, Any]) -> dict[str, Any]:
        train_x = np.asarray(params.get("train_x", np.zeros((10, 2))))
        train_y = np.asarray(params.get("train_y", np.zeros(10)))
        test_x = np.asarray(params.get("test_x", np.zeros((5, 2))))
        n_train = len(train_x)
        n_test = len(test_x)
        K = self._rbf_kernel(train_x, train_x) + self.noise_variance * np.eye(n_train)
        K_s = self._rbf_kernel(train_x, test_x)
        K_ss = self._rbf_kernel(test_x, test_x)
        try:
            L = np.linalg.cholesky(K)
            alpha = np.linalg.solve(L.T, np.linalg.solve(L, train_y))
            mean = K_s.T @ alpha
            v = np.linalg.solve(L, K_s)
            var = np.diag(K_ss) - np.sum(v ** 2, axis=0)
            var = np.maximum(var, 1e-10)
        except np.linalg.LinAlgError:
            mean = np.zeros(n_test)
            var = np.ones(n_test) * self.signal_variance
        return {"mean": mean.tolist(), "variance": var.tolist(), "std": np.sqrt(var).tolist(), "confidence_95_lower": (mean - 1.96 * np.sqrt(var)).tolist(), "confidence_95_upper": (mean + 1.96 * np.sqrt(var)).tolist(), "n_train": n_train, "n_test": n_test}

    def _rbf_kernel(self, X1, X2):
        dists = cdist(X1, X2, metric="sqeuclidean")
        return self.signal_variance * np.exp(-0.5 * dists / self.length_scale ** 2)
