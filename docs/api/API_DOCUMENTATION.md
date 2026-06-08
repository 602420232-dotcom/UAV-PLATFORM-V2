# UAV Path Planning System — API 文档

## 一、API 网关路由表

| 路由前缀 | 目标服务 | 端口 |
|----------|----------|:----:|
| `/api/v1/auth/**` | uav-platform-service | 8080 |
| `/api/v1/data-sources/**` | uav-platform-service | 8080 |
| `/api/v1/real-data/**` | uav-platform-service | 8080 |
| `/api/platform/**` | uav-platform-service | 8080 |
| `/api/wrf/**` | wrf-processor-service | 8081 |
| `/api/assimilation/**` | data-assimilation-service | 8084 |
| `/api/forecast/**` | meteor-forecast-service | 8082 |
| `/api/planning/**` | path-planning-service | 8083 |
| `/api/weather/**` | uav-weather-collector | 8086 |
| `/api/fengwu/**` | fengwu-service | 8085 |
| `/api/tianzi/**` | tianzi-service | 8090 |

## 二、认证服务 (uav-platform-service :8080)

### POST /api/v1/auth/register
注册新用户
```json
{"username":"user","password":"pass","email":"user@test.com","fullName":"Test User"}
```

### POST /api/v1/auth/login
登录获取JWT Token
```json
{"username":"user","password":"pass"}
```

### POST /api/v1/auth/refresh
刷新 JWT Token
```json
{"refreshToken":"your_refresh_token"}
```

### POST /api/v1/auth/logout
用户登出

## 三、数据源管理 (uav-platform-service :8080)

### GET /api/v1/data-sources
获取数据源列表 → `200 {"code":200,"data":[...]}`

### GET /api/v1/data-sources/{id}
按ID获取数据源详情 → `200 / 404 DataNotFoundException`

### POST /api/v1/data-sources
创建数据源 → `200 {"code":200,"data":{...}}`

### PUT /api/v1/data-sources/{id}
更新数据源 → `200 / 404`

### DELETE /api/v1/data-sources/{id}
删除数据源 → `200 / 404`

### POST /api/v1/data-sources/test
测试数据源连接 → `200 {"code":200,"data":{"success":true}}`

### GET /api/v1/data-sources/types
获取数据源类型列表 → `200 {"code":200,"data":[...]}`

## 四、实时数据 (uav-platform-service :8080)

### GET /api/v1/real-data/ground-station
获取地面站实时数据 → `200 {"code":200,"data":[...]}`

### GET /api/v1/real-data/buoy
获取浮标实时数据 → `200 {"code":200,"data":[...]}`

### GET /api/v1/real-data/status
获取数据源状态 → `200 {"code":200,"data":{...}}`

## 五、平台编排 (uav-platform-service :8080)

### POST /api/platform/plan
提交完整规划流程（WRF解析→贝叶斯同化→气象预测→路径规划）
```json
{"weatherData":{},"drones":[],"tasks":[]}
```

### GET /api/platform/weather?fileId={id}
获取气象数据 → `200 {"success":true,"data":{...}}`

### POST /api/platform/task
任务管理 → `200 {"success":true,"message":"任务管理成功"}`

### GET /api/platform/drones
获取无人机列表 → `200 {"success":true,"data":[]}`

### GET /api/platform/health
健康检查 → `200 {"success":true,"status":"UP"}`

## 六、WRF气象处理 (wrf-processor-service :8081)

### POST /api/wrf/upload
上传NetCDF气象文件
- 支持格式: `.nc`, `.netcdf`
- 验证: 文件名不得包含路径遍历字符
- 内容类型: multipart/form-data

### GET /api/wrf/weather/{fileId}
获取气象数据 → `200 {"success":true,"data":{...}}`

### GET /api/wrf/statistics/{fileId}
获取统计信息 → `200 {"success":true,"data":{...}}`

## 七、数据同化 (data-assimilation-service :8084)

### POST /api/assimilation/execute
执行3D-Var/4D-Var/EnKF同化
```json
{"algorithm":"3dvar","background":{},"observations":{},"config":{}}
```

### POST /api/assimilation/variance
计算方差场

### POST /api/assimilation/batch
批量同化处理

## 八、气象预测 (meteor-forecast-service :8082)

### POST /api/forecast/predict
气象预测 (LSTM/XGBoost/Hybrid)
```json
{"method":"lstm","data":{"latitude":39.9,"longitude":116.4},"config":{}}
```

### POST /api/forecast/correct
数据订正

### GET /api/forecast/models
获取可用模型列表

## 九、路径规划 (path-planning-service :8083)

### POST /api/planning/vrptw
VRPTW路径规划
```json
{"algorithm":"vrptw","drones":{},"tasks":{},"weatherData":{}}
```

### POST /api/planning/astar
A*全局路径规划

### POST /api/planning/dwa
DWA局部路径规划

### POST /api/planning/full
三层完整路径规划（全局+局部+动态避障）

## 十、气象采集 (uav-weather-collector :8086)

### POST /api/weather/collect
采集无人机传感器数据

### GET /api/weather/drone/{droneId}
获取无人机气象数据

### GET /api/weather/history/{droneId}/{minutes}
获取气象历史

### GET /api/weather/fused/{droneId}
获取融合气象数据

### GET /api/weather/sources
获取可用数据源列表

### GET /api/weather/alerts/{droneId}
获取无人机告警

## 十一、FengWu 气象模型 (fengwu-service :8085) [Python FastAPI]

### POST /api/fengwu/forecast
全球气象预测（基于 ONNX 推理引擎）
```json
{
  "input_0h": [[[...]]],
  "input_6h": [[[...]]],
  "steps": 56,
  "surface_only": true
}
```
**参数说明:**
- `input_0h`: T+0h 时刻的 ERA5 大气数据，形状 (69, 721, 1440)
- `input_6h`: T+6h 时刻的 ERA5 大气数据，形状 (69, 721, 1440)
- `steps`: 预测步数，1~56，每步 6 小时
- `surface_only`: 仅返回地表变量（u10、v10、t2m、msl）

### POST /api/fengwu/wind
风场快速查询（轻量级端点，适用于无人机路径规划）
```json
{
  "latitude": 39.9,
  "longitude": 116.4,
  "height": 100
}
```

### GET /api/fengwu/model/info
获取模型信息 → `200 {"model":"FengWu","version":"1.0","variables":69}`

### GET /api/fengwu/health
健康检查 → `200 {"success":true,"status":"UP","model_loaded":true}`

## 十二、TianZi 高分辨率分析 (tianzi-service :8090) [Python FastAPI]

基于 TianZi 深度学习模型的高分辨率气象分析服务。

### POST /api/tianzi/analysis
高分辨率气象分析
```json
{
  "observation_data": [[[...]]],
  "background_data": [[[...]]],
  "analysis_type": "analysis",
  "resolution_km": 1.0
}
```
**参数说明:**
- `observation_data`: 观测数据网格，形状 (variables, lat, lon)
- `background_data`: 可选背景场数据，用于同化
- `analysis_type`: 分析类型，可选值: `analysis`, `forecast`, `assimilation`
- `resolution_km`: 目标分辨率（公里），最高 1km

**响应示例:**
```json
{
  "status": "success",
  "model": "tianzi.onnx",
  "analysis_type": "analysis",
  "resolution_km": 1.0,
  "computation_time_s": 2.5,
  "results": [
    {"variable": "u10", "data": [[...]], "units": "m/s", "description": "10m U wind component"},
    {"variable": "v10", "data": [[...]], "units": "m/s", "description": "10m V wind component"},
    {"variable": "t2m", "data": [[...]], "units": "K", "description": "2m temperature"},
    {"variable": "msl", "data": [[...]], "units": "Pa", "description": "Mean sea level pressure"},
    {"variable": "rh2m", "data": [[...]], "units": "%", "description": "2m relative humidity"},
    {"variable": "precip", "data": [[...]], "units": "mm/h", "description": "Precipitation rate"}
  ]
}
```

### POST /api/tianzi/analysis/wind-field
风场快速查询（轻量级端点，适用于无人机路径规划）
```json
{
  "observation_data": [[[...]]],
  "resolution_km": 1.0
}
```

**响应示例:**
```json
{
  "status": "success",
  "model": "tianzi.onnx",
  "resolution_km": 1.0,
  "u10": [[...]],
  "v10": [[...]],
  "wind_speed_avg": 5.2,
  "wind_speed_max": 15.8,
  "wind_speed_min": 0.3
}
```

### GET /api/tianzi/model/info
获取模型信息 → `200 {"model":"TianZi","version":"1.0","variables":12,"max_resolution_km":1.0}`

### GET /api/tianzi/health
健康检查 → `200 {"status":"UP","model_loaded":true,"model_path":"/app/model/tianzi.onnx","uptime_seconds":3600}`

## 十三、边云协同 (edge-cloud-coordinator :8000 REST / :8765 WebSocket) [Python FastAPI]

> 📘 完整 OpenAPI 文档：[openapi.yaml](edge-cloud-coordinator/openapi.yaml) | 在线 Swagger：启动后访问 http://localhost:8000/docs

### GET /health
健康检查 → `200 {"status":"healthy"}`

### POST /tasks
提交边云任务（自动分配到云端或边缘处理）
```json
{"task_type":"global_path","priority":5,"data":{},"deadline":60.0}
```

### GET /tasks/{task_id}
查询任务状态 → `200 {"task_id":"task_1","status":"completed","result":{}}`

### GET /tasks?status=completed&limit=10
获取任务列表

### DELETE /tasks/{task_id}
取消任务

### POST /tasks/batch
批量提交任务（上限 100 个）

### GET /status
获取系统状态（节点ID、队列大小、云端/边缘连接状态）

### POST /sync
同步云端模型到边缘节点 → `200 {"models":["path_planner","weather_model"]}`

### POST /upload
上传边缘数据到云端（异步后台任务）

### GET /models
列出可用模型（云端 + 本地）

### 联邦学习接口

| 端点 | 方法 | 说明 |
|------|:----:|------|
| `/fl/update` | POST | 接收无人机客户端的模型更新（FedAvg 聚合） |
| `/fl/status` | GET | 获取联邦学习当前状态（轮次/准确率/策略） |
| `/fl/history` | GET | 获取联邦学习训练历史 |
| `/fl/train` | POST | 模拟无人机本地训练 |

### WebSocket 实时同步

```
ws://localhost:8765/ws
```

**客户端→服务端**：订阅频道 `{"type":"subscribe","channel":"drone_status"}`  
**服务端→客户端**：推送更新 `{"type":"drone_update","drone_id":"UAV-001","position":{...}}`

## 十四、数据同化算法平台 (data-assimilation-platform) [Python]

> 路径：`data-assimilation-platform/algorithm_core/` | Java 服务封装：`data-assimilation-service` (端口 8084)

### 核心算法

| 算法 | 说明 |
|------|------|
| **3D-VAR** | 三维变分同化，最小化背景场与观测的代价函数 |
| **4D-VAR** | 四维变分同化，在时间窗口内优化初始条件 |
| **EnKF** | 集合卡尔曼滤波，蒙特卡洛近似背景误差协方差 |
| **Hybrid** | 混合方法，结合变分与集合卡尔曼滤波优势 |

### 通过 Java 服务调用 (推荐)

```bash
# 执行同化
curl -X POST http://localhost:8088/api/assimilation/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"algorithm":"3dvar","background":{},"observations":{},"config":{}}'

# 计算方差场
curl -X POST http://localhost:8088/api/assimilation/variance \
  -H "Authorization: Bearer $TOKEN"

# 批量处理
curl -X POST http://localhost:8088/api/assimilation/batch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"items":[...]}'
```

## 十五、错误码

| 状态码 | 含义 | 处理方式 |
|:------:|------|----------|
| 200 | 成功 | 正常处理 |
| 400 | 参数校验失败 | 检查请求体 |
| 401 | 未认证 | 添加JWT Token |
| 403 | 权限不足 | 检查角色权限 |
| 404 | 资源不存在 | 检查ID/路径 |
| 429 | 请求频率超限 | 稍后重试或联系管理员 |
| 500 | 服务器内部错误 | 联系运维 |
| 503 | 服务不可用（熔断器打开） | 稍后重试 |

## 十六、通用响应格式

```json
// 成功
{"code": 200, "message": "操作成功", "data": {...}}
// 失败
{"code": 400, "message": "参数错误", "error": "详细错误信息"}
```
---

> **最后更新**: 2026-06-08  
> **版本**: 2.4  
> **维护者**: DITHIOTHREITOL
