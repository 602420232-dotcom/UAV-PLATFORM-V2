"""Prometheus metrics for the Algorithm Engine.

Defines standard UAV algorithm metrics including execution counters,
duration histograms, registration gauges, and active execution gauges.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Metric definitions
# ---------------------------------------------------------------------------

ALGORITHM_EXECUTIONS_TOTAL = Counter(
    "uav_algorithm_executions_total",
    "Total number of algorithm executions",
    ["algorithm_id", "category", "status"],
)

ALGORITHM_EXECUTION_DURATION_SECONDS = Histogram(
    "uav_algorithm_execution_duration_seconds",
    "Duration of algorithm executions in seconds",
    ["algorithm_id", "category"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

ALGORITHM_REGISTERED_TOTAL = Gauge(
    "uav_algorithm_registered_total",
    "Number of registered algorithms by category",
    ["category"],
)

ALGORITHM_ACTIVE_EXECUTIONS = Gauge(
    "uav_algorithm_active_executions",
    "Number of currently active (running) algorithm executions by category",
    ["category"],
)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


class ExecutionTimer:
    """Context manager that times an algorithm execution and records metrics.

    Usage::

        with ExecutionTimer("3dvar", "assimilation") as timer:
            result = adapter.execute(params)
        # On success the timer records status="success" automatically.
        # On exception the timer records status="error" automatically.
    """

    def __init__(self, algorithm_id: str, category: str) -> None:
        self.algorithm_id = algorithm_id
        self.category = category
        self._start: Optional[float] = None
        self._status: str = "success"

    def __enter__(self) -> "ExecutionTimer":
        self._start = time.perf_counter()
        ALGORITHM_ACTIVE_EXECUTIONS.labels(category=self.category).inc()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        duration = time.perf_counter() - (self._start or time.perf_counter())
        if exc_type is not None:
            self._status = "error"
        record_execution(
            algorithm_id=self.algorithm_id,
            category=self.category,
            duration=duration,
            status=self._status,
        )
        ALGORITHM_ACTIVE_EXECUTIONS.labels(category=self.category).dec()


def record_execution(
    algorithm_id: str,
    category: str,
    duration: float,
    status: str,
) -> None:
    """Record a single algorithm execution event.

    Args:
        algorithm_id: Unique identifier of the algorithm.
        category: Algorithm category (e.g. "assimilation", "planning").
        duration: Execution wall-clock time in seconds.
        status: Execution result status (e.g. "success", "error").
    """
    ALGORITHM_EXECUTIONS_TOTAL.labels(
        algorithm_id=algorithm_id,
        category=category,
        status=status,
    ).inc()
    ALGORITHM_EXECUTION_DURATION_SECONDS.labels(
        algorithm_id=algorithm_id,
        category=category,
    ).observe(duration)
    logger.debug(
        "Recorded execution metric: algorithm=%s category=%s status=%s duration=%.3fs",
        algorithm_id,
        category,
        status,
        duration,
    )


def update_registered_count(category: str, count: int) -> None:
    """Update the registered-algorithm gauge for a given *category*.

    Args:
        category: Algorithm category.
        count: Number of algorithms registered in this category.
    """
    ALGORITHM_REGISTERED_TOTAL.labels(category=category).set(count)


def get_metrics() -> tuple[bytes, str]:
    """Return the Prometheus exposition-format metrics as ``(body, content_type)``."""
    return generate_latest(), CONTENT_TYPE_LATEST
