"""
Planning API module.

Provides methods for path planning and mission planning, including
VRPTW, DE-RRT*, DWA, MPC, A*, Dijkstra, and RRT* algorithms.
"""

from __future__ import annotations

from typing import cast

from uav_platform.http import AsyncHttpClient, HttpClient
from uav_platform.models import (
    MissionPlan,
    PathResult,
    PlanMissionRequest,
    PlanningTask,
    PlanPathRequest,
)


class PlanningApi:
    """
    Path and mission planning API client.

    Wraps all ``/v1/planning/*`` endpoints.
    """

    def __init__(self, http: HttpClient | AsyncHttpClient) -> None:
        self._http = http

    # ------------------------------------------------------------------
    # Sync methods
    # ------------------------------------------------------------------

    def plan_path(
        self,
        start_point: dict[str, float],
        end_point: dict[str, float],
        waypoints: list[dict[str, float]] | None = None,
        algorithm: str | None = None,
    ) -> PlanningTask:
        """Submit a path planning task."""
        data = PlanPathRequest(
            start_point=start_point,
            end_point=end_point,
            waypoints=waypoints,
            algorithm=algorithm,
        )
        raw = self._http.post("/v1/planning/path", data.model_dump(exclude_none=True))
        return PlanningTask.model_validate(raw)

    def plan_mission(
        self,
        area: dict[str, float],
        altitude: float,
        overlap: float = 0.0,
        algorithm: str | None = None,
    ) -> PlanningTask:
        """Submit a mission planning task."""
        data = PlanMissionRequest(
            area=area,
            altitude=altitude,
            overlap=overlap,
            algorithm=algorithm,
        )
        raw = self._http.post("/v1/planning/mission", data.model_dump(exclude_none=True))
        return PlanningTask.model_validate(raw)

    def get_task(self, task_id: int) -> PlanningTask:
        """Get planning task status."""
        raw = self._http.get(f"/v1/planning/tasks/{task_id}")
        return PlanningTask.model_validate(raw)

    def get_path_result(self, task_id: int) -> PathResult:
        """Get path planning result."""
        raw = self._http.get(f"/v1/planning/tasks/{task_id}/result")
        return PathResult.model_validate(raw)

    def get_mission_plan(self, task_id: int) -> MissionPlan:
        """Get mission planning result."""
        raw = self._http.get(f"/v1/planning/tasks/{task_id}/mission")
        return MissionPlan.model_validate(raw)

    def list_tasks(self) -> list[PlanningTask]:
        """List all planning tasks."""
        raw = self._http.get("/v1/planning/tasks")
        return [PlanningTask.model_validate(item) for item in cast(list, raw)]

    def cancel_task(self, task_id: int) -> None:
        """Cancel a planning task."""
        self._http.post(f"/v1/planning/tasks/{task_id}/cancel")

    # ------------------------------------------------------------------
    # Async methods
    # ------------------------------------------------------------------

    async def plan_path_async(
        self,
        start_point: dict[str, float],
        end_point: dict[str, float],
        waypoints: list[dict[str, float]] | None = None,
        algorithm: str | None = None,
    ) -> PlanningTask:
        """Async: Submit a path planning task."""
        data = PlanPathRequest(
            start_point=start_point,
            end_point=end_point,
            waypoints=waypoints,
            algorithm=algorithm,
        )
        raw = await self._http.post("/v1/planning/path", data.model_dump(exclude_none=True))
        return PlanningTask.model_validate(raw)

    async def plan_mission_async(
        self,
        area: dict[str, float],
        altitude: float,
        overlap: float = 0.0,
        algorithm: str | None = None,
    ) -> PlanningTask:
        """Async: Submit a mission planning task."""
        data = PlanMissionRequest(
            area=area,
            altitude=altitude,
            overlap=overlap,
            algorithm=algorithm,
        )
        raw = await self._http.post("/v1/planning/mission", data.model_dump(exclude_none=True))
        return PlanningTask.model_validate(raw)

    async def get_task_async(self, task_id: int) -> PlanningTask:
        """Async: Get planning task status."""
        raw = await self._http.get(f"/v1/planning/tasks/{task_id}")
        return PlanningTask.model_validate(raw)

    async def get_path_result_async(self, task_id: int) -> PathResult:
        """Async: Get path planning result."""
        raw = await self._http.get(f"/v1/planning/tasks/{task_id}/result")
        return PathResult.model_validate(raw)

    async def get_mission_plan_async(self, task_id: int) -> MissionPlan:
        """Async: Get mission planning result."""
        raw = await self._http.get(f"/v1/planning/tasks/{task_id}/mission")
        return MissionPlan.model_validate(raw)

    async def list_tasks_async(self) -> list[PlanningTask]:
        """Async: List all planning tasks."""
        raw = await self._http.get("/v1/planning/tasks")
        return [PlanningTask.model_validate(item) for item in raw]

    async def cancel_task_async(self, task_id: int) -> None:
        """Async: Cancel a planning task."""
        await self._http.post(f"/v1/planning/tasks/{task_id}/cancel")
