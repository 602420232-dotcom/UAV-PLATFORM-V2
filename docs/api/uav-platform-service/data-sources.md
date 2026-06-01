# 数据源管理接口

数据源管理提供地面站、浮标、气象卫星等多源数据的CRUD操作。

## 接口列表

### 1. 获取数据源列表

**接口地址**：`GET /api/v1/data-sources`

**功能**：获取所有数据源

**响应**：
```json
{
  "code": 200,
  "message": "获取数据源列表成功",
  "data": [
    {"id": 1, "name": "地面站数据源", "type": "ground_station", "status": "active"},
    {"id": 2, "name": "浮标数据源", "type": "buoy", "status": "active"}
  ]
}
```

### 2. 获取数据源详情

**接口地址**：`GET /api/v1/data-sources/{id}`

### 3. 创建数据源

**接口地址**：`POST /api/v1/data-sources`

### 4. 更新数据源

**接口地址**：`PUT /api/v1/data-sources/{id}`

### 5. 删除数据源

**接口地址**：`DELETE /api/v1/data-sources/{id}`

### 6. 测试数据源

**接口地址**：`POST /api/v1/data-sources/test`

### 7. 获取数据源类型列表

**接口地址**：`GET /api/v1/data-sources/types`

### 8. 获取地面站数据

**接口地址**：`GET /api/v1/real-data/ground-station`

**功能**：获取实时地面站观测数据

### 9. 获取浮标数据

**接口地址**：`GET /api/v1/real-data/buoy`

**功能**：获取实时海洋浮标数据

### 10. 获取数据源状态

**接口地址**：`GET /api/v1/real-data/status`

**功能**：获取各数据源的连接状态和最新更新时间
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
