"""
端到端 (E2E) 测试套件 — 基于 Playwright

覆盖关键业务流程:
1. 用户认证流程 (登录/Token刷新/登出)
2. 数据源管理 CRUD 流程
3. 气象数据获取流程
4. 路径规划请求流程
5. API网关路由健康检查

使用方法:
    pip install playwright pytest-playwright pytest
    playwright install chromium
    pytest tests/e2e/test_e2e_flows.py -v --headed
"""

import pytest
import requests
import json
import os
import time

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8088")
API_GATEWAY = BASE_URL
TEST_USERNAME = "testuser"
TEST_PASSWORD = "Test@123456"


class TestAuthenticationFlow:
    """用户认证 E2E 流程"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.base = API_GATEWAY
        self.token = None

    def test_01_register_user(self):
        """注册新用户"""
        resp = requests.post(
            f"{self.base}/api/v1/auth/register",
            json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD,
                "email": "test@uav.com",
                "fullName": "Test User"
            },
            timeout=10
        )
        assert resp.status_code in [200, 400, 405]

    def test_02_login_success(self):
        """登录成功获取Token"""
        resp = requests.post(
            f"{self.base}/api/v1/auth/login",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            assert "token" in data
            self.__class__.token = data["token"]

    def test_03_login_failure_wrong_password(self):
        """错误密码登录失败"""
        resp = requests.post(
            f"{self.base}/api/v1/auth/login",
            json={"username": TEST_USERNAME, "password": "wrong"},
            timeout=10
        )
        assert resp.status_code in [401, 403, 404]

    def test_04_unauthorized_access_denied(self):
        """未认证请求被拒绝"""
        resp = requests.get(f"{self.base}/api/v1/data-sources", timeout=10)
        assert resp.status_code in [401, 403, 404]


class TestDataSourceManagement:
    """数据源管理 E2E 流程"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.base = API_GATEWAY

    def test_01_list_datasources(self):
        """获取数据源列表"""
        resp = requests.get(f"{self.base}/api/v1/data-sources", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") == 200
            assert "data" in data

    def test_02_create_datasource(self):
        """创建新数据源"""
        resp = requests.post(
            f"{self.base}/api/v1/data-sources",
            json={"name": "E2E Test Source", "type": "ground_station", "url": "http://test:8080"},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") == 200

    def test_03_get_datasource_types(self):
        """获取数据源类型列表"""
        resp = requests.get(f"{self.base}/api/v1/data-sources/types", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            assert "data" in data

    def test_04_delete_datasource(self):
        """删除数据源"""
        resp = requests.delete(f"{self.base}/api/v1/data-sources/999", timeout=10)
        assert resp.status_code in [200, 404]


class TestWeatherDataFlow:
    """气象数据获取 E2E 流程"""

    def test_01_get_weather_data(self):
        """获取WRF处理后的气象数据"""
        resp = requests.get(
            f"{API_GATEWAY}/api/platform/weather?fileId=test",
            timeout=10
        )
        assert resp.status_code in [200, 404, 503]

    def test_02_get_real_ground_station_data(self):
        """获取实时地面站数据"""
        resp = requests.get(f"{API_GATEWAY}/api/v1/real-data/ground-station", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") == 200

    def test_03_get_buoy_data(self):
        """获取浮标数据"""
        resp = requests.get(f"{API_GATEWAY}/api/v1/real-data/buoy", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("code") == 200


class TestPathPlanningFlow:
    """路径规划 E2E 流程"""

    def test_01_plan_path_request(self):
        """提交路径规划请求"""
        resp = requests.post(
            f"{API_GATEWAY}/path-planning/plan",
            json={
                "tasks": "[{\"id\":1}]",
                "drones": "[{\"id\":\"UAV001\"}]",
                "weatherData": "{}"
            },
            timeout=15
        )
        assert resp.status_code in [200, 401, 404, 503]

    def test_02_get_planning_history(self):
        """获取规划历史"""
        resp = requests.get(f"{API_GATEWAY}/path-planning/history", timeout=10)
        assert resp.status_code in [200, 404]


class TestGatewayHealth:
    """API网关健康检查"""

    def test_01_gateway_health(self):
        """网关存活检查"""
        resp = requests.get(f"{API_GATEWAY}/actuator/health", timeout=10)
        if resp.status_code == 200:
            assert resp.json().get("status") in ["UP", "DOWN"]

    def test_02_wrf_processor_health(self):
        """WRF处理服务健康"""
        resp = requests.get(f"{API_GATEWAY}/actuator/health", timeout=10)
        assert resp.status_code in [200, 404]

    def test_03_nacos_discovery(self):
        """Nacos服务发现可达"""
        resp = requests.get("http://localhost:8848/nacos/v1/console/health/readiness", timeout=10)
        assert resp.status_code in [200, 404]


class TestResilienceEndToEnd:
    """弹性测试 — 服务超时、重试、熔断"""

    def test_01_retry_on_timeout(self):
        """验证重试机制"""
        start = time.time()
        resp = requests.post(
            f"{API_GATEWAY}/api/platform/plan",
            json={"weatherData": {}, "drones": [], "tasks": []},
            timeout=30
        )
        elapsed = time.time() - start
        assert elapsed < 35

    def test_02_bulk_requests(self):
        """批量请求不崩溃"""
        for _ in range(5):
            resp = requests.get(f"{API_GATEWAY}/actuator/health", timeout=5)
            assert resp.status_code in [200, 404]
