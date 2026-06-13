"""
SDK entry point -- UavPlatformClient.

Provides both synchronous and asynchronous access to all UAV Platform API modules.
"""

from __future__ import annotations

from typing import Self

from uav_platform.api.assimilation import AssimilationApi
from uav_platform.api.planning import PlanningApi
from uav_platform.api.risk import RiskApi
from uav_platform.api.utm import UtmApi
from uav_platform.api.weather import WeatherApi
from uav_platform.config import UavPlatformConfig
from uav_platform.http import AsyncHttpClient, HttpClient


class UavPlatformClient:
    """
    Main SDK client providing synchronous access to all UAV Platform API modules.

    Usage::

        client = UavPlatformClient(
            base_url="http://localhost:8080",
            api_key="your-key",
            api_secret="your-secret",
        )
        weather = client.weather.query_point(lon=116.4, lat=39.9)
        client.close()

    Or use as a context manager::

        with UavPlatformClient(...) as client:
            weather = client.weather.query_point(lon=116.4, lat=39.9)
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        api_secret: str,
        timeout: int = 30,
        api_version: str = "1.0",
    ) -> None:
        config = UavPlatformConfig(
            base_url=base_url,
            api_key=api_key,
            api_secret=api_secret,
            timeout=timeout,
            api_version=api_version,
        )
        self._config = config
        self._http = HttpClient(config)
        self._weather = WeatherApi(self._http)
        self._assimilation = AssimilationApi(self._http)
        self._planning = PlanningApi(self._http)
        self._risk = RiskApi(self._http)
        self._utm = UtmApi(self._http)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def weather(self) -> WeatherApi:
        """Weather data query API (sync)."""
        return self._weather

    @property
    def assimilation(self) -> AssimilationApi:
        """Data assimilation API (sync)."""
        return self._assimilation

    @property
    def planning(self) -> PlanningApi:
        """Path and mission planning API (sync)."""
        return self._planning

    @property
    def risk(self) -> RiskApi:
        """Risk and airworthiness assessment API (sync)."""
        return self._risk

    @property
    def utm(self) -> UtmApi:
        """UTM (airspace, flight plans, tracking) API (sync)."""
        return self._utm

    @property
    def config(self) -> UavPlatformConfig:
        """Read-only access to the current configuration."""
        return self._config

    # ------------------------------------------------------------------
    # Sync context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client and release resources."""
        self._http.close()


class AsyncUavPlatformClient:
    """
    Asynchronous SDK client providing async access to all UAV Platform API modules.

    Usage::

        async with AsyncUavPlatformClient(...) as client:
            weather = await client.weather.query_point_async(lon=116.4, lat=39.9)
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        api_secret: str,
        timeout: int = 30,
        api_version: str = "1.0",
    ) -> None:
        config = UavPlatformConfig(
            base_url=base_url,
            api_key=api_key,
            api_secret=api_secret,
            timeout=timeout,
            api_version=api_version,
        )
        self._config = config
        self._http = AsyncHttpClient(config)
        self._weather = WeatherApi(self._http)
        self._assimilation = AssimilationApi(self._http)
        self._planning = PlanningApi(self._http)
        self._risk = RiskApi(self._http)
        self._utm = UtmApi(self._http)

    @property
    def weather(self) -> WeatherApi:
        """Weather data query API (async)."""
        return self._weather

    @property
    def assimilation(self) -> AssimilationApi:
        """Data assimilation API (async)."""
        return self._assimilation

    @property
    def planning(self) -> PlanningApi:
        """Path and mission planning API (async)."""
        return self._planning

    @property
    def risk(self) -> RiskApi:
        """Risk and airworthiness assessment API (async)."""
        return self._risk

    @property
    def utm(self) -> UtmApi:
        """UTM (airspace, flight plans, tracking) API (async)."""
        return self._utm

    @property
    def config(self) -> UavPlatformConfig:
        return self._config

    # ------------------------------------------------------------------
    # Async context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying async HTTP client."""
        await self._http.close()
