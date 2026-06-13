"""Pipeline - sequential algorithm orchestration with data passing and conditional branching."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Optional

from app.core.models import (
    PipelineExecuteRequest,
    PipelineResult,
    PipelineStepConfig,
    StepResult,
)
from app.core.registry import get_registry

logger = logging.getLogger(__name__)


class Pipeline:
    """Build and execute a multi-step algorithm pipeline.

    Steps are executed sequentially.  The output of step *N* is fed as the
    input to step *N+1*.  A ``params_transform`` callable can be provided to
    reshape the data between steps.  A ``condition`` callable can skip a
    step based on the intermediate result.

    Usage::

        pipe = Pipeline("weather-planning")
        pipe.add_step("3dvar")
        pipe.add_step("weather_risk", condition=lambda ctx: ctx.get("risk_score", 0) > 0.5)
        pipe.add_step("rrt_star")
        result = await pipe.execute({"observation_data": [...]})
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._steps: list[PipelineStepConfig] = []
        self._transforms: dict[str, Callable] = {}
        self._conditions: dict[str, Callable] = {}

    def add_step(
        self,
        algorithm_id: str,
        params_transform: Optional[Callable[[dict[str, Any]], dict[str, Any]]] = None,
        condition: Optional[Callable[[dict[str, Any]], bool]] = None,
    ) -> "Pipeline":
        """Append a step to the pipeline.

        Args:
            algorithm_id: ID of a registered algorithm.
            params_transform: Optional callable to transform the previous
                step output into this step input.
            condition: Optional callable evaluated against the intermediate
                context; step is skipped if it returns ``False``.
        """
        step = PipelineStepConfig(
            algorithm_id=algorithm_id,
            params_transform=params_transform.__name__ if params_transform else None,
            condition=condition.__name__ if condition else None,
        )
        if params_transform:
            self._transforms[algorithm_id] = params_transform
        if condition:
            self._conditions[algorithm_id] = condition
        self._steps.append(step)
        return self

    async def execute(self, initial_params: dict[str, Any]) -> PipelineResult:
        """Execute all pipeline steps sequentially."""
        registry = get_registry()
        context: dict[str, Any] = dict(initial_params)
        steps_results: list[StepResult] = []
        total_start = time.monotonic()
        success = True

        for idx, step_cfg in enumerate(self._steps):
            step_start = time.monotonic()

            # Check condition
            condition_fn = self._conditions.get(step_cfg.algorithm_id)
            if condition_fn and not condition_fn(context):
                steps_results.append(StepResult(
                    step_index=idx,
                    algorithm_id=step_cfg.algorithm_id,
                    input_params={},
                    skipped=True,
                    elapsed_seconds=0.0,
                ))
                logger.info("Pipeline '%s': step %d (%s) skipped by condition",
                            self.name, idx, step_cfg.algorithm_id)
                continue

            # Transform params
            transform_fn = self._transforms.get(step_cfg.algorithm_id)
            step_params = transform_fn(context) if transform_fn else context

            # Execute
            algo_cls = registry.get(step_cfg.algorithm_id)
            if algo_cls is None:
                steps_results.append(StepResult(
                    step_index=idx,
                    algorithm_id=step_cfg.algorithm_id,
                    input_params=step_params,
                    error=f"Algorithm not registered: {step_cfg.algorithm_id}",
                    elapsed_seconds=time.monotonic() - step_start,
                ))
                success = False
                break

            try:
                adapter = algo_cls()
                output = adapter.execute(step_params)
                context.update(output if isinstance(output, dict) else {"result": output})
                steps_results.append(StepResult(
                    step_index=idx,
                    algorithm_id=step_cfg.algorithm_id,
                    input_params=step_params,
                    output=output,
                    elapsed_seconds=time.monotonic() - step_start,
                ))
            except Exception as exc:
                steps_results.append(StepResult(
                    step_index=idx,
                    algorithm_id=step_cfg.algorithm_id,
                    input_params=step_params,
                    error=str(exc),
                    elapsed_seconds=time.monotonic() - step_start,
                ))
                success = False
                logger.exception("Pipeline '%s': step %d failed", self.name, idx)
                break

        return PipelineResult(
            pipeline_name=self.name,
            steps_results=steps_results,
            total_time=time.monotonic() - total_start,
            success=success,
        )
