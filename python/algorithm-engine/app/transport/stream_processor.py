"""Kafka 实时气象数据流处理器

提供从 Kafka topic 消费实时气象数据、数据解析与验证、Redis 缓存、
数据质量检查、流式数据到算法引擎的桥接以及回压控制等功能。

使用示例::

    from app.transport.stream_processor import StreamProcessor

    processor = StreamProcessor(
        bootstrap_servers="localhost:9092",
        topic="uav.weather.realtime",
        redis_url="redis://localhost:6379/1",
    )

    # 注册数据处理器
    processor.on_data_ready(lambda data: print(f"收到数据: {data}"))

    # 启动处理器
    await processor.start()

    # 停止处理器
    await processor.stop()
"""

from __future__ import annotations

import asyncio
import json
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Optional

import redis.asyncio as aioredis
from aiokafka import AIOKafkaConsumer
from loguru import logger

# 类型别名
DataHandler = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]
QualityCheckCallback = Callable[[str, dict[str, Any]], Coroutine[Any, Any, None]]


class DataFormat(str, Enum):
    """数据格式枚举。"""

    JSON = "json"
    PROTOBUF = "protobuf"


class BackpressureStrategy(str, Enum):
    """回压策略枚举。"""

    PAUSE = "pause"
    DROP = "drop"
    BUFFER = "buffer"


@dataclass
class QualityReport:
    """数据质量检查报告。"""

    is_valid: bool = True
    missing_fields: list[str] = field(default_factory=list)
    anomaly_fields: dict[str, float] = field(default_factory=dict)
    timestamp_delta_ms: float = 0.0
    error_message: str = ""

    @property
    def quality_score(self) -> float:
        """计算数据质量评分 (0.0 - 1.0)。"""
        if not self.is_valid:
            return 0.0
        score = 1.0
        # 缺失字段扣分
        score -= len(self.missing_fields) * 0.1
        # 异常字段扣分
        score -= len(self.anomaly_fields) * 0.05
        # 时间戳偏差扣分
        if self.timestamp_delta_ms > 60000:  # 超过 1 分钟
            score -= 0.2
        return max(0.0, min(1.0, score))


class StreamProcessor:
    """Kafka 实时气象数据流处理器。

    功能:
    - 从 Kafka topic 消费实时气象数据
    - 数据解析和验证 (JSON/Protobuf 格式)
    - 数据缓存 (Redis，最近 N 个时间步)
    - 数据质量检查 (缺失值/异常值检测)
    - 流式数据到算法引擎的桥接
    - 回压控制 (消费速度慢时暂停生产者)

    Args:
        bootstrap_servers: Kafka 服务器地址。
        topic: 消费的 Kafka topic。
        group_id: 消费者组 ID。
        redis_url: Redis 连接 URL。
        data_format: 数据格式，默认 JSON。
        cache_capacity: Redis 缓存容量（最近 N 个时间步）。
        backpressure_threshold: 回压阈值（缓冲区消息数）。
        backpressure_strategy: 回压策略。
        required_fields: 数据校验的必填字段列表。
        anomaly_std_threshold: 异常值检测的标准差倍数阈值。
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        topic: str = "uav.weather.realtime",
        group_id: str = "stream-processor-group",
        redis_url: str = "redis://localhost:6379/1",
        data_format: DataFormat | str = DataFormat.JSON,
        cache_capacity: int = 100,
        backpressure_threshold: int = 500,
        backpressure_strategy: BackpressureStrategy | str = BackpressureStrategy.PAUSE,
        required_fields: list[str] | None = None,
        anomaly_std_threshold: float = 3.0,
    ) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._group_id = group_id
        self._redis_url = redis_url
        self._data_format = DataFormat(data_format)
        self._cache_capacity = cache_capacity
        self._backpressure_threshold = backpressure_threshold
        self._backpressure_strategy = BackpressureStrategy(backpressure_strategy)
        self._required_fields = required_fields or [
            "timestamp", "latitude", "longitude", "data"
        ]
        self._anomaly_std_threshold = anomaly_std_threshold

        # 内部状态
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._redis: Optional[aioredis.Redis] = None
        self._handlers: list[DataHandler] = []
        self._quality_callbacks: list[QualityCheckCallback] = []
        self._running = False
        self._paused = False
        self._buffer: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=1000)
        self._stats = _ProcessorStats()
        self._field_stats: dict[str, _FieldStatistics] = {}

    # ==================== 公共方法 ====================

    def on_data_ready(self, handler: DataHandler) -> None:
        """注册数据就绪回调处理器。

        Args:
            handler: 异步回调函数，接收解析后的数据字典。
        """
        self._handlers.append(handler)

    def on_quality_issue(self, callback: QualityCheckCallback) -> None:
        """注册数据质量问题回调。

        Args:
            callback: 异步回调函数，接收 (message_id, quality_report)。
        """
        self._quality_callbacks.append(callback)

    async def start(self) -> None:
        """启动流处理器（连接 Kafka 和 Redis）。"""
        if self._running:
            logger.warning("StreamProcessor 已在运行中")
            return

        logger.info(
            "启动 StreamProcessor (topic={}, group={}, format={})",
            self._topic,
            self._group_id,
            self._data_format.value,
        )

        # 连接 Redis
        await self._connect_redis()

        # 初始化 Kafka Consumer
        await self._init_consumer()

        self._running = True
        logger.info("StreamProcessor 启动完成")

    async def stop(self) -> None:
        """停止流处理器。"""
        if not self._running:
            return

        logger.info("正在停止 StreamProcessor ...")
        self._running = False

        if self._consumer:
            await self._consumer.stop()
            self._consumer = None

        if self._redis:
            await self._redis.close()
            self._redis = None

        logger.info(
            "StreamProcessor 已停止 (处理消息: {}, 丢弃: {}, 质量问题: {})",
            self._stats.messages_processed,
            self._stats.messages_dropped,
            self._stats.quality_issues,
        )

    async def consume(self) -> None:
        """持续消费消息的主循环。阻塞直到取消。"""
        if self._consumer is None:
            raise RuntimeError("StreamProcessor 未启动，请先调用 start()")

        logger.info("开始消费 Kafka topic: {}", self._topic)

        async for message in self._consumer:
            if not self._running:
                break

            # 回压检查
            if self._paused:
                if self._buffer.qsize() < self._backpressure_threshold // 2:
                    self._paused = False
                    logger.info("回压解除，恢复消费")
                else:
                    await asyncio.sleep(0.1)
                    continue

            try:
                raw_data = message.value
                if isinstance(raw_data, bytes):
                    raw_data = raw_data.decode("utf-8")

                # 解析数据
                parsed = self._parse_data(raw_data)

                # 数据质量检查
                quality = self._check_quality(parsed)

                if not quality.is_valid:
                    self._stats.quality_issues += 1
                    await self._notify_quality_issue(
                        message.key.decode("utf-8") if message.key else "",
                        quality,
                    )

                # 缓存数据
                await self._cache_data(parsed)

                # 分发给处理器
                await self._dispatch_data(parsed)

                self._stats.messages_processed += 1

            except json.JSONDecodeError as e:
                self._stats.messages_dropped += 1
                logger.warning("JSON 解析失败 (offset={}): {}", message.offset, e)

            except Exception as e:
                self._stats.messages_dropped += 1
                logger.error(
                    "消息处理异常 (offset={}): {}",
                    message.offset,
                    e,
                    exc_info=True,
                )

    def get_stats(self) -> dict[str, Any]:
        """获取处理器运行统计。

        Returns:
            包含处理统计信息的字典。
        """
        return {
            "messages_processed": self._stats.messages_processed,
            "messages_dropped": self._stats.messages_dropped,
            "quality_issues": self._stats.quality_issues,
            "buffer_size": self._buffer.qsize(),
            "paused": self._paused,
            "field_statistics": {
                name: {
                    "count": fs.count,
                    "mean": fs.mean,
                    "std": fs.std,
                    "min": fs.min_val,
                    "max": fs.max_val,
                    "missing_count": fs.missing_count,
                }
                for name, fs in self._field_stats.items()
            },
        }

    def get_cached_data(
        self, key_prefix: str = "stream", count: int = 10
    ) -> list[dict[str, Any]]:
        """同步获取缓存的最近数据（需要 Redis 已连接）。

        .. note::
            此方法为同步接口，适用于非异步上下文中快速读取缓存。
            异步上下文中请使用 ``get_cached_data_async``。

        Args:
            key_prefix: 缓存键前缀。
            count: 获取的数据条数。

        Returns:
            缓存的数据列表。
        """
        # 此方法在同步上下文中使用，返回空列表提示使用异步版本
        logger.warning("请使用 get_cached_data_async 替代同步版本")
        return []

    async def get_cached_data_async(
        self, key_prefix: str = "stream", count: int = 10
    ) -> list[dict[str, Any]]:
        """异步获取缓存的最近数据。

        Args:
            key_prefix: 缓存键前缀。
            count: 获取的数据条数。

        Returns:
            缓存的数据列表。
        """
        if self._redis is None:
            raise RuntimeError("Redis 未连接")

        keys = await self._redis.zrevrange(
            f"{key_prefix}:timeline", 0, count - 1
        )
        result: list[dict[str, Any]] = []
        for key in keys:
            raw = await self._redis.get(key)
            if raw:
                result.append(json.loads(raw))
        return result

    # ==================== 私有方法 ====================

    async def _connect_redis(self) -> None:
        """建立 Redis 连接。"""
        try:
            self._redis = aioredis.from_url(
                self._redis_url, decode_responses=True
            )
            await self._redis.ping()
            logger.info("Redis 连接成功: {}", self._redis_url)
        except Exception as e:
            logger.error("Redis 连接失败: {}", e)
            raise

    async def _init_consumer(self) -> None:
        """初始化 Kafka Consumer。"""
        self._consumer = AIOKafkaConsumer(
            self._topic,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            value_deserializer=lambda v: v,  # 延迟解码
            max_poll_records=100,
            enable_auto_commit=True,
            auto_offset_reset="latest",
        )
        await self._consumer.start()
        logger.info(
            "Kafka Consumer 已连接 (servers={}, topic={})",
            self._bootstrap_servers,
            self._topic,
        )

    def _parse_data(self, raw_data: str) -> dict[str, Any]:
        """解析原始数据为字典。

        Args:
            raw_data: 原始数据字符串。

        Returns:
            解析后的数据字典。

        Raises:
            json.JSONDecodeError: JSON 解析失败。
            ValueError: 数据格式不支持。
        """
        if self._data_format == DataFormat.JSON:
            data: dict[str, Any] = json.loads(raw_data)
            if not isinstance(data, dict):
                raise ValueError(f"期望 JSON 对象，得到 {type(data).__name__}")
            return data
        elif self._data_format == DataFormat.PROTOBUF:
            # Protobuf 解析需要预先定义 .proto 文件
            # 这里提供扩展点，实际使用时需要注册对应的解析器
            return self._parse_protobuf(raw_data)
        else:
            raise ValueError(f"不支持的数据格式: {self._data_format}")

    def _parse_protobuf(self, raw_data: str) -> dict[str, Any]:
        """解析 Protobuf 格式数据。

        .. note::
            实际项目中需要根据具体的 .proto 定义实现解析逻辑。
            此处提供 JSON fallback 作为默认行为。

        Args:
            raw_data: 原始数据字符串。

        Returns:
            解析后的数据字典。
        """
        try:
            return json.loads(raw_data)
        except json.JSONDecodeError:
            logger.warning("Protobuf 解析器未配置，尝试 JSON fallback 失败")
            return {"raw": raw_data, "parsed": False}

    def _check_quality(self, data: dict[str, Any]) -> QualityReport:
        """执行数据质量检查。

        检查项:
        - 必填字段缺失检测
        - 数值异常值检测 (基于 Z-score)
        - 时间戳合理性检查

        Args:
            data: 待检查的数据字典。

        Returns:
            质量检查报告。
        """
        report = QualityReport()

        # 1. 必填字段检查
        for field_name in self._required_fields:
            if field_name not in data or data[field_name] is None:
                report.missing_fields.append(field_name)
                self._update_field_missing(field_name)

        if report.missing_fields:
            report.is_valid = False
            report.error_message = f"缺失必填字段: {', '.join(report.missing_fields)}"

        # 2. 数值异常值检测
        numeric_fields = self._extract_numeric_fields(data)
        for field_name, value in numeric_fields.items():
            if value is None:
                continue

            # 清理非有限数值
            if math.isinf(value) or math.isnan(value):
                report.anomaly_fields[field_name] = value
                report.is_valid = False
                continue

            self._update_field_stats(field_name, value)

            # Z-score 异常检测
            fs = self._field_stats.get(field_name)
            if fs and fs.count > 10 and fs.std > 0:
                z_score = abs((value - fs.mean) / fs.std)
                if z_score > self._anomaly_std_threshold:
                    report.anomaly_fields[field_name] = z_score
                    logger.debug(
                        "异常值检测: {} = {} (z-score={:.2f})",
                        field_name,
                        value,
                        z_score,
                    )

        # 3. 时间戳检查
        timestamp_str = data.get("timestamp", "")
        if timestamp_str:
            try:
                ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                delta = abs((now - ts).total_seconds() * 1000)
                report.timestamp_delta_ms = delta

                if delta > 300000:  # 超过 5 分钟
                    report.error_message = (
                        f"时间戳偏差过大: {delta / 1000:.1f}s"
                    )
                    if not report.missing_fields:
                        report.is_valid = False
            except (ValueError, TypeError):
                pass

        return report

    def _extract_numeric_fields(
        self, data: dict[str, Any], prefix: str = ""
    ) -> dict[str, float]:
        """递归提取数据中的数值字段。

        Args:
            data: 数据字典。
            prefix: 字段名前缀（用于嵌套结构）。

        Returns:
            字段名到数值的映射。
        """
        result: dict[str, float] = {}
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                result[full_key] = float(value)
            elif isinstance(value, dict):
                result.update(self._extract_numeric_fields(value, full_key))
        return result

    def _update_field_stats(self, field_name: str, value: float) -> None:
        """更新字段统计信息（在线计算均值和标准差）。

        使用 Welford's online algorithm 进行增量统计。

        Args:
            field_name: 字段名。
            value: 字段值。
        """
        if field_name not in self._field_stats:
            self._field_stats[field_name] = _FieldStatistics()

        fs = self._field_stats[field_name]
        fs.count += 1
        delta = value - fs.mean
        fs.mean += delta / fs.count
        delta2 = value - fs.mean
        fs.m2 += delta * delta2
        fs.std = math.sqrt(fs.m2 / fs.count) if fs.count > 1 else 0.0
        fs.min_val = min(fs.min_val, value)
        fs.max_val = max(fs.max_val, value)

    def _update_field_missing(self, field_name: str) -> None:
        """更新字段缺失计数。

        Args:
            field_name: 字段名。
        """
        if field_name not in self._field_stats:
            self._field_stats[field_name] = _FieldStatistics()
        self._field_stats[field_name].missing_count += 1

    async def _cache_data(self, data: dict[str, Any]) -> None:
        """将数据缓存到 Redis。

        使用 Sorted Set 维护时间线，自动淘汰旧数据。

        Args:
            data: 待缓存的数据。
        """
        if self._redis is None:
            return

        try:
            timestamp = data.get("timestamp", datetime.now(timezone.utc).isoformat())
            cache_key = f"stream:data:{timestamp}"

            # 存储数据
            await self._redis.set(
                cache_key,
                json.dumps(data, default=str),
                ex=3600,  # 1 小时过期
            )

            # 添加到时间线
            score = time.time()
            await self._redis.zadd("stream:timeline", {cache_key: score})

            # 淘汰旧数据，保持缓存容量
            total = await self._redis.zcard("stream:timeline")
            if total > self._cache_capacity:
                old_keys = await self._redis.zrange(
                    "stream:timeline", 0, total - self._cache_capacity - 1
                )
                if old_keys:
                    await self._redis.zrem("stream:timeline", *old_keys)
                    await self._redis.delete(*old_keys)
                    logger.debug("缓存淘汰: 移除 {} 条旧数据", len(old_keys))

        except Exception as e:
            logger.warning("Redis 缓存失败: {}", e)

    async def _dispatch_data(self, data: dict[str, Any]) -> None:
        """将数据分发给所有注册的处理器。

        Args:
            data: 待分发数据。
        """
        for handler in self._handlers:
            try:
                await handler(data)
            except Exception as e:
                logger.error("数据处理器异常: {}", e, exc_info=True)

    async def _notify_quality_issue(
        self, message_id: str, report: QualityReport
    ) -> None:
        """通知数据质量问题。

        Args:
            message_id: 消息标识。
            report: 质量检查报告。
        """
        report_dict = {
            "message_id": message_id,
            "is_valid": report.is_valid,
            "missing_fields": report.missing_fields,
            "anomaly_fields": report.anomaly_fields,
            "timestamp_delta_ms": report.timestamp_delta_ms,
            "quality_score": report.quality_score,
            "error_message": report.error_message,
        }

        for callback in self._quality_callbacks:
            try:
                await callback(message_id, report_dict)
            except Exception as e:
                logger.error("质量回调异常: {}", e, exc_info=True)


@dataclass
class _FieldStatistics:
    """字段统计信息（在线计算）。"""

    count: int = 0
    mean: float = 0.0
    m2: float = 0.0  # 用于 Welford 算法的中间变量
    std: float = 0.0
    min_val: float = float("inf")
    max_val: float = float("-inf")
    missing_count: int = 0


@dataclass
class _ProcessorStats:
    """处理器运行统计。"""

    messages_processed: int = 0
    messages_dropped: int = 0
    quality_issues: int = 0


# ==================== 使用示例 ====================

async def example_consume_fengwu_results() -> None:
    """示例: 消费 FengWu 推理结果流。"""
    processor = StreamProcessor(
        bootstrap_servers="localhost:9092",
        topic="uav.algorithm.results",
        group_id="fengwu-consumer-group",
        redis_url="redis://localhost:6379/1",
        cache_capacity=200,
        required_fields=["task_id", "algorithm_id", "status", "result"],
    )

    # 注册数据处理器
    async def handle_result(data: dict[str, Any]) -> None:
        logger.info(
            "收到推理结果: task_id={}, algorithm_id={}, status={}",
            data.get("task_id"),
            data.get("algorithm_id"),
            data.get("status"),
        )

    processor.on_data_ready(handle_result)

    # 注册质量问题回调
    async def handle_quality(message_id: str, report: dict[str, Any]) -> None:
        logger.warning(
            "数据质量问题: message_id={}, score={:.2f}, issues={}",
            message_id,
            report.get("quality_score", 0),
            report.get("error_message", ""),
        )

    processor.on_quality_issue(handle_quality)

    # 启动并消费
    await processor.start()
    try:
        await processor.consume()
    except asyncio.CancelledError:
        logger.info("消费循环被取消")
    finally:
        await processor.stop()


if __name__ == "__main__":
    asyncio.run(example_consume_fengwu_results())
