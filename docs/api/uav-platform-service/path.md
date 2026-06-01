# 路径规划接口

> ⚠️ **注意**: 以下接口为计划中的 API 定义，当前版本尚未实现完整 CRUD。
> 当前可用的路径规划接口：`POST /api/platform/plan`（PlatformController）

## 生成路径规划

### 请求

```
POST /api/v1/path-planning/generate
Content-Type: application/json
Authorization: Bearer <JWT令牌>
```

**请求体：**

```json
{
  "taskId": 1,
  "droneId": 1,
  "startLocation": {
    "latitude": 39.9042,
    "longitude": 116.4074,
    "altitude": 0
  },
  "waypoints": [
    {
      "latitude": 39.9142,
      "longitude": 116.4174,
      "altitude": 100,
      "timeWindow": {
        "start": "2024-01-01T00:00:00Z",
        "end": "2024-01-01T00:30:00Z"
      }
    },
    {
      "latitude": 39.9242,
      "longitude": 116.4274,
      "altitude": 100,
      "timeWindow": {
        "start": "2024-01-01T00:30:00Z",
        "end": "2024-01-01T01:00:00Z"
      }
    }
  ],
  "constraints": {
    "maxSpeed": 50,
    "maxAltitude": 500,
    "minBatteryLevel": 20
  }
}
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "生成路径规划成功",
  "data": {
    "pathId": 1,
    "taskId": 1,
    "droneId": 1,
    "path": [
      {
        "latitude": 39.9042,
        "longitude": 116.4074,
        "altitude": 0,
        "timestamp": "2024-01-01T00:00:00Z"
      },
      {
        "latitude": 39.9142,
        "longitude": 116.4174,
        "altitude": 100,
        "timestamp": "2024-01-01T00:15:00Z"
      },
      {
        "latitude": 39.9242,
        "longitude": 116.4274,
        "altitude": 100,
        "timestamp": "2024-01-01T00:30:00Z"
      }
    ],
    "estimatedDuration": 30,
    "estimatedBatteryUsage": 15
  }
}
```

**失败：**

```json
{
  "code": 400,
  "message": "路径规划失败",
  "details": "无法生成有效的路径"
}
```

## 获取路径规划详情

### 请求

```
GET /api/v1/path-planning/{id}
Authorization: Bearer <JWT令牌>
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "获取路径规划详情成功",
  "data": {
    "id": 1,
    "taskId": 1,
    "droneId": 1,
    "status": "GENERATED",
    "path": [
      {
        "latitude": 39.9042,
        "longitude": 116.4074,
        "altitude": 0,
        "timestamp": "2024-01-01T00:00:00Z"
      },
      {
        "latitude": 39.9142,
        "longitude": 116.4174,
        "altitude": 100,
        "timestamp": "2024-01-01T00:15:00Z"
      },
      {
        "latitude": 39.9242,
        "longitude": 116.4274,
        "altitude": 100,
        "timestamp": "2024-01-01T00:30:00Z"
      }
    ],
    "estimatedDuration": 30,
    "estimatedBatteryUsage": 15,
    "createdAt": "2024-01-01T00:00:00Z"
  }
}
```

**失败：**

```json
{
  "code": 404,
  "message": "路径规划不存在",
  "details": null
}
```

## 更新路径规划

### 请求

```
PUT /api/v1/path-planning/{id}
Content-Type: application/json
Authorization: Bearer <JWT令牌>
```

**请求体：**

```json
{
  "status": "EXECUTING",
  "currentWaypointIndex": 1
}
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "更新路径规划成功",
  "data": {
    "id": 1,
    "taskId": 1,
    "droneId": 1,
    "status": "EXECUTING",
    "currentWaypointIndex": 1,
    "updatedAt": "2024-01-01T00:15:00Z"
  }
}
```

**失败：**

```json
{
  "code": 404,
  "message": "路径规划不存在",
  "details": null
}
```

## 获取任务的路径规划列表

### 请求

```
GET /api/v1/tasks/{taskId}/path-planning
Authorization: Bearer <JWT令牌>
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "获取路径规划列表成功",
  "data": [
    {
      "id": 1,
      "droneId": 1,
      "status": "EXECUTING",
      "estimatedDuration": 30,
      "createdAt": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "droneId": 2,
      "status": "PENDING",
      "estimatedDuration": 45,
      "createdAt": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**失败：**

```json
{
  "code": 404,
  "message": "任务不存在",
  "details": null
}
```
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
