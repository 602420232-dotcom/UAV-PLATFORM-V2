# UAV Platform Java SDK

> UAV Platform V2 官方 Java SDK，提供类型安全的 API 客户端、HMAC-SHA256 认证和核心工具类。

## 快速开始

### Maven 依赖

```xml
<dependency>
    <groupId>com.uav</groupId>
    <artifactId>java-sdk</artifactId>
    <version>2.0.1</version>
</dependency>
```

### Gradle

```groovy
implementation 'com.uav:java-sdk:2.0.1'
```

## 初始化客户端

```java
import com.uav.sdk.UavPlatformClient;
import com.uav.sdk.config.SdkConfig;

SdkConfig config = SdkConfig.builder()
    .baseUrl("https://api.uav-platform.example.com")
    .apiKey("your-api-key")
    .apiSecret("your-api-secret")
    .timeoutSeconds(30)
    .build();

UavPlatformClient client = new UavPlatformClient(config);
```

## 核心 API

### 气象服务

```java
import com.uav.sdk.dto.weather.WeatherQueryRequest;
import com.uav.sdk.dto.weather.WeatherGrid;

WeatherQueryRequest request = WeatherQueryRequest.builder()
    .longitude(116.4074)
    .latitude(39.9042)
    .altitude(100.0)
    .build();

WeatherGrid weather = client.weather().queryPoint(request);
System.out.println("Temperature: " + weather.getTemperature());
System.out.println("Wind Speed: " + weather.getWindSpeed());
```

### 风险评估

```java
import com.uav.sdk.dto.risk.RiskQueryRequest;
import com.uav.sdk.dto.risk.RiskAssessment;

RiskQueryRequest request = RiskQueryRequest.builder()
    .longitude(116.4074)
    .latitude(39.9042)
    .altitude(100.0)
    .uavModel("DJI-M300")
    .missionType("INSPECTION")
    .build();

RiskAssessment risk = client.risk().assess(request);
System.out.println("Risk Score: " + risk.getScore());
System.out.println("Risk Level: " + risk.getLevel());
```

### 路径规划

```java
import com.uav.sdk.dto.planning.PlanPathRequest;
import com.uav.sdk.dto.planning.PlanningTask;

PlanPathRequest request = PlanPathRequest.builder()
    .start(Map.of("lon", 116.4074, "lat", 39.9042, "alt", 100.0))
    .end(Map.of("lon", 116.5000, "lat", 39.9500, "alt", 120.0))
    .uavModel("DJI-M300")
    .optimizationTarget("BALANCED")
    .build();

PlanningTask task = client.planning().submitPathPlanning(request);
System.out.println("Task ID: " + task.getId());
System.out.println("Status: " + task.getStatus());
```

### 飞行计划 (UTM)

```java
import com.uav.sdk.dto.utm.FlightPlanRequest;
import com.uav.sdk.dto.utm.FlightPlan;

FlightPlanRequest request = FlightPlanRequest.builder()
    .uavId("UAV-001")
    .operatorId("OP-001")
    .plannedWaypoints(List.of(
        Map.of("lon", 116.4074, "lat", 39.9042, "alt", 100.0),
        Map.of("lon", 116.5000, "lat", 39.9500, "alt", 120.0)
    ))
    .plannedStartTime(LocalDateTime.now().plusHours(1))
    .plannedEndTime(LocalDateTime.now().plusHours(2))
    .build();

FlightPlan plan = client.utm().submitFlightPlan(request);
System.out.println("Plan ID: " + plan.getPlanId());
System.out.println("Status: " + plan.getStatus());
```

## 认证机制

SDK 自动处理 HMAC-SHA256 签名：

```java
// 每个请求自动附加以下 Header：
// X-API-Key: your-api-key
// X-Timestamp: 1718275200000
// X-Signature: HMAC-SHA256(signature)
```

### 手动签名（高级用法）

```java
import com.uav.sdk.auth.HmacSigner;

Map<String, String> headers = HmacSigner.signRequest(
    "GET", "/api/v1/weather/point",
    apiKey, apiSecret, requestBody
);
```

## 错误处理

```java
import com.uav.sdk.exception.UavApiException;
import com.uav.sdk.exception.UavAuthException;

try {
    WeatherGrid weather = client.weather().queryPoint(request);
} catch (UavAuthException e) {
    // API Key 无效或签名错误
    System.err.println("Auth failed: " + e.getMessage());
} catch (UavApiException e) {
    // API 返回错误
    System.err.println("API error: " + e.getStatusCode() + " - " + e.getMessage());
}
```

## 异步调用

```java
import java.util.concurrent.CompletableFuture;

CompletableFuture<WeatherGrid> future = client.weather().queryPointAsync(request);
future.thenAccept(weather -> {
    System.out.println("Async result: " + weather.getTemperature());
});
```

## WebSocket 实时订阅

```java
import com.uav.sdk.ws.UavWebSocketClient;

UavWebSocketClient wsClient = client.utm().createWebSocketClient();
wsClient.subscribeUavPosition("UAV-001", position -> {
    System.out.println("Position update: " + position);
});
wsClient.subscribeAlerts(alert -> {
    System.out.println("Alert: " + alert);
});
```

## 配置参考

| 属性 | 默认值 | 说明 |
|------|--------|------|
| `baseUrl` | — | API 基础 URL |
| `apiKey` | — | API Key |
| `apiSecret` | — | API Secret |
| `timeoutSeconds` | 30 | 请求超时（秒） |
| `maxRetries` | 3 | 最大重试次数 |
| `retryIntervalMs` | 1000 | 重试间隔（毫秒） |
| `connectionPoolSize` | 10 | HTTP 连接池大小 |

## 版本兼容性

| SDK 版本 | 平台版本 | JDK |
|----------|----------|-----|
| 2.0.1 | 2.0.1 | 21+ |
| 2.0.0 | 2.0.0 | 21+ |

## 许可证

MIT License
