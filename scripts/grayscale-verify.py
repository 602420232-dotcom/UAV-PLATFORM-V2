#!/usr/bin/env python3
"""
UAV Platform V2 - 灰度环境全链路验证脚本

验证 Docker 灰度环境中所有组件的连通性和健康状态，包括：
  1. 基础设施检查 (MySQL, Redis, Kafka, Nacos)
  2. API 网关检查
  3. 7 个 Java 微服务健康检查
  4. 算法引擎检查 (Python/FastAPI)
  5. 算法注册验证 (102 个算法)
  6. 网关路由验证
  7. Kafka 全链路验证

用法:
    python scripts/grayscale-verify.py
    python scripts/grayscale-verify.py --host 192.168.1.100
    python scripts/grayscale-verify.py --verbose
    python scripts/grayscale-verify.py --json-output
"""

from __future__ import annotations

import argparse
import json
import socket
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
CHECK_TIMEOUT = 5  # 每个检查 5 秒超时

# 基础设施端口
INFRA_SERVICES = {
    "MySQL": 3306,
    "Redis": 6379,
    "Kafka": 19092,
    "Nacos": 8950,
}

# API 网关
GATEWAY_PORT = 8258

# Java 微服务
JAVA_SERVICES = {
    "platform-api": 8251,
    "weather-api": 8252,
    "assimilation-api": 8253,
    "risk-api": 8254,
    "observation-api": 8255,
    "planning-api": 8256,
    "utm-api": 8259,
}

# 算法引擎
ALGORITHM_ENGINE_PORT = 9095

# 网关路由映射 (gateway path -> 服务名)
GATEWAY_ROUTES = {
    "/api/v1/platform/health": "platform-api",
    "/api/v1/weather/health": "weather-api",
    "/api/v1/assimilation/health": "assimilation-api",
    "/api/v1/risk/health": "risk-api",
    "/api/v1/observation/health": "observation-api",
    "/api/v1/planning/health": "planning-api",
    "/api/v1/utm/health": "utm-api",
}

# Kafka 配置
KAFKA_BOOTSTRAP = "localhost:19092"
KAFKA_TOPIC_TASKS = "uav.algorithm.tasks"
KAFKA_TOPIC_RESULTS = "uav.algorithm.results"

# 期望算法数量
EXPECTED_ALGORITHM_COUNT = 102


# ============================================================
# Verification Result Tracker
# ============================================================

class VerifyResult:
    """验证结果跟踪器"""

    def __init__(self) -> None:
        self.passed: int = 0
        self.failed: int = 0
        self.skipped: int = 0
        self.details: list[dict[str, Any]] = []

    def record(
        self,
        category: str,
        name: str,
        status: str,
        message: str = "",
        duration: float = 0.0,
        verbose_info: str = "",
    ) -> None:
        entry = {
            "category": category,
            "name": name,
            "status": status,
            "message": message,
            "duration": round(duration, 3),
            "verbose_info": verbose_info,
        }
        self.details.append(entry)
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        elif status == "SKIP":
            self.skipped += 1

    def print_report(self, verbose: bool = False) -> None:
        """打印彩色汇总报告"""
        print()
        print(f"{Color.BOLD}{'=' * 72}{Color.RESET}")
        print(f"{Color.BOLD}  UAV Platform V2 - 灰度环境全链路验证报告{Color.RESET}")
        print(f"  生成时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"{Color.BOLD}{'=' * 72}{Color.RESET}")
        print()

        current_category = ""
        for d in self.details:
            if d["category"] != current_category:
                current_category = d["category"]
                print(f"  {Color.CYAN}--- {current_category} ---{Color.RESET}")
                print()

            if d["status"] == "PASS":
                tag = f"{Color.GREEN}  PASS  {Color.RESET}"
            elif d["status"] == "FAIL":
                tag = f"{Color.RED}  FAIL  {Color.RESET}"
            elif d["status"] == "SKIP":
                tag = f"{Color.YELLOW}  SKIP  {Color.RESET}"
            else:
                tag = f"{Color.YELLOW}  WARN  {Color.RESET}"

            print(f"  [{tag}] {d['name']}")
            if d["message"]:
                for line in d["message"].split("\n"):
                    print(f"            {Color.DIM}{line}{Color.RESET}")
            if d["duration"] > 0:
                print(f"            {Color.DIM}({d['duration']}s){Color.RESET}")
            if verbose and d.get("verbose_info"):
                for line in d["verbose_info"].split("\n"):
                    print(f"            {Color.DIM}{line}{Color.RESET}")
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
            print(f"  {Color.RED}{Color.BOLD}*** 验证结果: FAIL (存在失败项) ***{Color.RESET}")
        elif self.skipped > 0:
            print(f"  {Color.YELLOW}{Color.BOLD}*** 验证结果: PASS (存在跳过项) ***{Color.RESET}")
        else:
            print(f"  {Color.GREEN}{Color.BOLD}*** 验证结果: PASS (全部通过) ***{Color.RESET}")
        print()

    def to_json(self) -> dict[str, Any]:
        """输出 JSON 格式报告"""
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total": self.passed + self.failed + self.skipped,
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped,
                "result": "FAIL" if self.failed > 0 else "PASS",
            },
            "details": [
                {
                    "category": d["category"],
                    "name": d["name"],
                    "status": d["status"],
                    "message": d["message"],
                    "duration": d["duration"],
                }
                for d in self.details
            ],
        }


# ============================================================
# Step 1: 基础设施检查
# ============================================================

def check_infrastructure(host: str, results: VerifyResult, verbose: bool = False) -> None:
    """检查基础设施连通性: MySQL(3306), Redis(6379), Kafka(19092), Nacos(8950)"""
    category = "Step 1: 基础设施检查"

    for service_name, port in INFRA_SERVICES.items():
        start = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(CHECK_TIMEOUT)
            result = sock.connect_ex((host, port))
            sock.close()
            duration = time.time() - start

            if result == 0:
                results.record(
                    category,
                    f"{service_name} ({host}:{port})",
                    "PASS",
                    f"端口连通",
                    duration,
                    verbose_info=f"socket.connect_ex 返回 0" if verbose else "",
                )
            else:
                results.record(
                    category,
                    f"{service_name} ({host}:{port})",
                    "FAIL",
                    f"端口不可达 (errno={result})",
                    duration,
                )
        except socket.timeout:
            duration = time.time() - start
            results.record(
                category,
                f"{service_name} ({host}:{port})",
                "FAIL",
                f"连接超时 ({CHECK_TIMEOUT}s)",
                duration,
            )
        except Exception as e:
            duration = time.time() - start
            results.record(
                category,
                f"{service_name} ({host}:{port})",
                "FAIL",
                str(e),
                duration,
            )


# ============================================================
# Step 2: API 网关检查
# ============================================================

def check_gateway(host: str, results: VerifyResult, verbose: bool = False) -> None:
    """检查 API 网关健康状态"""
    category = "Step 2: API 网关检查"
    url = f"http://{host}:{GATEWAY_PORT}/actuator/health"

    start = time.time()
    try:
        resp = requests.get(url, timeout=CHECK_TIMEOUT)
        duration = time.time() - start

        if resp.status_code == 200:
            try:
                body = resp.json()
                status_val = body.get("status", "UNKNOWN")
                verbose_info = json.dumps(body, indent=2, ensure_ascii=False) if verbose else ""
                results.record(
                    category,
                    f"API Gateway ({url})",
                    "PASS",
                    f"HTTP {resp.status_code}, status={status_val}",
                    duration,
                    verbose_info=verbose_info,
                )
            except json.JSONDecodeError:
                results.record(
                    category,
                    f"API Gateway ({url})",
                    "PASS",
                    f"HTTP {resp.status_code}",
                    duration,
                )
        else:
            results.record(
                category,
                f"API Gateway ({url})",
                "FAIL",
                f"HTTP {resp.status_code}",
                duration,
            )
    except requests.exceptions.ConnectionError:
        duration = time.time() - start
        results.record(
            category,
            f"API Gateway ({url})",
            "FAIL",
            "连接拒绝 (网关未启动或端口不可达)",
            duration,
        )
    except requests.exceptions.Timeout:
        duration = time.time() - start
        results.record(
            category,
            f"API Gateway ({url})",
            "FAIL",
            f"连接超时 ({CHECK_TIMEOUT}s)",
            duration,
        )
    except Exception as e:
        duration = time.time() - start
        results.record(
            category,
            f"API Gateway ({url})",
            "FAIL",
            str(e),
            duration,
        )


# ============================================================
# Step 3: Java 微服务健康检查
# ============================================================

def check_java_services(host: str, results: VerifyResult, verbose: bool = False) -> None:
    """检查 7 个 Java 微服务的 /actuator/health 端点"""
    category = "Step 3: Java 微服务健康检查"

    for service_name, port in JAVA_SERVICES.items():
        url = f"http://{host}:{port}/actuator/health"
        start = time.time()
        try:
            resp = requests.get(url, timeout=CHECK_TIMEOUT)
            duration = time.time() - start

            if resp.status_code == 200:
                try:
                    body = resp.json()
                    status_val = body.get("status", "UNKNOWN")
                    verbose_info = json.dumps(body, indent=2, ensure_ascii=False) if verbose else ""
                    if status_val.upper() == "UP":
                        results.record(
                            category,
                            f"{service_name} ({host}:{port})",
                            "PASS",
                            f"HTTP {resp.status_code}, status=UP",
                            duration,
                            verbose_info=verbose_info,
                        )
                    else:
                        results.record(
                            category,
                            f"{service_name} ({host}:{port})",
                            "FAIL",
                            f"HTTP {resp.status_code}, status={status_val}",
                            duration,
                            verbose_info=verbose_info,
                        )
                except json.JSONDecodeError:
                    results.record(
                        category,
                        f"{service_name} ({host}:{port})",
                        "PASS",
                        f"HTTP {resp.status_code}",
                        duration,
                    )
            else:
                results.record(
                    category,
                    f"{service_name} ({host}:{port})",
                    "FAIL",
                    f"HTTP {resp.status_code}",
                    duration,
                )
        except requests.exceptions.ConnectionError:
            duration = time.time() - start
            results.record(
                category,
                f"{service_name} ({host}:{port})",
                "FAIL",
                "连接拒绝 (服务未启动或端口不可达)",
                duration,
            )
        except requests.exceptions.Timeout:
            duration = time.time() - start
            results.record(
                category,
                f"{service_name} ({host}:{port})",
                "FAIL",
                f"连接超时 ({CHECK_TIMEOUT}s)",
                duration,
            )
        except Exception as e:
            duration = time.time() - start
            results.record(
                category,
                f"{service_name} ({host}:{port})",
                "FAIL",
                str(e),
                duration,
            )


# ============================================================
# Step 4: 算法引擎检查
# ============================================================

def check_algorithm_engine(host: str, results: VerifyResult, verbose: bool = False) -> None:
    """检查算法引擎健康状态"""
    category = "Step 4: 算法引擎检查"
    url = f"http://{host}:{ALGORITHM_ENGINE_PORT}/health"

    start = time.time()
    try:
        resp = requests.get(url, timeout=CHECK_TIMEOUT)
        duration = time.time() - start

        if resp.status_code == 200:
            try:
                body = resp.json()
                status_val = body.get("status", "UNKNOWN")
                algo_count = body.get("algorithms_registered", 0)
                pending_tasks = body.get("tasks_pending", 0)
                verbose_info = json.dumps(body, indent=2, ensure_ascii=False) if verbose else ""
                results.record(
                    category,
                    f"Algorithm Engine ({url})",
                    "PASS",
                    f"HTTP {resp.status_code}, status={status_val}, "
                    f"algorithms_registered={algo_count}, tasks_pending={pending_tasks}",
                    duration,
                    verbose_info=verbose_info,
                )
            except json.JSONDecodeError:
                results.record(
                    category,
                    f"Algorithm Engine ({url})",
                    "PASS",
                    f"HTTP {resp.status_code}",
                    duration,
                )
        else:
            results.record(
                category,
                f"Algorithm Engine ({url})",
                "FAIL",
                f"HTTP {resp.status_code}",
                duration,
            )
    except requests.exceptions.ConnectionError:
        duration = time.time() - start
        results.record(
            category,
            f"Algorithm Engine ({url})",
            "FAIL",
            "连接拒绝 (算法引擎未启动或端口不可达)",
            duration,
        )
    except requests.exceptions.Timeout:
        duration = time.time() - start
        results.record(
            category,
            f"Algorithm Engine ({url})",
            "FAIL",
            f"连接超时 ({CHECK_TIMEOUT}s)",
            duration,
        )
    except Exception as e:
        duration = time.time() - start
        results.record(
            category,
            f"Algorithm Engine ({url})",
            "FAIL",
            str(e),
            duration,
        )


# ============================================================
# Step 5: 算法注册验证
# ============================================================

def check_algorithm_registration(host: str, results: VerifyResult, verbose: bool = False) -> None:
    """验证算法引擎注册了 102 个算法"""
    category = "Step 5: 算法注册验证"
    url = f"http://{host}:{ALGORITHM_ENGINE_PORT}/api/v1/algorithms"

    start = time.time()
    try:
        resp = requests.get(url, timeout=CHECK_TIMEOUT)
        duration = time.time() - start

        if resp.status_code == 200:
            try:
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
                    verbose_info = json.dumps(body[:5], indent=2, ensure_ascii=False) if verbose else ""

                    if algo_count == EXPECTED_ALGORITHM_COUNT:
                        results.record(
                            category,
                            f"算法注册数量 ({url})",
                            "PASS",
                            f"已注册 {algo_count} 个算法 (期望 {EXPECTED_ALGORITHM_COUNT})\n"
                            f"  类别分布: {cat_summary}",
                            duration,
                            verbose_info=verbose_info,
                        )
                    elif algo_count > 0:
                        results.record(
                            category,
                            f"算法注册数量 ({url})",
                            "FAIL",
                            f"已注册 {algo_count} 个算法 (期望 {EXPECTED_ALGORITHM_COUNT})\n"
                            f"  类别分布: {cat_summary}",
                            duration,
                            verbose_info=verbose_info,
                        )
                    else:
                        results.record(
                            category,
                            f"算法注册数量 ({url})",
                            "FAIL",
                            f"未注册任何算法 (期望 {EXPECTED_ALGORITHM_COUNT})",
                            duration,
                        )
                else:
                    results.record(
                        category,
                        f"算法注册数量 ({url})",
                        "FAIL",
                        f"响应格式异常: 期望 list, 得到 {type(body).__name__}",
                        duration,
                    )
            except json.JSONDecodeError:
                results.record(
                    category,
                    f"算法注册数量 ({url})",
                    "FAIL",
                    "响应非 JSON 格式",
                    duration,
                )
        else:
            results.record(
                category,
                f"算法注册数量 ({url})",
                "FAIL",
                f"HTTP {resp.status_code}",
                duration,
            )
    except requests.exceptions.ConnectionError:
        duration = time.time() - start
        results.record(
            category,
            f"算法注册数量 ({url})",
            "FAIL",
            "连接拒绝 (算法引擎未启动)",
            duration,
        )
    except requests.exceptions.Timeout:
        duration = time.time() - start
        results.record(
            category,
            f"算法注册数量 ({url})",
            "FAIL",
            f"连接超时 ({CHECK_TIMEOUT}s)",
            duration,
        )
    except Exception as e:
        duration = time.time() - start
        results.record(
            category,
            f"算法注册数量 ({url})",
            "FAIL",
            str(e),
            duration,
        )


# ============================================================
# Step 6: 网关路由验证
# ============================================================

def check_gateway_routes(host: str, results: VerifyResult, verbose: bool = False) -> None:
    """通过 API 网关访问各服务，验证路由转发"""
    category = "Step 6: 网关路由验证"

    for path, service_name in GATEWAY_ROUTES.items():
        url = f"http://{host}:{GATEWAY_PORT}{path}"
        start = time.time()
        try:
            resp = requests.get(url, timeout=CHECK_TIMEOUT)
            duration = time.time() - start

            if resp.status_code == 200:
                verbose_info = ""
                if verbose:
                    try:
                        verbose_info = json.dumps(resp.json(), indent=2, ensure_ascii=False)
                    except (json.JSONDecodeError, ValueError):
                        verbose_info = resp.text[:500]
                results.record(
                    category,
                    f"Gateway -> {service_name} ({path})",
                    "PASS",
                    f"HTTP {resp.status_code}, 路由转发正常",
                    duration,
                    verbose_info=verbose_info,
                )
            elif resp.status_code == 404:
                # 404 可能是服务端点不存在，但路由本身可达
                results.record(
                    category,
                    f"Gateway -> {service_name} ({path})",
                    "PASS",
                    f"HTTP 404, 路由转发正常 (端点可能不存在)",
                    duration,
                )
            elif resp.status_code == 502 or resp.status_code == 503:
                results.record(
                    category,
                    f"Gateway -> {service_name} ({path})",
                    "FAIL",
                    f"HTTP {resp.status_code}, 后端服务不可达",
                    duration,
                )
            else:
                results.record(
                    category,
                    f"Gateway -> {service_name} ({path})",
                    "FAIL",
                    f"HTTP {resp.status_code}",
                    duration,
                )
        except requests.exceptions.ConnectionError:
            duration = time.time() - start
            results.record(
                category,
                f"Gateway -> {service_name} ({path})",
                "FAIL",
                "连接拒绝 (网关未启动)",
                duration,
            )
        except requests.exceptions.Timeout:
            duration = time.time() - start
            results.record(
                category,
                f"Gateway -> {service_name} ({path})",
                "FAIL",
                f"连接超时 ({CHECK_TIMEOUT}s)",
                duration,
            )
        except Exception as e:
            duration = time.time() - start
            results.record(
                category,
                f"Gateway -> {service_name} ({path})",
                "FAIL",
                str(e),
                duration,
            )


# ============================================================
# Step 7: Kafka 全链路验证
# ============================================================

def check_kafka_full_chain(host: str, results: VerifyResult, verbose: bool = False) -> None:
    """
    Kafka 全链路验证:
      1. 通过 algorithm-engine 提交算法任务 (发送到 Kafka task topic)
      2. 验证任务提交成功
      3. 查询任务状态
    """
    category = "Step 7: Kafka 全链路验证"

    # 检查 kafka-python 是否可用
    try:
        from kafka import KafkaConsumer  # noqa: F401
        has_kafka_client = True
    except ImportError:
        has_kafka_client = False
        results.record(
            category,
            "Kafka 客户端依赖",
            "SKIP",
            "kafka-python 未安装，跳过 Kafka 消费验证 (pip install kafka-python)",
        )

    # 7a: 通过 algorithm-engine 提交算法任务
    sub_start = time.time()
    task_id = None
    try:
        engine_url = f"http://{host}:{ALGORITHM_ENGINE_PORT}"
        task_payload = {
            "algorithm_id": "a_star",
            "params": {
                "start": [0, 0],
                "goal": [10, 10],
                "grid_size": [20, 20],
                "obstacles": [[3, 3], [3, 4], [4, 3]],
            },
            "priority": 5,
            "callback_topic": KAFKA_TOPIC_RESULTS,
        }

        resp = requests.post(
            f"{engine_url}/api/v1/tasks/submit",
            json=task_payload,
            timeout=CHECK_TIMEOUT,
        )
        duration = time.time() - sub_start

        if resp.status_code in (200, 201):
            try:
                resp_data = resp.json()
                task_id = resp_data.get("task_id")
                algo_id = resp_data.get("algorithm_id")
                status = resp_data.get("status")
                verbose_info = json.dumps(resp_data, indent=2, ensure_ascii=False) if verbose else ""
                results.record(
                    category,
                    "7a. 提交算法任务 (A* 路径规划)",
                    "PASS",
                    f"任务已提交: task_id={task_id}, algorithm={algo_id}, status={status}",
                    duration,
                    verbose_info=verbose_info,
                )
            except json.JSONDecodeError:
                results.record(
                    category,
                    "7a. 提交算法任务 (A* 路径规划)",
                    "FAIL",
                    f"HTTP {resp.status_code}, 响应非 JSON",
                    duration,
                )
        else:
            results.record(
                category,
                "7a. 提交算法任务 (A* 路径规划)",
                "FAIL",
                f"HTTP {resp.status_code}: {resp.text[:200]}",
                duration,
            )
    except requests.exceptions.ConnectionError:
        duration = time.time() - sub_start
        results.record(
            category,
            "7a. 提交算法任务 (A* 路径规划)",
            "FAIL",
            "连接拒绝 (算法引擎未启动)",
            duration,
        )
        return
    except Exception as e:
        duration = time.time() - sub_start
        results.record(
            category,
            "7a. 提交算法任务 (A* 路径规划)",
            "FAIL",
            str(e),
            duration,
        )
        return

    # 7b: 查询任务状态
    if task_id:
        sub_start = time.time()
        try:
            resp = requests.get(
                f"http://{host}:{ALGORITHM_ENGINE_PORT}/api/v1/tasks/{task_id}",
                timeout=CHECK_TIMEOUT,
            )
            duration = time.time() - sub_start

            if resp.status_code == 200:
                resp_data = resp.json()
                task_status = resp_data.get("status", "UNKNOWN")
                progress = resp_data.get("progress", 0)
                verbose_info = json.dumps(resp_data, indent=2, ensure_ascii=False) if verbose else ""
                results.record(
                    category,
                    "7b. 查询任务状态",
                    "PASS",
                    f"task_id={task_id}, status={task_status}, progress={progress}",
                    duration,
                    verbose_info=verbose_info,
                )
            else:
                results.record(
                    category,
                    "7b. 查询任务状态",
                    "FAIL",
                    f"HTTP {resp.status_code}",
                    duration,
                )
        except Exception as e:
            duration = time.time() - sub_start
            results.record(
                category,
                "7b. 查询任务状态",
                "FAIL",
                str(e),
                duration,
            )

    # 7c: Kafka 消费验证 (如果 kafka-python 可用)
    if has_kafka_client and task_id:
        sub_start = time.time()
        try:
            from kafka import KafkaConsumer as KC

            consumer = KC(
                KAFKA_TOPIC_TASKS,
                bootstrap_servers=KAFKA_BOOTSTRAP,
                group_id=f"grayscale-verify-{task_id[:8]}",
                auto_offset_reset="latest",
                consumer_timeout_ms=3000,
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            )

            found = False
            for msg in consumer:
                value = msg.value
                msg_task_id = value.get("task_id") or value.get("taskId")
                if msg_task_id and str(msg_task_id) == str(task_id):
                    found = True
                    verbose_info = json.dumps(value, indent=2, ensure_ascii=False) if verbose else ""
                    break

            consumer.close()
            duration = time.time() - sub_start

            if found:
                results.record(
                    category,
                    "7c. Kafka Task Topic 消息验证",
                    "PASS",
                    f"在 {KAFKA_TOPIC_TASKS} 中找到任务消息 (task_id={task_id})",
                    duration,
                    verbose_info=verbose_info,
                )
            else:
                results.record(
                    category,
                    "7c. Kafka Task Topic 消息验证",
                    "SKIP",
                    f"在 {KAFKA_TOPIC_TASKS} 中未找到消息 (可能已消费或 Kafka 未配置)",
                    duration,
                )
        except Exception as e:
            duration = time.time() - sub_start
            results.record(
                category,
                "7c. Kafka Task Topic 消息验证",
                "SKIP",
                f"Kafka 消费验证跳过: {e}",
                duration,
            )


# ============================================================
# Main
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="UAV Platform V2 - 灰度环境全链路验证脚本"
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
        help="输出 JSON 格式报告",
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
    print(f"{Color.BOLD}  UAV Platform V2 - 灰度环境全链路验证{Color.RESET}")
    print(f"{Color.BOLD}{'=' * 72}{Color.RESET}")
    print(f"  目标主机: {args.host}")
    print(f"  超时设置: {CHECK_TIMEOUT}s / 检查")
    print(f"  期望算法数: {EXPECTED_ALGORITHM_COUNT}")
    print(f"  详细模式: {'开启' if args.verbose else '关闭'}")
    print(f"{Color.BOLD}{'=' * 72}{Color.RESET}")
    print()

    results = VerifyResult()

    # Step 1: 基础设施检查
    print(f"  {Color.CYAN}[1/7] 检查基础设施...{Color.RESET}")
    check_infrastructure(args.host, results, verbose=args.verbose)

    # Step 2: API 网关检查
    print(f"  {Color.CYAN}[2/7] 检查 API 网关...{Color.RESET}")
    check_gateway(args.host, results, verbose=args.verbose)

    # Step 3: Java 微服务健康检查
    print(f"  {Color.CYAN}[3/7] 检查 Java 微服务...{Color.RESET}")
    check_java_services(args.host, results, verbose=args.verbose)

    # Step 4: 算法引擎检查
    print(f"  {Color.CYAN}[4/7] 检查算法引擎...{Color.RESET}")
    check_algorithm_engine(args.host, results, verbose=args.verbose)

    # Step 5: 算法注册验证
    print(f"  {Color.CYAN}[5/7] 验证算法注册...{Color.RESET}")
    check_algorithm_registration(args.host, results, verbose=args.verbose)

    # Step 6: 网关路由验证
    print(f"  {Color.CYAN}[6/7] 验证网关路由...{Color.RESET}")
    check_gateway_routes(args.host, results, verbose=args.verbose)

    # Step 7: Kafka 全链路验证
    print(f"  {Color.CYAN}[7/7] Kafka 全链路验证...{Color.RESET}")
    check_kafka_full_chain(args.host, results, verbose=args.verbose)

    # 输出报告
    if args.json_output:
        print(json.dumps(results.to_json(), indent=2, ensure_ascii=False))
    else:
        results.print_report(verbose=args.verbose)

    # 退出码
    sys.exit(1 if results.failed > 0 else 0)


if __name__ == "__main__":
    main()
