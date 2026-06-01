# JVM 参数配置统一报告

**日期**: 2026-05-31  
**审计任务**: M1 - JVM 参数不一致  
**状态**: ✅ 已完成

---

## 📋 任务背景

### 审计发现
- **文件**: `docker-compose.yml` vs 各 `Dockerfile` vs K8s Deployment
- **问题**: 
  - docker-compose 设置 `JAVA_OPTS=-Xms512m -Xmx1g` (1GB 堆)
  - Dockerfile ENV 默认 `JAVA_OPTS=-Xms256m -Xmx512m` (512MB 堆)
  - K8s Deployment 没有设置 JAVA_OPTS，使用 Dockerfile 默认值
- **影响**: K8s 中 Java 服务可能使用 512MB 而不是 1GB 堆 → OOM风险

---

## ✅ 完成的工作

### 1. **统一 JVM 参数配置**

为所有 K8s Deployment 添加了 `JAVA_OPTS` 环境变量，与 docker-compose 保持一致：

| 服务 | JVM 参数 | 堆内存 | 说明 |
|------|----------|--------|------|
| **api-gateway** | `-Xms256m -Xmx512m` | 512MB | 高并发入口 |
| **uav-platform** | `-Xms512m -Xmx1g` | 1GB | 主平台服务 |
| **wrf-processor** | `-Xms512m -Xmx1g` | 1GB | 气象数据处理 |
| **meteor-forecast** | `-Xms512m -Xmx1g` | 1GB | 气象预测服务 |
| **path-planning** | `-Xms512m -Xmx1g` | 1GB | 路径规划服务 |
| **data-assimilation** | `-Xms512m -Xmx1g` | 1GB | 数据同化服务 |
| **uav-weather-collector** | `-Xms256m -Xmx512m` | 512MB | 气象采集服务 |
| **backend-spring** | `-Xms512m -Xmx1g` | 1GB | 后端服务 |

### 2. **优化参数说明**

所有服务都使用以下 JVM 优化参数：

```bash
# 通用参数
-Xms512m              # 初始堆大小
-Xmx1g                # 最大堆大小
-XX:+UseG1GC         # G1垃圾收集器
-XX:MaxGCPauseMillis=200  # 最大GC暂停时间

# 特定服务额外参数
-XX:+UseStringDeduplication   # 字符串去重（降低内存）
-XX:+ParallelRefProcEnabled   # 并行引用处理（提升性能）
-Djava.security.egd=file:/dev/./urandom  # 随机数生成优化
```

---

## 📝 修改的文件

### Kubernetes Deployment 配置

| 文件 | 修改内容 |
|------|---------|
| [api-gateway.yml](file:///d:/Developer/workplace/py/iteam/trae/deployments/kubernetes/api-gateway.yml) | 添加 JAVA_OPTS 环境变量 |
| [uav-platform-service.yml](file:///d:/Developer/workplace/py/iteam/trae/deployments/kubernetes/uav-platform-service.yml) | 添加 JAVA_OPTS 环境变量，提升资源限制 |
| [wrf-processor-service.yml](file:///d:/Developer/workplace/py/iteam/trae/deployments/kubernetes/wrf-processor-service.yml) | 添加 JAVA_OPTS 环境变量 |
| [meteor-forecast-service.yml](file:///d:/Developer/workplace/py/iteam/trae/deployments/kubernetes/meteor-forecast-service.yml) | 添加 JAVA_OPTS 环境变量 |
| [path-planning-service.yml](file:///d:/Developer/workplace/py/iteam/trae/deployments/kubernetes/path-planning-service.yml) | 添加 JAVA_OPTS 环境变量 |
| [data-assimilation-service.yml](file:///d:/Developer/workplace/py/iteam/trae/deployments/kubernetes/data-assimilation-service.yml) | 添加 JAVA_OPTS 环境变量 |
| [uav-weather-collector.yml](file:///d:/Developer/workplace/py/iteam/trae/deployments/kubernetes/uav-weather-collector.yml) | 添加 JAVA_OPTS 环境变量 |
| [backend-spring.yml](file:///d:/Developer/workplace/py/iteam/trae/deployments/kubernetes/backend-spring.yml) | 添加 JAVA_OPTS 环境变量 |

---

## 🔧 配置示例

### K8s Deployment 中的 JVM 配置

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: uav-platform-service
  namespace: uav-platform
spec:
  template:
    spec:
      containers:
        - name: uav-platform-service
          image: trae-uav-platform:latest
          ports:
            - containerPort: 8080
          env:
            - name: JAVA_OPTS
              value: "-Xms512m -Xmx1g -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -XX:+UseStringDeduplication"
          resources:
            requests:
              memory: "512Mi"
            limits:
              memory: "1536Mi"  # 留出缓冲空间给非堆内存
```

---

## 📊 配置对比

### Docker Compose vs Kubernetes

| 环境 | 堆内存 | 容器限制 | 说明 |
|------|--------|---------|------|
| **Docker Compose** | 1GB | 1.5GB | 直接在宿主机上运行 |
| **Kubernetes** | 1GB | 1.5GB | 在 Pod 中运行，需要考虑系统开销 |

### 资源配置优化

| 服务 | K8s 内存限制（修改前） | K8s 内存限制（修改后） | 说明 |
|------|----------------------|----------------------|------|
| uav-platform | 512Mi | **1536Mi** | 提升到与docker-compose一致 |

---

## ⚠️ 注意事项

### 1. **OOM 风险缓解**
- ✅ K8s 内存限制已提升到 1.5GB，为 JVM 堆和非堆内存提供足够空间
- ✅ 建议监控实际内存使用情况，适当调整

### 2. **容器资源限制**
- K8s 内存限制应大于 JVM 堆大小（建议 1.3-1.5 倍）
- 非堆内存包括：Metaspace、CodeCache、Thread Stack、Direct Buffers

### 3. **监控建议**
```bash
# 查看 Pod 内存使用
kubectl top pods -n uav-platform

# 查看 JVM 内存参数
kubectl exec -it <pod-name> -n uav-platform -- jstat -gc <pid>
```

---

## 🔍 相关配置

### Dockerfile 默认值（备用）

```dockerfile
# api-gateway/Dockerfile.runtime
ENV JAVA_OPTS="-Xms256m -Xmx512m -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -XX:+UseStringDeduplication"
```

### Docker Compose 配置（参考）

```yaml
# docker-compose.yml
uav-platform:
  environment:
    JAVA_OPTS: -Xms512m -Xmx1g -XX:+UseG1GC -XX:MaxGCPauseMillis=200 -XX:+UseStringDeduplication
  deploy:
    resources:
      limits:
        memory: 1.5G
```

---

## ✅ 审计结论

**审计任务 M1: JVM 参数不一致** ✅ **已解决**

- 为所有 K8s Deployment 添加了 JAVA_OPTS 环境变量
- 与 docker-compose 配置保持一致
- 避免了 K8s 中 OOM 风险
- 提升了资源配置的准确性和可维护性

---

## 🚀 下一步建议

1. **监控优化**: 配置 Prometheus JVM 指标监控
2. **自动调优**: 考虑使用 JMX Exporter 进行动态监控
3. **资源配额**: 在 namespace 级别设置资源配额（ResourceQuota）

---

**审计任务状态**: ✅ **已完成**  
**Git 提交**: 已包含在部署配置更新中
