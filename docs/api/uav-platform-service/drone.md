# 无人机管理接口

> ⚠️ **注意**: 以下接口为计划中的 API 定义，当前版本尚未实现完整 CRUD。
> 当前可用的无人机接口：`GET /api/platform/drones`（PlatformController）

## 获取无人机列表

### 请求

```
GET /api/v1/drones
Authorization: Bearer <JWT令牌>
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "获取无人机列表成功",
  "data": [
    {
      "id": 1,
      "name": "Drone-001",
      "model": "DJI Mavic Pro",
      "status": "AVAILABLE",
      "batteryLevel": 85,
      "lastPosition": {
        "latitude": 39.9042,
        "longitude": 116.4074,
        "altitude": 0
      },
      "createdAt": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "name": "Drone-002",
      "model": "DJI Phantom 4",
      "status": "IN_USE",
      "batteryLevel": 60,
      "lastPosition": {
        "latitude": 39.9142,
        "longitude": 116.4174,
        "altitude": 100
      },
      "createdAt": "2024-01-01T00:00:00Z"
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

## 获取无人机详情

### 请求

```
GET /api/v1/drones/{id}
Authorization: Bearer <JWT令牌>
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "获取无人机详情成功",
  "data": {
    "id": 1,
    "name": "Drone-001",
    "model": "DJI Mavic Pro",
    "status": "AVAILABLE",
    "batteryLevel": 85,
    "lastPosition": {
      "latitude": 39.9042,
      "longitude": 116.4074,
      "altitude": 0
    },
    "maxSpeed": 50,
    "maxAltitude": 500,
    "payloadCapacity": 1.0,
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z"
  }
}
```

**失败：**

```json
{
  "code": 404,
  "message": "无人机不存在",
  "details": null
}
```

## 创建无人机

### 请求

```
POST /api/v1/drones
Content-Type: application/json
Authorization: Bearer <JWT令牌>
```

**请求体：**

```json
{
  "name": "Drone-003",
  "model": "DJI Air 2S",
  "maxSpeed": 68,
  "maxAltitude": 600,
  "payloadCapacity": 0.5
}
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "创建无人机成功",
  "data": {
    "id": 3,
    "name": "Drone-003",
    "model": "DJI Air 2S",
    "status": "AVAILABLE",
    "batteryLevel": 100,
    "maxSpeed": 68,
    "maxAltitude": 600,
    "payloadCapacity": 0.5,
    "createdAt": "2024-01-01T00:00:00Z"
  }
}
```

**失败：**

```json
{
  "code": 400,
  "message": "请求参数错误",
  "details": "无人机名称已存在"
}
```

## 更新无人机

### 请求

```
PUT /api/v1/drones/{id}
Content-Type: application/json
Authorization: Bearer <JWT令牌>
```

**请求体：**

```json
{
  "name": "Updated Drone",
  "status": "MAINTENANCE",
  "batteryLevel": 50
}
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "更新无人机成功",
  "data": {
    "id": 1,
    "name": "Updated Drone",
    "model": "DJI Mavic Pro",
    "status": "MAINTENANCE",
    "batteryLevel": 50,
    "lastPosition": {
      "latitude": 39.9042,
      "longitude": 116.4074,
      "altitude": 0
    },
    "updatedAt": "2024-01-01T00:30:00Z"
  }
}
```

**失败：**

```json
{
  "code": 404,
  "message": "无人机不存在",
  "details": null
}
```

## 删除无人机

### 请求

```
DELETE /api/v1/drones/{id}
Authorization: Bearer <JWT令牌>
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "删除无人机成功",
  "data": null
}
```

**失败：**

```json
{
  "code": 404,
  "message": "无人机不存在",
  "details": null
}
```
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
