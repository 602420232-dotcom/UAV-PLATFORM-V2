"""FastAPI application entry point for the Algorithm Engine.

Run with::

    uvicorn app.main:app --host 0.0.0.0 --port 9090
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.api.routes import router, set_scheduler
from app.config import get_settings
from app.core.error_handler import register_error_handlers
from app.core.registry import get_registry
from app.core.scheduler import TaskScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: start scheduler and register algorithms."""
    settings = get_settings()
    logger.info(
        "Starting Algorithm Engine v%s on %s:%d",
        settings.app_version,
        settings.host,
        settings.port,
    )

    scheduler = TaskScheduler(
        max_concurrent=settings.max_concurrent_tasks,
        task_timeout=settings.task_timeout,
        task_ttl=settings.redis_task_ttl,
        kafka_bootstrap_servers=settings.kafka_bootstrap_servers,
    )
    await scheduler.start()
    set_scheduler(scheduler)
    _register_builtin_algorithms()
    _update_registered_metrics()

    logger.info("Algorithm Engine ready. Registered %d algorithms.", len(get_registry()))
    yield

    await scheduler.stop()
    logger.info("Algorithm Engine shut down.")


def _register_builtin_algorithms() -> None:
    """Register all built-in algorithm adapters with the global registry."""
    from app.adapters.assimilation_adapter import (
        AdaptiveAssimilatorAdapter,
        AdaptiveHybridAdapter,
        AdaptiveVarianceFieldAdapter,
        BayesianAssimilatorAdapter,
        CompatibleAssimilatorAdapter,
        EnhancedBayesianAdapter,
        EnKFAdapter,
        FiveDimensionalVarAdapter,
        FourDimensionalVarAdapter,
        HybridAssimilationAdapter,
        MultiScaleHybridAdapter,
        ThreeDimensionalVarAdapter,
        VarianceFieldOptimizerAdapter,
    )
    from app.adapters.edge_adapter import (
        EdgeAggregatorAdapter,
        EdgeAIInferenceAdapter,
        EdgeAnomalyDetectorAdapter,
        EdgeBandwidthOptimizerAdapter,
        EdgeCacheManagerAdapter,
        EdgeDataSyncAdapter,
        EdgeFaultToleranceAdapter,
        EdgeModelUpdateAdapter,
        EdgeResourceMonitorAdapter,
        EdgeSchedulerAdapter,
        EdgeSecurityAdapter,
        EdgeTaskOffloadAdapter,
        FederatedLearningAdapter,
        KnowledgeDistillationAdapter,
        LLMAssistedDecisionAdapter,
        ModelCompressorAdapter,
        ModelQuantizationAdapter,
        SelfOrganizingNetworkAdapter,
        SplitLearningAdapter,
        V2XCommunicationAdapter,
    )
    from app.adapters.model_engine_adapter import (
        BayesianNNAdapter,
        CNNCorrectorAdapter,
        DataPipelineAdapter,
        DQNModelAdapter,
        DynamicWeightFusionAdapter,
        EnsembleKalmanFilterModelAdapter,
        GPRegressionModelAdapter,
        GPRiskEstimatorAdapter,
        GPRPathPlannerAdapter,
        GPRUncertaintyAdapter,
        LSTMPredictorAdapter,
        LSTMTemporalCorrectorAdapter,
        ModelPredictiveControllerAdapter,
        MultiUAVConflictResolverAdapter,
        PhysicsConstraintAdapter,
        PPOModelAdapter,
        ProbabilisticUNetAdapter,
        RiskCostFunctionAdapter,
        SparseGPModelAdapter,
        UNetWeatherPredictorAdapter,
        XGBoostCorrectorAdapter,
    )
    from app.adapters.observation_adapter import (
        AdaptiveObservationAdapter,
        InformationGainAdapter,
        SensorSchedulingAdapter,
    )
    from app.adapters.planning_adapter import (
        AntColonyAdapter,
        AStarAdapter,
        BidirectionalAStarAdapter,
        CBBAAdapter,
        CBSAdapter,
        ConflictDetectorAdapter,
        DERRTStarAdapter,
        DigitalTwinAdapter,
        DijkstraAdapter,
        DQNPlannerAdapter,
        DStarLiteAdapter,
        DWAAdapter,
        GeneticAlgorithmAdapter,
        GreedyBestFirstAdapter,
        InformedRRTAdapter,
        JumpPointSearchAdapter,
        KnowledgeGraphAdapter,
        LazyThetaStarAdapter,
        LPAStarAdapter,
        MarketBasedAdapter,
        MPCAdapter,
        MultiObjectivePlannerAdapter,
        NSGA2Adapter,
        OrbitalDecompositionAdapter,
        ParticleSwarmAdapter,
        PotentialFieldAdapter,
        PPOPlannerAdapter,
        RapidlyExploringTreeAdapter,
        RiskAwareAStarAdapter,
        RiskAwareRRTStarAdapter,
        RRTStarAdapter,
        SimulatedAnnealingAdapter,
        SpatialPartitionAdapter,
        TabuSearchAdapter,
        ThetaStarAdapter,
        ThreeLayerPlannerAdapter,
        Trajectory4DAdapter,
        UncertaintyAwarePlannerAdapter,
        VisibilityGraphAdapter,
        VoronoiRoadmapAdapter,
        VRPTWAdapter,
    )
    from app.adapters.risk_adapter import (
        AirspaceRiskAdapter,
        CompositeRiskAdapter,
        TerrainRiskAdapter,
        WeatherRiskAdapter,
    )

    registry = get_registry()

    all_adapters = (
        [
            ThreeDimensionalVarAdapter,
            FourDimensionalVarAdapter,
            FiveDimensionalVarAdapter,
            EnKFAdapter,
            HybridAssimilationAdapter,
            EnhancedBayesianAdapter,
            AdaptiveHybridAdapter,
            MultiScaleHybridAdapter,
            AdaptiveAssimilatorAdapter,
            VarianceFieldOptimizerAdapter,
            AdaptiveVarianceFieldAdapter,
            BayesianAssimilatorAdapter,
            CompatibleAssimilatorAdapter,
        ]
        + [
            VRPTWAdapter,
            DERRTStarAdapter,
            DWAAdapter,
            MPCAdapter,
            AStarAdapter,
            DijkstraAdapter,
            RRTStarAdapter,
            AntColonyAdapter,
            ParticleSwarmAdapter,
            GeneticAlgorithmAdapter,
            SimulatedAnnealingAdapter,
            TabuSearchAdapter,
            GreedyBestFirstAdapter,
            BidirectionalAStarAdapter,
            JumpPointSearchAdapter,
            ThetaStarAdapter,
            LazyThetaStarAdapter,
            DStarLiteAdapter,
            LPAStarAdapter,
            PotentialFieldAdapter,
            VoronoiRoadmapAdapter,
            VisibilityGraphAdapter,
            RapidlyExploringTreeAdapter,
            InformedRRTAdapter,
            CBBAAdapter,
            OrbitalDecompositionAdapter,
            MarketBasedAdapter,
            SpatialPartitionAdapter,
            # Phase 2 新增：HTML重构计划对齐
            CBSAdapter,
            NSGA2Adapter,
            ConflictDetectorAdapter,
            DQNPlannerAdapter,
            PPOPlannerAdapter,
            ThreeLayerPlannerAdapter,
            RiskAwareAStarAdapter,
            RiskAwareRRTStarAdapter,
            UncertaintyAwarePlannerAdapter,
            MultiObjectivePlannerAdapter,
            DigitalTwinAdapter,
            KnowledgeGraphAdapter,
            Trajectory4DAdapter,
        ]
        + [WeatherRiskAdapter, TerrainRiskAdapter, AirspaceRiskAdapter, CompositeRiskAdapter]
        + [InformationGainAdapter, AdaptiveObservationAdapter, SensorSchedulingAdapter]
        + [
            GPRUncertaintyAdapter,
            BayesianNNAdapter,
            LSTMPredictorAdapter,
            UNetWeatherPredictorAdapter,
            # Phase 2 新增：HTML重构计划对齐
            CNNCorrectorAdapter,
            ProbabilisticUNetAdapter,
            LSTMTemporalCorrectorAdapter,
            XGBoostCorrectorAdapter,
            DQNModelAdapter,
            PPOModelAdapter,
            GPRegressionModelAdapter,
            SparseGPModelAdapter,
            GPRiskEstimatorAdapter,
            DynamicWeightFusionAdapter,
            PhysicsConstraintAdapter,
            ModelPredictiveControllerAdapter,
            GPRPathPlannerAdapter,
            RiskCostFunctionAdapter,
            MultiUAVConflictResolverAdapter,
            EnsembleKalmanFilterModelAdapter,
            DataPipelineAdapter,
        ]
        + [FederatedLearningAdapter, ModelQuantizationAdapter, V2XCommunicationAdapter]
        + [
            # Phase 2 新增：HTML重构计划对齐 - 边云算法
            EdgeAIInferenceAdapter,
            LLMAssistedDecisionAdapter,
            SelfOrganizingNetworkAdapter,
            EdgeAggregatorAdapter,
            ModelCompressorAdapter,
            SplitLearningAdapter,
            KnowledgeDistillationAdapter,
            EdgeSchedulerAdapter,
            EdgeCacheManagerAdapter,
            EdgeDataSyncAdapter,
            EdgeModelUpdateAdapter,
            EdgeResourceMonitorAdapter,
            EdgeTaskOffloadAdapter,
            EdgeSecurityAdapter,
            EdgeFaultToleranceAdapter,
            EdgeBandwidthOptimizerAdapter,
            EdgeAnomalyDetectorAdapter,
        ]
    )

    for cls in all_adapters:
        adapter = cls()  # type: ignore[abstract]
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


def _update_registered_metrics() -> None:
    """Update the Prometheus registered-algorithm gauge for every category."""
    from collections import Counter

    from app.core.metrics import update_registered_count

    registry = get_registry()
    category_counts = Counter(e.category for e in registry.get_entries().values())
    for category, count in category_counts.items():
        update_registered_count(category, count)


app = FastAPI(
    title="Algorithm Engine",
    description="UAV Platform V2 - Algorithm Orchestration Engine",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)

# 注册全局异常处理器
register_error_handlers(app)
