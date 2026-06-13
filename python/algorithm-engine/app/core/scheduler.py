"""Task Scheduler - async task execution with priority queue and Redis backing."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.models import TaskStatus, TaskStatusEnum

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Async task scheduler backed by Redis for state persistence.

    Features:
    * Priority-based task queue
    * ``asyncio`` + ``ThreadPoolExecutor`` for running synchronous algorithms
    * Redis storage for task state and results (TTL 1 hour)
    * Task cancellation support
    """

    def __init__(
        self,
        redis_client: Any = None,
        max_concurrent: int = 10,
        task_timeout: int = 300,
        task_ttl: int = 3600,
        kafka_bootstrap_servers: str = "localhost:9092",
    ) -> None:
        self._redis = redis_client
        self._max_concurrent = max_concurrent
        self._task_timeout = task_timeout
        self._task_ttl = task_ttl
        self._tasks: dict[str, TaskStatus] = {}
        self._results: dict[str, dict[str, Any]] = {}
        self._futures: dict[str, asyncio.Task] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self._priority_queue: asyncio.PriorityQueue[tuple[int, str, dict[str, Any]]] = asyncio.PriorityQueue()
        self._running = False
        # Kafka producer (lazy-loaded)
        self._kafka_bootstrap_servers = kafka_bootstrap_servers
        self._kafka_producer: Any | None = None

    async def start(self) -> None:
        """Start the scheduler loop."""
        self._running = True
        asyncio.create_task(self._worker_loop())
        logger.info("TaskScheduler started (max_concurrent=%d)", self._max_concurrent)

    async def stop(self) -> None:
        """Stop the scheduler loop."""
        self._running = False
        self._executor.shutdown(wait=False)
        # Clean up Kafka producer
        if self._kafka_producer is not None:
            try:
                await self._kafka_producer.stop()
            except Exception:
                logger.exception("Error stopping Kafka producer")
            self._kafka_producer = None
        logger.info("TaskScheduler stopped")

    async def submit(
        self,
        algorithm_id: str,
        params: dict[str, Any],
        priority: int = 0,
        callback_topic: Optional[str] = None,
    ) -> str:
        """Submit a new task and return its *task_id*.

        Higher *priority* values are scheduled first.
        """
        task_id = str(uuid.uuid4())
        status = TaskStatus(
            task_id=task_id,
            algorithm_id=algorithm_id,
            status=TaskStatusEnum.PENDING,
        )
        self._tasks[task_id] = status
        await self._save_task(task_id, status.model_dump())
        await self._priority_queue.put((-priority, task_id, {
            "algorithm_id": algorithm_id,
            "params": params,
            "callback_topic": callback_topic,
        }))
        logger.info("Task submitted: %s (algorithm=%s, priority=%d)", task_id, algorithm_id, priority)
        return task_id

    async def get_status(self, task_id: str) -> TaskStatus | None:
        """Return the current status of a task."""
        if task_id in self._tasks:
            return self._tasks[task_id]
        data = await self._load_task(task_id)
        if data:
            return TaskStatus(**data)
        return None

    async def get_result(self, task_id: str) -> dict[str, Any] | None:
        """Return the result of a completed task, or ``None``."""
        if task_id in self._results:
            return self._results[task_id]
        data = await self._load_result(task_id)
        if data:
            return data
        return None

    async def cancel(self, task_id: str) -> bool:
        """Cancel a pending or running task.  Returns ``True`` if successful."""
        status = self._tasks.get(task_id)
        if status is None:
            return False
        if status.status in (TaskStatusEnum.SUCCESS, TaskStatusEnum.FAILED, TaskStatusEnum.CANCELLED):
            return False
        status.status = TaskStatusEnum.CANCELLED
        status.completed_at = datetime.now(timezone.utc)
        await self._save_task(task_id, status.model_dump())
        future = self._futures.get(task_id)
        if future and not future.done():
            future.cancel()
        logger.info("Task cancelled: %s", task_id)
        return True

    async def list_tasks(
        self,
        status: Optional[TaskStatusEnum] = None,
        limit: int = 50,
    ) -> list[TaskStatus]:
        """List tasks, optionally filtered by *status*."""
        tasks = list(self._tasks.values())
        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)[:limit]

    async def _worker_loop(self) -> None:
        """Pull tasks from the priority queue and execute them."""
        while self._running:
            try:
                _, task_id, payload = await asyncio.wait_for(
                    self._priority_queue.get(), timeout=1.0
                )
            except asyncio.TimeoutError:
                continue
            asyncio.create_task(self._execute_task(task_id, payload))

    async def _execute_task(self, task_id: str, payload: dict[str, Any]) -> None:
        """Execute a single task inside the semaphore."""
        async with self._semaphore:
            status = self._tasks.get(task_id)
            if status is None or status.status == TaskStatusEnum.CANCELLED:
                return
            status.status = TaskStatusEnum.RUNNING
            await self._save_task(task_id, status.model_dump())
            try:
                from app.core.registry import get_registry
                registry = get_registry()
                algo_cls = registry.get(payload["algorithm_id"])
                if algo_cls is None:
                    raise ValueError(f"Algorithm not found: {payload['algorithm_id']}")
                adapter = algo_cls()
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(self._executor, adapter.execute, payload["params"]),
                    timeout=self._task_timeout,
                )
                status.status = TaskStatusEnum.SUCCESS
                status.result = result
                self._results[task_id] = result
                await self._save_result(task_id, result)
            except asyncio.CancelledError:
                status.status = TaskStatusEnum.CANCELLED
                status.error = "Task was cancelled"
            except Exception as exc:
                status.status = TaskStatusEnum.FAILED
                status.error = str(exc)
                logger.exception("Task %s failed", task_id)
            finally:
                status.completed_at = datetime.now(timezone.utc)
                await self._save_task(task_id, status.model_dump())
                # Send Kafka result notification if callback_topic is set
                callback_topic = payload.get("callback_topic")
                if callback_topic:
                    await self._send_kafka_result(
                        callback_topic,
                        task_id=task_id,
                        algorithm_id=payload.get("algorithm_id", ""),
                        status_value=status.status.value,
                        result=status.result if status.status == TaskStatusEnum.SUCCESS else None,
                        error=status.error,
                    )

    async def _save_task(self, task_id: str, data: dict[str, Any]) -> None:
        if self._redis:
            await self._redis.set(
                f"task:{task_id}", json.dumps(data, default=str), ex=self._task_ttl
            )

    async def _load_task(self, task_id: str) -> dict[str, Any] | None:
        if self._redis:
            raw = await self._redis.get(f"task:{task_id}")
            if raw:
                return json.loads(raw)
        return None

    async def _save_result(self, task_id: str, data: dict[str, Any]) -> None:
        if self._redis:
            await self._redis.set(
                f"result:{task_id}", json.dumps(data, default=str), ex=self._task_ttl
            )

    async def _load_result(self, task_id: str) -> dict[str, Any] | None:
        if self._redis:
            raw = await self._redis.get(f"result:{task_id}")
            if raw:
                return json.loads(raw)
        return None

    async def _get_kafka_producer(self):
        """Return a lazily-initialized KafkaTaskProducer.

        If the producer cannot be created (e.g. Kafka is unavailable),
        returns ``None`` so that task execution can continue with Redis only.
        """
        if self._kafka_producer is not None:
            return self._kafka_producer
        try:
            from app.transport.kafka_producer import KafkaTaskProducer
            producer = KafkaTaskProducer(
                bootstrap_servers=self._kafka_bootstrap_servers,
            )
            await producer.start()
            self._kafka_producer = producer
            logger.info("Kafka producer initialized (servers=%s)", self._kafka_bootstrap_servers)
            return self._kafka_producer
        except Exception as exc:
            logger.warning(
                "Failed to initialize Kafka producer, "
                "falling back to Redis-only mode: %s",
                exc,
            )
            return None

    async def _send_kafka_result(
        self,
        topic: str,
        *,
        task_id: str,
        algorithm_id: str,
        status_value: str,
        result: Any = None,
        error: Optional[str] = None,
    ) -> None:
        """Send a task-result message to the specified Kafka *topic*.

        Failures are silently logged so that Kafka unavailability never
        blocks or breaks task execution.
        """
        producer = await self._get_kafka_producer()
        if producer is None:
            return
        message = {
            "task_id": task_id,
            "algorithm_id": algorithm_id,
            "status": status_value,
            "result": result,
            "error": error,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "progress": 100 if status_value == "SUCCESS" else 0,
        }
        try:
            await producer.send_to_topic(topic, message, key=task_id)
            logger.debug(
                "Kafka result sent: task=%s status=%s topic=%s",
                task_id, status_value, topic,
            )
        except Exception as exc:
            logger.error(
                "Failed to send Kafka result for task %s to topic %s: %s",
                task_id, topic, exc,
            )
