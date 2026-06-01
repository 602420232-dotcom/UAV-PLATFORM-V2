# 历史数据接口

> ⚠️ **注意**: 以下接口为计划中的 API 定义，当前版本尚未实现。历史数据功能待后续版本开发。

## 获取历史任务记录

### 请求

```
GET /api/v1/history/tasks
Authorization: Bearer <JWT令牌>
```

**查询参数：**

- `startDate`: 开始日期 (ISO格式，如 2024-01-01T00:00:00Z)
- `endDate`: 结束日期 (ISO格式，如 2024-01-31T23:59:59Z)
- `status`: 任务状态 (如 COMPLETED, FAILED)
- `page`: 页码 (默认 1)
- `size`: 每页大小 (默认 10)

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "获取历史任务记录成功",
  "data": {
    "total": 100,
    "page": 1,
    "size": 10,
    "items": [
      {
        "id": 1,
        "name": "巡逻任务1",
        "status": "COMPLETED",
        "startTime": "2024-01-01T00:00:00Z",
        "endTime": "2024-01-01T02:00:00Z",
        "actualEndTime": "2024-01-01T01:55:00Z",
        "createdAt": "2024-01-01T00:00:00Z"
      },
      {
        "id": 2,
        "name": "监测任务2",
        "status": "FAILED",
        "startTime": "2024-01-01T01:00:00Z",
        "endTime": "2024-01-01T03:00:00Z",
        "actualEndTime": "2024-01-01T01:30:00Z",
        "errorMessage": "无人机电池电量不足",
        "createdAt": "2024-01-01T00:30:00Z"
      }
    ]
  }
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

## 获取历史路径记录

### 请求

```
GET /api/v1/history/paths
Authorization: Bearer <JWT令牌>
```

**查询参数：**

- `startDate`: 开始日期 (ISO格式)
- `endDate`: 结束日期 (ISO格式)
- `droneId`: 无人机ID
- `page`: 页码 (默认 1)
- `size`: 每页大小 (默认 10)

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "获取历史路径记录成功",
  "data": {
    "total": 50,
    "page": 1,
    "size": 10,
    "items": [
      {
        "id": 1,
        "taskId": 1,
        "droneId": 1,
        "status": "COMPLETED",
        "estimatedDuration": 30,
        "actualDuration": 25,
        "estimatedBatteryUsage": 15,
        "actualBatteryUsage": 12,
        "createdAt": "2024-01-01T00:00:00Z",
        "completedAt": "2024-01-01T01:55:00Z"
      },
      {
        "id": 2,
        "taskId": 2,
        "droneId": 2,
        "status": "FAILED",
        "estimatedDuration": 45,
        "actualDuration": 30,
        "estimatedBatteryUsage": 20,
        "actualBatteryUsage": 15,
        "errorMessage": "无人机电池电量不足",
        "createdAt": "2024-01-01T01:00:00Z",
        "completedAt": "2024-01-01T01:30:00Z"
      }
    ]
  }
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

## 获取无人机历史状态

### 请求

```
GET /api/v1/history/drones/{droneId}/status
Authorization: Bearer <JWT令牌>
```

**查询参数：**

- `startDate`: 开始日期 (ISO格式)
- `endDate`: 结束日期 (ISO格式)
- `page`: 页码 (默认 1)
- `size`: 每页大小 (默认 10)

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "获取无人机历史状态成功",
  "data": {
    "total": 200,
    "page": 1,
    "size": 10,
    "items": [
      {
        "id": 1,
        "droneId": 1,
        "status": "AVAILABLE",
        "batteryLevel": 85,
        "position": {
          "latitude": 39.9042,
          "longitude": 116.4074,
          "altitude": 0
        },
        "timestamp": "2024-01-01T00:00:00Z"
      },
      {
        "id": 2,
        "droneId": 1,
        "status": "IN_USE",
        "batteryLevel": 80,
        "position": {
          "latitude": 39.9142,
          "longitude": 116.4174,
          "altitude": 100
        },
        "timestamp": "2024-01-01T00:15:00Z"
      }
    ]
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

## 获取历史气象数据

### 请求

```
GET /api/v1/history/weather
Authorization: Bearer <JWT令牌>
```

**查询参数：**

- `startDate`: 开始日期 (ISO格式)
- `endDate`: 结束日期 (ISO格式)
- `latitude`: 纬度
- `longitude`: 经度
- `radius`: 半径 (公里)

### 响应

**成功：**

```json
{
  "code": 200,
  "message": "获取历史气象数据成功",
  "data": [
    {
      "id": 1,
      "latitude": 39.9042,
      "longitude": 116.4074,
      "timestamp": "2024-01-01T00:00:00Z",
      "temperature": 25.5,
      "humidity": 60,
      "windSpeed": 10.5,
      "windDirection": 180,
      "pressure": 1013.25
    },
    {
      "id": 2,
      "latitude": 39.9042,
      "longitude": 116.4074,
      "timestamp": "2024-01-01T01:00:00Z",
      "temperature": 24.8,
      "humidity": 65,
      "windSpeed": 9.8,
      "windDirection": 175,
      "pressure": 1012.8
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
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
