#!/usr/bin/env bash
# ============================================================
# UAV Platform V2 - 一键启动脚本 (Bash)
# ============================================================
# 用法:
#   ./start.sh              # 完整启动（构建 + 启动）
#   ./start.sh --skip-build    # 跳过构建，直接启动
#   ./start.sh --infra-only    # 仅启动基础设施
#   ./start.sh --down          # 停止所有服务
#   ./start.sh --status        # 查看服务状态
#   ./start.sh --logs          # 查看日志 (Ctrl+C 退出)
# ============================================================

set -euo pipefail

# 颜色
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

log_info()  { echo -e "${BLUE}[INFO]${NC} $(date '+%H:%M:%S') $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}   $(date '+%H:%M:%S') $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $(date '+%H:%M:%S') $1"; }
log_err()   { echo -e "${RED}[ERR]${NC}  $(date '+%H:%M:%S') $1"; }

# 项目目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
ENV_FILE="$PROJECT_DIR/.env"
ENV_EXAMPLE="$PROJECT_DIR/.env.example"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"

# ============================================================
# 前置检查
# ============================================================
check_prerequisites() {
    local missing=()
    command -v docker >/dev/null 2>&1 || missing+=("docker")
    docker compose version >/dev/null 2>&1 || missing+=("docker-compose")
    if [[ "${SKIP_BUILD:-0}" != "1" ]]; then
        command -v mvn >/dev/null 2>&1 || missing+=("mvn")
    fi
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_err "缺少必要工具: ${missing[*]}"
        exit 1
    fi
    log_ok "前置条件检查通过"
}

# ============================================================
# 初始化 .env
# ============================================================
init_env() {
    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ -f "$ENV_EXAMPLE" ]]; then
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            log_info "已从 .env.example 创建 .env"
            log_warn "请编辑 .env 填入实际密码，然后重新运行"
            echo ""
            echo "  编辑命令: nano $ENV_FILE"
            exit 0
        else
            log_err "未找到 .env.example"
            exit 1
        fi
    fi
    log_ok ".env 已就绪"
}

# ============================================================
# Maven 构建
# ============================================================
build_maven() {
    log_info "Maven 打包 Java 服务..."
    cd "$PROJECT_DIR"
    mvn package -DskipTests -q
    log_ok "Maven 构建完成"
}

# ============================================================
# 等待健康
# ============================================================
wait_healthy() {
    local containers=("$@")
    local timeout="${WAIT_TIMEOUT:-180}"
    local interval=5

    for container in "${containers[@]}"; do
        local elapsed=0
        while [[ $elapsed -lt $timeout ]]; do
            local health
            health=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "not found")
            if [[ "$health" == "healthy" ]]; then
                log_ok "$container 就绪"
                break
            elif [[ "$health" == "unhealthy" ]]; then
                log_warn "$container unhealthy: docker logs $container --tail 20"
                break
            fi
            sleep $interval
            elapsed=$((elapsed + interval))
        done
        if [[ $elapsed -ge $timeout ]]; then
            log_warn "$container 启动超时 (${timeout}s)"
        fi
    done
}

# ============================================================
# 打印访问地址
# ============================================================
show_endpoints() {
    echo ""
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}  UAV Platform V2 服务已启动${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""
    echo "  业务服务:"
    echo -e "    API 网关:       ${GREEN}http://localhost:8258${NC}"
    echo -e "    前端控制台:     ${GREEN}http://localhost:3002${NC}"
    echo -e "    算法引擎:       ${GREEN}http://localhost:9095${NC}"
    echo ""
    echo "  基础设施:"
    echo "    MySQL:          localhost:3307"
    echo "    Redis:          localhost:6380"
    echo "    Nacos:          http://localhost:8950/nacos"
    echo "    Kafka:          localhost:19092"
    echo ""
    echo "  监控:"
    echo "    Prometheus:     http://localhost:19091"
    echo "    Grafana:        http://localhost:3001"
    echo ""
    echo "  常用命令:"
    echo "    查看日志:   docker compose logs -f"
    echo "    停止服务:   ./start.sh --down"
    echo "    查看状态:   ./start.sh --status"
    echo -e "${CYAN}============================================================${NC}"
}

# ============================================================
# 主逻辑
# ============================================================
case "${1:-}" in
    --down)
        log_info "停止所有服务..."
        cd "$PROJECT_DIR"
        docker compose -f "$COMPOSE_FILE" --env-file .env down --volumes
        log_ok "所有服务已停止"
        ;;
    --status)
        cd "$PROJECT_DIR"
        docker compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
        ;;
    --logs)
        cd "$PROJECT_DIR"
        docker compose -f "$COMPOSE_FILE" logs -f --tail 50
        ;;
    --infra-only)
        check_prerequisites
        init_env
        [[ "${SKIP_BUILD:-0}" != "1" ]] && build_maven
        log_info "启动基础设施..."
        cd "$PROJECT_DIR"
        docker compose -f "$COMPOSE_FILE" --env-file .env up -d --build \
            mysql redis nacos zookeeper kafka
        log_info "等待基础设施就绪..."
        wait_healthy uav-mysql uav-redis uav-nacos
        log_ok "基础设施已启动"
        ;;
    --skip-build)
        export SKIP_BUILD=1
        check_prerequisites
        init_env
        log_info "启动所有服务 (跳过构建)..."
        cd "$PROJECT_DIR"
        docker compose -f "$COMPOSE_FILE" --env-file .env up -d
        log_info "等待核心服务就绪..."
        wait_healthy uav-mysql uav-redis uav-nacos uav-gateway uav-platform-api uav-algorithm-engine uav-console
        show_endpoints
        ;;
    *)
        check_prerequisites
        init_env
        build_maven
        log_info "构建并启动所有服务..."
        cd "$PROJECT_DIR"
        docker compose -f "$COMPOSE_FILE" --env-file .env up -d --build
        log_info "等待核心服务就绪..."
        wait_healthy uav-mysql uav-redis uav-nacos uav-gateway uav-platform-api uav-algorithm-engine uav-console
        show_endpoints
        ;;
esac
