"""FastAPI application entry point for the Algorithm Engine.

Run with::

    uvicorn app.main:app --host 0.0.0.0 --port 9090
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.config import get_settings
from app.core.registry import get_registry
from app.core.scheduler import TaskScheduler
from app.api.routes import router, set_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: start scheduler and register algorithms."""
    settings = get_settings()
    logger.info("Starting Algorithm Engine v%s on %s:%d", settings.app_version, settings.host, settings.port)

    scheduler = TaskScheduler(
        max_concurrent=settings.max_concurrent_tasks,
        task_timeout=settings.task_timeout,
        task_ttl=settings.redis_task_ttl,
    )
    await scheduler.start()
    set_scheduler(scheduler)
    _register_builtin_algorithms()

    logger.info("Algorithm Engine ready. Registered %d algorithms.", len(get_registry()))
    yield

    await scheduler.stop()
    logger.info("Algorithm Engine shut down.")


def _register_builtin_algorithms() -> None:
    """Register all built-in algorithm adapters with the global registry."""
    from app.adapters.assimilation_adapter import (
        ThreeDimensionalVarAdapter, FourDimensionalVarAdapter, FiveDimensionalVarAdapter,
        EnKFAdapter, HybridAssimilationAdapter, EnhancedBayesianAdapter,
    )
    from app.adapters.planning_adapter import (
        VRPTWAdapter, DERRTStarAdapter, DWAAdapter, MPCAdapter,
        AStarAdapter, DijkstraAdapter, RRTStarAdapter,
    )
    from app.adapters.risk_adapter import (
        WeatherRiskAdapter, TerrainRiskAdapter, AirspaceRiskAdapter, CompositeRiskAdapter,
    )
    from app.adapters.observation_adapter import (
        InformationGainAdapter, AdaptiveObservationAdapter, SensorSchedulingAdapter,
    )

    registry = get_registry()

    all_adapters = (
        [ThreeDimensionalVarAdapter, FourDimensionalVarAdapter, FiveDimensionalVarAdapter,
         EnKFAdapter, HybridAssimilationAdapter, EnhancedBayesianAdapter] +
        [VRPTWAdapter, DERRTStarAdapter, DWAAdapter, MPCAdapter,
         AStarAdapter, DijkstraAdapter, RRTStarAdapter] +
        [WeatherRiskAdapter, TerrainRiskAdapter, AirspaceRiskAdapter, CompositeRiskAdapter] +
        [InformationGainAdapter, AdaptiveObservationAdapter, SensorSchedulingAdapter]
    )

    for cls in all_adapters:
        adapter = cls()
        meta = adapter.get_metadata()
        registry.register(
            algorithm_id=meta.id,
            algorithm_class=cls,
            category=meta.category,
            version=meta.version,
            description=meta.description,
            input_schema=meta.input_schema,
            output_schema=meta.output_schema,
        )


app = FastAPI(
    title="Algorithm Engine",
    description="UAV Platform V2 - Algorithm Orchestration Engine",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)
