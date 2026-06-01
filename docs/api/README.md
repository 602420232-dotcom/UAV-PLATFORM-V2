# API 文档

本文档提供了无人机路径规划系统的 API 接口说明，包括各个微服务的接口定义、参数说明和使用示例。

## 服务列表

| 服务 | 端口 | 说明 |
|------|------|------|
| **api-gateway** | 8088 | API 网关，统一入口 |
| **uav-platform-service** | 8080 | 主服务，提供系统的核心功能 |
| **wrf-processor-service** | 8081 | WRF 气象数据处理服务 |
| **meteor-forecast-service** | 8082 | 气象预测服务 |
| **path-planning-service** | 8083 | 路径规划服务 |
| **data-assimilation-service** | 8084 | 贝叶斯同化服务 |
| **uav-weather-collector** | 8086 | 气象信息收集服务 |
| **edge-cloud-coordinator** | 8000 | 边云协同框架（联邦学习/WebSocket） |

## 认证与授权

所有 API 接口都需要使用 JWT 令牌进行认证。在请求头中添加以下信息：

```
Authorization: Bearer <JWT令牌>
```

## 接口文档

### uav-platform-service

- [认证接口](uav-platform-service/auth.md)
- [用户管理接口](uav-platform-service/user.md)
- [任务管理接口](uav-platform-service/task.md)
- [无人机管理接口](uav-platform-service/drone.md)
- [路径规划接口](uav-platform-service/path.md)
- [历史数据接口](uav-platform-service/history.md)
- [数据源管理接口](uav-platform-service/data-sources.md)

### wrf-processor-service

- [WRF 数据处理接口](wrf-processor-service/wrf.md)

### meteor-forecast-service

- [气象预测接口](meteor-forecast-service/forecast.md)

### path-planning-service

- [路径规划算法接口](path-planning-service/path.md)

### uav-weather-collector

- [气象信息收集接口](uav-weather-collector/weather.md)

### edge-cloud-coordinator

- [边云协同接口](edge-cloud-coordinator/coordinator.md)

## 通用错误处理

所有 API 接口返回统一的错误格式：

```json
{
  "code": "错误代码",
  "message": "错误信息",
  "details": "详细错误信息"
}
```

常见错误代码：
- `400`: 请求参数错误
- `401`: 未授权
- `403`: 禁止访问
- `404`: 资源不存在
- `500`: 服务器内部错误

## 版本控制

API 版本通过 URL 路径进行控制，例如：

```
/api/v1/auth/login
```


---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
