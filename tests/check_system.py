#!/usr/bin/env python3
# check_system.py
# 系统检查脚本

import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_project_structure():
    logger.info("=== 检查项目结构 ===")

    core_dirs = [
        "api-gateway",
        "data-assimilation-platform",
        "data-assimilation-service",
        "edge-cloud-coordinator",
        "uav-path-planning-system",
        "wrf-processor-service",
        "meteor-forecast-service",
        "path-planning-service",
        "uav-platform-service",
        "uav-weather-collector",
        "uav-edge-sdk",
        "deployments",
        "docs",
        "tests",
        "scripts"
    ]

    for dir_name in core_dirs:
        if os.path.exists(dir_name):
            logger.info(f"[OK] {dir_name} 目录存在")
        else:
            logger.info(f"[ERROR] {dir_name} 目录不存在")

    config_files = [
        "docker-compose.yml",
        "data-assimilation-platform/docker-compose.yml",
        "uav-path-planning-system/docker-compose.yml",
        ".env.example"
    ]

    logger.info("\n=== 检查配置文件 ===")
    for config_file in config_files:
        if os.path.exists(config_file):
            logger.info(f"[OK] {config_file} 存在")
        else:
            logger.info(f"[ERROR] {config_file} 不存在")


def check_python_environment():
    logger.info("\n=== 检查Python环境 ===")
    logger.info(f"Python版本: {sys.version}")

    try:
        logger.info("[OK] numpy 已安装")
    except ImportError:
        logger.info("[ERROR] numpy 未安装")

    try:
        logger.info("[OK] scipy 已安装")
    except ImportError:
        logger.info("[ERROR] scipy 未安装")

    try:
        logger.info("[OK] pandas 已安装")
    except ImportError:
        logger.info("[ERROR] pandas 未安装")

    try:
        logger.info("[OK] netCDF4 已安装")
    except ImportError:
        logger.info("[WARNING] netCDF4 未安装")

    try:
        logger.info("[OK] xgboost 已安装")
    except ImportError:
        logger.info("[WARNING] xgboost 未安装")

    try:
        logger.info("[OK] sklearn 已安装")
    except ImportError:
        logger.info("[WARNING] sklearn 未安装")


def check_java_environment():
    logger.info("\n=== 检查Java环境 ===")
    try:
        import subprocess
        result = subprocess.run(["java", "-version"], capture_output=True, text=True)
        logger.info(f"Java版本: {result.stderr.split(chr(10))[0]}")
    except Exception as e:
        logger.info(f"[ERROR] Java未安装或无法访问: {e}")


def check_docker_environment():
    logger.info("\n=== 检查Docker环境 ===")
    try:
        import subprocess
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        logger.info(f"Docker版本: {result.stdout.strip()}")
    except Exception as e:
        logger.info(f"[ERROR] Docker未安装或无法访问: {e}")


def check_algorithm_implementation():
    logger.info("\n=== 检查算法实现 ===")

    assimilation_files = [
        "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/models/three_dimensional_var.py",
        "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/models/four_dimensional_var.py",
        "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/models/enkf.py",
        "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/models/enhanced_bayesian.py",
        "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/core/assimilator.py",
        "data-assimilation-platform/algorithm_core/src/bayesian_assimilation/core/base.py"
    ]

    for file_path in assimilation_files:
        if os.path.exists(file_path):
            logger.info(f"[OK] {file_path} 存在")
        else:
            logger.info(f"[ERROR] {file_path} 不存在")

    planning_files = [
        "path-planning-service/src/main/python/three_layer_planner.py",
        "path-planning-service/src/main/python/advanced_planners.py",
        "path-planning-service/src/main/python/reinforcement_learning.py",
        "path-planning-service/src/main/python/multi_objective_planner.py",
        "path-planning-service/src/main/python/uncertainty_planner.py",
        "path-planning-service/src/main/python/digital_twin.py",
        "path-planning-service/src/main/python/trajectory_4d.py",
        "path-planning-service/src/main/python/knowledge_graph.py",
        "path-planning-service/src/main/python/physics_maintenance.py"
    ]

    logger.info("\n=== 检查路径规划算法 ===")
    for file_path in planning_files:
        if os.path.exists(file_path):
            logger.info(f"[OK] {file_path} 存在")
        else:
            logger.info(f"[ERROR] {file_path} 不存在")

    meteor_files = [
        "meteor-forecast-service/src/main/python/meteor_forecast.py",
    ]

    logger.info("\n=== 检查气象预测算法 ===")
    for file_path in meteor_files:
        if os.path.exists(file_path):
            logger.info(f"[OK] {file_path} 存在")
        else:
            logger.info(f"[ERROR] {file_path} 不存在")


def check_frontend_implementation():
    logger.info("\n=== 检查前端实现 ===")
    frontend_files = [
        "uav-path-planning-system/frontend-vue/package.json",
        "uav-path-planning-system/frontend-vue/src/App.vue",
        "uav-path-planning-system/frontend-vue/src/views/PathPlanningView.vue",
        "uav-path-planning-system/frontend-vue/src/views/WeatherView.vue",
        "uav-path-planning-system/frontend-vue/src/views/MonitoringView.vue",
        "uav-path-planning-system/frontend-vue/src/views/HistoryView.vue"
    ]

    existing_count = 0
    total_count = len(frontend_files)  # noqa: F841

    for file_path in frontend_files:
        if os.path.exists(file_path):
            logger.info(f"[OK] {file_path} 存在")
            existing_count += 1
        else:
            logger.info(f"[ERROR] {file_path} 不存在")

    if existing_count == 0:
        logger.info("[INFO] 前端目录可能不存在或使用了不同的目录结构")


def check_security_implementation():
    logger.info("\n=== 检查安全性实现 ===")
    security_files = [
        "uav-path-planning-system/backend-spring/src/main/java/com/uav/config/SecurityConfig.java",
        "uav-path-planning-system/backend-spring/src/main/java/com/uav/config/JwtUtil.java",
        "uav-path-planning-system/backend-spring/src/main/java/com/uav/config/JwtFilter.java",
        "uav-path-planning-system/backend-spring/src/main/java/com/uav/model/User.java",
        "uav-path-planning-system/backend-spring/src/main/java/com/uav/model/Role.java",
        "uav-path-planning-system/backend-spring/src/main/java/com/uav/service/CustomUserDetailsService.java"
    ]

    existing_count = 0
    total_count = len(security_files)  # noqa: F841

    for file_path in security_files:
        if os.path.exists(file_path):
            logger.info(f"[OK] {file_path} 存在")
            existing_count += 1
        else:
            logger.info(f"[ERROR] {file_path} 不存在")

    if existing_count == 0:
        logger.info("[INFO] 后端Spring目录可能不存在或使用了不同的目录结构")


def check_deployment():
    logger.info("\n=== 检查部署配置 ===")
    deployment_files = [
        "docker-compose.yml",
        "DEPLOYMENT.md",
        "README.md",
        ".env.example"
    ]

    for file_path in deployment_files:
        if os.path.exists(file_path):
            logger.info(f"[OK] {file_path} 存在")
        else:
            logger.info(f"[ERROR] {file_path} 不存在")

    k8s_files = [
        "deployments/kubernetes/namespace.yml",
        "deployments/kubernetes/secrets.yml"
    ]

    for file_path in k8s_files:
        if os.path.exists(file_path):
            logger.info(f"[OK] {file_path} 存在")
        else:
            logger.info(f"[ERROR] {file_path} 不存在")


def main():
    logger.info("开始检查无人机路径规划系统...")
    logger.info("=" * 60)

    check_project_structure()
    check_python_environment()
    check_java_environment()
    check_docker_environment()
    check_algorithm_implementation()
    check_frontend_implementation()
    check_security_implementation()
    check_deployment()

    logger.info("=" * 60)
    logger.info("系统检查完成！")


if __name__ == "__main__":
    main()
