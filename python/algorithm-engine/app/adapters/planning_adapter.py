"""Adapters for path planning algorithms."""

from __future__ import annotations

import logging
from typing import Any

from app.core.adapter import AlgorithmAdapter
from app.core.models import AlgorithmMetadata

logger = logging.getLogger(__name__)


class PlanningAdapter(AlgorithmAdapter):
    """Base adapter for planning algorithms."""

    category = "planning"

    def validate_input(self, params: dict[str, Any]) -> bool:
        required = ["start", "goal"]
        return all(k in params for k in required)


class VRPTWAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="vrptw",
                name="VRPTW",
                category="planning",
                version="1.0.0",
                description=(
                    "Vehicle Routing Problem with Time Windows"
                    " for multi-UAV mission planning"
                ),
                input_schema={
                    "type": "object",
                    "required": ["start", "goal", "waypoints"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "waypoints": {"type": "array"},
                        "time_windows": {"type": "array"},
                        "capacity": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "routes": {"type": "array"},
                        "total_cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.vrptw import VRPTWPlanner

        return VRPTWPlanner(params).solve()


class DERRTStarAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="de_rrt_star",
                name="DERRTStar",
                category="planning",
                version="1.0.0",
                description=("Differential Evolution enhanced RRT* for complex environments"),
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "obstacles": {"type": "array"},
                        "max_iterations": {"type": "integer"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.de_rrt_star import DERRTStarPlanner

        return DERRTStarPlanner(params).solve()


class DWAAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="dwa",
                name="DWA",
                category="planning",
                version="1.0.0",
                description="Dynamic Window Approach for local obstacle avoidance",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "obstacles": {"type": "array"},
                        "velocity": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "trajectory": {"type": "array"},
                        "velocity": {"type": "array"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.dwa import DWAPlanner

        return DWAPlanner(params).solve()


class MPCAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="mpc",
                name="MPC",
                category="planning",
                version="1.0.0",
                description=("Model Predictive Control for dynamic re-planning under uncertainty"),
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "horizon": {"type": "integer"},
                        "risk_field": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "control_sequence": {"type": "array"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.mpc import MPCPlanner

        return MPCPlanner(params).solve()


class AStarAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="a_star",
                name="AStar",
                category="planning",
                version="1.0.0",
                description="A* search algorithm for grid-based path planning",
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "grid_size": {"type": "array"},
                        "obstacles": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.a_star import AStarPlanner

        return AStarPlanner(params).solve()


class DijkstraAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="dijkstra",
                name="Dijkstra",
                category="planning",
                version="1.0.0",
                description=("Dijkstra shortest path algorithm for grid-based planning"),
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "grid_size": {"type": "array"},
                        "obstacles": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.dijkstra import DijkstraPlanner

        return DijkstraPlanner(params).solve()


class RRTStarAdapter(PlanningAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.set_metadata(
            AlgorithmMetadata(
                id="rrt_star",
                name="RRTStar",
                category="planning",
                version="1.0.0",
                description=("Rapidly-exploring Random Tree Star for optimal path planning"),
                input_schema={
                    "type": "object",
                    "required": ["start", "goal"],
                    "properties": {
                        "start": {"type": "array"},
                        "goal": {"type": "array"},
                        "obstacles": {"type": "array"},
                        "max_iterations": {"type": "integer"},
                        "step_size": {"type": "number"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "array"},
                        "cost": {"type": "number"},
                    },
                },
            )
        )

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.algorithms.planning.rrt_star import RRTStarPlanner

        return RRTStarPlanner(params).solve()
