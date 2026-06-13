"""Redis cache for task state and algorithm results."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class RedisCache:
    """Async Redis wrapper for caching task state and algorithm results.

    * Task status TTL: 1 hour (configurable)
    * Algorithm results TTL: 1 hour (configurable)
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        task_ttl: int = 3600,
        result_ttl: int = 3600,
    ) -> None:
        self._redis_url = redis_url
        self._task_ttl = task_ttl
        self._result_ttl = result_ttl
        self._redis: Optional[aioredis.Redis] = None

    async def connect(self) -> None:
        """Establish connection to Redis."""
        self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        logger.info("RedisCache connected (%s)", self._redis_url)

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._redis:
            await self._redis.close()
            logger.info("RedisCache closed")

    @property
    def client(self) -> aioredis.Redis:
        if self._redis is None:
            raise RuntimeError("Redis not connected. Call connect() first.")
        return self._redis

    async def set_task_status(self, task_id: str, status: dict[str, Any]) -> None:
        """Cache task status with TTL."""
        await self.client.set(f"task:{task_id}", json.dumps(status, default=str), ex=self._task_ttl)

    async def get_task_status(self, task_id: str) -> Optional[dict[str, Any]]:
        """Retrieve cached task status."""
        raw = await self.client.get(f"task:{task_id}")
        return json.loads(raw) if raw else None

    async def delete_task_status(self, task_id: str) -> None:
        """Remove a task status entry."""
        await self.client.delete(f"task:{task_id}")

    async def set_result(self, task_id: str, result: dict[str, Any]) -> None:
        """Cache algorithm result with TTL."""
        await self.client.set(f"result:{task_id}", json.dumps(result, default=str), ex=self._result_ttl)

    async def get_result(self, task_id: str) -> Optional[dict[str, Any]]:
        """Retrieve cached algorithm result."""
        raw = await self.client.get(f"result:{task_id}")
        return json.loads(raw) if raw else None

    async def ping(self) -> bool:
        """Check Redis connectivity."""
        try:
            return await self.client.ping()
        except Exception:
            return False
