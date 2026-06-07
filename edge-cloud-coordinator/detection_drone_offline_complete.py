#!/usr/bin/env python3
"""
探测无人机离线上传集成模块（完整版）

场景：探测无人机在海上/山区/高空飞行，全程可能无网络。
采集数据全部走 OfflineCache 缓存 → 着陆后触发 processSyncQueue 自动上传。

新增：集成气象风险映射模块
"""

import time
import logging
import threading
import sqlite3
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from collections import deque
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@dataclass
class OfflineSample:
    """离线样本数据结构"""
    mission_id: int
    drone_id: str
    sequence_num: int = 0
    longitude: float = 0.0
    latitude: float = 0.0
    altitude: float = 0.0
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    pressure: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[float] = None
    wind_gust: Optional[float] = None
    visibility: Optional[float] = None
    co2: Optional[float] = None
    pm25: Optional[float] = None
    quality_flag: float = 1.0
    # 新增：风险相关字段
    u_wind: Optional[float] = None
    v_wind: Optional[float] = None
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    sample_time: float = field(default_factory=time.time)

    def to_api_payload(self) -> dict:
        return {k: v for k, v in {
            "longitude": self.longitude,
            "latitude": self.latitude,
            "altitude": self.altitude,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "windSpeed": self.wind_speed,
            "windDirection": self.wind_direction,
            "windGust": self.wind_gust,
            "visibility": self.visibility,
            "co2": self.co2,
            "pm25": self.pm25,
            "qualityFlag": self.quality_flag,
            "uWind": self.u_wind,
            "vWind": self.v_wind,
            "riskLevel": self.risk_level,
            "riskScore": self.risk_score,
            "sampleTime": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(self.sample_time))
        }.items() if v is not None}

    def to_sqlite_row(self) -> tuple:
        return (
            self.mission_id,
            self.drone_id,
            self.sequence_num,
            self.longitude,
            self.latitude,
            self.altitude,
            self.temperature,
            self.humidity,
            self.pressure,
            self.wind_speed,
            self.wind_direction,
            self.wind_gust,
            self.visibility,
            self.co2,
            self.pm25,
            self.quality_flag,
            self.u_wind,
            self.v_wind,
            self.risk_level,
            self.risk_score,
            self.sample_time
        )


class SQLiteOfflineCache:
    """SQLite离线缓存数据库"""

    def __init__(self, db_path: str = "offline_cache.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS offline_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id INTEGER NOT NULL,
                drone_id TEXT NOT NULL,
                sequence_num INTEGER NOT NULL,
                longitude REAL,
                latitude REAL,
                altitude REAL,
                temperature REAL,
                humidity REAL,
                pressure REAL,
                wind_speed REAL,
                wind_direction REAL,
                wind_gust REAL,
                visibility REAL,
                co2 REAL,
                pm25 REAL,
                quality_flag REAL,
                u_wind REAL,
                v_wind REAL,
                risk_level TEXT,
                risk_score REAL,
                sample_time REAL,
                uploaded BOOLEAN DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_mission_drone
            ON offline_samples (mission_id, drone_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_uploaded
            ON offline_samples (uploaded)
        ''')
        conn.commit()
        conn.close()
        logger.info(f"SQLite缓存数据库初始化完成: {self.db_path}")

    def save_sample(self, sample: OfflineSample) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO offline_samples (
                mission_id, drone_id, sequence_num, longitude, latitude, altitude,
                temperature, humidity, pressure, wind_speed, wind_direction, wind_gust,
                visibility, co2, pm25, quality_flag, u_wind, v_wind,
                risk_level, risk_score, sample_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample.to_sqlite_row())
        sample_id = cursor.lastrowid
        conn.commit()
        conn.close()
        assert sample_id is not None, "INSERT should return a valid row id"
        return sample_id

    def get_pending_samples(
        self, mission_id: int, drone_id: str, max_count: int = 1000
    ) -> List[OfflineSample]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM offline_samples
            WHERE mission_id = ? AND drone_id = ? AND uploaded = 0
            ORDER BY sequence_num
            LIMIT ?
        ''', (mission_id, drone_id, max_count))
        rows = cursor.fetchall()

        samples = []
        for row in rows:
            samples.append(OfflineSample(
                mission_id=row['mission_id'],
                drone_id=row['drone_id'],
                sequence_num=row['sequence_num'],
                longitude=row['longitude'],
                latitude=row['latitude'],
                altitude=row['altitude'],
                temperature=row['temperature'],
                humidity=row['humidity'],
                pressure=row['pressure'],
                wind_speed=row['wind_speed'],
                wind_direction=row['wind_direction'],
                wind_gust=row['wind_gust'],
                visibility=row['visibility'],
                co2=row['co2'],
                pm25=row['pm25'],
                quality_flag=row['quality_flag'],
                u_wind=row['u_wind'],
                v_wind=row['v_wind'],
                risk_level=row['risk_level'],
                risk_score=row['risk_score'],
                sample_time=row['sample_time']
            ))

        conn.close()
        return samples

    def mark_as_uploaded(self, sample_ids: List[int]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for sample_id in sample_ids:
            cursor.execute(
                'UPDATE offline_samples SET uploaded = 1 WHERE id = ?',
                (sample_id,)
            )
        conn.commit()
        conn.close()

    def get_pending_count(self, mission_id: int, drone_id: str) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM offline_samples
            WHERE mission_id = ? AND drone_id = ? AND uploaded = 0
        ''', (mission_id, drone_id))
        count = cursor.fetchone()[0]
        conn.close()
        return count


class OfflineSampleBuffer:
    """离线样本缓冲区
    在飞行期间缓存所有采集样本，着陆后批量上传。
    同时支持内存缓冲 + SQLite持久化。
    """

    def __init__(self, mission_id: int, drone_id: str,
                 max_buffer_size: int = 50000,
                 db_path: str = "offline_cache.db"):
        self.mission_id = mission_id
        self.drone_id = drone_id
        self.buffer: deque = deque(maxlen=max_buffer_size)
        self.sequence_counter = 0
        self.lock = threading.Lock()
        self.db = SQLiteOfflineCache(db_path)

        # 风险映射器（可选）
        self.risk_mapper = None
        self._init_risk_mapper()

    def _init_risk_mapper(self):
        """初始化风险映射器（如果可用）"""
        try:
            # 添加风险映射模块路径
            import sys
            current_dir = Path(__file__).parent
            risk_mapper_path = (
                current_dir.parent / "data-assimilation-platform"
                / "algorithm_core" / "src"
            )
            if str(risk_mapper_path) not in sys.path:
                sys.path.insert(0, str(risk_mapper_path))

            from bayesian_assimilation.utils.risk_mapper import WeatherToRiskMapper
            self.risk_mapper = WeatherToRiskMapper()
            logger.info("风险映射器初始化成功")
        except Exception as e:
            logger.warning(f"风险映射器初始化失败（将不计算风险）: {e}")
            self.risk_mapper = None

    def add_sample(self, sample: OfflineSample) -> int:
        with self.lock:
            self.sequence_counter += 1
            sample.sequence_num = self.sequence_counter
            sample.mission_id = self.mission_id
            sample.drone_id = self.drone_id

            # 计算风险（如果有可用的风险映射器）
            if self.risk_mapper and sample.u_wind is not None and sample.v_wind is not None:
                try:
                    # 简化版：单个点的风险计算
                    # 注意：实际使用应该基于更大的网格数据
                    wind_speed = (sample.u_wind ** 2 + sample.v_wind ** 2) ** 0.5
                    risk_score = min(wind_speed / 20.0, 1.0)

                    if risk_score < 0.3:
                        sample.risk_level = "LOW"
                    elif risk_score < 0.6:
                        sample.risk_level = "MEDIUM"
                    else:
                        sample.risk_level = "HIGH"

                    sample.risk_score = risk_score
                except Exception as e:
                    logger.warning(f"风险计算失败: {e}")

            self.buffer.append(sample)
            # 同时保存到SQLite
            self.db.save_sample(sample)
            return self.sequence_counter

    def add_from_sensor(self, sensor_data: dict):
        """从传感器原始数据创建样本并加入缓冲区"""
        sample = OfflineSample(
            mission_id=self.mission_id,
            drone_id=self.drone_id,
            longitude=sensor_data.get("longitude", 0),
            latitude=sensor_data.get("latitude", 0),
            altitude=sensor_data.get("altitude", 0),
            temperature=sensor_data.get("temperature"),
            humidity=sensor_data.get("humidity"),
            pressure=sensor_data.get("pressure"),
            wind_speed=sensor_data.get("wind_speed"),
            wind_direction=sensor_data.get("wind_direction"),
            wind_gust=sensor_data.get("wind_gust"),
            visibility=sensor_data.get("visibility"),
            co2=sensor_data.get("co2"),
            pm25=sensor_data.get("pm25"),
            u_wind=sensor_data.get("u_wind"),
            v_wind=sensor_data.get("v_wind"),
            quality_flag=sensor_data.get("data_quality", 1.0)
        )
        return self.add_sample(sample)

    def get_buffer_size(self) -> int:
        return len(self.buffer)

    def to_batch_payload(self, max_batch_size: int = 1000) -> List[dict]:
        """生成批量上传的 payload，分批次返回"""
        with self.lock:
            samples = list(self.buffer)
        batches = []
        for i in range(0, len(samples), max_batch_size):
            batch = samples[i:i + max_batch_size]
            batches.append({
                "missionId": self.mission_id,
                "droneId": self.drone_id,
                "fromOffline": True,
                "samples": [s.to_api_payload() for s in batch]
            })
        return batches

    def clear(self):
        with self.lock:
            self.buffer.clear()


class NetworkMonitor:
    """网络状态监控器"""

    def __init__(self, check_interval: float = 5.0):
        self.check_interval = check_interval
        self._online = False
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks = []

    def add_callback(self, callback):
        self._callbacks.append(callback)

    def is_online(self) -> bool:
        return self._online

    def _check_network(self):
        try:
            # 简单的网络检查
            import socket
            sock = socket.create_connection(("8.8.8.8", 53), timeout=3)
            sock.close()
            return True
        except OSError:
            return False

    def _monitor_loop(self):
        while self._running:
            was_online = self._online
            self._online = self._check_network()

            if self._online and not was_online:
                logger.info("网络已恢复")
                for callback in self._callbacks:
                    try:
                        callback()
                    except Exception as e:
                        logger.error(f"网络恢复回调执行失败: {e}")

            time.sleep(self.check_interval)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("网络监控器已启动")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()
        logger.info("网络监控器已停止")


class DetectionDroneOfflineUploader:
    """探测无人机离线上传管理器
    封装离线缓存 → 网络恢复 → 自动上传的完整链路。
    集成：SQLite持久化 + 网络监控 + 风险映射。
    """

    def __init__(self, upload_endpoint: Optional[str] = None,
                 db_path: str = "offline_cache.db"):
        self.buffers: Dict[str, OfflineSampleBuffer] = {}
        self.db_path = db_path
        self.upload_endpoint = (
            upload_endpoint
            or "http://detection-drone:8092/api/detection/sample/upload"
        )
        self._online = False
        self._pending_upload = False
        self._upload_thread: Optional[threading.Thread] = None

        # 网络监控器
        self.network_monitor = NetworkMonitor()
        self.network_monitor.add_callback(self.on_network_restored)

    def start_mission(self, mission_id: int, drone_id: str) -> OfflineSampleBuffer:
        """开始一个新探测任务，创建离线缓冲区"""
        buffer = OfflineSampleBuffer(mission_id, drone_id, db_path=self.db_path)
        key = f"{drone_id}_{mission_id}"
        self.buffers[key] = buffer
        logger.info(f"探测任务开始: missionId={mission_id}, droneId={drone_id}")

        # 启动网络监控
        self.network_monitor.start()
        return buffer

    def end_mission(self, mission_id: int, drone_id: str):
        """结束任务，标记为待上传"""
        key = f"{drone_id}_{mission_id}"
        buffer = self.buffers.get(key)
        if buffer:
            sample_count = buffer.get_buffer_size()
            logger.info(f"探测任务结束: missionId={mission_id}, samples={sample_count}, 等待网络恢复上传")
            self._pending_upload = True

    def on_network_restored(self):
        """网络恢复回调 — 由 NetworkMonitor 触发"""
        logger.info("网络已恢复，开始上传离线数据...")
        self._online = True
        if self._pending_upload:
            self._upload_thread = threading.Thread(target=self._upload_all_pending, daemon=True)
            self._upload_thread.start()

    def _upload_all_pending(self):
        """批量上传所有待处理的离线数据"""
        try:
            import requests
        except ImportError:
            logger.error("requests 库未安装，无法执行离线上传")
            return

        for key, buffer in list(self.buffers.items()):
            if buffer.get_buffer_size() == 0:
                continue
            batches = buffer.to_batch_payload(max_batch_size=500)
            total_batches = len(batches)
            for i, batch in enumerate(batches):
                try:
                    resp = requests.post(self.upload_endpoint, json=batch, timeout=60)
                    if resp.status_code == 200:
                        logger.info(f"离线数据上传成功: {key}, batch={i + 1}/{total_batches}")
                    else:
                        logger.warning(f"离线数据上传失败: {key}, HTTP {resp.status_code}")
                        break  # 失败则停止，等下次重试
                except Exception as e:
                    logger.error(f"离线数据上传异常: {key}, {e}")
                    break
            else:
                # 全部成功，清除缓冲区
                buffer.clear()
                logger.info(f"离线数据全部上传完成: {key}")

        # 检查是否全部完成
        remaining = sum(b.get_buffer_size() for b in self.buffers.values())
        if remaining == 0:
            self._pending_upload = False
            logger.info("所有离线数据已上传")

    def get_pending_count(self) -> int:
        return sum(b.get_buffer_size() for b in self.buffers.values())

    def get_mission_summary(self) -> List[dict]:
        return [{
            "missionId": buf.mission_id,
            "droneId": buf.drone_id,
            "sampleCount": buf.get_buffer_size(),
            "pending": buf.get_buffer_size() > 0
        } for buf in self.buffers.values()]


def demo():
    """演示完整的离线采集 + 风险映射流程"""
    logger.info("=" * 70)
    logger.info("探测无人机离线上传集成模块 - 演示")
    logger.info("=" * 70)

    # 初始化上传管理器
    uploader = DetectionDroneOfflineUploader(db_path="demo_cache.db")

    # 开始任务
    mission_id = 1001
    drone_id = "drone-probe-001"
    buffer = uploader.start_mission(mission_id, drone_id)

    logger.info(f"\n任务开始: mission={mission_id}, drone={drone_id}")

    # 模拟传感器数据采集
    logger.info("\n模拟传感器数据采集（带风险计算）...")
    for i in range(10):
        sensor_data = {
            "longitude": 116.4 + i * 0.01,
            "latitude": 39.9 + i * 0.01,
            "altitude": 100.0 + i * 10,
            "temperature": 25.0 + i * 0.5,
            "humidity": 60.0 - i * 2,
            "wind_speed": 5.0 + i * 2,
            "wind_direction": 90.0 + i * 5,
            "u_wind": 3.0 + i * 1.5,
            "v_wind": 4.0 + i * 1.0,
            "data_quality": 0.95
        }

        buffer.add_from_sensor(sensor_data)
        logger.info(f"  已采集样本 {i + 1}: 风速={sensor_data['wind_speed']:.1f}m/s")

    logger.info(f"\n缓冲区大小: {buffer.get_buffer_size()}")

    # 查看样本信息（包含风险）
    logger.info("\n样本详情:")
    for sample in buffer.buffer:
        logger.info(
            f"  #{sample.sequence_num}: 位置=({sample.longitude:.3f}, {sample.latitude:.3f}), "
            f"风险={sample.risk_level}({sample.risk_score:.2f})"
        )

    # 结束任务
    uploader.end_mission(mission_id, drone_id)

    # 清理演示数据库
    try:
        import os
        os.remove("demo_cache.db")
    except OSError:
        pass

    logger.info("\n" + "=" * 70)
    logger.info("演示完成!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo()
