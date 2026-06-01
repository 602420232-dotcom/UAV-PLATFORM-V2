# JWT 认证使用指南

> **文档版本**: v1.0  
> **最后更新**: 2026-06-01  
> **适用模块**: backend-spring, uav-platform-service, api-gateway

---

## 目录

1. [认证架构概述](#1-认证架构概述)
2. [认证流程](#2-认证流程)
3. [API 接口](#3-api-接口)
4. [前端集成](#4-前端集成)
5. [DEMO 模式](#5-demo-模式)
6. [安全配置](#6-安全配置)
7. [故障排除](#7-故障排除)

---

## 1. 认证架构概述

### 1.1 组件说明

| 组件 | 端口 | 职责 |
|------|------|------|
| **backend-spring** | 8089 | JWT Token 生成、验证、刷新 |
| **uav-platform-service** | 8080 | 平台 API，依赖 JWT 认证 |
| **api-gateway** | 8088 | 请求路由、Token 转发 |

### 1.2 认证机制

项目采用 **JWT (JSON Web Token)** 实现无状态认证：

- **Token 类型**: Access Token + Refresh Token
- **加密算法**: HS256 (对称密钥)
- **Token 有效期**: Access Token 1小时，Refresh Token 7天
- **密钥管理**: 通过环境变量 `JWT_SECRET` 配置

---

## 2. 认证流程

### 2.1 标准登录流程

```
用户提交凭证
    ↓
POST /api/v1/auth/login
    ↓
后端验证用户名密码 (BCrypt)
    ↓
生成 JWT Access Token + Refresh Token
    ↓
返回 Token 给客户端
    ↓
客户端在后续请求 Header 中携带 Token
Authorization: Bearer <access_token>
```

### 2.2 Token 刷新流程

```
Access Token 过期 (401)
    ↓
POST /api/v1/auth/refresh
Body: { "refreshToken": "<refresh_token>" }
    ↓
验证 Refresh Token 有效性
    ↓
生成新的 Access Token
    ↓
返回新 Token 给客户端
```

### 2.3 请求拦截流程

```
客户端请求
    ↓
API Gateway 路由
    ↓
JwtAuthenticationFilter 拦截
    ↓
验证 Token 签名和有效期
    ↓
解析用户信息，设置 SecurityContext
    ↓
控制器方法执行
```

---

## 3. API 接口

### 3.1 登录接口

**端点**: `POST /api/v1/auth/login`

**请求体**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**成功响应** (200):
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiJ9...",
    "expiresIn": 3600,
    "tokenType": "Bearer"
  }
}
```

**失败响应** (401):
```json
{
  "code": 401,
  "message": "用户名或密码错误"
}
```

### 3.2 Token 刷新接口

**端点**: `POST /api/v1/auth/refresh`

**请求体**:
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiJ9..."
}
```

**成功响应** (200):
```json
{
  "code": 200,
  "message": "Token刷新成功",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiJ9...",
    "expiresIn": 3600
  }
}
```

### 3.3 登出接口

**端点**: `POST /api/v1/auth/logout`

**请求头**:
```
Authorization: Bearer <access_token>
```

**成功响应** (200):
```json
{
  "code": 200,
  "message": "登出成功"
}
```

### 3.4 获取当前用户信息

**端点**: `GET /api/v1/auth/me`

**请求头**:
```
Authorization: Bearer <access_token>
```

**成功响应** (200):
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "username": "admin",
    "roles": ["ROLE_ADMIN", "ROLE_USER"],
    "permissions": ["task:create", "task:read", ...]
  }
}
```

---

## 4. 前端集成

### 4.1 Vue 前端集成

**文件**: `uav-path-planning-system/frontend-vue/src/api/auth.js`

```javascript
import api from './index'

export function login(username, password) {
  return api.post('/v1/auth/login', { username, password })
}

export function refreshToken(refreshToken) {
  return api.post('/v1/auth/refresh', { refreshToken })
}

export function logout() {
  return api.post('/v1/auth/logout')
}

export function getCurrentUser() {
  return api.get('/v1/auth/me')
}
```

### 4.2 Flutter 移动端集成

**文件**: `uav-mobile-app/lib/services/auth_service.dart`

```dart
class AuthService {
  final ApiClient _api;
  
  Future<AuthResult> login(String username, String password) async {
    final response = await _api.post('/api/v1/auth/login', {
      'username': username,
      'password': password,
    });
    
    if (response['code'] == 200) {
      final data = response['data'];
      await _secureStorage.saveToken(data['accessToken']);
      await _secureStorage.saveRefreshToken(data['refreshToken']);
      return AuthResult.success();
    }
    return AuthResult.failure(response['message']);
  }
}
```

### 4.3 Token 自动刷新拦截器

在 `api_interceptor.dart` 中实现 Token 自动刷新：

```dart
void onError(DioException err) async {
  if (err.response?.statusCode == 401) {
    final refreshToken = await _secureStorage.getRefreshToken();
    if (refreshToken != null) {
      try {
        final result = await _authService.refreshToken(refreshToken);
        if (result.success) {
          // 重试原请求
          final opts = err.requestOptions;
          opts.headers['Authorization'] = 'Bearer ${result.accessToken}';
          final response = await _dio.fetch(opts);
          return response;
        }
      } catch (e) {
        // Refresh失败，清除Token并跳转登录
        await _secureStorage.clearAll();
        Get.offAllNamed('/login');
      }
    }
  }
  return err;
}
```

---

## 5. DEMO 模式

项目支持 **DEMO 模式**，用于开发和演示环境。

### 5.1 启用 DEMO 模式

在 `application.yml` 中配置：

```yaml
spring:
  profiles:
    active: demo

uav:
  security:
    demo-mode-enabled: true
```

### 5.2 DEMO 模式特性

| 特性 | 说明 |
|------|------|
| **简化认证** | 使用静态 Token "demo" 即可访问所有 API |
| **绕过密码验证** | 登录接口直接返回有效 Token |
| **日志警告** | 所有请求记录 "DEMO MODE ACTIVE" 警告 |
| **生产禁用** | 生产环境必须禁用 DEMO 模式 |

### 5.3 DEMO Token 使用

```bash
# 使用 DEMO Token 访问 API
curl -X GET http://localhost:8080/api/v1/tasks \
  -H "Authorization: Bearer demo"
```

### 5.4 生产环境安全建议

```yaml
# application-prod.yml
spring:
  profiles:
    active: prod

uav:
  security:
    demo-mode-enabled: false  # 必须禁用
    jwt:
      secret: ${JWT_SECRET}  # 必须通过环境变量注入强密钥
      expiration: 3600        # Access Token 有效期
      refresh-expiration: 604800  # Refresh Token 有效期
```

---

## 6. 安全配置

### 6.1 JWT 密钥配置

**环境变量**:
```bash
# 生成强密钥
openssl rand -base64 32

# 配置到环境变量
export JWT_SECRET="your-secure-256-bit-secret-key-here"
```

**application.yml**:
```yaml
uav:
  jwt:
    secret: ${JWT_SECRET}
    expiration: 3600
    refresh-expiration: 604800
    header: Authorization
    prefix: Bearer
```

### 6.2 密码加密

使用 **BCrypt** 密码编码器：

```java
@Configuration
public class SecurityConfig {
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
```

**密码验证示例**:
```java
boolean matches = passwordEncoder.matches(rawPassword, encodedPassword);
```

### 6.3 CORS 配置

配置允许的前端域名：

```yaml
uav:
  cors:
    allowed-origins:
      - http://localhost:3000
      - http://localhost:8080
      - https://your-production-domain.com
```

### 6.4 安全审计

系统自动记录所有认证事件：

| 事件类型 | 记录内容 |
|---------|---------|
| LOGIN_SUCCESS | 用户名、IP、时间 |
| LOGIN_FAILURE | 用户名、原因、IP、时间 |
| TOKEN_REFRESH | 用户名、时间 |
| LOGOUT | 用户名、IP、时间 |
| ACCESS_DENIED | 用户名、资源、IP、时间 |

---

## 7. 故障排除

### 7.1 常见错误

| 错误码 | 错误信息 | 原因 | 解决方案 |
|--------|---------|------|---------|
| 401 | Token 已过期 | Access Token 过期 | 调用刷新接口 |
| 401 | 无效 Token | Token 格式错误或被篡改 | 重新登录获取新 Token |
| 403 | 权限不足 | 用户角色不匹配 | 检查用户角色配置 |
| 500 | Token 生成失败 | JWT 密钥未配置 | 检查 JWT_SECRET 环境变量 |

### 7.2 Token 验证失败排查

1. **检查 Token 格式**
   ```javascript
   // 正确的格式
   Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
   
   // 错误的格式 (缺少Bearer前缀)
   Authorization: eyJhbGciOiJIUzI1NiJ9...
   ```

2. **检查 Token 有效期**
   ```javascript
   // 解码 Token 验证过期时间
   const payload = JSON.parse(atob(token.split('.')[1]));
   console.log('过期时间:', new Date(payload.exp * 1000));
   ```

3. **检查密钥一致性**
   - 确保所有服务使用相同的 `JWT_SECRET`
   - 检查环境变量是否正确加载

### 7.3 前端调试技巧

**浏览器开发者工具**:
```javascript
// 在控制台查看当前 Token
const token = localStorage.getItem('accessToken');
console.log('Token:', token);

// 解码 Token
const decoded = JSON.parse(atob(token.split('.')[1]));
console.log('用户信息:', decoded);
```

**Postman/Insomnia**:
- 添加 Authorization Header: `Bearer <token>`
- 或使用 Bearer Token 认证类型

---

## 附录 A: 默认用户

| 用户名 | 密码 | 角色 | 权限 |
|--------|------|------|------|
| admin | admin123 | ADMIN | 全部权限 |
| dispatcher | dispatch123 | DISPATCHER | 任务管理、路径规划 |
| operator | operator123 | OPERATOR | 数据采集、监控 |
| user | user123 | USER | 查看权限 |

> ⚠️ **注意**: 以上为默认密码，生产环境必须修改！

## 附录 B: 相关文件清单

| 文件路径 | 说明 |
|---------|------|
| `backend-spring/src/main/java/com/uav/config/JwtUtil.java` | JWT 工具类 |
| `backend-spring/src/main/java/com/uav/config/SecurityConfig.java` | Spring Security 配置 |
| `backend-spring/src/main/java/com/uav/controller/AuthController.java` | 认证控制器 |
| `backend-spring/src/main/java/com/uav/service/CustomUserDetailsService.java` | 用户认证服务 |
| `common-utils/src/main/java/com/uav/common/security/JwtAuthenticationFilter.java` | JWT 认证过滤器 |
| `api-gateway/src/main/resources/application.yml` | 网关认证配置 |

---

> **维护者**: UAV Platform Team  
> **文档版本**: 1.0  
> **创建日期**: 2026-05-31
