# WRF处理服务API

WRF处理服务提供气象数据的解析和处理功能，支持从WRF输出文件中提取低空气象参数。

## 接口列表

### 1. 解析WRF文件

**接口地址**：`POST /api/wrf/parse`

**功能**：解析WRF输出的NetCDF4文件，提取气象数据

**请求参数**：`multipart/form-data`
- `file`：WRF输出的NetCDF4文件

**响应**：
```json
{
  "success": true,
  "data": { "file_id": "wrf_xxx", "variables": ["temperature", "humidity"], "time_steps": 24 }
}
```

### 2. 获取处理后的气象数据

**接口地址**：`GET /api/wrf/data`

**功能**：获取解析后的气象数据

**请求参数**：Query
- `fileId`：文件ID

**响应**：
```json
{
  "success": true,
  "data": { "variable": "temperature", "grid": {...} }
}
```

### 3. 获取数据统计信息

**接口地址**：`GET /api/wrf/stats`

**功能**：获取气象数据的统计信息

**请求参数**：Query
- `fileId`：文件ID

**响应**：
```json
{
  "success": true,
  "data": { "statistics": { "min": 15.2, "max": 25.8, "mean": 20.5 } }
}
```
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
