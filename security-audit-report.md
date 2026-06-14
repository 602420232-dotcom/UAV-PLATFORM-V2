# UAV Platform V2 安全审计报告

**审计日期**: 2026-06-15
**项目版本**: 2.0.0
**审计范围**: 全栈安全审计（Java 后端 / Vue 前端 / Python 算法引擎）
**总体安全评分**: **6.2 / 10** (中等风险)

---

## 一、发现的安全问题总览

| 严重程度 | 数量 |
|----------|------|
| Critical | 3    |
| High     | 5    |
| Medium   | 7    |
| Low      | 4    |
| **合计** | **19** |

---

## 二、安全问题详情（按严重程度排序）

### CRITICAL 级别

#### C-01: JWT 默认密钥硬编码，生产环境可被直接伪造 Token

- **位置**: `common/common-security/src/main/java/com/uav/common/security/service/JwtService.java:30`
- **代码**:
  ```java
  @Value("${security.jwt.secret:uav-platform-default-secret-key-must-be-changed-in-production}")
  private String jwtSecret;
  ```
- **问题**: JWT 签名密钥在代码中提供了明文默认值。如果部署时未通过环境变量 `security.jwt.secret` 覆盖，攻击者可使用此默认密钥伪造任意用户的 JWT Token，获得完全系统访问权限。
- **风险**: 完全认证绕过，可冒充任何用户（包括 ADMIN）。
- **修复建议**:
  1. 移除默认值，改为启动时必须提供：`@Value("${security.jwt.secret}")`，缺失时直接启动失败。
  2. 在应用启动时增加密钥强度校验（至少 256 位 Base64 编码）。
  3. 添加启动时的安全检查，如果检测到使用默认密钥则拒绝启动。

#### C-02: UTM 回调 HMAC 密钥硬编码默认值

- **位置**: `gateway/api-gateway/src/main/java/com/uav/gateway/filter/UtmCallbackFilter.java:39`
- **代码**:
  ```java
  @Value("${gateway.utm.secret:default-secret-key}")
  private String utmSecret;
  ```
- **关联配置**: `gateway/api-gateway/src/main/resources/application.yml:271`
  ```yaml
  secret: ${UTM_SECRET:uav-platform-utm-secret-key-2024}
  ```
- **问题**: UTM 回调的 HMAC 签名验证密钥存在两处默认值（Java 代码和 YAML 配置），攻击者可利用默认密钥伪造合法的 UTM 回调请求，绕过 IP 白名单和签名验证。
- **风险**: 伪造 UTM 系统回调，可能注入虚假的无人机位置数据、飞行计划审批结果等。
- **修复建议**:
  1. 移除所有默认密钥值，强制从环境变量或密钥管理服务读取。
  2. 启动时校验密钥强度。

#### C-03: Actuator 端点未鉴权暴露

- **位置**: `common/common-security/src/main/java/com/uav/common/security/config/SecurityConfig.java:60`
- **代码**:
  ```java
  .requestMatchers(
      "/health",
      "/actuator/**",   // <-- 放行所有 Actuator 端点
      "/swagger-ui/**",
      "/v3/api-docs/**",
      "/api/v1/auth/**",
      "/public/**"
  ).permitAll()
  ```
- **关联配置**: 各服务 `application.yml` 暴露了 `health,info,metrics,prometheus` 端点，Gateway 暴露了 `health,info,gateway,metrics,prometheus`。
- **问题**: `/actuator/**` 被完全放行，无需认证即可访问。`/actuator/gateway` 端点可查看所有路由配置，`/actuator/metrics` 可泄露内部运行指标，`/actuator/prometheus` 暴露详细性能数据。结合已知的 CVE-2026-40976（Spring Boot Actuator CVSS 9.1），可能存在远程代码执行风险。
- **风险**: 信息泄露、潜在远程代码执行。
- **修复建议**:
  1. 将 `/actuator/**` 从 permitAll 中移除，改为需要 `ROLE_ADMIN` 认证。
  2. 仅保留 `/actuator/health` 为公开端点。
  3. 确认 Spring Boot 版本已修复 CVE-2026-40976。

---

### HIGH 级别

#### H-01: CORS 配置过于宽松（通配符 Origin）

- **位置**:
  - `gateway/api-gateway/src/main/java/com/uav/gateway/config/GatewayConfig.java:23`
  - `common/common-web/src/main/java/com/uav/common/web/config/WebConfig.java:20`
  - `gateway/api-gateway/src/main/resources/application.yml:20`
- **代码**:
  ```java
  config.setAllowedOriginPatterns(Collections.singletonList("*"));
  config.setAllowCredentials(true);
  ```
  ```yaml
  allowedOriginPatterns: "*"
  allowCredentials: true
  ```
- **问题**: CORS 配置允许所有来源 (`*`) 并且允许携带凭证 (`allowCredentials: true`)。这意味着任何恶意网站都可以通过 CSRF-like 攻击，利用已登录用户的 Cookie/Token 发起跨域请求。
- **风险**: 跨站请求伪造、敏感数据泄露。
- **修复建议**:
  1. 将 `allowedOriginPatterns` 限定为具体的前端域名列表。
  2. 生产环境禁止使用通配符。

#### H-02: 数据库连接默认密码硬编码

- **位置**: 所有微服务的 `application.yml`（共 6 个服务）
- **代码示例** (`services/weather-api/src/main/resources/application.yml:23`):
  ```yaml
  password: ${MYSQL_PASSWORD:rootpass}
  ```
- **问题**: 所有 6 个微服务（weather、utm、risk、platform、planning、observation）的 MySQL 密码默认值为 `rootpass`。如果部署时未设置环境变量，将使用此弱密码连接数据库。
- **风险**: 数据库未授权访问、数据泄露。
- **修复建议**:
  1. 移除默认密码值，改为 `${MYSQL_PASSWORD}`，缺失时启动失败。
  2. 使用密钥管理服务（如 Vault、AWS Secrets Manager）管理数据库凭证。

#### H-03: 大量业务 API 端点缺少权限注解

- **位置**: 以下控制器中的所有端点均无 `@PreAuthorize` 或 `@RequireApiKey` 注解：
  - `services/weather-api/.../WeatherController.java` - 5 个端点
  - `services/utm-api/.../UavTrackingController.java` - 5 个端点
  - `services/utm-api/.../FlightPlanController.java` - 7 个端点
  - `services/utm-api/.../AirspaceController.java` - 3 个端点
  - `services/risk-api/.../RiskController.java` - 3 个端点
  - `services/risk-api/.../AirworthinessController.java` - 2 个端点
  - `services/planning-api/.../PlanningController.java` - 7 个端点
  - `services/planning-api/.../MpcController.java` - 5 个端点
  - `services/observation-api/.../ObservationController.java` - 4 个端点
  - `services/observation-api/.../ObservationDecisionController.java` - 4 个端点
  - `services/assimilation-api/.../AssimilationController.java` - 5 个端点
  - `services/assimilation-api/.../GprPostprocessController.java` - 2 个端点
  - `services/platform-api/.../ApiKeyController.java` - 6 个端点
  - `services/platform-api/.../UsageController.java` - 2 个端点
- **问题**: 仅有 `TenantController` 使用了 `@PreAuthorize` 注解。其余 **70+ 个 API 端点** 仅依赖 Spring Security 的 `.anyRequest().authenticated()` 进行认证检查，但缺少细粒度的权限控制。任何已认证用户（包括普通租户用户）都可以调用所有业务 API。
- **风险**: 水平越权（普通用户可执行管理操作）、垂直越权（低权限用户访问高权限功能）。
- **修复建议**:
  1. 为所有业务端点添加 `@PreAuthorize("hasPermission(...)")` 或 `@RequireApiKey` 注解。
  2. 建立基于 RBAC 的权限矩阵，确保每个 API 都有对应的权限控制。

#### H-04: Python 边缘安全模块使用不安全的加密实现

- **位置**: `python/algorithm-engine/app/algorithms/edge/edge_security.py:53,73-76,86-88`
- **代码**:
  ```python
  key = params.get("key", "default_secret_key")
  # XOR "encryption" - not real encryption
  encrypted = np.bitwise_xor(data_bytes, np.resize(key_array, data_bytes.shape))
  # ChaCha20 with np.random - predictable seed
  np.random.seed(42)  # Fixed seed!
  key_stream = np.random.randint(0, 256, len(data_bytes), dtype=np.uint8)
  ```
- **问题**:
  1. 使用固定随机种子 `np.random.seed(42)`，ChaCha20 的密钥流完全可预测。
  2. AES 实际使用的是 XOR 而非真正的 AES 加密。
  3. 默认密钥为 `default_secret_key`。
  4. `verify` 操作在 `provided_hash` 为空时直接返回 `is_valid = True`。
- **风险**: 数据加密形同虚设，敏感数据可被轻易解密。
- **修复建议**:
  1. 使用 `cryptography` 库实现真正的 AES-GCM 或 ChaCha20-Poly1305 加密。
  2. 移除固定随机种子，使用 `os.urandom()` 或 `secrets` 模块。
  3. 修复 verify 逻辑，空 hash 应返回 False。

#### H-05: 无 HTTPS/TLS 配置

- **位置**: 所有 `application.yml` 配置文件
- **问题**: 整个项目没有任何 TLS/SSL 终端配置。所有服务间通信（Gateway -> 微服务、微服务 -> MySQL、微服务 -> Redis、微服务 -> Kafka）均使用明文 HTTP 协议。MySQL 连接字符串中明确设置了 `useSSL=false`。
- **风险**: 中间人攻击、数据窃听、凭证截获。
- **修复建议**:
  1. Gateway 配置 SSL 证书，强制 HTTPS。
  2. 服务间通信启用 mTLS 或至少使用 TLS。
  3. MySQL 连接改为 `useSSL=true` 并配置 CA 证书。
  4. Redis 启用 TLS (`rediss://`)。
  5. Kafka 启用 SSL 传输。

---

### MEDIUM 级别

#### M-01: JWT Token 过期时间过长（24 小时）

- **位置**: `common/common-security/src/main/java/com/uav/common/security/service/JwtService.java:33`
- **代码**:
  ```java
  @Value("${security.jwt.expiration:86400000}")  // 24 小时
  private long jwtExpirationMs;
  ```
- **问题**: JWT Token 有效期为 24 小时，且无 Refresh Token 机制。Token 一旦泄露，攻击者在 24 小时内可持续使用。
- **修复建议**:
  1. 缩短 Access Token 有效期至 15-30 分钟。
  2. 实现 Refresh Token 机制（有效期 7 天，支持撤销）。
  3. 添加 Token 黑名单/撤销机制。

#### M-02: UTM 回调 Nonce 重放保护存在内存泄漏风险

- **位置**: `gateway/api-gateway/src/main/java/com/uav/gateway/filter/UtmCallbackFilter.java:51`
- **代码**:
  ```java
  private final Set<String> usedNonces = ConcurrentHashMap.newKeySet();
  ```
- **问题**: `usedNonces` 集合只增不减，没有过期清理机制。长时间运行后会导致内存泄漏。
- **修复建议**:
  1. 使用带有 TTL 的缓存（如 Caffeine 或 Redis）替代纯内存 Set。
  2. 设置 Nonce 过期时间与 `replayWindowSeconds` 一致。

#### M-03: Swagger/OpenAPI 文档端点未鉴权

- **位置**: `common/common-security/src/main/java/com/uav/common/security/config/SecurityConfig.java:61-62`
- **代码**:
  ```java
  "/swagger-ui/**",
  "/v3/api-docs/**",
  ```
- **问题**: Swagger UI 和 OpenAPI 文档在所有环境（包括生产环境）下均公开访问，暴露了完整的 API 结构信息。
- **修复建议**:
  1. 生产环境禁用 Swagger 端点。
  2. 或将其限制为仅管理员可访问。

#### M-04: 缺少日志脱敏机制

- **位置**: 全局
- **问题**:
  1. `RequestLogFilter` 记录了完整的请求路径、客户端 IP、User-Agent，但未对可能包含敏感信息的参数进行脱敏。
  2. `JwtService` 在异常日志中记录了 JWT 错误信息。
  3. `HmacAuthenticationFilter` 日志中记录了 API Key。
  4. 未发现任何 Logback 脱敏配置或自定义脱敏 Filter。
- **修复建议**:
  1. 添加 Logback 脱敏 Pattern（对 password、secret、token 等字段进行掩码）。
  2. 避免在日志中记录完整的 API Key 和 Token。
  3. 对请求参数中的敏感字段进行脱敏。

#### M-05: IP 白名单不支持 CIDR 子网匹配

- **位置**: `gateway/api-gateway/src/main/java/com/uav/gateway/filter/UtmCallbackFilter.java:104-109`
- **代码**:
  ```java
  private boolean isIpWhitelisted(String clientIp) {
      List<String> whitelist = Arrays.asList(whitelistStr.split(","));
      return whitelist.stream().map(String::trim).anyMatch(ip -> ip.equals(clientIp));
  }
  ```
- **问题**: 配置中包含了 CIDR 格式的网段（`10.0.0.0/8,172.16.0.0/12,192.168.0.0/16`），但代码仅做字符串精确匹配，CIDR 格式的网段永远不会匹配成功。实际效果等同于无 IP 白名单限制。
- **修复建议**:
  1. 使用 `org.apache.commons.net.util.SubnetUtils` 或 Spring 的 `IpRange` 实现真正的 CIDR 匹配。

#### M-06: Redis 无密码保护默认配置

- **位置**: 所有 `application.yml` 中的 Redis 配置
- **代码**:
  ```yaml
  password: ${REDIS_PASSWORD:}
  ```
- **问题**: Redis 密码默认为空。如果部署时未设置 `REDIS_PASSWORD` 环境变量，Redis 将无密码保护。
- **修复建议**:
  1. 移除空默认值，强制配置密码。
  2. 生产环境 Redis 启用 ACL 和 TLS。

#### M-07: ApiKeyController 缺少权限控制

- **位置**: `services/platform-api/src/main/java/com/uav/platform/controller/ApiKeyController.java`
- **问题**: API Key 的创建、查询、启用、禁用、删除操作均无 `@PreAuthorize` 注解。任何已认证用户都可以创建 API Key、查看其他租户的 Key、或删除任意 Key。
- **修复建议**:
  1. 所有 API Key 管理操作添加 `@PreAuthorize("hasRole('ADMIN')")` 注解。
  2. 查询操作添加租户隔离校验。

---

### LOW 级别

#### L-01: Spring Boot 4.0.0 / Spring Framework 7.0 为最新大版本，潜在未知漏洞

- **位置**: `pom.xml:10,28`
- **问题**: Spring Boot 4.0.0 和 Spring Framework 7.0 是非常新的主版本（2025 年底发布），可能存在尚未被发现的安全漏洞。已确认存在 CVE-2026-40976（CVSS 9.1）影响 Actuator 端点。
- **修复建议**:
  1. 持续关注 Spring Security 公告。
  2. 尽快升级到已修复 CVE-2026-40976 的版本。
  3. 订阅 Spring Security 邮件列表获取安全更新通知。

#### L-02: MySQL allowPublicKeyRetrieval=true 潜在风险

- **位置**: 所有 `application.yml` 的数据库连接 URL
- **代码**:
  ```yaml
  url: jdbc:mysql://...?allowPublicKeyRetrieval=true&useSSL=false
  ```
- **问题**: `allowPublicKeyRetrieval=true` 允许客户端从服务器获取公钥，在 `useSSL=false` 的情况下可能遭受中间人攻击。
- **修复建议**: 启用 SSL 连接后可安全保留此选项。

#### L-03: .gitignore 缺少敏感文件类型

- **位置**: `.gitignore`
- **问题**: `.gitignore` 排除了 `.env` 文件，但未排除以下敏感文件类型：
  - `*.pem`, `*.key`, `*.crt`, `*.p12`（证书和密钥文件）
  - `*.jks`（Java KeyStore）
  - `docker-compose.override.yml`（可能包含生产环境密码）
- **修复建议**: 在 `.gitignore` 中添加上述文件类型。

#### L-04: 前端依赖 axios 1.7.9 无已知 CVE，但建议定期更新

- **位置**: `console/package.json`
- **问题**: 前端依赖（Element Plus 2.9.1、ECharts 5.6.0、axios 1.7.9）均使用 `^` 版本范围，lock 文件未纳入版本控制，可能导致不同环境安装不同版本。
- **修复建议**:
  1. 使用 `pnpm lock` 或 `npm shrinkwrap` 锁定依赖版本。
  2. 定期运行 `npm audit` 检查前端依赖漏洞。

---

## 三、RBAC 权限矩阵分析

### 已定义的角色

| 角色 | 代码 | 说明 |
|------|------|------|
| ADMIN | `ROLE_ADMIN` | 管理员，可执行所有管理操作 |
| OPERATOR | `ROLE_OPERATOR` | 运维人员，可查看租户信息 |

### 权限覆盖情况

| 模块 | 控制器 | 端点数 | 有权限注解 | 覆盖率 |
|------|--------|--------|-----------|--------|
| Platform | TenantController | 7 | 7 (@PreAuthorize) | 100% |
| Platform | ApiKeyController | 6 | 0 | **0%** |
| Platform | UsageController | 2 | 0 | **0%** |
| Weather | WeatherController | 5 | 0 | **0%** |
| UTM | UavTrackingController | 5 | 0 | **0%** |
| UTM | FlightPlanController | 7 | 0 | **0%** |
| UTM | AirspaceController | 3 | 0 | **0%** |
| Risk | RiskController | 3 | 0 | **0%** |
| Risk | AirworthinessController | 2 | 0 | **0%** |
| Planning | PlanningController | 7 | 0 | **0%** |
| Planning | MpcController | 5 | 0 | **0%** |
| Observation | ObservationController | 4 | 0 | **0%** |
| Observation | ObservationDecisionController | 4 | 0 | **0%** |
| Assimilation | AssimilationController | 5 | 0 | **0%** |
| Assimilation | GprPostprocessController | 2 | 0 | **0%** |
| **合计** | | **67** | **7** | **10.4%** |

### RBAC 评估结论

RBAC 框架设计完整（支持角色、权限、资源类型 API/MENU/DATA），但实际应用覆盖率极低。仅 `TenantController` 使用了权限注解，其余 **89.6% 的端点** 完全依赖认证（Authentication）而非授权（Authorization）。`@RequireApiKey` 注解已定义但**未在任何 Controller 上使用**。

---

## 四、依赖漏洞扫描结果

### Java 后端依赖

| 依赖 | 版本 | 已知 CVE | 风险评估 |
|------|------|----------|----------|
| Spring Boot | 4.0.0 | CVE-2026-40976 (CVSS 9.1, Actuator) | **高** |
| Spring Cloud | 2025.1.0 | 未发现已知 CVE | 低 |
| MyBatis-Plus | 3.5.16 | 未发现已知 CVE | 低 |
| JJWT | 0.12.6 | 未发现已知 CVE | 低 |
| Resilience4j | 2.3.0 | 未发现已知 CVE | 低 |
| MySQL Connector | 8.4.0 | 未发现高危 CVE | 低 |
| Micrometer | 1.14.2 | 未发现已知 CVE | 低 |

### 前端依赖

| 依赖 | 版本 | 已知 CVE | 风险评估 |
|------|------|----------|----------|
| Vue | 3.5.13 | 未发现已知 CVE | 低 |
| Element Plus | 2.9.1 | 未发现已知 CVE | 低 |
| ECharts | 5.6.0 | 未发现已知 CVE | 低 |
| Axios | 1.7.9 | 未发现已知 CVE | 低 |
| Pinia | 2.3.0 | 未发现已知 CVE | 低 |

### Python 依赖

| 依赖 | 版本要求 | 已知 CVE | 风险评估 |
|------|----------|----------|----------|
| FastAPI | >=0.115.0 | 未发现高危 CVE | 低 |
| Redis | >=5.0.0 | 未发现高危 CVE | 低 |
| Pydantic | >=2.7.0 | 未发现已知 CVE | 低 |
| httpx | >=0.27.0 | 未发现已知 CVE | 低 |

---

## 五、HTTPS/TLS 配置检查

| 检查项 | 状态 | 说明 |
|--------|------|------|
| Gateway TLS 终端 | **未配置** | 无 SSL 证书配置 |
| 服务间 mTLS | **未配置** | 所有服务间通信为明文 HTTP |
| MySQL SSL | **已禁用** | 所有连接字符串设置 `useSSL=false` |
| Redis TLS | **未配置** | 使用明文 `redis://` 协议 |
| Kafka SSL | **未配置** | 无 SSL 传输配置 |
| CORS 配置 | **过于宽松** | `allowedOriginPatterns: "*"` + `allowCredentials: true` |

---

## 六、敏感数据审计

| 检查项 | 状态 | 说明 |
|--------|------|------|
| .gitignore 排除 .env | **已配置** | `.env` 和 `.env.local` 已排除 |
| .gitignore 排除证书文件 | **未配置** | 缺少 `*.pem`, `*.key`, `*.jks` 等规则 |
| JWT 密钥硬编码 | **存在** | 默认值写在源代码中 |
| UTM 密钥硬编码 | **存在** | 默认值写在源代码和配置中 |
| 数据库密码硬编码 | **存在** | 默认值 `rootpass` 写在配置中 |
| 日志脱敏 | **未配置** | 无任何脱敏机制 |
| Actuator 信息泄露 | **存在** | `/actuator/**` 无需认证即可访问 |

---

## 七、修复优先级建议

### 立即修复（P0 - 1 周内）

1. **C-01/C-02**: 移除所有硬编码的默认密钥，强制从环境变量读取
2. **C-03**: 收紧 Actuator 端点访问权限，确认 CVE-2026-40976 修复状态
3. **H-01**: 收紧 CORS 配置，限定具体域名

### 短期修复（P1 - 2 周内）

4. **H-02**: 移除数据库默认密码
5. **H-03/H-04/M-07**: 为所有 API 端点添加权限注解
6. **H-05**: 启用 HTTPS/TLS 通信

### 中期修复（P2 - 1 个月内）

7. **M-01**: 实现 Refresh Token 机制
8. **M-04**: 添加日志脱敏
9. **M-05**: 修复 IP 白名单 CIDR 匹配
10. **M-06**: 强制 Redis 密码配置

### 长期改进（P3 - 持续）

11. **L-01**: 持续关注依赖安全更新
12. **L-03**: 完善 .gitignore 规则
13. **L-04**: 锁定前端依赖版本

---

## 八、安全架构亮点（正面发现）

1. **JWT + HMAC 双重认证机制**: 设计了 JWT（用户认证）和 HMAC-SHA256（API Key 签名）两套认证体系，架构设计合理。
2. **RBAC 框架完整**: 角色实体、权限实体、权限评估器、方法安全配置齐全，支持 API/MENU/DATA 三种资源类型。
3. **BCrypt 密码哈希**: 使用 `BCryptPasswordEncoder` 进行密码哈希存储。
4. **UTM 回调安全**: 设计了 IP 白名单 + HMAC 签名 + Nonce 防重放 + 时间戳校验的多重防护（虽然实现有缺陷）。
5. **幂等性控制**: 实现了 `@Idempotent` 注解和 Redis 幂等性切面。
6. **多租户隔离**: 实现了基于 Schema 的多租户数据隔离。
7. **限流保护**: Gateway 配置了多级限流（租户级、API Key 级、路径级）。
8. **.env 文件排除**: .gitignore 正确排除了环境变量文件。

---

*报告生成工具: SOLO Security Auditor*
*审计完成时间: 2026-06-15*
