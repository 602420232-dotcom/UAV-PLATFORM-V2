# UAV Platform V2 - 发布操作手册 (Release Runbook)

> 版本: 2.0.0 | 最后更新: 2026-06-15 | 维护团队: UAV Platform Team

---

## 目录

1. [发布前检查清单](#1-发布前检查清单)
2. [发布步骤](#2-发布步骤)
3. [金丝雀发布流程](#3-金丝雀发布流程)
4. [回滚步骤](#4-回滚步骤)
5. [发布后验证](#5-发布后验证)
6. [常见问题与处理](#6-常见问题与处理)
7. [紧急联系](#7-紧急联系)

---

## 1. 发布前检查清单

### 1.1 代码与构建

| 序号 | 检查项 | 状态 | 备注 |
|------|--------|------|------|
| 1 | 所有单元测试通过 | [ ] | `mvn test` / `pytest` |
| 2 | 集成测试通过 | [ ] | CI/CD Pipeline 绿色 |
| 3 | E2E 测试通过 | [ ] | `python scripts/e2e-test.py` |
| 4 | 代码审查已完成 | [ ] | 至少 1 人 Approve |
| 5 | CHANGELOG.md 已更新 | [ ] | 记录变更内容 |
| 6 | 版本号已更新 | [ ] | pom.xml / pyproject.toml |
| 7 | 无未合并的 Hotfix | [ ] | 确认 main 分支干净 |

### 1.2 基础设施

| 序号 | 检查项 | 状态 | 备注 |
|------|--------|------|------|
| 8 | Kubernetes 集群健康 | [ ] | `kubectl get nodes` |
| 9 | Nginx Ingress Controller 正常 | [ ] | `kubectl get pods -n ingress-nginx` |
| 10 | Prometheus 正常运行 | [ ] | Grafana Dashboard 可访问 |
| 11 | GHCR 镜像仓库可访问 | [ ] | `docker pull` 权限正常 |
| 12 | ArgoCD 同步状态正常 | [ ] | `argocd app list` |
| 13 | 磁盘/内存资源充足 | [ ] | 集群资源余量 > 30% |

### 1.3 数据库与中间件

| 序号 | 检查项 | 状态 | 备注 |
|------|--------|------|------|
| 14 | 数据库迁移脚本已准备 | [ ] | Flyway/Liquibase |
| 15 | Redis 缓存策略已确认 | [ ] | 是否需要清缓存 |
| 16 | Kafka Topic 无积压 | [ ] | Consumer Lag 正常 |
| 17 | Nacos 配置已更新 | [ ] | 新版本所需配置 |

### 1.4 业务确认

| 序号 | 检查项 | 状态 | 备注 |
|------|--------|------|------|
| 18 | 产品负责人已确认发布窗口 | [ ] | 避开业务高峰期 |
| 19 | 通知相关团队 | [ ] | 运维、测试、产品 |
| 20 | 回滚方案已准备 | [ ] | 明确回滚步骤 |

---

## 2. 发布步骤

### 2.1 自动发布（推荐）

使用发布自动化脚本一键完成：

```powershell
# 发布单个服务
.\scripts\release.ps1 -Service api-gateway -Version "2.1.0"

# 发布所有服务
.\scripts\release.ps1 -All -Version "2.1.0"

# 跳过构建（使用已有镜像）
.\scripts\release.ps1 -Service api-gateway -Version "2.1.0" -SkipBuild
```

### 2.2 手动发布步骤

如需手动操作，按以下步骤执行：

#### Step 1: 构建并推送镜像

```bash
# Java 服务
docker build -f Dockerfile.jre \
  --build-arg SERVICE_NAME=api-gateway \
  --build-arg SERVICE_DIR=services/api-gateway \
  -t ghcr.io/602420232-dotcom/api-gateway:2.1.0 \
  -t ghcr.io/602420232-dotcom/api-gateway:canary \
  .

docker push ghcr.io/602420232-dotcom/api-gateway:2.1.0
docker push ghcr.io/602420232-dotcom/api-gateway:canary
```

#### Step 2: 更新 Helm Values

```bash
helm upgrade uav-platform ./helm/uav-platform \
  -f ./helm/uav-platform/values.yaml \
  -f ./helm/uav-platform/values-prod.yaml \
  --set apiGateway.image.tag=2.1.0 \
  --namespace uav-platform \
  --wait --timeout 300s
```

#### Step 3: 部署金丝雀

```bash
# 应用金丝雀资源
kubectl apply -f k8s/canary/canary-deployment.yaml -n uav-platform
kubectl apply -f k8s/canary/canary-service.yaml -n uav-platform
kubectl apply -f k8s/canary/canary-ingress.yaml -n uav-platform

# 等待金丝雀 Pod 就绪
kubectl rollout status deployment/api-gateway-canary -n uav-platform
```

#### Step 4: 验证金丝雀

```bash
# 检查金丝雀 Pod 状态
kubectl get pods -n uav-platform -l app.kubernetes.io/track=canary

# 使用 X-Canary 头测试金丝雀
curl -H "X-Canary: true" https://uav-platform.local/api/v1/health

# 查看金丝雀日志
kubectl logs -f deployment/api-gateway-canary -n uav-platform
```

---

## 3. 金丝雀发布流程

### 3.1 流量切分策略

```
Phase 1: 5% 流量   -> 等待 5 分钟  -> 检查指标
Phase 2: 25% 流量  -> 等待 10 分钟 -> 检查指标
Phase 3: 50% 流量  -> 等待 10 分钟 -> 检查指标
Phase 4: 100% 流量 -> 等待 5 分钟  -> 检查指标 -> 完成发布
```

### 3.2 手动调整流量权重

```bash
# 调整金丝雀 Ingress 权重
kubectl annotate ingress api-gateway-canary-ingress \
  -n uav-platform \
  "nginx.ingress.kubernetes.io/canary-weight=25" \
  --overwrite
```

### 3.3 请求头路由（测试用）

携带 `X-Canary: true` 请求头的流量将 100% 路由到金丝雀版本：

```bash
# 测试金丝雀版本
curl -H "X-Canary: true" https://uav-platform.local/api/v1/platform/tenants

# 测试稳定版本（不带 header）
curl https://uav-platform.local/api/v1/platform/tenants
```

### 3.4 自动回滚条件

| 指标 | 阈值 | 动作 |
|------|------|------|
| 错误率 (5xx) | > 5% | 自动回滚 |
| P99 延迟 | > 1000ms | 自动回滚 |
| Pod 健康检查 | 失败 3 次 | 自动回滚 |
| 容器重启 | > 2 次/5 分钟 | 告警 + 人工确认 |

### 3.5 手动推进金丝雀

```powershell
# 推进到下一阶段
.\scripts\release.ps1 -Promote -Service api-gateway

# 中止发布（回滚）
.\scripts\release.ps1 -Abort -Service api-gateway
```

---

## 4. 回滚步骤

### 4.1 回滚到上一个版本

```powershell
# PowerShell
.\scripts\rollback.ps1 -Service api-gateway

# Bash
./scripts/rollback.sh --service api-gateway
```

### 4.2 回滚到指定版本

```powershell
# 查看版本历史
kubectl rollout history deployment/api-gateway -n uav-platform

# 回滚到 revision 2
.\scripts\rollback.ps1 -Service api-gateway -Revision 2
```

### 4.3 批量回滚所有服务

```powershell
# 回滚所有服务到上一个版本
.\scripts\rollback.ps1 -All

# 自动回滚（无确认提示）
.\scripts\rollback.ps1 -All -Auto
```

### 4.4 金丝雀回滚

```powershell
# 删除所有金丝雀资源，100% 流量切回稳定版本
.\scripts\rollback.ps1 -Canary
```

### 4.5 回滚验证

```bash
# 1. 确认 Deployment 版本
kubectl get deployment api-gateway -n uav-platform -o jsonpath='{.spec.template.spec.containers[0].image}'

# 2. 确认 Pod 已更新
kubectl get pods -n uav-platform -l app.kubernetes.io/name=api-gateway

# 3. 确认 Rollout 状态
kubectl rollout status deployment/api-gateway -n uav-platform

# 4. 验证服务可用性
curl -sf https://uav-platform.local/api/v1/health
```

---

## 5. 发布后验证

### 5.1 服务健康检查

```bash
# 检查所有 Deployment 状态
kubectl get deployments -n uav-platform

# 检查所有 Pod 状态
kubectl get pods -n uav-platform

# 检查 HPA 状态
kubectl get hpa -n uav-platform

# 检查 Service 端点
kubectl get endpoints -n uav-platform
```

### 5.2 功能验证

| 序号 | 验证项 | 方法 | 状态 |
|------|--------|------|------|
| 1 | API Gateway 健康检查 | `GET /actuator/health` | [ ] |
| 2 | 用户认证/授权 | 登录 + Token 验证 | [ ] |
| 3 | 核心业务接口 | 主要 CRUD 操作 | [ ] |
| 4 | 算法引擎接口 | `GET /api/v1/algorithm/health` | [ ] |
| 5 | 前端页面加载 | Console 正常渲染 | [ ] |
| 6 | WebSocket 连接 | 实时数据推送 | [ ] |

### 5.3 性能验证

```bash
# 使用 E2E 测试验证
python scripts/e2e-test.py --mode live --base-url https://uav-platform.local

# 使用性能基准测试
python scripts/perf-benchmark.py --duration 60 --concurrency 10
```

### 5.4 监控指标确认

在 Grafana Dashboard 中确认以下指标：

- [ ] HTTP 请求成功率 > 99.5%
- [ ] P50 延迟 < 200ms
- [ ] P99 延迟 < 1000ms
- [ ] JVM 堆内存使用 < 80%
- [ ] 数据库连接池使用 < 70%
- [ ] Kafka Consumer Lag < 100
- [ ] Pod CPU/内存使用在 HPA 范围内

### 5.5 发布完成确认

```bash
# 确认 ArgoCD 同步状态
argocd app get uav-platform

# 确认无金丝雀资源残留
kubectl get all -n uav-platform -l app.kubernetes.io/track=canary

# 确认日志无异常
kubectl logs -l app.kubernetes.io/name=api-gateway -n uav-platform --tail=50 | grep -i error
```

---

## 6. 常见问题与处理

### 6.1 金丝雀 Pod 启动失败

**现象**: `kubectl get pods` 显示 CrashLoopBackOff

**排查步骤**:
```bash
# 查看 Pod 事件
kubectl describe pod <pod-name> -n uav-platform

# 查看容器日志
kubectl logs <pod-name> -n uav-platform --previous

# 检查镜像是否可拉取
kubectl get events -n uav-platform --field-selector type=Warning
```

**处理**: 修复问题后重新部署，或执行回滚。

### 6.2 金丝雀流量未生效

**现象**: 请求始终路由到稳定版本

**排查步骤**:
```bash
# 检查 Ingress 注解
kubectl get ingress api-gateway-canary-ingress -n uav-platform -o yaml

# 确认主 Ingress 存在
kubectl get ingress -n uav-platform

# 检查 Nginx Ingress Controller 日志
kubectl logs -l app.kubernetes.io/name=ingress-nginx -n ingress-nginx --tail=100
```

**注意**: Nginx Ingress Canary 要求主 Ingress 和金丝雀 Ingress 的 `host` 和 `path` 完全匹配。

### 6.3 Helm Upgrade 失败

**现象**: `helm upgrade` 超时或报错

**排查步骤**:
```bash
# 查看 Helm Release 状态
helm status uav-platform -n uav-platform

# 查看 Helm 历史
helm history uav-platform -n uav-platform

# 回滚 Helm Release
helm rollback uav-platform -n uav-platform
```

### 6.4 ArgoCD 同步失败

**现象**: ArgoCD 显示 OutOfSync 或 Degraded

**排查步骤**:
```bash
# 查看应用状态
argocd app get uav-platform

# 手动同步
argocd app sync uav-platform --prune

# 查看同步差异
argocd app diff uav-platform
```

### 6.5 发布后内存泄漏

**现象**: Pod 内存持续增长

**处理步骤**:
1. 立即检查 JVM Heap Dump: `kubectl exec <pod> -- jcmd 1 GC.heap_dump /tmp/heapdump.hprof`
2. 导出 Heap Dump: `kubectl cp <pod>:/tmp/heapdump.hprof ./heapdump.hprof`
3. 分析 Heap Dump 确认泄漏点
4. 如果无法快速修复，执行回滚

---

## 7. 紧急联系

| 角色 | 联系方式 | 职责 |
|------|----------|------|
| 发布负责人 | @release-oncall | 发布决策、回滚授权 |
| 运维团队 | @ops-team | 集群、基础设施问题 |
| DBA | @dba-team | 数据库相关回滚 |
| 产品负责人 | @product-owner | 业务影响评估 |

---

## 附录

### A. 服务端口映射

| 服务 | 容器端口 | Service 端口 |
|------|----------|-------------|
| api-gateway | 8088 | 8088 |
| platform-api | 8081 | 8081 |
| weather-api | 8082 | 8082 |
| assimilation-api | 8083 | 8083 |
| risk-api | 8084 | 8084 |
| observation-api | 8085 | 8085 |
| planning-api | 8086 | 8086 |
| utm-api | 8087 | 8087 |
| algorithm-engine | 9090 | 9090 |

### B. 镜像仓库地址

```
ghcr.io/602420232-dotcom/<service-name>:<tag>
```

### C. 相关文件路径

| 文件 | 用途 |
|------|------|
| `k8s/canary/canary-deployment.yaml` | 金丝雀 Deployment 配置 |
| `k8s/canary/canary-service.yaml` | 金丝雀 Service 配置 |
| `k8s/canary/canary-ingress.yaml` | 金丝雀 Ingress 配置 |
| `scripts/release.ps1` | 发布自动化脚本 |
| `scripts/rollback.ps1` | 回滚脚本 (PowerShell) |
| `scripts/rollback.sh` | 回滚脚本 (Bash) |
| `argocd/application.yaml` | ArgoCD Application 配置 |
| `argocd/app-of-apps.yaml` | ArgoCD ApplicationSet 配置 |
| `helm/uav-platform/values-prod.yaml` | 生产环境 Helm Values |
