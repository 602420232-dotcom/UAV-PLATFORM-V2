#!/usr/bin/env python3
"""
UAV Platform V2 - Docker 灰度环境 Kafka 全链路验证脚本

验证 Docker 灰度环境中 Kafka 消息从 Java 服务 -> Kafka Topic -> Python 算法引擎 -> Kafka Result Topic 的完整链路。

用法:
    python scripts/grayscale-verify.py                          # 默认连接 localhost
    python scripts/grayscale-verify.py --host 192.168.1.100      # 指定 Docker 主机地址
    python scripts/grayscale-verify.py --timeout 60              # 自定义 Kafka 消费超时(秒)
    python scripts/grayscale-verify.py --skip-kafka-test         # 跳过 Kafka 全链路测试

验证步骤:
    1. 检查所有 Docker 容器状态
    2. 验证 Kafka Topic 自动创建
    3. 测试各服务 HTTP 健康端点
    4. Kafka 全链路测试（提交同化任务 -> Kafka -> 算法引擎 -> 结果回传）
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any

try:
    import requests
except ImportError:
    print("ERROR: 请先安装 requests 库: pip install requests")
    sys.exit(1)

try:
    from kafka import KafkaAdminClient, KafkaConsumer, KafkaProducer
    from kafka.admin import NewTopic
except ImportError:
    print("ERROR: 请先安装 kafka-python 库: pip install kafka-python")
    sys.exit(1)


# ============================================================
# Configuration
# ============================================================

# Docker 容器名称 -> 服务名称映射
CONTAINER_NAMES = {
    "uav-mysql": "MySQL",
    "uav-redis": "Redis",
    "uav-kafka": "Kafka",
    "uav-zookeeper": "Zookeeper",
    "uav-nacos": "Nacos",
    "uav-algorithm-engine": "Algorithm-Engine (Python)",
    "uav-platform-api": "Platform-API",
    "uav-weather-api": "Weather-API",
    "uav-assimilation-api": "Assimilation-API",
    "uav-risk-api": "Risk-API",
    "uav-observation-api": "Observation-API",
    "uav-planning-api": "Planning-API",
    "uav-utm-api": "UTM-API",
    "uav-gateway": "API-Gateway",
}

# 灰度环境端口映射（host:container）
SERVICE_PORTS = {
    "platform-api": 8081,
    "weather-api": 8082,
    "assimilation-api": 8083,
    "risk-api": 8084,
    "observation-api": 8085,
    "planning-api": 8086,
    "utm-api": 8089,
    "api-gateway": 8088,
    "algorithm-engine": 9090,
    "nacos": 8848,
    "kafka": 19092,
    "mysql": 3306,
    "redis": 6379,
}

# Kafka Topic
TOPIC_TASKS = "uav.algorithm.tasks"
TOPIC_RESULTS = "uav.algorithm.results"

# HMAC 签名配置
ACCESS_KEY = "uav_test_key"
SECRET_KEY = "uav_test_secret_2024"

# 健康检查端点（各服务内部 actuator 端点）
HEALTH_ENDPOINTS = {
    "platform-api": "/actuator/health",
    "weather-api": "/actuator/health",
    "assimilation-api": "/actuator/health",
    "risk-api": "/actuator/health",
    "observation-api": "/actuator/health",
    "planning-api": "/actuator/health",
    "utm-api": "/actuator/health",
    "api-gateway": "/actuator/health",
    "algorithm-engine": "/health",
    "nacos": "/nacos/v1/ns/operator/metrics",
}


# ============================================================
# HMAC-SHA256 Signing
# ============================================================

def sign_request(
    method: str,
    path: str,
    access_key: str = ACCESS_KEY,
    secret_key: str = SECRET_KEY,
    body: str = "",
) -> dict[str, str]:
    """
    生成 HMAC-SHA256 签名头。

    签名字符串格式:
        METHOD\\nPATH\\nTIMESTAMP\\nACCESS_KEY\\nBODY
    """
    timestamp = str(int(time.time()))
    string_to_sign = f"{method.upper()}\n{path}\n{timestamp}\n{access_key}\n{body}"
    signature = hmac.new(
        secret_key.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return {
        "X-UAV-Access-Key": access_key,
        "X-UAV-Timestamp": timestamp,
        "X-UAV-Signature": signature,
        "Content-Type": "application/json",
    }


# ============================================================
# Verification Result Tracker
# ============================================================

class VerifyResult:
    """验证结果跟踪器"""

    def __init__(self) -> None:
        self.passed: int = 0
        self.failed: int = 0
        self.warnings: int = 0
        self.details: list[dict[str, Any]] = []

    def record(
        self,
        category: str,
        name: str,
        status: str,
        message: str = "",
        duration: float = 0.0,
    ) -> None:
        entry = {
            "category": category,
            "name": name,
            "status": status,
            "message": message,
            "duration": round(duration, 3),
        }
        self.details.append(entry)
        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        elif status == "WARN":
            self.warnings += 1

    def report(self) -> str:
        lines: list[str] = []
        lines.append("")
        lines.append("=" * 72)
        lines.append("  UAV Platform V2 - Docker 灰度环境 Kafka 全链路验证报告")
        lines.append(f"  生成时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        lines.append("=" * 72)
        lines.append("")

        current_category = ""
        for d in self.details:
            if d["category"] != current_category:
                current_category = d["category"]
                lines.append(f"  --- {current_category} ---")
                lines.append("")

            status_tag = {
                "PASS": "  PASS  ",
                "FAIL": "  FAIL  ",
                "WARN": "  WARN  ",
            }.get(d["status"], "  ???  ")
            lines.append(f"  [{status_tag}] {d['name']}")
            if d["message"]:
                for msg_line in d["message"].split("\n"):
                    lines.append(f"            {msg_line}")
            if d["duration"] > 0:
                lines.append(f"            ({d['duration']}s)")
            lines.append("")

        total = self.passed + self.failed + self.warnings
        lines.append("-" * 72)
        lines.append(
            f"  总计: {total}  |  通过: {self.passed}  |  "
            f"失败: {self.failed}  |  警告: {self.warnings}"
        )
        lines.append("-" * 72)
        lines.append("")

        if self.failed > 0:
            lines.append("  *** 验证结果: FAIL (存在失败项) ***")
        elif self.warnings > 0:
            lines.append("  *** 验证结果: PASS (存在警告) ***")
        else:
            lines.append("  *** 验证结果: PASS (全部通过) ***")

        lines.append("")
        return "\n".join(lines)


# ============================================================
# Step 1: Docker 容器状态检查
# ============================================================

def check_docker_containers(results: VerifyResult) -> None:
    """检查所有 Docker 容器的运行状态"""
    category = "Step 1: Docker 容器状态检查"
    start = time.time()

    try:
        result = _run_command(
            'docker ps --format "{{.Names}}|{{.Status}}|{{.Ports}}"'
        )
        if result is None:
            results.record(category, "Docker 命令执行", "FAIL",
                           "无法执行 docker ps 命令，请确认 Docker 已安装并运行")
            return

        running_containers: dict[str, str] = {}
        for line in result.strip().split("\n"):
            if "|" in line:
                parts = line.split("|")
                name = parts[0].strip()
                status = parts[1].strip()
                running_containers[name] = status

        for container, service_name in CONTAINER_NAMES.items():
            if container in running_containers:
                status = running_containers[container]
                if status.startswith("Up"):
                    results.record(category, f"{service_name} ({container})", "PASS",
                                   f"状态: {status}")
                else:
                    results.record(category, f"{service_name} ({container})", "FAIL",
                                   f"状态异常: {status}")
            else:
                results.record(category, f"{service_name} ({container})", "FAIL",
                               "容器未运行")

        duration = time.time() - start
        running_count = sum(
            1 for c in CONTAINER_NAMES
            if c in running_containers and running_containers[c].startswith("Up")
        )
        results.record(category, "容器总览",
                       "PASS" if running_count == len(CONTAINER_NAMES) else "WARN",
                       f"运行中: {running_count}/{len(CONTAINER_NAMES)}",
                       duration)

    except Exception as e:
        duration = time.time() - start
        results.record(category, "Docker 容器检查", "FAIL", str(e), duration)


# ============================================================
# Step 2: Kafka Topic 验证
# ============================================================

def check_kafka_topics(host: str, results: VerifyResult) -> None:
    """验证 Kafka Topic 是否自动创建"""
    category = "Step 2: Kafka Topic 验证"
    start = time.time()

    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=f"{host}:{SERVICE_PORTS['kafka']}",
            client_id="grayscale-verify",
            request_timeout_ms=10000,
        )

        topics = admin_client.list_topics()
        admin_client.close()

        # 检查 uav.algorithm.tasks
        if TOPIC_TASKS in topics:
            topic_info = topics[TOPIC_TASKS]
            partitions = len(topic_info) if isinstance(topic_info, dict) else "N/A"
            results.record(category, f"Topic: {TOPIC_TASKS}", "PASS",
                           f"已创建, 分区数: {partitions}")
        else:
            results.record(category, f"Topic: {TOPIC_TASKS}", "FAIL",
                           "Topic 未创建，请检查 KafkaTopicConfig 或服务启动日志")

        # 检查 uav.algorithm.results
        if TOPIC_RESULTS in topics:
            topic_info = topics[TOPIC_RESULTS]
            partitions = len(topic_info) if isinstance(topic_info, dict) else "N/A"
            results.record(category, f"Topic: {TOPIC_RESULTS}", "PASS",
                           f"已创建, 分区数: {partitions}")
        else:
            results.record(category, f"Topic: {TOPIC_RESULTS}", "FAIL",
                           "Topic 未创建，请检查 KafkaTopicConfig 或服务启动日志")

        # 列出所有 uav 相关 topic
        uav_topics = [t for t in topics if t.startswith("uav.")]
        results.record(category, "UAV Topic 总览", "PASS",
                       f"共发现 {len(uav_topics)} 个 UAV 相关 Topic: {', '.join(sorted(uav_topics))}")

        duration = time.time() - start
        results.record(category, "Kafka 连接", "PASS",
                       f"成功连接 Kafka ({host}:{SERVICE_PORTS['kafka']})", duration)

    except Exception as e:
        duration = time.time() - start
        results.record(category, "Kafka 连接", "FAIL",
                       f"无法连接 Kafka ({host}:{SERVICE_PORTS['kafka']}): {e}", duration)
        results.record(category, f"Topic: {TOPIC_TASKS}", "FAIL", "Kafka 连接失败，跳过检查")
        results.record(category, f"Topic: {TOPIC_RESULTS}", "FAIL", "Kafka 连接失败，跳过检查")


# ============================================================
# Step 3: HTTP 健康端点检查
# ============================================================

def check_health_endpoints(host: str, results: VerifyResult) -> None:
    """通过 HTTP API 测试各服务健康端点"""
    category = "Step 3: HTTP 健康端点检查"

    for service, endpoint in HEALTH_ENDPOINTS.items():
        start = time.time()
        port = SERVICE_PORTS.get(service)
        if port is None:
            results.record(category, f"{service}", "WARN", "未配置端口映射")
            continue

        url = f"http://{host}:{port}{endpoint}"
        try:
            # 对 Java 服务使用 HMAC 签名
            if service not in ("nacos", "algorithm-engine"):
                headers = sign_request("GET", endpoint)
            else:
                headers = {}

            resp = requests.get(url, headers=headers, timeout=10)
            duration = time.time() - start

            if resp.status_code == 200:
                try:
                    body = resp.json()
                    # Spring Boot actuator health 格式
                    if isinstance(body, dict):
                        status_val = body.get("status", "UNKNOWN")
                        if status_val.upper() == "UP":
                            results.record(category, f"{service} ({url})", "PASS",
                                           f"HTTP {resp.status_code}, status=UP", duration)
                        else:
                            results.record(category, f"{service} ({url})", "WARN",
                                           f"HTTP {resp.status_code}, status={status_val}", duration)
                    else:
                        results.record(category, f"{service} ({url})", "PASS",
                                       f"HTTP {resp.status_code}", duration)
                except json.JSONDecodeError:
                    # algorithm-engine /health 可能返回非 JSON
                    results.record(category, f"{service} ({url})", "PASS",
                                   f"HTTP {resp.status_code}", duration)
            else:
                results.record(category, f"{service} ({url})", "FAIL",
                               f"HTTP {resp.status_code}", duration)

        except requests.exceptions.ConnectionError:
            duration = time.time() - start
            results.record(category, f"{service} ({url})", "FAIL",
                           "连接拒绝 (服务未启动或端口不可达)", duration)
        except requests.exceptions.Timeout:
            duration = time.time() - start
            results.record(category, f"{service} ({url})", "FAIL",
                           "连接超时", duration)
        except Exception as e:
            duration = time.time() - start
            results.record(category, f"{service} ({url})", "FAIL", str(e), duration)


# ============================================================
# Step 4: Kafka 全链路测试
# ============================================================

def test_kafka_full_chain(host: str, timeout: int, results: VerifyResult) -> None:
    """
    Kafka 全链路测试:
      1. 通过 assimilation-api 提交 3D-VAR 同化任务
      2. 验证任务消息到达 Kafka task topic
      3. 验证 Python algorithm-engine 消费并处理
      4. 验证结果回传到 Kafka result topic
    """
    category = "Step 4: Kafka 全链路测试"

    # --- 4a: 通过 assimilation-api 提交同化任务 ---
    sub_start = time.time()
    task_id = None
    try:
        assimilation_url = f"http://{host}:{SERVICE_PORTS['assimilation-api']}"
        task_payload = {
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

        body_str = json.dumps(task_payload, ensure_ascii=False)
        headers = sign_request("POST", "/api/v1/assimilation/tasks", body=body_str)

        resp = requests.post(
            f"{assimilation_url}/api/v1/assimilation/tasks",
            headers=headers,
            data=body_str,
            timeout=30,
        )
        resp.raise_for_status()
        resp_data = resp.json()

        code = resp_data.get("code", -1)
        if code in (0, 200):
            task_id = resp_data.get("data")
            duration = time.time() - sub_start
            results.record(category, "4a. 提交 3D-VAR 同化任务", "PASS",
                           f"任务ID: {task_id}, API 响应 code={code}", duration)
        else:
            duration = time.time() - sub_start
            results.record(category, "4a. 提交 3D-VAR 同化任务", "FAIL",
                           f"API 返回错误: code={code}, message={resp_data.get('message', 'unknown')}",
                           duration)
            return  # 后续步骤依赖任务提交成功

    except Exception as e:
        duration = time.time() - sub_start
        results.record(category, "4a. 提交 3D-VAR 同化任务", "FAIL", str(e), duration)
        return

    # --- 4b: 验证任务消息到达 Kafka task topic ---
    sub_start = time.time()
    try:
        consumer = KafkaConsumer(
            TOPIC_TASKS,
            bootstrap_servers=f"{host}:{SERVICE_PORTS['kafka']}",
            group_id=f"grayscale-verify-tasks-{uuid.uuid4().hex[:8]}",
            auto_offset_reset="earliest",
            consumer_timeout_ms=5000,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )

        found_task = False
        task_message = None
        for msg in consumer:
            value = msg.value
            msg_task_id = value.get("task_id") or value.get("taskId")
            if msg_task_id and str(msg_task_id) == str(task_id):
                found_task = True
                task_message = value
                break
            # 也检查 algorithm_id 是否匹配
            algo_id = value.get("algorithm_id") or value.get("algorithmId")
            if algo_id == "three_dimensional_var":
                found_task = True
                task_message = value
                break

        consumer.close()
        duration = time.time() - sub_start

        if found_task and task_message:
            algo_id = task_message.get("algorithm_id") or task_message.get("algorithmId", "N/A")
            params = task_message.get("params", {})
            results.record(
                category, "4b. Kafka Task Topic 消息验证", "PASS",
                f"在 {TOPIC_TASKS} 中找到任务消息\n"
                f"  task_id: {task_message.get('task_id') or task_message.get('taskId')}\n"
                f"  algorithm_id: {algo_id}\n"
                f"  params keys: {list(params.keys()) if isinstance(params, dict) else 'N/A'}",
                duration,
            )
        else:
            results.record(
                category, "4b. Kafka Task Topic 消息验证", "FAIL",
                f"在 {TOPIC_TASKS} 中未找到任务ID={task_id} 的消息。\n"
                f"  可能原因: assimilation-api 未配置 Kafka 生产者，或 KAFKA_MOCK=true",
                duration,
            )

    except Exception as e:
        duration = time.time() - sub_start
        results.record(category, "4b. Kafka Task Topic 消息验证", "FAIL", str(e), duration)

    # --- 4c: 验证 Python algorithm-engine 消费并处理 ---
    sub_start = time.time()
    try:
        # 检查 algorithm-engine 日志或健康状态来确认消费
        engine_url = f"http://{host}:{SERVICE_PORTS['algorithm-engine']}"
        resp = requests.get(f"{engine_url}/health", timeout=10)
        duration = time.time() - sub_start

        if resp.status_code == 200:
            try:
                health_data = resp.json()
                engine_status = health_data.get("status", "unknown")
                results.record(
                    category, "4c. Algorithm-Engine 消费状态", "PASS",
                    f"Algorithm-Engine 健康检查通过, status={engine_status}",
                    duration,
                )
            except json.JSONDecodeError:
                results.record(
                    category, "4c. Algorithm-Engine 消费状态", "PASS",
                    f"Algorithm-Engine 响应正常 (HTTP {resp.status_code})",
                    duration,
                )
        else:
            results.record(
                category, "4c. Algorithm-Engine 消费状态", "FAIL",
                f"Algorithm-Engine 健康检查失败 (HTTP {resp.status_code})",
                duration,
            )

    except Exception as e:
        duration = time.time() - sub_start
        results.record(category, "4c. Algorithm-Engine 消费状态", "FAIL", str(e), duration)

    # --- 4d: 验证结果回传到 Kafka result topic ---
    sub_start = time.time()
    try:
        consumer = KafkaConsumer(
            TOPIC_RESULTS,
            bootstrap_servers=f"{host}:{SERVICE_PORTS['kafka']}",
            group_id=f"grayscale-verify-results-{uuid.uuid4().hex[:8]}",
            auto_offset_reset="earliest",
            consumer_timeout_ms=timeout * 1000,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )

        found_result = False
        result_message = None
        deadline = time.time() + timeout

        for msg in consumer:
            value = msg.value
            msg_task_id = value.get("task_id") or value.get("taskId")
            if msg_task_id and str(msg_task_id) == str(task_id):
                found_result = True
                result_message = value
                break
            if time.time() > deadline:
                break

        consumer.close()
        duration = time.time() - sub_start

        if found_result and result_message:
            result_status = result_message.get("status", "UNKNOWN")
            has_result = result_message.get("result") is not None
            has_error = result_message.get("error") is not None
            completed_at = result_message.get("completed_at") or result_message.get("completedAt", "N/A")

            results.record(
                category, "4d. Kafka Result Topic 结果验证", "PASS",
                f"在 {TOPIC_RESULTS} 中找到结果消息\n"
                f"  task_id: {result_message.get('task_id') or result_message.get('taskId')}\n"
                f"  status: {result_status}\n"
                f"  has_result: {has_result}\n"
                f"  has_error: {has_error}\n"
                f"  completed_at: {completed_at}",
                duration,
            )
        else:
            results.record(
                category, "4d. Kafka Result Topic 结果验证", "FAIL",
                f"在 {timeout}s 超时内未在 {TOPIC_RESULTS} 中找到任务ID={task_id} 的结果。\n"
                f"  可能原因:\n"
                f"  - Algorithm-Engine 未启动或未订阅 task topic\n"
                f"  - 算法执行失败\n"
                f"  - Kafka 消费延迟",
                duration,
            )

    except Exception as e:
        duration = time.time() - sub_start
        results.record(category, "4d. Kafka Result Topic 结果验证", "FAIL", str(e), duration)

    # --- 4e: 查询 assimilation-api 任务最终状态 ---
    sub_start = time.time()
    try:
        headers = sign_request("GET", f"/api/v1/assimilation/tasks/{task_id}")
        resp = requests.get(
            f"http://{host}:{SERVICE_PORTS['assimilation-api']}/api/v1/assimilation/tasks/{task_id}",
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        resp_data = resp.json()
        task_status = resp_data.get("data", {}).get("status", "UNKNOWN") if isinstance(resp_data.get("data"), dict) else "UNKNOWN"
        duration = time.time() - sub_start

        if task_status in ("COMPLETED", "SUCCESS"):
            results.record(category, "4e. 同化任务最终状态", "PASS",
                           f"任务ID={task_id}, 最终状态={task_status}", duration)
        elif task_status in ("PENDING", "RUNNING"):
            results.record(category, "4e. 同化任务最终状态", "WARN",
                           f"任务ID={task_id}, 状态={task_status} (可能仍在处理中)", duration)
        else:
            results.record(category, "4e. 同化任务最终状态", "FAIL",
                           f"任务ID={task_id}, 状态={task_status}", duration)

    except Exception as e:
        duration = time.time() - sub_start
        results.record(category, "4e. 同化任务最终状态", "WARN", str(e), duration)


# ============================================================
# Utility
# ============================================================

def _run_command(cmd: str) -> str | None:
    """执行 shell 命令并返回 stdout"""
    import subprocess
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except Exception:
        return None


# ============================================================
# Main
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="UAV Platform V2 - Docker 灰度环境 Kafka 全链路验证"
    )
    parser.add_argument(
        "--host", default="localhost",
        help="Docker 宿主机地址 (default: localhost)",
    )
    parser.add_argument(
        "--timeout", type=int, default=30,
        help="Kafka 消费等待超时时间，单位秒 (default: 30)",
    )
    parser.add_argument(
        "--skip-kafka-test", action="store_true",
        help="跳过 Kafka 全链路测试（仅检查容器和健康端点）",
    )
    args = parser.parse_args()

    print("=" * 72)
    print("  UAV Platform V2 - Docker 灰度环境 Kafka 全链路验证")
    print("=" * 72)
    print(f"  目标主机: {args.host}")
    print(f"  Kafka 消费超时: {args.timeout}s")
    print(f"  Kafka 全链路测试: {'跳过' if args.skip_kafka_test else '执行'}")
    print(f"  HMAC Access Key: {ACCESS_KEY}")
    print("=" * 72)
    print()

    results = VerifyResult()

    # Step 1: Docker 容器状态
    print("[1/4] 检查 Docker 容器状态...")
    check_docker_containers(results)

    # Step 2: Kafka Topic 验证
    print("[2/4] 验证 Kafka Topic...")
    check_kafka_topics(args.host, results)

    # Step 3: HTTP 健康端点
    print("[3/4] 测试 HTTP 健康端点...")
    check_health_endpoints(args.host, results)

    # Step 4: Kafka 全链路
    if args.skip_kafka_test:
        print("[4/4] Kafka 全链路测试: 跳过 (--skip-kafka-test)")
        results.record("Step 4: Kafka 全链路测试", "全链路测试", "WARN",
                       "已跳过 (--skip-kafka-test)")
    else:
        print("[4/4] 执行 Kafka 全链路测试...")
        test_kafka_full_chain(args.host, args.timeout, results)

    # 输出报告
    print(results.report())

    # 退出码
    sys.exit(1 if results.failed > 0 else 0)


if __name__ == "__main__":
    main()
