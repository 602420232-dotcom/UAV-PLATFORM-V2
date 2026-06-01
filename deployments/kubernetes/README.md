# UAV平台 Kubernetes部署优化
# Kubernetes Deployment - Production-Ready Deployment Configuration

## 概述

本目录包含UAV平台的Kubernetes部署配置，已针对生产环境进行优化。

## 主要改进

### 1. ConfigMap 环境变量外化

- 所有通用环境变量已外化为 `configmap.yml`
- 各服务Deployment通过`envFrom`引用ConfigMap
- 避免在每个Deployment中重复定义
- 简化了配置管理和维护

### 2. 安全配置优化

所有服务都包含以下安全配置：
- 非Root用户运行 (`runAsNonRoot: true`)
- 禁止权限提升 (`allowPrivilegeEscalation: false`)
- 只读文件系统 (`readOnlyRootFilesystem: true`)
- 禁用所有Capability (`capabilities.drop: ["ALL"]`)
- Seccomp配置 (`RuntimeDefault`)
- 临时目录使用emptyDir挂载

### 3. 资源请求和限制

- 所有容器都配置了合理的requests和limits
- 根据服务特性调整资源配额
- 防止资源耗尽和服务质量保障

### 4. 健康检查和就绪探针

所有服务都包含：
- ReadinessProbe：就绪检查，用于流量调度
- LivenessProbe：存活检查，用于自动重启
- StartupProbe：启动检查，为应用启动提供更长的宽限期
- 适当的初始延迟、检查间隔和超时配置

### 5. 滚动更新策略

- 配置了合理的maxUnavailable和maxSurge
- 对于关键数据库服务使用StatefulSet而非Deployment
- 配置了minReadySeconds确保服务就绪后再接收流量
- 保留10个修订版本历史 (`revisionHistoryLimit`)

### 6. PodDisruptionBudget (PDB)

- 为关键服务配置了PDB
- 防止在维护期间服务不可用
- 对于有状态服务设置maxUnavailable: 0

### 7. 部署脚本优化

- 提供了Windows PowerShell版本部署脚本 `deploy.ps1`
- 提供部署验证脚本 `validate.ps1`
- 前置检查kubectl和集群连接性
- 分步部署和状态验证

## 快速开始

### 前置要求

1. Kubernetes集群 (v1.20+
2. kubectl配置正确
3. Ingress Controller (推荐Nginx)

### 部署步骤

1. 配置Secrets:
   ```powershell
   cd deployments/kubernetes
   cp secrets.example.yml secrets.yml
   # 编辑secrets.yml，填入真实密码 (Base64编码)
   ```

2. 部署:
   ```powershell
   .\deploy.ps1
   ```

3. 验证:
   ```powershell
   .\validate.ps1
   ```

### 本地开发 (Kind

使用Kind创建本地集群：
```powershell
# 如果在WSL2或Linux中运行
kind create cluster --config kind-config.yaml

# 或者使用Docker Desktop自带的Kubernetes
```

## 目录结构

```
deployments/kubernetes/
├── namespace.yml                  # 命名空间定义
├── configmap.yml                  # 应用配置
├── secrets.example.yml           # 示例Secrets配置示例
├── persistent-volumes.yml        # 持久卷声明
├── database-services.yml       # MySQL & Redis
├── api-gateway.yml           # API网关
├── uav-platform-service.yml  # 主平台服务
├── data-assimilation-service.yml
├── wrf-processor-service.yml
├── meteor-forecast-service.yml
├── path-planning-service.yml
├── uav-weather-collector.yml
├── fengwu-service.yml
├── edge-cloud-coordinator.yml
├── frontend-vue.yml
├── nginx-ingress.yml          # Ingress配置
├── hpa.yml                  # 水平自动扩展
├── monitoring.yml            # 监控配置
├── deploy.ps1                 # PowerShell部署脚本
├── validate.ps1              # 验证脚本
├── deploy.sh               # Bash部署脚本 (Linux/Mac
└── kind-config.yaml        # Kind本地集群配置
```

## 验证部署

主要功能验证部署后，可以通过以下方式验证：

1. 运行验证脚本：
```powershell
.\validate.ps1
```

2. 手动检查：
```powershell
kubectl get all -n uav-platform
kubectl get pods -n uav-platform -w
```

3. 查看日志：
```powershell
kubectl logs -n uav-platform <pod-name>
```

## 回滚

回滚到以前的版本：

```powershell
# 查看部署历史
kubectl rollout history deployment/<deployment-name> -n uav-platform

# 回滚到上一版本
kubectl rollout undo deployment/<deployment-name> -n uav-platform

# 回滚到特定版本
kubectl rollout undo deployment/<deployment-name> --to-revision=2 -n uav-platform
```

## 监控与扩展

### 水平扩展

可以使用水平Pod Autoscaler：

```powershell
# 查看HPA状态
kubectl get hpa -n uav-platform

# 手动扩缩容
kubectl scale deployment/<deployment-name> --replicas=3 -n uav-platform
```

### 资源监控

如果配置了资源请求和限制，监控资源使用：

```powershell
# 查看Pod资源使用
kubectl top pods -n uav-platform

# 查看节点资源使用
kubectl top nodes
```

## 故障排查

### 常见问题

1. **Pod启动失败
   - 检查日志：`kubectl describe pod <pod-name> -n uav-platform`
   - 检查事件：`kubectl get events -n uav-platform --sort-by='.lastTimestamp'`

2. **服务不可访问
   - 检查Service：`kubectl get svc -n uav-platform`
   - 检查Endpoints：`kubectl get endpoints <svc-name> -n uav-platform`
   - 检查Ingress：`kubectl get ingress -n uav-platform`

3. **ConfigMap或Secret问题
   - 检查是否正确创建：`kubectl get cm,secret -n uav-platform`
   - 验证内容：`kubectl describe cm uav-platform-config -n uav-platform`

## 生产环境注意事项

1. **存储：
   - 确保有状态服务使用StatefulSet
   - 使用存储类根据环境配置持久卷
   - 定期备份PVC数据

2. **安全：
   - 使用Secrets管理使用加密存储
   - 网络策略限制Pod间通信
   - 使用RBAC控制权限

3. **监控和告警：
   - 配置Prometheus和Grafana
   - 设置日志收集和告警规则
   - 启用日志聚合

4. **高可用性：
   - 多副本部署无状态服务
   - 使用PodDisruptionBudget
   - 节点亲和性和反亲和性
   - 多可用区分布

## 更新记录

- 2026-06-01: 初始生产优化版本
  - ConfigMap环境变量外化
  - 安全配置加固
  - 完善健康检查和探针
  - 优化资源配置
  - 添加滚动更新策略
  - PDB配置
  - 部署和验证脚本
