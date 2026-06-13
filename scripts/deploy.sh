#!/bin/bash
# ============================================================
# UAV Platform V2 - 部署脚本 (Bash)
# ============================================================
# 用法:
#   ./scripts/deploy.sh              # 构建并启动所有服务
#   ./scripts/deploy.sh --build-only # 仅构建镜像
#   ./scripts/deploy.sh --push       # 构建并推送到镜像仓库
#   ./scripts/deploy.sh --down       # 停止所有服务
#   ./scripts/deploy.sh --clean      # 停止并清除所有容器和镜像
# ============================================================

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.yml"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-ghcr.io/uav-platform}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# 服务列表
JAVA_SERVICES=(
    "api-gateway"
    "platform-api"
    "weather-api"
    "assimilation-api"
    "risk-api"
    "observation-api"
    "planning-api"
    "utm-api"
)
PYTHON_SERVICES=(
    "algorithm-engine"
)
ALL_SERVICES=("${JAVA_SERVICES[@]}" "${PYTHON_SERVICES[@]}" "console")

# ============================================================
# 工具函数
# ============================================================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') $1"
}

# ============================================================
# 构建函数
# ============================================================
build_java_services() {
    log_info "开始构建 Java 微服务..."
    cd "$PROJECT_DIR"

    # Maven 打包
    log_info "执行 Maven 打包..."
    mvn package -DskipTests -q

    for service in "${JAVA_SERVICES[@]}"; do
        log_info "构建镜像: $IMAGE_REGISTRY/$service:$IMAGE_TAG"

        if [ "$service" = "api-gateway" ]; then
            docker build -t "$IMAGE_REGISTRY/$service:$IMAGE_TAG" \
                -f gateway/api-gateway/Dockerfile . \
                --build-arg SERVICE_NAME="$service" \
                --build-arg SERVICE_DIR="gateway/api-gateway"
        else
            docker build -t "$IMAGE_REGISTRY/$service:$IMAGE_TAG" \
                -f services/$service/Dockerfile . \
                --build-arg SERVICE_NAME="$service" \
                --build-arg SERVICE_DIR="services/$service"
        fi

        log_success "镜像构建完成: $IMAGE_REGISTRY/$service:$IMAGE_TAG"
    done
}

build_python_services() {
    log_info "开始构建 Python 服务..."
    cd "$PROJECT_DIR"

    for service in "${PYTHON_SERVICES[@]}"; do
        log_info "构建镜像: $IMAGE_REGISTRY/$service:$IMAGE_TAG"
        docker build -t "$IMAGE_REGISTRY/$service:$IMAGE_TAG" \
            -f python/$service/Dockerfile python/$service/
        log_success "镜像构建完成: $IMAGE_REGISTRY/$service:$IMAGE_TAG"
    done
}

build_frontend() {
    log_info "开始构建前端控制台..."
    cd "$PROJECT_DIR"
    docker build -t "$IMAGE_REGISTRY/console:$IMAGE_TAG" \
        -f console/Dockerfile console/
    log_success "镜像构建完成: $IMAGE_REGISTRY/console:$IMAGE_TAG"
}

build_all() {
    log_info "========== 开始构建所有 Docker 镜像 =========="
    build_java_services
    build_python_services
    build_frontend
    log_success "========== 所有镜像构建完成 =========="
}

# ============================================================
# 推送函数
# ============================================================
push_images() {
    log_info "========== 开始推送镜像到仓库 =========="
    for service in "${ALL_SERVICES[@]}"; do
        log_info "推送镜像: $IMAGE_REGISTRY/$service:$IMAGE_TAG"
        docker push "$IMAGE_REGISTRY/$service:$IMAGE_TAG" || log_warn "推送失败: $service"
    done
    log_success "========== 镜像推送完成 =========="
}

# ============================================================
# 部署函数
# ============================================================
deploy() {
    log_info "========== 开始部署 UAV Platform V2 =========="
    cd "$PROJECT_DIR"

    # 启动基础设施
    log_info "启动基础设施服务 (MySQL, Redis, Nacos, Kafka)..."
    docker compose -f "$COMPOSE_FILE" up -d mysql redis zookeeper kafka nacos

    # 等待基础设施就绪
    log_info "等待基础设施服务就绪..."
    wait_for_service "uav-mysql" 60
    wait_for_service "uav-redis" 30
    wait_for_service "uav-nacos" 60

    # 启动业务服务
    log_info "启动业务微服务..."
    docker compose -f "$COMPOSE_FILE" up -d \
        api-gateway \
        platform-api \
        weather-api \
        assimilation-api \
        risk-api \
        observation-api \
        planning-api \
        utm-api \
        algorithm-engine \
        console

    # 等待所有服务就绪
    log_info "等待所有服务就绪..."
    local services=(
        "uav-gateway"
        "uav-platform-api"
        "uav-weather-api"
        "uav-assimilation-api"
        "uav-risk-api"
        "uav-observation-api"
        "uav-planning-api"
        "uav-utm-api"
        "uav-algorithm-engine"
        "uav-console"
    )

    for service in "${services[@]}"; do
        wait_for_service "$service" 120 || log_warn "服务 $service 启动超时"
    done

    # 显示服务状态
    show_status

    log_success "========== UAV Platform V2 部署完成 =========="
    echo ""
    echo "服务访问地址:"
    echo "  - API 网关:    http://localhost:8088"
    echo "  - 前端控制台:  http://localhost:3000"
    echo "  - Nacos 控制台: http://localhost:8848/nacos"
    echo "  - Grafana:      http://localhost:3001"
    echo "  - Prometheus:   http://localhost:9091"
}

# ============================================================
# 健康检查
# ============================================================
wait_for_service() {
    local container_name=$1
    local timeout=${2:-60}
    local elapsed=0

    while [ $elapsed -lt $timeout ]; do
        local status
        status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "not found")

        if [ "$status" = "healthy" ]; then
            log_success "$container_name is healthy"
            return 0
        elif [ "$status" = "unhealthy" ]; then
            log_error "$container_name is unhealthy"
            return 1
        fi

        sleep 5
        elapsed=$((elapsed + 5))
    done

    log_warn "$container_name health check timed out after ${timeout}s"
    return 1
}

# ============================================================
# 状态显示
# ============================================================
show_status() {
    echo ""
    echo "============================================================"
    echo "  UAV Platform V2 - 服务状态"
    echo "============================================================"
    docker compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    echo "============================================================"
}

# ============================================================
# 主逻辑
# ============================================================
case "${1:-}" in
    --build-only)
        build_all
        ;;
    --push)
        build_all
        push_images
        ;;
    --down)
        log_info "停止所有服务..."
        docker compose -f "$COMPOSE_FILE" down
        log_success "所有服务已停止"
        ;;
    --clean)
        log_info "停止并清除所有容器、网络和镜像..."
        docker compose -f "$COMPOSE_FILE" down --volumes --rmi local
        log_success "清理完成"
        ;;
    --status)
        show_status
        ;;
    *)
        build_all
        deploy
        ;;
esac
