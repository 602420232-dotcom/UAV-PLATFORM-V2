"""Adapters for data assimilation algorithms."""

from __future__ import annotations

import logging
from typing import Any

from app.core.adapter import AlgorithmAdapter
from app.core.models import AlgorithmMetadata

logger = logging.getLogger(__name__)


class AssimilationAdapter(AlgorithmAdapter):
    """Base adapter for assimilation algorithms."""

    category = "assimilation"

    def validate_input(self, params: dict[str, Any]) -> bool:
        required = ["background_field", "observations"]
        return all(k in params for k in required)


class ThreeDimensionalVarAdapter(AssimilationAdapter):
    """3D-VAR data assimilation adapter."""

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="3dvar",
                name="ThreeDimensionalVAR",
                category="assimilation",
                version="1.0.0",
                description=(
                    "3D-VAR data assimilation using spatial covariance"
                    " and variational optimization"
                ),
                input_schema={
                    "type": "object",
                    "required": ["background_field", "observations"],
                    "properties": {
                        "background_field": {"type": "array"},
                        "observations": {"type": "array"},
                        "grid_shape": {"type": "array"},
                        "resolution": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis_field": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.assimilation.three_dimensional_var import (
            ThreeDimensionalVAR,
        )

        algo = ThreeDimensionalVAR(params.get("config"))
        return algo.assimilate(params)


class FourDimensionalVarAdapter(AssimilationAdapter):
    """4D-VAR data assimilation adapter."""

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="4dvar",
                name="FourDimensionalVar",
                category="assimilation",
                version="1.0.0",
                description=("4D-VAR data assimilation with temporal dimension support"),
                input_schema={
                    "type": "object",
                    "required": ["background_field", "observations"],
                    "properties": {
                        "background_field": {"type": "array"},
                        "observations": {"type": "array"},
                        "time_windows": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {"analysis_field": {"type": "array"}},
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.assimilation.four_dimensional_var import (
            FourDimensionalVAR,
        )

        algo = FourDimensionalVAR(params.get("config"))
        return algo.assimilate(params)


class FiveDimensionalVarAdapter(AssimilationAdapter):
    """5D-VAR data assimilation adapter."""

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="5dvar",
                name="FiveDimensionalVar",
                category="assimilation",
                version="1.0.0",
                description=(
                    "5D-VAR with risk, dynamic perturbation,"
                    " and AI parameterization dimensions"
                ),
                input_schema={
                    "type": "object",
                    "required": ["background_field", "observations"],
                    "properties": {
                        "background_field": {"type": "array"},
                        "observations": {"type": "array"},
                        "risk_weight": {"type": "number"},
                        "ai_correction": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis_field": {"type": "array"},
                        "risk_cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.assimilation.five_dimensional_var import (
            FiveDimensionalVAR,
        )

        algo = FiveDimensionalVAR(params.get("config"))
        return algo.assimilate(params)


class EnKFAdapter(AssimilationAdapter):
    """Ensemble Kalman Filter adapter."""

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="enkf",
                name="EnKF",
                category="assimilation",
                version="1.0.0",
                description="Ensemble Kalman Filter for nonlinear systems",
                input_schema={
                    "type": "object",
                    "required": ["background_field", "observations"],
                    "properties": {
                        "background_field": {"type": "array"},
                        "observations": {"type": "array"},
                        "ensemble_size": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis_field": {"type": "array"},
                        "spread": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.assimilation.ensemble_kalman_filter import EnKF

        algo = EnKF(params.get("config"))
        return algo.assimilate(params)


class HybridAssimilationAdapter(AssimilationAdapter):
    """Hybrid assimilation adapter."""

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="hybrid_assimilation",
                name="HybridAssimilation",
                category="assimilation",
                version="1.0.0",
                description=("Hybrid assimilation combining multiple algorithm strengths"),
                input_schema={
                    "type": "object",
                    "required": ["background_field", "observations"],
                    "properties": {
                        "background_field": {"type": "array"},
                        "observations": {"type": "array"},
                        "algorithm_types": {"type": "array"},
                        "weights": {"type": "object"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis_field": {"type": "array"},
                        "weights": {"type": "object"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.assimilation.hybrid_assimilation import (
            HybridAssimilation,
        )

        algo = HybridAssimilation(
            params.get("config"),
            params.get("algorithm_types"),
        )
        return algo.assimilate(params)


class EnhancedBayesianAdapter(AssimilationAdapter):
    """Enhanced Bayesian assimilation adapter."""

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="enhanced_bayesian",
                name="EnhancedBayesianAssimilation",
                category="assimilation",
                version="1.0.0",
                description=("Enhanced Bayesian assimilation with deep learning components"),
                input_schema={
                    "type": "object",
                    "required": ["background_field", "observations"],
                    "properties": {
                        "background_field": {"type": "array"},
                        "observations": {"type": "array"},
                        "use_ml": {"type": "boolean"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis_field": {"type": "array"},
                        "ml_correction": {"type": "array"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.assimilation.enhanced_bayesian import (
            EnhancedBayesianAssimilation,
        )

        algo = EnhancedBayesianAssimilation(params.get("config"))
        return algo.assimilate(params)
