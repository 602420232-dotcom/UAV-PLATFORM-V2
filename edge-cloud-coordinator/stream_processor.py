"""
实时数据流处理框架
Kafka + Flink 实现实时气象数据分析和动态路径调整
"""
import logging
import threading
import time
from typing import Callable, List, Optional
from dataclasses import dataclass
from collections import deque
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


@dataclass
class StreamEvent:
    topic: str
    key: str
    data: dict
    timestamp: float
    source: str


class StreamProcessor:
    """实时数据流处理器"""

    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        self.event_buffer = deque(maxlen=10000)
        self.window_sliding = deque(maxlen=window_size)
        self.processors = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.running = False

    def register_processor(self, topic: str, processor_fn: Callable):
        """注册流处理器"""
        self.processors[topic] = processor_fn
        logger.info(f"注册流处理器: {topic}")

    def ingest(self, event: StreamEvent):
        """接收实时事件"""
        self.event_buffer.append(event)
        self.window_sliding.append(event)
        if event.topic in self.processors:
            self.executor.submit(self._process, event)

    def _process(self, event: StreamEvent):
        """处理事件"""
        try:
            result = self.processors[event.topic](event)
            logger.debug(f"处理事件 {event.topic}/{event.key}: {result}")
        except Exception as e:
            logger.error(f"事件处理失败: {e}")

    def window_aggregate(self, topic: Optional[str] = None) -> dict:
        """滑动窗口聚合分析"""
        events = [e for e in self.window_sliding if topic is None or e.topic == topic]
        if not events:
            return {'count': 0}

        values = [e.data.get('value', 0) for e in events if 'value' in e.data]
        return {
            'count': len(events),
            'mean': sum(values) / len(values) if values else 0,
            'max': max(values) if values else 0,
            'min': min(values) if values else 0,
            'window_seconds': self.window_size
        }

    def detect_anomaly(self, events: List[StreamEvent], threshold: float = 3.0) -> List[dict]:
        """异常检测"""
        values = [e.data.get('value', 0) for e in events if 'value' in e.data]
        if len(values) < 10:
            return []

        mean = sum(values) / len(values)
        std = (sum((v - mean)**2 for v in values) / len(values))**0.5 or 1
        anomalies = []
        for e in events:
            v = e.data.get('value', 0)
            if abs(v - mean) > threshold * std:
                anomalies.append({
                    'key': e.key,
                    'value': v,
                    'zscore': abs(v - mean) / std,
                    'timestamp': e.timestamp
                })
        return anomalies

    def dynamic_replan_trigger(self, weather_event: dict) -> bool:
        """判断是否触发动态重规划"""
        wind_speed = weather_event.get('wind_speed', 0)
        wind_gust = weather_event.get('wind_gust', 0)
        turbulence = weather_event.get('turbulence', 0)
        if wind_gust > 15 or wind_speed > 12 or turbulence > 0.8:
            logger.warning(f"气象条件恶化，触发动态重规划: wind={wind_speed}, gust={wind_gust}")
            return True
        return False


class KafkaProducerMock:
    """模拟Kafka生产者"""

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.sent = []

    def send(self, topic: str, key: str, data: dict):
        event = StreamEvent(topic=topic, key=key, data=data,
                           timestamp=time.time(), source='kafka')
        self.sent.append(event)
        logger.info(f"Kafka 发送: {topic}/{key}")
        return event


class FlinkJobManager:
    """Flink 作业管理器（模拟）"""

    def __init__(self):
        self.jobs = {}

    def submit_job(self, name: str, sql: str):
        """提交 Flink SQL 作业"""
        self.jobs[name] = {'sql': sql, 'status': 'running'}
        logger.info(f"Flink 作业提交: {name}")

    def streaming_etl(self, source_topic: str, sink_topic: str, transform_fn: Callable):
        """流式ETL"""

        def _run():
            logger.info(f"启动流式ETL: {source_topic} -> {sink_topic}")
            while True:
                time.sleep(1)
        threading.Thread(target=_run, daemon=True).start()

    def real_time_risk_analysis(self):
        """实时风险分析"""
        sql = """
        INSERT INTO risk_alerts
        SELECT
            drone_id,
            AVG(wind_speed) AS avg_wind,
            MAX(wind_gust) AS max_gust,
            CASE
                WHEN AVG(wind_speed) > 12 THEN 'HIGH'
                WHEN AVG(wind_speed) > 8 THEN 'MEDIUM'
                ELSE 'LOW'
            END AS risk_level
        FROM weather_stream
        GROUP BY TUMBLE(proctime, INTERVAL '1' MINUTE), drone_id
        HAVING AVG(wind_speed) > 8
        """
        self.submit_job('real-time-risk', sql)
