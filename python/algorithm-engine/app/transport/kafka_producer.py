"""Kafka producer for sending algorithm tasks."""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timezone
from typing import Any, Optional

from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)


def _sanitize_value(obj: Any) -> Any:
    """Recursively sanitize a value for JSON serialization.

    Replaces non-finite floats (inf, nan) with None so that Java
    Jackson can deserialize the message without errors.
    """
    if isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize_value(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_value(item) for item in obj]
    return obj


def _value_serializer(v: Any) -> bytes:
    """Serialize a value to JSON bytes, sanitizing non-finite floats."""
    return json.dumps(_sanitize_value(v), default=str).encode("utf-8")


class KafkaTaskProducer:
    """Async Kafka producer for publishing algorithm task messages.

    Message format (topic ``uav.algorithm.tasks``)::

        {
            "task_id": "uuid",
            "algorithm_id": "string",
            "params": {...},
            "timestamp": "ISO-8601",
            "priority": 0
        }
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        topic: str = "uav.algorithm.tasks",
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._producer: Optional[AIOKafkaProducer] = None

    async def start(self) -> None:
        """Initialize and start the Kafka producer."""
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._bootstrap_servers,
            value_serializer=_value_serializer,
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
        await self._producer.start()
        logger.info(
            "KafkaTaskProducer started (servers=%s, topic=%s)",
            self._bootstrap_servers,
            self._topic,
        )

    async def stop(self) -> None:
        """Stop and clean up the producer."""
        if self._producer:
            await self._producer.stop()
            logger.info("KafkaTaskProducer stopped")

    async def send_task(
        self,
        task_id: str,
        algorithm_id: str,
        params: dict[str, Any],
        priority: int = 0,
    ) -> None:
        """Publish a task message to the Kafka topic."""
        if self._producer is None:
            raise RuntimeError("Producer not started. Call start() first.")
        message = {
            "task_id": task_id,
            "algorithm_id": algorithm_id,
            "params": params,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "priority": priority,
        }
        await self._producer.send_and_wait(self._topic, value=message, key=task_id)
        logger.debug("Task sent to Kafka: %s (algorithm=%s)", task_id, algorithm_id)

    async def send_to_topic(
        self,
        topic: str,
        message: dict[str, Any],
        key: Optional[str] = None,
    ) -> None:
        """Send an arbitrary message to a specified Kafka topic.

        This is a generic method that can be used for sending results,
        notifications, or any other messages to any topic.

        Args:
            topic: The Kafka topic to send the message to.
            message: The message payload (will be JSON-serialized).
            key: Optional message key for partition routing.
        """
        if self._producer is None:
            raise RuntimeError("Producer not started. Call start() first.")
        await self._producer.send_and_wait(topic, value=message, key=key)
        logger.debug("Message sent to Kafka topic %s (key=%s)", topic, key)
