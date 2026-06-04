# Backend Spring API

路径规划系统后端 API - 用户认证授权、用户管理

## 基础信息

- **Base URL**: `http://localhost:8089`
- **服务**: backend-spring
- **熔断器**: ✅
- **认证**: JWT Bearer Token

---

## 认证接口 `/api/v1/auth`

### POST /login - 用户登录

用户登录获取 JWT 令牌

**请求体**:
```json
{
  "username": "admin",
  "password": "password123"
}
```

**响应** (200):
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**错误响应** (401):
```json
{
  "code": 401,
  "message": "用户名或密码错误"
}
```

---

### POST /register - 用户注册

注册新用户并自动登录

**请求体**:
```json
{
  "username": "newuser",
  "password": "password123",
  "email": "user@example.com",
  "fullName": "张三"
}
```

**响应** (201):
```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

### POST /refresh - 刷新令牌

刷新 JWT 令牌

**请求体**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应** (200):
```json
{
  "code": 200,
  "message": "令牌刷新成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

---

### POST /logout - 用户登出

用户登出并记录审计日志

**响应** (200):
```json
{
  "code": 200,
  "message": "登出成功"
}
```

---

## 用户管理 `/api/admin/users`

### GET / - 获取用户列表

获取所有用户列表

**响应** (200):
```json
[
  {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "fullName": "管理员",
    "enabled": true,
    "roles": [...]
  }
]
```

---

### GET /{id} - 获取用户详情

根据 ID 获取用户详情

**参数**: `id` - 用户ID (Long)

**响应** (200):
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "fullName": "管理员",
  "enabled": true,
  "roles": [...]
}
```

---

### POST / - 创建用户

创建新用户

**请求体**:
```json
{
  "username": "newuser",
  "password": "password123",
  "email": "user@example.com",
  "fullName": "新用户",
  "roles": [{"id": 1, "name": "USER"}]
}
```

**响应** (201):
```json
{
  "id": 2,
  "username": "newuser",
  "email": "user@example.com",
  "fullName": "新用户",
  "enabled": true,
  "roles": [...]
}
```

---

### PUT /{id} - 更新用户

更新用户信息

**参数**: `id` - 用户ID (Long)

**请求体**:
```json
{
  "username": "updateduser",
  "email": "updated@example.com",
  "fullName": "更新用户",
  "enabled": true,
  "roles": [{"id": 2, "name": "DISPATCHER"}]
}
```

**响应** (200): 返回更新后的用户对象

---

### DELETE /{id} - 删除用户

删除指定用户

**参数**: `id` - 用户ID (Long)

**响应** (200):
```json
true
```

---

## 路径规划 `/api/planning`

### POST /optimize - 路径优化

提交路径优化任务

**请求体**:
```json
{
  "startLocation": {"lat": 30.5, "lng": 114.3},
  "endLocation": {"lat": 31.5, "lng": 115.3},
  "waypoints": [],
  "constraints": {
    "maxDistance": 100,
    "avoidAreas": []
  }
}
```

**响应** (200):
```json
{
  "code": 200,
  "data": {
    "taskId": "task_123",
    "status": "submitted"
  }
}
```

---

### GET /status/{taskId} - 查询任务状态

查询路径规划任务状态

**参数**: `taskId` - 任务ID (String)

**响应** (200):
```json
{
  "code": 200,
  "data": {
    "taskId": "task_123",
    "status": "completed",
    "result": {
      "path": [...],
      "distance": 85.5,
      "duration": 3600
    }
  }
}
```

---

## 健康检查

### GET /actuator/health

**响应** (200):
```json
{
  "status": "UP"
}
```

---

## 熔断器端点

### GET /actuator/health/circuitbreakers

查看熔断器状态

---

> **最后更新**: 2026-05-14
