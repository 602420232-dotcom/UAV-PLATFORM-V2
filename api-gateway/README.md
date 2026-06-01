# API 网关 - api-gateway

## 概述

API 网关（api-gateway）是无人机路径规划系统的统一入口。基于 Spring Cloud Gateway 实现路由转发、负载均衡、限流熔断和安全过滤。

## 技术栈

- **框架**: Spring Cloud Gateway 2023.0.0
- **语言**: Java 17
- **构建工具**: Maven
- **服务发现**: Nacos
- **限流**: Redis + RequestRateLimiter

## 服务信息

- **服务端口**: 8088
- **服务名称**: api-gateway

## 路由列表

| 路由 | 目标服务 | 端口 | 熔断器 | 说明 |
|------|---------|:----:|:------:|------|
| `/api/v1/**` | uav-platform-service | 8080 | ✅ | 主平台服务 |
| `/api/wrf/**` | wrf-processor-service | 8081 | ✅ | WRF气象处理 |
| `/api/forecast/**` | meteor-forecast-service | 8082 | ✅ | 气象预报服务 |
| `/api/planning/**` | path-planning-service | 8083 | ✅ | 路径规划服务 |
| `/api/assimilation/**` | data-assimilation-service | 8084 | ✅ | 数据同化服务 |

### 熔断器配置

所有路由均通过 `common-utils` 模块的 Resilience4j 熔断器保护：

- **失败率阈值**: 50%
- **恢复等待时间**: 10秒
- **滑动窗口**: 10次调用

详见: [Circuit Breaker Guide](../../docs/CIRCUIT_BREAKER_GUIDE.md)

## 默认过滤

- **限流**: RequestRateLimiter (100/s 补全, 200 突发)
- **重试**: Retry (3次, BAD_GATEWAY/SERVICE_UNAVAILABLE)
- **负载均衡**: Nacos lb:// 服务发现
- **熔断器**: Resilience4j Circuit Breaker (通过 common-utils)

## 熔断器监控

```bash
# 查看熔断器状态
curl http://localhost:8080/api/admin/circuit-breaker/status

# 查看健康检查
curl http://localhost:8080/api/admin/circuit-breaker/health
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `NACOS_ADDR` | `localhost:8848` | Nacos 注册中心地址 |
| `REDIS_HOST` | `localhost` | Redis 主机 |
| `REDIS_PORT` | `6379` | Redis 端口 |
| `SERVER_PORT` | `8088` | 网关监听端口 |

## 基础设施依赖

- **Nacos**: 服务注册与发现（启动前需运行）
- **Redis**: 令牌桶限流（启动前需运行）

## 构建与运行

```bash
# 构建
mvn clean package -DskipTests -pl api-gateway -am

# 运行
mvn spring-boot:run -pl api-gateway
```

## 配置

详见 `src/main/resources/application.yml`


---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
