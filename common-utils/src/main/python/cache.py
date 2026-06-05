"""
Shared thread-safe cache with TTL expiration and LRU-like eviction.

Provides a simple, thread-safe in-memory cache used across multiple services.
Entries automatically expire after a configurable TTL (time-to-live).
Eviction uses dict insertion order (Python 3.7+) to remove the oldest entry
when the cache reaches its maximum size.


Usage:
    from common_utils.cache import Cache

    cache = Cache(max_size=500, default_ttl_seconds=300)
    cache.set("key", value)
    value = cache.get("key")
"""

import time
import threading
from typing import Any, Optional


class Cache:
    """Thread-safe bounded cache with TTL expiration and oldest-entry eviction."""

    def __init__(self, max_size: int = 1000, default_ttl_seconds: Optional[int] = None) -> None:
        """
        Initialize the cache.

        Args:
            max_size: Maximum number of entries before eviction.
            default_ttl_seconds: Default time-to-live in seconds.
                                 If None, entries never expire by time.
        """
        self.max_size = max_size
        self.default_ttl = default_ttl_seconds
        self._cache: dict = {}
        self._expiry: dict = {}
        self._lock = threading.Lock()

    def get(self, key: Any) -> Optional[Any]:
        """Get value by key. Returns None if missing or expired."""
        with self._lock:
            self._evict_expired()
            return self._cache.get(key)

    def set(self, key: Any, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Set a cache entry with optional per-key TTL.

        Args:
            key: Cache key.
            value: Value to store.
            ttl_seconds: Time-to-live in seconds for this specific entry.
                         Falls back to default_ttl if None.
        """
        with self._lock:
            if key not in self._cache and len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._expiry.pop(oldest_key, None)
            self._cache[key] = value
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
            if ttl is not None:
                self._expiry[key] = time.time() + ttl
            else:
                self._expiry.pop(key, None)

    def delete(self, key: Any) -> None:
        """Remove a specific key from the cache."""
        with self._lock:
            self._cache.pop(key, None)
            self._expiry.pop(key, None)

    def clear(self) -> None:
        """Remove all entries from the cache."""
        with self._lock:
            self._cache.clear()
            self._expiry.clear()

    def _evict_expired(self) -> None:
        """Remove all expired entries (caller must hold lock)."""
        now = time.time()
        expired = [k for k, t in self._expiry.items() if t <= now]
        for k in expired:
            del self._cache[k]
            del self._expiry[k]

    def __len__(self) -> int:
        with self._lock:
            self._evict_expired()
            return len(self._cache)

    def __contains__(self, key: Any) -> bool:
        with self._lock:
            self._evict_expired()
            return key in self._cache
