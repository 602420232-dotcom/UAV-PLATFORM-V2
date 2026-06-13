"""边缘缓存管理器模块。

边缘缓存策略管理，支持 LRU、LFU 和预测性缓存策略，
优化边缘数据访问效率。
"""

from __future__ import annotations

import logging
import time as _time
from collections import OrderedDict
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EdgeCacheManager:
    """边缘缓存管理器。

    管理边缘设备的缓存策略，支持 LRU（最近最少使用）、
    LFU（最不经常使用）和预测性缓存策略。
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.cache_policy = self.config.get("cache_policy", "lru")
        self.max_size = self.config.get("max_size", 100)
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.access_counts: dict[str, int] = {}
        self.access_history: list[str] = []

    def manage(self, params: dict[str, Any]) -> dict[str, Any]:
        """执行缓存管理操作。

        Args:
            params: 缓存管理参数字典，包含：
                - operation: 操作类型，"get"/"put"/"evict"/"stats"，默认 "stats"。
                - key: 缓存键。
                - value: 缓存值（put 操作时使用）。
                - cache_policy: 缓存策略，"lru"/"lfu"/"predictive"，默认 "lru"。
                - max_size: 缓存最大容量，默认 100。

        Returns:
            缓存管理结果字典，包含：
                - cache_status: 缓存状态信息。
                - hit_rate: 缓存命中率。
                - evicted_items: 被驱逐的缓存项列表。
        """
        np.random.seed(42)

        operation = params.get("operation", "stats")
        cache_policy = params.get("cache_policy", self.cache_policy)
        max_size = params.get("max_size", self.max_size)

        t_start = _time.perf_counter()

        evicted_items: list[str] = []
        result_value: Any = None
        hit = False

        if operation == "put":
            key = params.get("key", "")
            value = params.get("value", None)
            if key:
                # 如果缓存已满，执行驱逐
                while len(self.cache) >= max_size and key not in self.cache:
                    evicted_key = self._evict_one(cache_policy)
                    if evicted_key:
                        evicted_items.append(evicted_key)
                        self.cache.pop(evicted_key, None)
                        self.access_counts.pop(evicted_key, None)
                    else:
                        break
                self.cache[key] = value
                self.access_counts[key] = self.access_counts.get(key, 0) + 1
                self.access_history.append(key)
                # LRU: 移到末尾
                self.cache.move_to_end(key)

        elif operation == "get":
            key = params.get("key", "")
            if key and key in self.cache:
                result_value = self.cache[key]
                self.access_counts[key] = self.access_counts.get(key, 0) + 1
                self.access_history.append(key)
                self.cache.move_to_end(key)
                hit = True
            else:
                result_value = None

        elif operation == "evict":
            n_evict = params.get("n_evict", 1)
            for _ in range(n_evict):
                evicted_key = self._evict_one(cache_policy)
                if evicted_key:
                    evicted_items.append(evicted_key)
                    self.cache.pop(evicted_key, None)
                    self.access_counts.pop(evicted_key, None)

        elif operation == "predictive":
            # 预测性缓存：基于访问历史预测可能需要的项
            prediction_keys = self._predict_accesses()
            for key in prediction_keys:
                if len(self.cache) < max_size and key not in self.cache:
                    self.cache[key] = {"predicted": True}
                    self.access_counts[key] = 0

        # 计算命中率
        total_accesses = len(self.access_history)
        if total_accesses > 0:
            hits = sum(1 for k in self.access_history if k in self.cache)
            hit_rate = hits / total_accesses
        else:
            hit_rate = 0.0

        t_end = _time.perf_counter()
        manage_time = (t_end - t_start) * 1000

        result: dict[str, Any] = {
            "cache_status": {
                "size": len(self.cache),
                "max_size": max_size,
                "policy": cache_policy,
                "keys": list(self.cache.keys()),
            },
            "hit_rate": round(hit_rate, 4),
            "evicted_items": evicted_items,
            "manage_time_ms": round(manage_time, 3),
        }

        if operation == "get":
            result["value"] = result_value
            result["hit"] = hit

        return result

    def _evict_one(self, policy: str) -> Optional[str]:
        """根据策略驱逐一个缓存项。"""
        if not self.cache:
            return None

        if policy == "lru":
            # LRU: 驱逐最久未访问的（OrderedDict 最前面的）
            return next(iter(self.cache))
        elif policy == "lfu":
            # LFU: 驱逐访问次数最少的
            return min(self.cache, key=lambda k: self.access_counts.get(k, 0))
        else:
            return next(iter(self.cache))

    def _predict_accesses(self) -> list[str]:
        """基于访问历史预测可能需要的缓存项。"""
        if len(self.access_history) < 2:
            return []

        # 简单的序列预测：找到最近访问的项之后通常访问的项
        predictions: list[str] = []
        recent = self.access_history[-5:] if len(self.access_history) >= 5 else self.access_history

        for i in range(len(recent) - 1):
            next_item = recent[i + 1]
            # 如果不在缓存中，加入预测
            if next_item not in self.cache and next_item not in predictions:
                predictions.append(next_item)

        return predictions[:3]  # 最多预测3个
