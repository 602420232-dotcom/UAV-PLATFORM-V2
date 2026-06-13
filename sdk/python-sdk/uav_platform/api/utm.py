"""
UTM API module.

Provides methods for airspace management, flight plan submission,
real-time position tracking, and conflict detection.
"""

from __future__ import annotations

from typing import cast

from uav_platform.http import AsyncHttpClient, HttpClient
from uav_platform.models import (
    Airspace,
    ConflictAlert,
    ConflictCheckRequest,
    FlightPlan,
    SubmitFlightPlanRequest,
    UavPosition,
)


class UtmApi:
    """
    UTM (Unmanned Aircraft System Traffic Management) API client.

    Wraps all ``/v1/airspaces/*``, ``/v1/flight-plans/*``,
    ``/v1/tracking/*``, and ``/v1/conflict-alerts/*`` endpoints.
    """

    def __init__(self, http: HttpClient | AsyncHttpClient) -> None:
        self._http = http

    # ------------------------------------------------------------------
    # Airspace management
    # ------------------------------------------------------------------

    def list_airspaces(self) -> list[Airspace]:
        """List all airspaces."""
        raw = self._http.get("/v1/airspaces")
        return [Airspace.model_validate(item) for item in cast(list, raw)]

    def create_airspace(self, data: dict) -> Airspace:
        """Create a dynamic airspace."""
        raw = self._http.post("/v1/airspaces", data)
        return Airspace.model_validate(raw)

    def check_restriction(self, lon: float, lat: float, altitude: float) -> bool:
        """Check if a location has airspace restrictions."""
        raw = self._http.get(
            "/v1/airspaces/check",
            params={"lon": lon, "lat": lat, "altitude": altitude},
        )
        return bool(raw)

    # ------------------------------------------------------------------
    # Flight plan management
    # ------------------------------------------------------------------

    def submit_flight_plan(
        self,
        uav_id: str,
        waypoints: list[dict[str, float]],
        estimated_departure_time: str,
    ) -> FlightPlan:
        """Submit a flight plan for approval."""
        data = SubmitFlightPlanRequest(
            uav_id=uav_id,
            waypoints=waypoints,
            estimated_departure_time=estimated_departure_time,
        )
        raw = self._http.post("/v1/flight-plans", data.model_dump())
        return FlightPlan.model_validate(raw)

    def list_flight_plans(self) -> list[FlightPlan]:
        """List all flight plans."""
        raw = self._http.get("/v1/flight-plans")
        return [FlightPlan.model_validate(item) for item in cast(list, raw)]

    def approve_flight_plan(self, plan_id: int) -> FlightPlan:
        """Approve a submitted flight plan."""
        raw = self._http.post(f"/v1/flight-plans/{plan_id}/approve")
        return FlightPlan.model_validate(raw)

    def start_flight_plan(self, plan_id: int) -> FlightPlan:
        """Start (activate) an approved flight plan."""
        raw = self._http.post(f"/v1/flight-plans/{plan_id}/start")
        return FlightPlan.model_validate(raw)

    # ------------------------------------------------------------------
    # Tracking
    # ------------------------------------------------------------------

    def report_position(self, position: UavPosition) -> None:
        """Report real-time UAV position."""
        self._http.post("/v1/tracking/positions", position.model_dump())

    def check_conflict(
        self,
        planned_path: list[dict[str, float | str]],
        time_window: dict[str, str],
    ) -> list[ConflictAlert]:
        """Check for conflicts with existing flights."""
        data = ConflictCheckRequest(planned_path=planned_path, time_window=time_window)
        raw = self._http.post("/v1/tracking/conflicts/check", data.model_dump())
        return [ConflictAlert.model_validate(item) for item in cast(list, raw)]

    def list_conflict_alerts(self) -> list[ConflictAlert]:
        """List all active conflict alerts."""
        raw = self._http.get("/v1/conflict-alerts")
        return [ConflictAlert.model_validate(item) for item in cast(list, raw)]

    # ------------------------------------------------------------------
    # Async methods
    # ------------------------------------------------------------------

    async def list_airspaces_async(self) -> list[Airspace]:
        """Async: List all airspaces."""
        raw = await self._http.get("/v1/airspaces")
        return [Airspace.model_validate(item) for item in raw]

    async def create_airspace_async(self, data: dict) -> Airspace:
        """Async: Create a dynamic airspace."""
        raw = await self._http.post("/v1/airspaces", data)
        return Airspace.model_validate(raw)

    async def check_restriction_async(self, lon: float, lat: float, altitude: float) -> bool:
        """Async: Check if a location has airspace restrictions."""
        raw = await self._http.get(
            "/v1/airspaces/check",
            params={"lon": lon, "lat": lat, "altitude": altitude},
        )
        return bool(raw)

    async def submit_flight_plan_async(
        self,
        uav_id: str,
        waypoints: list[dict[str, float]],
        estimated_departure_time: str,
    ) -> FlightPlan:
        """Async: Submit a flight plan for approval."""
        data = SubmitFlightPlanRequest(
            uav_id=uav_id,
            waypoints=waypoints,
            estimated_departure_time=estimated_departure_time,
        )
        raw = await self._http.post("/v1/flight-plans", data.model_dump())
        return FlightPlan.model_validate(raw)

    async def list_flight_plans_async(self) -> list[FlightPlan]:
        """Async: List all flight plans."""
        raw = await self._http.get("/v1/flight-plans")
        return [FlightPlan.model_validate(item) for item in raw]

    async def approve_flight_plan_async(self, plan_id: int) -> FlightPlan:
        """Async: Approve a submitted flight plan."""
        raw = await self._http.post(f"/v1/flight-plans/{plan_id}/approve")
        return FlightPlan.model_validate(raw)

    async def start_flight_plan_async(self, plan_id: int) -> FlightPlan:
        """Async: Start (activate) an approved flight plan."""
        raw = await self._http.post(f"/v1/flight-plans/{plan_id}/start")
        return FlightPlan.model_validate(raw)

    async def report_position_async(self, position: UavPosition) -> None:
        """Async: Report real-time UAV position."""
        await self._http.post("/v1/tracking/positions", position.model_dump())

    async def check_conflict_async(
        self,
        planned_path: list[dict[str, float | str]],
        time_window: dict[str, str],
    ) -> list[ConflictAlert]:
        """Async: Check for conflicts with existing flights."""
        data = ConflictCheckRequest(planned_path=planned_path, time_window=time_window)
        raw = await self._http.post("/v1/tracking/conflicts/check", data.model_dump())
        return [ConflictAlert.model_validate(item) for item in raw]

    async def list_conflict_alerts_async(self) -> list[ConflictAlert]:
        """Async: List all active conflict alerts."""
        raw = await self._http.get("/v1/conflict-alerts")
        return [ConflictAlert.model_validate(item) for item in raw]
