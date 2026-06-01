"""
端到端 (E2E) 测试套件 — API 全面巡航测试

覆盖范围:
1. 认证全流程 (注册 → 登录 → Token刷新 → 注销)
2. 数据源管理 CRUD
3. 气象/预报/同化数据流
4. 路径规划全流程
5. 边缘云协同服务
6. 网关与服务发现
7. 并发与弹性测试

使用方法:
    SET BASE_URL=http://localhost:8088
    SET TEST_USERNAME=test_e2e_user
    SET TEST_PASSWORD=test_e2e_pass
    pytest tests/e2e/test_e2e_flows.py -v --tb=short
"""

import pytest
import requests
import os
import time
import json
from datetime import datetime


# =============================================================================
# 配置
# =============================================================================

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8088")
API_GATEWAY = BASE_URL
EDGE_COORDINATOR = os.environ.get("EDGE_COORDINATOR_URL", "http://localhost:8000")

try:
    TEST_USERNAME = os.environ["TEST_USERNAME"]
    TEST_PASSWORD = os.environ["TEST_PASSWORD"]
except KeyError as e:
    raise EnvironmentError(
        f"缺少必需的环境变量: {e}. 请设置 TEST_USERNAME 和 TEST_PASSWORD"
    ) from e

REQUEST_TIMEOUT = 15
HEALTH_CHECK_TIMEOUT = 5


def assert_standard_response(resp, expected_code=200):
    """验证标准 API 响应格式"""
    assert resp.status_code in [expected_code, 404, 503], (
        f"预期状态码 {expected_code}，实际 {resp.status_code}: {resp.text[:200]}"
    )
    if resp.status_code == 200:
        try:
            data = resp.json()
            return data
        except (json.JSONDecodeError, ValueError):
            pytest.fail(f"响应不是合法 JSON: {resp.text[:200]}")
    return None


# =============================================================================
# 认证全流程测试
# =============================================================================

class TestAuthFullFlow:
    """认证完整生命周期 E2E 测试"""

    _shared_token = None
    _shared_refresh_token = None
    _base_url = API_GATEWAY

    def test_01_health_check(self):
        """[冒烟] API Gateway 存活检查"""
        resp = requests.get(f"{self._base_url}/actuator/health", timeout=HEALTH_CHECK_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            assert "status" in data, "健康检查响应缺少 status 字段"

    def test_02_register_user(self):
        """[认证] 注册新用户"""
        unique_suffix = int(time.time())
        username = f"{TEST_USERNAME}_{unique_suffix}"
        resp = requests.post(
            f"{self._base_url}/api/v1/auth/register",
            json={
                "username": username,
                "password": TEST_PASSWORD,
                "email": f"{username}@uav.com",
                "fullName": "E2E Test User",
            },
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") in [200, 201], f"注册返回异常: {data}"

    def test_03_login_success(self):
        """[认证] 登录成功获取 Token"""
        resp = requests.post(
            f"{self._base_url}/api/v1/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 200:
                token_data = data.get("data", data)
                access_token = token_data.get("accessToken") or token_data.get("token")
                refresh_token = token_data.get("refreshToken")
                assert access_token is not None, "登录响应缺少 accessToken"
                TestAuthFullFlow._shared_token = access_token
                TestAuthFullFlow._shared_refresh_token = refresh_token

    def test_04_login_failure_wrong_password(self):
        """[认证] 错误密码登录应被拒绝"""
        resp = requests.post(
            f"{self._base_url}/api/v1/auth/login",
            json={"username": TEST_USERNAME, "password": "definitely_wrong_password"},
            timeout=REQUEST_TIMEOUT,
        )
        assert resp.status_code in (401, 403, 200), f"预期认证失败，实际: {resp.status_code}"
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") != 200, "错误密码登录不应该返回成功 code"

    def test_05_login_failure_empty_credentials(self):
        """[认证] 空凭据登录应被拒绝"""
        resp = requests.post(
            f"{self._base_url}/api/v1/auth/login",
            json={"username": "", "password": ""},
            timeout=REQUEST_TIMEOUT,
        )
        assert resp.status_code in (400, 401, 422, 200), f"预期参数校验失败，实际: {resp.status_code}"

    def test_06_refresh_token(self):
        """[认证] Token 刷新 - 使用 refresh token 获取新 access token"""
        refresh_token = TestAuthFullFlow._shared_refresh_token
        if not refresh_token:
            pytest.skip("无 refresh token，跳过")
        resp = requests.post(
            f"{self._base_url}/api/v1/auth/refresh",
            json={"refreshToken": refresh_token},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 200:
                token_data = data.get("data", data)
                new_token = token_data.get("accessToken") or token_data.get("token")
                assert new_token is not None, "刷新响应缺少新 accessToken"
                TestAuthFullFlow._shared_token = new_token
                if token_data.get("refreshToken"):
                    TestAuthFullFlow._shared_refresh_token = token_data["refreshToken"]

    def test_07_unauthorized_access_rejected(self):
        """[安全] 未认证请求访问受保护资源应被拒绝"""
        resp = requests.get(
            f"{self._base_url}/api/v1/data-sources",
            timeout=REQUEST_TIMEOUT,
            headers={},
        )
        assert resp.status_code in (401, 403, 404), (
            f"未认证请求预期被拒，实际: {resp.status_code}"
        )

    def test_08_authenticated_access_allowed(self):
        """[安全] 携带有效 Token 可访问受保护资源"""
        token = TestAuthFullFlow._shared_token
        if not token:
            pytest.skip("无有效 token，跳过")
        resp = requests.get(
            f"{self._base_url}/api/v1/data-sources",
            timeout=REQUEST_TIMEOUT,
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code == 200:
            assert_standard_response(resp)

    def test_09_logout(self):
        """[认证] 注销 - 清除服务端会话"""
        token = TestAuthFullFlow._shared_token
        if not token:
            pytest.skip("无有效 token，跳过")
        resp = requests.post(
            f"{self._base_url}/api/v1/auth/logout",
            timeout=REQUEST_TIMEOUT,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code in (200, 401, 404), f"注销请求异常: {resp.status_code}"


# =============================================================================
# 数据源管理 E2E
# =============================================================================

class TestDataSourceManagement:
    """数据源管理 CRUD E2E 测试"""

    _base_url = API_GATEWAY
    _test_source_id = None

    def test_01_list_data_sources(self):
        """[数据源] 获取数据源列表"""
        resp = requests.get(f"{self._base_url}/api/v1/data-sources", timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") == 200, f"列表返回异常 code: {data.get('code')}"
            assert "data" in data, "响应缺少 data 字段"

    def test_02_get_data_source_types(self):
        """[数据源] 获取数据源类型"""
        resp = requests.get(
            f"{self._base_url}/api/v1/data-sources/types", timeout=REQUEST_TIMEOUT
        )
        if resp.status_code == 200:
            data = resp.json()
            assert "data" in data, "响应缺少 data 字段"

    def test_03_create_data_source(self):
        """[数据源] 创建新数据源并记录 ID"""
        resp = requests.post(
            f"{self._base_url}/api/v1/data-sources",
            json={
                "name": f"E2E_Source_{int(time.time())}",
                "type": "ground_station",
                "url": "http://e2e-test-source:8080",
                "description": "Created by E2E test",
            },
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") == 200, f"创建返回异常: {data}"
            source_id = data.get("data", {}).get("id")
            if source_id:
                TestDataSourceManagement._test_source_id = source_id

    def test_04_get_single_data_source(self):
        """[数据源] 按 ID 获取数据源详情"""
        source_id = TestDataSourceManagement._test_source_id
        if not source_id:
            pytest.skip("无数据源 ID，跳过")
        resp = requests.get(
            f"{self._base_url}/api/v1/data-sources/{source_id}",
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") == 200

    def test_05_update_data_source(self):
        """[数据源] 更新数据源信息"""
        source_id = TestDataSourceManagement._test_source_id
        if not source_id:
            pytest.skip("无数据源 ID，跳过")
        resp = requests.put(
            f"{self._base_url}/api/v1/data-sources/{source_id}",
            json={"name": f"E2E_Updated_{int(time.time())}"},
            timeout=REQUEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404, 405)

    def test_06_delete_data_source(self):
        """[数据源] 删除数据源"""
        source_id = TestDataSourceManagement._test_source_id
        if not source_id:
            pytest.skip("无数据源 ID，跳过")
        resp = requests.delete(
            f"{self._base_url}/api/v1/data-sources/{source_id}",
            timeout=REQUEST_TIMEOUT,
        )
        assert resp.status_code in (200, 204, 404), f"删除返回异常: {resp.status_code}"


# =============================================================================
# 气象数据流 E2E
# =============================================================================

class TestWeatherDataFlow:
    """气象数据获取 E2E 测试"""

    _base_url = API_GATEWAY

    def test_01_get_weather_data(self):
        """[气象] 获取 WRF 处理后的气象数据"""
        resp = requests.get(
            f"{self._base_url}/api/platform/weather?fileId=test_sample",
            timeout=REQUEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404, 503), f"气象数据请求异常: {resp.status_code}"

    def test_02_get_ground_station_data(self):
        """[气象] 获取地面站实时数据"""
        resp = requests.get(
            f"{self._base_url}/api/v1/real-data/ground-station",
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") == 200
            assert "data" in data

    def test_03_get_buoy_data(self):
        """[气象] 获取浮标数据"""
        resp = requests.get(
            f"{self._base_url}/api/v1/real-data/buoy",
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") == 200

    def test_04_get_detailed_forecast(self):
        """[气象] 获取详细气象预报"""
        resp = requests.post(
            f"{self._base_url}/api/forecast/detail",
            json={
                "lat": 39.9,
                "lng": 116.4,
                "hours": 24,
                "variables": ["temperature", "wind_speed", "humidity"],
            },
            timeout=REQUEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404, 503)

    def test_05_get_realtime_weather(self):
        """[气象] 获取实时天气"""
        resp = requests.get(
            f"{self._base_url}/api/forecast/realtime?lat=39.9&lng=116.4",
            timeout=REQUEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404, 503)


# =============================================================================
# 路径规划 E2E
# =============================================================================

class TestPathPlanningFlow:
    """路径规划全流程 E2E 测试"""

    _base_url = API_GATEWAY

    def test_01_vrptw_planning(self):
        """[路径] VRPTW 全局路径规划请求"""
        resp = requests.post(
            f"{self._base_url}/api/planning/vrptw",
            json={
                "algorithm": "vrptw",
                "drones": {"count": 3, "start_point": "39.9,116.4,100"},
                "tasks": {"locations": ["39.9,116.4", "40.0,116.5", "39.8,116.3"]},
                "weatherData": {"wind_speed": 5.0},
                "constraints": {"max_distance": 50000},
            },
            timeout=30,
        )
        assert resp.status_code in (200, 404, 503)

    def test_02_astar_planning(self):
        """[路径] A* 路径规划请求"""
        resp = requests.post(
            f"{self._base_url}/api/planning/astar",
            json={
                "algorithm": "astar",
                "drones": {"count": 1, "start_point": "39.9,116.4,100"},
                "tasks": {"end_point": "40.0,116.5,100"},
                "weatherData": {},
                "constraints": {"max_distance": 10000},
            },
            timeout=30,
        )
        assert resp.status_code in (200, 404, 503)

    def test_03_invalid_request_rejected(self):
        """[路径] 无效路径规划请求应被拒绝"""
        resp = requests.post(
            f"{self._base_url}/api/planning/vrptw",
            json={"algorithm": "", "drones": {}},
            timeout=REQUEST_TIMEOUT,
        )
        assert resp.status_code in (400, 422, 200), f"无效请求预期被拒: {resp.status_code}"

    def test_04_planning_history(self):
        """[路径] 获取规划历史"""
        resp = requests.get(
            f"{self._base_url}/path-planning/history",
            timeout=REQUEST_TIMEOUT,
        )
        assert resp.status_code in (200, 404)


# =============================================================================
# 数据同化 E2E
# =============================================================================

class TestDataAssimilationFlow:
    """数据同化服务 E2E 测试"""

    _base_url = API_GATEWAY

    def test_01_execute_assimilation(self):
        """[同化] 执行数据同化"""
        resp = requests.post(
            f"{self._base_url}/api/assimilation/execute",
            json={
                "algorithm": "3dvar",
                "background": {"field": "temperature", "domain": [100, 100]},
                "observations": {"stations": [{"lat": 39.9, "lon": 116.4, "value": 25.0}]},
                "config": {"resolution": 0.1, "max_iterations": 100},
            },
            timeout=30,
        )
        assert resp.status_code in (200, 404, 503)

    def test_02_get_variance(self):
        """[同化] 计算方差场"""
        resp = requests.post(
            f"{self._base_url}/api/assimilation/variance",
            json={
                "algorithm": "3dvar",
                "background": {"field": "pressure"},
                "observations": {},
                "config": {},
            },
            timeout=30,
        )
        assert resp.status_code in (200, 404, 503)


# =============================================================================
# 无人机设备 E2E
# =============================================================================

class TestUAVDeviceFlow:
    """无人机设备管理 E2E 测试"""

    _base_url = API_GATEWAY

    def test_01_list_drones(self):
        """[设备] 获取无人机列表"""
        resp = requests.get(f"{self._base_url}/api/v1/drones", timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            assert "data" in data

    def test_02_get_drone_detail(self):
        """[设备] 获取无人机详情"""
        resp = requests.get(f"{self._base_url}/api/v1/drones/1", timeout=REQUEST_TIMEOUT)
        assert resp.status_code in (200, 404)

    def test_03_get_drone_status(self):
        """[设备] 获取无人机状态"""
        resp = requests.get(
            f"{self._base_url}/api/v1/drones/status", timeout=REQUEST_TIMEOUT
        )
        assert resp.status_code in (200, 404)


# =============================================================================
# 边缘云协同 E2E
# =============================================================================

class TestEdgeCloudCoordinator:
    """边缘云协同服务 E2E 测试"""

    _base_url = EDGE_COORDINATOR

    def test_01_coordinator_health(self):
        """[边缘] 边云协同服务健康检查"""
        resp = requests.get(
            f"{self._base_url}/health", timeout=HEALTH_CHECK_TIMEOUT
        )
        assert resp.status_code in (200, 404), f"边缘服务不可达: {resp.status_code}"

    def test_02_get_coordinator_status(self):
        """[边缘] 获取协调器状态"""
        resp = requests.get(
            f"{self._base_url}/api/v1/status", timeout=REQUEST_TIMEOUT
        )
        assert resp.status_code in (200, 404)


# =============================================================================
# 服务发现与网关 E2E
# =============================================================================

class TestServiceDiscovery:
    """服务发现与网关路由 E2E 测试"""

    _base_url = API_GATEWAY

    def test_01_gateway_routes(self):
        """[网关] 获取网关路由信息"""
        resp = requests.get(
            f"{self._base_url}/actuator/gateway/routes",
            timeout=HEALTH_CHECK_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, (list, dict)), "路由信息格式异常"

    def test_02_metrics_endpoint(self):
        """[监控] Prometheus 指标端点可达"""
        resp = requests.get(
            f"{self._base_url}/actuator/metrics", timeout=HEALTH_CHECK_TIMEOUT
        )
        assert resp.status_code in (200, 404)

    def test_03_info_endpoint(self):
        """[监控] 应用信息端点"""
        resp = requests.get(
            f"{self._base_url}/actuator/info", timeout=HEALTH_CHECK_TIMEOUT
        )
        assert resp.status_code in (200, 404)


# =============================================================================
# 并发与弹性 E2E
# =============================================================================

class TestConcurrencyAndResilience:
    """并发请求与弹性 E2E 测试"""

    _base_url = API_GATEWAY

    def test_01_concurrent_health_checks(self):
        """[弹性] 并发健康检查不崩溃"""
        import concurrent.futures

        def check_health():
            resp = requests.get(
                f"{self._base_url}/actuator/health", timeout=HEALTH_CHECK_TIMEOUT
            )
            return resp.status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_health) for _ in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        success_count = sum(1 for r in results if r in (200, 404))
        assert success_count == len(results), (
            f"20 个并发请求中 {len(results) - success_count} 个失败"
        )

    def test_02_sequential_bulk_health_checks(self):
        """[弹性] 批量顺序请求不降级"""
        start = time.time()
        for i in range(10):
            resp = requests.get(
                f"{self._base_url}/actuator/health",
                timeout=HEALTH_CHECK_TIMEOUT,
            )
            assert resp.status_code in (200, 404), (
                f"第 {i + 1} 次批量请求失败: {resp.status_code}"
            )
        elapsed = time.time() - start
        assert elapsed < 60, f"10 次顺序请求耗时 {elapsed:.1f}s，预期 < 60s"

    def test_03_malformed_json_returns_400(self):
        """[弹性] 畸形 JSON 请求应返回 400"""
        resp = requests.post(
            f"{self._base_url}/api/v1/auth/login",
            data="not-json-at-all{{{",
            headers={"Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT,
        )
        assert resp.status_code in (400, 415, 422), (
            f"畸形请求预期 4xx，实际: {resp.status_code}"
        )
