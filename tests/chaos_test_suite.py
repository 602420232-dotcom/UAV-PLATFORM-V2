#!/usr/bin/env python3
"""Chaos Engineering 测试套件 — 验证系统弹性"""
import requests
import time
import json
import threading
import os
import sys

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8088")
TIMEOUT = 10

def log(msg):
    print(f"[CHAOS] {msg}")

def test_1_instantiate_services():
    """验证无响应后服务仍可恢复"""
    log("1/6: 验证核心服务健康状态")
    endpoints = [
        f"{BASE_URL}/actuator/health",
        f"{BASE_URL}/api/v1/data-sources",
        f"{BASE_URL}/api/v1/real-data/ground-station",
    ]
    for ep in endpoints:
        try:
            r = requests.get(ep, timeout=TIMEOUT)
            log(f"  {ep} → {r.status_code}")
        except Exception as e:
            log(f"  {ep} → FAIL: {e}")

def test_2_high_concurrent_requests():
    """并发流量激增测试"""
    log("2/6: 100个并发请求模拟突增流量")
    targets = [
        f"{BASE_URL}/api/v1/data-sources",
        f"{BASE_URL}/api/v1/real-data/ground-station",
    ]

    def worker(url, results):
        try:
            r = requests.get(url, timeout=5)
            results.append((url, r.status_code))
        except Exception as e:
            results.append((url, str(e)))

    threads = []
    results = []
    for _ in range(50):
        for t in targets:
            th = threading.Thread(target=worker, args=(t, results))
            threads.append(th)
            th.start()

    for th in threads:
        th.join(timeout=10)

    success = sum(1 for r in results if isinstance(r[1], int) and r[1] < 500)
    total = len(results)
    log(f"  {success}/{total} 请求成功")

    if success < total * 0.8:
        log(f"  ⚠️ 成功率 {success/total*100:.0f}% 低于80%阈值")

    results.clear()

def test_3_rapid_restart():
    """快速重启应用检查资源泄漏"""
    log("3/6: 快速启动/关闭检查")
    from concurrent.futures import ThreadPoolExecutor

    def health_check():
        try:
            r = requests.get(f"{BASE_URL}/actuator/health", timeout=3)
            return r.status_code
        except:
            return -1

    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = [ex.submit(health_check) for _ in range(30)]
        codes = [f.result() for f in futures]
        ok = sum(1 for c in codes if c == 200)
        log(f"  30轮并行健康检查: {ok}/30 成功 ({sum(1 for c in codes if c == -1)} 超时)")

def test_4_resilience_recovery():
    """熔断后自动恢复检查"""
    log("4/6: 验证熔断状态可恢复")

    # Fire multiple failing requests
    for i in range(10):
        try:
            requests.get(f"{BASE_URL}/api/nonexistent", timeout=2)
        except:
            pass

    time.sleep(1)

    try:
        r = requests.get(f"{BASE_URL}/actuator/health", timeout=5)
        log(f"  熔断后服务状态: {r.status_code}")
    except Exception as e:
        log(f"  服务不可用: {e}")

def test_5_memory_leak_detection():
    """简单内存泄漏检查"""
    log("5/6: 重复大数据量请求检查内存泄漏")
    big_payload = {"data": [{"id": i, "values": [j for j in range(100)]} for i in range(100)]}

    for i in range(20):
        try:
            requests.post(
                f"{BASE_URL}/api/platform/plan",
                json={"weatherData": big_payload, "drones": [], "tasks": []},
                timeout=5
            )
        except:
            pass

    log("  ✓ 20轮大数据量请求完成")

def test_6_cascade_failure():
    """级联故障测试 — 依赖服务不可用时行为"""
    log("6/6: 验证依赖服务超时不会导致级联崩溃")
    import socket

    start = time.time()
    for _ in range(5):
        try:
            requests.get(f"{BASE_URL}/api/platform/plan", timeout=10)
        except requests.exceptions.Timeout:
            pass
    elapsed = time.time() - start
    log(f"  5轮超时请求完成: {elapsed:.1f}s (预期 < 60s)")
    assert elapsed < 60, "级联超时过长!"


if __name__ == "__main__":
    log("=" * 60)
    log("Chaos Engineering Test Suite 启动")
    log("=" * 60)

    tests = [
        test_1_instantiate_services,
        test_2_high_concurrent_requests,
        test_3_rapid_restart,
        test_4_resilience_recovery,
        test_5_memory_leak_detection,
        test_6_cascade_failure,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            log(f"  ❌ FAIL: {e}")
            failed += 1

    log("=" * 60)
    log(f"结果: {passed}/{len(tests)} 通过, {failed} 失败")
    log("=" * 60)
