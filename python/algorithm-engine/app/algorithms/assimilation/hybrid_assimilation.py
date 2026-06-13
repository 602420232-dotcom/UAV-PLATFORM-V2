"""Hybrid Assimilation Algorithm.

Migrated from: data-assimilation-platform/algorithm_core/src/bayesian_assimilation/models/hybrid.py
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class HybridAssimilation:
    """Hybrid data assimilation combining multiple algorithms.

    Supports weighted combination of 3D-VAR, EnKF, 4D-VAR, and Enhanced Bayesian.
    """

    def __init__(self, config: Optional[dict[str, Any]] = None, algorithm_types: Optional[list[str]] = None):
        self.config = config or {}
        self.algorithm_types = algorithm_types or ["3dvar", "enkf"]
        self.weights: dict[str, float] = {}
        self._init_weights()

    def _init_weights(self) -> None:
        n = len(self.algorithm_types)
        for algo_type in self.algorithm_types:
            self.weights[algo_type] = 1.0 / n

    def assimilate(self, params: dict[str, Any]) -> dict[str, Any]:
        """Run hybrid assimilation."""
        from app.algorithms.assimilation.three_dimensional_var import ThreeDimensionalVAR
        from app.algorithms.assimilation.ensemble_kalman_filter import EnKF

        custom_weights = params.get("weights")
        if custom_weights:
            self.weights.update(custom_weights)

        background = np.asarray(params.get("background_field"))
        results: dict[str, dict[str, Any]] = {}
        analysis_fields: list[np.ndarray] = []

        for algo_type in self.algorithm_types:
            try:
                if algo_type == "3dvar":
                    algo = ThreeDimensionalVAR(self.config)
                    result = algo.assimilate(params)
                elif algo_type == "enkf":
                    algo = EnKF(self.config)
                    result = algo.assimilate(params)
                else:
                    logger.warning("Unknown algorithm type: %s, skipping", algo_type)
                    continue
                results[algo_type] = result
                field = np.asarray(result["analysis_field"])
                analysis_fields.append(field)
            except Exception as exc:
                logger.error("Algorithm %s failed: %s", algo_type, exc)
                results[algo_type] = {"error": str(exc)}

        if analysis_fields:
            weights = np.array([self.weights.get(t, 0) for t in self.algorithm_types if t in results and "error" not in results[t]])
            if weights.sum() > 0:
                weights = weights / weights.sum()
                combined = sum(w * f for w, f in zip(weights, analysis_fields))
            else:
                combined = analysis_fields[0]
        else:
            combined = background

        return {
            "analysis_field": combined.tolist(),
            "individual_results": results,
            "weights_used": self.weights,
            "algorithms_used": self.algorithm_types,
        }
