#!/usr/bin/env python3
"""
UAV Platform - Performance Benchmark (Python)
Tests key API endpoints for response time, throughput, and error rate
"""
import asyncio
import aiohttp
import time
import statistics
import json
import sys
from dataclasses import dataclass
from typing import List


@dataclass
class BenchmarkResult:
    endpoint: str
    avg_response_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    throughput: float
    error_rate: float
    total_requests: int


class BenchRunner:
    def __init__(self, base_url: str = "http://localhost:8088"):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def run_single(self, session, endpoint: str, method: str = "GET", **kwargs) -> dict:
        start = time.time()
        try:
            url = f"{self.base_url}{endpoint}"
            async with session.request(method, url, timeout=self.timeout, **kwargs) as resp:
                elapsed = (time.time() - start) * 1000
                return {"success": resp.status < 500, "status": resp.status, "elapsed_ms": elapsed}
        except Exception as e:
            return {"success": False, "error": str(e), "elapsed_ms": (time.time() - start) * 1000}

    async def benchmark_endpoint(self, endpoint: str, concurrency: int = 20,
                                 requests: int = 100, method: str = "GET", **kwargs) -> BenchmarkResult:
        connector = aiohttp.TCPConnector(limit=concurrency, limit_per_host=concurrency)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self.run_single(session, endpoint, method, **kwargs) for _ in range(requests)]
            results = await asyncio.gather(*tasks)

        elapsed_list = [r["elapsed_ms"] for r in results]
        errors = [r for r in results if not r["success"]]
        sorted_elapsed = sorted(elapsed_list)

        return BenchmarkResult(
            endpoint=endpoint,
            avg_response_ms=statistics.mean(elapsed_list) if elapsed_list else 0,
            p50_ms=sorted_elapsed[len(sorted_elapsed)//2] if sorted_elapsed else 0,
            p95_ms=sorted_elapsed[int(len(sorted_elapsed)*0.95)] if sorted_elapsed else 0,
            p99_ms=sorted_elapsed[int(len(sorted_elapsed)*0.99)] if sorted_elapsed else 0,
            throughput=len(elapsed_list) / (sum(elapsed_list)/1000) if elapsed_list else 0,
            error_rate=len(errors) / max(len(results), 1) * 100,
            total_requests=len(results)
        )


async def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8088"
    runner = BenchRunner(base_url)

    endpoints = [
        ("GET", "/actuator/health"),
        ("POST", "/v1/auth/login", {"json": {"username": "admin", "password": "test"}}),
        ("GET", "/api/platform/drones?page=0&size=10"),
        ("GET", "/api/forecast/meteor?lat=31.23&lon=121.47"),
        ("GET", "/api/wrf/data?fileId=test"),
    ]

    print("=" * 70)
    print("  UAV Platform Performance Benchmark")
    print(f"  Target: {base_url}")
    print("  Concurrency: 20, Requests per endpoint: 100")
    print("=" * 70)

    results = []
    for method, endpoint, *extra in endpoints:
        kwargs = extra[0] if extra else {}
        print(f"\n📡 Testing: {method} {endpoint}")
        result = await runner.benchmark_endpoint(endpoint, method=method, **kwargs)
        results.append(result)
        print(f"    Avg: {result.avg_response_ms:7.1f}ms | P50: {result.p50_ms:6.1f}ms | "
              f"P95: {result.p95_ms:6.1f}ms | P99: {result.p99_ms:6.1f}ms | "
              f"TPS: {result.throughput:6.0f} | ❌: {result.error_rate:.1f}%")

    print("\n" + "=" * 70)
    print("  Summary")
    print("=" * 70)

    all_ok = all(r.error_rate < 1.0 for r in results)
    all_fast = all(r.p95_ms < 500 for r in results)

    if all_ok and all_fast:
        print("  ✅ ALL BENCHMARKS PASSED")
    else:
        if not all_ok:
            print("  ❌ Some endpoints have high error rates")
        if not all_fast:
            print("  ❌ Some endpoints exceed P95 < 500ms target")
        for r in results:
            if r.error_rate >= 1.0:
                print(f"    - {r.endpoint}: error rate {r.error_rate:.1f}%")
            if r.p95_ms >= 500:
                print(f"    - {r.endpoint}: P95 {r.p95_ms:.1f}ms > 500ms")

    print("=" * 70)
    return 0 if (all_ok and all_fast) else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
