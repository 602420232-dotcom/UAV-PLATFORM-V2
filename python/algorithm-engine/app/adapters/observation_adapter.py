"""Adapters for observation decision algorithms."""

from __future__ import annotations

import logging
from typing import Any

from app.core.adapter import AlgorithmAdapter
from app.core.models import AlgorithmMetadata

logger = logging.getLogger(__name__)


class ObservationAdapter(AlgorithmAdapter):
    """Base adapter for observation decision algorithms."""
    category = "observation"

    def validate_input(self, params: dict[str, Any]) -> bool:
        required = ["current_state", "available_sensors"]
        return all(k in params for k in required)


class InformationGainAdapter(ObservationAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(AlgorithmMetadata(
            id="information_gain",
            name="InformationGain",
            category="observation",
            version="1.0.0",
            description=(
                "Information gain based optimal observation placement"
            ),
            input_schema={
                "type": "object",
                "required": ["current_state", "available_sensors"],
                "properties": {
                    "current_state": {"type": "object"},
                    "available_sensors": {"type": "array"},
                    "uncertainty_field": {"type": "array"},
                    "budget": {"type": "integer"},
                },
            },
            output_schema={
                "type": "object",
                "properties": {
                    "selected_positions": {"type": "array"},
                    "expected_gain": {"type": "number"},
                },
            },
        ))

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.observation.information_gain import (
            InformationGainOptimizer,
        )
        return InformationGainOptimizer(params).optimize()


class AdaptiveObservationAdapter(ObservationAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(AlgorithmMetadata(
            id="adaptive_observation",
            name="AdaptiveObservation",
            category="observation",
            version="1.0.0",
            description=(
                "Adaptive observation strategy that adjusts "
                "based on real-time uncertainty"
            ),
            input_schema={
                "type": "object",
                "required": ["current_state", "available_sensors"],
                "properties": {
                    "current_state": {"type": "object"},
                    "available_sensors": {"type": "array"},
                    "uncertainty_field": {"type": "array"},
                    "history": {"type": "array"},
                },
            },
            output_schema={
                "type": "object",
                "properties": {
                    "strategy": {"type": "object"},
                    "positions": {"type": "array"},
                },
            },
        ))

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.observation.adaptive_observation import (
            AdaptiveObservationPlanner,
        )
        return AdaptiveObservationPlanner(params).plan()


class SensorSchedulingAdapter(ObservationAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(AlgorithmMetadata(
            id="sensor_scheduling",
            name="SensorScheduling",
            category="observation",
            version="1.0.0",
            description=(
                "Multi-sensor scheduling optimization "
                "for UAV fleet observation"
            ),
            input_schema={
                "type": "object",
                "required": ["current_state", "available_sensors"],
                "properties": {
                    "current_state": {"type": "object"},
                    "available_sensors": {"type": "array"},
                    "time_horizon": {"type": "number"},
                    "constraints": {"type": "object"},
                },
            },
            output_schema={
                "type": "object",
                "properties": {
                    "schedule": {"type": "array"},
                    "coverage": {"type": "number"},
                },
            },
        ))

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.observation.sensor_scheduling import SensorScheduler
        return SensorScheduler(params).schedule()
