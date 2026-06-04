# Feign Client迁移指南

## 概述

本文档说明如何将现有的 `RestTemplate` 调用迁移到 `Feign Client`，以实现声明式服务调用。

## 迁移步骤

### 1. 添加依赖

在服务的 `pom.xml` 中添加 Feign 依赖：

```xml
<!-- 如果common-utils已包含Feign则只需在需要的模块添加 -->
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-openfeign</artifactId>
</dependency>
```

### 2. 启用Feign

在主应用类或配置类添加 `@EnableFeignClients` 注解：

```java
@SpringBootApplication
@EnableFeignClients(basePackages = "com.uav.common.feign")
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

### 3. 配置服务URL

在 `application.yml` 中配置各服务的URL：

```yaml
services:
  wrf-processor:
    url: http://wrf-processor:8081
  data-assimilation:
    url: http://data-assimilation:8084
  meteor-forecast:
    url: http://meteor-forecast:8082
  path-planning:
    url: http://path-planning:8083
```

### 4. 注入并使用

```java
@RestController
public class MyController {
    
    @Autowired
    private PathPlanningClient pathPlanningClient;
    
    @PostMapping("/plan")
    public Map<String, Object> plan(@RequestBody Map<String, Object> request) {
        // 直接调用就像调用本地方法一样
        return pathPlanningClient.planVRPTW(request);
    }
}
```

## Feign Client列表

### 已创建的Client

| Client | 服务 | 用途 |
|--------|------|------|
| `WrfProcessorClient` | wrf-processor-service | WRF气象数据处理 |
| `DataAssimilationClient` | data-assimilation-service | 贝叶斯同化 |
| `MeteorForecastClient` | meteor-forecast-service | 气象预测 |
| `PathPlanningClient` | path-planning-service | 路径规划 |

### 添加新的Client

在 `common-utils/src/main/java/com/uav/common/feign/` 目录下创建新的Client接口：

```java
@FeignClient(name = "my-service", url = "${services.my-service.url}")
public interface MyServiceClient {
    
    @GetMapping("/api/resource/{id}")
    Resource getResource(@PathVariable("id") Long id);
    
    @PostMapping("/api/resource")
    Resource createResource(@RequestBody ResourceRequest request);
}
```

## 与熔断器集成

### 使用Feign + Resilience4j

#### 方式1：FallbackFactory（推荐）

```java
@Component
public class PathPlanningClientFallbackFactory implements FallbackFactory<PathPlanningClient> {
    
    @Override
    public PathPlanningClient create(Throwable cause) {
        return new PathPlanningClient() {
            @Override
            public Map<String, Object> planVRPTW(Map<String, Object> request) {
                log.warn("Fallback triggered for planVRPTW", cause);
                return Map.of("success", false, "error", "服务暂时不可用");
            }
            
            // 实现其他方法...
        };
    }
}
```

在Client中添加fallbackFactory：

```java
@FeignClient(
    name = "path-planning-service", 
    url = "${services.path-planning.url}",
    fallbackFactory = PathPlanningClientFallbackFactory.class
)
public interface PathPlanningClient {
    // ...
}
```

#### 方式2使用Sentinel

```java
@FeignClient(name = "path-planning-service", url = "${services.path-planning.url}")
public interface PathPlanningClient {
    
    @SentinelFeign(name = "pathPlanning", fallback = PathPlanningFallback.class)
    @PostMapping("/api/planning/vrptw")
    Map<String, Object> planVRPTW(@RequestBody Map<String, Object> request);
}
```

## 配置文件参考

### application.yml

```yaml
spring:
  cloud:
    openfeign:
      client:
        config:
          default:
            connectTimeout: 5000
            readTimeout: 10000
            loggerLevel: basic
          # 针对特定服务的配置
          path-planning-service:
            connectTimeout: 3000
            readTimeout: 5000
      # 启用压缩
      compression:
        request:
          enabled: true
        response:
          enabled: true
      # Hystrix配置如果使用
      hystrix:
        enabled: true
```

## 常见问题

### Q: 如何调试Feign请求?

A: `application.yml` 中设置日志级别

```yaml
logging:
  level:
    com.uav.common.feign: DEBUG
```

### Q: 如何传递Header?

A: 使用 `@RequestHeader` 注解：

```java
@FeignClient(name = "service")
public interface ServiceClient {
    
    @GetMapping("/api/data")
    Data getData(
        @RequestHeader("Authorization") String token,
        @RequestParam("id") Long id
    );
}
```

### Q: 如何处理404等HTTP错误？

A: 使用 `ResponseEntity` 作为返回类型：

```java
@GetMapping("/api/resource/{id}")
ResponseEntity<Resource> getResource(@PathVariable Long id);
```

## 迁移对照表

### Before (RestTemplate)

```java
@Service
public class MyService {
    
    @Autowired
    private RestTemplate restTemplate;
    
    @Value("${services.path-planning.url}")
    private String planningUrl;
    
    public Map<String, Object> plan(Map<String, Object> request) {
        try {
            Map<String, Object> response = restTemplate.postForObject(
                planningUrl + "/api/planning/vrptw",
                request,
                Map.class
            );
            return response;
        } catch (Exception e) {
            log.error("Planning failed", e);
            return Map.of("success", false, "error", e.getMessage());
        }
    }
}
```

### After (Feign Client)

```java
@Service
public class MyService {
    
    @Autowired
    private PathPlanningClient pathPlanningClient;
    
    public Map<String, Object> plan(Map<String, Object> request) {
        return pathPlanningClient.planVRPTW(request);
    }
}
```

## 最佳实践

1. **使用Fallback**始终为Feign Client配置降级逻辑
2. **超时配置**根据业务设置合理的超时时间
3. **日志记录**在Fallback中记录详细的错误信息
4. **健康检查**：实现health()方法用于服务健康检查
5. **统一封装**：在common-utils中维护统一的Client接口

---

*最后更新 2026-06-01*

