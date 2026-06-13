"""
Weather API module.

Provides methods for querying meteorological data including point queries,
regional grids, wind profiles, and multi-source fusion.
"""

from __future__ import annotations

from typing import cast

from uav_platform.http import AsyncHttpClient, HttpClient
from uav_platform.models import (
    RegionQueryParams,
    WeatherGrid,
    WeatherQueryRequest,
    WindProfile,
    WindProfileQueryRequest,
)


class WeatherApi:
    """
    Weather data API client.

    Wraps all ``/v1/weather/*`` endpoints with automatic HMAC signing
    and response unwrapping. Supports both sync and async usage depending
    on whether an ``HttpClient`` or ``AsyncHttpClient`` is injected.
    """

    def __init__(self, http: HttpClient | AsyncHttpClient) -> None:
        self._http = http

    # ------------------------------------------------------------------
    # Sync methods
    # ------------------------------------------------------------------

    def query_point(
        self,
        lon: float,
        lat: float,
        altitude: float | None = None,
        source: str | None = None,
        forecast_time: str | None = None,
    ) -> WeatherGrid:
        """Query weather data at a single geographic point."""
        data = WeatherQueryRequest(
            lon=lon,
            lat=lat,
            altitude=altitude,
            source=source,
            forecast_time=forecast_time,
        )
        raw = self._http.post("/v1/weather/point", data.model_dump(exclude_none=True))
        return WeatherGrid.model_validate(raw)

    def query_region(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        altitude: float | None = None,
        source: str | None = None,
        forecast_time: str | None = None,
    ) -> list[WeatherGrid]:
        """Query weather data for a geographic region."""
        params = RegionQueryParams(
            min_lon=min_lon,
            min_lat=min_lat,
            max_lon=max_lon,
            max_lat=max_lat,
            altitude=altitude,
            source=source,
            forecast_time=forecast_time,
        )
        raw = self._http.get("/v1/weather/region", params=params.model_dump(exclude_none=True))
        return [WeatherGrid.model_validate(item) for item in cast(list, raw)]

    def query_wind_profile(
        self,
        lon: float,
        lat: float,
        max_altitude: float | None = None,
        levels: int | None = None,
        source: str | None = None,
    ) -> WindProfile:
        """Query vertical wind profile at a location."""
        data = WindProfileQueryRequest(
            lon=lon,
            lat=lat,
            max_altitude=max_altitude,
            levels=levels,
            source=source,
        )
        raw = self._http.post("/v1/weather/wind-profile", data.model_dump(exclude_none=True))
        return WindProfile.model_validate(raw)

    def query_fusion(
        self,
        lon: float,
        lat: float,
        altitude: float | None = None,
        source: str | None = None,
        forecast_time: str | None = None,
    ) -> WeatherGrid:
        """Query multi-source fused weather data."""
        data = WeatherQueryRequest(
            lon=lon,
            lat=lat,
            altitude=altitude,
            source=source,
            forecast_time=forecast_time,
        )
        raw = self._http.post("/v1/weather/fusion", data.model_dump(exclude_none=True))
        return WeatherGrid.model_validate(raw)

    # ------------------------------------------------------------------
    # Async methods
    # ------------------------------------------------------------------

    async def query_point_async(
        self,
        lon: float,
        lat: float,
        altitude: float | None = None,
        source: str | None = None,
        forecast_time: str | None = None,
    ) -> WeatherGrid:
        """Async: Query weather data at a single geographic point."""
        data = WeatherQueryRequest(
            lon=lon,
            lat=lat,
            altitude=altitude,
            source=source,
            forecast_time=forecast_time,
        )
        raw = await self._http.post("/v1/weather/point", data.model_dump(exclude_none=True))
        return WeatherGrid.model_validate(raw)

    async def query_region_async(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        altitude: float | None = None,
        source: str | None = None,
        forecast_time: str | None = None,
    ) -> list[WeatherGrid]:
        """Async: Query weather data for a geographic region."""
        params = RegionQueryParams(
            min_lon=min_lon,
            min_lat=min_lat,
            max_lon=max_lon,
            max_lat=max_lat,
            altitude=altitude,
            source=source,
            forecast_time=forecast_time,
        )
        raw = await self._http.get(
            "/v1/weather/region", params=params.model_dump(exclude_none=True)
        )
        return [WeatherGrid.model_validate(item) for item in raw]

    async def query_wind_profile_async(
        self,
        lon: float,
        lat: float,
        max_altitude: float | None = None,
        levels: int | None = None,
        source: str | None = None,
    ) -> WindProfile:
        """Async: Query vertical wind profile at a location."""
        data = WindProfileQueryRequest(
            lon=lon,
            lat=lat,
            max_altitude=max_altitude,
            levels=levels,
            source=source,
        )
        raw = await self._http.post("/v1/weather/wind-profile", data.model_dump(exclude_none=True))
        return WindProfile.model_validate(raw)

    async def query_fusion_async(
        self,
        lon: float,
        lat: float,
        altitude: float | None = None,
        source: str | None = None,
        forecast_time: str | None = None,
    ) -> WeatherGrid:
        """Async: Query multi-source fused weather data."""
        data = WeatherQueryRequest(
            lon=lon,
            lat=lat,
            altitude=altitude,
            source=source,
            forecast_time=forecast_time,
        )
        raw = await self._http.post("/v1/weather/fusion", data.model_dump(exclude_none=True))
        return WeatherGrid.model_validate(raw)
