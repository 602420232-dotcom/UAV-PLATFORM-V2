# Circuit Breaker 快速集成示例

## 🚀 在服务中集成熔断器

### 示例1: 在 UAV Platform Service 中调用气象预报服务

```java
package com.uav.platform.service;

import com.uav.common.resilience.CircuitBreakerService;
import com.uav.common.resilience.CircuitBreakerService.ServiceUnavailableException;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class WeatherIntegrationService {
    
    @Autowired
    private CircuitBreakerService circuitBreakerService;
    
    /**
     * 获取无人机当前位置的天气信息
     * 使用熔断器保护，防止气象服务故障影响主流程
     */
    public WeatherResponse getDroneWeather(String droneId) {
        String url = "http://meteor-forecast-service/api/weather/drone/" + droneId;
        
        try {
            ResponseEntity<WeatherResponse> response = 
                circuitBreakerService.callMeteorForecast(url, WeatherResponse.class);
            
            return response.getBody();
            
        } catch (ServiceUnavailableException e) {
            // 降级处理：返回默认天气或缓存数据
            log.warn("Weather service unavailable, using default weather for drone {}", droneId);
            return getDefaultWeather(droneId);
        }
    }
    
    /**
     * 批量获取天气预警
     */
    public List<WeatherAlert> getWeatherAlerts(List<String> droneIds) {
        return droneIds.stream()
            .map(this::getDroneWeather)
            .filter(w -> w.hasAlert())
            .map(w -> new WeatherAlert(w.getDroneId(), w.getAlertMessage()))
            .collect(Collectors.toList());
    }
}
```

### 示例2: 在 Path Planning Service 中调用数据同化服务

```java
package com.uav.pathplanning.service;

import com.uav.common.resilience.CircuitBreakerService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
@Slf4j
public class PathPlanningService {
    
    @Autowired
    private CircuitBreakerService circuitBreakerService;
    
    /**
     * 基于气象数据规划路径
     */
    public Path planPath(PathRequest request) {
        // 获取气象预报（带熔断保护）
        WeatherData weather = getWeatherData(request.getDroneId());
        
        // 获取数据同化结果（带熔断保护）
        AssimilationResult assimilation = getAssimilationData(request.getAreaId());
        
        // 执行路径规划
        return executePathPlanning(request, weather, assimilation);
    }
    
    private WeatherData getWeatherData(String droneId) {
        String url = "http://meteor-forecast-service/api/weather/" + droneId;
        
        try {
            ResponseEntity<WeatherData> response = 
                circuitBreakerService.callMeteorForecast(url, WeatherData.class);
            return response.getBody();
            
        } catch (ServiceUnavailableException e) {
            log.warn("Weather service unavailable, using conservative planning");
            return WeatherData.getConservative();  // 保守的天气数据
        }
    }
    
    private AssimilationResult getAssimilationData(String areaId) {
        String url = "http://data-assimilation-service/api/assimilation/area/" + areaId;
        
        try {
            ResponseEntity<AssimilationResult> response = 
                circuitBreakerService.callDataAssimilation(url, AssimilationResult.class);
            return response.getBody();
            
        } catch (ServiceUnavailableException e) {
            log.warn("Assimilation service unavailable, using default model");
            return AssimilationResult.getDefault();  // 默认同化结果
        }
    }
}
```

### 示例3: 使用 @CircuitBreaker 注解（需要添加 AOP 依赖）

```java
package com.uav.weather.service;

import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

@Service
public class WeatherService {
    
    private final RestTemplate restTemplate;
    
    public WeatherService(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }
    
    @CircuitBreaker(name = "meteor-forecast-service", fallbackMethod = "getWeatherFallback")
    public WeatherData getWeather(String droneId) {
        return restTemplate.getForObject(
            "http://meteor-forecast-service/api/weather/" + droneId,
            WeatherData.class
        );
    }
    
    // 降级方法必须与原方法签名一致，最后一个参数是 Throwable
    public WeatherData getWeatherFallback(String droneId, Throwable throwable) {
        log.error("Weather service call failed: {}", throwable.getMessage());
        return WeatherData.getDefault(droneId);
    }
}
```

### 示例4: 配置 Feign Client 集成熔断器

```java
package com.uav.platform.client;

import feign CircuitBreaker;
import feign.Feign;
import feign.httpclient.ApacheHttpClient;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.context.annotation.Bean;

@FeignClient(
    name = "meteor-forecast-service",
    url = "http://meteor-forecast-service",
    configuration = WeatherClientConfig.class
)
public interface WeatherClient {
    
    @GetMapping("/api/weather/{droneId}")
    WeatherData getWeather(@PathVariable("droneId") String droneId);
}

class WeatherClientConfig {
    @Bean
    public WeatherClient weatherClient() {
        return Feign.builder()
            .client(new ApacheHttpClient())
            .circuitBreaker(new CircuitBreaker())
            .target(WeatherClient.class, new WeatherClientFallback());
    }
}

class WeatherClientFallback implements WeatherClient {
    @Override
    public WeatherData getWeather(String droneId) {
        return WeatherData.getDefault(droneId);
    }
}
```

---

## 🎯 降级策略示例

### 1. 返回缓存数据

```java
public WeatherData getWeatherFallback(String droneId, Throwable t) {
    // 尝试从缓存获取
    WeatherData cached = weatherCache.get(droneId);
    if (cached != null && !cached.isExpired()) {
        log.info("Using cached weather data for drone {}", droneId);
        return cached;
    }
    
    // 返回默认值
    return WeatherData.getDefault(droneId);
}
```

### 2. 返回静态默认数据

```java
public PathPlan getPathPlanFallback(PathRequest request, Throwable t) {
    // 使用保守的路径规划
    log.warn("Path planning service unavailable, using conservative plan");
    return PathPlan.getConservativePlan(request.getStartPoint(), request.getEndPoint());
}
```

### 3. 调用备用服务

```java
public WeatherData getWeatherFallback(String droneId, Throwable t) {
    // 尝试备用气象服务
    try {
        return backupWeatherService.getWeather(droneId);
    } catch (Exception e) {
        log.error("Backup weather service also failed", e);
        return WeatherData.getDefault(droneId);
    }
}
```

### 4. 返回友好错误信息

```java
public ApiResponse getForecastFallback(String areaId, Throwable t) {
    return ApiResponse.error(
        "FORECAST_UNAVAILABLE",
        "Weather forecast service is temporarily unavailable. Please try again later."
    );
}
```

---

## 📊 监控和告警配置

### Prometheus 告警规则

```yaml
groups:
  - name: circuit_breaker_alerts
    interval: 30s
    rules:
      # 熔断器打开告警
      - alert: CircuitBreakerOpen
        expr: resilience4j_circuitbreaker_state{state="OPEN"} > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Circuit breaker {{ $labels.name }} is OPEN"
          description: "The circuit breaker for {{ $labels.name }} has been open for 1 minute"

      # 高失败率告警
      - alert: HighCircuitBreakerFailureRate
        expr: resilience4j_circuitbreaker_failure_rate > 50
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High failure rate for {{ $labels.name }}"
          description: "Failure rate is above 50%"

      # 被拒绝的调用告警
      - alert: CircuitBreakerRejectingCalls
        expr: resilience4j_circuitbreaker_not_permitted_calls_total > 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Circuit breaker {{ $labels.name }} is rejecting calls"
          description: "Service calls are being rejected"

      # 熔断器恢复告警
      - alert: CircuitBreakerRecovered
        expr: rate(resilience4j_circuitbreaker_state{state="HALF_OPEN"}[1m]) > 0
        labels:
          severity: info
        annotations:
          summary: "Circuit breaker {{ $labels.name }} is recovering"
          description: "The circuit breaker is now in HALF_OPEN state"
```

---

## ✅ 验证熔断器工作

### 1. 查看熔断器状态

```bash
# 查看所有熔断器状态
curl http://localhost:8080/api/admin/circuit-breaker/status

# 查看指定熔断器详情
curl http://localhost:8080/api/admin/circuit-breaker/details/meteor-forecast-service
```

### 2. 测试熔断器

```bash
# 手动触发熔断
curl -X POST http://localhost:8080/api/admin/circuit-breaker/trip/meteor-forecast-service

# 验证服务调用失败
curl http://localhost:8080/api/weather/drone/UAV001

# 应该返回降级响应或错误

# 手动重置熔断器
curl -X POST http://localhost:8080/api/admin/circuit-breaker/reset/meteor-forecast-service

# 再次调用
curl http://localhost:8080/api/weather/drone/UAV001

# 应该恢复正常
```

### 3. Grafana Dashboard 查询

```promql
# 熔断器状态
resilience4j_circuitbreaker_state

# 失败率
resilience4j_circuitbreaker_failure_rate{name="meteor-forecast-service"}

# 调用统计
sum(rate(resilience4j_circuitbreaker_calls_total[5m])) by (name, kind)

# 被拒绝的调用
resilience4j_circuitbreaker_not_permitted_calls_total
```

---

## 📝 完整集成清单

### ✅ 已完成

- [x] 添加 Resilience4j 依赖到 pom.xml
- [x] 创建熔断器配置文件 resilience4j-circuitbreaker.yml
- [x] 创建 ResilienceConfig.java 配置类
- [x] 创建 CircuitBreakerService.java 服务封装
- [x] 创建 CircuitBreakerController.java 监控接口
- [x] 添加 Prometheus 指标暴露

### 🔄 待完成（在各服务中）

- [ ] 在 uav-platform-service 中集成气象预报服务调用
- [ ] 在 path-planning-service 中集成数据同化服务调用
- [ ] 在 weather-collector-service 中添加降级逻辑
- [ ] 配置 Grafana 熔断器监控仪表板
- [ ] 添加熔断器告警到 Alertmanager
- [ ] 编写熔断器单元测试

### 📋 集成检查表

每个服务集成时需要：

1. ✅ 添加 `@Autowired CircuitBreakerService circuitBreakerService`
2. ✅ 替换所有直接的服务调用为 `circuitBreakerService.callXxx()`
3. ✅ 实现降级逻辑（fallback）
4. ✅ 添加降级逻辑的单元测试
5. ✅ 在 Grafana 中添加监控面板
6. ✅ 更新 API 文档

---

## 🎓 熔断器工作流程

```
正常请求流程：
1. 请求 → CircuitBreaker (CLOSED) → 服务 → 响应成功 ✓
2. 请求 → CircuitBreaker (CLOSED) → 服务 → 响应失败 ✗
3. ... (连续失败达到阈值)
4. 请求 → CircuitBreaker (OPEN) → 直接返回降级响应 ✗✓

恢复流程：
1. CircuitBreaker (OPEN) → 等待 10秒
2. CircuitBreaker (HALF_OPEN) → 允许 3个请求
3. 请求全部成功 → CircuitBreaker (CLOSED) ✓
4. 请求失败 → CircuitBreaker (OPEN) ✗
```

---

## 🔧 调优建议

### 生产环境推荐配置

```yaml
resilience4j.circuitbreaker:
  configs:
    production:
      # 更严格的阈值
      failureRateThreshold: 40
      
      # 更大的滑动窗口
      slidingWindowSize: 20
      minimumNumberOfCalls: 10
      
      # 快速失败
      waitDurationInOpenState: 5s
      permittedNumberOfCallsInHalfOpenState: 2
      
      # 记录更多异常
      recordExceptions:
        - java.io.IOException
        - java.net.ConnectException
        - java.net.SocketTimeoutException
        - org.springframework.web.client.ResourceAccessException
        - com.uav.common.exception.BusinessException
```

### 开发环境配置

```yaml
resilience4j.circuitbreaker:
  configs:
    development:
      # 开发环境可以更宽松
      failureRateThreshold: 80
      waitDurationInOpenState: 30s
      automaticTransitionFromOpenToHalfOpenEnabled: false  # 手动恢复
```

---

**如有问题，请参考**: [CIRCUIT_BREAKER_GUIDE.md](CIRCUIT_BREAKER_GUIDE.md)
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
