#!/usr/bin/env python3
"""
UAV Platform V2 - 性能基准测试脚本

使用并发 HTTP 请求对平台各端点进行压力测试，输出延迟分布和吞吐量指标。

测试端点:
  1. Algorithm Engine: GET /api/v1/algorithms (列表查询)
  2. Algorithm Engine: POST /api/v1/algorithms/astar/execute (A* 执行)
  3. API Gateway: GET /actuator/health (网关健康)
  4. platform-api: GET /actuator/health (平台健康)

用法:
    python scripts/perf-benchmark.py
    python scripts/perf-benchmark.py --concurrency 20 --requests 200
    python scripts/perf-benchmark.py --url http://192.168.1.100
    python scripts/perf-benchmark.py --json-output > report.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

try:
    import requests
except ImportError:
    print("ERROR: 请先安装 requests 库: pip install requests")
    sys.exit(1)


# ============================================================
# ANSI Color Codes
# ============================================================

class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    DIM = "\033[2m"

    @staticmethod
    def disable() -> None:
        Color.RESET = ""
        Color.BOLD = ""
        Color.RED = ""
        Color.GREEN = ""
        Color.YELLOW = ""
        Color.CYAN = ""
        Color.WHITE = ""
        Color.DIM = ""


# ============================================================
# Configuration
# ============================================================

DEFAULT_BASE_URL = "http://localhost"
DEFAULT_CONCURRENCY = 10
DEFAULT_REQUESTS = 100
REQUEST_TIMEOUT = 10  # 单个请求超时秒数
P99_TARGET_MS = 500  # P99 成功标准 (毫秒)

# 端点定义
ENDPOINTS = {
    "algorithm-list": {
        "method": "GET",
        "path": "/api/v1/algorithms",
        "port": 9095,
        "description": "Algorithm Engine - 算法列表查询",
    },
    "astar-execute": {
        "method": "POST",
        "path": "/api/v1/algorithms/astar/execute",
        "port": 9095,
        "description": "Algorithm Engine - A* 路径规划执行",
        "payload": {
            "start": [0, 0],
            "goal": [10, 10],
            "grid_size": [20, 20],
            "obstacles": [[3, 3], [3, 4], [4, 3]],
        },
    },
    "gateway-health": {
        "method": "GET",
        "path": "/actuator/health",
        "port": 8258,
        "description": "API Gateway - 健康检查",
    },
    "platform-health": {
        "method": "GET",
        "path": "/actuator/health",
        "port": 8251,
        "description": "platform-api - 健康检查",
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


@dataclass
class BenchmarkStats:
    """单个端点的基准测试统计"""
    endpoint_key: str
    description: str
    total: int = 0
    success: int = 0
    failed: int = 0
    response_times: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def error_rate(self) -> float:
        return (self.failed / self.total * 100) if self.total > 0 else 0.0

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
    def p50_ms(self) -> float:
        return _percentile(self.response_times, 50) if self.response_times else 0.0

    @property
    def p95_ms(self) -> float:
        return _percentile(self.response_times, 95) if self.response_times else 0.0

    @property
    def p99_ms(self) -> float:
        return _percentile(self.response_times, 99) if self.response_times else 0.0

    @property
    def rps(self) -> float:
        """基于成功请求的每秒吞吐量"""
        if not self.response_times:
            return 0.0
        total_time_s = sum(self.response_times) / 1000.0
        return self.success / total_time_s if total_time_s > 0 else 0.0

    @property
    def meets_p99_target(self) -> bool:
        return self.p99_ms < P99_TARGET_MS

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint_key,
            "description": self.description,
            "total": self.total,
            "success": self.success,
            "failed": self.failed,
            "error_rate_pct": round(self.error_rate, 2),
            "avg_ms": round(self.avg_ms, 2),
            "min_ms": round(self.min_ms, 2),
            "max_ms": round(self.max_ms, 2),
            "p50_ms": round(self.p50_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "p99_ms": round(self.p99_ms, 2),
            "rps": round(self.rps, 2),
            "meets_p99_target": self.meets_p99_target,
            "errors": self.errors[:10],  # 最多记录 10 条错误
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


def _send_request(base_url: str, endpoint_key: str, endpoint_config: dict) -> RequestResult:
    """发送单个 HTTP 请求并记录结果"""
    url = f"{base_url}:{endpoint_config['port']}{endpoint_config['path']}"
    method = endpoint_config["method"]

    start = time.monotonic()
    try:
        if method == "GET":
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        elif method == "POST":
            payload = endpoint_config.get("payload", {})
            resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        else:
            return RequestResult(
                endpoint_key=endpoint_key,
                success=False,
                error=f"不支持的 HTTP 方法: {method}",
            )

        elapsed_ms = (time.monotonic() - start) * 1000.0
        success = 200 <= resp.status_code < 400

        return RequestResult(
            endpoint_key=endpoint_key,
            success=success,
            status_code=resp.status_code,
            response_time_ms=elapsed_ms,
            error=None if success else f"HTTP {resp.status_code}",
        )
    except requests.exceptions.ConnectionError:
        elapsed_ms = (time.monotonic() - start) * 1000.0
        return RequestResult(
            endpoint_key=endpoint_key,
            success=False,
            response_time_ms=elapsed_ms,
            error="连接拒绝",
        )
    except requests.exceptions.Timeout:
        elapsed_ms = (time.monotonic() - start) * 1000.0
        return RequestResult(
            endpoint_key=endpoint_key,
            success=False,
            response_time_ms=elapsed_ms,
            error=f"请求超时 ({REQUEST_TIMEOUT}s)",
        )
    except Exception as e:
        elapsed_ms = (time.monotonic() - start) * 1000.0
        return RequestResult(
            endpoint_key=endpoint_key,
            success=False,
            response_time_ms=elapsed_ms,
            error=str(e),
        )


# ============================================================
# Benchmark Runner
# ============================================================

def run_benchmark(
    base_url: str,
    endpoint_key: str,
    endpoint_config: dict,
    concurrency: int,
    total_requests: int,
) -> BenchmarkStats:
    """对单个端点运行基准测试"""
    stats = BenchmarkStats(
        endpoint_key=endpoint_key,
        description=endpoint_config["description"],
    )

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(_send_request, base_url, endpoint_key, endpoint_config): i
            for i in range(total_requests)
        }

        for future in as_completed(futures):
            result: RequestResult = future.result()
            stats.total += 1
            if result.success:
                stats.success += 1
                stats.response_times.append(result.response_time_ms)
            else:
                stats.failed += 1
                if result.error:
                    stats.errors.append(result.error)

    return stats


def run_all_benchmarks(
    base_url: str,
    concurrency: int,
    total_requests: int,
) -> list[BenchmarkStats]:
    """对所有端点运行基准测试"""
    all_stats: list[BenchmarkStats] = []

    for endpoint_key, endpoint_config in ENDPOINTS.items():
        stats = run_benchmark(
            base_url=base_url,
            endpoint_key=endpoint_key,
            endpoint_config=endpoint_config,
            concurrency=concurrency,
            total_requests=total_requests,
        )
        all_stats.append(stats)

    return all_stats


# ============================================================
# Report Output
# ============================================================

def print_report(all_stats: list[BenchmarkStats], total_wall_time: float) -> None:
    """打印彩色基准测试报告"""
    print()
    print(f"{Color.BOLD}{'=' * 80}{Color.RESET}")
    print(f"{Color.BOLD}  UAV Platform V2 - 性能基准测试报告{Color.RESET}")
    print(f"  生成时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"  总耗时: {total_wall_time:.2f}s")
    print(f"  P99 成功标准: <{P99_TARGET_MS}ms")
    print(f"{Color.BOLD}{'=' * 80}{Color.RESET}")
    print()

    # 汇总
    grand_total = sum(s.total for s in all_stats)
    grand_success = sum(s.success for s in all_stats)
    grand_failed = sum(s.failed for s in all_stats)
    grand_error_rate = (grand_failed / grand_total * 100) if grand_total > 0 else 0.0
    all_response_times = []
    for s in all_stats:
        all_response_times.extend(s.response_times)
    grand_avg = statistics.mean(all_response_times) if all_response_times else 0.0
    grand_p50 = _percentile(all_response_times, 50) if all_response_times else 0.0
    grand_p95 = _percentile(all_response_times, 95) if all_response_times else 0.0
    grand_p99 = _percentile(all_response_times, 99) if all_response_times else 0.0
    grand_rps = grand_success / total_wall_time if total_wall_time > 0 else 0.0

    print(f"  {Color.CYAN}--- 汇总 ---{Color.RESET}")
    print()
    print(f"    总请求数:   {grand_total}")
    print(f"    成功数:     {Color.GREEN}{grand_success}{Color.RESET}")
    print(f"    失败数:     {Color.RED}{grand_failed}{Color.RESET}")
    print(f"    错误率:     {Color.RED if grand_error_rate > 5 else Color.GREEN}{grand_error_rate:.2f}%{Color.RESET}")
    print(f"    平均响应:   {grand_avg:.2f}ms")
    print(f"    P50:        {grand_p50:.2f}ms")
    print(f"    P95:        {grand_p95:.2f}ms")
    print(f"    P99:        {Color.RED if grand_p99 >= P99_TARGET_MS else Color.GREEN}{grand_p99:.2f}ms{Color.RESET}")
    print(f"    吞吐量:     {grand_rps:.2f} RPS")
    print(f"    P99 达标:   {'YES' if grand_p99 < P99_TARGET_MS else 'NO'}")
    print()

    # 各端点详情
    print(f"  {Color.CYAN}--- 各端点详情 ---{Color.RESET}")
    print()

    for stats in all_stats:
        p99_tag = Color.GREEN if stats.meets_p99_target else Color.RED
        err_tag = Color.RED if stats.error_rate > 5 else Color.GREEN

        print(f"    {Color.BOLD}{stats.description}{Color.RESET}")
        print(f"      端点:       {stats.endpoint_key}")
        print(f"      请求数:     {stats.total}")
        print(f"      成功/失败:  {Color.GREEN}{stats.success}{Color.RESET} / {Color.RED}{stats.failed}{Color.RESET}")
        print(f"      错误率:     {err_tag}{stats.error_rate:.2f}%{Color.RESET}")
        print(f"      平均响应:   {stats.avg_ms:.2f}ms")
        print(f"      Min/Max:    {stats.min_ms:.2f}ms / {stats.max_ms:.2f}ms")
        print(f"      P50/P95/P99:{stats.p50_ms:.2f}ms / {stats.p95_ms:.2f}ms / {p99_tag}{stats.p99_ms:.2f}ms{Color.RESET}")
        print(f"      吞吐量:     {stats.rps:.2f} RPS")
        print(f"      P99 达标:   {'YES' if stats.meets_p99_target else 'NO'}")

        if stats.errors:
            error_summary: dict[str, int] = {}
            for e in stats.errors:
                error_summary[e] = error_summary.get(e, 0) + 1
            top_errors = sorted(error_summary.items(), key=lambda x: -x[1])[:3]
            error_str = ", ".join(f"{err}({cnt}x)" for err, cnt in top_errors)
            print(f"      主要错误:   {Color.DIM}{error_str}{Color.RESET}")
        print()

    # 最终判定
    all_pass = all(s.meets_p99_target for s in all_stats if s.total > 0)
    print(f"{Color.BOLD}{'-' * 80}{Color.RESET}")
    if all_pass and grand_error_rate == 0:
        print(f"  {Color.GREEN}{Color.BOLD}*** 基准测试结果: PASS (所有端点 P99 < {P99_TARGET_MS}ms, 零错误) ***{Color.RESET}")
    elif all_pass:
        print(f"  {Color.YELLOW}{Color.BOLD}*** 基准测试结果: PASS (所有端点 P99 < {P99_TARGET_MS}ms, 存在错误) ***{Color.RESET}")
    else:
        print(f"  {Color.RED}{Color.BOLD}*** 基准测试结果: FAIL (存在端点 P99 >= {P99_TARGET_MS}ms) ***{Color.RESET}")
    print(f"{Color.BOLD}{'-' * 80}{Color.RESET}")
    print()


def generate_json_report(all_stats: list[BenchmarkStats], total_wall_time: float) -> dict[str, Any]:
    """生成 JSON 格式报告"""
    all_response_times = []
    for s in all_stats:
        all_response_times.extend(s.response_times)

    grand_total = sum(s.total for s in all_stats)
    grand_success = sum(s.success for s in all_stats)
    grand_failed = sum(s.failed for s in all_stats)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": {
            "concurrency": DEFAULT_CONCURRENCY,
            "requests_per_endpoint": DEFAULT_REQUESTS,
            "p99_target_ms": P99_TARGET_MS,
            "request_timeout_s": REQUEST_TIMEOUT,
        },
        "summary": {
            "total_wall_time_s": round(total_wall_time, 2),
            "total_requests": grand_total,
            "total_success": grand_success,
            "total_failed": grand_failed,
            "error_rate_pct": round(
                (grand_failed / grand_total * 100) if grand_total > 0 else 0.0, 2
            ),
            "avg_ms": round(
                statistics.mean(all_response_times) if all_response_times else 0.0, 2
            ),
            "p50_ms": round(
                _percentile(all_response_times, 50) if all_response_times else 0.0, 2
            ),
            "p95_ms": round(
                _percentile(all_response_times, 95) if all_response_times else 0.0, 2
            ),
            "p99_ms": round(
                _percentile(all_response_times, 99) if all_response_times else 0.0, 2
            ),
            "rps": round(grand_success / total_wall_time, 2) if total_wall_time > 0 else 0.0,
            "meets_p99_target": all(
                s.meets_p99_target for s in all_stats if s.total > 0
            ),
        },
        "endpoints": [s.to_dict() for s in all_stats],
    }


# ============================================================
# Main
# ============================================================

def main() -> None:
    global DEFAULT_CONCURRENCY, DEFAULT_REQUESTS

    parser = argparse.ArgumentParser(
        description="UAV Platform V2 - 性能基准测试脚本"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"并发线程数 (default: {DEFAULT_CONCURRENCY})",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=DEFAULT_REQUESTS,
        help=f"每个端点的总请求数 (default: {DEFAULT_REQUESTS})",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_BASE_URL,
        help=f"基础 URL (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="输出 JSON 格式报告",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="禁用彩色输出",
    )
    parser.add_argument(
        "--endpoint",
        choices=list(ENDPOINTS.keys()),
        default=None,
        help="仅测试指定端点 (默认测试全部)",
    )
    args = parser.parse_args()

    DEFAULT_CONCURRENCY = args.concurrency
    DEFAULT_REQUESTS = args.requests

    # 禁用颜色
    if args.no_color or args.json_output:
        Color.disable()

    # 打印标题
    if not args.json_output:
        print(f"{Color.BOLD}{'=' * 80}{Color.RESET}")
        print(f"{Color.BOLD}  UAV Platform V2 - 性能基准测试{Color.RESET}")
        print(f"{Color.BOLD}{'=' * 80}{Color.RESET}")
        print(f"  基础 URL:    {args.url}")
        print(f"  并发数:      {args.concurrency}")
        print(f"  每端点请求数: {args.requests}")
        print(f"  请求超时:    {REQUEST_TIMEOUT}s")
        print(f"  P99 标准:    <{P99_TARGET_MS}ms")
        if args.endpoint:
            print(f"  测试端点:    {args.endpoint} ({ENDPOINTS[args.endpoint]['description']})")
        else:
            print(f"  测试端点:    全部 ({len(ENDPOINTS)} 个)")
        print(f"{Color.BOLD}{'=' * 80}{Color.RESET}")
        print()

    # 选择要测试的端点
    endpoints_to_test = (
        {args.endpoint: ENDPOINTS[args.endpoint]}
        if args.endpoint
        else ENDPOINTS
    )

    # 运行基准测试
    wall_start = time.monotonic()
    all_stats = run_all_benchmarks(
        base_url=args.url,
        concurrency=args.concurrency,
        total_requests=args.requests,
    )
    # 如果指定了单个端点, 过滤结果
    if args.endpoint:
        all_stats = [s for s in all_stats if s.endpoint_key == args.endpoint]
    total_wall_time = time.monotonic() - wall_start

    # 输出报告
    if args.json_output:
        report = generate_json_report(all_stats, total_wall_time)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(all_stats, total_wall_time)

    # 退出码: 如果任何端点 P99 不达标或存在错误则返回 1
    has_failure = any(
        not s.meets_p99_target or s.failed > 0
        for s in all_stats
        if s.total > 0
    )
    sys.exit(1 if has_failure else 0)


if __name__ == "__main__":
    main()
