"""Pytest fixtures for algorithm engine unit tests."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest

# Ensure the app package is importable when running tests from the tests/ directory
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


# ---------------------------------------------------------------------------
# Standard test parameters for path planning algorithms
# ---------------------------------------------------------------------------


@pytest.fixture
def start() -> list[int]:
    """Standard start position for path planning tests."""
    return [0, 0]


@pytest.fixture
def goal() -> list[int]:
    """Standard goal position for path planning tests."""
    return [10, 10]


@pytest.fixture
def grid_size() -> list[int]:
    """Standard grid size for path planning tests."""
    return [100, 100]


@pytest.fixture
def obstacles() -> list[list[int]]:
    """Standard obstacle list for path planning tests (empty by default)."""
    return []


@pytest.fixture
def planning_params(start, goal, grid_size, obstacles) -> dict[str, Any]:
    """Combined planning parameters dict."""
    return {
        "start": start,
        "goal": goal,
        "grid_size": grid_size,
        "obstacles": obstacles,
    }


# ---------------------------------------------------------------------------
# Standard test parameters for assimilation algorithms
# ---------------------------------------------------------------------------


@pytest.fixture
def grid_shape() -> tuple[int, int, int]:
    """Standard 3D grid shape for assimilation tests."""
    return (10, 10, 5)


@pytest.fixture
def background_field(grid_shape) -> np.ndarray:
    """Standard background field (zeros) for assimilation tests."""
    return np.zeros(grid_shape, dtype=np.float64)


@pytest.fixture
def sample_observations() -> list[dict[str, Any]]:
    """Standard observation data for assimilation tests."""
    return [
        {"position": [2, 3, 1], "value": 1.0},
        {"position": [5, 7, 2], "value": 2.5},
        {"position": [8, 1, 3], "value": -0.5},
    ]


@pytest.fixture
def assimilation_params(background_field, sample_observations) -> dict[str, Any]:
    """Combined assimilation parameters dict."""
    return {
        "background_field": background_field,
        "observations": sample_observations,
    }


# ---------------------------------------------------------------------------
# Smart scheduler fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def scheduler():
    """Fresh SmartAlgorithmScheduler instance for each test."""
    from app.core.smart_scheduler import SmartAlgorithmScheduler

    return SmartAlgorithmScheduler()
