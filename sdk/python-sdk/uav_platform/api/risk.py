"""
Risk API module.

Provides methods for comprehensive risk assessment, regional risk maps,
historical records, and airworthiness evaluation.
"""

from __future__ import annotations

from typing import cast

from uav_platform.http import AsyncHttpClient, HttpClient
from uav_platform.models import (
    AirworthinessAssessment,
    AirworthinessRequest,
    RiskAssessment,
    RiskQueryRequest,
)


class RiskApi:
    """
    Risk and airworthiness assessment API client.

    Wraps all ``/v1/risk/*`` endpoints.
    """

    def __init__(self, http: HttpClient | AsyncHttpClient) -> None:
        self._http = http

    # ------------------------------------------------------------------
    # Sync methods
    # ------------------------------------------------------------------

    def assess(
        self,
        path: list[dict[str, float]],
        time: str,
        uav_type: str | None = None,
    ) -> RiskAssessment:
        """Perform comprehensive risk assessment along a flight path."""
        data = RiskQueryRequest(path=path, time=time, uav_type=uav_type)
        raw = self._http.post("/v1/risk/assess", data.model_dump(exclude_none=True))
        return RiskAssessment.model_validate(raw)

    def get_risk_map(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        resolution: float | None = None,
    ) -> list[RiskAssessment]:
        """Get regional risk grid map."""
        params = {
            "minLon": min_lon,
            "minLat": min_lat,
            "maxLon": max_lon,
            "maxLat": max_lat,
        }
        if resolution is not None:
            params["resolution"] = resolution
        raw = self._http.get("/v1/risk/map", params=params)
        return [RiskAssessment.model_validate(item) for item in cast(list, raw)]

    def get_history(
        self,
        tenant_id: int | None = None,
        type: str | None = None,
        limit: int | None = None,
    ) -> list[RiskAssessment]:
        """Get historical risk assessment records."""
        params: dict = {}
        if tenant_id is not None:
            params["tenantId"] = tenant_id
        if type is not None:
            params["type"] = type
        if limit is not None:
            params["limit"] = limit
        raw = self._http.get("/v1/risk/history", params=params)
        return [RiskAssessment.model_validate(item) for item in cast(list, raw)]

    def assess_airworthiness(
        self,
        uav_type: str,
        weather_conditions: dict[str, float],
        route: list[dict[str, float]],
    ) -> AirworthinessAssessment:
        """Perform airworthiness assessment."""
        data = AirworthinessRequest(
            uav_type=uav_type,
            weather_conditions=weather_conditions,
            route=route,
        )
        raw = self._http.post("/v1/risk/airworthiness", data.model_dump())
        return AirworthinessAssessment.model_validate(raw)

    # ------------------------------------------------------------------
    # Async methods
    # ------------------------------------------------------------------

    async def assess_async(
        self,
        path: list[dict[str, float]],
        time: str,
        uav_type: str | None = None,
    ) -> RiskAssessment:
        """Async: Perform comprehensive risk assessment along a flight path."""
        data = RiskQueryRequest(path=path, time=time, uav_type=uav_type)
        raw = await self._http.post("/v1/risk/assess", data.model_dump(exclude_none=True))
        return RiskAssessment.model_validate(raw)

    async def get_risk_map_async(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        resolution: float | None = None,
    ) -> list[RiskAssessment]:
        """Async: Get regional risk grid map."""
        params = {
            "minLon": min_lon,
            "minLat": min_lat,
            "maxLon": max_lon,
            "maxLat": max_lat,
        }
        if resolution is not None:
            params["resolution"] = resolution
        raw = await self._http.get("/v1/risk/map", params=params)
        return [RiskAssessment.model_validate(item) for item in raw]

    async def get_history_async(
        self,
        tenant_id: int | None = None,
        type: str | None = None,
        limit: int | None = None,
    ) -> list[RiskAssessment]:
        """Async: Get historical risk assessment records."""
        params: dict = {}
        if tenant_id is not None:
            params["tenantId"] = tenant_id
        if type is not None:
            params["type"] = type
        if limit is not None:
            params["limit"] = limit
        raw = await self._http.get("/v1/risk/history", params=params)
        return [RiskAssessment.model_validate(item) for item in raw]

    async def assess_airworthiness_async(
        self,
        uav_type: str,
        weather_conditions: dict[str, float],
        route: list[dict[str, float]],
    ) -> AirworthinessAssessment:
        """Async: Perform airworthiness assessment."""
        data = AirworthinessRequest(
            uav_type=uav_type,
            weather_conditions=weather_conditions,
            route=route,
        )
        raw = await self._http.post("/v1/risk/airworthiness", data.model_dump())
        return AirworthinessAssessment.model_validate(raw)
