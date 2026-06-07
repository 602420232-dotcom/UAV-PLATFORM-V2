#!/usr/bin/env python3
# test_system.py
# 系统功能测试脚本

import logging
import time

import requests

logger = logging.getLogger(__name__)

# 服务地址
BASE_URL = "http://localhost:8080/api"
WRF_URL = "http://localhost:8081/api/wrf"
ASSIMILATION_URL = "http://localhost:8084/api/assimilation"
FORECAST_URL = "http://localhost:8082/api/forecast"
PLANNING_URL = "http://localhost:8083/api/planning"

# 测试结果
results = []


def test_service(name, url, endpoint, method="GET", data=None):
    """测试服务是否正常运行"""
    try:
        full_url = f"{url}{endpoint}"
        if method == "GET":
            response = requests.get(full_url, timeout=10)
        else:
            response = requests.post(full_url, json=data, timeout=10)

        status = "成功" if response.status_code == 200 else "失败"
        results.append({
            "service": name,
            "endpoint": endpoint,
            "status": status,
            "status_code": response.status_code,
            "response": response.text[:100] + "..." if len(response.text) > 100 else response.text
        })
        print(f"✓ {name} {endpoint}: {status} ({response.status_code})")
    except Exception as e:
        results.append({
            "service": name,
            "endpoint": endpoint,
            "status": "失败",
            "error": str(e)
        })
        print(f"✗ {name} {endpoint}: 失败 - {str(e)}")


def test_wrf_service():
    """测试WRF处理服务"""
    logger.info("\n=== 测试WRF处理服务 ===")
    test_service("WRF处理服务", WRF_URL, "/data")


def test_assimilation_service():
    """测试贝叶斯同化服务"""
    logger.info("\n=== 测试贝叶斯同化服务 ===")
    test_service("贝叶斯同化服务", ASSIMILATION_URL, "/health")


def test_forecast_service():
    """测试气象预测服务"""
    logger.info("\n=== 测试气象预测服务 ===")
    test_service("气象预测服务", FORECAST_URL, "/models")


def test_planning_service():
    """测试路径规划服务"""
    logger.info("\n=== 测试路径规划服务 ===")
    test_service("路径规划服务", PLANNING_URL, "/health")


def test_main_platform():
    """测试主平台服务"""
    logger.info("\n=== 测试主平台服务 ===")
    test_service("主平台服务", BASE_URL, "/platform/health")


def test_integration():
    """测试服务集成"""
    logger.info("\n=== 测试服务集成 ===")
    # 测试完整路径规划流程
    test_data = {
        "droneCount": 2,
        "taskPoints": [
            {"id": 1, "lat": 39.9042, "lng": 116.4074, "demand": 1},
            {"id": 2, "lat": 39.9142, "lng": 116.4174, "demand": 2},
            {"id": 3, "lat": 39.9242, "lng": 116.4274, "demand": 1}
        ],
        "baseLocation": {"lat": 39.9042, "lng": 116.4074},
        "timeWindow": {"start": "2024-01-01T08:00:00", "end": "2024-01-01T18:00:00"}
    }
    test_service("主平台服务", BASE_URL, "/platform/plan", "POST", test_data)


def generate_report():
    """生成测试报告"""
    logger.info("\n=== 测试报告 ===")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试服务数量: {len(results)}")

    success_count = sum(1 for r in results if r.get("status") == "成功")
    failure_count = len(results) - success_count

    print(f"成功: {success_count}")
    print(f"失败: {failure_count}")
    print(f"成功率: {success_count / len(results) * 100:.1f}%")

    if failure_count > 0:
        logger.info("\n失败详情:")
        for r in results:
            if r.get("status") != "成功":
                print(f"- {r['service']} {r['endpoint']}: {r.get('error', '未知错误')}")


if __name__ == "__main__":
    logger.info("开始测试无人机路径规划系统...")

    # 测试各个服务
    test_wrf_service()
    test_assimilation_service()
    test_forecast_service()
    test_planning_service()
    test_main_platform()

    # 测试服务集成
    test_integration()

    # 生成测试报告
    generate_report()

    logger.info("\n测试完成!")
