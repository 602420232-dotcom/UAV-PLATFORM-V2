"""
Assimilation API module.

Provides methods for submitting, querying, and managing data assimilation tasks
(3DVAR, 4DVAR, 5DVAR, EnKF, Hybrid, Enhanced Bayesian).
"""

from __future__ import annotations

from typing import Any, cast

from uav_platform.http import AsyncHttpClient, HttpClient
from uav_platform.models import (
    AssimilationResult,
    AssimilationTask,
    SubmitTaskRequest,
    TaskQueryRequest,
)


class AssimilationApi:
    """
    Data assimilation API client.

    Wraps all ``/v1/assimilation/*`` endpoints.
    """

    def __init__(self, http: HttpClient | AsyncHttpClient) -> None:
        self._http = http

    # ------------------------------------------------------------------
    # Sync methods
    # ------------------------------------------------------------------

    def submit_task(
        self,
        type: str,
        algorithm: str,
        start_time: str,
        end_time: str,
        region: dict | None = None,
        observation_sources: list[str] | None = None,
    ) -> int:
        """Submit a new data assimilation task. Returns the task ID."""
        data = SubmitTaskRequest(
            type=type,
            algorithm=algorithm,
            start_time=start_time,
            end_time=end_time,
            region=region,
            observation_sources=observation_sources,
        )
        raw = self._http.post("/v1/assimilation/tasks", data.model_dump(exclude_none=True))
        return int(cast(Any, raw))

    def get_task_status(self, task_id: int) -> AssimilationTask:
        """Get the status of an assimilation task."""
        raw = self._http.get(f"/v1/assimilation/tasks/{task_id}")
        return AssimilationTask.model_validate(raw)

    def get_task_result(self, task_id: int) -> AssimilationResult:
        """Get the result of a completed assimilation task."""
        raw = self._http.get(f"/v1/assimilation/tasks/{task_id}/result")
        return AssimilationResult.model_validate(raw)

    def list_tasks(
        self,
        status: str | None = None,
        type: str | None = None,
        page: int = 1,
        size: int = 10,
    ) -> dict:
        """List assimilation tasks with optional filtering."""
        params = TaskQueryRequest(status=status, type=type, page=page, size=size)
        raw = self._http.get("/v1/assimilation/tasks", params=params.model_dump(exclude_none=True))
        return cast(dict, raw)

    def cancel_task(self, task_id: int) -> None:
        """Cancel a pending or running assimilation task."""
        self._http.post(f"/v1/assimilation/tasks/{task_id}/cancel")

    # ------------------------------------------------------------------
    # Async methods
    # ------------------------------------------------------------------

    async def submit_task_async(
        self,
        type: str,
        algorithm: str,
        start_time: str,
        end_time: str,
        region: dict | None = None,
        observation_sources: list[str] | None = None,
    ) -> int:
        """Async: Submit a new data assimilation task."""
        data = SubmitTaskRequest(
            type=type,
            algorithm=algorithm,
            start_time=start_time,
            end_time=end_time,
            region=region,
            observation_sources=observation_sources,
        )
        raw = await self._http.post("/v1/assimilation/tasks", data.model_dump(exclude_none=True))
        return int(raw)

    async def get_task_status_async(self, task_id: int) -> AssimilationTask:
        """Async: Get the status of an assimilation task."""
        raw = await self._http.get(f"/v1/assimilation/tasks/{task_id}")
        return AssimilationTask.model_validate(raw)

    async def get_task_result_async(self, task_id: int) -> AssimilationResult:
        """Async: Get the result of a completed assimilation task."""
        raw = await self._http.get(f"/v1/assimilation/tasks/{task_id}/result")
        return AssimilationResult.model_validate(raw)

    async def list_tasks_async(
        self,
        status: str | None = None,
        type: str | None = None,
        page: int = 1,
        size: int = 10,
    ) -> dict:
        """Async: List assimilation tasks with optional filtering."""
        params = TaskQueryRequest(status=status, type=type, page=page, size=size)
        raw = await self._http.get(
            "/v1/assimilation/tasks", params=params.model_dump(exclude_none=True)
        )
        return raw

    async def cancel_task_async(self, task_id: int) -> None:
        """Async: Cancel a pending or running assimilation task."""
        await self._http.post(f"/v1/assimilation/tasks/{task_id}/cancel")
