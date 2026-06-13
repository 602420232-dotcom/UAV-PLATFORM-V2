# 架构设计文档

## 1. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端层                              │
│  SDK (Java/Python/Go) / 集成方系统 / 开发者控制台            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│  认证(X-API-Key) / 限流(租户配额) / 路由 / 熔断 / 日志        │
│  独立构建: Spring Boot 3.4.x + Spring Cloud 2024.0.3         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      核心服务层                              │
│  platform-api  weather-api  planning-api  assimilation-api  │
│  observation-api  risk-api  utm-api                         │
│  (risk-api 包含适航评估功能)                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      Python 算法层                           │
│  algorithm-engine (20+ 算法: 风乌/天资/风雷/同化/规划/评估)   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      基础设施层                              │
│  MySQL 8.4.7  Redis 7.2  Kafka 7.8  Zookeeper              │
└─────────────────────────────────────────────────────────────┘
```

> **服务清单**: 共 8 个服务 — 1 个 API Gateway + 7 个业务服务（platform, weather, assimilation, risk, observation, planning, utm）。
> **Gateway 说明**: API Gateway 采用独立构建方式运行于 Spring Boot 3.4.x，与主项目 Spring Boot 4.0 解耦，避免兼容性问题。

## 2. 多租户隔离方案

### 2.1 Schema 隔离

- 公共 Schema：`public` — 租户信息、API 调用日志、审计日志
- 租户 Schema：`tenant_{tenant_id}` — 业务数据

### 2.2 动态 Schema 切换

```java
// 通过 TenantContext 动态切换数据源
public class TenantContext {
    private static final ThreadLocal<String> CURRENT_TENANT = new ThreadLocal<>();

    public static void setTenant(String tenantId) {
        CURRENT_TENANT.set("tenant_" + tenantId);
    }

    public static String getTenant() {
        return CURRENT_TENANT.get();
    }
}
```

### 2.3 连接池配置

- 每个租户独立连接池
- 连接池大小根据租户配额动态调整

## 3. API 版本策略

### 3.1 Header 版本控制

```
Accept: application/vnd.uav.v1+json
Accept: application/vnd.uav.v2+json
```

### 3.2 版本解析

```java
@Component
public class ApiVersionResolver implements HandlerMapping {
    @Override
    protected void initApplicationContext() {
        // 解析 Accept Header 中的版本信息
    }
}
```

## 4. 认证方案

### 4.1 API Key + HMAC 签名

```
X-API-Key: <api_key>
X-Timestamp: <unix_timestamp>
X-Signature: HMAC-SHA256(api_key + timestamp + request_body, api_secret)
```

### 4.2 签名验证流程

1. 提取 API Key，查询对应租户和 Secret
2. 验证时间戳（±5 分钟有效窗口）
3. 重新计算签名，比对是否一致
4. 验证通过后将租户信息写入 TenantContext

## 5. 限流策略

### 5.1 多级限流

| 级别 | 粒度 | 配置 |
|------|------|------|
| 全局 | 系统总 QPS | 10000/s |
| 租户 | 单租户 QPS | 100/s（可配置） |
| API | 单 API 端点 | 50/s（可配置） |

### 5.2 实现方式

- Redis 令牌桶算法
- 超限返回 429 Too Many Requests

## 6. 核心算法流水线

```
多源数据(WRF/风乌/天资/风雷)
    ↓
数据预处理(质量控制)
    ↓
多模型动态融合(加权平均)
    ↓
CNN空间订正 + LSTM时序订正
    ↓
U-Net降尺度(3km→1km)
    ↓
贝叶斯同化(3D-VAR/EnKF)
    ↓
稀疏GPR风险场生成
    ↓
风险代价重构
    ↓
滚动时域路径优化(MPC)
    ↓
主动观测决策(方差阈值判断)
    ↓
多机冲突消解
    ↓
路径输出
```

## 7. 部署架构

### 7.1 开发环境

- Docker Compose 单节点部署
- 所有服务本地启动
- Gateway 独立构建运行于 Spring Boot 3.4.x

### 7.2 生产环境

- Kubernetes 集群部署
- 滚动发布策略
- Prometheus + Grafana 监控
- ELK 日志收集
