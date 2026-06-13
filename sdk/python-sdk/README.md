# UAV Platform Python SDK

Python SDK for UAV Platform V2 -- WRF meteorology-driven UAV VRP intelligent path planning system.

## Installation

```bash
pip install uav-platform-sdk
```

Or install from source:

```bash
cd sdk/python-sdk
pip install -e .
```

## Quick Start

### Synchronous Usage

```python
from uav_platform import UavPlatformClient

client = UavPlatformClient(
    base_url="http://localhost:8080",
    api_key="your-api-key",
    api_secret="your-api-secret",
)

# Query weather at a point
weather = client.weather.query_point(
    lon=116.4,
    lat=39.9,
    altitude=100,
)
print(f"Temperature: {weather.temperature} C")
print(f"Wind: {weather.wind_speed} m/s, direction: {weather.wind_direction}")

# Submit an assimilation task
task_id = client.assimilation.submit_task(
    type="3DVAR",
    algorithm="three_dimensional_var",
    start_time="2024-01-01T00:00:00Z",
    end_time="2024-01-01T06:00:00Z",
)
print(f"Task submitted: {task_id}")

# Check task status
task = client.assimilation.get_task_status(task_id)
print(f"Task status: {task.status}")

# Path planning
planning_task = client.planning.plan_path(
    start_point={"lon": 116.4, "lat": 39.9, "altitude": 100},
    end_point={"lon": 117.0, "lat": 40.0, "altitude": 200},
    algorithm="rrt_star",
)
print(f"Planning task: {planning_task.id}, status: {planning_task.status}")

# Risk assessment
assessment = client.risk.assess(
    path=[
        {"lon": 116.4, "lat": 39.9, "altitude": 100},
        {"lon": 116.7, "lat": 39.95, "altitude": 150},
    ],
    time="2024-01-01T12:00:00Z",
)
print(f"Risk level: {assessment.risk_level}, score: {assessment.score}")

# UTM flight plan
flight_plan = client.utm.submit_flight_plan(
    uav_id="UAV-001",
    waypoints=[
        {"lon": 116.4, "lat": 39.9, "altitude": 100, "speed": 15},
        {"lon": 117.0, "lat": 40.0, "altitude": 200, "speed": 20},
    ],
    estimated_departure_time="2024-01-01T10:00:00Z",
)
print(f"Flight plan submitted: {flight_plan.id}")
```

### Asynchronous Usage

```python
import asyncio
from uav_platform import UavPlatformClient

async def main():
    async with UavPlatformClient(
        base_url="http://localhost:8080",
        api_key="your-api-key",
        api_secret="your-api-secret",
    ) as client:
        # Query weather asynchronously
        weather = await client.weather.query_point_async(
            lon=116.4,
            lat=39.9,
            altitude=100,
        )
        print(f"Temperature: {weather.temperature} C")

        # Submit assimilation task
        task_id = await client.assimilation.submit_task_async(
            type="3DVAR",
            algorithm="three_dimensional_var",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-01-01T06:00:00Z",
        )

        # Wait for completion
        while True:
            task = await client.assimilation.get_task_status_async(task_id)
            if task.status in ("COMPLETED", "FAILED"):
                break
            await asyncio.sleep(2)

        if task.status == "COMPLETED":
            result = await client.assimilation.get_task_result_async(task_id)
            print(f"Analysis time: {result.analysis_time}")

asyncio.run(main())
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `base_url` | required | API gateway base URL |
| `api_key` | required | API key for HMAC signing |
| `api_secret` | required | API secret for HMAC signing |
| `timeout` | 30 | Request timeout in seconds |
| `api_version` | "1.0" | API version header |

## API Modules

- **WeatherApi** (`client.weather`) -- Meteorological data query and multi-source fusion
- **AssimilationApi** (`client.assimilation`) -- Data assimilation task management (3DVAR/4DVAR/5DVAR/EnKF/Hybrid)
- **PlanningApi** (`client.planning`) -- Path planning and mission planning (VRPTW/DE-RRT*/DWA/MPC/A*/Dijkstra/RRT*)
- **RiskApi** (`client.risk`) -- Comprehensive risk assessment and airworthiness evaluation
- **UtmApi** (`client.utm`) -- Airspace management, flight plans, tracking, and conflict detection

## License

Apache 2.0
