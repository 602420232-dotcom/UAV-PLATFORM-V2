"""
Pydantic v2 data models for UAV Platform API.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# ============================================================
# Common / Shared
# ============================================================


class Result(BaseModel):
    """Unified API response envelope."""

    code: int = 0
    message: str = "ok"
    data: Any = None
    request_id: str = ""
    timestamp: int = 0


class PageResult(BaseModel):
    """Paginated result."""

    records: list[Any] = []
    total: int = 0
    size: int = 10
    current: int = 1
    pages: int = 0


# ============================================================
# Weather Models
# ============================================================

class WeatherGrid(BaseModel):
    """Single-point weather data grid."""

    lon: float
    lat: float
    altitude: float
    wind_speed: float = Field(0.0, description="Wind speed in m/s")
    wind_direction: float = Field(0.0, description="Wind direction in degrees")
    temperature: float = Field(0.0, description="Temperature in Celsius")
    humidity: float = Field(0.0, description="Relative humidity percentage")
    pressure: float = Field(0.0, description="Atmospheric pressure in hPa")
    visibility: float = Field(0.0, description="Visibility in meters")
    weather_code: int = Field(0, description="WMO weather code")
    source: str = Field("", description="Data source (wrf, fengyun, tianzi, fenglei)")
    forecast_time: str = ""


class WindLevel(BaseModel):
    """Wind data at a specific altitude level."""

    altitude: float
    wind_speed: float
    wind_direction: float
    temperature: float


class WindProfile(BaseModel):
    """Vertical wind profile at a location."""

    lon: float
    lat: float
    levels: list[WindLevel] = []


class WeatherQueryRequest(BaseModel):
    """Request for point weather query."""

    lon: float
    lat: float
    altitude: float | None = None
    source: str | None = None
    forecast_time: str | None = None


class WindProfileQueryRequest(BaseModel):
    """Request for wind profile query."""

    lon: float
    lat: float
    max_altitude: float | None = None
    levels: int | None = None
    source: str | None = None


class RegionQueryParams(BaseModel):
    """Parameters for regional weather grid query."""

    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float
    altitude: float | None = None
    source: str | None = None
    forecast_time: str | None = None


# ============================================================
# Assimilation Models
# ============================================================

class GridInfo(BaseModel):
    """Grid metadata for assimilation results."""

    min_lon: float
    min_lat: float
    max_lon: float
    max_lat: float
    resolution: float
    levels: int


class AssimilationTask(BaseModel):
    """Data assimilation task entity."""

    id: int
    type: str
    status: str
    algorithm: str
    created_at: str
    completed_at: str | None = None
    error_message: str | None = None


class AssimilationResult(BaseModel):
    """Data assimilation result."""

    task_id: int
    analysis_time: str
    variables: list[str] = []
    grid_info: GridInfo | None = None
    data_url: str = ""


class SubmitTaskRequest(BaseModel):
    """Request to submit an assimilation task."""

    type: str = Field(
        ...,
        description="Assimilation type: 3DVAR, 4DVAR, 5DVAR, EnKF, Hybrid, EnhancedBayesian",
    )
    algorithm: str = Field(..., description="Algorithm identifier")
    start_time: str = Field(..., description="ISO 8601 start time")
    end_time: str = Field(..., description="ISO 8601 end time")
    region: dict[str, float] | None = Field(
        None, description="Bounding box: minLon, minLat, maxLon, maxLat"
    )
    observation_sources: list[str] | None = None


class TaskQueryRequest(BaseModel):
    """Request for querying assimilation tasks."""

    status: str | None = None
    type: str | None = None
    page: int = 1
    size: int = 10


# ============================================================
# Planning Models
# ============================================================

class Waypoint(BaseModel):
    """A single waypoint in a flight path."""

    lon: float
    lat: float
    altitude: float
    speed: float = 0.0
    timestamp: str = ""


class PathResult(BaseModel):
    """Path planning result."""

    task_id: int
    waypoints: list[Waypoint] = []
    total_distance: float = 0.0
    estimated_time: float = 0.0
    fuel_consumption: float = 0.0


class MissionSegment(BaseModel):
    """A segment of a mission plan."""

    start_point: Waypoint
    end_point: Waypoint
    altitude: float
    speed: float
    distance: float


class MissionPlan(BaseModel):
    """Mission planning result."""

    task_id: int
    segments: list[MissionSegment] = []
    total_distance: float = 0.0
    estimated_duration: float = 0.0


class PlanningTask(BaseModel):
    """Planning task entity."""

    id: int
    type: str
    status: str
    created_at: str
    completed_at: str | None = None
    error_message: str | None = None


class PlanPathRequest(BaseModel):
    """Request for path planning."""

    start_point: dict[str, float]
    end_point: dict[str, float]
    waypoints: list[dict[str, float]] | None = None
    algorithm: str | None = None


class PlanMissionRequest(BaseModel):
    """Request for mission planning."""

    area: dict[str, float]
    altitude: float
    overlap: float = 0.0
    algorithm: str | None = None


# ============================================================
# Risk Models
# ============================================================

class RiskFactor(BaseModel):
    """Individual risk factor."""

    name: str
    value: float
    weight: float
    level: str


class RiskAssessment(BaseModel):
    """Comprehensive risk assessment result."""

    id: int = 0
    type: str = ""
    risk_level: str = ""
    score: float = 0.0
    factors: list[RiskFactor] = []
    lon: float = 0.0
    lat: float = 0.0
    altitude: float = 0.0
    assessed_at: str = ""
    tenant_id: int | None = None


class AirworthinessFactor(BaseModel):
    """Individual airworthiness evaluation factor."""

    name: str
    score: float
    threshold: float
    passed: bool


class AirworthinessAssessment(BaseModel):
    """Airworthiness assessment result."""

    id: int = 0
    uav_type: str = ""
    overall_score: float = 0.0
    decision: str = ""
    factors: list[AirworthinessFactor] = []
    assessed_at: str = ""


class RiskQueryRequest(BaseModel):
    """Request for risk assessment along a path."""

    path: list[dict[str, float]]
    time: str
    uav_type: str | None = None


class AirworthinessRequest(BaseModel):
    """Request for airworthiness assessment."""

    uav_type: str
    weather_conditions: dict[str, float]
    route: list[dict[str, float]]


# ============================================================
# UTM Models
# ============================================================

class Airspace(BaseModel):
    """Airspace entity."""

    id: int = 0
    name: str = ""
    type: str = ""
    status: str = ""
    min_altitude: float = 0.0
    max_altitude: float = 0.0
    geometry: Any = None
    restrictions: list[str] = []
    created_at: str = ""


class FlightWaypoint(BaseModel):
    """Waypoint in a flight plan."""

    lon: float
    lat: float
    altitude: float
    speed: float = 0.0
    timestamp: str = ""


class FlightPlan(BaseModel):
    """UTM flight plan entity."""

    id: int = 0
    uav_id: str = ""
    status: str = ""
    waypoints: list[FlightWaypoint] = []
    submitted_at: str = ""
    approved_at: str | None = None


class UavPosition(BaseModel):
    """Real-time UAV position report."""

    uav_id: str
    lon: float
    lat: float
    altitude: float
    heading: float = 0.0
    speed: float = 0.0
    timestamp: str = ""


class ConflictAlert(BaseModel):
    """Conflict alert between UAVs."""

    id: int = 0
    type: str = ""
    severity: str = ""
    status: str = ""
    uav_id1: str = ""
    uav_id2: str = ""
    location: dict[str, float] = {}
    time_to_conflict: float = 0.0
    created_at: str = ""


class SubmitFlightPlanRequest(BaseModel):
    """Request to submit a flight plan."""

    uav_id: str
    waypoints: list[dict[str, float]]
    estimated_departure_time: str


class ConflictCheckRequest(BaseModel):
    """Request for conflict detection."""

    planned_path: list[dict[str, float | str]]
    time_window: dict[str, str]


# ============================================================
# Observation Models
# ============================================================

class ObservationTask(BaseModel):
    """Observation task entity."""

    id: int = 0
    type: str = ""
    status: str = ""
    priority: int = 0
    region: dict[str, float] = {}
    target_variables: list[str] = []
    platform: str = ""
    created_at: str = ""
    completed_at: str | None = None


class ObservationDecision(BaseModel):
    """Observation decision recommendation."""

    id: int = 0
    task_id: int = 0
    decision: str = ""
    reason: str = ""
    suggested_platforms: list[str] = []
    suggested_time: str = ""
    coverage_score: float = 0.0
    created_at: str = ""


class CreateObservationRequest(BaseModel):
    """Request to create an observation task."""

    type: str
    priority: int = 0
    region: dict[str, float]
    target_variables: list[str] = []
    platform: str | None = None
    time_window: dict[str, str] | None = None


class ObservationDecisionRequest(BaseModel):
    """Request for observation decision."""

    region: dict[str, float]
    target_variables: list[str] = []
    time_window: dict[str, str] | None = None
