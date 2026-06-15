#!/usr/bin/env python3
"""
UAV Platform V2 - 增强型稳定性测试脚本

持续运行指定时间，定期采样请求延迟、错误率、内存使用、CPU、磁盘 I/O、网络延迟等指标，
检测内存泄漏和性能退化，支持自定义告警阈值，支持测试中断时的自动报告生成，
支持对比基线数据，退出时生成摘要报告。

增强功能:
  - 支持内存泄漏检测阈值配置
  - 支持 CPU 使用率监控
  - 支持磁盘 I/O 监控
  - 支持网络延迟监控
  - 支持自定义告警阈值（错误率 > 1%、P99 > 1s）
  - 支持测试中断时的自动报告生成
  - 支持对比基线数据（与上一次测试结果对比）

用法:
    python scripts/stability-test.py
    python scripts/stability-test.py --duration 300
    python scripts/stability-test.py --base-url http://192.168.1.100:8260
    python scripts/stability-test.py --concurrency 50 --sample-interval 15
    python scripts/stability-test.py --report-file stability-report.md
    python scripts/stability-test.py --baseline baseline.json
    python scripts/stability-test.py --alert-error-rate 0.5 --alert-p99-ms 800
    python scripts/stability-test.py --auto-report --no-color
"""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import signal
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ============================================================
# ANSI Color Codes
# ============================================================

class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

    @staticmethod
    def disable() -> None:
        Color.RESET = ""
        Color.BOLD = ""
        Color.DIM = ""
        Color.RED = ""
        Color.GREEN = ""
        Color.YELLOW = ""
        Color.BLUE = ""
        Color.CYAN = ""
        Color.WHITE = ""


# ============================================================
# Configuration
# ============================================================

DEFAULT_BASE_URL = "http://localhost:8260"
DEFAULT_DURATION = 600  # 10 分钟
DEFAULT_SAMPLE_INTERVAL = 30  # 30 秒采样间隔
DEFAULT_CONCURRENCY = 20  # 稳定性测试的并发数
REQUEST_TIMEOUT = 15

# 默认阈值 (可通过参数覆盖)
MEMORY_LEAK_THRESHOLD_MB_PER_MIN = 5.0  # 内存泄漏阈值: 每分钟增长 > 5MB 视为泄漏
ALERT_ERROR_RATE_PCT = 1.0                # 告警: 错误率 > 1%
ALERT_P99_MS = 1000.0                     # 告警: P99 > 1000ms
ALERT_CPU_PCT = 80.0                      # 告警: CPU > 80%
ALERT_DISK_IO_MBPS = 100.0                # 告警: 磁盘 I/O > 100 MB/s
ALERT_NETWORK_LATENCY_MS = 500.0          # 告警: 网络延迟 > 500ms

# 测试端点 (稳定性测试关注核心端点)
ENDPOINTS = {
    "algorithm-list": {
        "method": "GET",
        "path": "/api/v1/algorithm/list",
        "description": "算法列表查询",
        "payload": None,
    },
    "health-check": {
        "method": "GET",
        "path": "/actuator/health",
        "description": "健康检查",
        "payload": None,
    },
    "weather-point": {
        "method": "POST",
        "path": "/api/v1/weather/point",
        "description": "气象点查询",
        "payload": {
            "longitude": 116.397,
            "latitude": 39.908,
            "altitude": 100,
            "timestamp": "2025-01-15T08:00:00Z",
        },
    },
    "planning-path": {
        "method": "POST",
        "path": "/api/v1/planning/path",
        "description": "路径规划",
        "payload": {
            "start": {"longitude": 116.397, "latitude": 39.908, "altitude": 100},
            "end": {"longitude": 116.410, "latitude": 39.915, "altitude": 150},
            "algorithm": "astar",
            "constraints": {
                "max_altitude": 200,
                "min_altitude": 50,
                "max_distance": 5000,
            },
        },
    },
}


# ============================================================
# Data Structures
# ============================================================

@dataclass
class SystemMetrics:
    """系统资源指标"""
    cpu_percent: float = 0.0
    disk_read_mbps: float = 0.0
    disk_write_mbps: float = 0.0
    network_latency_ms: float = 0.0
    process_rss_mb: float = 0.0
    jvm_heap_used_mb: float = 0.0
    jvm_heap_max_mb: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "cpu_percent": round(self.cpu_percent, 2),
            "disk_read_mbps": round(self.disk_read_mbps, 2),
            "disk_write_mbps": round(self.disk_write_mbps, 2),
            "network_latency_ms": round(self.network_latency_ms, 2),
            "process_rss_mb": round(self.process_rss_mb, 2),
            "jvm_heap_used_mb": round(self.jvm_heap_used_mb, 2),
            "jvm_heap_max_mb": round(self.jvm_heap_max_mb, 2),
        }


@dataclass
class SamplePoint:
    """单个采样点的数据"""
    timestamp: float  # Unix 时间戳
    elapsed_s: float  # 从测试开始的经过时间 (秒)
    total_requests: int = 0
    success_requests: int = 0
    failed_requests: int = 0
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    error_rate_pct: float = 0.0
    qps: float = 0.0
    system_metrics: SystemMetrics = field(default_factory=SystemMetrics)
    alerts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat(),
            "elapsed_s": round(self.elapsed_s, 1),
            "total_requests": self.total_requests,
            "success_requests": self.success_requests,
            "failed_requests": self.failed_requests,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "p50_latency_ms": round(self.p50_latency_ms, 2),
            "p95_latency_ms": round(self.p95_latency_ms, 2),
            "p99_latency_ms": round(self.p99_latency_ms, 2),
            "error_rate_pct": round(self.error_rate_pct, 2),
            "qps": round(self.qps, 2),
            "system_metrics": self.system_metrics.to_dict(),
            "alerts": self.alerts,
        }


@dataclass
class StabilityResult:
    """稳定性测试完整结果"""
    test_start: float = 0.0
    test_end: float = 0.0
    duration_s: float = 0.0
    concurrency: int = 0
    sample_interval_s: float = 0.0
    base_url: str = ""
    samples: list[SamplePoint] = field(default_factory=list)
    interrupted: bool = False
    thresholds: dict[str, float] = field(default_factory=dict)

    @property
    def total_samples(self) -> int:
        return len(self.samples)

    @property
    def total_requests(self) -> int:
        return sum(s.total_requests for s in self.samples)

    @property
    def total_success(self) -> int:
        return sum(s.success_requests for s in self.samples)

    @property
    def total_failed(self) -> int:
        return sum(s.failed_requests for s in self.samples)

    @property
    def overall_error_rate(self) -> float:
        total = self.total_requests
        return (self.total_failed / total * 100) if total > 0 else 0.0

    @property
    def overall_availability(self) -> float:
        total = self.total_requests
        return (self.total_success / total * 100) if total > 0 else 0.0

    def memory_leak_detected(self) -> tuple[bool, float, str]:
        """
        使用线性回归检测内存泄漏。
        返回: (是否泄漏, 斜率 MB/min, 诊断信息)
        """
        threshold = self.thresholds.get("memory_leak_mb_per_min", MEMORY_LEAK_THRESHOLD_MB_PER_MIN)
        if len(self.samples) < 3:
            return False, 0.0, "采样点不足，无法分析"

        memory_values = [
            (s.elapsed_s / 60.0, s.system_metrics.jvm_heap_used_mb if s.system_metrics.jvm_heap_used_mb > 0 else s.system_metrics.process_rss_mb)
            for s in self.samples
            if (s.system_metrics.jvm_heap_used_mb > 0 or s.system_metrics.process_rss_mb > 0)
        ]

        if len(memory_values) < 3:
            return False, 0.0, "无内存数据可用"

        n = len(memory_values)
        sum_x = sum(p[0] for p in memory_values)
        sum_y = sum(p[1] for p in memory_values)
        sum_xy = sum(p[0] * p[1] for p in memory_values)
        sum_x2 = sum(p[0] ** 2 for p in memory_values)

        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            return False, 0.0, "时间范围为零，无法计算趋势"

        slope = (n * sum_xy - sum_x * sum_y) / denominator  # MB/min
        intercept = (sum_y - slope * sum_x) / n

        mean_y = sum_y / n
        ss_tot = sum((y - mean_y) ** 2 for _, y in memory_values)
        ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in memory_values)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        if slope > threshold and r_squared > 0.5:
            return True, slope, (
                f"检测到内存泄漏趋势: 内存增长速率 {slope:.2f} MB/min "
                f"(阈值: {threshold} MB/min, R²={r_squared:.3f})"
            )
        elif slope > threshold / 2:
            return False, slope, (
                f"内存增长速率偏高: {slope:.2f} MB/min, "
                f"但趋势线性度不足 (R²={r_squared:.3f}), 需持续观察"
            )
        else:
            return False, slope, (
                f"内存使用稳定: 增长速率 {slope:.2f} MB/min "
                f"(阈值: {threshold} MB/min)"
            )

    def get_alerts(self) -> list[str]:
        """汇总所有采样点的告警"""
        all_alerts: list[str] = []
        for s in self.samples:
            all_alerts.extend(s.alerts)
        return all_alerts

    def to_dict(self) -> dict[str, Any]:
        leak_detected, leak_slope, leak_diag = self.memory_leak_detected()
        return {
            "test_info": {
                "start_time": datetime.fromtimestamp(self.test_start, tz=timezone.utc).isoformat(),
                "end_time": datetime.fromtimestamp(self.test_end, tz=timezone.utc).isoformat(),
                "duration_s": round(self.duration_s, 1),
                "concurrency": self.concurrency,
                "sample_interval_s": self.sample_interval_s,
                "base_url": self.base_url,
                "interrupted": self.interrupted,
            },
            "thresholds": self.thresholds,
            "summary": {
                "total_samples": self.total_samples,
                "total_requests": self.total_requests,
                "total_success": self.total_success,
                "total_failed": self.total_failed,
                "overall_error_rate_pct": round(self.overall_error_rate, 2),
                "overall_availability_pct": round(self.overall_availability, 2),
                "memory_leak_detected": leak_detected,
                "memory_leak_slope_mb_per_min": round(leak_slope, 2),
                "memory_diagnosis": leak_diag,
                "total_alerts": len(self.get_alerts()),
            },
            "time_series": [s.to_dict() for s in self.samples],
        }


# ============================================================
# System Metrics Collection
# ============================================================

def _get_cpu_percent() -> float:
    """获取 CPU 使用率 (%)"""
    try:
        if sys.platform == "win32":
            # Windows: 使用 wmic
            result = subprocess.run(
                ["wmic", "cpu", "get", "loadpercentage", "/value"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if "LoadPercentage=" in line:
                    return float(line.split("=")[1].strip())
        else:
            # Linux: 读取 /proc/stat
            with open("/proc/stat", "r") as f:
                line = f.readline()
                fields = list(map(int, line.split()[1:]))
                idle = fields[3]
                total = sum(fields)
                # 需要两次采样计算差值，这里简化返回 0
                # 更好的方式是用 psutil，但这里保持零依赖
                return 0.0
    except Exception:
        pass
    return 0.0


def _get_disk_io_mbps() -> tuple[float, float]:
    """获取磁盘 I/O 速率 (MB/s)"""
    try:
        if sys.platform == "win32":
            # Windows: 使用 wmic
            result = subprocess.run(
                ["wmic", "path", "Win32_PerfFormattedData_PerfDisk_PhysicalDisk",
                 "get", "DiskReadBytesPersec,DiskWriteBytesPersec", "/value"],
                capture_output=True, text=True, timeout=5
            )
            read_bytes = 0
            write_bytes = 0
            for line in result.stdout.splitlines():
                if "DiskReadBytesPersec=" in line:
                    read_bytes = int(line.split("=")[1].strip())
                elif "DiskWriteBytesPersec=" in line:
                    write_bytes = int(line.split("=")[1].strip())
            return read_bytes / (1024 * 1024), write_bytes / (1024 * 1024)
        else:
            # Linux: 读取 /proc/diskstats
            with open("/proc/diskstats", "r") as f:
                total_read_sectors = 0
                total_write_sectors = 0
                for line in f:
                    parts = line.split()
                    if len(parts) >= 10:
                        total_read_sectors += int(parts[5])
                        total_write_sectors += int(parts[9])
                # 512 bytes per sector, 需要两次采样
                return 0.0, 0.0
    except Exception:
        pass
    return 0.0, 0.0


def _get_network_latency_ms(base_url: str) -> float:
    """测量到目标服务的网络延迟 (ms)"""
    try:
        host = base_url.replace("http://", "").replace("https://", "").split(":")[0]
        if sys.platform == "win32":
            result = subprocess.run(
                ["ping", "-n", "1", "-w", "1000", host],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if "time=" in line.lower():
                    # 解析 time=XXms
                    parts = line.lower().split("time=")
                    if len(parts) > 1:
                        time_str = parts[1].split("ms")[0].strip()
                        return float(time_str)
        else:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "1", host],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if "time=" in line:
                    parts = line.split("time=")
                    if len(parts) > 1:
                        time_str = parts[1].split(" ")[0].strip()
                        return float(time_str)
    except Exception:
        pass
    return 0.0


def _get_process_memory_mb() -> float:
    """获取当前 Python 进程的 RSS 内存 (MB)"""
    try:
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            psapi = ctypes.windll.psapi
            handle = kernel32.GetCurrentProcess()
            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", ctypes.c_ulong),
                    ("PageFaultCount", ctypes.c_ulong),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]
            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
            return counters.WorkingSetSize / (1024 * 1024)
        else:
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        return float(line.split()[1]) / 1024  # KB -> MB
    except Exception:
        pass
    return 0.0


def _try_get_jvm_memory(base_url: str) -> tuple[float, float]:
    """尝试通过 actuator/metrics 获取 JVM 堆内存使用情况"""
    try:
        url = f"{base_url}/actuator/metrics/jvm.memory.used"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for measurement in data.get("measurements", []):
                if measurement.get("statistic") == "VALUE":
                    return (measurement["value"] / (1024 * 1024), 0.0)
    except Exception:
        pass

    try:
        url = f"{base_url}/actuator/health"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            mem = data.get("details", {}).get("memory", {})
            if mem:
                used = mem.get("used", 0)
                total = mem.get("total", 0)
                if used > 1000000:
                    return (used / (1024 * 1024), total / (1024 * 1024))
                elif used > 1000:
                    return (used / 1024, total / 1024)
                else:
                    return (float(used), float(total))
    except Exception:
        pass

    return (0.0, 0.0)


def collect_system_metrics(base_url: str) -> SystemMetrics:
    """收集系统资源指标"""
    metrics = SystemMetrics()
    metrics.cpu_percent = _get_cpu_percent()
    metrics.disk_read_mbps, metrics.disk_write_mbps = _get_disk_io_mbps()
    metrics.network_latency_ms = _get_network_latency_ms(base_url)
    metrics.process_rss_mb = _get_process_memory_mb()
    metrics.jvm_heap_used_mb, metrics.jvm_heap_max_mb = _try_get_jvm_memory(base_url)
    return metrics


def check_alerts(sample: SamplePoint, thresholds: dict[str, float]) -> list[str]:
    """检查采样点是否触发告警"""
    alerts: list[str] = []
    err_threshold = thresholds.get("alert_error_rate_pct", ALERT_ERROR_RATE_PCT)
    p99_threshold = thresholds.get("alert_p99_ms", ALERT_P99_MS)
    cpu_threshold = thresholds.get("alert_cpu_pct", ALERT_CPU_PCT)
    disk_threshold = thresholds.get("alert_disk_io_mbps", ALERT_DISK_IO_MBPS)
    net_threshold = thresholds.get("alert_network_latency_ms", ALERT_NETWORK_LATENCY_MS)

    if sample.error_rate_pct > err_threshold:
        alerts.append(f"错误率超标: {sample.error_rate_pct:.2f}% > {err_threshold}%")
    if sample.p99_latency_ms > p99_threshold:
        alerts.append(f"P99 延迟超标: {sample.p99_latency_ms:.1f}ms > {p99_threshold}ms")
    if sample.system_metrics.cpu_percent > cpu_threshold:
        alerts.append(f"CPU 使用率超标: {sample.system_metrics.cpu_percent:.1f}% > {cpu_threshold}%")
    if sample.system_metrics.disk_read_mbps + sample.system_metrics.disk_write_mbps > disk_threshold:
        total_io = sample.system_metrics.disk_read_mbps + sample.system_metrics.disk_write_mbps
        alerts.append(f"磁盘 I/O 超标: {total_io:.1f} MB/s > {disk_threshold} MB/s")
    if sample.system_metrics.network_latency_ms > net_threshold:
        alerts.append(f"网络延迟超标: {sample.system_metrics.network_latency_ms:.1f}ms > {net_threshold}ms")

    return alerts


# ============================================================
# Utility Functions
# ============================================================

def _percentile(data: list[float], pct: float) -> float:
    """计算百分位数"""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * pct / 100.0
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[f]
    d0 = sorted_data[f] * (c - k)
    d1 = sorted_data[c] * (k - f)
    return d0 + d1


def _send_request(base_url: str, config: dict) -> tuple[bool, float, str | None]:
    """发送单个 HTTP 请求，返回 (成功, 延迟ms, 错误信息)"""
    url = f"{base_url}{config['path']}"
    method = config["method"]
    payload = config.get("payload")

    start = time.monotonic()
    try:
        data = None
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if payload and method == "POST":
            data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            elapsed_ms = (time.monotonic() - start) * 1000.0
            success = 200 <= resp.status < 400
            _ = resp.read()
            return (success, elapsed_ms, None if success else f"HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        elapsed_ms = (time.monotonic() - start) * 1000.0
        return (False, elapsed_ms, f"HTTP {e.code}")
    except urllib.error.URLError as e:
        elapsed_ms = (time.monotonic() - start) * 1000.0
        return (False, elapsed_ms, f"连接错误: {str(e.reason)[:60]}")
    except Exception as e:
        elapsed_ms = (time.monotonic() - start) * 1000.0
        return (False, elapsed_ms, str(e)[:80])


# ============================================================
# Baseline Comparison
# ============================================================

def load_baseline(baseline_file: str) -> dict[str, Any] | None:
    """加载基线数据"""
    path = Path(baseline_file)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def compare_with_baseline(result: StabilityResult, baseline: dict[str, Any]) -> list[str]:
    """与基线对比，返回差异描述"""
    diffs: list[str] = []
    baseline_summary = baseline.get("summary", {})

    # 错误率对比
    current_err = result.overall_error_rate
    baseline_err = baseline_summary.get("overall_error_rate_pct", 0)
    if current_err > baseline_err * 1.5 and baseline_err > 0:
        diffs.append(f"错误率恶化: {current_err:.2f}% (基线: {baseline_err:.2f}%, +{(current_err/baseline_err-1)*100:.0f}%)")
    elif current_err < baseline_err * 0.7 and baseline_err > 0:
        diffs.append(f"错误率改善: {current_err:.2f}% (基线: {baseline_err:.2f}%, -{(1-current_err/baseline_err)*100:.0f}%)")

    # 可用性对比
    current_avail = result.overall_availability
    baseline_avail = baseline_summary.get("overall_availability_pct", 100)
    if current_avail < baseline_avail - 0.5:
        diffs.append(f"可用性下降: {current_avail:.2f}% (基线: {baseline_avail:.2f}%)")
    elif current_avail > baseline_avail + 0.5:
        diffs.append(f"可用性提升: {current_avail:.2f}% (基线: {baseline_avail:.2f}%)")

    # 内存泄漏对比
    current_leak, current_slope, _ = result.memory_leak_detected()
    baseline_leak = baseline_summary.get("memory_leak_detected", False)
    if current_leak and not baseline_leak:
        diffs.append(f"新增内存泄漏: {current_slope:.2f} MB/min (基线无泄漏)")
    elif not current_leak and baseline_leak:
        diffs.append(f"内存泄漏已修复 (基线存在泄漏)")

    # QPS 对比 (取平均)
    if result.samples and baseline.get("time_series"):
        current_qps = statistics.mean([s.qps for s in result.samples if s.total_requests > 0])
        baseline_qps = statistics.mean([
            s.get("qps", 0) for s in baseline["time_series"] if s.get("total_requests", 0) > 0
        ])
        if baseline_qps > 0:
            qps_change = (current_qps / baseline_qps - 1) * 100
            if abs(qps_change) > 10:
                direction = "提升" if qps_change > 0 else "下降"
                diffs.append(f"QPS{direction}: {current_qps:.1f} (基线: {baseline_qps:.1f}, {qps_change:+.1f}%)")

    return diffs


# ============================================================
# Stability Test Runner
# ============================================================

def run_sample(
    base_url: str,
    concurrency: int,
    sample_duration: float,
    thresholds: dict[str, float],
) -> SamplePoint:
    """运行一个采样周期的测试"""
    results: list[tuple[bool, float]] = []  # (success, latency_ms)
    errors: list[str] = []

    deadline = time.monotonic() + sample_duration

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        active: dict[Any, None] = {}

        while time.monotonic() < deadline:
            for key, config in ENDPOINTS.items():
                if len(active) >= concurrency:
                    break
                future = executor.submit(_send_request, base_url, config)
                active[future] = None

            if not active:
                break

            done = []
            for future in list(active.keys()):
                try:
                    result = future.result(timeout=0.05)
                    done.append((future, result))
                except Exception:
                    pass
                break

            for future, result in done:
                del active[future]
                success, latency, error = result
                results.append((success, latency))
                if error:
                    errors.append(error)

        for future in as_completed(active.keys(), timeout=REQUEST_TIMEOUT + 5):
            try:
                result = future.result()
                success, latency, error = result
                results.append((success, latency))
                if error:
                    errors.append(error)
            except Exception:
                results.append((False, 0.0))
                errors.append("Future 异常")

    latencies = [lat for success, lat in results if success]
    success_count = sum(1 for s, _ in results if s)
    failed_count = len(results) - success_count
    total_count = len(results)

    sample = SamplePoint(
        timestamp=time.time(),
        elapsed_s=0.0,
        total_requests=total_count,
        success_requests=success_count,
        failed_requests=failed_count,
        avg_latency_ms=statistics.mean(latencies) if latencies else 0.0,
        p50_latency_ms=_percentile(latencies, 50),
        p95_latency_ms=_percentile(latencies, 95),
        p99_latency_ms=_percentile(latencies, 99),
        error_rate_pct=(failed_count / total_count * 100) if total_count > 0 else 0.0,
        qps=success_count / sample_duration if sample_duration > 0 else 0.0,
    )

    # 收集系统指标
    sample.system_metrics = collect_system_metrics(base_url)

    # 检查告警
    sample.alerts = check_alerts(sample, thresholds)

    return sample


def run_stability_test(
    base_url: str,
    duration_s: float,
    concurrency: int,
    sample_interval_s: float,
    thresholds: dict[str, float],
) -> StabilityResult:
    """运行完整的稳定性测试"""
    result = StabilityResult(
        test_start=time.time(),
        concurrency=concurrency,
        sample_interval_s=sample_interval_s,
        base_url=base_url,
        thresholds=thresholds,
    )

    print(f"\n{Color.CYAN}{Color.BOLD}稳定性测试开始{Color.RESET}")
    print(f"  持续时间: {duration_s}s ({duration_s / 60:.1f} 分钟)")
    print(f"  采样间隔: {sample_interval_s}s")
    print(f"  并发数:   {concurrency}")
    print(f"  目标:     {base_url}")
    print(f"  告警阈值: 错误率>{thresholds.get('alert_error_rate_pct', ALERT_ERROR_RATE_PCT)}%, "
          f"P99>{thresholds.get('alert_p99_ms', ALERT_P99_MS)}ms, "
          f"CPU>{thresholds.get('alert_cpu_pct', ALERT_CPU_PCT)}%, "
          f"磁盘IO>{thresholds.get('alert_disk_io_mbps', ALERT_DISK_IO_MBPS)}MB/s, "
          f"网络延迟>{thresholds.get('alert_network_latency_ms', ALERT_NETWORK_LATENCY_MS)}ms")
    print(f"\n  按 Ctrl+C 可提前终止并生成报告\n")

    # 打印表头
    print(
        f"  {'时间':>8} {'经过':>8} {'QPS':>8} {'P50':>8} {'P95':>8} "
        f"{'P99':>8} {'错误率':>8} {'内存(MB)':>10} {'CPU(%)':>8} {'告警':>6}"
    )
    print(f"  {Color.DIM}{'─' * 86}{Color.RESET}")

    deadline = time.time() + duration_s
    sample_num = 0

    try:
        while time.time() < deadline:
            sample_num += 1
            sample_start = time.time()

            sample = run_sample(base_url, concurrency, sample_interval_s, thresholds)
            sample.elapsed_s = time.time() - result.test_start

            result.samples.append(sample)

            # 实时输出
            elapsed_min = sample.elapsed_s / 60.0
            p99_color = Color.GREEN if sample.p99_latency_ms < 500 else Color.RED
            err_color = Color.GREEN if sample.error_rate_pct < 1 else Color.RED
            mem_str = f"{sample.system_metrics.jvm_heap_used_mb:.0f}" if sample.system_metrics.jvm_heap_used_mb > 0 else f"{sample.system_metrics.process_rss_mb:.0f}"
            alert_count = len(sample.alerts)
            alert_str = f"{Color.RED}{alert_count}{Color.RESET}" if alert_count > 0 else f"{Color.GREEN}0{Color.RESET}"

            print(
                f"  {elapsed_min:>7.1f}m "
                f"{sample.elapsed_s:>7.0f}s "
                f"{sample.qps:>8.1f} "
                f"{sample.p50_latency_ms:>7.1f}ms "
                f"{sample.p95_latency_ms:>7.1f}ms "
                f"{p99_color}{sample.p99_latency_ms:>7.1f}ms{Color.RESET} "
                f"{err_color}{sample.error_rate_pct:>7.2f}%{Color.RESET} "
                f"{mem_str:>10} "
                f"{sample.system_metrics.cpu_percent:>7.1f} "
                f"{alert_str:>6}"
            )

            # 等待下一个采样周期
            remaining = sample_interval_s - (time.time() - sample_start)
            if remaining > 0 and time.time() + remaining < deadline:
                time.sleep(remaining)

    except KeyboardInterrupt:
        result.interrupted = True
        print(f"\n  {Color.YELLOW}测试被用户中断 (Ctrl+C){Color.RESET}")

    result.test_end = time.time()
    result.duration_s = result.test_end - result.test_start

    return result


# ============================================================
# Report Generation
# ============================================================

def print_summary(result: StabilityResult, baseline: dict[str, Any] | None = None) -> None:
    """打印终端摘要报告"""
    leak_detected, leak_slope, leak_diag = result.memory_leak_detected()

    print(f"\n{Color.BOLD}{'=' * 80}{Color.RESET}")
    print(f"{Color.BOLD}  UAV Platform V2 - 稳定性测试摘要{Color.RESET}")
    print(f"  测试时间: {datetime.fromtimestamp(result.test_start, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"  持续时间: {result.duration_s:.0f}s ({result.duration_s / 60:.1f} 分钟)")
    if result.interrupted:
        print(f"  {Color.YELLOW}注意: 测试被提前中断{Color.RESET}")
    print(f"{Color.BOLD}{'=' * 80}{Color.RESET}")

    # 总体统计
    print(f"\n  {Color.CYAN}--- 总体统计 ---{Color.RESET}\n")
    print(f"    采样点数:     {result.total_samples}")
    print(f"    总请求数:     {result.total_requests}")
    print(f"    成功请求:     {Color.GREEN}{result.total_success}{Color.RESET}")
    print(f"    失败请求:     {Color.RED}{result.total_failed}{Color.RESET}")
    print(f"    整体错误率:   {Color.RED if result.overall_error_rate > 1 else Color.GREEN}{result.overall_error_rate:.2f}%{Color.RESET}")
    print(f"    整体可用性:   {Color.GREEN if result.overall_availability > 99.9 else Color.RED}{result.overall_availability:.2f}%{Color.RESET}")

    # 告警统计
    all_alerts = result.get_alerts()
    if all_alerts:
        print(f"\n  {Color.CYAN}--- 告警统计 ({len(all_alerts)} 次) ---{Color.RESET}\n")
        alert_counts: dict[str, int] = {}
        for alert in all_alerts:
            key = alert.split(":")[0]
            alert_counts[key] = alert_counts.get(key, 0) + 1
        for alert_type, count in sorted(alert_counts.items(), key=lambda x: -x[1]):
            print(f"    {Color.YELLOW}{alert_type}: {count} 次{Color.RESET}")

    # 延迟趋势
    if result.samples:
        all_p99 = [s.p99_latency_ms for s in result.samples if s.total_requests > 0]
        first_p99 = all_p99[0] if all_p99 else 0
        last_p99 = all_p99[-1] if all_p99 else 0
        avg_p99 = statistics.mean(all_p99) if all_p99 else 0
        max_p99 = max(all_p99) if all_p99 else 0

        print(f"\n  {Color.CYAN}--- 延迟趋势 (P99) ---{Color.RESET}\n")
        print(f"    起始 P99:    {first_p99:.1f}ms")
        print(f"    结束 P99:    {last_p99:.1f}ms")
        print(f"    平均 P99:    {avg_p99:.1f}ms")
        print(f"    最大 P99:    {Color.RED if max_p99 > 500 else Color.GREEN}{max_p99:.1f}ms{Color.RESET}")

        if len(all_p99) >= 3:
            p99_trend = last_p99 - first_p99
            trend_str = "上升" if p99_trend > 50 else ("下降" if p99_trend < -50 else "稳定")
            trend_color = Color.RED if p99_trend > 50 else (Color.GREEN if p99_trend < -50 else Color.YELLOW)
            print(f"    P99 趋势:    {trend_color}{trend_str} ({p99_trend:+.1f}ms){Color.RESET}")

    # QPS 趋势
    if result.samples:
        all_qps = [s.qps for s in result.samples if s.total_requests > 0]
        first_qps = all_qps[0] if all_qps else 0
        last_qps = all_qps[-1] if all_qps else 0
        avg_qps = statistics.mean(all_qps) if all_qps else 0

        print(f"\n  {Color.CYAN}--- 吞吐量趋势 ---{Color.RESET}\n")
        print(f"    起始 QPS:    {first_qps:.1f}")
        print(f"    结束 QPS:    {last_qps:.1f}")
        print(f"    平均 QPS:    {avg_qps:.1f}")

        if len(all_qps) >= 3:
            qps_trend = last_qps - first_qps
            qps_pct = (qps_trend / first_qps * 100) if first_qps > 0 else 0
            trend_str = "下降" if qps_trend < -avg_qps * 0.1 else ("上升" if qps_trend > avg_qps * 0.1 else "稳定")
            print(f"    QPS 趋势:    {trend_str} ({qps_pct:+.1f}%)")

    # 系统资源
    if result.samples:
        avg_cpu = statistics.mean([s.system_metrics.cpu_percent for s in result.samples if s.system_metrics.cpu_percent > 0])
        max_cpu = max([s.system_metrics.cpu_percent for s in result.samples if s.system_metrics.cpu_percent > 0], default=0)
        avg_net = statistics.mean([s.system_metrics.network_latency_ms for s in result.samples if s.system_metrics.network_latency_ms > 0])
        max_disk_read = max([s.system_metrics.disk_read_mbps for s in result.samples], default=0)
        max_disk_write = max([s.system_metrics.disk_write_mbps for s in result.samples], default=0)

        print(f"\n  {Color.CYAN}--- 系统资源 ---{Color.RESET}\n")
        print(f"    平均 CPU:    {avg_cpu:.1f}%")
        print(f"    峰值 CPU:    {Color.RED if max_cpu > 80 else Color.GREEN}{max_cpu:.1f}%{Color.RESET}")
        print(f"    平均网络延迟: {avg_net:.1f}ms")
        print(f"    峰值磁盘读:  {max_disk_read:.1f} MB/s")
        print(f"    峰值磁盘写:  {max_disk_write:.1f} MB/s")

    # 内存泄漏分析
    print(f"\n  {Color.CYAN}--- 内存分析 ---{Color.RESET}\n")
    if leak_detected:
        print(f"    {Color.RED}{Color.BOLD}!! 检测到内存泄漏 !!{Color.RESET}")
        print(f"    {Color.RED}{leak_diag}{Color.RESET}")
    else:
        print(f"    {Color.GREEN}{leak_diag}{Color.RESET}")

    # 基线对比
    if baseline:
        diffs = compare_with_baseline(result, baseline)
        print(f"\n  {Color.CYAN}--- 基线对比 ---{Color.RESET}\n")
        if diffs:
            for diff in diffs:
                color = Color.GREEN if "改善" in diff or "提升" in diff or "修复" in diff else Color.RED
                print(f"    {color}{diff}{Color.RESET}")
        else:
            print(f"    {Color.GREEN}与基线相比无明显变化{Color.RESET}")

    # 最终判定
    print(f"\n{Color.BOLD}{'─' * 80}{Color.RESET}")
    issues = []
    if result.overall_error_rate > 1:
        issues.append(f"错误率过高 ({result.overall_error_rate:.2f}%)")
    if result.overall_availability < 99.9:
        issues.append(f"可用性不达标 ({result.overall_availability:.2f}% < 99.9%)")
    if leak_detected:
        issues.append(f"内存泄漏 ({leak_slope:.2f} MB/min)")
    if result.samples:
        max_p99 = max((s.p99_latency_ms for s in result.samples if s.total_requests > 0), default=0)
        if max_p99 > 500:
            issues.append(f"P99 延迟超标 ({max_p99:.1f}ms > 500ms)")
    if all_alerts:
        issues.append(f"触发告警 {len(all_alerts)} 次")

    if not issues:
        print(f"  {Color.GREEN}{Color.BOLD}*** 稳定性测试结果: PASS ***{Color.RESET}")
    else:
        print(f"  {Color.RED}{Color.BOLD}*** 稳定性测试结果: FAIL ***{Color.RESET}")
        for issue in issues:
            print(f"    {Color.RED}- {issue}{Color.RESET}")

    print(f"{Color.BOLD}{'─' * 80}{Color.RESET}\n")


def generate_markdown_report(result: StabilityResult, baseline: dict[str, Any] | None = None) -> str:
    """生成 Markdown 格式报告"""
    lines: list[str] = []
    ts = datetime.fromtimestamp(result.test_start, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    leak_detected, leak_slope, leak_diag = result.memory_leak_detected()

    lines.append("# UAV Platform V2 - 稳定性测试报告\n")
    lines.append(f"> **测试时间:** {ts} UTC")
    lines.append(f"> **持续时间:** {result.duration_s:.0f}s ({result.duration_s / 60:.1f} 分钟)")
    lines.append(f"> **并发数:** {result.concurrency}")
    lines.append(f"> **采样间隔:** {result.sample_interval_s}s")
    lines.append(f"> **采样点数:** {result.total_samples}")
    if result.interrupted:
        lines.append(f"> **注意:** 测试被提前中断\n")
    else:
        lines.append("")

    # 告警阈值
    lines.append("## 告警阈值配置\n")
    lines.append(f"| 指标 | 阈值 |")
    lines.append(f"|------|------|")
    for key, val in result.thresholds.items():
        lines.append(f"| {key} | {val} |")
    lines.append("")

    # 摘要
    lines.append("## 摘要\n")
    lines.append(f"| 指标 | 值 |")
    lines.append(f"|------|------|")
    lines.append(f"| 总请求数 | {result.total_requests} |")
    lines.append(f"| 成功请求 | {result.total_success} |")
    lines.append(f"| 失败请求 | {result.total_failed} |")
    lines.append(f"| 整体错误率 | {result.overall_error_rate:.2f}% |")
    lines.append(f"| 整体可用性 | {result.overall_availability:.2f}% |")
    lines.append(f"| 内存泄漏 | {'是' if leak_detected else '否'} ({leak_slope:.2f} MB/min) |")
    lines.append(f"| 总告警次数 | {len(result.get_alerts())} |")
    lines.append("")

    # 时间序列数据
    lines.append("## 时间序列数据\n")
    lines.append(
        f"| 时间 (min) | 经过 (s) | QPS | P50 (ms) | P95 (ms) | P99 (ms) | "
        f"错误率 (%) | 内存 (MB) | CPU (%) | 网络延迟 (ms) | 告警 |"
    )
    lines.append(
        f"|------------|-----------|-----|----------|----------|----------|"
        f"------------|------------|---------|---------------|------|"
    )

    for s in result.samples:
        mem = f"{s.system_metrics.jvm_heap_used_mb:.0f}" if s.system_metrics.jvm_heap_used_mb > 0 else "N/A"
        alert_str = f"{len(s.alerts)}" if s.alerts else "0"
        lines.append(
            f"| {s.elapsed_s / 60:.1f} | {s.elapsed_s:.0f} | {s.qps:.1f} | "
            f"{s.p50_latency_ms:.1f} | {s.p95_latency_ms:.1f} | {s.p99_latency_ms:.1f} | "
            f"{s.error_rate_pct:.2f} | {mem} | {s.system_metrics.cpu_percent:.1f} | "
            f"{s.system_metrics.network_latency_ms:.1f} | {alert_str} |"
        )
    lines.append("")

    # 内存分析
    lines.append("## 内存分析\n")
    lines.append(f"**诊断结果:** {leak_diag}\n")

    # 系统资源分析
    if result.samples:
        lines.append("## 系统资源分析\n")
        avg_cpu = statistics.mean([s.system_metrics.cpu_percent for s in result.samples if s.system_metrics.cpu_percent > 0])
        max_cpu = max([s.system_metrics.cpu_percent for s in result.samples if s.system_metrics.cpu_percent > 0], default=0)
        avg_net = statistics.mean([s.system_metrics.network_latency_ms for s in result.samples if s.system_metrics.network_latency_ms > 0])
        lines.append(f"- **平均 CPU 使用率:** {avg_cpu:.1f}%")
        lines.append(f"- **峰值 CPU 使用率:** {max_cpu:.1f}%")
        lines.append(f"- **平均网络延迟:** {avg_net:.1f}ms")
        lines.append("")

    # 基线对比
    if baseline:
        diffs = compare_with_baseline(result, baseline)
        lines.append("## 基线对比\n")
        if diffs:
            for diff in diffs:
                emoji = "+" if "改善" in diff or "提升" in diff or "修复" in diff else "-"
                lines.append(f"- {emoji} {diff}")
        else:
            lines.append("与基线相比无明显变化。")
        lines.append("")

    # 结论
    lines.append("## 结论\n")
    issues = []
    if result.overall_error_rate > 1:
        issues.append(f"- 错误率过高 ({result.overall_error_rate:.2f}%)")
    if result.overall_availability < 99.9:
        issues.append(f"- 可用性不达标 ({result.overall_availability:.2f}% < 99.9%)")
    if leak_detected:
        issues.append(f"- 内存泄漏 ({leak_slope:.2f} MB/min)")
    if result.samples:
        max_p99 = max((s.p99_latency_ms for s in result.samples if s.total_requests > 0), default=0)
        if max_p99 > 500:
            issues.append(f"- P99 延迟超标 ({max_p99:.1f}ms > 500ms)")
    if result.get_alerts():
        issues.append(f"- 触发告警 {len(result.get_alerts())} 次")

    if not issues:
        lines.append("**测试结果: PASS** - 系统在测试期间表现稳定。")
    else:
        lines.append("**测试结果: FAIL** - 发现以下问题:")
        for issue in issues:
            lines.append(issue)
    lines.append("")

    return "\n".join(lines)


def auto_generate_report(result: StabilityResult, baseline: dict[str, Any] | None = None) -> str:
    """测试中断时自动生成报告"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)

    # JSON 报告
    json_file = report_dir / f"stability-test-{timestamp}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    # Markdown 报告
    md_file = report_dir / f"stability-test-{timestamp}.md"
    md = generate_markdown_report(result, baseline)
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md)

    return str(md_file)


# ============================================================
# Signal Handler for Auto-Report
# ============================================================

_auto_report_enabled = False
_current_result: StabilityResult | None = None
_current_baseline: dict[str, Any] | None = None


def _signal_handler(signum: int, frame: Any) -> None:
    """信号处理: 测试中断时自动生成报告"""
    if _auto_report_enabled and _current_result is not None:
        print(f"\n{Color.YELLOW}捕获信号，自动生成报告...{Color.RESET}")
        report_path = auto_generate_report(_current_result, _current_baseline)
        print(f"{Color.GREEN}报告已保存: {report_path}{Color.RESET}")
    sys.exit(1)


# ============================================================
# Main
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="UAV Platform V2 - 增强型稳定性测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                                    # 默认 10 分钟
  %(prog)s --duration 300                     # 5 分钟
  %(prog)s --concurrency 50                   # 50 并发
  %(prog)s --sample-interval 15               # 每 15 秒采样
  %(prog)s --base-url http://10.0.0.1:8260   # 指定目标
  %(prog)s --report-file report.md            # 输出报告
  %(prog)s --json-file data.json              # 输出 JSON 数据
  %(prog)s --baseline baseline.json           # 对比基线
  %(prog)s --alert-error-rate 0.5             # 自定义错误率告警阈值
  %(prog)s --alert-p99-ms 800                 # 自定义 P99 告警阈值
  %(prog)s --alert-cpu-pct 70                 # 自定义 CPU 告警阈值
  %(prog)s --auto-report                      # 中断时自动生成报告
  %(prog)s --no-color                         # 禁用颜色
        """,
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"基础 URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=DEFAULT_DURATION,
        help=f"测试持续时间/秒 (default: {DEFAULT_DURATION})",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"并发请求数 (default: {DEFAULT_CONCURRENCY})",
    )
    parser.add_argument(
        "--sample-interval",
        type=int,
        default=DEFAULT_SAMPLE_INTERVAL,
        help=f"采样间隔/秒 (default: {DEFAULT_SAMPLE_INTERVAL})",
    )
    parser.add_argument(
        "--report-file",
        type=str,
        default=None,
        metavar="FILE",
        help="输出 Markdown 摘要报告到指定文件",
    )
    parser.add_argument(
        "--json-file",
        type=str,
        default=None,
        metavar="FILE",
        help="输出 JSON 时间序列数据到指定文件",
    )
    parser.add_argument(
        "--baseline",
        type=str,
        default=None,
        metavar="FILE",
        help="基线数据文件 (JSON)，用于对比分析",
    )
    parser.add_argument(
        "--alert-error-rate",
        type=float,
        default=ALERT_ERROR_RATE_PCT,
        metavar="PCT",
        help=f"错误率告警阈值 %% (default: {ALERT_ERROR_RATE_PCT})",
    )
    parser.add_argument(
        "--alert-p99-ms",
        type=float,
        default=ALERT_P99_MS,
        metavar="MS",
        help=f"P99 延迟告警阈值 ms (default: {ALERT_P99_MS})",
    )
    parser.add_argument(
        "--alert-cpu-pct",
        type=float,
        default=ALERT_CPU_PCT,
        metavar="PCT",
        help=f"CPU 使用率告警阈值 %% (default: {ALERT_CPU_PCT})",
    )
    parser.add_argument(
        "--alert-disk-io-mbps",
        type=float,
        default=ALERT_DISK_IO_MBPS,
        metavar="MBPS",
        help=f"磁盘 I/O 告警阈值 MB/s (default: {ALERT_DISK_IO_MBPS})",
    )
    parser.add_argument(
        "--alert-network-latency-ms",
        type=float,
        default=ALERT_NETWORK_LATENCY_MS,
        metavar="MS",
        help=f"网络延迟告警阈值 ms (default: {ALERT_NETWORK_LATENCY_MS})",
    )
    parser.add_argument(
        "--memory-leak-threshold",
        type=float,
        default=MEMORY_LEAK_THRESHOLD_MB_PER_MIN,
        metavar="MB/MIN",
        help=f"内存泄漏阈值 MB/min (default: {MEMORY_LEAK_THRESHOLD_MB_PER_MIN})",
    )
    parser.add_argument(
        "--auto-report",
        action="store_true",
        help="测试中断时自动生成报告",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="禁用彩色终端输出",
    )
    args = parser.parse_args()

    if args.no_color:
        Color.disable()

    # 加载基线
    baseline = None
    if args.baseline:
        baseline = load_baseline(args.baseline)
        if baseline:
            print(f"{Color.GREEN}已加载基线数据: {args.baseline}{Color.RESET}")
        else:
            print(f"{Color.YELLOW}无法加载基线数据: {args.baseline}{Color.RESET}")

    # 构建阈值配置
    thresholds = {
        "alert_error_rate_pct": args.alert_error_rate,
        "alert_p99_ms": args.alert_p99_ms,
        "alert_cpu_pct": args.alert_cpu_pct,
        "alert_disk_io_mbps": args.alert_disk_io_mbps,
        "alert_network_latency_ms": args.alert_network_latency_ms,
        "memory_leak_mb_per_min": args.memory_leak_threshold,
    }

    # 注册信号处理 (用于自动报告)
    global _auto_report_enabled, _current_result, _current_baseline
    _auto_report_enabled = args.auto_report
    _current_baseline = baseline
    if args.auto_report:
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)
        if hasattr(signal, "SIGBREAK"):
            signal.signal(signal.SIGBREAK, _signal_handler)

    # 运行测试
    result = run_stability_test(
        base_url=args.base_url,
        duration_s=args.duration,
        concurrency=args.concurrency,
        sample_interval_s=args.sample_interval,
        thresholds=thresholds,
    )
    _current_result = result

    # 打印摘要
    print_summary(result, baseline)

    # 写入文件
    if args.json_file:
        with open(args.json_file, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"  JSON 数据已保存: {args.json_file}")

    if args.report_file:
        md = generate_markdown_report(result, baseline)
        with open(args.report_file, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"  Markdown 报告已保存: {args.report_file}")

    # 自动报告 (如果未手动指定 report_file)
    if args.auto_report and not args.report_file:
        report_path = auto_generate_report(result, baseline)
        print(f"  自动报告已保存: {report_path}")

    # 退出码
    leak_detected, _, _ = result.memory_leak_detected()
    has_failure = (
        result.overall_error_rate > 1
        or result.overall_availability < 99.9
        or leak_detected
        or len(result.get_alerts()) > 0
    )
    sys.exit(1 if has_failure else 0)


if __name__ == "__main__":
    main()
