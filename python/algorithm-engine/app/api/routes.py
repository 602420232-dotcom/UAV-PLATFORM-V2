"""HTTP API routes for the algorithm engine."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.core.models import (
    HealthResponse,
    PipelineExecuteRequest,
    PipelineResult,
    TaskStatus,
    TaskStatusEnum,
    TaskSubmitRequest,
    TaskSubmitResponse,
)
from app.core.pipeline import Pipeline
from app.core.registry import get_registry
from app.core.scheduler import TaskScheduler

logger = logging.getLogger(__name__)

router = APIRouter()

_scheduler: TaskScheduler | None = None


def set_scheduler(scheduler: TaskScheduler) -> None:
    """Inject the task scheduler instance (called from main.py)."""
    global _scheduler
    _scheduler = scheduler


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    registry = get_registry()
    pending = 0
    if _scheduler:
        tasks = await _scheduler.list_tasks(status=TaskStatusEnum.PENDING)
        pending = len(tasks)
    return HealthResponse(status="ok", algorithms_registered=len(registry), tasks_pending=pending)


@router.get("/api/v1/algorithms")
async def list_algorithms():
    """List all registered algorithms."""
    registry = get_registry()
    return [m.model_dump() for m in registry.list_all()]


@router.get("/api/v1/algorithms/{category}")
async def list_algorithms_by_category(category: str):
    """List algorithms filtered by category."""
    registry = get_registry()
    algorithms = registry.list_by_category(category)
    if not algorithms:
        raise HTTPException(status_code=404, detail=f"No algorithms found in category '{category}'")
    return [m.model_dump() for m in algorithms]


@router.post("/api/v1/tasks/submit", response_model=TaskSubmitResponse)
async def submit_task(request: TaskSubmitRequest):
    """Submit an algorithm execution task."""
    registry = get_registry()
    if request.algorithm_id not in registry:
        raise HTTPException(
            status_code=404,
            detail=f"Algorithm '{request.algorithm_id}' not registered",
        )
    if _scheduler is None:
        raise HTTPException(status_code=503, detail="Task scheduler not available")
    task_id = await _scheduler.submit(
        algorithm_id=request.algorithm_id,
        params=request.params,
        priority=request.priority,
        callback_topic=request.callback_topic,
    )
    return TaskSubmitResponse(
        task_id=task_id,
        algorithm_id=request.algorithm_id,
        status=TaskStatusEnum.PENDING,
    )


@router.get("/api/v1/tasks/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Query the status of a submitted task."""
    if _scheduler is None:
        raise HTTPException(status_code=503, detail="Task scheduler not available")
    status = await _scheduler.get_status(task_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return status


@router.get("/api/v1/tasks/{task_id}/result")
async def get_task_result(task_id: str):
    """Get the result of a completed task."""
    if _scheduler is None:
        raise HTTPException(status_code=503, detail="Task scheduler not available")
    result = await _scheduler.get_result(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Result for task '{task_id}' not found")
    return result


@router.post("/api/v1/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a pending or running task."""
    if _scheduler is None:
        raise HTTPException(status_code=503, detail="Task scheduler not available")
    success = await _scheduler.cancel(task_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Task '{task_id}' not found or cannot be cancelled",
        )
    return {"message": f"Task '{task_id}' cancelled", "task_id": task_id}


@router.post("/api/v1/pipelines/execute", response_model=PipelineResult)
async def execute_pipeline(request: PipelineExecuteRequest):
    """Execute a multi-step algorithm pipeline."""
    registry = get_registry()
    pipeline = Pipeline(name=request.name)
    for step in request.steps:
        if step.algorithm_id not in registry:
            raise HTTPException(
                status_code=404,
                detail=(f"Pipeline step algorithm '{step.algorithm_id}' not registered"),
            )
        pipeline.add_step(step.algorithm_id)
    result = await pipeline.execute(request.initial_params)
    return result
