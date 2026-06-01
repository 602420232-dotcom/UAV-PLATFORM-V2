# 异常处理与HTTP状态码指南

## 📋 概述

本文档说明 common-utils 模块中的异常处理机制，特别是HTTP状态码的支持。

**创建时间**: 2026-05-08  
**版本**: 1.0.0  
**状态**: ✅ **已完成**

---

## 🎯 改进内容

### ✅ BusinessException HTTP状态码支持

**改进前**:
```java
// 只能使用固定的400状态码
throw new BusinessException("ERR_CODE", "错误信息");
```

**改进后** ✅:
```java
// 可以使用任意HTTP状态码
throw new BusinessException("ERR_CODE", "错误信息", HttpStatus.NOT_FOUND);

// 或者使用便捷的工厂方法
throw BusinessException.badRequest("ERR_001", "参数不合法");
throw BusinessException.notFound("ERR_002", "数据未找到");
throw BusinessException.conflict("ERR_003", "数据已存在");
```

### ✅ ServiceUnavailableException HTTP状态码支持

**改进前**:
```java
// 只能使用固定的503状态码
throw new ServiceUnavailableException("service", "服务不可用");
```

**改进后** ✅:
```java
// 可以使用任意HTTP状态码
throw new ServiceUnavailableException("service", "消息", HttpStatus.GATEWAY_TIMEOUT);

// 或者使用便捷的工厂方法
throw ServiceUnavailableException.serviceDown("service", "服务维护中");
throw ServiceUnavailableException.gatewayTimeout("service", "服务响应超时");
throw ServiceUnavailableException.badGateway("service", "服务异常");
throw ServiceUnavailableException.circuitBreakerOpen("service");
```

---

## 📊 异常与HTTP状态码映射

### BusinessException 工厂方法

| 方法 | HTTP状态码 | 使用场景 | 示例 |
|------|----------|---------|------|
| `badRequest()` | 400 | 参数错误、格式错误 | `badRequest("ERR_001", "参数不能为空")` |
| `unauthorized()` | 401 | 未认证、Token无效 | `unauthorized("ERR_002", "请先登录")` |
| `forbidden()` | 403 | 权限不足 | `forbidden("ERR_003", "无权访问")` |
| `notFound()` | 404 | 资源不存在 | `notFound("ERR_004", "用户不存在")` |
| `conflict()` | 409 | 资源冲突 | `conflict("ERR_005", "数据已存在")` |
| `unprocessableEntity()` | 422 | 数据验证失败 | `unprocessableEntity("ERR_006", "数据格式错误")` |
| `tooManyRequests()` | 429 | 请求过于频繁 | `tooManyRequests("ERR_007", "限流中")` |
| `internal()` | 500 | 服务器内部错误 | `internal("ERR_008", "系统错误")` |

### ServiceUnavailableException 工厂方法

| 方法 | HTTP状态码 | 使用场景 | 示例 |
|------|----------|---------|------|
| `serviceDown()` | 503 | 服务维护、暂时不可用 | `serviceDown("user", "服务维护中")` |
| `gatewayTimeout()` | 504 | 网关超时 | `gatewayTimeout("order", "服务响应超时")` |
| `badGateway()` | 502 | 网关错误 | `badGateway("payment", "支付服务异常")` |
| `circuitBreakerOpen()` | 503 | 熔断器打开（推荐） | `circuitBreakerOpen("weather")` |

---

## 🔧 GlobalExceptionHandler 响应格式

所有异常处理器现在都返回统一的JSON响应格式：

### 响应结构

```json
{
  "success": false,
  "error": "错误信息",
  "code": "错误代码",
  "httpStatus": 400
}
```

### 响应示例

**400 Bad Request**:
```json
{
  "success": false,
  "error": "参数不能为空",
  "code": "ERR_001",
  "httpStatus": 400
}
```

**404 Not Found**:
```json
{
  "success": false,
  "error": "用户不存在",
  "code": "ERR_004",
  "httpStatus": 404
}
```

**503 Service Unavailable**:
```json
{
  "success": false,
  "error": "服务暂时不可用",
  "service": "meteor-forecast-service",
  "httpStatus": 503
}
```

---

## 💻 使用示例

### 在Controller中使用

```java
@RestController
@RequestMapping("/api/users")
public class UserController {

    @GetMapping("/{id}")
    public ResponseEntity<User> getUser(@PathVariable Long id) {
        try {
            User user = userService.findById(id);
            if (user == null) {
                // 使用404
                throw BusinessException.notFound("USER_NOT_FOUND", 
                    "用户ID " + id + " 不存在");
            }
            return ResponseEntity.ok(user);
        } catch (BusinessException e) {
            throw e; // 让GlobalExceptionHandler处理
        }
    }

    @PostMapping
    public ResponseEntity<User> createUser(@RequestBody @Valid UserRequest request) {
        // 检查用户名是否存在
        if (userService.existsByUsername(request.getUsername())) {
            // 使用409冲突
            throw BusinessException.conflict("USERNAME_EXISTS", 
                "用户名 " + request.getUsername() + " 已存在");
        }
        
        User user = userService.create(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(user);
    }

    @GetMapping("/profile")
    public ResponseEntity<UserProfile> getProfile() {
        // 检查登录状态
        if (!isAuthenticated()) {
            // 使用401
            throw BusinessException.unauthorized("NOT_AUTHENTICATED", 
                "请先登录");
        }
        
        // 检查权限
        if (!hasPermission("VIEW_PROFILE")) {
            // 使用403
            throw BusinessException.forbidden("INSUFFICIENT_PERMISSION", 
                "无权查看此资料");
        }
        
        return ResponseEntity.ok(getCurrentUserProfile());
    }
}
```

### 在Service中使用

```java
@Service
public class WeatherService {

    @Autowired
    private CircuitBreakerService circuitBreakerService;

    public WeatherData getWeather(String location) {
        try {
            String url = "http://meteor-forecast-service/api/weather/" + location;
            ResponseEntity<WeatherResponse> response = 
                circuitBreakerService.callMeteorForecast(url, WeatherResponse.class);
            return response.getBody().getData();
            
        } catch (ServiceUnavailableException e) {
            // 熔断器打开，使用降级数据
            log.warn("Weather service unavailable, using fallback data");
            return getCachedWeather(location);
        }
    }
}
```

### 在Feign Client中使用

```java
@FeignClient(name = "path-planning-service", fallbackFactory = PathPlanningFallbackFactory.class)
public interface PathPlanningClient {

    @PostMapping("/api/planning/optimize")
    RouteResult optimizeRoute(@RequestBody RouteRequest request);
}

@Component
public class PathPlanningFallbackFactory implements FallbackFactory<PathPlanningClient> {
    
    @Override
    public PathPlanningClient create(Throwable cause) {
        return new PathPlanningClient() {
            @Override
            public RouteResult optimizeRoute(RouteRequest request) {
                if (cause instanceof ServiceUnavailableException) {
                    // 使用503状态码
                    throw ServiceUnavailableException.circuitBreakerOpen(
                        "path-planning-service");
                }
                // 使用500状态码
                throw BusinessException.internal("SERVICE_ERROR", 
                    "路径规划服务调用失败: " + cause.getMessage());
            }
        };
    }
}
```

---

## 🧪 测试验证

### 使用curl测试

```bash
# 测试400错误
curl -X POST http://localhost:8080/api/users \
  -H "Content-Type: application/json" \
  -d '{"username": ""}'
# 响应: HTTP 400 {"success": false, "error": "参数不能为空", "code": "ERR_001", "httpStatus": 400}

# 测试404错误
curl http://localhost:8080/api/users/99999
# 响应: HTTP 404 {"success": false, "error": "用户不存在", "code": "ERR_004", "httpStatus": 404}

# 测试409错误
curl -X POST http://localhost:8080/api/users \
  -H "Content-Type: application/json" \
  -d '{"username": "existing_user"}'
# 响应: HTTP 409 {"success": false, "error": "用户名已存在", "code": "ERR_005", "httpStatus": 409}

# 测试503错误（熔断器打开）
curl http://localhost:8080/api/weather/Beijing
# 响应: HTTP 503 {"success": false, "error": "服务暂时不可用", "service": "meteor-forecast-service", "httpStatus": 503}
```

### 使用Postman测试

1. 创建新请求
2. 设置方法为 `POST`
3. 设置URL为 `http://localhost:8080/api/users`
4. 在Body中选择 `raw` → `JSON`
5. 输入 `{"username": ""}`
6. 点击Send
7. 检查响应状态码是否为 `400`
8. 检查响应Body中的 `httpStatus` 字段是否为 `400`

---

## 📝 全局异常处理器实现

```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<Map<String, Object>> handleBusinessException(
            BusinessException e) {
        log.warn("业务异常: {} - {} (HTTP {})", 
            e.getCode(), e.getMessage(), e.getHttpStatus());
        
        Map<String, Object> body = new HashMap<>();
        body.put("success", false);
        body.put("error", e.getMessage());
        body.put("code", e.getCode());
        body.put("httpStatus", e.getHttpStatus().value());
        
        return ResponseEntity.status(e.getHttpStatus()).body(body);
    }

    @ExceptionHandler(ServiceUnavailableException.class)
    public ResponseEntity<Map<String, Object>> handleServiceUnavailable(
            ServiceUnavailableException e) {
        log.error("服务不可用: {} - {} (HTTP {})", 
            e.getServiceName(), e.getMessage(), e.getHttpStatus());
        
        Map<String, Object> body = new HashMap<>();
        body.put("success", false);
        body.put("error", "服务暂时不可用");
        body.put("service", e.getServiceName());
        body.put("httpStatus", e.getHttpStatus().value());
        
        return ResponseEntity.status(e.getHttpStatus()).body(body);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, Object>> handleValidationErrors(
            MethodArgumentNotValidException e) {
        String message = e.getBindingResult().getFieldErrors().stream()
            .map(FieldError::getDefaultMessage)
            .collect(Collectors.joining(", "));
        
        return ResponseEntity.badRequest().body(Map.of(
            "success", false,
            "error", message,
            "code", "VALIDATION_ERROR",
            "httpStatus", 400
        ));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleGenericException(Exception e) {
        log.error("未处理的异常", e);
        
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(Map.of(
                "success", false,
                "error", "服务器内部错误",
                "code", "INTERNAL_ERROR",
                "httpStatus", 500
            ));
    }
}
```

---

## 🔗 相关文档

- [Circuit Breaker Guide](CIRCUIT_BREAKER_GUIDE.md) - 熔断器完整使用指南
- [Circuit Breaker Examples](CIRCUIT_BREAKER_USAGE_EXAMPLES.md) - 代码示例
- [common-utils README](../common-utils/README.md) - 模块文档


---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
