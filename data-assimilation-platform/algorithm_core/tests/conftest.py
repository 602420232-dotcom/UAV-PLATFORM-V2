# Type annotations added: 2026-05-08 13:22:43
from typing import Dict, Any

"""
pytest配置文件
提供共享的fixture和测试配置
"""

import sys
import os
import pytest
import numpy as np
from datetime import datetime

# 添加src目录到Python路径
SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_PATH = os.path.join(SRC_DIR, 'src')


if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


@pytest.fixture
def sample_config():
    """提供测试配置"""
    from bayesian_assimilation.utils.config import AssimilationConfig

    return AssimilationConfig(
        method="3DVAR",
        grid_resolution=50.0,
        background_error_scale=1.5,
        observation_error_scale=0.8,
        correlation_length=50.0
    )


@pytest.fixture
def simple_config():
    """提供简单测试配置"""
    from bayesian_assimilation.utils.config import BaseConfig

    return BaseConfig(
        method="3DVAR",
        grid_resolution=100.0,
        background_error_scale=1.0,
        observation_error_scale=1.0
    )


@pytest.fixture
def background_field():
    """提供测试用背景场数据"""
    nx, ny, nz = 20, 20, 5
    x = np.linspace(0, 2000, nx)
    y = np.linspace(0, 2000, ny)
    z = np.linspace(0, 500, nz)

    # 创建3D背景场
    background = np.zeros((nx, ny, nz))
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                background[i, j, k] = 10.0 + 0.1 * x[i] + 0.05 * y[j] + 0.2 * z[k]

    return background


@pytest.fixture
def observation_data():
    """提供测试用观测数据"""
    # 10个观测点
    n_obs = 10
    np.random.seed(42)

    observations = np.random.uniform(10, 30, n_obs)
    obs_locations = np.random.uniform(0, 2000, (n_obs, 3))
    obs_locations[:, 2] = np.random.uniform(0, 500, n_obs)  # z坐标

    obs_errors = np.random.uniform(0.5, 1.5, n_obs)

    return observations, obs_locations.astype(int), obs_errors


@pytest.fixture
def assimilation_result(background_field, observation_data):
    """提供同化结果fixture"""
    from bayesian_assimilation.core.assimilator import BayesianAssimilator
    from bayesian_assimilation.utils.config import AssimilationConfig

    config = AssimilationConfig(
        grid_resolution=100.0,
        background_error_scale=1.0,
        observation_error_scale=1.0
    )

    assimilator = BayesianAssimilator(config)
    observations, obs_locations, obs_errors = observation_data

    analysis, variance = assimilator.assimilate(
        background_field, observations, obs_locations, obs_errors
    )

    return {
        'assimilator': assimilator,
        'background': background_field,
        'analysis': analysis,
        'variance': variance,
        'observations': observations,
        'obs_locations': obs_locations
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """提供临时输出目录"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return str(output_dir)


@pytest.fixture
def wind_field():
    """提供测试用风场数据"""
    nx, ny, nz = 15, 15, 5
    u = np.random.randn(nx, ny, nz) * 5 + 10  # U风分量
    v = np.random.randn(nx, ny, nz) * 3 + 5   # V风分量

    return u, v


@pytest.fixture
def time_series_data():
    """提供时间序列测试数据"""
    n_times = 10
    n_points = 20

    times = [datetime.now().replace(hour=i) for i in range(n_times)]
    data = [np.random.randn(n_points) * 2 + 15 for _ in range(n_times)]

    return times, data


class TestDataGenerators:
    """测试数据生成器集合"""

    @staticmethod
    def generate_random_field(shape, mean=0, std=1):
        """生成随机场"""
        return np.random.randn(*shape) * std + mean

    @staticmethod
    def generate_synthetic_observations(field, n_obs=20, noise_std=0.5):
        """从场生成合成观测"""
        nx, ny, nz = field.shape

        obs_idx = np.random.randint(0, min(nx, ny, nz), size=(n_obs, 3))
        obs_idx[:, 0] = np.clip(obs_idx[:, 0], 0, nx - 1)
        obs_idx[:, 1] = np.clip(obs_idx[:, 1], 0, ny - 1)
        obs_idx[:, 2] = np.clip(obs_idx[:, 2], 0, nz - 1)

        observations = np.array([field[tuple(idx)] for idx in obs_idx])
        observations += np.random.randn(n_obs) * noise_std

        return observations, obs_idx.astype(int)


def pytest_configure(config: Dict[str, Any]):
    """pytest配置钩子"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config: Dict[str, Any], items: Any):
    """修改测试收集项"""
    for item in items:
        # 根据测试文件路径添加标记
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
