# FengLei Weather Service

## 概述

风雷（FengLei）区域模式数据服务，基于 CMA GRAPES_MESO 中尺度模式，提供高分辨率（3km）区域气象预报数据。

## 功能特性

- 高分辨率气象数据分析（3km 分辨率）
- 支持多种分析模式：分析、预报
- 轻量级风场查询接口（专为无人机路径规划优化）
- API Key 认证
- Spring Boot Actuator 兼容的健康检查

## 环境变量

| 变量名 | 必填 | 说明 | 默认值 |
|--------|------|------|--------|
| FENGLEI_API_KEY | 生产环境必填 | API 密钥 | 空（开发环境禁用认证） |
| FENGLEI_CACHE_DIR | 否 | 缓存目录 | `/app/cache` |
| FENGLEI_UPDATE_INTERVAL | 否 | 更新间隔（分钟） | `30` |
| FENGLEI_ENV | 否 | 运行环境 | `production` |
| CORS_ORIGINS | 生产环境必填 | 允许的 CORS 源 | `*` |

## API 端点

### 健康检查

```
GET /health
GET /health/ready
```

### 模型信息

```
GET /api/v1/model/info
```

### 气象预报

```
POST /api/v1/forecast
```

**请求体:**
```json
{
  "fcst_hour": 0,
  "variables": ["u10", "v10", "t2m", "rh2m", "ps", "blh"]
}
```

### 风场查询

```
GET /api/v1/forecast/wind-field?fcst_hour=0
```

### 实时分析

```
GET /api/v1/analysis
```

## 技术栈

- Python 3.11+
- FastAPI
- xarray
- cfgrib
- netCDF4

## 部署

### Docker

```bash
docker build -t fenglei-service .
docker run -p 8091:8091 \
  -e FENGLEI_API_KEY=your-key \
  fenglei-service
```

### Docker Compose

```yaml
services:
  fenglei-service:
    build: ./fenglei-service
    ports:
      - "8091:8091"
    environment:
      - FENGLEI_API_KEY=${FENGLEI_API_KEY}
      - CORS_ORIGINS=${CORS_ORIGINS}
```

## 开发

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8091 --reload
```

访问 Swagger UI: http://localhost:8091/docs