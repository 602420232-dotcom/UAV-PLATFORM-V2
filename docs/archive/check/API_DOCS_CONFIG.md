# SpringDoc API 文档配置指南

> **文档版本**: v1.0  
> **最后更新**: 2026-06-01  
> **适用服务**: 微服务平台  
> **Swagger UI 访问**: http://localhost:{service-port}/swagger-ui.html

---

## 目录

1. [概述](#1-概述)
2. [已配置服务](#2-已配置服务)
3. [API Gateway 聚合配置](#3-api-gateway-聚合配置)
4. [访问 API 文档](#4-访问-api-文档)
5. [认证配置](#5-认证配置)

---

## 1. 概述

SpringDoc 是一个 OpenAPI 3 (Swagger) 的实现，为 Spring Boot 应用自动生成交互式 API 文档。

### 1.1 主要功能

- 自动生成 OpenAPI 3 规范文档
- 提供交互式 Swagger UI 界面
- 支持 JWT 认证
- API 测试功能

### 1.2 依赖版本

```xml
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version>2.3.0</version>
</dependency>
```

---

## 2. 已配置服务

### 2.1 UAV Platform Service (端口 8080)

**访问地址**: http://localhost:8080/swagger-ui.html  
**OpenAPI JSON**: http://localhost:8080/v3/api-docs

**配置类**: `com.uav.platform.config.OpenApiConfig`

```java
@Configuration
public class OpenApiConfig {
    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title("uav-platform-service API")
                .version("1.0.0")
                .description("WRF气象驱动的无人机VRP智能路径规划系统..."))
            .servers(List.of(
                new Server().url("http://localhost:8080").description("Local"),
                new Server().url("http://uav-platform:8080").description("Docker")
            ))
            .components(new Components()
                .addSecuritySchemes("bearerAuth",
                    new SecurityScheme()
                        .type(SecurityScheme.Type.HTTP)
                        .scheme("bearer")
                        .bearerFormat("JWT")));
    }
}
```

### 2.2 其他微服务

各微服务均已配置 SpringDoc，访问地址：

| 服务 | 端口 | Swagger UI |
|------|------|-----------|
| uav-platform | 8080 | http://localhost:8080/swagger-ui.html |
| wrf-processor | 8081 | http://localhost:8081/swagger-ui.html |
| meteor-forecast | 8082 | http://localhost:8082/swagger-ui.html |
| path-planning | 8083 | http://localhost:8083/swagger-ui.html |
| data-assimilation | 8084 | http://localhost:8084/swagger-ui.html |

---

## 3. API Gateway 聚合配置

API Gateway 使用 Spring Cloud Gateway (WebFlux)，需要单独配置 OpenAPI 聚合。

### 3.1 依赖配置

API Gateway 需要添加 springdoc 依赖：

```xml
<!-- 在 api-gateway/pom.xml 中添加 -->
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webflux-ui</artifactId>
    <version>2.3.0</version>
</dependency>
```

### 3.2 聚合配置

使用 SpringDoc 的 OpenAPI Resource 端点进行聚合：

```yaml
# api-gateway/src/main/resources/application.yml
springdoc:
  swagger-ui:
    urls:
      - name: "Platform Service"
        url: /v3/api-docs/uav-platform-service
      - name: "WRF Processor"
        url: /v3/api-docs/wrf-processor-service
      - name: "Meteor Forecast"
        url: /v3/api-docs/meteor-forecast-service
      - name: "Path Planning"
        url: /v3/api-docs/path-planning-service
      - name: "Data Assimilation"
        url: /v3/api-docs/data-assimilation-service
  api-docs:
    path: /v3/api-docs
```

### 3.3 路由配置

确保 Gateway 正确路由到各个服务的 API 文档：

```yaml
spring.cloud.gateway.routes:
  - id: platform-api
    uri: http://uav-platform:8080
    predicates:
      - Path=/api/v1/**
    filters:
      - StripPrefix=1

  # OpenAPI 文档路由
  - id: platform-docs
    uri: http://uav-platform:8080
    predicates:
      - Path=/v3/api-docs/**
```

---

## 4. 访问 API 文档

### 4.1 本地开发环境

启动服务后，访问各服务的 Swagger UI：

```bash
# UAV Platform Service
start http://localhost:8080/swagger-ui.html

# WRF Processor
start http://localhost:8081/swagger-ui.html

# Meteor Forecast
start http://localhost:8082/swagger-ui.html
```

### 4.2 Docker 环境

在 Docker Compose 环境中：

```bash
# 查看服务
docker-compose ps

# 访问单个服务的文档
start http://localhost:8080/swagger-ui.html

# API Gateway 聚合文档（配置完成后）
start http://localhost:8088/swagger-ui.html
```

### 4.3 Kubernetes 环境

```bash
# 端口转发
kubectl port-forward svc/uav-platform 8080:8080

# 访问文档
start http://localhost:8080/swagger-ui.html
```

---

## 5. 认证配置

### 5.1 JWT Bearer Token

所有服务已配置 JWT 认证：

1. 在 Swagger UI 页面点击右上角的 **Authorize** 按钮
2. 输入 JWT Token
3. 点击 **Authorize** 确认

### 5.2 获取 Token

```bash
# 获取访问令牌
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

响应示例：

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### 5.3 在 Swagger UI 中测试

1. 展开需要测试的 API
2. 点击 **Try it out** 按钮
3. 填写请求参数
4. 点击 **Execute** 执行请求
5. 查看响应结果

---

## 附录 A: 自定义配置

### A.1 自定义文档标题

在 `OpenApiConfig` 中修改：

```java
.info(new Info()
    .title("Custom Service Name API")
    .version("2.0.0")
    .description("Your service description"))
```

### A.2 禁用某个端点

使用 `@Operation` 注解的 `hidden` 属性：

```java
@Operation(hidden = true)
@GetMapping("/internal/health")
public Health health() {
    return Health.up().build();
}
```

### A.3 自定义分组

```java
@Bean
public GroupedOpenApi customApiGroup() {
    return GroupedOpenApi.builder()
        .group("custom-group")
        .pathsToMatch("/api/v1/custom/**")
        .build();
}
```

---

## 附录 B: 常见问题

### Q: Swagger UI 无法访问？

1. 检查服务是否启动
2. 确认端口是否正确
3. 检查 `springdoc` 依赖是否添加
4. 查看日志是否有启动错误

### Q: 如何禁用 Swagger UI？

```yaml
springdoc:
  swagger-ui:
    enabled: false
```

### Q: 聚合文档无法加载？

1. 确认各微服务的 `/v3/api-docs` 端点可访问
2. 检查 Gateway 路由配置
3. 确认服务发现正常工作

---

> **维护者**: DITHIOTHREITOL  
> **文档版本**: 1.0  
> **创建日期**: 2026-06-01
