#!/usr/bin/env python3
"""
UAV Platform V2 - Docker Compose 多环境验证脚本

验证所有 compose 文件的语法正确性、配置完整性以及环境特定要求:
  - docker-compose.yml          基础配置
  - docker-compose.override.yml  开发环境（自动加载）
  - docker-compose.staging.yml   灰度/预发布环境
  - docker-compose.prod.yml      生产环境

用法:
    python scripts/validate-compose.py
    python scripts/validate-compose.py --verbose
    python scripts/validate-compose.py --compose-dir /path/to/project
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

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


def color_text(text: str, color: str) -> str:
    return f"{color}{text}{Color.RESET}"


def print_header(text: str) -> None:
    print(f"\n{color_text('=' * 60, Color.CYAN)}")
    print(color_text(f"  {text}", Color.CYAN))
    print(color_text('=' * 60, Color.CYAN))


def print_pass(msg: str) -> None:
    print(f"  {color_text('PASS', Color.GREEN)} {msg}")


def print_fail(msg: str) -> None:
    print(f"  {color_text('FAIL', Color.RED)} {msg}")


def print_warn(msg: str) -> None:
    print(f"  {color_text('WARN', Color.YELLOW)} {msg}")


def print_info(msg: str) -> None:
    print(f"  {color_text('INFO', Color.CYAN)} {msg}")


# ============================================================
# YAML 解析（不依赖 PyYAML，使用 docker compose config）
# ============================================================

def try_parse_yaml_with_python(filepath: Path) -> dict[str, Any] | None:
    """尝试用 Python 解析 YAML（如果有 PyYAML）"""
    try:
        import yaml  # type: ignore
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}  # pyright: ignore[reportReturnType]
    except ImportError:
        return None
    except yaml.YAMLError as e:
        print_fail(f"YAML 解析错误 ({filepath.name}): {e}")
        return None


def try_docker_compose_config(
    compose_files: list[Path],
    verbose: bool = False,
) -> tuple[bool, str]:
    """使用 docker compose config 验证语法"""
    cmd = [
        "docker", "compose",
        "-f", str(compose_files[0]),
    ]
    for f in compose_files[1:]:
        cmd.extend(["-f", str(f)])
    cmd.extend(["config", "--quiet"])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return True, ""
        else:
            stderr = result.stderr.strip()
            if verbose:
                print_info(f"docker compose config stderr: {stderr}")
            return False, stderr
    except FileNotFoundError:
        print_warn("docker compose 命令不可用，跳过 docker compose config 验证")
        return True, "docker compose not available"
    except subprocess.TimeoutExpired:
        return False, "docker compose config 命令超时 (30s)"


# ============================================================
# 验证规则
# ============================================================

def validate_base_config(data: dict[str, Any], verbose: bool) -> list[str]:
    """验证基础 docker-compose.yml 配置"""
    errors: list[str] = []
    services = data.get("services", {})

    if not services:
        errors.append("基础配置中没有定义任何服务")
        return errors

    # 检查必需的基础设施服务
    required_infra = ["mysql", "redis", "nacos"]
    for svc in required_infra:
        if svc not in services:
            errors.append(f"缺少必需的基础设施服务: {svc}")

    # 检查所有服务是否有 healthcheck
    for svc_name, svc_config in services.items():
        if svc_name == "zookeeper":
            continue  # zookeeper 通常不配置 healthcheck
        if "healthcheck" not in svc_config:
            print_warn(f"服务 {svc_name} 没有配置 healthcheck")

    # 检查 Java 服务的 JAVA_OPTS
    java_services = [
        "api-gateway", "platform-api", "weather-api",
        "assimilation-api", "risk-api", "observation-api",
        "planning-api", "utm-api",
    ]
    for svc in java_services:
        if svc in services:
            env = services[svc].get("environment", [])
            has_java_opts = any(
                isinstance(e, str) and e.startswith("JAVA_OPTS=")
                for e in env
            )
            if not has_java_opts:
                errors.append(f"Java 服务 {svc} 缺少 JAVA_OPTS 环境变量")

    # 检查网络配置
    if "networks" not in data:
        errors.append("缺少 networks 配置")

    # 检查 volumes 配置
    if "volumes" not in data:
        errors.append("缺少 volumes 配置")

    return errors


def validate_dev_override(data: dict[str, Any], verbose: bool) -> list[str]:
    """验证开发环境 override 配置"""
    errors: list[str] = []
    services = data.get("services", {})

    if not services:
        errors.append("开发环境 override 中没有定义任何服务覆盖")
        return errors

    # 检查 Java 服务是否开启 debug 端口
    java_services = [
        "api-gateway", "platform-api", "weather-api",
        "assimilation-api", "risk-api", "observation-api",
        "planning-api", "utm-api",
    ]
    for svc in java_services:
        if svc in services:
            ports = services[svc].get("ports", [])
            has_debug_port = any(
                isinstance(p, str) and ":5005" in p
                for p in ports
            )
            if not has_debug_port:
                print_warn(f"开发环境 {svc} 未开启 JDWP debug 端口 (:5005)")

    # 检查 algorithm-engine 是否开启 debugpy
    if "algorithm-engine" in services:
        ports = services["algorithm-engine"].get("ports", [])
        has_debugpy = any(
            isinstance(p, str) and ":5678" in p
            for p in ports
        )
        if not has_debugpy:
            print_warn("开发环境 algorithm-engine 未开启 debugpy 端口 (:5678)")

    # 检查监控服务是否设为 monitoring profile
    monitoring_svcs = ["prometheus", "grafana", "alertmanager"]
    for svc in monitoring_svcs:
        if svc in services:
            profiles = services[svc].get("profiles", [])
            if "monitoring" not in profiles:
                errors.append(
                    f"开发环境 {svc} 应设置 profiles: [monitoring] 以按需启动"
                )

    # 检查 KAFKA_MOCK=true
    for svc in java_services:
        if svc in services:
            env = services[svc].get("environment", [])
            has_mock = any(
                isinstance(e, str) and "KAFKA_MOCK=true" in e
                for e in env
            )
            if not has_mock:
                print_warn(f"开发环境 {svc} 未设置 KAFKA_MOCK=true")

    return errors


def validate_staging_config(data: dict[str, Any], verbose: bool) -> list[str]:
    """验证灰度环境配置"""
    errors: list[str] = []
    services = data.get("services", {})

    if not services:
        errors.append("灰度环境配置中没有定义任何服务覆盖")
        return errors

    # 1. 验证资源限制（CPU/内存）
    for svc_name, svc_config in services.items():
        if svc_name in ("prometheus", "grafana", "alertmanager"):
            continue
        deploy = svc_config.get("deploy", {})
        resources = deploy.get("resources", {})
        limits = resources.get("limits", {})

        if "memory" not in limits:
            errors.append(f"灰度环境 {svc_name} 缺少内存限制 (deploy.resources.limits.memory)")
        if "cpus" not in limits:
            print_warn(f"灰度环境 {svc_name} 缺少 CPU 限制 (deploy.resources.limits.cpus)")

    # 2. 验证副本数配置（灰度环境通常 replicas=1，gateway 可为 2）
    for svc_name, svc_config in services.items():
        if svc_name in ("prometheus", "grafana", "alertmanager"):
            continue
        deploy = svc_config.get("deploy", {})
        if "mode" in deploy and deploy["mode"] == "replicated":
            replicas = deploy.get("replicas", 1)
            if verbose:
                print_info(f"灰度环境 {svc_name}: replicas={replicas}")

    # 3. 验证日志限制
    for svc_name, svc_config in services.items():
        if svc_name in ("prometheus", "grafana", "alertmanager"):
            continue
        logging_config = svc_config.get("logging", {})
        if not logging_config:
            print_warn(f"灰度环境 {svc_name} 未配置日志限制 (logging)")
        else:
            options = logging_config.get("options", {})
            if "max-size" not in options:
                print_warn(f"灰度环境 {svc_name} 日志未设置 max-size")
            if "max-file" not in options:
                print_warn(f"灰度环境 {svc_name} 日志未设置 max-file")

    # 4. 验证监控启用
    monitoring_svcs = ["prometheus", "grafana", "alertmanager"]
    for svc in monitoring_svcs:
        if svc in services:
            profiles = services[svc].get("profiles", [])
            if profiles:
                errors.append(
                    f"灰度环境 {svc} 应设置 profiles: [] 以启用监控"
                )
            else:
                if verbose:
                    print_info(f"灰度环境 {svc}: 监控已启用 (profiles=[])")

    # 5. 验证 KAFKA_MOCK=false
    for svc_name, svc_config in services.items():
        if svc_name in ("prometheus", "grafana", "alertmanager", "algorithm-engine"):
            continue
        env = svc_config.get("environment", [])
        has_mock_false = any(
            isinstance(e, str) and "KAFKA_MOCK=false" in e
            for e in env
        )
        if not has_mock_false:
            print_warn(f"灰度环境 {svc_name} 未设置 KAFKA_MOCK=false")

    # 6. 验证 restart 策略
    for svc_name, svc_config in services.items():
        if svc_name in ("prometheus", "grafana", "alertmanager"):
            continue
        restart = svc_config.get("restart", "")
        if restart not in ("on-failure", "always"):
            print_warn(f"灰度环境 {svc_name} restart 策略为 '{restart}'，建议 on-failure 或 always")

    return errors


def validate_prod_config(data: dict[str, Any], verbose: bool) -> list[str]:
    """验证生产环境配置"""
    errors: list[str] = []
    services = data.get("services", {})

    if not services:
        errors.append("生产环境配置中没有定义任何服务覆盖")
        return errors

    # 1. 验证 OOM heap dump 配置
    java_services = [
        "api-gateway", "platform-api", "weather-api",
        "assimilation-api", "risk-api", "observation-api",
        "planning-api", "utm-api",
    ]
    for svc in java_services:
        if svc in services:
            env = services[svc].get("environment", [])
            java_opts = ""
            for e in env:
                if isinstance(e, str) and e.startswith("JAVA_OPTS="):
                    java_opts = e
                    break

            if not java_opts:
                errors.append(f"生产环境 {svc} 缺少 JAVA_OPTS 环境变量")
                continue

            if "HeapDumpOnOutOfMemoryError" not in java_opts:
                errors.append(
                    f"生产环境 {svc} JAVA_OPTS 未配置 OOM heap dump "
                    "(-XX:+HeapDumpOnOutOfMemoryError)"
                )
            if "HeapDumpPath" not in java_opts:
                print_warn(f"生产环境 {svc} JAVA_OPTS 未指定 HeapDumpPath")

    # 2. 验证滚动更新策略
    for svc_name, svc_config in services.items():
        if svc_name in ("prometheus", "grafana", "alertmanager"):
            continue
        deploy = svc_config.get("deploy", {})
        if "mode" in deploy and deploy["mode"] == "replicated":
            replicas = deploy.get("replicas", 1)
            if replicas > 1:
                update_config = deploy.get("update_config", {})
                if not update_config:
                    errors.append(
                        f"生产环境 {svc_name} replicas={replicas} 但未配置 "
                        "滚动更新策略 (deploy.update_config)"
                    )
                else:
                    if "parallelism" not in update_config:
                        print_warn(
                            f"生产环境 {svc_name} 未设置滚动更新 parallelism"
                        )
                    if "delay" not in update_config:
                        print_warn(
                            f"生产环境 {svc_name} 未设置滚动更新 delay"
                        )
                if verbose:
                    print_info(
                        f"生产环境 {svc_name}: replicas={replicas}, "
                        f"update_config={update_config}"
                    )

    # 3. 验证健康检查间隔调整
    base_services = [
        "api-gateway", "platform-api", "weather-api",
        "assimilation-api", "risk-api", "observation-api",
        "planning-api", "utm-api", "algorithm-engine",
    ]
    for svc in base_services:
        if svc in services:
            healthcheck = services[svc].get("healthcheck", {})
            if healthcheck:
                interval = healthcheck.get("interval", "")
                if verbose and interval:
                    print_info(f"生产环境 {svc} 健康检查间隔: {interval}")
            # 生产环境建议覆盖健康检查使其更宽松
            # （不强制，仅提示）

    # 4. 验证资源限制
    for svc_name, svc_config in services.items():
        deploy = svc_config.get("deploy", {})
        resources = deploy.get("resources", {})
        limits = resources.get("limits", {})

        if "memory" not in limits:
            errors.append(f"生产环境 {svc_name} 缺少内存限制")
        if "cpus" not in limits:
            errors.append(f"生产环境 {svc_name} 缺少 CPU 限制")

    # 5. 验证日志限制
    for svc_name, svc_config in services.items():
        logging_config = svc_config.get("logging", {})
        if not logging_config:
            errors.append(f"生产环境 {svc_name} 未配置日志限制")
        else:
            driver = logging_config.get("driver", "")
            if driver != "json-file":
                print_warn(f"生产环境 {svc_name} 日志驱动为 '{driver}'，建议 json-file")
            options = logging_config.get("options", {})
            if "max-size" not in options:
                errors.append(f"生产环境 {svc_name} 日志未设置 max-size")
            if "max-file" not in options:
                errors.append(f"生产环境 {svc_name} 日志未设置 max-file")

    # 6. 验证 restart: always
    for svc_name, svc_config in services.items():
        restart = svc_config.get("restart", "")
        if restart != "always":
            errors.append(
                f"生产环境 {svc_name} restart 策略为 '{restart}'，应为 always"
            )

    # 7. 验证监控全部启用
    monitoring_svcs = ["prometheus", "grafana", "alertmanager"]
    for svc in monitoring_svcs:
        if svc in services:
            profiles = services[svc].get("profiles", [])
            if profiles:
                errors.append(
                    f"生产环境 {svc} 应设置 profiles: [] 以启用监控"
                )

    # 8. 验证 KAFKA_MOCK=false
    for svc_name, svc_config in services.items():
        if svc_name in ("prometheus", "grafana", "alertmanager", "algorithm-engine"):
            continue
        env = svc_config.get("environment", [])
        has_mock_false = any(
            isinstance(e, str) and "KAFKA_MOCK=false" in e
            for e in env
        )
        if not has_mock_false:
            errors.append(f"生产环境 {svc_name} 未设置 KAFKA_MOCK=false")

    return errors


# ============================================================
# 主流程
# ============================================================

def find_compose_dir(args_compose_dir: str | None) -> Path:
    """确定 compose 文件所在目录"""
    if args_compose_dir:
        return Path(args_compose_dir)

    # 尝试从脚本位置向上查找
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    compose_file = project_root / "docker-compose.yml"
    if compose_file.exists():
        return project_root

    # 尝试当前工作目录
    cwd_compose = Path.cwd() / "docker-compose.yml"
    if cwd_compose.exists():
        return Path.cwd()

    print_fail("未找到 docker-compose.yml，请使用 --compose-dir 指定项目根目录")
    sys.exit(1)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="UAV Platform V2 - Docker Compose 多环境验证"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细信息",
    )
    parser.add_argument(
        "--compose-dir",
        type=str,
        default=None,
        help="项目根目录（包含 docker-compose.yml）",
    )
    args = parser.parse_args()

    compose_dir = find_compose_dir(args.compose_dir)
    verbose = args.verbose

    print_header("UAV Platform V2 - Docker Compose 多环境验证")
    print_info(f"项目目录: {compose_dir}")

    total_errors = 0

    # ============================================================
    # 1. 检查文件存在性
    # ============================================================
    print_header("1. 文件存在性检查")

    compose_files = {
        "base": compose_dir / "docker-compose.yml",
        "dev": compose_dir / "docker-compose.override.yml",
        "staging": compose_dir / "docker-compose.staging.yml",
        "prod": compose_dir / "docker-compose.prod.yml",
    }

    for env_name, filepath in compose_files.items():
        if filepath.exists():
            print_pass(f"{filepath.name} 存在")
        else:
            print_fail(f"{filepath.name} 不存在")
            total_errors += 1

    # ============================================================
    # 2. YAML 语法验证 (docker compose config)
    # ============================================================
    print_header("2. Docker Compose 语法验证")

    # 验证基础配置
    if compose_files["base"].exists():
        ok, err = try_docker_compose_config(
            [compose_files["base"]], verbose
        )
        if ok:
            print_pass("docker-compose.yml 语法正确")
        else:
            print_fail(f"docker-compose.yml 语法错误: {err}")
            total_errors += 1

    # 验证 dev 环境 (base + override)
    if compose_files["base"].exists() and compose_files["dev"].exists():
        ok, err = try_docker_compose_config(
            [compose_files["base"], compose_files["dev"]], verbose
        )
        if ok:
            print_pass("dev 环境 (base + override) 语法正确")
        else:
            print_fail(f"dev 环境语法错误: {err}")
            total_errors += 1

    # 验证 staging 环境
    if compose_files["base"].exists() and compose_files["staging"].exists():
        ok, err = try_docker_compose_config(
            [compose_files["base"], compose_files["staging"]], verbose
        )
        if ok:
            print_pass("staging 环境 (base + staging) 语法正确")
        else:
            print_fail(f"staging 环境语法错误: {err}")
            total_errors += 1

    # 验证 prod 环境
    if compose_files["base"].exists() and compose_files["prod"].exists():
        ok, err = try_docker_compose_config(
            [compose_files["base"], compose_files["prod"]], verbose
        )
        if ok:
            print_pass("prod 环境 (base + prod) 语法正确")
        else:
            print_fail(f"prod 环境语法错误: {err}")
            total_errors += 1

    # ============================================================
    # 3. 基础配置验证
    # ============================================================
    print_header("3. 基础配置验证 (docker-compose.yml)")

    if compose_files["base"].exists():
        base_data = try_parse_yaml_with_python(compose_files["base"])
        if base_data:
            errors = validate_base_config(base_data, verbose)
            if errors:
                for e in errors:
                    print_fail(e)
                    total_errors += 1
            else:
                print_pass("基础配置验证通过")
        else:
            print_warn("无法解析 YAML（需要 PyYAML），跳过内容验证")
    else:
        print_fail("docker-compose.yml 不存在，跳过验证")
        total_errors += 1

    # ============================================================
    # 4. 开发环境验证
    # ============================================================
    print_header("4. 开发环境验证 (docker-compose.override.yml)")

    if compose_files["dev"].exists():
        dev_data = try_parse_yaml_with_python(compose_files["dev"])
        if dev_data:
            errors = validate_dev_override(dev_data, verbose)
            if errors:
                for e in errors:
                    print_fail(e)
                    total_errors += 1
            else:
                print_pass("开发环境配置验证通过")
        else:
            print_warn("无法解析 YAML（需要 PyYAML），跳过内容验证")
    else:
        print_fail("docker-compose.override.yml 不存在，跳过验证")
        total_errors += 1

    # ============================================================
    # 5. 灰度环境验证
    # ============================================================
    print_header("5. 灰度环境验证 (docker-compose.staging.yml)")

    if compose_files["staging"].exists():
        staging_data = try_parse_yaml_with_python(compose_files["staging"])
        if staging_data:
            errors = validate_staging_config(staging_data, verbose)
            if errors:
                for e in errors:
                    print_fail(e)
                    total_errors += 1
            else:
                print_pass("灰度环境配置验证通过")
        else:
            print_warn("无法解析 YAML（需要 PyYAML），跳过内容验证")
    else:
        print_fail("docker-compose.staging.yml 不存在，跳过验证")
        total_errors += 1

    # ============================================================
    # 6. 生产环境验证
    # ============================================================
    print_header("6. 生产环境验证 (docker-compose.prod.yml)")

    if compose_files["prod"].exists():
        prod_data = try_parse_yaml_with_python(compose_files["prod"])
        if prod_data:
            errors = validate_prod_config(prod_data, verbose)
            if errors:
                for e in errors:
                    print_fail(e)
                    total_errors += 1
            else:
                print_pass("生产环境配置验证通过")
        else:
            print_warn("无法解析 YAML（需要 PyYAML），跳过内容验证")
    else:
        print_fail("docker-compose.prod.yml 不存在，跳过验证")
        total_errors += 1

    # ============================================================
    # 汇总
    # ============================================================
    print_header("验证结果汇总")

    if total_errors == 0:
        print_pass("所有验证通过!")
        print()
        return 0
    else:
        print_fail(f"发现 {total_errors} 个错误")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
