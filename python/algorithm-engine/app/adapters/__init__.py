"""Built-in algorithm adapters."""
from app.adapters.assimilation_adapter import (
    AssimilationAdapter,
    ThreeDimensionalVarAdapter,
    FourDimensionalVarAdapter,
    FiveDimensionalVarAdapter,
    EnKFAdapter,
    HybridAssimilationAdapter,
    EnhancedBayesianAdapter,
)
from app.adapters.planning_adapter import (
    PlanningAdapter,
    VRPTWAdapter,
    DERRTStarAdapter,
    DWAAdapter,
    MPCAdapter,
    AStarAdapter,
    DijkstraAdapter,
    RRTStarAdapter,
)
from app.adapters.risk_adapter import (
    RiskAdapter,
    WeatherRiskAdapter,
    TerrainRiskAdapter,
    AirspaceRiskAdapter,
    CompositeRiskAdapter,
)
from app.adapters.observation_adapter import (
    ObservationAdapter,
    InformationGainAdapter,
    AdaptiveObservationAdapter,
    SensorSchedulingAdapter,
)

__all__ = [
    "AssimilationAdapter", "ThreeDimensionalVarAdapter", "FourDimensionalVarAdapter",
    "FiveDimensionalVarAdapter", "EnKFAdapter", "HybridAssimilationAdapter",
    "EnhancedBayesianAdapter",
    "PlanningAdapter", "VRPTWAdapter", "DERRTStarAdapter", "DWAAdapter",
    "MPCAdapter", "AStarAdapter", "DijkstraAdapter", "RRTStarAdapter",
    "RiskAdapter", "WeatherRiskAdapter", "TerrainRiskAdapter",
    "AirspaceRiskAdapter", "CompositeRiskAdapter",
    "ObservationAdapter", "InformationGainAdapter",
    "AdaptiveObservationAdapter", "SensorSchedulingAdapter",
]
