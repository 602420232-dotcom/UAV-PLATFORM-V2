# 用户管理接口

## 获取用户列表

### 请求

```
GET /api/v1/users
Authorization: Bearer <JWT令牌>
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "获取用户列表成功",
  "data": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "fullName": "Admin User",
      "roles": ["ADMIN"],
      "enabled": true
    },
    {
      "id": 2,
      "username": "dispatcher",
      "email": "dispatcher@example.com",
      "fullName": "Dispatcher User",
      "roles": ["DISPATCHER"],
      "enabled": true
    }
  ]
}
```

**失败：**

```json
{
  "code": 403,
  "message": "无权访问",
  "details": null
}
```

## 获取用户详情

### 请求

```
GET /api/v1/users/{id}
Authorization: Bearer <JWT令牌>
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "获取用户详情成功",
  "data": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "fullName": "Admin User",
    "roles": ["ADMIN"],
    "enabled": true,
    "createdAt": "2024-01-01T00:00:00Z"
  }
}
```

**失败：**

```json
{
  "code": 404,
  "message": "用户不存在",
  "details": null
}
```

## 创建用户

### 请求

```
POST /api/v1/users
Content-Type: application/json
Authorization: Bearer <JWT令牌>
```

**请求体：**

```json
{
  "username": "newuser",
  "password": "password123",
  "email": "newuser@example.com",
  "fullName": "New User",
  "roleIds": [1, 2]
}
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "创建用户成功",
  "data": {
    "id": 3,
    "username": "newuser",
    "email": "newuser@example.com",
    "fullName": "New User",
    "roles": ["USER", "DISPATCHER"]
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

## 更新用户

### 请求

```
PUT /api/v1/users/{id}
Content-Type: application/json
Authorization: Bearer <JWT令牌>
```

**请求体：**

```json
{
  "email": "updated@example.com",
  "fullName": "Updated User",
  "roleIds": [1],
  "enabled": true
}
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "更新用户成功",
  "data": {
    "id": 2,
    "username": "dispatcher",
    "email": "updated@example.com",
    "fullName": "Updated User",
    "roles": ["USER"],
    "enabled": true
  }
}
```

**失败：**

```json
{
  "code": 404,
  "message": "用户不存在",
  "details": null
}
```

## 删除用户

### 请求

```
DELETE /api/v1/users/{id}
Authorization: Bearer <JWT令牌>
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "删除用户成功",
  "data": null
}
```

**失败：**

```json
{
  "code": 404,
  "message": "用户不存在",
  "details": null
}
```
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
