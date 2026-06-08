"""
流式处理工作流模块
提供实时数据流同化处理功能
"""

import logging
import numpy as np
from typing import Iterator, List, Dict, Any, Optional, Callable
from datetime import datetime
from collections import deque
from dataclasses import dataclass, field
import threading

# 尝试导入必要的类


try:
    from bayesian_assimilation.core.assimilator import BayesianAssimilator  # type: ignore[assignment]  # noqa: E501
except ImportError:

    class BayesianAssimilator:

        def __init__(self, config=None):
            self.config = config
            self.logger = logging.getLogger(__name__)

        def initialize_grid(self: Any, domain_size: int, resolution: Any = None):
            self.domain_size = domain_size
            self.resolution = resolution

        def assimilate_3dvar(self, background, observations, obs_locations, obs_errors=None):
            return background.copy(), np.zeros_like(background)

        def assimilate(self, background, observations, obs_locations, obs_errors=None):
            return self.assimilate_3dvar(background, observations, obs_locations, obs_errors)

try:
    from bayesian_assimilation.utils.config import AssimilationConfig  # type: ignore[assignment]  # noqa: E501
except ImportError:

    class AssimilationConfig:
        observation_error_scale: float = 1.0

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

try:
    from bayesian_assimilation.utils.metrics import PerformanceMetrics  # type: ignore[assignment]  # noqa: E501
except ImportError:

    class PerformanceMetrics:

        def __init__(self):
            pass

logger = logging.getLogger(__name__)


@dataclass
class StreamData:
    """流数据容器"""
    timestamp: datetime
    data: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssimilationResult:
    """同化结果"""
    timestamp: datetime
    analysis: np.ndarray
    variance: np.ndarray
    latency: float  # 处理延迟（秒）
    processing_time: float  # 处理耗时（秒）


class StreamBuffer:
    """
    流数据缓冲区
    用于缓存和批量处理流数据
    """

    def __init__(self, max_size: int = 100, batch_size: int = 10):
        """
        Args:
            max_size: 最大缓冲区大小
            batch_size: 批处理大小
        """
        self.max_size = max_size
        self.batch_size = batch_size
        self.buffer = deque(maxlen=max_size)
        self.lock = threading.Lock()

    def add(self, data: StreamData):
        """添加数据到缓冲区"""
        with self.lock:
            self.buffer.append(data)

    def get_batch(self) -> List[StreamData]:
        """获取一批数据"""
        with self.lock:
            batch_size = min(len(self.buffer), self.batch_size)
            if batch_size == 0:
                return []

            batch = [self.buffer.popleft() for _ in range(batch_size)]
            return batch

    def size(self) -> int:
        """获取缓冲区大小"""
        with self.lock:
            return len(self.buffer)

    def clear(self):
        """清空缓冲区"""
        with self.lock:
            self.buffer.clear()


class StreamingAssimilator:
    """
    流式同化器
    处理实时数据流，执行增量同化
    """

    def __init__(self,
                 config: Optional[AssimilationConfig] = None,
                 buffer_size: int = 100,
                 batch_size: int = 10,
                 window_size: int = 5):
        """
        Args:
            config: 同化配置
            buffer_size: 缓冲区大小
            batch_size: 批处理大小
            window_size: 滑动窗口大小
        """
        self.config = config or AssimilationConfig()
        self.buffer_size = buffer_size
        self.batch_size = batch_size
        self.window_size = window_size

        self.assimilator = BayesianAssimilator(self.config)
        self.buffer = StreamBuffer(buffer_size, batch_size)
        self.metrics = PerformanceMetrics()

        self.background = None
        self.results_history: deque = deque(maxlen=1000)
        self.is_running = False
        self._lock = threading.Lock()

        # 滑动窗口
        self.observation_window: deque = deque(maxlen=window_size)
        self.location_window: deque = deque(maxlen=window_size)
        self.error_window: deque = deque(maxlen=window_size)

    def update_background(self, background: np.ndarray):
        """
        更新背景场

        Args:
            background: 新的背景场
        """
        # 确保线程安全更新背景场
        with self._lock:
            self.background = background
            logger.info(f"背景场已更新: {background.shape}")

    def add_observation(self,
                        observations: np.ndarray,
                        locations: np.ndarray,
                        errors: Optional[np.ndarray] = None,
                        timestamp: Optional[datetime] = None):
        """添加观测数据"""
        timestamp = timestamp or datetime.now()

        stream_data = StreamData(
            timestamp=timestamp,
            data=observations,
            metadata={
                'locations': locations,
                'errors': (
                    errors if errors is not None
                    else np.ones_like(observations) * self.config.observation_error_scale
                )
            }
        )

        self.buffer.add(stream_data)

        # 更新滑动窗口
        self.observation_window.append(observations)
        self.location_window.append(locations)
        self.error_window.append(errors)

    def process_batch(self) -> List[AssimilationResult]:
        """
        处理一批观测数据

        Returns:
            同化结果列表
        """
        if self.background is None:
            logger.warning("背景场未设置，跳过处理")
            return []

        batch = self.buffer.get_batch()
        if not batch:
            return []

        results = []
        start_time = datetime.now()  # noqa: F841

        for stream_data in batch:
            try:
                obs_start = datetime.now()

                # 获取观测数据
                observations = stream_data.data
                locations = stream_data.metadata['locations']
                errors = stream_data.metadata['errors']

                # 执行同化
                analysis, variance = self.assimilator.assimilate(
                    self.background,
                    observations,
                    locations,
                    errors
                )

                obs_end = datetime.now()

                # 构建结果
                result = AssimilationResult(
                    timestamp=stream_data.timestamp,
                    analysis=analysis,
                    variance=variance,
                    latency=(obs_end - stream_data.timestamp).total_seconds(),
                    processing_time=(obs_end - obs_start).total_seconds()
                )

                results.append(result)
                self.results_history.append(result)

            except Exception as e:
                logger.error(f"处理观测数据失败: {e}")

        logger.info(f"批次处理完成: {len(results)} 个结果")
        return results

    def get_latest_result(self) -> Optional[AssimilationResult]:
        """
        获取最新的同化结果

        Returns:
            最新的结果或None
        """
        if self.results_history:
            return self.results_history[-1]
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计字典
        """
        if not self.results_history:
            return {
                'total_results': 0,
                'buffer_size': self.buffer.size(),
                'avg_latency': 0,
                'max_latency': 0,
                'avg_processing_time': 0,
                'observation_window_size': len(self.observation_window)
            }

        latencies = [r.latency for r in self.results_history]
        proc_times = [r.processing_time for r in self.results_history]

        return {
            'total_results': len(self.results_history),
            'buffer_size': self.buffer.size(),
            'avg_latency': np.mean(latencies) if latencies else 0,
            'max_latency': np.max(latencies) if latencies else 0,
            'avg_processing_time': np.mean(proc_times) if proc_times else 0,
            'observation_window_size': len(self.observation_window)
        }


class ContinuousAssimilator:
    """
    连续同化器
    支持连续观测数据的同化处理
    """

    def __init__(self,
                 config: Optional[AssimilationConfig] = None,
                 cycle_interval: float = 60.0,
                 assimilation_window: int = 3):
        """
        Args:
            config: 同化配置
            cycle_interval: 同化周期间隔（秒）
            assimilation_window: 同化窗口大小（周期数）
        """
        self.config = config or AssimilationConfig()
        self.cycle_interval = cycle_interval
        self.assimilation_window = assimilation_window

        self.stream_assimilator = StreamingAssimilator(config)
        self.background_history: deque = deque(maxlen=assimilation_window)
        self.is_running = False
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self,
              background_provider: Callable[[], np.ndarray],
              observation_provider: Callable[[], tuple]):
        """
        启动连续同化

        Args:
            background_provider: 背景场提供者函数
            observation_provider: 观测提供者函数，返回 (observations, locations, errors) 元组
        """
        if self.is_running:
            logger.warning("连续同化器已在运行")
            return

        self._stop_event.clear()
        self.is_running = True

        def run_loop():
            while not self._stop_event.is_set():
                try:
                    # 获取背景场
                    background = background_provider()
                    self.stream_assimilator.update_background(background)
                    self.background_history.append(background)

                    # 获取观测数据
                    obs_data = observation_provider()
                    if obs_data is not None:
                        observations, locations, errors = obs_data
                        self.stream_assimilator.add_observation(
                            observations, locations, errors
                        )

                    # 处理批次
                    results = self.stream_assimilator.process_batch()

                    if results:
                        latest = results[-1]
                        logger.info(
                            f"同化完成: 延迟 {latest.latency:.3f}s, "
                            f"处理时间 {latest.processing_time:.3f}s"
                        )

                    # 更新背景场（如果需要）
                    if len(self.background_history) >= self.assimilation_window:
                        # 使用滑动平均更新背景场
                        avg_background = np.mean(
                            np.stack(list(self.background_history)),
                            axis=0
                        )
                        self.stream_assimilator.update_background(avg_background)

                except Exception as e:
                    logger.error(f"同化循环错误: {e}")

                self._stop_event.wait(self.cycle_interval)

        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()

        logger.info(
            f"连续同化器已启动，周期: {self.cycle_interval}s, "
            f"窗口大小: {self.assimilation_window}周期"
        )

    def stop(self):
        """停止连续同化"""
        if not self.is_running:
            return

        self._stop_event.set()
        self.is_running = False

        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

        logger.info("连续同化器已停止")

    def get_latest_analysis(self) -> Optional[np.ndarray]:
        """获取最新分析场"""
        result = self.stream_assimilator.get_latest_result()
        return result.analysis if result else None

    def get_latest_variance(self) -> Optional[np.ndarray]:
        """获取最新方差场"""
        result = self.stream_assimilator.get_latest_result()
        return result.variance if result else None


def create_stream_processor(config: Optional[AssimilationConfig] = None,
                            buffer_size: int = 100,
                            batch_size: int = 10) -> StreamingAssimilator:
    """
    创建流处理器辅助函数

    Args:
        config: 同化配置
        buffer_size: 缓冲区大小
        batch_size: 批处理大小

    Returns:
        StreamingAssimilator对象
    """
    return StreamingAssimilator(
        config=config,
        buffer_size=buffer_size,
        batch_size=batch_size
    )


def process_data_stream(
        data_iterator: Iterator[Dict[str, Any]],
        config: Optional[AssimilationConfig] = None,
        batch_size: int = 10) -> Iterator[List[AssimilationResult]]:
    """
    处理数据流的生成器函数

    Args:
        data_iterator: 数据迭代器
        config: 同化配置
        batch_size: 批处理大小

    Yields:
        同化结果列表
    """
    processor = StreamingAssimilator(config=config, batch_size=batch_size)
    batch = []

    for data_item in data_iterator:
        # 解析数据项
        observations = data_item['observations']
        locations = data_item['locations']
        errors = data_item.get('errors')
        background = data_item.get('background')

        if background is not None:
            processor.update_background(background)

        processor.add_observation(observations, locations, errors)
        batch.append(data_item)

        if len(batch) >= batch_size:
            results = processor.process_batch()
            if results:
                yield results
            batch = []

    # 处理剩余数据
    if batch:
        results = processor.process_batch()
        if results:
            yield results
