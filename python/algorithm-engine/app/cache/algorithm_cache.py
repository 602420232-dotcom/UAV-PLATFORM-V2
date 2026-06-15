"""算法推理结果缓存.

基于 TTL（Time-To-Live）的缓存机制，按算法类型和参数哈希缓存推理结果，
避免重复计算，提升算法引擎的响应速度。

支持功能：
- 按 algorithm_id + params_hash 缓存结果
- 可配置 TTL（默认 5 分钟）
- 缓存命中率统计
- 内存上限控制
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from collections import OrderedDict
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AlgorithmCacheEntry:
    """缓存条目."""

    __slots__ = ("value", "expires_at", "created_at", "algorithm_id", "params_hash")

    def __init__(
        self,
        value: Any,
        ttl_seconds: float,
        algorithm_id: str,
        params_hash: str,
    ) -> None:
        self.value = value
        self.created_at = time.monotonic()
        self.expires_at = self.created_at + ttl_seconds
        self.algorithm_id = algorithm_id
        self.params_hash = params_hash

    @property
    def is_expired(self) -> bool:
        """检查缓存条目是否已过期."""
        return time.monotonic() > self.expires_at

    @property
    def remaining_ttl(self) -> float:
        """返回剩余 TTL（秒）."""
        return max(0.0, self.expires_at - time.monotonic())


class AlgorithmCache:
    """算法推理结果缓存.

    基于 OrderedDict 实现的 LRU + TTL 缓存，支持按算法类型和参数
    哈希进行精确匹配缓存。

    Usage::

        cache = AlgorithmCache(default_ttl=300, max_size=1000)

        # 存储结果
        cache.put("gp_regression", params, result)

        # 获取结果
        cached = cache.get("gp_regression", params)
        if cached is not None:
            return cached

        # 查看统计
        stats = cache.get_stats()
    """

    def __init__(
        self,
        default_ttl: float = 300.0,
        max_size: int = 1000,
    ) -> None:
        """初始化缓存.

        Args:
            default_ttl: 默认 TTL（秒），默认 300 秒（5 分钟）.
            max_size: 最大缓存条目数，默认 1000.
        """
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._cache: OrderedDict[str, AlgorithmCacheEntry] = OrderedDict()
        self._lock = threading.Lock()

        # 统计计数器
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._puts = 0

        logger.info(
            "算法缓存初始化: default_ttl=%.1fs, max_size=%d",
            default_ttl,
            max_size,
        )

    @staticmethod
    def _compute_params_hash(params: dict[str, Any]) -> str:
        """计算参数字典的哈希值.

        将参数字典序列化为 JSON 后计算 MD5 哈希，
        确保相同参数产生相同的哈希值。

        Args:
            params: 算法参数字典.

        Returns:
            MD5 哈希字符串（32 位十六进制）.
        """
        # 对 numpy 数组等不可序列化对象进行转换
        def _serialize(obj: Any) -> Any:
            if hasattr(obj, "tolist"):
                return obj.tolist()
            if hasattr(obj, "shape"):
                return obj.tolist()
            return obj

        try:
            serialized = json.dumps(
                params,
                default=_serialize,
                sort_keys=True,
                ensure_ascii=False,
            )
        except (TypeError, ValueError):
            # 回退：使用 str 表示
            serialized = str(sorted(params.items()))

        return hashlib.md5(serialized.encode("utf-8")).hexdigest()

    def _make_key(self, algorithm_id: str, params_hash: str) -> str:
        """生成缓存键."""
        return f"{algorithm_id}:{params_hash}"

    def get(
        self,
        algorithm_id: str,
        params: dict[str, Any],
    ) -> Optional[Any]:
        """从缓存获取算法推理结果.

        Args:
            algorithm_id: 算法标识符.
            params: 算法参数字典.

        Returns:
            缓存的结果，如果未命中或已过期则返回 None.
        """
        params_hash = self._compute_params_hash(params)
        key = self._make_key(algorithm_id, params_hash)

        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                logger.debug(
                    "缓存未命中: algorithm_id=%s, key=%s",
                    algorithm_id,
                    key[:16],
                )
                return None

            if entry.is_expired:
                # 过期条目：删除并计为未命中
                del self._cache[key]
                self._misses += 1
                logger.debug(
                    "缓存过期: algorithm_id=%s, key=%s",
                    algorithm_id,
                    key[:16],
                )
                return None

            # 命中：移到末尾（LRU）
            self._cache.move_to_end(key)
            self._hits += 1
            logger.debug(
                "缓存命中: algorithm_id=%s, key=%s, remaining_ttl=%.1fs",
                algorithm_id,
                key[:16],
                entry.remaining_ttl,
            )
            return entry.value

    def put(
        self,
        algorithm_id: str,
        params: dict[str, Any],
        result: Any,
        ttl: Optional[float] = None,
    ) -> None:
        """存储算法推理结果到缓存.

        Args:
            algorithm_id: 算法标识符.
            params: 算法参数字典.
            result: 推理结果.
            ttl: 缓存 TTL（秒），None 则使用默认值.
        """
        params_hash = self._compute_params_hash(params)
        key = self._make_key(algorithm_id, params_hash)
        effective_ttl = ttl if ttl is not None else self._default_ttl

        with self._lock:
            # 如果已存在则先删除（更新）
            if key in self._cache:
                del self._cache[key]

            # LRU 淘汰：超出容量时删除最旧的条目
            while len(self._cache) >= self._max_size:
                evicted_key, evicted_entry = self._cache.popitem(last=False)
                self._evictions += 1
                logger.debug(
                    "LRU 淘汰: algorithm_id=%s, key=%s",
                    evicted_entry.algorithm_id,
                    evicted_key[:16],
                )

            entry = AlgorithmCacheEntry(
                value=result,
                ttl_seconds=effective_ttl,
                algorithm_id=algorithm_id,
                params_hash=params_hash,
            )
            self._cache[key] = entry
            self._puts += 1

            logger.debug(
                "缓存写入: algorithm_id=%s, key=%s, ttl=%.1fs",
                algorithm_id,
                key[:16],
                effective_ttl,
            )

    def invalidate(self, algorithm_id: str) -> int:
        """使指定算法的所有缓存条目失效.

        Args:
            algorithm_id: 算法标识符.

        Returns:
            被失效的条目数.
        """
        prefix = f"{algorithm_id}:"
        count = 0

        with self._lock:
            keys_to_remove = [
                k for k in self._cache if k.startswith(prefix)
            ]
            for key in keys_to_remove:
                del self._cache[key]
                count += 1

        if count > 0:
            logger.info(
                "缓存失效: algorithm_id=%s, count=%d",
                algorithm_id,
                count,
            )
        return count

    def clear(self) -> None:
        """清空所有缓存."""
        with self._lock:
            self._cache.clear()
            logger.info("缓存已清空")

    def cleanup_expired(self) -> int:
        """清理所有过期条目.

        Returns:
            被清理的条目数.
        """
        count = 0
        with self._lock:
            expired_keys = [
                k for k, v in self._cache.items() if v.is_expired
            ]
            for key in expired_keys:
                del self._cache[key]
                count += 1

        if count > 0:
            logger.info("清理过期缓存: %d 条", count)
        return count

    def get_stats(self) -> dict[str, Any]:
        """获取缓存统计信息.

        Returns:
            缓存统计字典:
                - hits: 命中次数
                - misses: 未命中次数
                - hit_rate: 命中率
                - puts: 写入次数
                - evictions: 淘汰次数
                - size: 当前缓存条目数
                - max_size: 最大容量
                - default_ttl: 默认 TTL
                - algorithm_stats: 按算法分类的统计
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0

            # 按算法分类统计
            algo_stats: dict[str, int] = {}
            for entry in self._cache.values():
                algo_stats[entry.algorithm_id] = (
                    algo_stats.get(entry.algorithm_id, 0) + 1
                )

            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 4),
                "puts": self._puts,
                "evictions": self._evictions,
                "size": len(self._cache),
                "max_size": self._max_size,
                "default_ttl": self._default_ttl,
                "algorithm_stats": algo_stats,
            }

    def get_or_compute(
        self,
        algorithm_id: str,
        params: dict[str, Any],
        compute_fn,
        ttl: Optional[float] = None,
    ) -> Any:
        """尝试从缓存获取，未命中时调用计算函数并缓存结果.

        Args:
            algorithm_id: 算法标识符.
            params: 算法参数字典.
            compute_fn: 无参数的可调用对象，执行实际推理计算.
            ttl: 缓存 TTL（秒），None 则使用默认值.

        Returns:
            推理结果（缓存或新计算）.
        """
        cached = self.get(algorithm_id, params)
        if cached is not None:
            return cached

        result = compute_fn()
        self.put(algorithm_id, params, result, ttl=ttl)
        return result


# 全局单例缓存实例
_global_cache: Optional[AlgorithmCache] = None


def get_algorithm_cache() -> AlgorithmCache:
    """获取全局算法缓存实例.

    Returns:
        全局 AlgorithmCache 单例.
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = AlgorithmCache(default_ttl=300.0, max_size=1000)
    return _global_cache
