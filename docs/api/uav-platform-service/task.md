# 任务管理接口

> ⚠️ **注意**: 以下接口为计划中的 API 定义，当前版本尚未实现完整 CRUD。
> 当前可用的任务接口：`POST /api/platform/task`（PlatformController）

## 获取任务列表

### 请求

```
GET /api/v1/tasks
Authorization: Bearer <JWT令牌>
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "获取任务列表成功",
  "data": [
    {
      "id": 1,
      "name": "巡逻任务1",
      "description": "区域巡逻任务",
      "status": "PENDING",
      "startTime": "2024-01-01T00:00:00Z",
      "endTime": "2024-01-01T02:00:00Z",
      "createdAt": "2024-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "name": "监测任务2",
      "description": "环境监测任务",
      "status": "IN_PROGRESS",
      "startTime": "2024-01-01T01:00:00Z",
      "endTime": "2024-01-01T03:00:00Z",
      "createdAt": "2024-01-01T00:30:00Z"
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

## 获取任务详情

### 请求

```
GET /api/v1/tasks/{id}
Authorization: Bearer <JWT令牌>
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "获取任务详情成功",
  "data": {
    "id": 1,
    "name": "巡逻任务1",
    "description": "区域巡逻任务",
    "status": "PENDING",
    "startTime": "2024-01-01T00:00:00Z",
    "endTime": "2024-01-01T02:00:00Z",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z",
    "waypoints": [
      {
        "id": 1,
        "latitude": 39.9042,
        "longitude": 116.4074,
        "altitude": 100,
        "order": 1
      },
      {
        "id": 2,
        "latitude": 39.9142,
        "longitude": 116.4174,
        "altitude": 100,
        "order": 2
      }
    ]
  }
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

## 创建任务

### 请求

```
POST /api/v1/tasks
Content-Type: application/json
Authorization: Bearer <JWT令牌>
```

**请求体：**

```json
{
  "name": "新任务",
  "description": "任务描述",
  "startTime": "2024-01-01T00:00:00Z",
  "endTime": "2024-01-01T02:00:00Z",
  "waypoints": [
    {
      "latitude": 39.9042,
      "longitude": 116.4074,
      "altitude": 100,
      "order": 1
    },
    {
      "latitude": 39.9142,
      "longitude": 116.4174,
      "altitude": 100,
      "order": 2
    }
  ]
}
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "创建任务成功",
  "data": {
    "id": 3,
    "name": "新任务",
    "description": "任务描述",
    "status": "PENDING",
    "startTime": "2024-01-01T00:00:00Z",
    "endTime": "2024-01-01T02:00:00Z",
    "createdAt": "2024-01-01T00:00:00Z"
  }
}
```

**失败：**

```json
{
  "code": 400,
  "message": "请求参数错误",
  "details": "结束时间必须晚于开始时间"
}
```

## 更新任务

### 请求

```
PUT /api/v1/tasks/{id}
Content-Type: application/json
Authorization: Bearer <JWT令牌>
```

**请求体：**

```json
{
  "name": "更新任务",
  "description": "更新任务描述",
  "status": "IN_PROGRESS",
  "endTime": "2024-01-01T03:00:00Z"
}
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "更新任务成功",
  "data": {
    "id": 1,
    "name": "更新任务",
    "description": "更新任务描述",
    "status": "IN_PROGRESS",
    "startTime": "2024-01-01T00:00:00Z",
    "endTime": "2024-01-01T03:00:00Z",
    "updatedAt": "2024-01-01T00:30:00Z"
  }
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

## 删除任务

### 请求

```
DELETE /api/v1/tasks/{id}
Authorization: Bearer <JWT令牌>
```

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "删除任务成功",
  "data": null
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
