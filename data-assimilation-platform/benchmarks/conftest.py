# Type annotations added: 2026-05-08 13:22:43
from typing import Dict, List, Any, Optional, Callable, Tuple

"""
pytest 配置：定义性能基准测试的共享 fixture 和全局参数
"""
import pytest
import numpy as np


@pytest.fixture(scope="session")
def small_grid():
    return {
        "shape": (50, 50, 20),
        "background": np.random.rand(50, 50, 20),
        "obs_count": 500,
        "observations": np.random.rand(500),
        "obs_locations": np.random.rand(500, 3),
    }


@pytest.fixture(scope="session")
def medium_grid():
    return {
        "shape": (100, 100, 50),
        "background": np.random.rand(100, 100, 50),
        "obs_count": 2000,
        "observations": np.random.rand(2000),
        "obs_locations": np.random.rand(2000, 3),
    }


@pytest.fixture(scope="session")
def large_grid():
    return {
        "shape": (200, 200, 100),
        "background": np.random.rand(200, 200, 100),
        "obs_count": 5000,
        "observations": np.random.rand(5000),
        "obs_locations": np.random.rand(5000, 3),
    }


def pytest_addoption(parser):
    parser.addoption(
        "--benchmark",
        action="store_true",
        default=False,
        help="运行性能基准测试",
    )


def pytest_configure(config: Dict[str, Any]):
    config.addinivalue_line(
        "markers",
        "benchmark: 标记性能基准测试，使用 --benchmark 选项运行",
    )


def pytest_collection_modifyitems(config: Dict[str, Any], items: Any):
    if not config.getoption("--benchmark"):
        skip_benchmark = pytest.mark.skip(reason="需要 --benchmark 选项才能运行")
        for item in items:
            if "benchmark" in item.keywords:
                item.add_marker(skip_benchmark)
