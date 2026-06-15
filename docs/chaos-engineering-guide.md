# UAV Platform V2 混沌工程指南

## 目录

1. [混沌工程原则](#混沌工程原则)
2. [实验设计方法](#实验设计方法)
3. [安全边界定义](#安全边界定义)
4. [回滚策略](#回滚策略)
5. [实验类型详解](#实验类型详解)
6. [执行流程](#执行流程)
7. [监控与告警](#监控与告警)
8. [最佳实践](#最佳实践)

---

## 混沌工程原则

### 1.1 核心原则

混沌工程是在生产环境或准生产环境中，通过**有控制地注入故障**来验证系统弹性的工程学科。其核心原则包括：

| 原则 | 说明 |
|------|------|
| **建立稳态假设** | 定义系统在正常情况下的行为指标（如响应时间、错误率、吞吐量） |
| **引入真实变量** | 注入真实的故障事件（Pod 崩溃、网络延迟、资源耗尽） |
| **验证假设** | 观察系统在故障下的行为，验证是否符合预期 |
| **持续自动化** | 将混沌实验集成到 CI/CD 流程中，持续验证系统弹性 |
| **最小化影响范围** | 控制故障影响范围，避免对真实业务造成不可逆损害 |

### 1.2 UAV Platform 混沌工程目标

- **验证服务自愈能力**：当 Pod 故障时，系统能否自动恢复
- **验证降级策略**：当依赖服务不可用时，系统能否优雅降级
- **验证熔断机制**：当服务延迟增加时，熔断器是否正常工作
- **验证资源限制**：当 CPU/内存压力增大时，系统是否稳定运行
- **验证网络韧性**：当网络分区或延迟发生时，服务间通信是否可靠

---

## 实验设计方法

### 2.1 实验设计流程

```
定义稳态假设 -> 选择实验变量 -> 确定影响范围 -> 执行实验 -> 分析结果 -> 优化系统
```

### 2.2 稳态指标定义

UAV Platform 的关键稳态指标：

| 指标 | 基线值 | 可接受阈值 | 监控方式 |
|------|--------|-----------|----------|
| API 响应时间 (P50) | < 200ms | < 500ms | Prometheus + Grafana |
| API 响应时间 (P99) | < 500ms | < 2000ms | Prometheus + Grafana |
| 错误率 | < 0.1% | < 1% | Prometheus Alertmanager |
| Pod 就绪率 | 100% | >= 95% | Kubernetes Metrics |
| 服务间调用成功率 | > 99.9% | > 99% | Distributed Tracing |
| 数据库连接池使用率 | < 50% | < 80% | Database Monitoring |

### 2.3 实验变量选择矩阵

| 故障类型 | 目标服务 | 影响范围 | 预期行为 | 验证点 |
|----------|----------|----------|----------|--------|
| Pod 故障 | platform-api | 单个实例 | 自动重启，流量切换 | 自愈能力、负载均衡 |
| 网络延迟 | api-gateway | 全部实例 | 请求超时触发熔断 | 熔断器、重试策略 |
| 网络分区 | platform-api <-> weather-api | 服务间通信 | 服务隔离，降级响应 | 服务发现、降级策略 |
| CPU 压力 | assimilation-api | 单个实例 | 水平扩容触发 | HPA、资源限制 |
| 内存压力 | planning-api | 单个实例 | OOMKilled，自动恢复 | 内存限制、优雅关闭 |
| 级联故障 | 多服务组合 | 多个服务 | 故障隔离，避免雪崩 | 熔断、限流、隔离 |

### 2.4 实验时间窗口

- **开发环境**：随时可执行，用于快速验证
- **测试环境**：工作日 10:00-12:00 或 14:00-16:00
- **预发布环境**：每周二、四 20:00-22:00（低流量时段）
- **生产环境**：每月一次，安排在凌晨 02:00-04:00（需提前通知）

---

## 安全边界定义

### 3.1 自动终止条件

当以下任一条件触发时，必须**立即停止实验**：

1. **错误率超过阈值**：HTTP 5xx 错误率 > 10% 持续 2 分钟
2. **延迟超过阈值**：P99 延迟 > 5 秒 持续 2 分钟
3. **Pod 崩溃循环**：Pod 重启频率 > 0.1 次/分钟 持续 3 分钟
4. **数据库连接耗尽**：连接池使用率 > 95% 持续 1 分钟
5. **消息队列堆积**：Kafka 消费延迟 > 5 分钟
6. **人工干预**：值班工程师通过告警通道手动终止

### 3.2 影响范围控制

- **Pod 故障**：每次最多影响 1 个 Pod，不超过总 Pod 数的 20%
- **网络延迟**：延迟不超过 500ms，不超过实验时长的 30%
- **CPU 压力**：负载不超过 90%，Worker 数不超过 CPU 核心数
- **内存压力**：占用不超过 90%，预留 10% 安全缓冲
- **网络分区**：仅影响非关键路径服务，避免隔离数据库

### 3.3 权限控制

- **生产环境**：仅 SRE 团队可执行，需双人审批
- **预发布环境**：开发团队负责人可执行，需提前报备
- **测试/开发环境**：开发团队自由执行

---

## 回滚策略

### 4.1 自动回滚机制

```yaml
# 安全边界检查配置
safety_boundary:
  error_rate_threshold: 0.10      # 10% 错误率阈值
  latency_p99_threshold: 5000     # 5 秒 P99 延迟阈值
  pod_restart_threshold: 0.1      # 0.1 次/分钟重启阈值
  auto_rollback: true             # 启用自动回滚
  rollback_timeout: 30            # 30 秒内完成回滚
```

### 4.2 手动回滚步骤

当自动回滚失效或需要紧急干预时：

```bash
# 1. 立即停止所有混沌实验
kubectl delete podchaos,networkchaos,stresschaos,iochaos,timechaos,jvmchaos,httpchaos --all -n uav-platform

# 2. 检查服务状态
kubectl get pods -n uav-platform

# 3. 强制重启异常 Pod
kubectl rollout restart deployment/<deployment-name> -n uav-platform

# 4. 检查服务恢复
kubectl rollout status deployment/<deployment-name> -n uav-platform

# 5. 验证业务指标
curl -s http://api-gateway.uav-platform.svc.cluster.local:8080/actuator/health
```

### 4.3 回滚验证清单

- [ ] 所有 Pod 处于 Running 状态
- [ ] 服务健康检查端点返回 200
- [ ] 错误率恢复到基线水平 (< 0.1%)
- [ ] P99 延迟恢复到基线水平 (< 500ms)
- [ ] 关键业务流程端到端测试通过
- [ ] 监控告警全部清除

---

## 实验类型详解

### 5.1 Pod 故障注入

**目的**：验证 Kubernetes 的自愈能力和服务的无状态设计

**配置**：
```yaml
action: pod-failure
mode: one
duration: 2m
```

**预期结果**：
- Pod 被删除后，ReplicaSet 自动创建新 Pod
- 服务在 30 秒内恢复就绪
- 负载均衡器自动将流量切换到健康实例

### 5.2 网络延迟注入

**目的**：验证超时配置、重试策略和熔断器

**配置**：
```yaml
action: delay
latency: 100ms
correlation: 50
jitter: 20ms
```

**预期结果**：
- 客户端请求超时后触发重试
- 重试失败后触发熔断器打开
- 熔断器打开后返回降级响应

### 5.3 网络分区

**目的**：验证服务发现和降级策略

**配置**：
```yaml
action: partition
direction: both
target:
  selector:
    app: weather-api
```

**预期结果**：
- 被隔离服务无法访问目标服务
- 系统返回缓存数据或默认值
- 服务网格（如 Istio）正确标记服务不可用

### 5.4 CPU 压力

**目的**：验证 HPA 自动扩容和资源限制

**配置**：
```yaml
stressors:
  cpu:
    workers: 4
    load: 80
```

**预期结果**：
- CPU 使用率上升触发 HPA 扩容
- 新 Pod 创建后负载均衡
- 资源限制防止单个 Pod 耗尽节点资源

### 5.5 内存压力

**目的**：验证内存限制和优雅关闭

**配置**：
```yaml
stressors:
  memory:
    workers: 2
    size: 80%
```

**预期结果**：
- 内存使用达到限制后触发 OOMKilled
- Kubernetes 自动重启 Pod
- 应用优雅关闭，不丢失正在处理的数据

### 5.6 级联故障

**目的**：验证故障隔离和防止雪崩效应

**配置**：
```yaml
type: Serial
children:
  - network-delay (api-gateway)
  - pod-kill (weather-api)
  - cpu-stress (assimilation-api)
```

**预期结果**：
- 单个服务故障不影响其他服务
- 熔断器防止故障扩散
- 系统整体可用性保持在 95% 以上

---

## 执行流程

### 6.1 实验前准备

1. **确认基线指标**：记录当前系统的稳态指标
2. **通知相关团队**：在 Slack/钉钉群发送实验通知
3. **检查监控告警**：确认告警通道正常
4. **准备回滚脚本**：确保回滚命令可快速执行
5. **确认实验窗口**：确认在允许的时间窗口内执行

### 6.2 实验执行步骤

```bash
# 1. 执行混沌测试脚本
./scripts/chaos-test.sh all 600

# 2. 实时监控指标
kubectl top pods -n uav-platform
watch -n 5 'kubectl get pods -n uav-platform'

# 3. 观察 Grafana 仪表板
# 打开 http://grafana.uav-platform.svc.cluster.local

# 4. 检查日志
kubectl logs -f deployment/api-gateway -n uav-platform
```

### 6.3 实验后分析

1. **收集实验数据**：从 Prometheus 导出实验期间的指标
2. **对比基线指标**：分析故障期间指标变化
3. **识别薄弱环节**：找出未通过验证的假设
4. **制定改进计划**：针对发现的问题制定优化方案
5. **更新实验配置**：根据分析结果调整实验参数

---

## 监控与告警

### 7.1 关键监控指标

| 指标 | 查询语句 (PromQL) | 告警阈值 |
|------|-------------------|----------|
| HTTP 错误率 | `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))` | > 10% |
| P99 延迟 | `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))` | > 5s |
| Pod 重启率 | `rate(kube_pod_container_status_restarts_total[10m])` | > 0.1 |
| CPU 使用率 | `sum(rate(container_cpu_usage_seconds_total[5m])) by (pod) / sum(container_spec_cpu_quota) by (pod)` | > 90% |
| 内存使用率 | `sum(container_memory_working_set_bytes) by (pod) / sum(container_spec_memory_limit_bytes) by (pod)` | > 90% |

### 7.2 告警通道

- **P0 (Critical)**：电话 + 短信 + 钉钉
- **P1 (Warning)**：钉钉 + 邮件
- **P2 (Info)**：钉钉群消息

### 7.3 实验期间值班

- 生产环境实验期间，SRE 团队必须有人值班
- 值班人员需保持钉钉/电话畅通
- 实验开始前 15 分钟在值班群发送通知

---

## 最佳实践

### 8.1 实验频率建议

| 环境 | 频率 | 说明 |
|------|------|------|
| 开发 | 每次代码提交后 | 快速验证 |
| 测试 | 每天一次 | 持续验证 |
| 预发布 | 每周两次 | 回归验证 |
| 生产 | 每月一次 | 真实环境验证 |

### 8.2 实验记录模板

每次实验后需记录：

```markdown
## 实验记录

- **实验日期**: 2026-06-15
- **实验类型**: Pod 故障注入
- **目标服务**: platform-api
- **实验时长**: 10 分钟
- **执行人**: SRE 团队

### 基线指标
- Pod 数: 3
- P50 延迟: 120ms
- P99 延迟: 350ms
- 错误率: 0.01%

### 实验结果
- 故障注入时间: 10:00:00
- Pod 恢复时间: 10:00:45 (45秒)
- 最大错误率: 0.5%
- 最大 P99 延迟: 800ms

### 发现的问题
- [ ] 无问题
- [x] 恢复时间略长（目标 < 30s）

### 改进措施
- 优化 readiness probe 检测间隔
- 增加 preStop hook 优雅关闭时间

### 验证状态
- [x] 已验证通过
- [ ] 需重新验证
```

### 8.3 常见陷阱

1. **不要在高峰期执行生产实验**：选择流量低谷时段
2. **不要同时注入过多故障**：一次只验证一个假设
3. **不要忽略监控告警**：实验期间告警必须有人响应
4. **不要忘记清理资源**：实验后清理所有 Chaos 资源
5. **不要跳过实验后分析**：每次实验都必须有结论

### 8.4 工具链

| 工具 | 用途 | 版本 |
|------|------|------|
| Chaos Mesh | 故障注入引擎 | v2.6+ |
| Prometheus | 指标采集 | v2.45+ |
| Grafana | 可视化监控 | v10.0+ |
| Alertmanager | 告警管理 | v0.25+ |
| kubectl | K8s 操作 | v1.28+ |

---

## 附录

### A. 快速参考命令

```bash
# 查看所有混沌实验
kubectl get podchaos,networkchaos,stresschaos -n uav-platform

# 查看实验详情
kubectl describe podchaos <name> -n uav-platform

# 删除所有实验
kubectl delete podchaos,networkchaos,stresschaos,iochaos,timechaos,jvmchaos,httpchaos --all -n uav-platform

# 查看 Pod 事件
kubectl get events -n uav-platform --sort-by='.lastTimestamp'

# 查看 HPA 状态
kubectl get hpa -n uav-platform
```

### B. 相关文档

- [Chaos Mesh 官方文档](https://chaos-mesh.org/docs/)
- [UAV Platform 部署指南](./deployment-guide.md)
- [UAV Platform 运维手册](./operations-runbook.md)
- [UAV Platform 性能基准报告](./performance-benchmark-report.md)

---

*文档版本: v1.0*
*更新日期: 2026-06-15*
*维护团队: UAV Platform SRE*
