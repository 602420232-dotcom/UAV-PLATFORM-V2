"""Pydantic data models for the algorithm engine."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AlgorithmMetadata(BaseModel):
    """Metadata describing a registered algorithm."""

    id: str
    name: str
    category: str
    version: str = "1.0.0"
    description: str = ""
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(BaseModel):
    """Runtime status of a submitted task."""

    task_id: str
    algorithm_id: str
    status: TaskStatusEnum = TaskStatusEnum.PENDING
    progress: float = 0.0
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class TaskSubmitRequest(BaseModel):
    """Request body for submitting an algorithm task."""

    algorithm_id: str
    params: dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    callback_topic: Optional[str] = None


class TaskSubmitResponse(BaseModel):
    """Response after submitting a task."""

    task_id: str
    algorithm_id: str
    status: TaskStatusEnum


class PipelineStepConfig(BaseModel):
    """Configuration for a single step inside a Pipeline."""

    algorithm_id: str
    params_transform: Optional[str] = None
    condition: Optional[str] = None


class PipelineExecuteRequest(BaseModel):
    """Request body for executing a pipeline."""

    name: str
    steps: list[PipelineStepConfig]
    initial_params: dict[str, Any] = Field(default_factory=dict)


class StepResult(BaseModel):
    """Result of a single pipeline step."""

    step_index: int
    algorithm_id: str
    input_params: dict[str, Any] = Field(default_factory=dict)
    output: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    elapsed_seconds: float = 0.0
    skipped: bool = False


class PipelineResult(BaseModel):
    """Aggregated result of a pipeline execution."""

    pipeline_name: str
    steps_results: list[StepResult] = Field(default_factory=list)
    total_time: float = 0.0
    success: bool = True


class HealthResponse(BaseModel):
    """Health-check response."""

    status: str = "ok"
    version: str = "0.1.0"
    algorithms_registered: int = 0
    tasks_pending: int = 0
