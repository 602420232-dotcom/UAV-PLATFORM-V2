#!/usr/bin/env python3
"""
UAV Platform V2 端到端集成测试

测试流程: WRF -> 气象融合 -> 同化 -> 风险评估 -> 路径规划 -> UTM
测试模式: mock=true（使用模拟数据，不需要真实基础设施）

用法:
    python scripts/e2e-test.py              # 默认 mock 模式
    python scripts/e2e-test.py --mock       # 显式 mock 模式
    python scripts/e2e-test.py --url http://localhost:8080  # 指定服务地址
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
import time
import urllib.parse
from typing import Any

try:
    import requests
except ImportError:
    print("ERROR: 请先安装 requests 库: pip install requests")
    sys.exit(1)


# ============================================================
# Configuration
# ============================================================

# Service endpoints (direct connection, bypassing gateway for E2E testing)
SERVICE_URLS = {
    "platform": "http://localhost:18081",
    "weather": "http://localhost:18082",
    "assimilation": "http://localhost:18083",
    "risk": "http://localhost:18084",
    "observation": "http://localhost:18085",
    "planning": "http://localhost:18086",
    "utm": "http://localhost:18087",
}
DEFAULT_BASE_URL = "http://localhost:18080"  # gateway (optional)
DEFAULT_API_KEY = "test-key"
DEFAULT_API_SECRET = "test-secret"
API_VERSION = "1.0"
API_PREFIX = "/api"


# ============================================================
# HMAC-SHA256 Signing
# ============================================================

def sign_request(
    method: str,
    path: str,
    api_key: str,
    api_secret: str,
    body: str = "",
) -> dict[str, str]:
    """
    Generate HMAC-SHA256 signature headers.

    Signature string format:
        METHOD\\nPATH\\nTIMESTAMP\\nAPI_KEY\\nBODY
    """
    timestamp = str(int(time.time()))
    string_to_sign = f"{method.upper()}\n{path}\n{timestamp}\n{api_key}\n{body}"
    signature = hmac.new(
        api_secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return {
        "X-API-Key": api_key,
        "X-Signature": signature,
        "X-Timestamp": timestamp,
        "X-API-Version": API_VERSION,
    }


# ============================================================
# Mock Data
# ============================================================

MOCK_WEATHER_POINT = {
    "code": 0,
    "message": "ok",
    "data": {
        "lon": 116.4,
        "lat": 39.9,
        "altitude": 100.0,
        "windSpeed": 5.2,
        "windDirection": 225.0,
        "temperature": 18.5,
        "humidity": 65.0,
        "pressure": 1013.2,
        "visibility": 10000.0,
        "weatherCode": 0,
        "source": "wrf",
        "forecastTime": "2024-01-15T12:00:00Z",
    },
    "requestId": "mock-req-001",
    "timestamp": int(time.time()),
}

MOCK_WEATHER_REGION = {
    "code": 0,
    "message": "ok",
    "data": [
        {
            "lon": 116.4,
            "lat": 39.9,
            "altitude": 100.0,
            "windSpeed": 5.2,
            "windDirection": 225.0,
            "temperature": 18.5,
            "humidity": 65.0,
            "pressure": 1013.2,
            "visibility": 10000.0,
            "weatherCode": 0,
            "source": "wrf",
            "forecastTime": "2024-01-15T12:00:00Z",
        },
        {
            "lon": 116.5,
            "lat": 39.9,
            "altitude": 100.0,
            "windSpeed": 4.8,
            "windDirection": 230.0,
            "temperature": 18.3,
            "humidity": 66.0,
            "pressure": 1013.1,
            "visibility": 9500.0,
            "weatherCode": 0,
            "source": "wrf",
            "forecastTime": "2024-01-15T12:00:00Z",
        },
    ],
    "requestId": "mock-req-002",
    "timestamp": int(time.time()),
}

MOCK_ASSIMILATION_TASK = {
    "code": 0,
    "message": "ok",
    "data": 1001,
    "requestId": "mock-req-003",
    "timestamp": int(time.time()),
}

MOCK_ASSIMILATION_STATUS = {
    "code": 0,
    "message": "ok",
    "data": {
        "id": 1001,
        "type": "3DVAR",
        "status": "COMPLETED",
        "algorithm": "three_dimensional_var",
        "createdAt": "2024-01-15T10:00:00Z",
        "completedAt": "2024-01-15T10:05:30Z",
        "errorMessage": None,
    },
    "requestId": "mock-req-004",
    "timestamp": int(time.time()),
}

MOCK_ASSIMILATION_RESULT = {
    "code": 0,
    "message": "ok",
    "data": {
        "taskId": 1001,
        "analysisTime": "2024-01-15T10:05:00Z",
        "variables": ["temperature", "humidity", "wind_u", "wind_v", "pressure"],
        "gridInfo": {
            "minLon": 115.0,
            "minLat": 39.0,
            "maxLon": 118.0,
            "maxLat": 41.0,
            "resolution": 0.1,
            "levels": 30,
        },
        "dataUrl": "s3://uav-platform/assimilation/1001/result.nc",
    },
    "requestId": "mock-req-005",
    "timestamp": int(time.time()),
}

MOCK_RISK_ASSESSMENT = {
    "code": 0,
    "message": "ok",
    "data": {
        "id": 2001,
        "type": "COMPOSITE",
        "riskLevel": "LOW",
        "score": 25.3,
        "factors": [
            {"name": "weather_risk", "value": 30.0, "weight": 0.4, "level": "LOW"},
            {"name": "terrain_risk", "value": 15.0, "weight": 0.3, "level": "LOW"},
            {"name": "airspace_risk", "value": 35.0, "weight": 0.3, "level": "MEDIUM"},
        ],
        "lon": 116.4,
        "lat": 39.9,
        "altitude": 100.0,
        "assessedAt": "2024-01-15T12:00:00Z",
    },
    "requestId": "mock-req-006",
    "timestamp": int(time.time()),
}

MOCK_AIRWORTHINESS = {
    "code": 0,
    "message": "ok",
    "data": {
        "id": 3001,
        "uavType": "multirotor",
        "overallScore": 85.5,
        "decision": "APPROVED",
        "factors": [
            {"name": "wind_speed", "score": 90.0, "threshold": 15.0, "passed": True},
            {"name": "visibility", "score": 95.0, "threshold": 3000.0, "passed": True},
            {"name": "temperature", "score": 80.0, "threshold": -10.0, "passed": True},
            {"name": "precipitation", "score": 70.0, "threshold": 5.0, "passed": True},
        ],
        "assessedAt": "2024-01-15T12:00:00Z",
    },
    "requestId": "mock-req-007",
    "timestamp": int(time.time()),
}

MOCK_OBSERVATION_DECISION = {
    "code": 0,
    "message": "ok",
    "data": {
        "id": 4001,
        "taskId": 0,
        "decision": "OBSERVE",
        "reason": "当前观测覆盖率不足，建议补充观测数据以提高同化精度",
        "suggestedPlatforms": ["UAV-001", "UAV-002", "surface_station"],
        "suggestedTime": "2024-01-15T13:00:00Z",
        "coverageScore": 0.62,
        "createdAt": "2024-01-15T12:00:00Z",
    },
    "requestId": "mock-req-008",
    "timestamp": int(time.time()),
}

MOCK_PLANNING_TASK = {
    "code": 0,
    "message": "ok",
    "data": {
        "id": 5001,
        "type": "PATH",
        "status": "COMPLETED",
        "createdAt": "2024-01-15T12:00:00Z",
        "completedAt": "2024-01-15T12:00:05Z",
        "errorMessage": None,
    },
    "requestId": "mock-req-009",
    "timestamp": int(time.time()),
}

MOCK_PATH_RESULT = {
    "code": 0,
    "message": "ok",
    "data": {
        "taskId": 5001,
        "waypoints": [
            {"lon": 116.4, "lat": 39.9, "altitude": 100.0, "speed": 15.0, "timestamp": "2024-01-15T12:00:00Z"},
            {"lon": 116.5, "lat": 39.92, "altitude": 120.0, "speed": 18.0, "timestamp": "2024-01-15T12:03:00Z"},
            {"lon": 116.6, "lat": 39.95, "altitude": 150.0, "speed": 20.0, "timestamp": "2024-01-15T12:06:00Z"},
            {"lon": 116.7, "lat": 39.95, "altitude": 180.0, "speed": 20.0, "timestamp": "2024-01-15T12:09:00Z"},
            {"lon": 117.0, "lat": 40.0, "altitude": 200.0, "speed": 15.0, "timestamp": "2024-01-15T12:15:00Z"},
        ],
        "totalDistance": 35.2,
        "estimatedTime": 900.0,
        "fuelConsumption": 2.8,
    },
    "requestId": "mock-req-010",
    "timestamp": int(time.time()),
}

MOCK_FLIGHT_PLAN = {
    "code": 0,
    "message": "ok",
    "data": {
        "id": 6001,
        "uavId": "UAV-TEST-001",
        "status": "SUBMITTED",
        "waypoints": [
            {"lon": 116.4, "lat": 39.9, "altitude": 100.0, "speed": 15.0, "timestamp": "2024-01-15T12:00:00Z"},
            {"lon": 117.0, "lat": 40.0, "altitude": 200.0, "speed": 15.0, "timestamp": "2024-01-15T12:15:00Z"},
        ],
        "submittedAt": "2024-01-15T11:50:00Z",
        "approvedAt": None,
    },
    "requestId": "mock-req-011",
    "timestamp": int(time.time()),
}

MOCK_FLIGHT_PLAN_APPROVED = {
    "code": 0,
    "message": "ok",
    "data": {
        "id": 6001,
        "uavId": "UAV-TEST-001",
        "status": "APPROVED",
        "waypoints": [
            {"lon": 116.4, "lat": 39.9, "altitude": 100.0, "speed": 15.0, "timestamp": "2024-01-15T12:00:00Z"},
            {"lon": 117.0, "lat": 40.0, "altitude": 200.0, "speed": 15.0, "timestamp": "2024-01-15T12:15:00Z"},
        ],
        "submittedAt": "2024-01-15T11:50:00Z",
        "approvedAt": "2024-01-15T11:55:00Z",
    },
    "requestId": "mock-req-012",
    "timestamp": int(time.time()),
}

MOCK_FLIGHT_PLAN_STARTED = {
    "code": 0,
    "message": "ok",
    "data": {
        "id": 6001,
        "uavId": "UAV-TEST-001",
        "status": "ACTIVE",
        "waypoints": [
            {"lon": 116.4, "lat": 39.9, "altitude": 100.0, "speed": 15.0, "timestamp": "2024-01-15T12:00:00Z"},
            {"lon": 117.0, "lat": 40.0, "altitude": 200.0, "speed": 15.0, "timestamp": "2024-01-15T12:15:00Z"},
        ],
        "submittedAt": "2024-01-15T11:50:00Z",
        "approvedAt": "2024-01-15T11:55:00Z",
    },
    "requestId": "mock-req-013",
    "timestamp": int(time.time()),
}

MOCK_POSITION_REPORT = {
    "code": 0,
    "message": "ok",
    "data": None,
    "requestId": "mock-req-014",
    "timestamp": int(time.time()),
}

MOCK_CONFLICT_CHECK = {
    "code": 0,
    "message": "ok",
    "data": [],
    "requestId": "mock-req-015",
    "timestamp": int(time.time()),
}

MOCK_HEALTH = {
    "code": 0,
    "message": "ok",
    "data": {"status": "UP", "services": ["weather", "assimilation", "planning", "risk", "utm", "observation"]},
    "requestId": "mock-req-health",
    "timestamp": int(time.time()),
}


# ============================================================
# Test Framework
# ============================================================

class TestResult:
    """Tracks individual test results."""

    def __init__(self) -> None:
        self.passed: int = 0
        self.failed: int = 0
        self.skipped: int = 0
        self.details: list[dict[str, Any]] = []

    def record(self, name: str, status: str, message: str = "", duration: float = 0.0) -> None:
        entry = {
            "name": name,
            "status": status,
            "message": message,
            "duration": round(duration, 3),
        }
        self.details.append(entry)
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        else:
            self.skipped += 1

    def report(self) -> str:
        lines = []
        lines.append("")
        lines.append("=" * 60)
        lines.append("  测试报告")
        lines.append("=" * 60)
        lines.append("")

        for d in self.details:
            status_tag = {
                "PASS": "  PASS  ",
                "FAIL": "  FAIL  ",
                "SKIP": "  SKIP  ",
            }.get(d["status"], "  ???  ")
            lines.append(f"  [{status_tag}] {d['name']}")
            if d["message"]:
                lines.append(f"            {d['message']}")
            if d["duration"] > 0:
                lines.append(f"            ({d['duration']}s)")

        total = self.passed + self.failed + self.skipped
        lines.append("")
        lines.append("-" * 60)
        lines.append(f"  总计: {total}  |  通过: {self.passed}  |  失败: {self.failed}  |  跳过: {self.skipped}")
        lines.append("-" * 60)
        lines.append("")

        if self.failed > 0:
            lines.append("  结果: 有测试失败")
        elif self.skipped > 0:
            lines.append("  结果: 全部通过（部分跳过）")
        else:
            lines.append("  结果: 全部通过")

        lines.append("")
        return "\n".join(lines)


# ============================================================
# Mock HTTP Client
# ============================================================

class MockResponse:
    """Simulates an HTTP response for mock mode."""

    def __init__(self, json_data: dict, status_code: int = 200) -> None:
        self._json_data = json_data
        self.status_code = status_code

    def json(self) -> dict:
        return self._json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"Mock HTTP {self.status_code}")


class MockHttpClient:
    """
    Mock HTTP client that returns predefined responses based on URL path.

    In mock mode, no real HTTP requests are made. Instead, predefined
    mock responses are returned to simulate the API behavior.
    """

    def __init__(self) -> None:
        self._call_log: list[dict[str, Any]] = []

    def _match(self, path: str, method: str) -> dict | None:
        """Match a request path and method to a mock response."""
        path_lower = path.lower()

        # Health check
        if path_lower == "/api/v1/health" and method == "GET":
            return MOCK_HEALTH

        # Weather - point query
        if path_lower == "/api/v1/weather/point" and method == "POST":
            return MOCK_WEATHER_POINT

        # Weather - region query
        if path_lower == "/api/v1/weather/region" and method == "GET":
            return MOCK_WEATHER_REGION

        # Weather - wind profile
        if path_lower == "/api/v1/weather/wind-profile" and method == "POST":
            return MOCK_WEATHER_POINT  # reuse for simplicity

        # Weather - fusion
        if path_lower == "/api/v1/weather/fusion" and method == "POST":
            return MOCK_WEATHER_POINT

        # Assimilation - submit task
        if path_lower == "/api/v1/assimilation/tasks" and method == "POST":
            return MOCK_ASSIMILATION_TASK

        # Assimilation - task status (match /api/v1/assimilation/tasks/{id})
        if "/api/v1/assimilation/tasks/" in path_lower and method == "GET" and "/result" not in path_lower:
            return MOCK_ASSIMILATION_STATUS

        # Assimilation - task result
        if "/api/v1/assimilation/tasks/" in path_lower and "/result" in path_lower and method == "GET":
            return MOCK_ASSIMILATION_RESULT

        # Assimilation - cancel
        if "/api/v1/assimilation/tasks/" in path_lower and "/cancel" in path_lower and method == "POST":
            return {"code": 0, "message": "ok", "data": None, "requestId": "mock-cancel", "timestamp": int(time.time())}

        # Risk - assess
        if path_lower == "/api/v1/risk/assess" and method == "POST":
            return MOCK_RISK_ASSESSMENT

        # Risk - airworthiness
        if path_lower == "/api/v1/risk/airworthiness" and method == "POST":
            return MOCK_AIRWORTHINESS

        # Risk - map
        if path_lower == "/api/v1/risk/map" and method == "GET":
            return {"code": 0, "message": "ok", "data": [MOCK_RISK_ASSESSMENT["data"]], "requestId": "mock-map", "timestamp": int(time.time())}

        # Risk - history
        if path_lower == "/api/v1/risk/history" and method == "GET":
            return {"code": 0, "message": "ok", "data": [MOCK_RISK_ASSESSMENT["data"]], "requestId": "mock-history", "timestamp": int(time.time())}

        # Observation - decision
        if path_lower == "/api/v1/observation/decisions" and method == "POST":
            return MOCK_OBSERVATION_DECISION

        # Observation - tasks
        if path_lower == "/api/v1/observation/tasks" and method == "POST":
            return {
                "code": 0, "message": "ok",
                "data": {
                    "id": 4002, "type": "adaptive", "status": "PENDING", "priority": 5,
                    "region": {"minLon": 116.0, "minLat": 39.5, "maxLon": 117.0, "maxLat": 40.5},
                    "targetVariables": ["temperature", "wind_u", "wind_v"],
                    "platform": "UAV-001", "createdAt": "2024-01-15T12:00:00Z", "completedAt": None,
                },
                "requestId": "mock-obs-task", "timestamp": int(time.time()),
            }

        # Planning - path
        if path_lower == "/api/v1/planning/path" and method == "POST":
            return MOCK_PLANNING_TASK

        # Planning - mission
        if path_lower == "/api/v1/planning/mission" and method == "POST":
            return MOCK_PLANNING_TASK

        # Planning - task status
        if "/api/v1/planning/tasks/" in path_lower and "/result" not in path_lower and "/mission" not in path_lower and "/cancel" not in path_lower and method == "GET":
            return MOCK_PLANNING_TASK

        # Planning - path result
        if "/api/v1/planning/tasks/" in path_lower and "/result" in path_lower and method == "GET":
            return MOCK_PATH_RESULT

        # Planning - cancel
        if "/api/v1/planning/tasks/" in path_lower and "/cancel" in path_lower and method == "POST":
            return {"code": 0, "message": "ok", "data": None, "requestId": "mock-plan-cancel", "timestamp": int(time.time())}

        # UTM - flight plans submit
        if path_lower == "/api/v1/flight-plans" and method == "POST":
            return MOCK_FLIGHT_PLAN

        # UTM - flight plans list
        if path_lower == "/api/v1/flight-plans" and method == "GET":
            return {"code": 0, "message": "ok", "data": [MOCK_FLIGHT_PLAN["data"]], "requestId": "mock-fp-list", "timestamp": int(time.time())}

        # UTM - approve flight plan
        if "/api/v1/flight-plans/" in path_lower and "/approve" in path_lower and method == "POST":
            return MOCK_FLIGHT_PLAN_APPROVED

        # UTM - start flight plan
        if "/api/v1/flight-plans/" in path_lower and "/start" in path_lower and method == "POST":
            return MOCK_FLIGHT_PLAN_STARTED

        # UTM - position report
        if path_lower == "/api/v1/tracking/positions" and method == "POST":
            return MOCK_POSITION_REPORT

        # UTM - conflict check
        if path_lower == "/api/v1/tracking/conflicts/check" and method == "POST":
            return MOCK_CONFLICT_CHECK

        # UTM - conflict alerts list
        if path_lower == "/api/v1/conflict-alerts" and method == "GET":
            return {"code": 0, "message": "ok", "data": [], "requestId": "mock-alerts", "timestamp": int(time.time())}

        # UTM - airspaces
        if path_lower == "/api/v1/airspaces" and method == "GET":
            return {
                "code": 0, "message": "ok",
                "data": [
                    {
                        "id": 1, "name": "Test Airspace", "type": "restricted",
                        "status": "active", "minAltitude": 0, "maxAltitude": 300,
                        "geometry": None, "restrictions": ["no-fly"],
                        "createdAt": "2024-01-01T00:00:00Z",
                    }
                ],
                "requestId": "mock-asp", "timestamp": int(time.time()),
            }

        # UTM - airspace check
        if path_lower == "/api/v1/airspaces/check" and method == "GET":
            return {"code": 0, "message": "ok", "data": False, "requestId": "mock-asp-check", "timestamp": int(time.time())}

        return None

    def request(self, method: str, url: str, json_data: dict | None = None, params: dict | None = None) -> MockResponse:
        """Perform a mock HTTP request."""
        parsed = urllib.parse.urlparse(url)
        path = parsed.path

        self._call_log.append({
            "method": method,
            "url": url,
            "path": path,
            "json": json_data,
            "params": params,
            "timestamp": time.time(),
        })

        mock_data = self._match(path, method)
        if mock_data is not None:
            return MockResponse(mock_data)

        return MockResponse(
            {"code": 404, "message": f"No mock for {method} {path}", "data": None, "requestId": "", "timestamp": int(time.time())},
            status_code=404,
        )


# ============================================================
# API Client (works with both real and mock)
# ============================================================

class E2EClient:
    """
    End-to-end test client.

    Supports both real HTTP requests (via requests library) and mock mode.
    """

    def __init__(self, base_url: str, api_key: str, api_secret: str, mock: bool = True) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.api_secret = api_secret
        self.mock = mock
        self._mock_client = MockHttpClient() if mock else None

    def _full_url(self, path: str) -> str:
        return f"{self.base_url}{API_PREFIX}{path}"

    def _headers(self, method: str, path: str, body: str = "") -> dict[str, str]:
        return sign_request(method, f"{API_PREFIX}{path}", self.api_key, self.api_secret, body)

    def _unwrap(self, resp: Any) -> Any:
        """Unwrap Result<T> envelope."""
        data = resp.json()
        code = data.get("code", -1)
        if code not in (0, 200):
            raise RuntimeError(f"API error: code={code}, message={data.get('message', 'unknown')}")
        return data.get("data")

    def get(self, path: str, params: dict | None = None) -> Any:
        if self.mock:
            resp = self._mock_client.request("GET", self._full_url(path), params=params)
        else:
            headers = self._headers("GET", path)
            resp = requests.get(self._full_url(path), headers=headers, params=params, timeout=30)
            resp.raise_for_status()
        return self._unwrap(resp)

    def post(self, path: str, data: dict | None = None) -> Any:
        body = json.dumps(data, ensure_ascii=False) if data else ""
        if self.mock:
            resp = self._mock_client.request("POST", self._full_url(path), json_data=data)
        else:
            headers = self._headers("POST", path, body)
            resp = requests.post(self._full_url(path), headers=headers, data=body, timeout=30)
            resp.raise_for_status()
        return self._unwrap(resp)


# ============================================================
# Test Functions
# ============================================================

def test_health_check(client: E2EClient, results: TestResult) -> None:
    """测试各服务健康状态"""
    name = "健康检查 (Health Check)"
    start = time.time()
    try:
        data = client.get("/v1/health")
        status = data.get("status", "UNKNOWN") if isinstance(data, dict) else "UNKNOWN"
        services = data.get("services", []) if isinstance(data, dict) else []
        duration = time.time() - start
        if status == "UP":
            results.record(name, "PASS", f"服务状态: UP, 服务列表: {services}", duration)
        else:
            results.record(name, "FAIL", f"服务状态异常: {status}", duration)
    except Exception as e:
        duration = time.time() - start
        results.record(name, "FAIL", str(e), duration)


def test_weather_query(client: E2EClient, results: TestResult) -> None:
    """测试气象数据查询"""
    name = "气象数据查询 (Weather Query)"
    start = time.time()
    try:
        # 单点查询
        data = client.post("/v1/weather/point", {
            "lon": 116.4,
            "lat": 39.9,
            "altitude": 100.0,
        })
        assert data["lon"] == 116.4, f"lon mismatch: {data['lon']}"
        assert "windSpeed" in data, "missing windSpeed"
        assert "temperature" in data, "missing temperature"

        # 区域查询
        region_data = client.get("/v1/weather/region", params={
            "minLon": 116.4, "minLat": 39.9,
            "maxLon": 116.5, "maxLat": 40.0,
        })
        assert isinstance(region_data, list), "region data should be a list"
        assert len(region_data) > 0, "region data should not be empty"

        duration = time.time() - start
        results.record(name, "PASS",
                       f"单点: {data['temperature']}C, {data['windSpeed']}m/s; 区域: {len(region_data)} 格点",
                       duration)
    except Exception as e:
        duration = time.time() - start
        results.record(name, "FAIL", str(e), duration)


def test_assimilation_task(client: E2EClient, results: TestResult) -> None:
    """测试数据同化任务提交和结果查询"""
    name = "数据同化任务 (Assimilation Task)"
    start = time.time()
    try:
        # 提交任务
        task_id = client.post("/v1/assimilation/tasks", {
            "type": "3DVAR",
            "algorithm": "three_dimensional_var",
            "startTime": "2024-01-15T00:00:00Z",
            "endTime": "2024-01-15T06:00:00Z",
            "region": {"minLon": 115.0, "minLat": 39.0, "maxLon": 118.0, "maxLat": 41.0},
            "observationSources": ["wrf", "surface_station"],
        })
        assert isinstance(task_id, (int, float)), f"task_id should be int, got {type(task_id)}"
        task_id = int(task_id)

        # 查询任务状态
        task = client.get(f"/v1/assimilation/tasks/{task_id}")
        assert task["id"] == task_id, f"task id mismatch"
        assert task["status"] in ("PENDING", "RUNNING", "COMPLETED", "FAILED"), f"unexpected status: {task['status']}"

        # 查询任务结果
        result = client.get(f"/v1/assimilation/tasks/{task_id}/result")
        assert result["taskId"] == task_id, f"result taskId mismatch"
        assert len(result["variables"]) > 0, "no variables in result"
        assert result["gridInfo"] is not None, "no gridInfo in result"

        duration = time.time() - start
        results.record(name, "PASS",
                       f"任务ID={task_id}, 状态={task['status']}, 变量数={len(result['variables'])}, "
                       f"分辨率={result['gridInfo']['resolution']}",
                       duration)
    except Exception as e:
        duration = time.time() - start
        results.record(name, "FAIL", str(e), duration)


def test_risk_assessment(client: E2EClient, results: TestResult) -> None:
    """测试风险评估"""
    name = "风险评估 (Risk Assessment)"
    start = time.time()
    try:
        assessment = client.post("/v1/risk/assess", {
            "path": [
                {"lon": 116.4, "lat": 39.9, "altitude": 100},
                {"lon": 116.7, "lat": 39.95, "altitude": 150},
                {"lon": 117.0, "lat": 40.0, "altitude": 200},
            ],
            "time": "2024-01-15T12:00:00Z",
            "uavType": "multirotor",
        })
        assert "riskLevel" in assessment, "missing riskLevel"
        assert "score" in assessment, "missing score"
        assert len(assessment["factors"]) > 0, "no risk factors"

        duration = time.time() - start
        results.record(name, "PASS",
                       f"风险等级={assessment['riskLevel']}, 分数={assessment['score']}, "
                       f"因子数={len(assessment['factors'])}",
                       duration)
    except Exception as e:
        duration = time.time() - start
        results.record(name, "FAIL", str(e), duration)


def test_airworthiness(client: E2EClient, results: TestResult) -> None:
    """测试适航评估"""
    name = "适航评估 (Airworthiness)"
    start = time.time()
    try:
        assessment = client.post("/v1/risk/airworthiness", {
            "uavType": "multirotor",
            "weatherConditions": {
                "windSpeed": 8.0,
                "visibility": 8000.0,
                "temperature": 18.0,
                "precipitation": 0.0,
            },
            "route": [
                {"lon": 116.4, "lat": 39.9, "altitude": 100},
                {"lon": 117.0, "lat": 40.0, "altitude": 200},
            ],
        })
        assert "decision" in assessment, "missing decision"
        assert "overallScore" in assessment, "missing overallScore"
        assert len(assessment["factors"]) > 0, "no factors"

        duration = time.time() - start
        results.record(name, "PASS",
                       f"决策={assessment['decision']}, 总分={assessment['overallScore']}, "
                       f"因子数={len(assessment['factors'])}",
                       duration)
    except Exception as e:
        duration = time.time() - start
        results.record(name, "FAIL", str(e), duration)


def test_observation_decision(client: E2EClient, results: TestResult) -> None:
    """测试观测决策"""
    name = "观测决策 (Observation Decision)"
    start = time.time()
    try:
        decision = client.post("/v1/observation/decisions", {
            "region": {"minLon": 116.0, "minLat": 39.5, "maxLon": 117.0, "maxLat": 40.5},
            "targetVariables": ["temperature", "wind_u", "wind_v"],
            "timeWindow": {"start": "2024-01-15T12:00:00Z", "end": "2024-01-15T18:00:00Z"},
        })
        assert "decision" in decision, "missing decision"
        assert "coverageScore" in decision, "missing coverageScore"

        duration = time.time() - start
        results.record(name, "PASS",
                       f"决策={decision['decision']}, 覆盖率={decision['coverageScore']}, "
                       f"建议平台={decision['suggestedPlatforms']}",
                       duration)
    except Exception as e:
        duration = time.time() - start
        results.record(name, "FAIL", str(e), duration)


def test_path_planning(client: E2EClient, results: TestResult) -> None:
    """测试路径规划"""
    name = "路径规划 (Path Planning)"
    start = time.time()
    try:
        # 提交路径规划
        task = client.post("/v1/planning/path", {
            "startPoint": {"lon": 116.4, "lat": 39.9, "altitude": 100},
            "endPoint": {"lon": 117.0, "lat": 40.0, "altitude": 200},
            "waypoints": [
                {"lon": 116.6, "lat": 39.95, "altitude": 150},
            ],
            "algorithm": "rrt_star",
        })
        task_id = task["id"]
        assert task["status"] in ("PENDING", "RUNNING", "COMPLETED"), f"unexpected status: {task['status']}"

        # 获取规划结果
        result = client.get(f"/v1/planning/tasks/{task_id}/result")
        assert len(result["waypoints"]) > 0, "no waypoints in result"
        assert result["totalDistance"] > 0, "totalDistance should be positive"

        duration = time.time() - start
        results.record(name, "PASS",
                       f"任务ID={task_id}, 航点数={len(result['waypoints'])}, "
                       f"总距离={result['totalDistance']}km, 预估时间={result['estimatedTime']}s",
                       duration)
    except Exception as e:
        duration = time.time() - start
        results.record(name, "FAIL", str(e), duration)


def test_utm_flight_plan(client: E2EClient, results: TestResult) -> None:
    """测试 UTM 飞行计划全流程"""
    name = "UTM 飞行计划 (Flight Plan Lifecycle)"
    start = time.time()
    try:
        # 提交飞行计划
        plan = client.post("/v1/flight-plans", {
            "uavId": "UAV-TEST-001",
            "waypoints": [
                {"lon": 116.4, "lat": 39.9, "altitude": 100, "speed": 15},
                {"lon": 116.6, "lat": 39.95, "altitude": 150, "speed": 18},
                {"lon": 117.0, "lat": 40.0, "altitude": 200, "speed": 15},
            ],
            "estimatedDepartureTime": "2024-01-15T12:00:00Z",
        })
        plan_id = plan["id"]
        assert plan["status"] == "SUBMITTED", f"expected SUBMITTED, got {plan['status']}"

        # 审批飞行计划
        approved = client.post(f"/v1/flight-plans/{plan_id}/approve")
        assert approved["status"] == "APPROVED", f"expected APPROVED, got {approved['status']}"

        # 启动飞行计划
        started = client.post(f"/v1/flight-plans/{plan_id}/start")
        assert started["status"] == "ACTIVE", f"expected ACTIVE, got {started['status']}"

        # 位置上报
        client.post("/v1/tracking/positions", {
            "uavId": "UAV-TEST-001",
            "lon": 116.4,
            "lat": 39.9,
            "altitude": 100,
            "heading": 45.0,
            "speed": 15.0,
            "timestamp": "2024-01-15T12:00:00Z",
        })

        # 冲突检测
        conflicts = client.post("/v1/tracking/conflicts/check", {
            "plannedPath": [
                {"lon": 116.4, "lat": 39.9, "altitude": 100, "timestamp": "2024-01-15T12:00:00Z"},
                {"lon": 117.0, "lat": 40.0, "altitude": 200, "timestamp": "2024-01-15T12:15:00Z"},
            ],
            "timeWindow": {"start": "2024-01-15T12:00:00Z", "end": "2024-01-15T12:30:00Z"},
        })
        assert isinstance(conflicts, list), "conflicts should be a list"

        duration = time.time() - start
        results.record(name, "PASS",
                       f"计划ID={plan_id}, 状态流转: SUBMITTED->APPROVED->ACTIVE, "
                       f"冲突数={len(conflicts)}",
                       duration)
    except Exception as e:
        duration = time.time() - start
        results.record(name, "FAIL", str(e), duration)


def test_full_pipeline(client: E2EClient, results: TestResult) -> None:
    """
    完整管线测试: 气象查询 -> 同化 -> 风险评估 -> 适航评估 -> 路径规划 -> UTM飞行计划
    """
    name = "完整管线 (Full Pipeline)"
    start = time.time()
    try:
        pipeline_results = {}

        # 1. 查询气象
        weather = client.post("/v1/weather/point", {
            "lon": 116.4, "lat": 39.9, "altitude": 100,
        })
        pipeline_results["weather"] = f"{weather['temperature']}C, {weather['windSpeed']}m/s"

        # 2. 提交同化任务
        task_id = client.post("/v1/assimilation/tasks", {
            "type": "3DVAR",
            "algorithm": "three_dimensional_var",
            "startTime": "2024-01-15T00:00:00Z",
            "endTime": "2024-01-15T06:00:00Z",
        })
        pipeline_results["assimilation_task_id"] = task_id

        # 3. 等待同化完成（mock 模式下直接完成）
        task = client.get(f"/v1/assimilation/tasks/{task_id}")
        pipeline_results["assimilation_status"] = task["status"]

        # 4. 风险评估
        risk = client.post("/v1/risk/assess", {
            "path": [
                {"lon": 116.4, "lat": 39.9, "altitude": 100},
                {"lon": 117.0, "lat": 40.0, "altitude": 200},
            ],
            "time": "2024-01-15T12:00:00Z",
        })
        pipeline_results["risk"] = f"{risk['riskLevel']}({risk['score']})"

        # 5. 适航评估
        airworthiness = client.post("/v1/risk/airworthiness", {
            "uavType": "multirotor",
            "weatherConditions": {
                "windSpeed": weather["windSpeed"],
                "visibility": weather["visibility"],
                "temperature": weather["temperature"],
            },
            "route": [
                {"lon": 116.4, "lat": 39.9, "altitude": 100},
                {"lon": 117.0, "lat": 40.0, "altitude": 200},
            ],
        })
        pipeline_results["airworthiness"] = f"{airworthiness['decision']}({airworthiness['overallScore']})"

        # 6. 路径规划
        plan_task = client.post("/v1/planning/path", {
            "startPoint": {"lon": 116.4, "lat": 39.9, "altitude": 100},
            "endPoint": {"lon": 117.0, "lat": 40.0, "altitude": 200},
            "algorithm": "rrt_star",
        })
        plan_id = plan_task["id"]
        path_result = client.get(f"/v1/planning/tasks/{plan_id}/result")
        pipeline_results["planning"] = f"{len(path_result['waypoints'])}航点, {path_result['totalDistance']}km"

        # 7. UTM 飞行计划申报
        flight_plan = client.post("/v1/flight-plans", {
            "uavId": "UAV-PIPELINE-001",
            "waypoints": [
                {"lon": wp["lon"], "lat": wp["lat"], "altitude": wp["altitude"], "speed": wp["speed"]}
                for wp in path_result["waypoints"]
            ],
            "estimatedDepartureTime": "2024-01-15T12:00:00Z",
        })
        fp_id = flight_plan["id"]

        # 8. 审批并启动
        client.post(f"/v1/flight-plans/{fp_id}/approve")
        client.post(f"/v1/flight-plans/{fp_id}/start")

        # 9. 位置上报
        for wp in path_result["waypoints"]:
            client.post("/v1/tracking/positions", {
                "uavId": "UAV-PIPELINE-001",
                "lon": wp["lon"],
                "lat": wp["lat"],
                "altitude": wp["altitude"],
                "heading": 45.0,
                "speed": wp["speed"],
                "timestamp": wp["timestamp"],
            })

        # 10. 冲突检测
        conflicts = client.post("/v1/tracking/conflicts/check", {
            "plannedPath": [
                {"lon": wp["lon"], "lat": wp["lat"], "altitude": wp["altitude"], "timestamp": wp["timestamp"]}
                for wp in path_result["waypoints"]
            ],
            "timeWindow": {"start": "2024-01-15T12:00:00Z", "end": "2024-01-15T13:00:00Z"},
        })
        pipeline_results["conflicts"] = f"{len(conflicts)}个冲突"

        duration = time.time() - start
        summary = " -> ".join([
            f"气象({pipeline_results['weather']})",
            f"同化({pipeline_results['assimilation_status']})",
            f"风险({pipeline_results['risk']})",
            f"适航({pipeline_results['airworthiness']})",
            f"规划({pipeline_results['planning']})",
            f"UTM(计划ID={fp_id})",
            f"冲突({pipeline_results['conflicts']})",
        ])
        results.record(name, "PASS", summary, duration)

    except Exception as e:
        duration = time.time() - start
        results.record(name, "FAIL", str(e), duration)


# ============================================================
# Main
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="UAV Platform V2 端到端集成测试")
    parser.add_argument("--url", default=DEFAULT_BASE_URL, help="API base URL")
    parser.add_argument("--key", default=DEFAULT_API_KEY, help="API key")
    parser.add_argument("--secret", default=DEFAULT_API_SECRET, help="API secret")
    parser.add_argument("--mock", action="store_true", default=True, help="使用模拟数据（默认开启）")
    parser.add_argument("--no-mock", action="store_true", help="禁用模拟模式，连接真实服务")
    args = parser.parse_args()

    mock_mode = args.mock and not args.no_mock

    print("=" * 60)
    print("  UAV Platform V2 端到端集成测试")
    print("=" * 60)
    print(f"  目标地址: {args.url}")
    print(f"  API Key:  {args.key}")
    print(f"  模式:     {'MOCK (模拟数据)' if mock_mode else 'LIVE (真实服务)'}")
    print("=" * 60)
    print()

    client = E2EClient(
        base_url=args.url,
        api_key=args.key,
        api_secret=args.secret,
        mock=mock_mode,
    )
    results = TestResult()

    # Run all tests
    test_health_check(client, results)
    test_weather_query(client, results)
    test_assimilation_task(client, results)
    test_risk_assessment(client, results)
    test_airworthiness(client, results)
    test_observation_decision(client, results)
    test_path_planning(client, results)
    test_utm_flight_plan(client, results)
    test_full_pipeline(client, results)

    # Print report
    print(results.report())

    # Exit code
    sys.exit(1 if results.failed > 0 else 0)


if __name__ == "__main__":
    main()
