#!/usr/bin/env python3
"""
UAV Platform V2 - 多并发级别压力测试脚本

使用 Python 标准库 (urllib + concurrent.futures) 对平台各端点进行多级并发压测，
输出 QPS、P50/P95/P99 延迟、错误率、吞吐量等指标，支持 JSON + Markdown 报告。

测试端点:
  1. GET  /api/v1/algorithm/list        - 算法列表查询
  2. GET  /actuator/health              - 健康检查
  3. POST /api/v1/weather/point         - 气象点查询
  4. POST /api/v1/planning/path         - 路径规划

用法:
    python scripts/load-test.py
    python scripts/load-test.py --base-url http://192.168.1.100:8260
    python scripts/load-test.py --concurrency-levels 10 50 100 --duration 30
    python scripts/load-test.py --json-output > report.json
    python scripts/load-test.py --markdown-output report.md
    python scripts/load-test.py --no-color
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
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
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"

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
        Color.BG_RED = ""
        Color.BG_GREEN = ""


# ============================================================
# Configuration
# ============================================================

DEFAULT_BASE_URL = "http://localhost:8260"
DEFAULT_CONCURRENCY_LEVELS = [10, 50, 100, 500, 1000]
DEFAULT_DURATION = 60  # 每个并发级别运行秒数
REQUEST_TIMEOUT = 15  # 单个请求超时秒数
P99_TARGET_MS = 500  # P99 成功标准 (毫秒)
SLA_AVAILABILITY = 99.9  # SLA 可用性目标 (%)

# 端点定义
ENDPOINTS = {
    "algorithm-list": {
        "method": "GET",
        "path": "/api/v1/algorithm/list",
        "description": "算法列表查询",
        "category": "查询",
        "payload": None,
    },
    "health-check": {
        "method": "GET",
        "path": "/actuator/health",
        "description": "健康检查",
        "category": "基础设施",
        "payload": None,
    },
    "weather-point": {
        "method": "POST",
        "path": "/api/v1/weather/point",
        "description": "气象点查询",
        "category": "数据服务",
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
        "category": "核心算法",
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
class RequestResult:
    """单个请求的结果"""
    endpoint_key: str
    success: bool
    status_code: int | None = None
    response_time_ms: float = 0.0
    error: str | None = None
    timestamp: float = 0.0


@dataclass
class EndpointStats:
    """单个端点在特定并发级别下的统计数据"""
    endpoint_key: str
    description: str
    category: str
    concurrency: int
    duration_s: float
    total: int = 0
    success: int = 0
    failed: int = 0
    response_times: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    wall_time_s: float = 0.0

    @property
    def error_rate(self) -> float:
        return (self.failed / self.total * 100) if self.total > 0 else 0.0

    @property
    def availability(self) -> float:
        return (self.success / self.total * 100) if self.total > 0 else 0.0

    @property
    def avg_ms(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0.0

    @property
    def min_ms(self) -> float:
        return min(self.response_times) if self.response_times else 0.0

    @property
    def max_ms(self) -> float:
        return max(self.response_times) if self.response_times else 0.0

    @property
    def std_dev_ms(self) -> float:
        return statistics.stdev(self.response_times) if len(self.response_times) > 1 else 0.0

    @property
    def p50_ms(self) -> float:
        return _percentile(self.response_times, 50) if self.response_times else 0.0

    @property
    def p95_ms(self) -> float:
        return _percentile(self.response_times, 95) if self.response_times else 0.0

    @property
    def p99_ms(self) -> float:
        return _percentile(self.response_times, 99) if self.response_times else 0.0

    @property
    def qps(self) -> float:
        """每秒查询数 (基于实际墙钟时间)"""
        return self.success / self.wall_time_s if self.wall_time_s > 0 else 0.0

    @property
    def throughput_kbps(self) -> float:
        """吞吐量 (假设平均响应 2KB)"""
        return self.qps * 2.0

    @property
    def meets_p99_target(self) -> bool:
        return self.p99_ms < P99_TARGET_MS if self.response_times else False

    @property
    def meets_sla(self) -> bool:
        return self.availability >= SLA_AVAILABILITY

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint_key,
            "description": self.description,
            "category": self.category,
            "concurrency": self.concurrency,
            "duration_s": round(self.duration_s, 2),
            "wall_time_s": round(self.wall_time_s, 2),
            "total": self.total,
            "success": self.success,
            "failed": self.failed,
            "error_rate_pct": round(self.error_rate, 2),
            "availability_pct": round(self.availability, 2),
            "avg_ms": round(self.avg_ms, 2),
            "min_ms": round(self.min_ms, 2),
            "max_ms": round(self.max_ms, 2),
            "std_dev_ms": round(self.std_dev_ms, 2),
            "p50_ms": round(self.p50_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "p99_ms": round(self.p99_ms, 2),
            "qps": round(self.qps, 2),
            "throughput_kbps": round(self.throughput_kbps, 2),
            "meets_p99_target": self.meets_p99_target,
            "meets_sla": self.meets_sla,
            "errors": self.errors[:10],
        }


@dataclass
class ConcurrencyLevelResult:
    """单个并发级别的完整测试结果"""
    concurrency: int
    wall_time_s: float = 0.0
    endpoints: dict[str, EndpointStats] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "concurrency": self.concurrency,
            "wall_time_s": round(self.wall_time_s, 2),
            "endpoints": {
                k: v.to_dict() for k, v in self.endpoints.items()
            },
        }


# ============================================================
# Utility Functions
# ============================================================

def _percentile(data: list[float], pct: float) -> float:
    """计算百分位数 (线性插值法)"""
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


def _send_request(base_url: str, endpoint_key: str, config: dict) -> RequestResult:
    """使用 urllib 发送单个 HTTP 请求"""
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
            status = resp.status
            success = 200 <= status < 400
            _ = resp.read()  # 消费响应体
            return RequestResult(
                endpoint_key=endpoint_key,
                success=success,
                status_code=status,
                response_time_ms=elapsed_ms,
                error=None if success else f"HTTP {status}",
                timestamp=time.time(),
            )

    except urllib.error.HTTPError as e:
        elapsed_ms = (time.monotonic() - start) * 1000.0
        return RequestResult(
            endpoint_key=endpoint_key,
            success=False,
            status_code=e.code,
            response_time_ms=elapsed_ms,
            error=f"HTTP {e.code} {e.reason}",
            timestamp=time.time(),
        )
    except urllib.error.URLError as e:
        elapsed_ms = (time.monotonic() - start) * 1000.0
        reason = str(e.reason)
        if "refused" in reason.lower() or "connection" in reason.lower():
            err_msg = "连接拒绝"
        elif "timed out" in reason.lower() or "timeout" in reason.lower():
            err_msg = f"连接超时 ({REQUEST_TIMEOUT}s)"
        else:
            err_msg = f"连接错误: {reason[:80]}"
        return RequestResult(
            endpoint_key=endpoint_key,
            success=False,
            response_time_ms=elapsed_ms,
            error=err_msg,
            timestamp=time.time(),
        )
    except Exception as e:
        elapsed_ms = (time.monotonic() - start) * 1000.0
        return RequestResult(
            endpoint_key=endpoint_key,
            success=False,
            response_time_ms=elapsed_ms,
            error=str(e)[:100],
            timestamp=time.time(),
        )


# ============================================================
# Load Test Runner
# ============================================================

def run_endpoint_test(
    base_url: str,
    endpoint_key: str,
    config: dict,
    concurrency: int,
    duration_s: float,
) -> EndpointStats:
    """对单个端点在指定并发级别下运行持续测试"""
    stats = EndpointStats(
        endpoint_key=endpoint_key,
        description=config["description"],
        category=config["category"],
        concurrency=concurrency,
        duration_s=duration_s,
    )

    wall_start = time.monotonic()
    deadline = wall_start + duration_s

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        active_futures: dict[Any, None] = {}

        while time.monotonic() < deadline:
            # 补充工作线程到满并发
            while len(active_futures) < concurrency and time.monotonic() < deadline:
                future = executor.submit(_send_request, base_url, endpoint_key, config)
                active_futures[future] = None

            if not active_futures:
                break

            # 等待任意一个完成
            done_futures = []
            remaining_wait = deadline - time.monotonic()
            if remaining_wait <= 0:
                break

            for future in list(active_futures.keys()):
                try:
                    result = future.result(timeout=min(0.1, remaining_wait))
                    done_futures.append((future, result))
                except Exception:
                    pass
                break  # 每次只检查一个

            for future, result in done_futures:
                del active_futures[future]
                stats.total += 1
                if result.success:
                    stats.success += 1
                    stats.response_times.append(result.response_time_ms)
                else:
                    stats.failed += 1
                    if result.error:
                        stats.errors.append(result.error)

    # 等待剩余的 futures 完成
    for future in as_completed(active_futures.keys(), timeout=REQUEST_TIMEOUT + 5):
        try:
            result = future.result()
            stats.total += 1
            if result.success:
                stats.success += 1
                stats.response_times.append(result.response_time_ms)
            else:
                stats.failed += 1
                if result.error:
                    stats.errors.append(result.error)
        except Exception:
            stats.total += 1
            stats.failed += 1
            stats.errors.append("Future 异常")

    stats.wall_time_s = time.monotonic() - wall_start
    return stats


def run_concurrency_level(
    base_url: str,
    concurrency: int,
    duration_s: float,
) -> ConcurrencyLevelResult:
    """在指定并发级别下测试所有端点"""
    result = ConcurrencyLevelResult(concurrency=concurrency)
    wall_start = time.monotonic()

    for endpoint_key, config in ENDPOINTS.items():
        stats = run_endpoint_test(
            base_url=base_url,
            endpoint_key=endpoint_key,
            config=config,
            concurrency=concurrency,
            duration_s=duration_s,
        )
        result.endpoints[endpoint_key] = stats

    result.wall_time_s = time.monotonic() - wall_start
    return result


def run_all_tests(
    base_url: str,
    concurrency_levels: list[int],
    duration_s: float,
) -> list[ConcurrencyLevelResult]:
    """运行所有并发级别的测试"""
    all_results: list[ConcurrencyLevelResult] = []

    for level in concurrency_levels:
        print(f"\n{Color.CYAN}{Color.BOLD}>>> 并发级别: {level} <<<{Color.RESET}")
        result = run_concurrency_level(base_url, level, duration_s)
        all_results.append(result)
        _print_level_summary(result)

    return all_results


# ============================================================
# Terminal Output
# ============================================================

def _print_level_summary(result: ConcurrencyLevelResult) -> None:
    """打印单个并发级别的摘要"""
    print(f"\n  {Color.DIM}{'─' * 60}{Color.RESET}")
    print(f"  {Color.BOLD}并发 {result.concurrency} - 各端点结果:{Color.RESET}")
    print(f"  {Color.DIM}{'─' * 60}{Color.RESET}")
    print(
        f"  {'端点':<20} {'QPS':>8} {'P50':>8} {'P95':>8} "
        f"{'P99':>8} {'错误率':>8} {'状态':>6}"
    )
    print(f"  {Color.DIM}{'─' * 60}{Color.RESET}")

    for key, stats in result.endpoints.items():
        p99_color = Color.GREEN if stats.meets_p99_target else Color.RED
        err_color = Color.GREEN if stats.error_rate < 1 else (Color.YELLOW if stats.error_rate < 5 else Color.RED)
        status = Color.GREEN + "OK" + Color.RESET if stats.meets_p99_target and stats.error_rate < 1 else Color.RED + "FAIL" + Color.RESET

        print(
            f"  {stats.description:<18} {stats.qps:>8.1f} {stats.p50_ms:>7.1f}ms "
            f"{stats.p95_ms:>7.1f}ms {p99_color}{stats.p99_ms:>7.1f}ms{Color.RESET} "
            f"{err_color}{stats.error_rate:>7.2f}%{Color.RESET} {status}"
        )

    print(f"  {Color.DIM}{'─' * 60}{Color.RESET}")
    print(f"  总耗时: {result.wall_time_s:.1f}s")


def print_full_report(all_results: list[ConcurrencyLevelResult]) -> None:
    """打印完整的彩色终端报告"""
    print()
    print(f"{Color.BOLD}{'=' * 80}{Color.RESET}")
    print(f"{Color.BOLD}  UAV Platform V2 - 多级并发压力测试报告{Color.RESET}")
    print(f"  生成时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"  并发级别: {[r.concurrency for r in all_results]}")
    print(f"  P99 目标: <{P99_TARGET_MS}ms | SLA 可用性: >={SLA_AVAILABILITY}%")
    print(f"{Color.BOLD}{'=' * 80}{Color.RESET}")

    # ── 汇总表 ──
    print(f"\n{Color.CYAN}{Color.BOLD}  [1] 各端点性能汇总{Color.RESET}\n")

    for key in ENDPOINTS:
        print(f"  {Color.BOLD}{ENDPOINTS[key]['description']}{Color.RESET} ({key})")
        print(
            f"  {'并发':>6} {'QPS':>10} {'P50(ms)':>10} {'P95(ms)':>10} "
            f"{'P99(ms)':>10} {'错误率(%)':>10} {'可用性(%)':>10} {'SLA':>6}"
        )
        print(f"  {Color.DIM}{'─' * 74}{Color.RESET}")

        for result in all_results:
            stats = result.endpoints.get(key)
            if not stats:
                continue
            p99_c = Color.GREEN if stats.meets_p99_target else Color.RED
            err_c = Color.GREEN if stats.error_rate < 1 else Color.RED
            sla_str = Color.GREEN + "PASS" + Color.RESET if stats.meets_sla else Color.RED + "FAIL" + Color.RESET

            print(
                f"  {stats.concurrency:>6} {stats.qps:>10.1f} {stats.p50_ms:>10.1f} "
                f"{stats.p95_ms:>10.1f} {p99_c}{stats.p99_ms:>10.1f}{Color.RESET} "
                f"{err_c}{stats.error_rate:>10.2f}{Color.RESET} "
                f"{stats.availability:>10.2f} {sla_str}"
            )
        print()

    # ── 扩展性分析 ──
    print(f"{Color.CYAN}{Color.BOLD}  [2] 并发扩展性分析{Color.RESET}\n")
    print(
        f"  {'并发':>6} {'总QPS':>10} {'平均P99(ms)':>14} {'平均错误率(%)':>14} "
        f"{'扩展效率':>10}"
    )
    print(f"  {Color.DIM}{'─' * 58}{Color.RESET}")

    prev_qps = None
    for result in all_results:
        total_qps = sum(s.qps for s in result.endpoints.values())
        avg_p99 = statistics.mean(
            [s.p99_ms for s in result.endpoints.values() if s.response_times]
        ) if any(s.response_times for s in result.endpoints.values()) else 0
        avg_err = statistics.mean(
            [s.error_rate for s in result.endpoints.values() if s.total > 0]
        ) if any(s.total > 0 for s in result.endpoints.values()) else 0

        if prev_qps and prev_qps > 0:
            efficiency = (total_qps / prev_qps) * 100
            eff_str = f"{efficiency:.0f}%"
            eff_color = Color.GREEN if efficiency > 70 else (Color.YELLOW if efficiency > 40 else Color.RED)
        else:
            eff_str = "BASE"
            eff_color = Color.DIM

        p99_c = Color.GREEN if avg_p99 < P99_TARGET_MS else Color.RED
        print(
            f"  {result.concurrency:>6} {total_qps:>10.1f} {p99_c}{avg_p99:>14.1f}{Color.RESET} "
            f"{avg_err:>14.2f} {eff_color}{eff_str:>10}{Color.RESET}"
        )
        prev_qps = total_qps

    print()

    # ── 最终判定 ──
    print(f"{Color.BOLD}{'─' * 80}{Color.RESET}")

    all_pass = all(
        stats.meets_p99_target and stats.meets_sla
        for result in all_results
        for stats in result.endpoints.values()
        if stats.total > 0
    )

    if all_pass:
        print(
            f"  {Color.GREEN}{Color.BG_GREEN}{Color.BOLD}"
            f"  PASS - 所有端点在所有并发级别下均满足 SLA 要求  "
            f"{Color.RESET}"
        )
    else:
        failed_endpoints = set()
        for result in all_results:
            for stats in result.endpoints.values():
                if stats.total > 0 and (not stats.meets_p99_target or not stats.meets_sla):
                    failed_endpoints.add(stats.endpoint_key)

        print(
            f"  {Color.RED}{Color.BG_RED}{Color.BOLD}"
            f"  FAIL - 以下端点未满足 SLA: {', '.join(sorted(failed_endpoints))}  "
            f"{Color.RESET}"
        )

    print(f"{Color.BOLD}{'─' * 80}{Color.RESET}\n")


# ============================================================
# JSON Report
# ============================================================

def generate_json_report(all_results: list[ConcurrencyLevelResult]) -> dict[str, Any]:
    """生成完整的 JSON 格式报告"""
    summary_data = []
    for result in all_results:
        total_qps = sum(s.qps for s in result.endpoints.values())
        avg_p99 = statistics.mean(
            [s.p99_ms for s in result.endpoints.values() if s.response_times]
        ) if any(s.response_times for s in result.endpoints.values()) else 0
        avg_err = statistics.mean(
            [s.error_rate for s in result.endpoints.values() if s.total > 0]
        ) if any(s.total > 0 for s in result.endpoints.values()) else 0
        summary_data.append({
            "concurrency": result.concurrency,
            "total_qps": round(total_qps, 2),
            "avg_p99_ms": round(avg_p99, 2),
            "avg_error_rate_pct": round(avg_err, 2),
            "wall_time_s": round(result.wall_time_s, 2),
        })

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "test_config": {
            "base_url": DEFAULT_BASE_URL,
            "concurrency_levels": [r.concurrency for r in all_results],
            "duration_per_level_s": DEFAULT_DURATION,
            "p99_target_ms": P99_TARGET_MS,
            "sla_availability_pct": SLA_AVAILABILITY,
            "request_timeout_s": REQUEST_TIMEOUT,
            "endpoints_tested": list(ENDPOINTS.keys()),
        },
        "summary_by_concurrency": summary_data,
        "details": [r.to_dict() for r in all_results],
    }


# ============================================================
# Markdown Report
# ============================================================

def generate_markdown_report(all_results: list[ConcurrencyLevelResult]) -> str:
    """生成 Markdown 格式报告"""
    lines: list[str] = []
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    lines.append(f"# UAV Platform V2 - 多级并发压力测试报告\n")
    lines.append(f"> 生成时间: {ts} UTC\n")
    lines.append(f"> 并发级别: {', '.join(str(r.concurrency) for r in all_results)}")
    lines.append(f"> 每级持续时间: {DEFAULT_DURATION}s")
    lines.append(f"> P99 目标: <{P99_TARGET_MS}ms | SLA 可用性: >= {SLA_AVAILABILITY}%\n")

    # 各端点详细表格
    for key, config in ENDPOINTS.items():
        lines.append(f"## {config['description']} (`{key}`)\n")
        lines.append(f"**分类:** {config['category']} | **方法:** {config['method']} {config['path']}\n")
        lines.append(
            f"| 并发 | QPS | P50 (ms) | P95 (ms) | P99 (ms) | 错误率 (%) | 可用性 (%) | SLA |"
        )
        lines.append(
            f"|------|-----|----------|----------|----------|------------|------------|-----|"
        )

        for result in all_results:
            stats = result.endpoints.get(key)
            if not stats:
                continue
            sla = "PASS" if stats.meets_sla else "FAIL"
            lines.append(
                f"| {stats.concurrency} | {stats.qps:.1f} | {stats.p50_ms:.1f} | "
                f"{stats.p95_ms:.1f} | {stats.p99_ms:.1f} | {stats.error_rate:.2f} | "
                f"{stats.availability:.2f} | {sla} |"
            )
        lines.append("")

    # 扩展性分析
    lines.append("## 并发扩展性分析\n")
    lines.append(
        "| 并发 | 总 QPS | 平均 P99 (ms) | 平均错误率 (%) | 扩展效率 |"
    )
    lines.append(
        "|------|--------|---------------|----------------|----------|"
    )

    prev_qps = None
    for result in all_results:
        total_qps = sum(s.qps for s in result.endpoints.values())
        avg_p99 = statistics.mean(
            [s.p99_ms for s in result.endpoints.values() if s.response_times]
        ) if any(s.response_times for s in result.endpoints.values()) else 0
        avg_err = statistics.mean(
            [s.error_rate for s in result.endpoints.values() if s.total > 0]
        ) if any(s.total > 0 for s in result.endpoints.values()) else 0

        if prev_qps and prev_qps > 0:
            efficiency = f"{(total_qps / prev_qps) * 100:.0f}%"
        else:
            efficiency = "BASE"
        lines.append(
            f"| {result.concurrency} | {total_qps:.1f} | {avg_p99:.1f} | "
            f"{avg_err:.2f} | {efficiency} |"
        )
        prev_qps = total_qps

    lines.append("")

    # 结论
    lines.append("## 结论\n")
    all_pass = all(
        stats.meets_p99_target and stats.meets_sla
        for result in all_results
        for stats in result.endpoints.values()
        if stats.total > 0
    )
    if all_pass:
        lines.append("**测试结果: PASS** - 所有端点在所有并发级别下均满足 SLA 要求。")
    else:
        lines.append("**测试结果: FAIL** - 部分端点在特定并发级别下未满足 SLA 要求。")
        for result in all_results:
            for stats in result.endpoints.values():
                if stats.total > 0 and (not stats.meets_p99_target or not stats.meets_sla):
                    reasons = []
                    if not stats.meets_p99_target:
                        reasons.append(f"P99={stats.p99_ms:.1f}ms >= {P99_TARGET_MS}ms")
                    if not stats.meets_sla:
                        reasons.append(f"可用性={stats.availability:.2f}% < {SLA_AVAILABILITY}%")
                    lines.append(f"- `{stats.endpoint_key}` @ 并发{stats.concurrency}: {', '.join(reasons)}")

    lines.append("")
    return "\n".join(lines)


# ============================================================
# Main
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="UAV Platform V2 - 多级并发压力测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                                    # 默认配置运行
  %(prog)s --base-url http://10.0.0.1:8260   # 指定目标地址
  %(prog)s --concurrency-levels 10 50 100    # 自定义并发级别
  %(prog)s --duration 30                      # 每级 30 秒
  %(prog)s --json-output                     # 输出 JSON
  %(prog)s --markdown-output report.md       # 输出 Markdown
  %(prog)s --no-color                         # 禁用颜色
        """,
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"基础 URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--concurrency-levels",
        type=int,
        nargs="+",
        default=DEFAULT_CONCURRENCY_LEVELS,
        help=f"并发级别列表 (default: {' '.join(str(x) for x in DEFAULT_CONCURRENCY_LEVELS)})",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=DEFAULT_DURATION,
        help=f"每个并发级别的测试持续时间/秒 (default: {DEFAULT_DURATION})",
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="输出 JSON 格式报告到 stdout",
    )
    parser.add_argument(
        "--markdown-output",
        type=str,
        default=None,
        metavar="FILE",
        help="输出 Markdown 报告到指定文件",
    )
    parser.add_argument(
        "--json-file",
        type=str,
        default=None,
        metavar="FILE",
        help="输出 JSON 报告到指定文件",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="禁用彩色终端输出",
    )
    args = parser.parse_args()

    if args.no_color or args.json_output:
        Color.disable()

    # 打印配置
    if not args.json_output:
        print(f"\n{Color.BOLD}{'=' * 80}{Color.RESET}")
        print(f"{Color.BOLD}  UAV Platform V2 - 多级并发压力测试{Color.RESET}")
        print(f"{Color.BOLD}{'=' * 80}{Color.RESET}")
        print(f"  目标地址:     {args.base_url}")
        print(f"  并发级别:     {args.concurrency_levels}")
        print(f"  每级持续时间: {args.duration}s")
        print(f"  请求超时:     {REQUEST_TIMEOUT}s")
        print(f"  P99 目标:     <{P99_TARGET_MS}ms")
        print(f"  SLA 可用性:   >= {SLA_AVAILABILITY}%")
        print(f"  测试端点:     {len(ENDPOINTS)} 个")
        for key, cfg in ENDPOINTS.items():
            print(f"    - {cfg['method']} {cfg['path']}  ({cfg['description']})")
        print(f"{Color.BOLD}{'=' * 80}{Color.RESET}")

    # 运行测试
    total_start = time.monotonic()
    all_results = run_all_tests(
        base_url=args.base_url,
        concurrency_levels=args.concurrency_levels,
        duration_s=args.duration,
    )
    total_time = time.monotonic() - total_start

    # 输出结果
    if args.json_output:
        report = generate_json_report(all_results)
        report["total_wall_time_s"] = round(total_time, 2)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_full_report(all_results)
        print(f"{Color.DIM}  总测试耗时: {total_time:.1f}s{Color.RESET}\n")

    # 写入文件
    if args.json_file:
        report = generate_json_report(all_results)
        report["total_wall_time_s"] = round(total_time, 2)
        with open(args.json_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        if not args.json_output:
            print(f"  JSON 报告已保存: {args.json_file}")

    if args.markdown_output:
        md = generate_markdown_report(all_results)
        with open(args.markdown_output, "w", encoding="utf-8") as f:
            f.write(md)
        if not args.json_output:
            print(f"  Markdown 报告已保存: {args.markdown_output}")

    # 退出码
    has_failure = any(
        not stats.meets_p99_target or not stats.meets_sla
        for result in all_results
        for stats in result.endpoints.values()
        if stats.total > 0
    )
    sys.exit(1 if has_failure else 0)


if __name__ == "__main__":
    main()
