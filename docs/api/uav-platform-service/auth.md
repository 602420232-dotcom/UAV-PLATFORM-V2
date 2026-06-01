# 认证接口

## 登录

### 请求

```
POST /api/v1/auth/login
Content-Type: application/json
```

**请求体：**

```json
{
  "username": "admin",
  "password": "admin"
}
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "fullName": "Admin User",
      "roles": ["ADMIN"]
    }
  }
}
```

**失败：**

```json
{
  "code": 401,
  "message": "用户名或密码错误",
  "details": null
}
```

## 注册

### 请求

```
POST /api/v1/auth/register
Content-Type: application/json
```

**请求体：**

```json
{
  "username": "newuser",
  "password": "password123",
  "email": "newuser@example.com",
  "fullName": "New User"
}
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "id": 2,
    "username": "newuser",
    "email": "newuser@example.com",
    "fullName": "New User"
  }
}
```

**失败：**

```json
{
  "code": 400,
  "message": "用户名已存在",
  "details": null
}
```

## 刷新令牌

### 请求

```
POST /api/v1/auth/refresh
Content-Type: application/json
Authorization: Bearer <当前令牌>
```

**请求体：**

```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "令牌刷新成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

**失败：**

```json
{
  "code": 401,
  "message": "刷新令牌无效",
  "details": null
}
```
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
