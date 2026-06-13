"""Kafka producer for sending algorithm tasks."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from aiokafka import AIOKafkaProducer

logger = logging.getLogger(__name__)


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
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
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
