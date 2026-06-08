"""
E2E测试配置文件
"""

import logging
logger = logging.getLogger(__name__)

import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def pytest_configure(config):
    """pytest配置钩子"""
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试集合"""
    # 为E2E测试添加标记
    for item in items:
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)


@pytest.fixture(scope="session")
def test_config():
    """测试配置fixture"""
    return {
        'api_base_url': os.getenv('API_BASE_URL', 'http://localhost:8088'),
        'timeout': int(os.getenv('TEST_TIMEOUT', '30')),
        'grid_size': 150,
        'risk_threshold': 0.5
    }


@pytest.fixture(scope="session")
def mock_risk_field():
    """模拟风险场fixture"""
    import numpy as np
    return np.random.rand(150, 150) * 0.5


@pytest.fixture(scope="session")
def mock_weather_data():
    """模拟气象数据fixture"""
    import numpy as np
    return {
        'temperature': np.random.rand(100, 100) * 30 + 273,
        'wind_u': np.random.rand(100, 100) * 20 - 10,
        'wind_v': np.random.rand(100, 100) * 20 - 10,
        'pressure': np.random.rand(100, 100) * 50 + 1000,
        'humidity': np.random.rand(100, 100) * 100
    }
