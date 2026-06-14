#!/usr/bin/env bash
# =============================================================================
# UAV Platform V2 - Rollback Script (Bash)
# =============================================================================
# 用法:
#   ./rollback.sh                          # 回滚到上一个版本（交互确认）
#   ./rollback.sh --service api-gateway     # 回滚指定服务到上一个版本
#   ./rollback.sh --revision 2              # 回滚到指定版本
#   ./rollback.sh --all                     # 批量回滚所有服务
#   ./rollback.sh --auto                    # 自动回滚（无确认提示）
#   ./rollback.sh --canary                  # 回滚金丝雀发布（删除金丝雀资源）
# =============================================================================

set -euo pipefail

# ---- 配置 ----
NAMESPACE="uav-platform"
SERVICES=(
    "api-gateway"
    "platform-api"
    "weather-api"
    "assimilation-api"
    "risk-api"
    "observation-api"
    "planning-api"
    "utm-api"
    "algorithm-engine"
)

# ---- 颜色输出 ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*"; }

# ---- 参数解析 ----
TARGET_SERVICE=""
TARGET_REVISION=""
ROLLBACK_ALL=false
AUTO_CONFIRM=false
ROLLBACK_CANARY=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --service)
            TARGET_SERVICE="$2"
            shift 2
            ;;
        --revision)
            TARGET_REVISION="$2"
            shift 2
            ;;
        --all)
            ROLLBACK_ALL=true
            shift
            ;;
        --auto)
            AUTO_CONFIRM=true
            shift
            ;;
        --canary)
            ROLLBACK_CANARY=true
            shift
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -h|--help)
            echo "UAV Platform V2 Rollback Script"
            echo ""
            echo "用法:"
            echo "  $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --service <name>   回滚指定服务"
            echo "  --revision <num>   回滚到指定版本号"
            echo "  --all              批量回滚所有服务"
            echo "  --auto             跳过确认提示"
            echo "  --canary           回滚金丝雀发布（删除金丝雀资源）"
            echo "  --namespace <ns>    指定命名空间（默认: uav-platform）"
            echo "  -h, --help         显示帮助信息"
            exit 0
            ;;
        *)
            log_error "未知参数: $1"
            exit 1
            ;;
    esac
done

# ---- 前置检查 ----
check_prerequisites() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl 未安装，请先安装 Kubernetes CLI"
        exit 1
    fi

    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_error "命名空间 $NAMESPACE 不存在"
        exit 1
    fi

    log_info "命名空间: $NAMESPACE"
}

# ---- 健康检查 ----
wait_for_healthy() {
    local service="$1"
    local max_wait="${2:-120}"
    local elapsed=0

    log_info "等待 $service 健康检查通过（最长 ${max_wait}s）..."

    while [ $elapsed -lt $max_wait ]; do
        local ready_replicas
        ready_replicas=$(kubectl get deployment "$service" \
            -n "$NAMESPACE" \
            -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")

        local desired_replicas
        desired_replicas=$(kubectl get deployment "$service" \
            -n "$NAMESPACE" \
            -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")

        if [ "$ready_replicas" = "$desired_replicas" ] && [ "$ready_replicas" != "0" ]; then
            log_success "$service 健康检查通过 ($ready_replicas/$desired_replicas ready)"
            return 0
        fi

        sleep 5
        elapsed=$((elapsed + 5))
        echo -ne "\r  已等待 ${elapsed}s ($ready_replicas/$desired_replicas ready)..."
    done

    echo ""
    log_warn "$service 健康检查超时（${max_wait}s），请手动检查"
    return 1
}

# ---- 确认提示 ----
confirm_action() {
    local message="$1"
    if [ "$AUTO_CONFIRM" = true ]; then
        return 0
    fi
    echo -ne "${YELLOW}[确认]${NC} $message [y/N]: "
    read -r response
    case "$response" in
        [yY]|[yY][eE][sS]) return 0 ;;
        *) log_info "操作已取消"; exit 0 ;;
    esac
}

# ---- 获取部署版本历史 ----
show_revision_history() {
    local service="$1"
    log_info "$service 部署版本历史:"
    kubectl rollout history deployment/"$service" -n "$NAMESPACE" 2>/dev/null || true
    echo ""
}

# ---- 回滚单个服务 ----
rollback_service() {
    local service="$1"
    local revision="${2:-}"

    log_info "===== 回滚服务: $service ====="

    # 显示当前状态
    local current_image
    current_image=$(kubectl get deployment "$service" \
        -n "$NAMESPACE" \
        -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "unknown")
    log_info "当前镜像: $current_image"

    # 显示版本历史
    show_revision_history "$service"

    # 执行回滚
    if [ -n "$revision" ]; then
        log_info "回滚 $service 到版本 revision $revision ..."
        kubectl rollout undo deployment/"$service" \
            -n "$NAMESPACE" \
            --to-revision="$revision"
    else
        log_info "回滚 $service 到上一个版本 ..."
        kubectl rollout undo deployment/"$service" -n "$NAMESPACE"
    fi

    # 等待回滚完成
    log_info "等待回滚完成..."
    kubectl rollout status deployment/"$service" \
        -n "$NAMESPACE" \
        --timeout=180s

    # 健康检查
    wait_for_healthy "$service" 120

    # 验证回滚后镜像
    local new_image
    new_image=$(kubectl get deployment "$service" \
        -n "$NAMESPACE" \
        -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "unknown")
    log_info "回滚后镜像: $new_image"

    if [ "$current_image" != "$new_image" ]; then
        log_success "$service 回滚成功"
    else
        log_warn "$service 镜像未变化，请确认回滚是否生效"
    fi

    echo ""
}

# ---- 金丝雀回滚 ----
rollback_canary() {
    log_info "===== 回滚金丝雀发布 ====="

    confirm_action "确认删除所有金丝雀资源？这将把 100% 流量切回稳定版本"

    # 删除金丝雀 Ingress
    for ingress in $(kubectl get ingress -n "$NAMESPACE" \
        -l "app.kubernetes.io/track=canary" \
        -o jsonpath='{.items[*].metadata.name}' 2>/dev/null); do
        log_info "删除金丝雀 Ingress: $ingress"
        kubectl delete ingress "$ingress" -n "$NAMESPACE" --timeout=30s
    done

    # 删除金丝雀 Service
    for svc in $(kubectl get svc -n "$NAMESPACE" \
        -l "app.kubernetes.io/track=canary" \
        -o jsonpath='{.items[*].metadata.name}' 2>/dev/null); do
        log_info "删除金丝雀 Service: $svc"
        kubectl delete svc "$svc" -n "$NAMESPACE" --timeout=30s
    done

    # 删除金丝雀 Deployment
    for deploy in $(kubectl get deployment -n "$NAMESPACE" \
        -l "app.kubernetes.io/track=canary" \
        -o jsonpath='{.items[*].metadata.name}' 2>/dev/null); do
        log_info "删除金丝雀 Deployment: $deploy"
        kubectl delete deployment "$deploy" -n "$NAMESPACE" --timeout=60s
    done

    log_success "金丝雀资源已全部删除，流量已切回稳定版本"
}

# ---- 批量回滚 ----
rollback_all_services() {
    log_info "===== 批量回滚所有服务 ====="

    confirm_action "确认回滚所有 ${#SERVICES[@]} 个服务？"

    local failed=()
    for service in "${SERVICES[@]}"; do
        if kubectl get deployment "$service" -n "$NAMESPACE" &> /dev/null; then
            if ! rollback_service "$service" "$TARGET_REVISION"; then
                failed+=("$service")
            fi
        else
            log_warn "服务 $service 不存在，跳过"
        fi
    done

    echo ""
    log_info "===== 回滚结果汇总 ====="
    if [ ${#failed[@]} -eq 0 ]; then
        log_success "所有服务回滚成功"
    else
        log_error "以下服务回滚失败: ${failed[*]}"
        exit 1
    fi
}

# ---- 主流程 ----
main() {
    echo "============================================"
    echo "  UAV Platform V2 - 回滚工具"
    echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "============================================"
    echo ""

    check_prerequisites

    if [ "$ROLLBACK_CANARY" = true ]; then
        rollback_canary
    elif [ "$ROLLBACK_ALL" = true ]; then
        rollback_all_services
    elif [ -n "$TARGET_SERVICE" ]; then
        confirm_action "确认回滚服务 $TARGET_SERVICE？"
        rollback_service "$TARGET_SERVICE" "$TARGET_REVISION"
    else
        log_error "请指定回滚目标: --service <name> | --all | --canary"
        echo "使用 $0 --help 查看帮助信息"
        exit 1
    fi
}

main "$@"
