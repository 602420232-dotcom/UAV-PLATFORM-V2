# Swagger/OpenAPI聚合配置

## 概述

本文档描述如何配置API Gateway统一聚合所有下游服务的Swagger/OpenAPI文档

## 配置步骤

### 1. 添加依赖

在 `api-gateway/pom.xml` 中添加以下依赖：

```xml
<!-- Swagger OpenAPI 聚合 -->
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version>2.3.0</version>
</dependency>
```

### 2. Gateway配置

创建聚合配置类

```java
package com.uav.gateway.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.MediaType;
import org.springframework.web.reactive.function.client.WebClient;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.Contact;
import java.util.Arrays;
import java.util.List;

@Configuration
public class OpenApiAggregatorConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title("UAV Path Planning System API")
                .version("2.1.0")
                .description("基于WRF气象驱动的无人机VRP智能路径规划系统 API")
                .contact(new Contact()
                    .name("UAV Team")
                    .email("team@uav-system.com"))
            );
    }

    @Bean
    public WebClient webClient() {
        return WebClient.builder()
            .defaultHeader("Accept", MediaType.APPLICATION_JSON_VALUE)
            .build();
    }
}
```

### 3. 动态聚合Controller

创建Swagger聚合端点

```java
package com.uav.gateway.controller;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

@RestController
@RequestMapping("/api-docs")
public class SwaggerAggregatorController {

    private final WebClient webClient;

    // 各服务Swagger端点
    private static final Map<String, String> SERVICE_SWAGGER_URLS = Map.of(
        "uav-platform", "http://uav-platform:8080/v3/api-docs",
        "wrf-processor", "http://wrf-processor:8081/v3/api-docs",
        "meteor-forecast", "http://meteor-forecast:8082/v3/api-docs",
        "path-planning", "http://path-planning:8083/v3/api-docs",
        "data-assimilation", "http://data-assimilation:8084/v3/api-docs"
    );

    public SwaggerAggregatorController(WebClient webClient) {
        this.webClient = webClient;
    }

    @GetMapping("/aggregate")
    public Mono<Map<String, Object>> aggregateDocs() {
        List<CompletableFuture<Map<String, Object>>> futures = new ArrayList<>();

        SERVICE_SWAGGER_URLS.forEach((serviceName, url) -> {
            CompletableFuture<Map<String, Object>> future = CompletableFuture.supplyAsync(() -> {
                try {
                    String doc = webClient.get()
                        .uri(url)
                        .retrieve()
                        .bodyToMono(String.class)
                        .timeout(Duration.ofSeconds(5))
                        .block();
                    return Map.of("service", serviceName, "doc", parseOpenApi(doc));
                } catch (Exception e) {
                    return Map.of("service", serviceName, "error", e.getMessage());
                }
            });
            futures.add(future);
        });

        return Mono.fromFuture(
            CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]))
                .thenApply(v -> {
                    Map<String, Object> result = new HashMap<>();
                    result.put("services", futures.stream()
                        .map(CompletableFuture::join)
                        .toList());
                    return result;
                })
        );
    }

    @GetMapping("/{service}")
    public Mono<Map<String, Object>> getServiceDoc(@PathVariable String service) {
        String url = SERVICE_SWAGGER_URLS.get(service.toLowerCase());
        if (url == null) {
            return Mono.error(new IllegalArgumentException("Service not found: " + service));
        }

        return webClient.get()
            .uri(url)
            .retrieve()
            .bodyToMono(Map.class)
            .map(doc -> {
                Map<String, Object> enrichedDoc = new HashMap<>(doc);
                enrichedDoc.put("_service", service);
                enrichedDoc.put("_gateway", "http://localhost:8088");
                return enrichedDoc;
            })
            .timeout(Duration.ofSeconds(10));
    }

    @GetMapping("/services")
    public Map<String, Map<String, String>> listServices() {
        Map<String, Map<String, String>> result = new LinkedHashMap<>();
        SERVICE_SWAGGER_URLS.forEach((service, url) -> {
            result.put(service, Map.of(
                "name", service,
                "api_url", url.replace("/v3/api-docs", "/swagger-ui.html"),
                "openapi_url", "/api-docs/" + service
            ));
        });
        return result;
    }

    private Object parseOpenApi(String json) {
        // 简单的JSON解析
        return json;
    }
}
```

### 4. SpringDoc配置

在各服务的 `application.yml` 中添加SpringDoc配置：

```yaml
springdoc:
  api-docs:
    enabled: true
    path: /v3/api-docs
  swagger-ui:
    enabled: true
    path: /swagger-ui.html
    operations-sorter: method
    tags-sorter: alpha
  show-actuator: false
```

### 5. 访问方式

部署后可通过以下URL访问聚合的API文档：

| 访问方式             | URL                                        |
| ---------------- | ------------------------------------------ |
|   聚合文档首页         | <http://localhost:8088/api-docs/>          |
|   统一Swagger UI   | <http://localhost:8088/swagger-ui.html>    |
|   特定服务文档         | <http://localhost:8088/api-docs/{service}> |
|   服务列表           | <http://localhost:8088/api-docs/services>  |

### 6. 服务文档列表

| 服务                | API端点        | Swagger UI                     |
| ----------------- | ------------ | ------------------------------ |
| UAV Platform      | /v3/api-docs | /swagger-ui.html#/platform     |
| WRF Processor     | /v3/api-docs | /swagger-ui.html#/wrf          |
| Meteor Forecast   | /v3/api-docs | /swagger-ui.html#/forecast     |
| Path Planning     | /v3/api-docs | /swagger-ui.html#/planning     |
| Data Assimilation | /v3/api-docs | /swagger-ui.html#/assimilation |

## 认证配置

如果服务需要认证，在Swagger UI中添加Bearer Token：

```yaml
springdoc:
  swagger-ui:
    configs:
      - addAuthorizationStripFilter: true
    tagsSorter: alpha
    operationsSorter: method
```

## 性能优化

### 缓存配置

```java
@Cacheable(value = "swagger-docs", unless = "#result == null")
@GetMapping("/{service}")
public Mono<Map<String, Object>> getServiceDoc(@PathVariable String service) {
    // ...
}
```

### 超时配置

```yaml
spring.cloud:
  gateway:
    httpclient:
      connect-timeout: 5000
      response-timeout: 10s
```

## 故障排查

### 常见问题

1. **服务不可达**
   - 检查服务是否启动
   - 检查网络连通性
   - 查看网关日志
2. **文档加载慢**
   - 启用缓存
   - 减少聚合的服务数量
   - 增加超时时间
3. **认证失败**
   - 配置CORS
   - 检查Token有效性

## 维护说明

- 添加新服务时在 `SERVICE_SWAGGER_URLS` Map中添加条目
- 定期检查各服务的OpenAPI文档是否正常
- 监控 `/api-docs` 端点的响应时间

---

**最后更新**: 2026-06-01
