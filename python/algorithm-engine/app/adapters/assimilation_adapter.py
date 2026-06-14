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
                    "3D-VAR data assimilation using spatial covariance "
                    "and variational optimization"
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
                description=(  # fmt: skip
                    "5D-VAR with risk, dynamic perturbation, and AI parameterization dimensions"
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


class AdaptiveHybridAdapter(AssimilationAdapter):
    """自适应混合同化适配器。"""

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="adaptive_hybrid",
                name="AdaptiveHybridAssimilation",
                category="assimilation",
                version="1.0.0",
                description="根据观测密度动态调整 3D-VAR 和 EnKF 权重的自适应混合同化",
                input_schema={
                    "type": "object",
                    "required": ["background_field", "observations"],
                    "properties": {
                        "background_field": {"type": "array"},
                        "observations": {"type": "array"},
                        "weight_threshold": {"type": "number"},
                        "density_radius": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis_field": {"type": "array"},
                        "adaptive_weights": {"type": "object"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.assimilation.adaptive_hybrid import (
            AdaptiveHybridAssimilation,
        )

        algo = AdaptiveHybridAssimilation(params.get("config"))
        return algo.assimilate(params)


class MultiScaleHybridAdapter(AssimilationAdapter):
    """多尺度混合同化适配器。"""

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="multiscale_hybrid",
                name="MultiScaleHybridAssimilation",
                category="assimilation",
                version="1.0.0",
                description="在不同空间分辨率上分别执行同化后融合的多尺度混合同化",
                input_schema={
                    "type": "object",
                    "required": ["background_field", "observations"],
                    "properties": {
                        "background_field": {"type": "array"},
                        "observations": {"type": "array"},
                        "coarse_factor": {"type": "integer"},
                        "fusion_weight": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis_field": {"type": "array"},
                        "coarse_analysis": {"type": "array"},
                        "fine_analysis": {"type": "array"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.assimilation.multiscale_hybrid import (
            MultiScaleHybridAssimilation,
        )

        algo = MultiScaleHybridAssimilation(params.get("config"))
        return algo.assimilate(params)


class AdaptiveAssimilatorAdapter(AssimilationAdapter):
    """自适应同化器适配器。"""

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="adaptive_assimilator",
                name="AdaptiveAssimilator",
                category="assimilation",
                version="1.0.0",
                description="根据背景误差与观测误差比值自动选择最优同化策略",
                input_schema={
                    "type": "object",
                    "required": ["background_field", "observations"],
                    "properties": {
                        "background_field": {"type": "array"},
                        "observations": {"type": "array"},
                        "error_ratio_threshold": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis_field": {"type": "array"},
                        "selected_strategy": {"type": "string"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.assimilation.adaptive_assimilator import (
            AdaptiveAssimilator,
        )

        algo = AdaptiveAssimilator(params.get("config"))
        return algo.assimilate(params)


class VarianceFieldOptimizerAdapter(AssimilationAdapter):
    """方差场优化器适配器。"""

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="variance_field_optimizer",
                name="VarianceFieldOptimizer",
                category="assimilation",
                version="1.0.0",
                description="基于 Desroziers 诊断迭代优化背景误差方差场",
                input_schema={
                    "type": "object",
                    "required": ["background_field", "observations"],
                    "properties": {
                        "background_field": {"type": "array"},
                        "observations": {"type": "array"},
                        "max_iterations": {"type": "integer"},
                        "relaxation_factor": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis_field": {"type": "array"},
                        "optimized_variance": {"type": "array"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.assimilation.variance_field_optimizer import (
            VarianceFieldOptimizer,
        )

        algo = VarianceFieldOptimizer(params.get("config"))
        return algo.assimilate(params)


class AdaptiveVarianceFieldAdapter(AssimilationAdapter):
    """自适应方差场适配器。"""

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="adaptive_variance_field",
                name="AdaptiveVarianceField",
                category="assimilation",
                version="1.0.0",
                description="基于流依赖的背景误差协方差估计（集合+气候学混合）",
                input_schema={
                    "type": "object",
                    "required": ["background_field", "observations"],
                    "properties": {
                        "background_field": {"type": "array"},
                        "observations": {"type": "array"},
                        "climatology_weight": {"type": "number"},
                        "localization_radius": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis_field": {"type": "array"},
                        "flow_dependent_variance": {"type": "array"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.assimilation.adaptive_variance_field import (
            AdaptiveVarianceField,
        )

        algo = AdaptiveVarianceField(params.get("config"))
        return algo.assimilate(params)


class BayesianAssimilatorAdapter(AssimilationAdapter):
    """贝叶斯同化器适配器。"""

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="bayesian_assimilator",
                name="BayesianAssimilator",
                category="assimilation",
                version="1.0.0",
                description="贝叶斯框架融合先验与似然的高斯后验同化",
                input_schema={
                    "type": "object",
                    "required": ["background_field", "observations"],
                    "properties": {
                        "background_field": {"type": "array"},
                        "observations": {"type": "array"},
                        "prior_confidence": {"type": "number"},
                        "likelihood_sigma": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis_field": {"type": "array"},
                        "posterior_variance": {"type": "array"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.assimilation.bayesian_assimilator import (
            BayesianAssimilator,
        )

        algo = BayesianAssimilator(params.get("config"))
        return algo.assimilate(params)


class CompatibleAssimilatorAdapter(AssimilationAdapter):
    """兼容同化器适配器。"""

    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="compatible_assimilator",
                name="CompatibleAssimilator",
                category="assimilation",
                version="1.0.0",
                description="在标准同化基础上施加兼容性约束，防止分析增量过大",
                input_schema={
                    "type": "object",
                    "required": ["background_field", "observations"],
                    "properties": {
                        "background_field": {"type": "array"},
                        "observations": {"type": "array"},
                        "max_analysis_increment": {"type": "number"},
                        "compatibility_weight": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "analysis_field": {"type": "array"},
                        "increment_clipped": {"type": "boolean"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.assimilation.compatible_assimilator import (
            CompatibleAssimilator,
        )

        algo = CompatibleAssimilator(params.get("config"))
        return algo.assimilate(params)
