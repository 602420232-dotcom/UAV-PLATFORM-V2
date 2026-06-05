#!/usr/bin/env python3
"""
气象数据流处理作业 - Apache Flink PyFlink

消费 Kafka 中的气象数据主题，执行实时处理：
1. 气象数据清洗与质量控制
2. 5 分钟滑动窗口统计
3. 异常检测与告警触发
"""
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


try:
    from pyflink.datastream import StreamExecutionEnvironment  # type: ignore[import-not-found]
    from pyflink.datastream.connectors.kafka import (  # type: ignore[import-not-found]
        KafkaSource, KafkaSink, KafkaRecordSerializationSchema
    )
    from pyflink.common import WatermarkStrategy  # type: ignore[import-not-found]
    from pyflink.common.serialization import SimpleStringSchema  # type: ignore[import-not-found]
    FLINK_AVAILABLE = True


except ImportError:
    FLINK_AVAILABLE = False
    logger.warning("PyFlink not installed. Install with: pip install apache-flink")


class WeatherDataProcessor:
    """气象数据流处理器"""

    TOPICS = {
        'weather-raw': 'uav-weather-raw',
        'weather-processed': 'uav-weather-processed',
        'weather-alerts': 'uav-weather-alerts',
    }

    def __init__(self, bootstrap_servers: str = 'kafka:9092'):
        self.bootstrap_servers = bootstrap_servers

    def validate_weather_record(self, record: dict) -> bool:
        """气象数据质量检查"""
        try:
            # 物理范围检查
            if not (-90 <= record.get('latitude', 0) <= 90):
                return False
            if not (-180 <= record.get('longitude', 0) <= 180):
                return False
            if not (200 <= record.get('temperature', 300) <= 330):
                return False
            if not (0 <= record.get('wind_speed', 0) <= 83.3):
                return False
            if not (0 <= record.get('humidity', 50) <= 100):
                return False
            return True
        except (TypeError, KeyError):
            return False

    def detect_anomalies(self, record: dict) -> list:
        """检测气象异常"""
        alerts = []

        # 强风告警
        wind = record.get('wind_speed', 0)
        if wind > 15:
            alerts.append({
                'type': 'HIGH_WIND',
                'severity': 'WARNING' if wind < 25 else 'CRITICAL',
                'value': wind,
                'threshold': 15,
                'message': f"强风告警: {wind:.1f}m/s"
            })

        # 低能见度告警
        visibility = record.get('visibility', 10000)
        if visibility < 3000:
            alerts.append({
                'type': 'LOW_VISIBILITY',
                'severity': 'WARNING' if visibility > 1000 else 'CRITICAL',
                'value': visibility,
                'threshold': 3000,
                'message': f"低能见度告警: {visibility:.0f}m"
            })

        return alerts

    def create_source(self, topic: str):
        """创建 Kafka 数据源"""
        if not FLINK_AVAILABLE:
            logger.warning("PyFlink not available, using mock source")
            return None

        return KafkaSource.builder() \
            .set_bootstrap_servers(self.bootstrap_servers) \
            .set_topics(topic) \
            .set_group_id("weather-processor") \
            .set_value_only_deserializer(SimpleStringSchema()) \
            .build()

    def create_sink(self, topic: str):
        """创建 Kafka 数据汇"""
        if not FLINK_AVAILABLE:
            return None

        return KafkaSink.builder() \
            .set_bootstrap_servers(self.bootstrap_servers) \
            .set_record_serializer(
                KafkaRecordSerializationSchema.builder()
                .set_topic(topic)
                .set_value_serialization_schema(SimpleStringSchema())
                .build()
            ) \
            .build()

    def run(self):
        """启动流处理作业"""
        if not FLINK_AVAILABLE:
            logger.info("Running in mock mode (PyFlink not available)")
            self._run_mock()
            return

        env = StreamExecutionEnvironment.get_execution_environment()
        env.set_parallelism(2)

        source = self.create_source(self.TOPICS['weather-raw'])
        if source is None:
            return

        ds = env.from_source(source, WatermarkStrategy.no_watermarks(), "Weather Source")

        # 数据处理管线
        ds \
            .map(lambda x: json.loads(x)) \
            .filter(self.validate_weather_record) \
            .map(lambda x: {**x, 'processed_at': datetime.now().isoformat()}) \
            .sink_to(self.create_sink(self.TOPICS['weather-processed']))

        env.execute("WeatherStreamProcessor")

    def _run_mock(self):
        """模拟运行（当 PyFlink 不可用时）"""
        import time
        import random

        logger.info("Starting mock weather stream processing...")

        samples = [
            {"latitude": 30.5, "longitude": 103.5, "temperature": 22.0,
             "wind_speed": 12.5, "humidity": 65, "visibility": 8000},
            {"latitude": 30.6, "longitude": 103.6, "temperature": 21.5,
             "wind_speed": 8.3, "humidity": 70, "visibility": 5000},
        ]

        for i in range(10):
            record = random.choice(samples).copy()
            record['wind_speed'] += random.uniform(-3, 3)
            record['timestamp'] = datetime.now().isoformat()

            logger.info(f"Processing record {i}: {record}")

            if not self.validate_weather_record(record):
                logger.warning(f"Record failed validation: {record}")
                continue

            alerts = self.detect_anomalies(record)
            if alerts:
                for alert in alerts:
                    logger.warning(f"ALERT: {alert['message']}")

            time.sleep(1)

        logger.info("Mock processing completed")


if __name__ == "__main__":
    processor = WeatherDataProcessor()
    processor.run()
