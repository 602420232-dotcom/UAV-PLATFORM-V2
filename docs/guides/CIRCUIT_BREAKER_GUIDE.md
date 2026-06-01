# UAV Platform Circuit Breaker Implementation Guide

## 📚 熔断器（Circuit Breaker）实现指南

**创建时间**: 2026-05-08  
**版本**: 1.0.0  
**状态**: ✅ **已完成**

---

## 🔥 为什么需要熔断器？

### 问题背景

在微服务架构中，服务间调用可能会出现以下问题：

1. **级联故障**: 一个服务不可用，导致调用它的服务也超时，最终整个系统瘫痪
2. **资源耗尽**: 大量请求堆积在等待中，耗尽线程池和连接池
3. **用户体验差**: 用户请求长时间等待，最终得到超时错误

### 熔断器模式

熔断器模式类似于电路保险丝：
- **闭合状态（Closed）**: 正常请求通过，失败率低
- **打开状态（Open）**: 快速失败，直接返回错误，不调用下游服务
- **半开状态（Half-Open）**: 尝试放行部分请求，测试服务是否恢复

---

## ✅ 已实现的熔断器

### 服务列表

| 服务名称 | 熔断器配置 | 失败率阈值 | 恢复等待时间 | 用途 |
|---------|-----------|----------|------------|------|
| **meteor-forecast-service** | default | 50% | 10秒 | 气象预报数据 |
| **path-planning-service** | highVolume | 60% | 20秒 | 路径规划算法 |
| **data-assimilation-service** | critical | 45% | 8秒 | 数据同化处理 |

---

## 📁 实现的文件

### 1. 配置文件

- ✅ `common-utils/src/main/resources/resilience4j-circuitbreaker.yml`
  - Circuit Breaker 配置
  - Retry 配置
  - Rate Limiter 配置
  - Bulkhead 配置
  - Time Limiter 配置

### 2. Java 配置类

- ✅ `common-utils/src/main/java/com/uav/common/resilience/ResilienceConfig.java`
  - CircuitBreakerRegistry Bean
  - RetryRegistry Bean
  - TimeLimiterRegistry Bean
  - RestTemplate Bean

### 3. 服务调用封装

- ✅ `common-utils/src/main/java/com/uav/common/resilience/CircuitBreakerService.java`
  - `callMeteorForecast()` - 调用气象预报服务
  - `callPathPlanning()` - 调用路径规划服务
  - `callDataAssimilation()` - 调用数据同化服务
  - `getCircuitBreakerStatus()` - 获取熔断器状态

### 4. 监控接口

- ✅ `common-utils/src/main/java/com/uav/common/resilience/CircuitBreakerController.java`
  - `GET /api/admin/circuit-breaker/status` - 获取所有熔断器状态
  - `GET /api/admin/circuit-breaker/status/{serviceName}` - 获取指定熔断器状态
  - `GET /api/admin/circuit-breaker/details/{serviceName}` - 获取详细配置和指标
  - `POST /api/admin/circuit-breaker/trip/{serviceName}` - 手动触发熔断
  - `POST /api/admin/circuit-breaker/reset/{serviceName}` - 手动重置熔断器
  - `POST /api/admin/circuit-breaker/half-open/{serviceName}` - 强制半开状态
  - `GET /api/admin/circuit-breaker/health` - 健康检查

---

## 🚀 使用指南

### 1. Maven 依赖

在 `pom.xml` 中添加依赖：

```xml
<!-- Resilience4j 熔断器 -->
<dependency>
    <groupId>io.github.resilience4j</groupId>
    <artifactId>resilience4j-spring-boot2</artifactId>
    <version>2.1.0</version>
</dependency>

<dependency>
    <groupId>io.github.resilience4j</groupId>
    <artifactId>resilience4j-circuitbreaker</artifactId>
    <version>2.1.0</version>
</dependency>

<dependency>
    <groupId>io.github.resilience4j</groupId>
    <artifactId>resilience4j-retry</artifactId>
    <version>2.1.0</version>
</dependency>

<dependency>
    <groupId>io.github.resilience4j</groupId>
    <artifactId>resilience4j-timelimiter</artifactId>
    <version>2.1.0</version>
</dependency>

<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-aop</artifactId>
</dependency>
```

### 2. 配置加载

在 `application.yml` 中引入熔断器配置：

```yaml
spring:
  application:
    name: uav-platform-service
  
  config:
    import: optional:classpath:resilience4j-circuitbreaker.yml
```

### 3. 使用熔断器服务

#### 方式一：自动注入（推荐）

```java
@Autowired
private CircuitBreakerService circuitBreakerService;

public void myMethod() {
    try {
        // 调用气象预报服务
        ResponseEntity<WeatherData> response = 
            circuitBreakerService.callMeteorForecast(
                "http://meteor-forecast-service/api/weather/current",
                WeatherData.class
            );
        
        // 处理响应
        WeatherData weather = response.getBody();
        
    } catch (CircuitBreakerService.ServiceUnavailableException e) {
        // 服务不可用，执行降级逻辑
        log.warn("Weather service unavailable, using cached data");
        return getCachedWeather();
    }
}
```

#### 方式二：使用 @CircuitBreaker 注解

```java
@Service
public class WeatherService {
    
    @Autowired
    private RestTemplate restTemplate;
    
    @CircuitBreaker(name = "meteor-forecast-service", fallbackMethod = "getWeatherFallback")
    public WeatherData getWeather(String droneId) {
        return restTemplate.getForObject(
            "http://meteor-forecast-service/api/weather/" + droneId,
            WeatherData.class
        );
    }
    
    // 降级方法
    public WeatherData getWeatherFallback(String droneId, Exception e) {
        log.warn("Weather service failed, returning default: {}", e.getMessage());
        return WeatherData.getDefault();
    }
}
```

#### 方式三：使用装饰器模式

```java
public void myMethod() {
    Supplier<Result> supplier = () -> callService();
    
    // 使用熔断器装饰
    Supplier<Result> decorated = CircuitBreaker
        .decorateSupplier(circuitBreakerRegistry.circuitBreaker("my-service"), supplier);
    
    // 使用重试装饰
    decorated = Retry.decorateSupplier(retryRegistry.retry("my-service"), decorated);
    
    Result result = decorated.get();
}
```

---

## 📊 熔断器配置详解

### Circuit Breaker 配置

```yaml
resilience4j.circuitbreaker:
  configs:
    default:
      # 熔断器开启条件
      failureRateThreshold: 50              # 失败率阈值（50%）
      slowCallRateThreshold: 100            # 慢调用率阈值
      
      # 滑动窗口配置
      slidingWindowSize: 10                 # 滑动窗口大小（最近10次调用）
      slidingWindowType: COUNT_BASED         # 基于调用次数（也可基于时间）
      minimumNumberOfCalls: 5                # 最少调用次数（达到后才计算失败率）
      
      # 熔断器恢复配置
      waitDurationInOpenState: 10s          # 熔断器打开后等待时间
      permittedNumberOfCallsInHalfOpenState: 3  # 半开状态允许的调用次数
      automaticTransitionFromOpenToHalfOpenEnabled: true  # 自动从打开转到半开
      
      # 异常处理
      recordExceptions:                     # 记录的异常
        - java.io.IOException
        - java.util.concurrent.TimeoutException
        - org.springframework.web.client.ResourceAccessException
      ignoreExceptions:                     # 忽略的异常（不计入失败）
        - com.uav.common.exception.BusinessException
```

### Retry 配置

```yaml
resilience4j.retry:
  configs:
    default:
      maxAttempts: 3                      # 最大重试次数
      waitDuration: 500ms                  # 初始等待时间
      enableExponentialBackoff: true       # 启用指数退避
      exponentialBackoffMultiplier: 2     # 退避倍数（500ms -> 1s -> 2s）
      retryExceptions:                     # 可重试的异常
        - java.io.IOException
        - org.springframework.web.client.ResourceAccessException
```

---

## 🔍 监控熔断器

### REST API

#### 1. 查看所有熔断器状态

```bash
curl http://localhost:8080/api/admin/circuit-breaker/status
```

响应示例：
```json
{
  "totalBreakers": 3,
  "breakers": [
    {
      "name": "meteor-forecast-service",
      "state": "CLOSED",
      "failureRate": 0.0,
      "successfulCalls": 150,
      "failedCalls": 0,
      "notPermittedCalls": 0
    }
  ],
  "timestamp": 1709800000000
}
```

#### 2. 查看指定熔断器详情

```bash
curl http://localhost:8080/api/admin/circuit-breaker/details/meteor-forecast-service
```

#### 3. 手动触发熔断

```bash
curl -X POST http://localhost:8080/api/admin/circuit-breaker/trip/meteor-forecast-service
```

#### 4. 手动重置熔断器

```bash
curl -X POST http://localhost:8080/api/admin/circuit-breaker/reset/meteor-forecast-service
```

#### 5. 健康检查

```bash
curl http://localhost:8080/api/admin/circuit-breaker/health
```

---

## 📈 集成到监控仪表板

### Prometheus 指标

熔断器自动暴露以下指标到 Prometheus：

```
# Circuit Breaker 指标
resilience4j_circuitbreaker_state{name="meteor-forecast-service",state="CLOSED"}
resilience4j_circuitbreaker_failure_rate{name="meteor-forecast-service"}
resilience4ircuitbreaker_successful_calls_total{name="meteor-forecast-service"}
resilience4j_circuitbreaker_failed_calls_total{name="meteor-forecast-service"}

# Retry 指标
resilience4j_retry_calls_total{name="meteor-forecast-service",kind="successful"}
resilience4j_retry_calls_total{name="meteor-forecast-service",kind="failed"}
```

### Grafana Dashboard

创建熔断器监控仪表板：

1. **熔断器状态面板**
   - 查询: `resilience4j_circuitbreaker_state{state="CLOSED"}`
   - 展示: 状态饼图

2. **失败率面板**
   - 查询: `resilience4j_circuitbreaker_failure_rate`
   - 告警: 失败率 > 50%

3. **调用统计面板**
   - 查询: `resilience4j_circuitbreaker_calls_total`
   - 展示: 成功/失败趋势图

---

## ⚠️ 最佳实践

### 1. 合理设置失败率阈值

```yaml
# 对于关键服务，使用更低的阈值
critical:
  failureRateThreshold: 40    # 更严格

# 对于高流量服务，可以适当放宽
highVolume:
  failureRateThreshold: 60    # 更宽松
```

### 2. 设置合理的滑动窗口

```yaml
# 窗口太小可能导致误判
smallWindow:
  slidingWindowSize: 5         # 可能误判
  minimumNumberOfCalls: 3

# 窗口太大可能导致恢复慢
largeWindow:
  slidingWindowSize: 50        # 可能恢复太慢
  minimumNumberOfCalls: 30
```

### 3. 实现有效的降级逻辑

```java
public WeatherData getWeatherFallback(String droneId, Exception e) {
    // 1. 记录日志
    log.warn("Weather service failed for drone {}, using fallback", droneId, e);
    
    // 2. 使用缓存数据
    WeatherData cached = weatherCache.get(droneId);
    if (cached != null) {
        return cached;
    }
    
    // 3. 返回默认值
    return WeatherData.getDefault(droneId);
}
```

### 4. 避免嵌套熔断器

```java
// ❌ 不推荐：嵌套熔断器
@CircuitBreaker(name = "serviceA")
public void callServiceA() {
    serviceB.method();  // serviceB也有熔断器
}

// ✅ 推荐：分开调用
public void orchestrate() {
    try {
        callServiceA();
    } catch (Exception e) {
        // 处理
    }
    
    try {
        callServiceB();
    } catch (Exception e) {
        // 处理
    }
}
```

### 5. 监控和告警

```yaml
# Alertmanager 告警规则
- alert: CircuitBreakerOpen
  expr: resilience4j_circuitbreaker_state{state="OPEN"} > 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Circuit breaker {{ $labels.name }} is OPEN"
    description: "Service {{ $labels.name }} circuit breaker has been open for 1 minute"
```

---

## 🧪 测试熔断器

### 1. 单元测试

```java
@Test
public void testCircuitBreakerOpens() {
    // 模拟服务连续失败
    for (int i = 0; i < 6; i++) {
        try {
            service.call();
        } catch (Exception e) {
            // 预期失败
        }
    }
    
    // 验证熔断器打开
    CircuitBreaker.State state = circuitBreaker.getState();
    assertEquals(CircuitBreaker.State.OPEN, state);
}

@Test
public void testFallback() {
    // 打开熔断器
    circuitBreaker.transitionToOpenState();
    
    // 调用应该触发降级
    Result result = service.call();
    assertEquals("fallback", result.getValue());
}
```

### 2. 集成测试

```java
@SpringBootTest
public class CircuitBreakerIntegrationTest {
    
    @Test
    public void testCircuitBreakerWithDownstreamService() {
        // 启动模拟服务
        wireMockServer.stubFor(get(urlEqualTo("/api/test"))
            .willReturn(serverError()));
        
        // 连续调用触发熔断
        for (int i = 0; i < 6; i++) {
            try {
                service.call();
            } catch (Exception e) {
                // 预期
            }
        }
        
        // 验证熔断器打开
        verify(6, getRequestedFor(urlEqualTo("/api/test")));
    }
}
```

---

## 📚 参考文档

- [Resilience4j Official Documentation](https://resilience4j.readme.io/)
- [Circuit Breaker Pattern - Martin Fowler](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Microservices with Spring Boot and Resilience4j](https://www.baeldung.com/spring-cloud-circuit-breaker)

---

## 🔗 相关配置

- [监控配置](deployments/monitoring/README.md)
- [日志配置](deployments/logging/README.md)
- [告警配置](deployments/monitoring/prometheus/alerts.yml)

---

## 📞 支持

如有问题，请查看：
- Resilience4j GitHub: https://github.com/resilience4j/resilience4j
- 项目 Wiki: https://wiki.example.com
- 联系: devops@example.com

---

**最后更新**: 2026-05-08 16:30  
**维护者**: DevOps Team  
**版本**: 1.0.0
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
