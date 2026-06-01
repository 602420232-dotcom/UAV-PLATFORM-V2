# 边云协同服务 API

边云协同服务（edge-cloud-coordinator）实现无人机与云端之间的分布式智能计算，支持任务编排、实时流处理、联邦学习和WebSocket同步。

## 服务信息

- **服务名称**: edge-cloud-coordinator
- **端口**: 8000 (REST) / 8765 (WebSocket)
- **文档地址**: http://localhost:8000/docs

## 接口列表

### 1. 健康检查

**接口地址**：`GET /health`

**功能**：健康检查

**响应**：
```json
{
  "status": "healthy"
}
```

### 2. 提交任务

**接口地址**：`POST /tasks`

**功能**：提交任务到边云协调器，根据任务类型自动分配到云端或边缘处理

**请求参数**：
```json
{
  "task_type": "global_path",
  "priority": 5,
  "data": {...},
  "deadline": 60.0
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_type | string | 是 | 任务类型: global_path, local_avoidance, sensor_fusion, model_update, batch_processing |
| priority | int | 否 | 优先级 1-10，默认5 |
| data | object | 否 | 任务数据 |
| deadline | float | 否 | 截止时间（秒），默认60 |

**响应**：
```json
{
  "task_id": "task_1",
  "status": "submitted",
  "message": "任务已提交到global_path队列"
}
```

### 3. 查询任务状态

**接口地址**：`GET /tasks/{task_id}`

**功能**：查询指定任务的状态

**响应**：
```json
{
  "task_id": "task_1",
  "task_type": "global_path",
  "priority": 5,
  "status": "completed",
  "result": {...}
}
```

### 4. 取消任务

**接口地址**：`DELETE /tasks/{task_id}`

**功能**：取消指定任务

**响应**：
```json
{
  "message": "任务 task_1 已取消"
}
```

### 5. 获取任务列表

**接口地址**：`GET /tasks?status=completed&limit=10`

**功能**：获取任务列表

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 状态过滤: completed |
| limit | int | 否 | 返回数量限制，默认10 |

**响应**：
```json
[
  {
    "task_id": "task_1",
    "task_type": "global_path",
    "priority": 5,
    "status": "completed"
  }
]
```

### 6. 获取系统状态

**接口地址**：`GET /status`

**功能**：获取边云协调器系统状态

**响应**：
```json
{
  "node_id": "edge-node-001",
  "queue_size": 5,
  "completed_count": 120,
  "cloud_connected": true,
  "edge_connected": true,
  "buffer_size": 0
}
```

### 7. 同步云端模型

**接口地址**：`POST /sync`

**功能**：同步云端模型到边缘节点

**响应**：
```json
{
  "message": "云端同步完成",
  "models": ["path_planner", "weather_model"]
}
```

### 8. 上传边缘数据

**接口地址**：`POST /upload`

**功能**：上传边缘数据到云端（异步）

**响应**：
```json
{
  "message": "数据上传任务已提交"
}
```

### 9. 列出可用模型

**接口地址**：`GET /models`

**功能**：列出云端和本地可用模型

**响应**：
```json
{
  "cloud_models": ["path_planner_v2", "weather_model_v3"],
  "local_models": ["local_path_planner"]
}
```

### 10. 批量提交任务

**接口地址**：`POST /tasks/batch`

**功能**：批量提交多个任务

**请求参数**：
```json
[
  {
    "task_type": "sensor_fusion",
    "priority": 8,
    "data": {...}
  },
  {
    "task_type": "local_avoidance",
    "priority": 10,
    "data": {...}
  }
]
```

**响应**：
```json
{
  "results": [
    {"task_id": "task_2", "status": "submitted"},
    {"task_id": "task_3", "status": "submitted"}
  ]
}
```

## 联邦学习接口

### 11. 接收联邦学习客户端更新

**接口地址**：`POST /fl/update`

**功能**：接收无人机客户端的模型更新

**请求参数**：
```json
{
  "drone_id": "UAV-001",
  "weights": {"layer1": [[1.0, 2.0], [3.0, 4.0]], "layer2": [0.5]},
  "n_samples": 100,
  "metrics": {"accuracy": 0.85}
}
```

**响应**：
```json
{
  "aggregated": true,
  "round_id": 5,
  "global_accuracy": 0.88
}
```

### 12. 获取联邦学习状态

**接口地址**：`GET /fl/status`

**功能**：获取联邦学习当前状态

**响应**：
```json
{
  "strategy": "FedAvg",
  "min_clients": 2,
  "round_id": 5,
  "clients_this_round": 3,
  "global_accuracy": 0.88,
  "total_rounds": 10
}
```

### 13. 获取联邦学习历史

**接口地址**：`GET /fl/history`

**功能**：获取联邦学习训练历史

**响应**：
```json
{
  "rounds": [
    {"round_id": 1, "accuracy": 0.75},
    {"round_id": 2, "accuracy": 0.80}
  ]
}
```

### 14. 模拟本地训练

**接口地址**：`POST /fl/train`

**功能**：模拟无人机本地训练

**请求参数**：
```json
{
  "drone_id": "UAV-001",
  "epochs": 5,
  "n_samples": 100
}
```

**响应**：
```json
{
  "drone_id": "UAV-001",
  "n_samples": 100,
  "metrics": {"accuracy": 0.85},
  "aggregated": true
}
```

## WebSocket 实时同步

### 连接地址

```
ws://localhost:8765/ws
```

### 消息格式

**客户端发送**：
```json
{
  "type": "subscribe",
  "channel": "drone_status"
}
```

**服务端推送**：
```json
{
  "type": "drone_update",
  "drone_id": "UAV-001",
  "position": {"lat": 39.9042, "lng": 116.4074, "alt": 100},
  "timestamp": 1712000000000
}
```

## 错误响应

所有接口返回统一的错误格式：
```json
{
  "detail": "错误信息"
}
```

常见HTTP状态码：
- `400`: 请求参数错误
- `404`: 资源不存在
- `500`: 服务器内部错误
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
