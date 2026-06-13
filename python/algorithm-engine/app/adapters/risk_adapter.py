"""Adapters for risk assessment algorithms."""

from __future__ import annotations

import logging
from typing import Any

from app.core.adapter import AlgorithmAdapter
from app.core.models import AlgorithmMetadata

logger = logging.getLogger(__name__)


class RiskAdapter(AlgorithmAdapter):
    """Base adapter for risk assessment algorithms."""
    category = "risk"

    def validate_input(self, params: dict[str, Any]) -> bool:
        required = ["area", "conditions"]
        return all(k in params for k in required)


class WeatherRiskAdapter(RiskAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(AlgorithmMetadata(
            id="weather_risk", name="WeatherRisk", category="risk", version="1.0.0",
            description="Weather-related flight risk assessment",
            input_schema={"type": "object", "required": ["area", "conditions"],
                          "properties": {"area": {"type": "object"}, "conditions": {"type": "object"},
                                         "wind_speed": {"type": "number"}, "visibility": {"type": "number"},
                                         "precipitation": {"type": "number"}}},
            output_schema={"type": "object", "properties": {"risk_score": {"type": "number"}, "risk_level": {"type": "string"}}},
        ))

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.risk.weather_risk import WeatherRiskAssessor
        return WeatherRiskAssessor(params).assess()


class TerrainRiskAdapter(RiskAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(AlgorithmMetadata(
            id="terrain_risk", name="TerrainRisk", category="risk", version="1.0.0",
            description="Terrain and obstacle risk assessment for low-altitude UAV flights",
            input_schema={"type": "object", "required": ["area", "conditions"],
                          "properties": {"area": {"type": "object"}, "conditions": {"type": "object"},
                                         "elevation_data": {"type": "array"}, "flight_altitude": {"type": "number"}}},
            output_schema={"type": "object", "properties": {"risk_score": {"type": "number"}, "terrain_map": {"type": "array"}}},
        ))

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.risk.terrain_risk import TerrainRiskAssessor
        return TerrainRiskAssessor(params).assess()


class AirspaceRiskAdapter(RiskAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(AlgorithmMetadata(
            id="airspace_risk", name="AirspaceRisk", category="risk", version="1.0.0",
            description="Airspace restriction and conflict risk assessment",
            input_schema={"type": "object", "required": ["area", "conditions"],
                          "properties": {"area": {"type": "object"}, "conditions": {"type": "object"},
                                         "airspace_zones": {"type": "array"}, "traffic_density": {"type": "number"}}},
            output_schema={"type": "object", "properties": {"risk_score": {"type": "number"}, "conflicts": {"type": "array"}}},
        ))

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.risk.airspace_risk import AirspaceRiskAssessor
        return AirspaceRiskAssessor(params).assess()


class CompositeRiskAdapter(RiskAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(AlgorithmMetadata(
            id="composite_risk", name="CompositeRisk", category="risk", version="1.0.0",
            description="Composite risk assessment combining weather, terrain, and airspace risks",
            input_schema={"type": "object", "required": ["area", "conditions"],
                          "properties": {"area": {"type": "object"}, "conditions": {"type": "object"},
                                         "weights": {"type": "object"}}},
            output_schema={"type": "object", "properties": {"risk_score": {"type": "number"}, "breakdown": {"type": "object"}}},
        ))

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.risk.composite_risk import CompositeRiskAssessor
        return CompositeRiskAssessor(params).assess()
