# Web Token 认证系统架构设计文档

> **文档版本**: v2.0
> **创建日期**: 2026-06-01
> **目标**: 实现基于 JWT 的安全认证机制，包含 Demo 模式功能

---

## 1. 架构概览

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Web (Vue)  │  │ Mobile (Flutter) │  │  Python CLI  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (8088)                        │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │ JWT Validation │  │ Rate Limiting  │  │ Route/Forward  │ │
│  └────────────────┘  └────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Java Backend   │ │  Python Micro   │ │  Python Micro   │
│ (Spring Boot)   │ │   Services      │ │   Services      │
│   Port: 8089    │ │ edge-coordinator │ │  fengwu-service │
│                 │ │   Port: 5000     │ │   Port: 8000    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
              ┌───────────────────────────────┐
              │     Shared Infrastructure      │
              │  ┌─────────────────────────┐  │
              │  │   MySQL/PostgreSQL       │  │
              │  │   - Users Table          │  │
              │  │   - Token Blacklist      │  │
              │  │   - Demo Tenant Data     │  │
              │  └─────────────────────────┘  │
              │  ┌─────────────────────────┐  │
              │  │   Redis Cache           │  │
              │  │   - Access Token Cache  │  │
              │  │   - Refresh Token Store │  │
              │  │   - Rate Limit Counters │  │
              │  │   - Demo Session Track  │  │
              │  └─────────────────────────┘  │
              └───────────────────────────────┘
```

### 1.2 核心技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| **Java Backend** | Spring Boot 3.x + Spring Security | 主业务服务 |
| **Java JWT** | jjwt 0.12.x | JWT 生成和验证 |
| **Python Services** | FastAPI / Flask | Python 微服务 |
| **Python JWT** | PyJWT | Python 服务 JWT 验证 |
| **Database** | MySQL 8.x / PostgreSQL 14+ | 用户数据、Token 黑名单 |
| **Cache** | Redis 7.x | Token 缓存、限流计数器 |
| **API Gateway** | Spring Cloud Gateway | 统一认证入口 |

---

## 2. JWT 认证机制设计

### 2.1 Token 设计

#### 2.1.1 Access Token

```json
{
  "header": {
    "alg": "HS512",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_id",
    "username": "admin",
    "roles": ["ROLE_ADMIN", "ROLE_USER"],
    "tenant_id": "demo_tenant_001",
    "token_type": "access",
    "iat": 1717200000,
    "exp": 1717207200,
    "jti": "unique-token-id-uuid"
  },
  "signature": "HMAC-SHA512(secret)"
}
```

**配置**:
- **算法**: HS512 (比 HS256 更安全)
- **有效期**: 2 小时 (7200 秒)
- **存储**: Redis TTL 自动过期

#### 2.1.2 Refresh Token

```json
{
  "header": {
    "alg": "HS512",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_id",
    "username": "admin",
    "token_type": "refresh",
    "iat": 1717200000,
    "exp": 1719792800,
    "jti": "unique-refresh-token-uuid"
  },
  "signature": "HMAC-SHA512(secret)"
}
```

**配置**:
- **算法**: HS512
- **有效期**: 30 天 (2592000 秒)
- **存储**: Redis + 数据库双重存储

### 2.2 认证流程

#### 2.2.1 标准登录流程

```
┌─────────────────────────────────────────────────────────────┐
│                     1. 用户登录                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ POST /api/v1/auth│
                    │ /login           │
                    │ {username, pass} │
                    └──────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │ 2. 验证用户名密码 (BCrypt)      │
              └───────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
              验证成功               验证失败
                    │                   │
                    ▼                   ▼
    ┌────────────────────────┐  ┌──────────────────┐
    │ 3. 生成 Access Token   │  │ 返回 401 错误      │
    │    + Refresh Token     │  │ LOG: 登录失败     │
    └────────────────────────┘  └──────────────────┘
                    │
                    ▼
    ┌────────────────────────┐
    │ 4. Redis 存储:          │
    │    - Access Token TTL   │
    │    - Refresh Token 映射 │
    └────────────────────────┘
                    │
                    ▼
    ┌────────────────────────┐
    │ 5. 返回给客户端:         │
    │ {                       │
    │   "accessToken": "...", │
    │   "refreshToken": "...",│
    │   "expiresIn": 7200     │
    │ }                       │
    └────────────────────────┘
```

#### 2.2.2 Token 刷新流程

```
┌─────────────────────────────────────────────────────────────┐
│                  6. Token 刷新 (Access Token 过期)           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ POST /api/v1/auth│
                    │ /refresh         │
                    │ {refreshToken}   │
                    └──────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │ 7. 验证 Refresh Token         │
              │   - 检查 Redis 是否已使用      │
              │   - 检查数据库是否在黑名单     │
              │   - 验证签名和过期时间         │
              └───────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
              验证成功               验证失败
                    │                   │
                    ▼                   ▼
    ┌────────────────────────┐  ┌──────────────────┐
    │ 8. 生成新 Access Token  │  │ 返回 401 错误      │
    │    + 可选新 Refresh Token│ │ 提示重新登录      │
    └────────────────────────┘  └──────────────────┘
                    │
                    ▼
    ┌────────────────────────┐
    │ 9. Redis 更新:         │
    │    - 旧 Refresh Token  │
    │      标记为已使用       │
    │    - 新 Refresh Token  │
    │      存储              │
    └────────────────────────┘
```

#### 2.2.3 登出流程 (Token 黑名单)

```
┌─────────────────────────────────────────────────────────────┐
│                        10. 用户登出                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ POST /api/v1/auth│
                    │ /logout          │
                    │ (Bearer Token)   │
                    └──────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │ 11. 添加到 Token 黑名单:       │
              │    - Redis: 快速查询           │
              │    - MySQL: 持久化记录         │
              │    TTL = Token 剩余有效期      │
              └───────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │ 12. 删除客户端本地 Token        │
              │    (前端清除 localStorage)     │
              └───────────────────────────────┘
```

### 2.3 Token 黑名单机制

#### 2.3.1 触发场景

| 场景 | 处理方式 |
|------|---------|
| 用户主动登出 | Access Token + Refresh Token 都加入黑名单 |
| 管理员强制登出 | 用户所有 Token 加入黑名单 |
| 密码修改 | 所有 Refresh Token 加入黑名单 |
| 账户冻结 | 所有 Token 加入黑名单 |
| Token 被盗 | 用户可主动撤销 |

#### 2.3.2 黑名单存储设计

**MySQL 表结构**:

```sql
CREATE TABLE token_blacklist (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    token_id VARCHAR(255) NOT NULL UNIQUE,  -- JTI
    user_id BIGINT NOT NULL,
    token_type ENUM('access', 'refresh', 'all') NOT NULL,
    reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,  -- Token 原始过期时间
    INDEX idx_token_id (token_id),
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at)
);

CREATE TABLE refresh_token_family (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    refresh_token_id VARCHAR(255) NOT NULL UNIQUE,
    is_used BOOLEAN DEFAULT FALSE,
    is_revoked BOOLEAN DEFAULT FALSE,
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    device_info VARCHAR(255),
    ip_address VARCHAR(45),
    INDEX idx_user_id (user_id),
    INDEX idx_token_id (refresh_token_id)
);
```

**Redis 键设计**:

```
blacklist:access:{jti} -> "1" (TTL = 剩余有效期)
blacklist:refresh:{jti} -> "1" (TTL = 剩余有效期)
blacklist:user:{user_id} -> Set<token_id> (所有该用户的黑名单Token)
refresh:token:{jti} -> {user_id, username, issued_at} (快速验证)
refresh:family:{user_id}:{family_id} -> 最新有效Token
```

---

## 3. Demo 模式设计

### 3.1 Demo 模式架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Demo Mode Architecture                   │
└─────────────────────────────────────────────────────────────┘

┌────────────────────┐    ┌────────────────────┐
│  Demo User Login   │    │  Standard Login    │
│  (Auto-registered)│    │  (Full Register)   │
└────────┬───────────┘    └────────┬───────────┘
         │                         │
         ▼                         ▼
┌─────────────────────────────────────────────────────────┐
│              Tenant ID Assignment                         │
│  ┌────────────────┐         ┌────────────────┐        │
│  │ Tenant: DEMO   │         │ Tenant: User ID │        │
│  │ (Read-only     │         │ (Full Access)  │        │
│  │  Demo Data)    │         │                │        │
│  └────────────────┘         └────────────────┘        │
└─────────────────────────────────────────────────────────┘
         │                         │
         ▼                         ▼
┌─────────────────────────────────────────────────────────┐
│              Data Access Layer                             │
│  @TenantIsolation 拦截器自动注入 tenant_id                  │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Demo 用户自动注册

**流程**:
1. 用户访问 `/api/v1/auth/demo-login`
2. 系统自动创建 Demo 用户 (用户名: `demo_{UUID}`)
3. 分配 `DEMO_TENANT` 租户 ID
4. 返回 Access Token + Refresh Token
5. 无需密码，一键体验

**Demo 用户特性**:
- 角色: `ROLE_DEMO` (特殊角色，权限受限)
- 租户: `DEMO_TENANT_{HASH}`
- 有效期: 24 小时自动过期
- 并发限制: 1 个会话

### 3.3 Demo 模式限制策略

#### 3.3.1 API 调用频率限制

**限制规则**:
- **1000 次/小时** (按用户维度)
- 使用 Redis 滑动窗口算法
- 限制的 API 类型:
  - 写入操作 (POST, PUT, DELETE): 100 次/小时
  - 读取操作 (GET): 1000 次/小时

**Redis 实现**:
```
ratelimit:demo:{user_id}:{hour}:{action_type} -> Counter
TTL: 3600 秒
```

#### 3.3.2 并发连接数限制

**限制规则**:
- **每个 Demo 用户最多 1 个会话**
- 使用 Redis Session Track
- 新登录自动使旧会话失效

**Redis 键**:
```
demo:session:{user_id} -> {session_id, created_at, ip_address}
TTL: 86400 秒 (24 小时)
```

#### 3.3.3 数据隔离策略

**逻辑隔离（同库不同租户）**:

```java
// 租户上下文
public class TenantContext {
    private static final ThreadLocal<String> currentTenant = new ThreadLocal<>();

    public static void setTenant(String tenantId) {
        currentTenant.set(tenantId);
    }

    public static String getTenant() {
        return currentTenant.get();
    }

    public static void clear() {
        currentTenant.remove();
    }
}

// 数据访问拦截器
@Aspect
@Component
public class TenantInterceptor {

    @Before("execution(* com.uav.repository.*.*(..))")
    public void injectTenantId(JoinPoint joinPoint) {
        String tenantId = TenantContext.getTenant();
        if (tenantId != null) {
            // 自动注入 tenant_id 条件
            addTenantFilter(joinPoint);
        }
    }
}

// Demo 数据自动注入
@Aspect
@Component
public class DemoDataAspect {

    @Before("execution(* com.uav.service.*.*(..))")
    public void checkDemoAccess(JoinPoint joinPoint) {
        if (isDemoUser()) {
            // Demo 用户只能访问 demo_ 前缀的数据
            enforceDemoDataOnly();
        }
    }
}
```

### 3.4 Demo 数据集

**预置 Demo 数据**:

| 数据类型 | 数量 | 说明 |
|---------|------|------|
| 无人机 | 5 架 | 演示用虚拟无人机 |
| 任务模板 | 10 个 | 典型任务场景 |
| 飞行路径 | 20 条 | 预规划路径 |
| 气象数据 | 24 小时 | 最近一天模拟数据 |
| 地理围栏 | 5 个 | 演示区域 |

**Demo 数据标记**:
```sql
-- 所有 Demo 数据都有统一标记
INSERT INTO drones (name, tenant_id, ... )
VALUES ('Demo-UAV-1', 'DEMO_TENANT_DEFAULT', ...);

-- 查询时自动过滤
SELECT * FROM drones WHERE tenant_id = :current_tenant;
```

---

## 4. RESTful API 设计

### 4.1 认证 API 端点

#### 4.1.1 登录

```
POST /api/v1/auth/login
Content-Type: application/json

Request:
{
  "username": "string (required)",
  "password": "string (required)"
}

Response 200:
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "accessToken": "string",
    "refreshToken": "string",
    "expiresIn": 7200,
    "tokenType": "Bearer",
    "user": {
      "id": "long",
      "username": "string",
      "roles": ["string"]
    }
  }
}

Response 401:
{
  "code": 401,
  "message": "用户名或密码错误",
  "details": null
}
```

#### 4.1.2 Demo 登录

```
POST /api/v1/auth/demo-login
Content-Type: application/json

Request: (可选)
{
  "purpose": "string (optional) - 演示目的说明"
}

Response 200:
{
  "code": 200,
  "message": "Demo模式登录成功",
  "data": {
    "accessToken": "string",
    "refreshToken": "string",
    "expiresIn": 7200,
    "tokenType": "Bearer",
    "demoInfo": {
      "demoUserId": "string",
      "expirationTime": "ISO8601",
      "limits": {
        "apiCallsPerHour": 1000,
        "concurrentSessions": 1,
        "validDuration": 86400
      }
    }
  }
}

Response 429: (Demo 服务已满)
{
  "code": 429,
  "message": "Demo服务当前用户数已满，请稍后再试"
}
```

#### 4.1.3 Token 刷新

```
POST /api/v1/auth/refresh
Content-Type: application/json

Request:
{
  "refreshToken": "string (required)"
}

Response 200:
{
  "code": 200,
  "message": "Token刷新成功",
  "data": {
    "accessToken": "string",
    "refreshToken": "string",  // 新的 Refresh Token (可选)
    "expiresIn": 7200
  }
}

Response 401:
{
  "code": 401,
  "message": "Refresh Token无效或已过期"
}
```

#### 4.1.4 登出

```
POST /api/v1/auth/logout
Authorization: Bearer {access_token}

Request:
{
  "refreshToken": "string (optional) - 同时撤销refresh token"
}

Response 200:
{
  "code": 200,
  "message": "登出成功"
}
```

#### 4.1.5 撤销 Token

```
POST /api/v1/auth/revoke
Authorization: Bearer {access_token}

Request:
{
  "tokenId": "string (optional) - 指定撤销的token ID"
}

Response 200:
{
  "code": 200,
  "message": "Token已撤销"
}
```

#### 4.1.6 获取当前用户

```
GET /api/v1/auth/me
Authorization: Bearer {access_token}

Response 200:
{
  "code": 200,
  "data": {
    "id": "long",
    "username": "string",
    "email": "string",
    "roles": ["string"],
    "tenantId": "string",
    "permissions": ["string"],
    "isDemo": "boolean"
  }
}
```

### 4.2 错误响应规范

#### 4.2.1 标准错误格式

```json
{
  "code": 400,
  "message": "错误信息",
  "details": {
    "field": "具体错误字段",
    "reason": "详细原因"
  },
  "timestamp": "ISO8601",
  "path": "/api/v1/..."
}
```

#### 4.2.2 HTTP 状态码映射

| 状态码 | 场景 | 说明 |
|-------|------|------|
| 200 | 成功 | 正常成功响应 |
| 201 | 创建成功 | 资源创建成功 |
| 400 | 参数错误 | 请求参数校验失败 |
| 401 | 未认证 | Token 缺失/无效/过期 |
| 403 | 权限不足 | 无权限访问资源 |
| 404 | 资源不存在 | 请求的资源不存在 |
| 429 | 请求过多 | 触发限流 |
| 500 | 服务器错误 | 内部错误 |

#### 4.2.3 认证错误码

| 错误码 | HTTP状态 | 说明 |
|--------|---------|------|
| AUTH_001 | 401 | Token 缺失 |
| AUTH_002 | 401 | Token 格式错误 |
| AUTH_003 | 401 | Token 已过期 |
| AUTH_004 | 401 | Token 签名无效 |
| AUTH_005 | 401 | Token 已被撤销 |
| AUTH_006 | 401 | Refresh Token 无效 |
| AUTH_007 | 403 | Demo 用户无此权限 |
| AUTH_008 | 429 | API 调用超限 |
| AUTH_009 | 429 | Demo 并发会话超限 |
| AUTH_010 | 401 | Demo 会话已过期 |

---

## 5. 安全性设计

### 5.1 密钥管理

**密钥生成**:
```bash
# 生成强密钥
openssl rand -base64 64  # 512-bit key for HS512

# 环境变量配置
export JWT_SECRET="your-512-bit-secret-key..."
export JWT_REFRESH_SECRET="separate-512-bit-refresh-key..."
```

**密钥轮换**:
- 当前密钥 + 历史密钥 (最多保留 2 个)
- 新 Token 使用新密钥签名
- 验证时尝试所有有效密钥

```java
// JwtUtil.java 改进
public class JwtUtil {
    private List<Key> signingKeys;

    @PostConstruct
    public void init() {
        // 加载当前密钥和历史密钥
        String currentSecret = jwtSecret;
        String previousSecret = jwtPreviousSecret; // 可选

        this.signingKeys = Arrays.asList(
            Keys.hmacShaKeyFor(currentSecret.getBytes()),
            Keys.hmacShaKeyFor(previousSecret.getBytes())
        );
    }

    public Claims parseToken(String token) {
        for (Key key : signingKeys) {
            try {
                return Jwts.parser()
                    .verifyWith((SecretKey) key)
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();
            } catch (Exception e) {
                // 尝试下一个密钥
            }
        }
        throw new JwtException("Token验证失败");
    }
}
```

### 5.2 密码安全

**密码策略**:
- 最小长度: 8 字符
- 必须包含: 大写字母、小写字母、数字
- 建议包含: 特殊字符
- 禁止: 常见密码词典

**密码加密**:
```java
// BCrypt 配置
@Bean
public PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder(12); // 强度因子 12
}

// 密码验证
boolean matches = passwordEncoder.matches(rawPassword, encodedPassword);
```

### 5.3 防止常见攻击

#### 5.3.1 Token 盗用防护

- HTTPS 强制
- HttpOnly Cookie (可选)
- Token 存储在内存而非 localStorage
- 敏感操作二次验证

#### 5.3.2 重放攻击防护

- Token 唯一 ID (JTI)
- 请求时间戳验证
- 请求序列号检查

#### 5.3.3 暴力破解防护

- 登录失败次数限制 (5次/15分钟)
- 账户锁定机制
- CAPTCHA 验证码 (可选)

```java
// 登录失败追踪
String loginFailKey = "login:fail:" + username;
long failCount = redis.incr(loginFailKey);
if (failCount == 1) {
    redis.expire(loginFailKey, 900); // 15分钟
}
if (failCount >= 5) {
    // 账户锁定
    accountLockService.lock(username, Duration.ofMinutes(15));
}
```

---

## 6. 实现计划

### 6.1 阶段一: Java Spring Boot 后端 (2-3天)

1. **Day 1**: 改进 JwtUtil 实现 Access + Refresh Token
2. **Day 2**: 实现 Token 黑名单机制 (Redis + MySQL)
3. **Day 3**: 实现 Demo 模式基础功能

### 6.2 阶段二: Python 微服务 (1-2天)

1. **统一认证中间件**: FastAPI/Flask JWT 验证
2. **与 Java 后端共享密钥**: 配置统一 JWT Secret
3. **Demo 模式支持**: Python 服务 Demo 访问控制

### 6.3 阶段三: API Gateway (1天)

1. **JWT 统一验证**: Gateway 层 Token 验证
2. **限流配置**: 基于用户/Demo 的限流
3. **日志和监控**: 认证事件追踪

### 6.4 阶段四: 测试和文档 (1-2天)

1. **单元测试**: JWT、Token 刷新、黑名单
2. **集成测试**: 完整认证流程
3. **安全测试**: 渗透测试
4. **API 文档**: 更新 OpenAPI/Swagger 文档

---

## 7. 技术选型总结

| 组件 | 技术 | 版本 |
|------|------|------|
| Java JWT | jjwt | 0.12.x |
| Python JWT | PyJWT | 2.8.x |
| Database | MySQL 8.0 / PostgreSQL 14 | 最新 |
| Cache | Redis | 7.x |
| API Gateway | Spring Cloud Gateway | 2023.x |
| 密码加密 | BCrypt | - |
| 序列化 | Jackson | 2.15.x |

---

## 8. 配置文件示例

### 8.1 application.yml

```yaml
jwt:
  secret: ${JWT_SECRET}
  refresh-secret: ${JWT_REFRESH_SECRET}
  access-expiration: 7200      # 2 hours
  refresh-expiration: 2592000   # 30 days
  issuer: uav-platform

demo:
  enabled: true
  max-concurrent-sessions: 1
  api-rate-limit: 1000          # per hour
  session-duration: 86400        # 24 hours
  data-isolation: logical       # logical or physical

security:
  login:
    max-fail-attempts: 5
    lockout-duration: 900       # 15 minutes
  cors:
    allowed-origins:
      - http://localhost:3000
      - https://your-domain.com
```

---

## 9. 监控和告警

### 9.1 认证指标

| 指标 | 说明 | 告警阈值 |
|------|------|---------|
| login_success_total | 登录成功次数 | - |
| login_failure_total | 登录失败次数 | > 10/分钟 |
| token_refresh_total | Token 刷新次数 | - |
| token_revoked_total | Token 撤销次数 | > 5/分钟 |
| demo_users_active | Demo 用户数 | > 100 |
| auth_latency_ms | 认证延迟 | > 100ms |

### 9.2 日志事件

```
# 认证成功
LOGIN_SUCCESS | user=admin | ip=192.168.1.1 | method=LOGIN

# 认证失败
LOGIN_FAILURE | user=admin | reason=INVALID_PASSWORD | ip=192.168.1.1

# Token 刷新
TOKEN_REFRESH | user=admin | old_jti=xxx | new_jti=yyy

# Demo 登录
DEMO_LOGIN | demo_id=demo_abc123 | purpose=demo

# 安全告警
SECURITY_ALERT | type=BRUTE_FORCE | user=admin | attempts=5
```

---

> **下一步**: 等待用户批准此设计方案，然后进入实现阶段。
