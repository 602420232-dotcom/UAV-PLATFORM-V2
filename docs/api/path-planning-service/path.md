# 路径规划服务API

路径规划服务提供无人机路径规划，采用VRPTW+DE-RRT*+DWA三层架构。

## 接口列表

### 1. VRPTW任务调度

**接口地址**：`POST /api/planning/vrptw`

**功能**：多无人机任务分配与排序

**请求参数**：JSON
```json
{
  "drones": [...],
  "tasks": [...],
  "weather_data": {...}
}
```

**响应**：
```json
{
  "success": true,
  "data": { "routes": [...], "unassigned_tasks": [] }
}
```

### 2. A* 全局路径规划

**接口地址**：`POST /api/planning/astar`

**功能**：A* 全局路径规划

### 3. DWA 实时避障

**接口地址**：`POST /api/planning/dwa`

**功能**：DWA 实时避障

### 4. 完整三层路径规划

**接口地址**：`POST /api/planning/full`

**功能**：VRPTW → DE-RRT* → DWA 完整三层路径规划
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
