"""Kafka consumer for receiving algorithm results."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Coroutine, Optional

from aiokafka import AIOKafkaConsumer

logger = logging.getLogger(__name__)

MessageHandler = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


class KafkaResultConsumer:
    """Async Kafka consumer for algorithm result messages.

    Message format (topic ``uav.algorithm.results``)::

        {
            "task_id": "uuid",
            "algorithm_id": "string",
            "status": "success|failed",
            "result": {...},
            "error": "string|null",
            "completed_at": "ISO-8601"
        }
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        topic: str = "uav.algorithm.results",
        group_id: str = "algorithm-engine-group",
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._group_id = group_id
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._handlers: list[MessageHandler] = []

    def on_message(self, handler: MessageHandler) -> None:
        """Register a callback for incoming result messages."""
        self._handlers.append(handler)

    async def start(self) -> None:
        """Initialize and start the Kafka consumer."""
        consumer = AIOKafkaConsumer(
            self._topic,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )
        await consumer.start()
        self._consumer = consumer
        logger.info(
            "KafkaResultConsumer started "
            "(servers=%s, topic=%s, group=%s)",
            self._bootstrap_servers,
            self._topic,
            self._group_id,
        )

    async def stop(self) -> None:
        """Stop the consumer."""
        if self._consumer:
            await self._consumer.stop()
            logger.info("KafkaResultConsumer stopped")

    async def consume(self) -> None:
        """Consume messages in a loop.  Blocks until cancelled."""
        if self._consumer is None:
            raise RuntimeError("Consumer not started. Call start() first.")
        async for message in self._consumer:
            raw = message.value
            data: dict[str, Any] = raw if isinstance(raw, dict) else {}
            logger.debug(
                "Received result: task_id=%s, status=%s",
                data.get("task_id"), data.get("status"),
            )
            for handler in self._handlers:
                try:
                    await handler(data)
                except Exception:
                    logger.exception(
                        "Handler error for task_id=%s",
                        data.get("task_id"),
                    )
