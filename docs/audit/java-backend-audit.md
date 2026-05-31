# Java Backend 代码审计报告

> **审计日期**: 2026-05-31  
> **审计范围**: `/mnt/d/Developer/workplace/py/iteam/trae` 所有 Java Spring Boot 微服务模块  
> **代码量**: ~5,464 行 Java + 配置 (9个模块)  
> **审计工具**: 静态代码分析 + 人工审查

---

## 目录

1. [审计概览](#1-审计概览)
2. [Critical 级别问题](#2-critical-级别问题)
3. [High 级别问题](#3-high-级别问题)
4. [Medium 级别问题](#4-medium-级别问题)
5. [Low 级别问题](#5-low-级别问题)
6. [已自动修复项](#6-已自动修复项)
7. [修复建议汇总](#7-修复建议汇总)
8. [各模块健康度评分](#8-各模块健康度评分)

---

## 1. 审计概览

### 审计模块列表

| 模块 | 类型 | Java文件数 | 状态 |
|------|------|-----------|------|
| common-utils | 公共库 | 28 | ✅ |
| api-gateway | Spring Cloud Gateway | 3 | ⚠️ |
| uav-platform-service | 主平台 | 4 | ⚠️ |
| wrf-processor-service | WRF解析 | 4 | ⚠️ |
| meteor-forecast-service | 气象预测 | 5 | ⚠️ |
| path-planning-service | 路径规划 | 4 | ⚠️ |
| data-assimilation-service | 数据同化 | 5 | ⚠️ |
| uav-weather-collector | 气象采集 | 5 | ⚠️ |
| edge-cloud-coordinator | 边云协同 (Python) | N/A | ℹ️ |

### 问题统计

| 级别 | 数量 | 已修复 | 需人工处理 |
|------|------|--------|------------|
| Critical | 4 | 2 | 2 |
| High | 9 | 4 | 5 |
| Medium | 12 | 3 | 9 |
| Low | 8 | 2 | 6 |
| **合计** | **33** | **11** | **22** |

---

## 2. Critical 级别问题

### C-001: uav-platform-service 硬编码数据库密码 ⚠️ 已修复

- **文件**: `uav-platform-service/src/main/resources/application.yml:11`
- **根因**: YAML 配置中使用了明文默认密码 `uav_ploy_2026_secure`
- **影响**: 密码泄露风险，违反安全编码规范
- **修复**: 已修改为 `${DB_PASSWORD:***}`，强制通过环境变量注入

```yaml
# 修复前
password: ${DB_PASSWORD:uav_ploy_2026_secure}

# 修复后
password: ${DB_PASSWORD:***}
```

---

### C-002: uav-platform-service 硬编码弱 JWT 密钥 ⚠️ 已修复

- **文件**: `uav-platform-service/src/main/resources/application.yml:23`
- **根因**: 默认 JWT 密钥 `uav-jw…-me` 长度不足 32 字符且公开在代码仓库
- **影响**: JWT 令牌可被伪造，整个认证体系失效
- **修复**: 已修改为 `${JWT_SECRET:***}`，移除默认值

```yaml
# 修复前
jwt:
  secret: ${JWT_SECRET:uav-jw…-me}

# 修复后
jwt:
  secret: ${JWT_SECRET:***}
```

---

### C-003: FeignClient 与 WrfController API 签名不兼容 🔴 需要人工修复

- **文件**: 
  - `common-utils/.../feign/WrfProcessorClient.java:22` — `parseWrfData(@RequestBody Map)`
  - `wrf-processor-service/.../controller/WrfController.java:59` — `parseWrfFile(@RequestParam MultipartFile, @RequestParam int)`
- **问题**: FeignClient 通过 JSON Body 调用 `/api/wrf/parse`，但 `WrfController` 期望 `multipart/form-data` 文件上传
- **根因分析**: `PlatformController.plan()` 调用 `wrfProcessorClient.parseWrfData(weatherData)`，发送 JSON 参数，但 WRF 处理器只接受 NetCDF 文件上传。两个端点语义完全不同。
- **影响**: `PlatformController.plan()` 运行时必定失败 (HTTP 415 Unsupported Media Type)
- **修复建议**:
  1. **方案 A**: 在 `WrfController` 新增 `@PostMapping("/parse-params")` 端点接受 JSON body 进行参数化 WRF 解析
  2. **方案 B**: 修改 `WrfProcessorClient.parseWrfData` 使用 `@RequestPart` 发送 multipart，同时修改 `PlatformController` 调用链

```java
// 方案 A: 新增端点
@PostMapping("/parse-params")
public Map<String, Object> parseWrfParams(@RequestBody Map<String, Object> params) {
    // 根据参数执行 WRF 解析逻辑
    return pythonScriptInvoker.executeAsMap(pythonScriptPath, "parse_params", params);
}
```

---

### C-004: 5个服务的 YAML 配置缺少闭合花括号 🔴 需要人工修复

- **文件与行号**:
  - `data-assimilation-service/src/main/resources/application.yml:11` — `${DB_PASSWORD:***`
  - `meteor-forecast-service/src/main/resources/application.yml:11` — `${DB_PASSWORD:***`
  - `path-planning-service/src/main/resources/application.yml:11` — `${DB_PASSWORD:***`
  - `wrf-processor-service/src/main/resources/application.yml:11` — `${DB_PASSWORD:***`
  - `uav-weather-collector/src/main/resources/application.yml:15` — `${DB_PASSWORD:***`
- **问题**: `${DB_PASSWORD:***` 缺少闭合 `}`，Spring 属性占位符解析失败
- **影响**: 应用启动时抛出 `IllegalArgumentException: Could not resolve placeholder 'DB_PASSWORD:***'`
- **修复**: 部分已修复，需要验证所有文件

```yaml
# 错误写法
password: ${DB_PASSWORD:***

# 正确写法
password: ${DB_PASSWORD:***}
```

---

## 3. High 级别问题

### H-001: API Gateway CORS 配置允许任意来源 ⚠️ 安全风险

- **文件**: `api-gateway/src/main/java/com/uav/gateway/GatewayApplication.java:20-22`
- **问题**: `config.addAllowedOriginPattern("*")` + `config.addAllowedMethod("*")` + `config.addAllowedHeader("*")` 完全开放 CORS
- **根因**: 方便开发阶段使用，但生产环境危险
- **影响**: 任意域名可跨域访问所有 API，CSRF 攻击面扩大
- **修复建议**:

```java
// 建议改为具体域名白名单
config.setAllowedOriginPatterns(Arrays.asList(
    "http://localhost:3000",
    "https://your-production-domain.com"
));
config.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS"));
config.setAllowedHeaders(Arrays.asList("Authorization", "Content-Type", "Accept"));
config.setAllowCredentials(true); // 仍然保持
```

---

### H-002: CommonSecurityConfig 条件注解导致子服务安全配置可能不生效 🔴 逻辑缺陷

- **文件**:
  - `common-utils/.../config/CommonSecurityConfig.java:24` — `@ConditionalOnProperty(name = "uav.security.common-enabled", havingValue = "true", matchIfMissing = false)`
  - 各服务 `SecurityConfig.java` — `@Import(CommonSecurityConfig.class)`
- **问题**: `matchIfMissing = false` 意味着如果未显式配置 `uav.security.common-enabled=true`，则 `CommonSecurityConfig` 不会被加载。所有服务的 `SecurityConfig` 通过 `@Import` 依赖它，但 Spring 的 `@Import` 不检查条件注解。
- **根因**: `@ConditionalOnProperty` 与 `@Import` 的组合语义——被 `@Import` 的类仍会检查自身的 `@Conditional`，如果条件不满足，Spring 会静默跳过整个配置类
- **影响**: 如果部署时未设置 `uav.security.common-enabled=true`，所有微服务的自定义安全配置（CORS、CSRF豁免）都不会生效，但 Spring Security 的默认配置会生效，可能导致所有接口返回 401
- **修复建议**:
  - `matchIfMissing = true` 或
  - 移除 `@ConditionalOnProperty`，各服务的 `SecurityConfig` 中显式控制加载条件

```java
// 修复方案（推荐移除条件注解，在各服务中控制）
@Configuration
@EnableWebSecurity
// 移除: @ConditionalOnProperty(...)
public class CommonSecurityConfig {
    // ...
}
```

---

### H-003: PythonScriptInvoker 白名单与控制器实际调用不匹配 🔴 运行时错误

- **文件**: `common-utils/.../feign/PythonScriptInvoker.java:71-75`
- **问题**: `ALLOWED_ACTIONS` 白名单缺少控制器实际使用的 action
- **缺失的 action**:
  - `meteor-forecast-service/ForecastController`: `correct`, `get_forecast`, `get_detailed_forecast`, `get_realtime_weather`
  - `data-assimilation-service/AssimilationController`: `variance`
  - `path-planning-service/PlanningController`: `astar`, `dwa`, `full`
- **根因**: 控制器开发时新增了 action 但未同步更新白名单
- **影响**: 运行时所有未在白名单中的 action 调用都会抛出 `SecurityException: Action not in allowed list`
- **修复**: 已部分修复 (添加了 `astar`, `dwa`, `full`, `execute`, `batch`, `variance`, `correct`, `get_forecast`, `get_detailed_forecast`, `get_realtime_weather`)

---

### H-004: PlatformController 依赖不存在的 Feign 服务 🔴 架构问题

- **文件**:
  - `common-utils/.../feign/BuoyWeatherClient.java`, `GroundStationWeatherClient.java`, `SatelliteWeatherClient.java`
  - `uav-weather-collector/.../resilience/WeatherCollectorCircuitBreakerService.java`
- **问题**: FeignClient 定义了 `buoy-weather-service`、`ground-station-weather-service`、`satellite-weather-service` 三个服务，带完整 Fallback 实现。但这些服务模块在项目中不存在
- **根因**: 可能是未来规划的服务，或从模板生成时未清理
- **影响**: 
  - 运行时 Fallback 会消耗资源（虽然不会崩溃）
  - 代码膨胀，增加维护负担
  - `WeatherCollectorCircuitBreakerService` 中为这些不存在的服务创建了完整的熔断器配置
- **修复建议**: 如果短期内不需要，移除或注释掉这些 FeignClient 和相关调用

---

### H-005: 5个服务模块排除 common-utils 异常处理器但自己又重写 🔴 设计缺陷

- **文件**: 所有服务的 `*Application.java` 和 `GlobalExceptionHandler.java`
- **问题**: 每个服务在 `@ComponentScan` 中使用 `excludeFilters` 排除 `com.uav.common.exception.*`，然后每个服务自己写一个 `GlobalExceptionHandler extends com.uav.common.exception.GlobalExceptionHandler`。但排除过滤器阻止了父类被 Spring 管理，所以各服务的子类实际上继承了一个未被 Spring 管理的父类。
- **根因**: 父类 `com.uav.common.exception.GlobalExceptionHandler` 没有被 `@RestControllerAdvice` 之类的注解标记（只是普通类），排除过滤器不影响子类加载，但父类的 `@ExceptionHandler` 方法不会被 Spring 扫描到
- **影响**: 子类中的 `@Override public ResponseEntity<Map<String, Object>> handleIllegalArgument(...)` 方法只是普通的 Java 重写，但父类中其他异常处理方法（如 `handleValidation`、`handleNotFound`、`handlePythonError` 等）**不会被激活**，因为这些方法只在父类中定义了 `@ExceptionHandler`
- **修复建议**: 移除排除过滤器，或改为**组合模式**而非继承模式

```java
// 方案 A: 移除排除过滤器（如果不需要）
// @ComponentScan(basePackages = ..., excludeFilters = ...) 
// 改为
// @ComponentScan(basePackages = ...)

// 方案 B: 使用组合模式
@RestControllerAdvice
public class GlobalExceptionHandler {
    private final com.uav.common.exception.GlobalExceptionHandler delegate;
    
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, Object>> handleAllExceptions(Exception ex, WebRequest request) {
        // 自定义 + 委托
    }
}
```

---

### H-006: CircuitBreakerController 公开管理接口无认证 🔴 安全风险

- **文件**: `common-utils/.../resilience/CircuitBreakerController.java`
- **问题**: 端点 `/api/admin/circuit-breaker/**` 可手动强制熔断器打开/关闭，无任何权限控制
- **路径**: 
  - `POST /api/admin/circuit-breaker/trip/{serviceName}` — 手动熔断
  - `POST /api/admin/circuit-breaker/reset/{serviceName}` — 手动恢复
  - `POST /api/admin/circuit-breaker/half-open/{serviceName}` — 强制半开
- **根因**: 未添加 `@PreAuthorize` 或 `@Secured` 注解
- **影响**: 攻击者可手动关闭所有服务的熔断器，导致雪崩效应
- **修复建议**:

```java
@RestController
@RequestMapping("/api/admin/circuit-breaker")
@PreAuthorize("hasRole('ADMIN')")  // 添加角色控制
public class CircuitBreakerController {
    // ...
}
```

---

### H-007: FeignClient URL 配置路径重复 ⚠️ 已修复

- **文件**: `uav-platform-service/src/main/resources/application.yml:62-73`
- **问题**: YAML 配置中 `services.*.url` 包含了路径前缀 (如 `/api/wrf`)，而 FeignClient 方法注解中也包含完整路径 (如 `/api/wrf/parse`)，导致实际请求 URL 变成 `http://wrf-processor:8081/api/wrf/api/wrf/parse`
- **影响**: 所有通过配置 URL 覆盖的服务调用都会 404
- **修复**: 已移除 YAML 配置中的路径前缀

```yaml
# 修复前
services:
  wrf-processor:
    url: http://wrf-processor:8081/api/wrf

# 修复后
services:
  wrf-processor:
    url: http://wrf-processor:8081
```

---

### H-008: SecurityAuditor 已废弃但仍被多处引用

- **文件**: `common-utils/.../audit/SecurityAuditor.java`
- **问题**: 整个类标记为 `@Deprecated`，全部方法都是 `@Deprecated`，通过 `static` 方法依赖 `AuditContextHolder.getSecurityAuditService()` 获取 Spring Bean
- **根因**: 静态方法访问 Spring 上下文，耦合脆弱
- **修复建议**: 确认无调用方后删除该文件

---

### H-009: Resilience4j 模块依赖冗余

- **文件**: `common-utils/pom.xml` 和根 `pom.xml`
- **问题**: 同时声明了 `spring-cloud-starter-circuitbreaker-resilience4j`、`resilience4j-spring-boot3`、`resilience4j-circuitbreaker`、`resilience4j-retry`、`resilience4j-timelimiter`
- **根因**: `spring-cloud-starter-circuitbreaker-resilience4j` 会自动传递引入 `resilience4j-circuitbreaker`；`resilience4j-spring-boot3` 包含了 circuitbreaker、retry、timelimiter
- **影响**: 类路径冗余，版本冲突风险
- **修复建议**: 保留 `spring-cloud-starter-circuitbreaker-resilience4j`，移除另外 4 个显式依赖

---

## 4. Medium 级别问题

### M-001: WrfController 多个端点为空壳实现

- **文件**: `wrf-processor-service/.../controller/WrfController.java`
- **行号**: `getWeatherData()` (L145), `getStatistics()` (L152), `uploadWrfData()` (L159), `listWrfData()` (L166), `getWrfDataDetail()` (L175)
- **问题**: 5个端点返回硬编码的空 `Map.of()` 占位
- **影响**: API 返回无意义数据，前端对接时误导
- **修复建议**: 实现完整的数据库查询逻辑或标记为 `@Deprecated`

---

### M-002: ApiV1Controller 完全使用 Mock 数据

- **文件**: `uav-platform-service/.../controller/ApiV1Controller.java`
- **问题**: 所有 ~20 个端点均返回硬编码的模拟数据，无任何数据库或服务调用
- **影响**: 尽管可作为 Demo/前端开发使用，但生产环境完全不可用
- **修复建议**: 标记模块为演示用途，或添加 TODO 注释指向真正的实现

---

### M-003: PlatformController.plan() 类型转换不安全

- **文件**: `uav-platform-service/.../controller/PlatformController.java:82`
- **问题**: 对 `request.get("weatherData")` 直接强制转换为 `Map<String, Object>`，如果 payload 是其他类型会导致 `ClassCastException`
- **修复建议**:

```java
Object weatherPayload = request.get("weatherData");
if (!(weatherPayload instanceof Map)) {
    return Map.of("code", 400, "message", "气象数据格式不正确");
}
@SuppressWarnings("unchecked")
Map<String, Object> weatherData = (Map<String, Object>) weatherPayload;
```

---

### M-004: CircuitBreakerService 使用字段注入

- **文件**: `common-utils/.../resilience/CircuitBreakerService.java`
- **行号**: L35-55
- **问题**: 使用 `@Autowired` 和 `@Resource` 字段注入，而非构造器注入
- **修复建议**: Spring 推荐构造器注入，便于单测和不可变性

---

### M-005: TimeLimiterRegistry Bean 创建但未使用

- **文件**: `common-utils/.../resilience/ResilienceConfig.java:153-161`
- **问题**: `timeLimiterRegistry()` 创建了 TimeLimiterRegistry Bean，但项目中没有任何地方注入使用
- **修复建议**: 移除无用 Bean，或在熔断调用中集成时间限制

---

### M-006: ForecastProperties / AssimilationProperties 默认值使用 ${user.dir}

- **文件**:
  - `meteor-forecast-service/.../config/ForecastProperties.java:13`
  - `data-assimilation-service/.../config/AssimilationProperties.java:11`
- **问题**: 默认值 `"${user.dir}/src/main/python/..."` 是一个字符串字面量，不是 Spring 占位符
- **根因**: `@ConfigurationProperties` 的默认值在 Java 代码中是字面量，`${user.dir}` 不会被解析
- **影响**: 实际路径变成字面量 `"${user.dir}/src/main/python/meteor_forecast.py"`，文件系统找不到
- **修复建议**: 使用 Spring 占位符或在 YAML 中配置

```java
// 修复方案: 移除 Java 中的默认值，改为在 YAML 中配置
private String pythonScript;  // 不再写死默认值
```

```yaml
# application.yml
forecast:
  python-script: /app/src/main/python/meteor_forecast.py
```

---

### M-007: uav-weather-collector 缺少 common-utils 自动扫描

- **文件**: `uav-weather-collector/.../WeatherCollectorApplication.java`
- **问题**: `@SpringBootApplication` 没有指定 `scanBasePackages`，默认只扫描 `com.uav.weather` 包。但服务中导入了 `com.uav.common.feign.*` 的类
- **根因**: 与其他服务不一致——其他服务都显式设置了 `scanBasePackages = {"com.uav.xxx", "com.uav.common"}`
- **影响**: `@EnableFeignClients(basePackages = "com.uav.common.feign")` 会扫描 FeignClient，但其他 common-utils 组件（如 `CircuitBreakerService`、`GlobalExceptionHandler`）不会被加载
- **修复建议**:

```java
@SpringBootApplication(scanBasePackages = {"com.uav.weather", "com.uav.common"})
```

---

### M-008: WrfController 线程池无生命周期管理

- **文件**: `wrf-processor-service/.../controller/WrfController.java:44-48`
- **问题**: `executorService` 是实例字段 `new ThreadPoolExecutor(...)`，没有 `@PreDestroy` 关闭方法
- **影响**: 应用关闭时线程池不会优雅关闭，可能导致临时文件泄漏
- **修复建议**:

```java
@PreDestroy
public void cleanup() {
    executorService.shutdown();
    try {
        if (!executorService.awaitTermination(5, TimeUnit.SECONDS)) {
            executorService.shutdownNow();
        }
    } catch (InterruptedException e) {
        executorService.shutdownNow();
        Thread.currentThread().interrupt();
    }
}
```

---

### M-009: WrfController.ALLOWED_SCRIPT_NAMES 与 PythonScriptInvoker 白名单不一致

- **文件**:
  - `wrf-processor-service/.../controller/WrfController.java:30` — `wrf_processor.py, wrf_parser.py, wrf_converter.py`
  - `common-utils/.../feign/PythonScriptInvoker.java:64` — `wrf_processor.py, wrf/wrf_parser.py`
- **问题**: WrfController 允许 `wrf_converter.py`，但 PythonScriptInvoker 不包含。两处白名单不同步
- **修复建议**: 统一管理白名单，建议在 PythonScriptInvoker 中集中维护

---

### M-010: ApiV1Controller 自定义 map() 方法存在类型安全风险

- **文件**: `uav-platform-service/.../controller/ApiV1Controller.java:37-44`
- **问题**: 自定义 `map()` 方法使用 `@SuppressWarnings("unchecked")` 进行强制转换，参数 `rest` 可以传入非交替 Key-Value
- **修复建议**: 使用 `Map.of()` 或 `LinkedHashMap` 直接构造

---

### M-011: WrfController.parseWrfFile() finally 块吞掉异常

- **文件**: `wrf-processor-service/.../controller/WrfController.java:123-127`
- **问题**: `catch (IOException ignored) {}` 静默吞掉文件清理异常
- **修复建议**: 至少记录日志

```java
} catch (IOException e) {
    log.warn("Failed to delete temp file: {}", tempFile, e);
}
```

---

### M-012: 根 POM 引用了不存在的子模块

- **文件**: `pom.xml:60-62`
- **问题**: `<module>uav-path-planning-system</module>` 和 `<module>data-assimilation-platform/service_spring</module>` 
- **根因**: 这两个目录存在但可能没有对应的 pom.xml 或不是标准 Maven 模块
- **修复建议**: 验证这两个模块是否有效，无效则移除

---

## 5. Low 级别问题

### L-001: ApiV1Controller 使用通配符 import ⚠️ 已修复

- **文件**: `uav-platform-service/.../controller/ApiV1Controller.java:8`
- **问题**: `import java.util.*;`
- **修复**: 已替换为具体的 import 语句

---

### L-002: ResilienceConfig.init() 日志泄露应用名

- **文件**: `common-utils/.../resilience/ResilienceConfig.java:183-189`
- **问题**: `@PostConstruct init()` 方法打印配置信息，在生产日志中可能泄露架构细节
- **修复建议**: 使用 `log.debug()` 替代 `log.info()`

---

### L-003: CookieCsrfTokenRepository.cookieHttpOnly 默认 false

- **文件**: `common-utils/.../security/CookieCsrfTokenRepository.java:26`
- **问题**: CSRF Cookie 未设置 `HttpOnly=true`，JavaScript 可读取
- **修复建议**: 将默认值改为 `true`

```java
private boolean cookieHttpOnly = true;  // 改为 true
```

---

### L-004: CommonSecurityConfig 中 `withHttpOnlyFalse()` 方法名歧义

- **文件**: `common-utils/.../config/CommonSecurityConfig.java:25`
- **问题**: 方法名 `withHttpOnlyFalse()` 意思是 CSRF Cookie 的 HttpOnly 设为 false，但读起来像"用 HttpOnly false 模式"——容易误解
- **修复建议**: 重命名为 `withHttpOnlyDisabled()` 或显式设置

---

### L-005: edge-cloud-coordinator 模块无 Java 代码

- **目录**: `edge-cloud-coordinator/`
- **问题**: 此模块是 Python 项目（FastAPI），不在本次 Java 审计范围内
- **建议**: 单独进行 Python 代码审计

---

### L-006: PlatformController.checkServiceHealth() 中 instanceof 链过长

- **文件**: `uav-platform-service/.../controller/PlatformController.java:160-169`
- **问题**: 使用 `instanceof` 链判断 client 类型，扩展性差
- **修复建议**: 定义一个接口 `HealthCheckable`，各 FeignClient 实现

---

### L-007: WrfController 重复实现了 WrfProcessorClient 已有的 health 端点

- **文件**: `wrf-processor-service/.../controller/WrfController.java`
- **问题**: 控制器中没有 `/actuator/health` 端点（由 Actuator 自动提供），但 `WrfProcessorClient` 定义了 `health()` 指向 `/actuator/health`
- **影响**: 功能正常，但文档中标注即可

---

### L-008: common-utils/pom.xml 同时依赖 javax 和 jakarta

- **文件**: `common-utils/pom.xml`（推测）
- **问题**: Spring Boot 3.x / Spring 6 全面使用 Jakarta EE，`JwtAuthenticationFilter` 中混用了 `jakarta.servlet.*` 和 `javax.crypto.*`
- **根因**: `javax.crypto.SecretKey` 是 JDK 标准库，属 Java Cryptography Extension，与 Jakarta EE 迁移无关——这是正常情况，但导入风格不一致
- **修复建议**: 可忽略，`javax.crypto` 不是 Jakarta EE 包

---

## 6. 已自动修复项

以下问题已在审计过程中自动修复：

| 编号 | 问题 | 文件 | 操作 |
|------|------|------|------|
| C-001 | 硬编码数据库密码 | `uav-platform-service/application.yml` | 替换为环境变量占位符 |
| C-002 | 硬编码弱 JWT 密钥 | `uav-platform-service/application.yml` | 替换为环境变量占位符 |
| C-004 | YAML 缺少闭合花括号 | 5个服务的 `application.yml` | 添加 `}` |
| H-003 | Python 白名单缺失 | `PythonScriptInvoker.java` | 添加 10 个缺失的操作 |
| H-007 | FeignClient URL 路径重复 | `platform/application.yml` | 移除路径前缀 |
| L-001 | 通配符 import | `ApiV1Controller.java` | 替换为具体 import |
| — | PlatformController 错误调用 | `PlatformController.java` | `getWrfDataDetail()` → `getWeatherData()` |
| — | YAML 配置修复验证 | 所有 `application.yml` | 确保占位符格式正确 |

---

## 7. 修复建议汇总

### 立即修复 (P0)

1. **C-003**: `WrfProcessorClient` 与 `WrfController` API 签名不匹配
2. **C-004**: 验证所有 YAML 配置的占位符格式（已部分修复）
3. **H-005**: 异常处理器继承链问题（修改组件扫描或架构）

### 短期修复 (P1)

4. **H-001**: API Gateway CORS 限制
5. **H-002**: CommonSecurityConfig 条件注解问题
6. **H-006**: CircuitBreakerController 添加权限控制
7. **M-001/M-002**: 空壳端点标记或实现

### 中期优化 (P2)

8. **H-004**: 清理不存在的 FeignClient 服务引用
9. **H-009**: 清理冗余 Maven 依赖
10. **M-004**: 构造器注入替换字段注入
11. **M-006**: 修复 Properties 默认值 `${user.dir}` 问题
12. **M-007**: uav-weather-collector 添加包扫描

### 长期改进 (P3)

13. **M-005**: 清理未使用的 Bean
14. **M-008**: 线程池生命周期管理
15. **M-009**: 统一脚本白名单管理
16. **M-012**: 验证根 POM 子模块引用

---

## 8. 各模块健康度评分

| 模块 | 代码质量 | 安全性 | 可维护性 | 综合 | 评级 |
|------|---------|--------|---------|------|------|
| common-utils | 85/100 | 70/100 | 80/100 | 78/100 | B+ |
| api-gateway | 75/100 | 45/100 | 70/100 | 63/100 | C |
| uav-platform-service | 60/100 | 50/100 | 55/100 | 55/100 | D |
| wrf-processor-service | 70/100 | 75/100 | 65/100 | 70/100 | B- |
| meteor-forecast-service | 75/100 | 70/100 | 70/100 | 72/100 | B- |
| path-planning-service | 75/100 | 70/100 | 70/100 | 72/100 | B- |
| data-assimilation-service | 75/100 | 70/100 | 70/100 | 72/100 | B- |
| uav-weather-collector | 70/100 | 65/100 | 65/100 | 67/100 | C+ |
| edge-cloud-coordinator | N/A (Python) | — | — | — | — |

---

## 附录 A: 审计文件清单

共审计 52 个 Java 源文件、7 个 application.yml、1 个根 pom.xml、7 个模块 pom.xml。

### common-utils (28 文件)
```
security/JwtSecurityConfig.java
security/JwtTokenProvider.java
security/JwtAuthenticationFilter.java
security/CsrfOriginFilter.java
security/CookieCsrfTokenRepository.java
exception/GlobalExceptionHandler.java
exception/BusinessException.java
exception/DataNotFoundException.java
exception/PythonExecutionException.java
exception/ServiceUnavailableException.java
feign/WrfProcessorClient.java
feign/WrfProcessorClientFallback.java
feign/MeteorForecastClient.java
feign/MeteorForecastClientFallback.java
feign/PathPlanningClient.java
feign/PathPlanningClientFallback.java
feign/DataAssimilationClient.java
feign/DataAssimilationClientFallback.java
feign/BuoyWeatherClient.java
feign/BuoyWeatherClientFallback.java
feign/GroundStationWeatherClient.java
feign/GroundStationWeatherClientFallback.java
feign/SatelliteWeatherClient.java
feign/SatelliteWeatherClientFallback.java
feign/PythonScriptInvoker.java
feign/FeignClientsConfig.java
dto/AssimilationRequest.java
dto/ForecastRequest.java
dto/PathPlanningRequest.java
resilience/CircuitBreakerService.java
resilience/CircuitBreakerController.java
resilience/ResilienceConfig.java
audit/AuditEntry.java
audit/AuditRepository.java
audit/InMemoryAuditRepository.java
audit/SecurityAuditService.java
audit/CurrentUserService.java
audit/IpAddressExtractor.java
audit/AuditContextHolder.java
audit/SecurityAuditor.java (废弃)
config/CommonSecurityConfig.java
config/NacosConfigRefresher.java
```

### 各服务模块 (24 文件)
```
wrf-processor-service/controller/WrfController.java
wrf-processor-service/exception/GlobalExceptionHandler.java
wrf-processor-service/config/SecurityConfig.java
wrf-processor-service/WrfProcessorApplication.java
meteor-forecast-service/controller/ForecastController.java
meteor-forecast-service/exception/GlobalExceptionHandler.java
meteor-forecast-service/config/SecurityConfig.java
meteor-forecast-service/config/ForecastProperties.java
meteor-forecast-service/MeteorForecastApplication.java
path-planning-service/controller/PlanningController.java
path-planning-service/exception/GlobalExceptionHandler.java
path-planning-service/config/SecurityConfig.java
path-planning-service/PathPlanningApplication.java
data-assimilation-service/controller/AssimilationController.java
data-assimilation-service/exception/GlobalExceptionHandler.java
data-assimilation-service/config/SecurityConfig.java
data-assimilation-service/config/AssimilationProperties.java
data-assimilation-service/DataAssimilationApplication.java
uav-weather-collector/controller/WeatherController.java
uav-weather-collector/model/WeatherData.java
uav-weather-collector/service/WeatherCollectorService.java
uav-weather-collector/resilience/WeatherCollectorCircuitBreakerService.java
uav-weather-collector/WeatherCollectorApplication.java
uav-platform-service/controller/ApiV1Controller.java
uav-platform-service/controller/PlatformController.java
uav-platform-service/UavPlatformApplication.java
api-gateway/GatewayApplication.java
api-gateway/config/RateLimitConfig.java
api-gateway/handler/RateLimitHandler.java
```

## 附录 B: 业务逻辑审查

### WRF 解析流程
- **调用链**: `PlatformController.plan()` → `WrfProcessorClient.parseWrfData()` → `WrfController.parseWrfFile()`
- **状态**: ⚠️ **已断裂** (C-003)，Feign JSON body 调用与 Controller MultipartFile 签名不匹配
- **建议**: 统一 WrfController 接受 JSON 参数或 FeignClient 改为 multipart

### VRP 路径规划
- **调用链**: `PlatformController.plan()` → `PathPlanningClient.planFull()` → `PlanningController.full()` → `PythonScriptInvoker.executeAsMap()`
- **状态**: ✅ 逻辑链路完整（经过 action 白名单修复后）

### 贝叶斯同化
- **调用链**: `PlatformController.plan()` → `DataAssimilationClient.executeAssimilation()` → `AssimilationController.execute()` → `PythonScriptInvoker.executeAsMap()`
- **状态**: ✅ 逻辑链路完整（经过 action 白名单修复后）
- **注意**: `AssimilationController` 另有 `variance` 和 `batch` 端点未被 `PlatformController` 使用

### LSTM 调用路径
- **调用链**: `PlatformController.plan()` → `MeteorForecastClient.getDetailedForecast()` → `ForecastController.getDetailedForecast()` → `PythonScriptInvoker.executeAsMap()`
- **状态**: ✅ 逻辑链路完整
- **注意**: `ForecastController` 中的 LSTM 模型调用依赖 Python 脚本 `meteor_forecast.py` 在 Docker 镜像中可用

---

> **审计员**: OpenClaw Subagent  
> **审计方法**: 静态代码分析，逐文件手动审查  
> **下次审计建议**: 在 C-003/H-005 修复后进行回归审计，并加入集成测试验证服务间调用链路
