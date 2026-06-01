# 🚀 UAV Path Planning System - 端口配置总表

## 📋 概述

本文档汇总 UAV Path Planning System 所有服务的端口配置，包括开发环境、生产环境和前端应用。

---

## 🖥️ 后端服务端口

### 微服务列表

| 服务 | 端口 | 协议 | 说明 | 熔断器 | 状态 |
|------|:----:|:----:|------|:------:|:----:|
| **API Gateway** | 8088 | HTTP | 统一入口（限流/熔断/路由） | ✅ | ✅ |
| **Platform Service** | 8080 | HTTP | 主平台服务（认证/任务/无人机） | ✅ | ✅ |
| **WRF Processor** | 8081 | HTTP | WRF 气象数据处理 | ✅ | ✅ |
| **Bayes Assimilator** | 8084 | HTTP | 贝叶斯同化计算 | ✅ | ✅ |
| **Meteor Forecaster** | 8082 | HTTP | 气象预测与订正（LSTM+XGBoost） | ✅ | ✅ |
| **Path Planner** | 8083 | HTTP | VRPTW+DE-RRT*+DWA 路径规划 | ✅ | ✅ |
| **Weather Collector** | 8086 | HTTP | 多源气象数据采集与融合 | - | ✅ |
| **Edge-Cloud Coordinator** | 8000 | HTTP | 边云协同 | - | ✅ |
| **Edge-Cloud Coordinator** | 8765 | WebSocket | WebSocket 通信 | - | ✅ |

### 端口分配原则

```
端口范围      | 用途
-------------|------------------
8080-8089    | 主要微服务
8090-8099    | 次要服务/管理接口
8000-8099    | 特殊服务（Edge-Cloud）
9000-9099    | 监控服务
```

---

## 🌐 前端应用端口

### 开发环境

| 应用 | 端口 | 技术栈 | API代理 | 说明 |
|------|:----:|--------|---------|------|
| **Frontend (Vue3)** | **3000** | Vue3 + Vite | http://localhost:8080 | Web 应用入口 |

### 前端配置

**配置文件**: `uav-path-planning-system/frontend-vue/vite.config.js`

```javascript
export default defineConfig({
  server: {
    port: 3000,  // 开发服务器端口
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
```

### 生产环境

| 应用 | 端口 | 说明 |
|------|:----:|------|
| **Frontend (Nginx)** | 80 | 静态资源托管 |
| **Frontend (HTTPS)** | 443 | HTTPS 端口 |

---

## 🔗 API 路由映射

### API Gateway 路由 (端口 8088)

| 外部路由 | 内部服务 | 目标端口 | 说明 |
|---------|---------|:--------:|------|
| `/api/v1/**` | uav-platform-service | 8080 | 主平台 API |
| `/api/wrf/**` | wrf-processor-service | 8081 | WRF 数据 API |
| `/api/forecast/**` | meteor-forecast-service | 8082 | 气象预报 API |
| `/api/planning/**` | path-planning-service | 8083 | 路径规划 API |
| `/api/assimilation/**` | data-assimilation-service | 8084 | 数据同化 API |

### 前端 API 调用

前端通过 Vite 代理访问后端：

```
用户浏览器 (localhost:3000)
    ↓ /api/xxx
Vite 开发服务器代理
    ↓
API Gateway (localhost:8088)
    ↓ /api/v1/xxx
Platform Service (localhost:8080)
```

---

## 📊 监控和管理端口

### 监控系统

| 服务 | 端口 | 说明 | 访问地址 |
|------|:----:|------|---------|
| **Prometheus** | 9090 | 指标收集 | http://localhost:9090 |
| **Grafana** | 3000* | 可视化仪表板 | http://localhost:3000 |
| **Alertmanager** | 9093 | 告警管理 | http://localhost:9093 |
| **Jaeger** | 16686 | 链路追踪 | http://localhost:16686 |
| **Kibana** | 5601 | 日志分析 | http://localhost:5601 |
| **Elasticsearch** | 9200 | 日志存储 | http://localhost:9200 |

> ⚠️ 注意: Grafana 默认端口 3000 与前端开发服务器冲突，请修改为 3030 或其他端口。

### 健康检查端点

| 服务 | 端口 | 健康检查端点 |
|------|:----:|-------------|
| API Gateway | 8088 | `/actuator/health` |
| Platform Service | 8080 | `/actuator/health` |
| WRF Processor | 8081 | `/actuator/health` |
| Meteor Forecaster | 8082 | `/actuator/health` |
| Path Planner | 8083 | `/actuator/health` |
| Data Assimilator | 8084 | `/actuator/health` |
| Weather Collector | 8086 | `/actuator/health` |
| Frontend | 3000 | `/` |

---

## 🗄️ 数据存储端口

### 数据库服务

| 服务 | 端口 | 默认数据库 | 说明 |
|------|:----:|-----------|------|
| **MySQL** | 3306 | `uav_platform` | 主数据库 |
| **MySQL** | 3307 | `meteor_data` | 气象数据 |
| **Redis** | 6379 | - | 缓存/会话 |
| **MongoDB** | 27017 | `uav_logs` | 日志存储 |

### 消息队列

| 服务 | 端口 | 说明 |
|------|:----:|------|
| **Kafka** | 9092 | 消息队列 |
| **Kafka** | 9093 | 内部通信 |

---

## 🐳 Docker 端口映射

### 开发环境

```yaml
services:
  # 后端服务
  api-gateway:
    ports:
      - "8088:8088"
  
  platform-service:
    ports:
      - "8080:8080"
  
  wrf-processor:
    ports:
      - "8081:8081"
  
  meteor-forecast:
    ports:
      - "8082:8082"
  
  path-planning:
    ports:
      - "8083:8083"
  
  data-assimilation:
    ports:
      - "8084:8084"
  
  weather-collector:
    ports:
      - "8086:8086"
  
  # 前端
  frontend:
    ports:
      - "3000:80"  # 开发映射到 3000，生产 80
  
  # 数据库
  mysql:
    ports:
      - "3306:3306"
  
  redis:
    ports:
      - "6379:6379"
  
  # 监控
  prometheus:
    ports:
      - "9090:9090"
  
  grafana:
    ports:
      - "3030:3000"  # 避免与前端冲突
  
  jaeger:
    ports:
      - "16686:16686"
```

---

## 🔧 端口配置最佳实践

### 1. 开发环境

**建议配置**:
- 使用标准端口（8080-8089）
- 前端开发服务器：3000
- Grafana 改为：3030（避免冲突）

**优点**:
- 易于记忆
- 避免常见端口冲突
- 便于团队协作

### 2. 生产环境

**建议配置**:
- API Gateway：443（HTTPS）
- 数据库：内网访问，不暴露
- 监控：VPN 或专用网络访问

**安全建议**:
- 使用环境变量管理端口
- 不暴露非必要端口
- 配置防火墙规则

---

## 🚨 常见端口冲突

### 冲突检测

```bash
# Linux/Mac
netstat -an | grep :3000
lsof -i :3000

# Windows
netstat -ano | findstr :3000
```

### 解决方案

1. **前端端口冲突**
   - 方案1: 修改 Vite 配置端口
   - 方案2: 修改 Grafana 端口

2. **后端端口冲突**
   - 方案1: 检查是否有其他服务占用
   - 方案2: 修改 application.yml 中的端口

### 端口修改示例

**修改前端端口** (vite.config.js):
```javascript
server: {
  port: 3001,  // 改为 3001
}
```

**修改 Grafana 端口** (docker-compose.yml):
```yaml
grafana:
  ports:
    - "3030:3000"  # 外部 3030，内部仍是 3000
```

---

## 📋 快速参考表

### 服务启动顺序

```
1. MySQL (3306)          - 数据库
2. Redis (6379)          - 缓存
3. Nacos (8848)          - 配置中心
4. Platform Service (8080) - 主平台
5. WRF Processor (8081)    - WRF服务
6. Meteor Forecaster (8082) - 气象服务
7. Path Planner (8083)     - 路径规划
8. Data Assimilation (8084) - 数据同化
9. Weather Collector (8086) - 气象采集
10. API Gateway (8088)      - API网关
11. Frontend (3000)         - 前端
```

### 端口总览

```
环境    | 服务                 | 端口
--------|---------------------|------
前端    | Vue3 Dev Server     | 3000
前端    | Vue3 Prod (Nginx)   | 80
后端    | Platform Service    | 8080
后端    | WRF Processor       | 8081
后端    | Meteor Forecaster   | 8082
后端    | Path Planner        | 8083
后端    | Data Assimilation   | 8084
后端    | Weather Collector   | 8086
后端    | Edge Coordinator    | 8000/8765
后端    | API Gateway         | 8088
数据库  | MySQL               | 3306
数据库  | Redis               | 6379
监控    | Prometheus          | 9090
监控    | Grafana             | 3030
监控    | Jaeger              | 16686
监控    | Kibana              | 5601
监控    | Elasticsearch       | 9200
```

---

## 📞 技术支持

如有问题，请参考：
1. [前端 README](../uav-path-planning-system/frontend-vue/README.md)
2. [部署指南](DEPLOYMENT.md)
3. [快速参考](QUICK_REFERENCE.md)


---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
