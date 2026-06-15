#!/bin/bash
# ============================================================
# UAV Platform V2 - 混沌测试自动化脚本
# 功能：执行故障注入、监控服务恢复时间、生成混沌测试报告
# 使用方式：./chaos-test.sh [experiment_name] [duration]
# ============================================================

set -euo pipefail

# ---------------------------
# 配置变量
# ---------------------------
NAMESPACE="uav-platform"
CHAOS_NAMESPACE="uav-platform"
REPORT_DIR="./chaos-reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${REPORT_DIR}/chaos-report-${TIMESTAMP}.md"
DURATION="${2:-600}"  # 默认实验时长 10 分钟
EXPERIMENT_NAME="${1:-all}"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ---------------------------
# 工具函数
# ---------------------------

log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖工具..."
    
    local deps=("kubectl" "curl" "jq" "date")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "缺少依赖: $dep，请先安装"
            exit 1
        fi
    done
    
    # 检查 Chaos Mesh CLI (optional)
    if command -v "chaosctl" &> /dev/null; then
        log_info "Chaos Mesh CLI (chaosctl) 已安装"
        HAS_CHAOSCTL=true
    else
        log_warn "Chaos Mesh CLI (chaosctl) 未安装，将使用 kubectl 直接操作"
        HAS_CHAOSCTL=false
    fi
    
    log_success "依赖检查通过"
}

# 检查集群连接
check_cluster() {
    log_info "检查 Kubernetes 集群连接..."
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "无法连接到 Kubernetes 集群"
        exit 1
    fi
    
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_error "命名空间 $NAMESPACE 不存在"
        exit 1
    fi
    
    log_success "集群连接正常，命名空间 $NAMESPACE 存在"
}

# 获取服务基线指标
get_baseline_metrics() {
    log_info "获取服务基线指标..."
    
    BASELINE_PODS=$(kubectl get pods -n "$NAMESPACE" --no-headers | wc -l)
    BASELINE_READY=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Running --no-headers | wc -l)
    
    log_info "基线状态: 总 Pod 数=$BASELINE_PODS, 就绪 Pod 数=$BASELINE_READY"
    
    # 尝试获取 Prometheus 指标
    if kubectl get svc -n monitoring prometheus &> /dev/null; then
        PROMETHEUS_URL="http://prometheus.monitoring.svc.cluster.local:9090"
        log_info "Prometheus 监控已检测到"
        HAS_PROMETHEUS=true
    else
        log_warn "Prometheus 监控未检测到，将使用基础 kubectl 指标"
        HAS_PROMETHEUS=false
    fi
}

# 执行混沌实验
run_experiment() {
    local experiment=$1
    local duration=$2
    
    log_info "启动混沌实验: $experiment (时长: ${duration}s)"
    
    local start_time=$(date +%s)
    
    case "$experiment" in
        "pod-failure")
            run_pod_failure_experiment "$duration"
            ;;
        "network-delay")
            run_network_delay_experiment "$duration"
            ;;
        "network-partition")
            run_network_partition_experiment "$duration"
            ;;
        "cpu-stress")
            run_cpu_stress_experiment "$duration"
            ;;
        "memory-stress")
            run_memory_stress_experiment "$duration"
            ;;
        "cascading")
            run_cascading_experiment "$duration"
            ;;
        *)
            log_error "未知实验类型: $experiment"
            return 1
            ;;
    esac
    
    local end_time=$(date +%s)
    local actual_duration=$((end_time - start_time))
    
    log_info "实验 $experiment 执行完成，实际耗时: ${actual_duration}s"
    
    # 记录实验结果
    echo "- 实验: $experiment" >> "$REPORT_FILE"
    echo "  - 计划时长: ${duration}s" >> "$REPORT_FILE"
    echo "  - 实际时长: ${actual_duration}s" >> "$REPORT_FILE"
}

# Pod 故障实验
run_pod_failure_experiment() {
    local duration=$1
    
    log_info "执行 Pod 故障注入..."
    
    # 随机选择一个 Pod
    local target_pod=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/part-of=uav-platform --no-headers | awk '{print $1}' | shuf -n 1)
    
    if [ -z "$target_pod" ]; then
        log_error "未找到目标 Pod"
        return 1
    fi
    
    log_info "目标 Pod: $target_pod"
    
    # 删除 Pod 模拟故障
    kubectl delete pod "$target_pod" -n "$NAMESPACE" --grace-period=0 --force 2>/dev/null || true
    
    # 监控恢复
    monitor_recovery "$duration" "$target_pod"
}

# 网络延迟实验
run_network_delay_experiment() {
    local duration=$1
    
    log_info "执行网络延迟注入 (100ms)..."
    
    # 使用 Chaos Mesh 创建网络延迟实验
    cat <<EOF | kubectl apply -f -
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: network-delay-test
  namespace: $CHAOS_NAMESPACE
spec:
  action: delay
  mode: all
  selector:
    namespaces:
      - $NAMESPACE
    labelSelectors:
      app.kubernetes.io/part-of: uav-platform
  delay:
    latency: 100ms
    correlation: "50"
    jitter: 20ms
  duration: ${duration}s
EOF
    
    # 等待实验完成
    sleep "$duration"
    
    # 清理实验
    kubectl delete networkchaos network-delay-test -n "$CHAOS_NAMESPACE" 2>/dev/null || true
    
    monitor_recovery 60
}

# 网络分区实验
run_network_partition_experiment() {
    local duration=$1
    
    log_info "执行网络分区实验..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: network-partition-test
  namespace: $CHAOS_NAMESPACE
spec:
  action: partition
  mode: all
  selector:
    namespaces:
      - $NAMESPACE
    labelSelectors:
      app: platform-api
  direction: both
  target:
    mode: all
    selector:
      namespaces:
        - $NAMESPACE
      labelSelectors:
        app: weather-api
  duration: ${duration}s
EOF
    
    sleep "$duration"
    kubectl delete networkchaos network-partition-test -n "$CHAOS_NAMESPACE" 2>/dev/null || true
    
    monitor_recovery 60
}

# CPU 压力实验
run_cpu_stress_experiment() {
    local duration=$1
    
    log_info "执行 CPU 压力实验 (80% 负载)..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: cpu-stress-test
  namespace: $CHAOS_NAMESPACE
spec:
  stressors:
    cpu:
      workers: 4
      load: 80
  mode: one
  selector:
    namespaces:
      - $NAMESPACE
    labelSelectors:
      app.kubernetes.io/part-of: uav-platform
  duration: ${duration}s
EOF
    
    sleep "$duration"
    kubectl delete stresschaos cpu-stress-test -n "$CHAOS_NAMESPACE" 2>/dev/null || true
    
    monitor_recovery 60
}

# 内存压力实验
run_memory_stress_experiment() {
    local duration=$1
    
    log_info "执行内存压力实验 (80% 负载)..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: memory-stress-test
  namespace: $CHAOS_NAMESPACE
spec:
  stressors:
    memory:
      workers: 2
      size: 80%
  mode: one
  selector:
    namespaces:
      - $NAMESPACE
    labelSelectors:
      app.kubernetes.io/part-of: uav-platform
  duration: ${duration}s
EOF
    
    sleep "$duration"
    kubectl delete stresschaos memory-stress-test -n "$CHAOS_NAMESPACE" 2>/dev/null || true
    
    monitor_recovery 60
}

# 级联故障实验
run_cascading_experiment() {
    local duration=$1
    
    log_info "执行级联故障实验..."
    
    # 步骤 1: 网络延迟
    log_info "级联步骤 1/3: 注入网络延迟"
    cat <<EOF | kubectl apply -f -
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: cascading-delay
  namespace: $CHAOS_NAMESPACE
spec:
  action: delay
  mode: all
  selector:
    namespaces:
      - $NAMESPACE
    labelSelectors:
      app: api-gateway
  delay:
    latency: 500ms
  duration: ${duration}s
EOF
    
    sleep 30
    
    # 步骤 2: Pod 故障
    log_info "级联步骤 2/3: 注入 Pod 故障"
    local target_pod=$(kubectl get pods -n "$NAMESPACE" -l app=weather-api --no-headers | awk '{print $1}' | shuf -n 1)
    kubectl delete pod "$target_pod" -n "$NAMESPACE" --grace-period=0 --force 2>/dev/null || true
    
    sleep 30
    
    # 步骤 3: CPU 压力
    log_info "级联步骤 3/3: 注入 CPU 压力"
    cat <<EOF | kubectl apply -f -
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: cascading-cpu
  namespace: $CHAOS_NAMESPACE
spec:
  stressors:
    cpu:
      workers: 4
      load: 90
  mode: one
  selector:
    namespaces:
      - $NAMESPACE
    labelSelectors:
      app: assimilation-api
  duration: ${duration}s
EOF
    
    sleep "$duration"
    
    # 清理所有级联实验
    kubectl delete networkchaos cascading-delay -n "$CHAOS_NAMESPACE" 2>/dev/null || true
    kubectl delete stresschaos cascading-cpu -n "$CHAOS_NAMESPACE" 2>/dev/null || true
    
    monitor_recovery 120
}

# 监控服务恢复
monitor_recovery() {
    local timeout=$1
    local target_pod=${2:-}
    local start_time=$(date +%s)
    
    log_info "监控服务恢复 (超时: ${timeout}s)..."
    
    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if [ "$elapsed" -ge "$timeout" ]; then
            log_warn "恢复监控超时"
            echo "  - 恢复状态: 超时" >> "$REPORT_FILE"
            echo "  - 恢复时间: >${timeout}s" >> "$REPORT_FILE"
            return 1
        fi
        
        # 检查 Pod 状态
        local ready_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Running --no-headers | wc -l)
        local total_pods=$(kubectl get pods -n "$NAMESPACE" --no-headers | wc -l)
        
        if [ "$ready_pods" -eq "$total_pods" ] && [ "$ready_pods" -ge "$BASELINE_READY" ]; then
            local recovery_time=$((current_time - start_time))
            log_success "服务已恢复! 恢复时间: ${recovery_time}s"
            echo "  - 恢复状态: 成功" >> "$REPORT_FILE"
            echo "  - 恢复时间: ${recovery_time}s" >> "$REPORT_FILE"
            return 0
        fi
        
        log_info "恢复中... 就绪 Pod: $ready_pods / $total_pods (目标: $BASELINE_READY)"
        sleep 5
    done
}

# 生成测试报告头部
generate_report_header() {
    mkdir -p "$REPORT_DIR"
    
    cat > "$REPORT_FILE" <<EOF
# UAV Platform V2 混沌测试报告

## 测试概览

| 项目 | 值 |
|------|-----|
| 测试时间 | $(date '+%Y-%m-%d %H:%M:%S') |
| 命名空间 | $NAMESPACE |
| 实验名称 | $EXPERIMENT_NAME |
| 计划时长 | ${DURATION}s |
| 基线 Pod 数 | $BASELINE_PODS |
| 基线就绪 Pod 数 | $BASELINE_READY |

## 实验结果

EOF
}

# 生成测试报告尾部
generate_report_footer() {
    local end_time=$(date +%s)
    local total_duration=$((end_time - START_TIME))
    
    cat >> "$REPORT_FILE" <<EOF

## 测试总结

| 指标 | 值 |
|------|-----|
| 总测试时长 | ${total_duration}s |
| 测试完成时间 | $(date '+%Y-%m-%d %H:%M:%S') |

## 建议

1. 根据恢复时间评估服务弹性
2. 检查错误日志和监控告警
3. 优化自动恢复机制
4. 更新混沌工程实验配置

---
*报告由 chaos-test.sh 自动生成*
EOF
    
    log_success "测试报告已生成: $REPORT_FILE"
}

# 获取当前 Pod 状态
get_pod_status() {
    log_info "当前 Pod 状态:"
    kubectl get pods -n "$NAMESPACE" -o wide
}

# 清理所有混沌实验资源
cleanup() {
    log_info "清理混沌实验资源..."
    
    kubectl delete podchaos --all -n "$CHAOS_NAMESPACE" 2>/dev/null || true
    kubectl delete networkchaos --all -n "$CHAOS_NAMESPACE" 2>/dev/null || true
    kubectl delete stresschaos --all -n "$CHAOS_NAMESPACE" 2>/dev/null || true
    kubectl delete iochaos --all -n "$CHAOS_NAMESPACE" 2>/dev/null || true
    kubectl delete timechaos --all -n "$CHAOS_NAMESPACE" 2>/dev/null || true
    kubectl delete jvmchaos --all -n "$CHAOS_NAMESPACE" 2>/dev/null || true
    kubectl delete httpchaos --all -n "$CHAOS_NAMESPACE" 2>/dev/null || true
    
    log_success "混沌实验资源已清理"
}

# 显示帮助信息
show_help() {
    cat <<EOF
UAV Platform V2 混沌测试脚本

使用方法:
  ./chaos-test.sh [experiment_name] [duration]

参数:
  experiment_name   实验名称 (默认: all)
  duration          实验时长（秒，默认: 600）

支持的实验:
  pod-failure       Pod 故障注入（随机删除 Pod）
  network-delay     网络延迟注入（100ms）
  network-partition 网络分区（隔离服务间通信）
  cpu-stress        CPU 压力（80% 负载）
  memory-stress     内存压力（80% 负载）
  cascading         级联故障（组合实验）
  all               顺序执行所有实验

示例:
  ./chaos-test.sh pod-failure 300
  ./chaos-test.sh network-delay 180
  ./chaos-test.sh all 600

环境变量:
  NAMESPACE         目标命名空间 (默认: uav-platform)
  REPORT_DIR        报告输出目录 (默认: ./chaos-reports)

EOF
}

# ---------------------------
# 主函数
# ---------------------------

main() {
    # 解析参数
    if [ "$EXPERIMENT_NAME" = "help" ] || [ "$EXPERIMENT_NAME" = "--help" ] || [ "$EXPERIMENT_NAME" = "-h" ]; then
        show_help
        exit 0
    fi
    
    START_TIME=$(date +%s)
    
    log_info "UAV Platform V2 混沌测试启动"
    log_info "实验: $EXPERIMENT_NAME, 时长: ${DURATION}s"
    
    # 检查依赖和集群
    check_dependencies
    check_cluster
    
    # 获取基线指标
    get_baseline_metrics
    
    # 生成报告头部
    generate_report_header
    
    # 执行实验
    if [ "$EXPERIMENT_NAME" = "all" ]; then
        log_info "顺序执行所有混沌实验..."
        run_experiment "pod-failure" "$DURATION"
        run_experiment "network-delay" "$DURATION"
        run_experiment "network-partition" "$DURATION"
        run_experiment "cpu-stress" "$DURATION"
        run_experiment "memory-stress" "$DURATION"
        run_experiment "cascading" "$DURATION"
    else
        run_experiment "$EXPERIMENT_NAME" "$DURATION"
    fi
    
    # 获取最终状态
    get_pod_status
    
    # 生成报告尾部
    generate_report_footer
    
    # 清理资源
    cleanup
    
    log_success "混沌测试完成!"
    log_info "报告文件: $REPORT_FILE"
}

# 注册退出处理函数
trap cleanup EXIT

# 运行主函数
main "$@"
