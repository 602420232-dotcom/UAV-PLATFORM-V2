# UAV Common Utilities Module

## 📋 模块概述

`common-utils` 是 UAV Path Planning System 的公共工具模块，提供跨服务的通用功能、安全配置、异常处理和弹性机制。

**Maven坐标**:
```xml
<dependency>
    <groupId>com.uav</groupId>
    <artifactId>common-utils</artifactId>
    <version>${project.version}</version>
</dependency>
```

---

## 📦 模块结构

```
common-utils/
├── src/
│   ├── main/
│   │   ├── java/com/uav/common/
│   │   │   ├── audit/           # 安全审计
│   │   │   ├── config/          # 配置类
│   │   │   ├── dto/             # 数据传输对象
│   │   │   ├── exception/       # 异常处理 ⭐ HTTP状态码支持
│   │   │   ├── resilience/       # 弹性机制 ⭐
│   │   │   ├── security/         # 安全认证
│   │   │   └── utils/           # 工具类
│   │   └── resources/
│   │       ├── application.yml
│   │       └── resilience4j-circuitbreaker.yml  # 熔断器配置
│   └── test/                     # 单元测试
├── pom.xml
└── README.md
```

---

## ✨ 核心功能

### 🔐 1. 安全认证 (`security/`)

| 类 | 功能 | 说明 |
:|---|------|------|
| `JwtAuthenticationFilter` | JWT认证过滤器 | Token验证、用户认证 |
| `JwtSecurityConfig` | JWT安全配置 | Token生成、验证 |
| `CookieCsrfTokenRepository` | CSRF Token存储 | Cookie存储CSRF Token |
| `CsrfOriginFilter` | CSRF来源验证 | HTTP Origin检查 |

**特性**:
- ✅ JWT Token生成和验证
- ✅ 生产环境强制密钥配置
- ✅ CSRF保护（启用状态）
- ✅ CORS配置

**配置示例**:
```yaml
uav:
  jwt:
    enabled: true
    secret: ${JWT_SECRET}  # 必需：至少32字符
    expiration: 86400000   # 24小时
```

### 🛡️ 2. 弹性机制 (`resilience/`) ⭐

| 类 | 功能 | 说明 |
:|---|------|------|
| `ResilienceConfig` | 熔断器配置 | CircuitBreaker/Retry/TimeLimiter |
| `CircuitBreakerService` | 服务调用封装 | 带熔断保护的HTTP调用 |
| `CircuitBreakerController` | 熔断器监控API | 状态查询、手动控制 |

**熔断器保护**:
- ✅ `meteor-forecast-service` - 气象预报服务
- ✅ `path-planning-service` - 路径规划服务
- ✅ `data-assimilation-service` - 数据同化服务

**使用示例**:
```java
@Autowired
private CircuitBreakerService circuitBreakerService;

public void callService() {
    try {
        ResponseEntity<Result> response = 
            circuitBreakerService.callMeteorForecast(url, Result.class);
    } catch (ServiceUnavailableException e) {
        // 降级处理
        return getFallback();
    }
}
```

### 🛑 3. 异常处理 (`exception/`) - HTTP状态码支持 ⭐

| 类 | 功能 | 默认状态码 | 可自定义 |
:|---|------|:--------:|:-------:|
| `BusinessException` | 业务异常 | 400 | ✅ |
| `DataNotFoundException` | 数据未找到 | 404 | - |
| `ServiceUnavailableException` | 服务不可用/熔断器 | 503 | ✅ |
| `PythonExecutionException` | Python执行异常 | 500 | - |
| `GlobalExceptionHandler` | 全局异常处理器 | - | ✅ |

**所有异常处理器都返回正确的HTTP状态码**

**BusinessException 工厂方法**:
```java
// 400 - 参数错误
throw BusinessException.badRequest("ERR_001", "参数不合法");

// 401 - 未认证
throw BusinessException.unauthorized("ERR_002", "请先登录");

// 403 - 权限不足
throw BusinessException.forbidden("ERR_003", "无权访问此资源");

// 404 - 资源不存在
throw BusinessException.notFound("ERR_004", "数据未找到");

// 409 - 资源冲突
throw BusinessException.conflict("ERR_005", "数据已存在");

// 422 - 无法处理的实体
throw BusinessException.unprocessableEntity("ERR_006", "数据格式错误");

// 429 - 请求过多
throw BusinessException.tooManyRequests("ERR_007", "请求过于频繁");

// 500 - 服务器内部错误
throw BusinessException.internal("ERR_008", "服务器内部错误");

// 自定义状态码
throw new BusinessException("CUSTOM_CODE", "错误信息", HttpStatus.NOT_FOUND);
```

**GlobalExceptionHandler 响应格式**:
```json
{
  "success": false,
  "error": "错误信息",
  "code": "ERR_CODE",
  "httpStatus": 400
}
```

**ServiceUnavailableException 工厂方法** (用于熔断器):
```java
// 503 - 服务不可用
throw ServiceUnavailableException.serviceDown("meteor-service", "服务维护中");

// 504 - 网关超时
throw ServiceUnavailableException.gatewayTimeout("planning-service", "服务响应超时");

// 502 - 网关错误
throw ServiceUnavailableException.badGateway("data-service", "服务异常");

// 熔断器打开
throw ServiceUnavailableException.circuitBreakerOpen("forecast-service");
```

### 📊 4. 数据传输对象 (`dto/`)

| 类 | 用途 |
:|------|
| `AssimilationRequest` | 数据同化请求 |
| `ForecastRequest` | 气象预报请求 |
| `PathPlanningRequest` | 路径规划请求 |

**验证特性**:
```java
public class AssimilationRequest {
    @NotNull(message = "数据不能为空")
    private Object data;
    
    @Size(min = 1, max = 100, message = "位置数量应在1-100之间")
    private List<double[]> locations;
    
    @Min(value = 0, message = "时间戳不能为负数")
    private Long timestamp;
}
```

### ⚙️ 5. 配置类 (`config/`)

| 类 | 功能 |
:|------|
| `CommonSecurityConfig` | 通用安全配置（CSRF/CORS） |
| `NacosConfigRefresher` | Nacos配置动态刷新 |

**CORS配置**:
```java
@Configuration
@EnableWebSecurity
public class CommonSecurityConfig {
    // ✅ CORS已配置，支持指定域名
    // ✅ CSRF已启用，API端点除外
}
```

### 🔍 6. 安全审计 (`audit/`)

| 类 | 功能 |
:|------|
| `SecurityAuditor` | 安全事件记录 |

**审计事件**:
- ✅ 登录成功
- ✅ 登录失败
- ✅ 权限验证
- ✅ 敏感操作

---

## 🚀 快速开始

### 1. 引入依赖

```xml
<dependency>
    <groupId>com.uav</groupId>
    <artifactId>common-utils</artifactId>
    <version>1.0.0</version>
</dependency>
```

### 2. 启用熔断器配置

```yaml
spring:
  config:
    import: optional:classpath:resilience4j-circuitbreaker.yml
```

### 3. 启用安全配置

```java
@SpringBootApplication
@EnableConfigurationProperties
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
```

---

## 📖 API参考

### 熔断器API

| 接口 | 方法 | 说明 |
:|------|------|------|
| `/api/admin/circuit-breaker/status` | GET | 获取所有熔断器状态 |
| `/api/admin/circuit-breaker/details/{name}` | GET | 获取熔断器详细信息 |
| `/api/admin/circuit-breaker/trip/{name}` | POST | 手动触发熔断 |
| `/api/admin/circuit-breaker/reset/{name}` | POST | 手动重置熔断器 |
| `/api/admin/circuit-breaker/health` | GET | 健康检查 |

### 使用示例

```bash
# 查看熔断器状态
curl http://localhost:8080/api/admin/circuit-breaker/status

# 响应示例
{
  "totalBreakers": 3,
  "breakers": [
    {
      "name": "meteor-forecast-service",
      "state": "CLOSED",
      "failureRate": 0.0,
      "successfulCalls": 150,
      "failedCalls": 0
    }
  ]
}
```

---

## 🔧 配置参考

### JWT配置

```yaml
uav:
  jwt:
    enabled: true
    secret: ${JWT_SECRET}                    # 生产环境必需
    secret-min-length: 32                   # 最小32字符
    expiration: 86400000                   # 24小时
```

### 熔断器配置

详细配置请参考: [resilience4j-circuitbreaker.yml](src/main/resources/resilience4j-circuitbreaker.yml)

### CORS配置

```yaml
uav:
  cors:
    allowed-origins:                       # 允许的域名
      - "http://localhost:3000"
      - "https://*.example.com"
    allowed-methods:                       # 允许的方法
      - GET
      - POST
      - PUT
      - DELETE
      - OPTIONS
    allow-credentials: true               # 允许凭证
    max-age: 3600                         # 预检请求缓存时间
```

---

## 📝 单元测试

模块包含完整的单元测试：

| 测试类 | 覆盖范围 |
:|--------|---------|
| `ConfigTests` | 配置测试 |
| `PythonExecutorTest` | Python执行器测试 |
| `PythonScriptInvokerTest` | 脚本调用测试 |
| `AssimilationRequestTest` | DTO验证测试 |
| `DtoValidationTests` | 数据验证测试 |
| `ExceptionTests` | 异常处理测试 |

**运行测试**:
```bash
mvn test -pl common-utils
```

---

## 🔗 依赖关系

```
common-utils
├── Spring Boot Starter Web
├── Spring Boot Starter Security
├── Spring Boot Starter Validation
├── Spring Boot Starter AOP
├── Resilience4j Circuit Breaker
├── Resilience4j Retry
├── Resilience4j Time Limiter
├── JJWT (JWT处理)
├── Lombok
└── JUnit + Mockito (测试)
```

---

## 📚 相关文档

| 文档 | 说明 |
:|------|------|
| [Circuit Breaker Guide](../../docs/CIRCUIT_BREAKER_GUIDE.md) | 熔断器完整使用指南 |
| [Circuit Breaker Examples](../../docs/CIRCUIT_BREAKER_USAGE_EXAMPLES.md) | 代码示例 |
| [Exception HTTP Status Guide](../../docs/EXCEPTION_HTTP_STATUS_GUIDE.md) | 异常处理与HTTP状态码 ⭐ |
| [Improvements Report](../../docs/IMPROVEMENTS_COMPLETED_REPORT.md) | 改进总结 |
| [Security Audit Report](../../docs/security_audit_report.md) | 安全审计报告 |

---

## 🐛 故障排查

### 常见问题

**Q: 熔断器状态为 OPEN？**
```bash
# 查看熔断器详情
curl http://localhost:8080/api/admin/circuit-breaker/details/meteor-forecast-service

# 手动重置
curl -X POST http://localhost:8080/api/admin/circuit-breaker/reset/meteor-forecast-service
```

**Q: JWT验证失败？**
```yaml
# 检查JWT密钥配置
uav:
  jwt:
    secret: ${JWT_SECRET}  # 确保环境变量已设置
```

**Q: CORS跨域问题？**
```yaml
# 检查CORS配置
uav:
  cors:
    allowed-origins:
      - "http://localhost:3000"  # 添加你的前端域名
```


---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
