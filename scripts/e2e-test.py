#!/usr/bin/env python3
"""
UAV Platform V2 - E2E 自动化测试脚本

端到端功能测试，覆盖完整业务链路:
  测试1: 算法列表查询 (验证 102 个算法，按类别统计)
  测试2: 算法执行测试 (调用 A* 算法进行路径规划)
  测试3: 同化任务提交 (提交 3DVAR 任务)
  测试4: 风险评估 (发起风险评估)
  测试5: 气象数据查询 (单点气象查询)
  测试6: 观测决策 (信息增益计算)
  测试7: 路径规划 (RRT* 路径规划)
  测试8: 智能调度器 (assimilation smart-select)

用法:
    python scripts/e2e-test.py
    python scripts/e2e-test.py --verbose
    python scripts/e2e-test.py --json-output
    python scripts/e2e-test.py --host 192.168.1.100
"""

from __future__ import annotations

import argparse
import json
import sys
import time
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

DEFAULT_HOST = "localhost"
REQUEST_TIMEOUT = 30  # API 请求超时

# 服务端口 (灰度环境 Docker 映射)
ALGORITHM_ENGINE_URL = "http://localhost:9095"
ASSIMILATION_API_URL = "http://localhost:8253"
RISK_API_URL = "http://localhost:8254"
WEATHER_API_URL = "http://localhost:8252"
OBSERVATION_API_URL = "http://localhost:8255"
PLANNING_API_URL = "http://localhost:8256"

# 期望算法数量
EXPECTED_ALGORITHM_COUNT = 102


# ============================================================
# Test Result Tracker
# ============================================================

class TestResult:
    """E2E 测试结果跟踪器"""

    def __init__(self) -> None:
        self.passed: int = 0
        self.failed: int = 0
        self.skipped: int = 0
        self.details: list[dict[str, Any]] = []
        self.start_time: float = time.time()

    def record(
        self,
        test_id: int,
        test_name: str,
        status: str,
        request_time: float = 0.0,
        response_status: int = 0,
        message: str = "",
        validation: str = "",
        response_data: Any = None,
    ) -> None:
        entry = {
            "test_id": test_id,
            "test_name": test_name,
            "status": status,
            "request_time": round(request_time, 3),
            "response_status": response_status,
            "message": message,
            "validation": validation,
            "response_data": response_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.details.append(entry)
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        elif status == "SKIP":
            self.skipped += 1

    def print_report(self, verbose: bool = False) -> None:
        """打印彩色测试报告"""
        total_duration = round(time.time() - self.start_time, 3)

        print()
        print(f"{Color.BOLD}{'=' * 72}{Color.RESET}")
        print(f"{Color.BOLD}  UAV Platform V2 - E2E 自动化测试报告{Color.RESET}")
        print(f"  生成时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"  总耗时: {total_duration}s")
        print(f"{Color.BOLD}{'=' * 72}{Color.RESET}")
        print()

        for d in self.details:
            test_id = d["test_id"]
            test_name = d["test_name"]

            if d["status"] == "PASS":
                tag = f"{Color.GREEN}PASS{Color.RESET}"
            elif d["status"] == "FAIL":
                tag = f"{Color.RED}FAIL{Color.RESET}"
            elif d["status"] == "SKIP":
                tag = f"{Color.YELLOW}SKIP{Color.RESET}"
            else:
                tag = f"{Color.YELLOW}WARN{Color.RESET}"

            print(f"  {Color.BOLD}测试 {test_id}: {test_name}{Color.RESET}")
            print(f"    状态: [{tag}]")
            print(f"    请求时间: {d['request_time']}s")
            if d["response_status"]:
                print(f"    响应状态: HTTP {d['response_status']}")
            if d["message"]:
                for line in d["message"].split("\n"):
                    print(f"    {Color.DIM}{line}{Color.RESET}")
            if d["validation"]:
                for line in d["validation"].split("\n"):
                    print(f"    {Color.DIM}{line}{Color.RESET}")
            if verbose and d.get("response_data") is not None:
                try:
                    data_str = json.dumps(d["response_data"], indent=2, ensure_ascii=False)
                    if len(data_str) > 1000:
                        data_str = data_str[:1000] + "\n  ... (truncated)"
                    for line in data_str.split("\n"):
                        print(f"    {Color.DIM}{line}{Color.RESET}")
                except (TypeError, ValueError):
                    pass
            print()

        total = self.passed + self.failed + self.skipped
        print(f"{Color.BOLD}{'-' * 72}{Color.RESET}")
        print(
            f"  {Color.BOLD}总计: {total}  |  "
            f"{Color.GREEN}通过: {self.passed}  |  "
            f"{Color.RED}失败: {self.failed}  |  "
            f"{Color.YELLOW}跳过: {self.skipped}{Color.RESET}"
        )
        print(f"{Color.BOLD}{'-' * 72}{Color.RESET}")
        print()

        if self.failed > 0:
            print(f"  {Color.RED}{Color.BOLD}*** 测试结果: FAIL (存在失败项) ***{Color.RESET}")
        elif self.skipped > 0:
            print(f"  {Color.YELLOW}{Color.BOLD}*** 测试结果: PASS (存在跳过项) ***{Color.RESET}")
        else:
            print(f"  {Color.GREEN}{Color.BOLD}*** 测试结果: PASS (全部通过) ***{Color.RESET}")
        print()

    def to_json(self) -> dict[str, Any]:
        """输出 JSON 格式测试报告"""
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_duration": round(time.time() - self.start_time, 3),
            "summary": {
                "total": self.passed + self.failed + self.skipped,
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped,
                "result": "FAIL" if self.failed > 0 else "PASS",
            },
            "tests": [
                {
                    "test_id": d["test_id"],
                    "test_name": d["test_name"],
                    "status": d["status"],
                    "request_time": d["request_time"],
                    "response_status": d["response_status"],
                    "message": d["message"],
                    "validation": d["validation"],
                    "timestamp": d["timestamp"],
                }
                for d in self.details
            ],
        }


# ============================================================
# Test 1: 算法列表查询
# ============================================================

def test_algorithm_list(results: TestResult, verbose: bool = False) -> None:
    """测试1: 算法列表查询 - 验证 102 个算法，按类别统计"""
    test_id = 1
    test_name = "算法列表查询"
    url = f"{ALGORITHM_ENGINE_URL}/api/v1/algorithms"

    start = time.time()
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        duration = time.time() - start

        if resp.status_code == 200:
            body = resp.json()
            if isinstance(body, list):
                algo_count = len(body)

                # 按类别统计
                category_counts: dict[str, int] = {}
                for algo in body:
                    cat = algo.get("category", "unknown")
                    category_counts[cat] = category_counts.get(cat, 0) + 1

                cat_summary = ", ".join(
                    f"{cat}={cnt}" for cat, cnt in sorted(category_counts.items())
                )

                # 验证
                count_match = algo_count == EXPECTED_ALGORITHM_COUNT
                has_categories = len(category_counts) > 0

                validation_parts = []
                if count_match:
                    validation_parts.append(f"算法数量匹配: {algo_count}/{EXPECTED_ALGORITHM_COUNT}")
                else:
                    validation_parts.append(
                        f"算法数量不匹配: {algo_count} (期望 {EXPECTED_ALGORITHM_COUNT})"
                    )
                validation_parts.append(f"类别数: {len(category_counts)}")
                validation_parts.append(f"类别分布: {cat_summary}")

                # 验证每个算法有 id, name, category
                valid_structure = all(
                    a.get("id") and a.get("name") and a.get("category")
                    for a in body
                )
                validation_parts.append(f"结构完整性: {'通过' if valid_structure else '失败'}")

                status = "PASS" if count_match and valid_structure else "FAIL"
                message = f"查询到 {algo_count} 个算法"

                results.record(
                    test_id, test_name, status,
                    request_time=duration,
                    response_status=resp.status_code,
                    message=message,
                    validation="\n".join(validation_parts),
                    response_data=body[:10] if verbose else None,
                )
            else:
                results.record(
                    test_id, test_name, "FAIL",
                    request_time=duration,
                    response_status=resp.status_code,
                    message="响应格式异常",
                    validation=f"期望 list, 得到 {type(body).__name__}",
                )
        else:
            results.record(
                test_id, test_name, "FAIL",
                request_time=duration,
                response_status=resp.status_code,
                message=f"HTTP {resp.status_code}",
                validation="期望 HTTP 200",
            )
    except requests.exceptions.ConnectionError:
        duration = time.time() - start
        results.record(
            test_id, test_name, "FAIL",
            request_time=duration,
            response_status=0,
            message="连接拒绝 (算法引擎未启动)",
            validation="算法引擎服务不可达",
        )
    except Exception as e:
        duration = time.time() - start
        results.record(
            test_id, test_name, "FAIL",
            request_time=duration,
            response_status=0,
            message=str(e),
            validation="请求异常",
        )


# ============================================================
# Test 2: 算法执行测试 (A* 路径规划)
# ============================================================

def test_algorithm_execution(results: TestResult, verbose: bool = False) -> None:
    """测试2: 算法执行测试 - 调用 A* 算法进行路径规划"""
    test_id = 2
    test_name = "算法执行测试 (A* 路径规划)"
    url = f"{ALGORITHM_ENGINE_URL}/api/v1/tasks/submit"

    payload = {
        "algorithm_id": "a_star",
        "params": {
            "start": [0, 0],
            "goal": [19, 19],
            "grid_size": [20, 20],
            "obstacles": [
                [5, 5], [5, 6], [5, 7], [6, 5],
                [10, 10], [10, 11], [11, 10],
                [15, 3], [15, 4], [16, 3],
            ],
        },
        "priority": 5,
    }

    start = time.time()
    try:
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        duration = time.time() - start

        if resp.status_code in (200, 201):
            body = resp.json()
            task_id = body.get("task_id")
            algo_id = body.get("algorithm_id")
            status = body.get("status")

            validation_parts = []
            validation_parts.append(f"task_id: {task_id}")
            validation_parts.append(f"algorithm_id: {algo_id}")
            validation_parts.append(f"status: {status}")

            has_task_id = task_id is not None
            has_status = status is not None
            validation_parts.append(f"返回结构完整: {'通过' if has_task_id and has_status else '失败'}")

            # 查询任务状态
            query_start = time.time()
            task_status_resp = None
            if task_id:
                try:
                    task_status_resp = requests.get(
                        f"{ALGORITHM_ENGINE_URL}/api/v1/tasks/{task_id}",
                        timeout=REQUEST_TIMEOUT,
                    )
                except Exception:
                    pass
            query_duration = time.time() - query_start

            if task_status_resp and task_status_resp.status_code == 200:
                task_data = task_status_resp.json()
                task_status_val = task_data.get("status", "UNKNOWN")
                progress = task_data.get("progress", 0)
                validation_parts.append(f"任务查询状态: {task_status_val}, progress={progress}")

                # 如果任务完成，获取结果
                if task_status_val == "success":
                    try:
                        result_resp = requests.get(
                            f"{ALGORITHM_ENGINE_URL}/api/v1/tasks/{task_id}/result",
                            timeout=REQUEST_TIMEOUT,
                        )
                        if result_resp.status_code == 200:
                            result_data = result_resp.json()
                            validation_parts.append("任务结果: 已获取")
                            if verbose:
                                results.record(
                                    test_id, test_name, "PASS",
                                    request_time=duration + query_duration,
                                    response_status=resp.status_code,
                                    message="A* 任务已提交并完成",
                                    validation="\n".join(validation_parts),
                                    response_data=result_data,
                                )
                                return
                    except Exception:
                        pass

            test_status = "PASS" if has_task_id and has_status else "FAIL"
            results.record(
                test_id, test_name, test_status,
                request_time=duration + query_duration,
                response_status=resp.status_code,
                message="A* 算法任务已提交",
                validation="\n".join(validation_parts),
                response_data=body if verbose else None,
            )
        else:
            results.record(
                test_id, test_name, "FAIL",
                request_time=duration,
                response_status=resp.status_code,
                message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                validation="期望 HTTP 200/201",
            )
    except requests.exceptions.ConnectionError:
        duration = time.time() - start
        results.record(
            test_id, test_name, "FAIL",
            request_time=duration,
            response_status=0,
            message="连接拒绝 (算法引擎未启动)",
            validation="算法引擎服务不可达",
        )
    except Exception as e:
        duration = time.time() - start
        results.record(
            test_id, test_name, "FAIL",
            request_time=duration,
            response_status=0,
            message=str(e),
            validation="请求异常",
        )


# ============================================================
# Test 3: 同化任务提交 (3DVAR)
# ============================================================

def test_assimilation_task(results: TestResult, verbose: bool = False) -> None:
    """测试3: 同化任务提交 - 提交 3DVAR 任务"""
    test_id = 3
    test_name = "同化任务提交 (3DVAR)"
    url = f"{ASSIMILATION_API_URL}/api/v1/assimilation/tasks"

    payload = {
        "type": "3DVAR",
        "algorithm": "three_dimensional_var",
        "startTime": "2024-01-15T00:00:00Z",
        "endTime": "2024-01-15T06:00:00Z",
        "region": {
            "minLon": 115.0,
            "minLat": 39.0,
            "maxLon": 118.0,
            "maxLat": 41.0,
        },
        "observationSources": ["wrf", "surface_station"],
    }

    start = time.time()
    try:
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        duration = time.time() - start

        if resp.status_code in (200, 201):
            body = resp.json()
            code = body.get("code", -1)
            data = body.get("data")

            validation_parts = []
            validation_parts.append(f"API code: {code}")

            if code in (0, 200):
                task_id = data
                validation_parts.append(f"任务ID: {task_id}")
                validation_parts.append("任务类型: 3DVAR")

                results.record(
                    test_id, test_name, "PASS",
                    request_time=duration,
                    response_status=resp.status_code,
                    message="3DVAR 同化任务提交成功",
                    validation="\n".join(validation_parts),
                    response_data=body if verbose else None,
                )
            else:
                msg = body.get("message", "unknown error")
                validation_parts.append(f"错误信息: {msg}")
                results.record(
                    test_id, test_name, "FAIL",
                    request_time=duration,
                    response_status=resp.status_code,
                    message=f"API 返回错误: code={code}",
                    validation="\n".join(validation_parts),
                )
        else:
            results.record(
                test_id, test_name, "FAIL",
                request_time=duration,
                response_status=resp.status_code,
                message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                validation="期望 HTTP 200/201",
            )
    except requests.exceptions.ConnectionError:
        duration = time.time() - start
        results.record(
            test_id, test_name, "FAIL",
            request_time=duration,
            response_status=0,
            message="连接拒绝 (assimilation-api 未启动)",
            validation="assimilation-api 服务不可达",
        )
    except Exception as e:
        duration = time.time() - start
        results.record(
            test_id, test_name, "FAIL",
            request_time=duration,
            response_status=0,
            message=str(e),
            validation="请求异常",
        )


# ============================================================
# Test 4: 风险评估
# ============================================================

def test_risk_assessment(results: TestResult, verbose: bool = False) -> None:
    """测试4: 风险评估 - 发起风险评估"""
    test_id = 4
    test_name = "风险评估"
    url = f"{RISK_API_URL}/api/v1/risk/assess"

    payload = {
        "path": [
            {"lon": 116.4, "lat": 39.9, "altitude": 100},
            {"lon": 116.6, "lat": 39.95, "altitude": 150},
            {"lon": 117.0, "lat": 40.0, "altitude": 200},
        ],
        "time": "2024-01-15T12:00:00Z",
        "uavType": "multirotor",
    }

    start = time.time()
    try:
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        duration = time.time() - start

        if resp.status_code in (200, 201):
            body = resp.json()
            code = body.get("code", -1)
            data = body.get("data")

            validation_parts = []
            validation_parts.append(f"API code: {code}")

            if code in (0, 200) and isinstance(data, dict):
                risk_level = data.get("riskLevel", "UNKNOWN")
                score = data.get("score")
                factors = data.get("factors", [])

                validation_parts.append(f"风险等级: {risk_level}")
                validation_parts.append(f"风险分数: {score}")
                validation_parts.append(f"风险因子数: {len(factors)}")

                has_level = risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
                has_score = score is not None
                has_factors = len(factors) > 0

                test_status = "PASS" if has_level and has_score else "FAIL"
                results.record(
                    test_id, test_name, test_status,
                    request_time=duration,
                    response_status=resp.status_code,
                    message="风险评估完成",
                    validation="\n".join(validation_parts),
                    response_data=data if verbose else None,
                )
            else:
                msg = body.get("message", "unknown error")
                validation_parts.append(f"错误信息: {msg}")
                results.record(
                    test_id, test_name, "FAIL",
                    request_time=duration,
                    response_status=resp.status_code,
                    message=f"风险评估返回异常: code={code}",
                    validation="\n".join(validation_parts),
                )
        else:
            results.record(
                test_id, test_name, "FAIL",
                request_time=duration,
                response_status=resp.status_code,
                message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                validation="期望 HTTP 200/201",
            )
    except requests.exceptions.ConnectionError:
        duration = time.time() - start
        results.record(
            test_id, test_name, "FAIL",
            request_time=duration,
            response_status=0,
            message="连接拒绝 (risk-api 未启动)",
            validation="risk-api 服务不可达",
        )
    except Exception as e:
        duration = time.time() - start
        results.record(
            test_id, test_name, "FAIL",
            request_time=duration,
            response_status=0,
            message=str(e),
            validation="请求异常",
        )


# ============================================================
# Test 5: 气象数据查询
# ============================================================

def test_weather_query(results: TestResult, verbose: bool = False) -> None:
    """测试5: 气象数据查询 - 单点气象查询"""
    test_id = 5
    test_name = "气象数据查询 (单点)"
    url = f"{WEATHER_API_URL}/api/v1/weather/point"

    payload = {
        "lon": 116.4,
        "lat": 39.9,
        "altitude": 100.0,
    }

    start = time.time()
    try:
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        duration = time.time() - start

        if resp.status_code in (200, 201):
            body = resp.json()
            code = body.get("code", -1)
            data = body.get("data")

            validation_parts = []
            validation_parts.append(f"API code: {code}")

            if code in (0, 200) and isinstance(data, dict):
                lon = data.get("lon")
                lat = data.get("lat")
                wind_speed = data.get("windSpeed")
                temperature = data.get("temperature")
                pressure = data.get("pressure")
                source = data.get("source")

                validation_parts.append(f"坐标: ({lon}, {lat})")
                validation_parts.append(f"风速: {wind_speed} m/s")
                validation_parts.append(f"温度: {temperature} C")
                validation_parts.append(f"气压: {pressure} hPa")
                validation_parts.append(f"数据源: {source}")

                # 验证关键字段
                has_weather = wind_speed is not None and temperature is not None
                coord_match = (
                    lon is not None and lat is not None
                    and abs(lon - 116.4) < 0.01 and abs(lat - 39.9) < 0.01
                )

                validation_parts.append(f"气象数据完整: {'通过' if has_weather else '失败'}")
                validation_parts.append(f"坐标匹配: {'通过' if coord_match else '失败'}")

                test_status = "PASS" if has_weather and coord_match else "FAIL"
                results.record(
                    test_id, test_name, test_status,
                    request_time=duration,
                    response_status=resp.status_code,
                    message="气象数据查询成功",
                    validation="\n".join(validation_parts),
                    response_data=data if verbose else None,
                )
            else:
                msg = body.get("message", "unknown error")
                validation_parts.append(f"错误信息: {msg}")
                results.record(
                    test_id, test_name, "FAIL",
                    request_time=duration,
                    response_status=resp.status_code,
                    message=f"气象查询返回异常: code={code}",
                    validation="\n".join(validation_parts),
                )
        else:
            results.record(
                test_id, test_name, "FAIL",
                request_time=duration,
                response_status=resp.status_code,
                message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                validation="期望 HTTP 200/201",
            )
    except requests.exceptions.ConnectionError:
        duration = time.time() - start
        results.record(
            test_id, test_name, "FAIL",
            request_time=duration,
            response_status=0,
            message="连接拒绝 (weather-api 未启动)",
            validation="weather-api 服务不可达",
        )
    except Exception as e:
        duration = time.time() - start
        results.record(
            test_id, test_name, "FAIL",
            request_time=duration,
            response_status=0,
            message=str(e),
            validation="请求异常",
        )


# ============================================================
# Test 6: 观测决策 (信息增益计算)
# ============================================================

def test_observation_decision(results: TestResult, verbose: bool = False) -> None:
    """测试6: 观测决策 - 信息增益计算"""
    test_id = 6
    test_name = "观测决策 (信息增益计算)"
    url = f"{OBSERVATION_API_URL}/api/v1/observation/decisions"

    payload = {
        "region": {
            "minLon": 116.0,
            "minLat": 39.5,
            "maxLon": 117.0,
            "maxLat": 40.5,
        },
        "targetVariables": ["temperature", "wind_u", "wind_v"],
        "timeWindow": {
            "start": "2024-01-15T12:00:00Z",
            "end": "2024-01-15T18:00:00Z",
        },
    }

    start = time.time()
    try:
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        duration = time.time() - start

        if resp.status_code in (200, 201):
            body = resp.json()
            code = body.get("code", -1)
            data = body.get("data")

            validation_parts = []
            validation_parts.append(f"API code: {code}")

            if code in (0, 200) and isinstance(data, dict):
                decision = data.get("decision", "UNKNOWN")
                coverage_score = data.get("coverageScore")
                suggested_platforms = data.get("suggestedPlatforms", [])
                reason = data.get("reason", "")

                validation_parts.append(f"决策: {decision}")
                validation_parts.append(f"覆盖率分数: {coverage_score}")
                validation_parts.append(f"建议平台: {suggested_platforms}")
                validation_parts.append(f"原因: {reason[:100] if reason else 'N/A'}")

                has_decision = decision in ("OBSERVE", "SKIP", "DEFER")
                has_coverage = coverage_score is not None

                validation_parts.append(f"决策有效: {'通过' if has_decision else '失败'}")
                validation_parts.append(f"覆盖率计算: {'通过' if has_coverage else '失败'}")

                test_status = "PASS" if has_decision and has_coverage else "FAIL"
                results.record(
                    test_id, test_name, test_status,
                    request_time=duration,
                    response_status=resp.status_code,
                    message="观测决策计算完成",
                    validation="\n".join(validation_parts),
                    response_data=data if verbose else None,
                )
            else:
                msg = body.get("message", "unknown error")
                validation_parts.append(f"错误信息: {msg}")
                results.record(
                    test_id, test_name, "FAIL",
                    request_time=duration,
                    response_status=resp.status_code,
                    message=f"观测决策返回异常: code={code}",
                    validation="\n".join(validation_parts),
                )
        else:
            results.record(
                test_id, test_name, "FAIL",
                request_time=duration,
                response_status=resp.status_code,
                message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                validation="期望 HTTP 200/201",
            )
    except requests.exceptions.ConnectionError:
        duration = time.time() - start
        results.record(
            test_id, test_name, "FAIL",
            request_time=duration,
            response_status=0,
            message="连接拒绝 (observation-api 未启动)",
            validation="observation-api 服务不可达",
        )
    except Exception as e:
        duration = time.time() - start
        results.record(
            test_id, test_name, "FAIL",
            request_time=duration,
            response_status=0,
            message=str(e),
            validation="请求异常",
        )


# ============================================================
# Test 7: 路径规划 (RRT*)
# ============================================================

def test_path_planning(results: TestResult, verbose: bool = False) -> None:
    """测试7: 路径规划 - RRT* 路径规划"""
    test_id = 7
    test_name = "路径规划 (RRT*)"
    url = f"{PLANNING_API_URL}/api/v1/planning/path"

    payload = {
        "startPoint": {"lon": 116.4, "lat": 39.9, "altitude": 100},
        "endPoint": {"lon": 117.0, "lat": 40.0, "altitude": 200},
        "waypoints": [
            {"lon": 116.6, "lat": 39.95, "altitude": 150},
        ],
        "algorithm": "rrt_star",
    }

    start = time.time()
    try:
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        duration = time.time() - start

        if resp.status_code in (200, 201):
            body = resp.json()
            code = body.get("code", -1)
            data = body.get("data")

            validation_parts = []
            validation_parts.append(f"API code: {code}")

            if code in (0, 200) and isinstance(data, dict):
                task_id = data.get("id")
                status = data.get("status", "UNKNOWN")

                validation_parts.append(f"任务ID: {task_id}")
                validation_parts.append(f"状态: {status}")

                has_task_id = task_id is not None
                valid_status = status in ("PENDING", "RUNNING", "COMPLETED", "SUCCESS")

                validation_parts.append(f"任务ID有效: {'通过' if has_task_id else '失败'}")
                validation_parts.append(f"状态有效: {'通过' if valid_status else '失败'}")

                test_status = "PASS" if has_task_id and valid_status else "FAIL"
                results.record(
                    test_id, test_name, test_status,
                    request_time=duration,
                    response_status=resp.status_code,
                    message="RRT* 路径规划任务已提交",
                    validation="\n".join(validation_parts),
                    response_data=data if verbose else None,
                )
            else:
                msg = body.get("message", "unknown error")
                validation_parts.append(f"错误信息: {msg}")
                results.record(
                    test_id, test_name, "FAIL",
                    request_time=duration,
                    response_status=resp.status_code,
                    message=f"路径规划返回异常: code={code}",
                    validation="\n".join(validation_parts),
                )
        else:
            results.record(
                test_id, test_name, "FAIL",
                request_time=duration,
                response_status=resp.status_code,
                message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                validation="期望 HTTP 200/201",
            )
    except requests.exceptions.ConnectionError:
        duration = time.time() - start
        results.record(
            test_id, test_name, "FAIL",
            request_time=duration,
            response_status=0,
            message="连接拒绝 (planning-api 未启动)",
            validation="planning-api 服务不可达",
        )
    except Exception as e:
        duration = time.time() - start
        results.record(
            test_id, test_name, "FAIL",
            request_time=duration,
            response_status=0,
            message=str(e),
            validation="请求异常",
        )


# ============================================================
# Test 8: 智能调度器 (assimilation smart-select)
# ============================================================

def test_smart_scheduler(results: TestResult, verbose: bool = False) -> None:
    """测试8: 智能调度器 - assimilation smart-select"""
    test_id = 8
    test_name = "智能调度器 (assimilation smart-select)"
    url = f"{ALGORITHM_ENGINE_URL}/api/v1/assimilation/smart-select"

    payload = {
        "background_field": [
            [300.0, 301.0, 299.5, 300.2],
            [300.5, 301.5, 300.0, 300.8],
            [299.8, 300.3, 299.0, 300.1],
        ],
        "observations": [
            {"position": [0, 0], "value": 300.5},
            {"position": [1, 1], "value": 301.2},
            {"position": [2, 2], "value": 299.8},
            {"position": [3, 3], "value": 300.3},
        ],
        "time_budget_seconds": 30.0,
        "require_probabilistic": False,
        "require_risk_aware": False,
        "gpu_available": False,
    }

    start = time.time()
    try:
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        duration = time.time() - start

        if resp.status_code in (200, 201):
            body = resp.json()

            validation_parts = []

            # smart-select 直接返回结果 (非 Result<T> 包装)
            algo_id = body.get("algorithm_id")
            reason = body.get("reason", "")
            config = body.get("config_overrides", {})
            explanation = body.get("decision_explanation", "")

            validation_parts.append(f"推荐算法: {algo_id}")
            validation_parts.append(f"推荐原因: {reason[:100] if reason else 'N/A'}")
            validation_parts.append(f"配置覆盖: {json.dumps(config) if config else '无'}")
            validation_parts.append(f"决策说明: {explanation[:100] if explanation else 'N/A'}")

            has_algo_id = algo_id is not None and len(str(algo_id)) > 0
            has_reason = reason is not None and len(str(reason)) > 0

            validation_parts.append(f"推荐算法有效: {'通过' if has_algo_id else '失败'}")
            validation_parts.append(f"推荐原因有效: {'通过' if has_reason else '失败'}")

            test_status = "PASS" if has_algo_id else "FAIL"
            results.record(
                test_id, test_name, test_status,
                request_time=duration,
                response_status=resp.status_code,
                message="智能调度器推荐完成",
                validation="\n".join(validation_parts),
                response_data=body if verbose else None,
            )
        else:
            results.record(
                test_id, test_name, "FAIL",
                request_time=duration,
                response_status=resp.status_code,
                message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                validation="期望 HTTP 200/201",
            )
    except requests.exceptions.ConnectionError:
        duration = time.time() - start
        results.record(
            test_id, test_name, "FAIL",
            request_time=duration,
            response_status=0,
            message="连接拒绝 (算法引擎未启动)",
            validation="算法引擎服务不可达",
        )
    except Exception as e:
        duration = time.time() - start
        results.record(
            test_id, test_name, "FAIL",
            request_time=duration,
            response_status=0,
            message=str(e),
            validation="请求异常",
        )


# ============================================================
# Main
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="UAV Platform V2 - E2E 自动化测试脚本"
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"目标主机地址 (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细输出 (响应体等)",
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="输出 JSON 格式测试报告",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="禁用彩色输出",
    )
    args = parser.parse_args()

    # 禁用颜色
    if args.no_color or args.json_output:
        Color.disable()

    # 打印标题
    print(f"{Color.BOLD}{'=' * 72}{Color.RESET}")
    print(f"{Color.BOLD}  UAV Platform V2 - E2E 自动化测试{Color.RESET}")
    print(f"{Color.BOLD}{'=' * 72}{Color.RESET}")
    print(f"  目标主机: {args.host}")
    print(f"  算法引擎: {ALGORITHM_ENGINE_URL}")
    print(f"  请求超时: {REQUEST_TIMEOUT}s")
    print(f"  详细模式: {'开启' if args.verbose else '关闭'}")
    print(f"{Color.BOLD}{'=' * 72}{Color.RESET}")
    print()

    results = TestResult()

    # 定义测试列表
    tests = [
        ("测试 1: 算法列表查询", test_algorithm_list),
        ("测试 2: 算法执行测试 (A*)", test_algorithm_execution),
        ("测试 3: 同化任务提交 (3DVAR)", test_assimilation_task),
        ("测试 4: 风险评估", test_risk_assessment),
        ("测试 5: 气象数据查询", test_weather_query),
        ("测试 6: 观测决策 (信息增益)", test_observation_decision),
        ("测试 7: 路径规划 (RRT*)", test_path_planning),
        ("测试 8: 智能调度器 (smart-select)", test_smart_scheduler),
    ]

    # 执行测试
    for label, test_func in tests:
        print(f"  {Color.CYAN}{label}...{Color.RESET}")
        test_func(results, verbose=args.verbose)

    # 输出报告
    if args.json_output:
        print(json.dumps(results.to_json(), indent=2, ensure_ascii=False))
    else:
        results.print_report(verbose=args.verbose)

    # 退出码
    sys.exit(1 if results.failed > 0 else 0)


if __name__ == "__main__":
    main()
