# 无人机气象信息收集服务 API

无人机气象信息收集服务（uav-weather-collector）对接多源气象数据，为路径规划提供实时气象信息支撑。

## 接口列表

### 1. 采集无人机传感器数据

**接口地址**：`POST /api/weather/collect/uav`

**功能**：接收无人机机载传感器实时气象数据

**请求参数**：
```json
{
  "drone_id": "UAV-001",
  "latitude": 39.9042,
  "longitude": 116.4074,
  "altitude": 100,
  "temperature": 25.0,
  "humidity": 60,
  "wind_speed": 4.2,
  "wind_direction": 180,
  "wind_gust": 6.1,
  "pressure": 1013.25,
  "visibility": 10,
  "turbulence": 0.1,
  "precipitation": 0
}
```

**响应**：
```json
{
  "success": true,
  "drone_id": "UAV-001",
  "data_quality": 0.9
}
```

### 2. 采集WRF模型数据

**接口地址**：`POST /api/weather/collect/wrf`

**功能**：接收WRF模型预报数据

### 3. 采集地面站数据

**接口地址**：`POST /api/weather/collect/ground`

**功能**：接收地面气象站观测数据

### 4. 获取无人机实时气象

**接口地址**：`GET /api/weather/drone/{droneId}`

**功能**：获取指定无人机最新气象数据

**响应**：
```json
{
  "success": true,
  "data": { "temperature": 25.0, "wind_speed": 4.2, "timestamp": 1712000000000 }
}
```

### 5. 获取气象历史

**接口地址**：`GET /api/weather/drone/{droneId}/history?minutes=10`

**功能**：获取指定无人机历史气象数据（默认最近10分钟）

### 6. 获取多源融合气象

**接口地址**：`GET /api/weather/fusion/{droneId}`

**功能**：获取多源融合气象（传感器70% + WRF 30% 加权融合）

**响应**：
```json
{
  "success": true,
  "drone_id": "UAV-001",
  "wind_speed": 4.5,
  "temperature": 25.0,
  "humidity": 60,
  "source_fusion": "sensor+wrf"
}
```

### 7. 气象告警评估

**接口地址**：`POST /api/weather/alert`

**功能**：评估气象是否触发告警

**响应**：
```json
{
  "has_alert": true,
  "warnings": ["风速告警: 13.5m/s"],
  "level": "MEDIUM"
}
```

### 8. 获取告警记录

**接口地址**：`GET /api/weather/alerts/{droneId}`

**功能**：获取指定无人机的历史告警记录

### 9. 获取数据源列表

**接口地址**：`GET /api/weather/sources`

**功能**：获取所有可用气象数据源

**响应**：
```json
{
  "sources": [
    { "id": "wrf", "name": "WRF模型", "type": "model", "status": "online" },
    { "id": "uav_sensor", "name": "无人机传感器", "type": "sensor", "status": "online" }
  ]
}
```

## 数据源

| 数据源 | 类型 | 说明 |
|--------|------|------|
| WRF 模型 | model | WRF 数值天气预报模型输出 |
| 无人机传感器 | sensor | 机载气象传感器实时数据 |
| 地面气象站 | station | 地面自动气象站观测数据 |
| 卫星遥感 | satellite | 气象卫星遥感数据 |
| 浮标站 | buoy | 海洋浮标气象数据 |

## 告警阈值

| 指标 | 阈值 | 级别 |
|------|------|------|
| 风速 | > 12 m/s | 告警 |
| 阵风 | > 18 m/s | 告警 |
| 能见度 | < 2 km | 告警 |
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
