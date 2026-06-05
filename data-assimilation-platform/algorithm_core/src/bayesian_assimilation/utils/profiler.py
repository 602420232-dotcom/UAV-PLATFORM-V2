"""
性能分析模块
提供代码性能剖析、函数耗时统计、调用次数分析等功能
"""

import time
import cProfile
import pstats
import io
import threading
from typing import Dict, Any, Optional, Callable, Union, TypeVar, ParamSpec
from contextlib import contextmanager
from functools import wraps


class Profiler:
    """
    性能分析器
    基于 cProfile 进行代码性能剖析，统计函数耗时和调用次数
    """

    def __init__(self, enabled: bool = True):
        """
        初始化性能分析器

        Args:
            enabled: 是否启用性能分析
        """
        self.enabled = enabled
        self._profiles: Dict[str, cProfile.Profile] = {}
        self._stats: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def start(self, name: str) -> None:
        """
        开始性能分析

        Args:
            name: 分析名称（如函数名）
        """
        if not self.enabled:
            return

        with self._lock:
            if name in self._profiles:
                self._profiles[name].enable()
            else:
                profiler = cProfile.Profile()
                profiler.enable()
                self._profiles[name] = profiler

    def stop(self, name: str) -> None:
        """
        停止性能分析并收集统计信息

        Args:
            name: 分析名称
        """
        if not self.enabled:
            return

        with self._lock:
            if name in self._profiles:
                profiler = self._profiles[name]
                profiler.disable()

                # 收集统计信息
                stream = io.StringIO()
                stats = pstats.Stats(profiler, stream=stream)
                stats.sort_stats(pstats.SortKey.CUMULATIVE)

                self._stats[name] = {
                    'profiler': profiler,
                    'stats': stats,
                    'stream': stream
                }

    def record(self, name: str, elapsed: float) -> None:
        """
        记录耗时数据（简单计时，不使用 cProfile）

        Args:
            name: 记录名称
            elapsed: 耗时（秒）
        """
        if not self.enabled:
            return

        with self._lock:
            if name not in self._stats:
                self._stats[name] = {
                    'total_time': 0.0,
                    'count': 0,
                    'min_time': float('inf'),
                    'max_time': 0.0,
                    'times': []
                }

            data = self._stats[name]
            data['total_time'] += elapsed
            data['count'] += 1
            data['min_time'] = min(data['min_time'], elapsed)
            data['max_time'] = max(data['max_time'], elapsed)
            data['times'].append(elapsed)

    def get_stats(self, name: Optional[str] = None) -> Union[Dict[str, Any], pstats.Stats]:
        """
        获取统计信息

        Args:
            name: 分析名称，如果为 None 则返回所有统计信息

        Returns:
            统计信息字典或 pstats.Stats 对象
        """
        with self._lock:
            if name is not None:
                if name in self._stats:
                    data = self._stats[name]
                    if 'stats' in data:
                        return data['stats']
                    else:
                        # 返回简单计时的统计信息
                        return {
                            'total_time': data['total_time'],
                            'count': data['count'],
                            'avg_time': data['total_time'] / data['count'] if data['count'] > 0 else 0,
                            'min_time': data['min_time'] if data['min_time'] != float('inf') else 0,
                            'max_time': data['max_time']
                        }
                return {}
            else:
                # 返回所有统计信息的摘要
                summary = {}
                for key, data in self._stats.items():
                    if 'stats' in data:
                        summary[key] = 'cProfile data available'
                    else:
                        summary[key] = {
                            'total_time': data['total_time'],
                            'count': data['count'],
                            'avg_time': data['total_time'] / data['count'] if data['count'] > 0 else 0
                        }
                return summary

    def reset(self, name: Optional[str] = None) -> None:
        """
        重置统计信息

        Args:
            name: 分析名称，如果为 None 则重置所有统计信息
        """
        with self._lock:
            if name is not None:
                if name in self._profiles:
                    del self._profiles[name]
                if name in self._stats:
                    del self._stats[name]
            else:
                self._profiles.clear()
                self._stats.clear()

    def print_report(self, name: Optional[str] = None, top_n: int = 20) -> str:
        """
        打印性能分析报告

        Args:
            name: 分析名称，如果为 None 则打印所有报告
            top_n: 显示前 N 个最耗时的函数

        Returns:
            报告字符串
        """
        with self._lock:
            report_lines = ["=" * 60, "性能分析报告", "=" * 60]

            if name is not None:
                # 打印单个分析报告
                if name in self._stats and 'stats' in self._stats[name]:
                    stream = self._stats[name]['stream']
                    stream.seek(0)
                    report_lines.append(f"\n>>> {name} <<<")
                    report_lines.append(stream.getvalue())
                elif name in self._stats:
                    data = self._stats[name]
                    report_lines.append(f"\n>>> {name} <<<")
                    report_lines.append(f"  调用次数: {data['count']}")
                    report_lines.append(f"  总耗时: {data['total_time']:.6f} 秒")
                    report_lines.append(f"  平均耗时: {data['total_time'] / data['count']:.6f} 秒" if data['count'] > 0 else "  平均耗时: N/A")
                    report_lines.append(f"  最小耗时: {data['min_time']:.6f} 秒")
                    report_lines.append(f"  最大耗时: {data['max_time']:.6f} 秒")
            else:
                # 打印所有简单计时的统计信息
                report_lines.append("\n>>> 所有计时统计 <<<")
                for key, data in self._stats.items():
                    if 'stats' not in data:
                        report_lines.append(f"\n  {key}:")
                        report_lines.append(f"    调用次数: {data['count']}")
                        report_lines.append(f"    总耗时: {data['total_time']:.6f} 秒")
                        if data['count'] > 0:
                            report_lines.append(f"    平均耗时: {data['total_time'] / data['count']:.6f} 秒")
                            report_lines.append(f"    最小耗时: {data['min_time']:.6f} 秒")
                            report_lines.append(f"    最大耗时: {data['max_time']:.6f} 秒")

            report_lines.append("=" * 60)
            return "\n".join(report_lines)


# 全局性能分析器实例
_global_profiler: Optional[Profiler] = None
_global_lock = threading.Lock()


def get_profiler() -> Profiler:
    """
    获取全局性能分析器实例（单例模式）

    Returns:
        全局 Profiler 实例
    """
    global _global_profiler
    if _global_profiler is None:
        with _global_lock:
            if _global_profiler is None:
                _global_profiler = Profiler()
    return _global_profiler


P = ParamSpec('P')
R = TypeVar('R')


def profile_function(func: Optional[Callable[P, R]] = None, *, name: Optional[str] = None) -> Union[Callable[[Callable[P, R]], Callable[P, R]], Callable[P, R]]:
    """
    函数性能分析装饰器

    Args:
        func: 被装饰的函数
        name: 自定义分析名称，如果为 None 则使用函数名

    Returns:
        装饰后的函数
    """

    def decorator(f: Callable[P, R]) -> Callable[P, R]:
        profiler = get_profiler()
        analysis_name = name or f.__name__

        @wraps(f)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            profiler.start(analysis_name)
            try:
                return f(*args, **kwargs)
            finally:
                profiler.stop(analysis_name)

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


@contextmanager
def timing_block(name: str, profiler: Optional[Profiler] = None):
    """
    计时上下文管理器

    Args:
        name: 计时名称
        profiler: 性能分析器实例，如果为 None 则使用全局实例

    Yields:
        None

    Example:
        with timing_block('my_operation'):
            # 执行一些操作
            pass
    """
    if profiler is None:
        profiler = get_profiler()

    start_time = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        profiler.record(name, elapsed)


class Timer:
    """
    手动计时器
    用于精确测量代码块的执行时间
    """

    def __init__(self, name: str = 'default', auto_start: bool = True):
        """
        初始化计时器

        Args:
            name: 计时器名称
            auto_start: 是否自动开始计时
        """
        self.name = name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed: float = 0.0

        if auto_start:
            self.start()

    def start(self) -> 'Timer':
        """
        开始计时

        Returns:
            self 以便链式调用
        """
        self.start_time = time.time()
        self.end_time = None
        self.elapsed = 0.0
        return self

    def stop(self) -> float:
        """
        停止计时

        Returns:
            耗时（秒）
        """
        if self.start_time is None:
            raise ValueError("计时器未启动")

        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time

        # 记录到全局性能分析器
        profiler = get_profiler()
        profiler.record(self.name, self.elapsed)

        return self.elapsed

    def pause(self) -> 'Timer':
        """
        暂停计时

        Returns:
            self 以便链式调用
        """
        if self.start_time is None:
            raise ValueError("计时器未启动")

        if self.end_time is None:
            self.elapsed += time.time() - self.start_time
            self.start_time = None

        return self

    def resume(self) -> 'Timer':
        """
        恢复计时

        Returns:
            self 以便链式调用
        """
        if self.start_time is not None:
            return self  # 已经在计时中

        self.start_time = time.time()
        return self

    def reset(self) -> 'Timer':
        """
        重置计时器

        Returns:
            self 以便链式调用
        """
        self.start_time = None
        self.end_time = None
        self.elapsed = 0.0
        return self

    def get_elapsed(self) -> float:
        """
        获取当前耗时

        Returns:
            耗时（秒）
        """
        if self.start_time is not None:
            # 正在计时中
            return self.elapsed + (time.time() - self.start_time)
        else:
            return self.elapsed

    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if self.start_time is not None:
            self.stop()

    def __str__(self) -> str:
        """字符串表示"""
        elapsed = self.get_elapsed()
        return f"Timer '{self.name}': {elapsed:.6f} 秒"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"Timer(name='{self.name}', elapsed={self.get_elapsed():.6f})"
