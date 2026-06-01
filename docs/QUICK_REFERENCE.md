# UAV Path Planning System - Quick Reference Card

## 🚀 快速开始

### 启动所有服务
```bash
docker-compose up -d
```

### 查看服务状态
```bash
docker-compose ps
```

### 访问地址
| 服务 | URL |
|------|-----|
| 前端 | http://localhost:3000 |
| API Gateway | http://localhost:8088 |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |
| Kibana | http://localhost:5601 |

---

## 🔧 常用命令

### Java服务
```bash
# 构建
mvn clean package -DskipTests

# 运行
mvn spring-boot:run

# 仅构建单个服务
mvn package -pl api-gateway -am
```

### Python服务
```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/ -v

# 类型检查
mypy src/
```

### Docker
```bash
# 构建镜像
docker build -t uav/service:latest .

# 查看日志
docker-compose logs -f service-name

# 重启服务
docker-compose restart service-name
```

---

## 📡 API端点

### 认证
```bash
# 登录
POST /api/v1/auth/login
{
  "username": "admin",
  "password": "password"
}

# 响应
{
  "token": "eyJhbGciOiJIUzI1NiJ9...",
  "user": {...}
}
```

### 气象数据
```bash
# 获取当前天气
GET /api/forecast/drone/{droneId}

# 获取天气预报
GET /api/forecast/area/{areaId}?hours=24

# 批量获取
POST /api/forecast/batch
{
  "droneIds": ["UAV001", "UAV002", "UAV003"]
}
```

### 路径规划
```bash
# 创建任务
POST /api/planning/mission
{
  "waypoints": [[39.9, 116.4], [40.0, 116.5]],
  "constraints": {
    "maxAltitude": 100,
    "maxSpeed": 20
  }
}

# 查询状态
GET /api/planning/mission/{missionId}
```

### 数据同化
```bash
# 执行同化
POST /api/assimilation/execute
{
  "background": {...},
  "observations": [...],
  "algorithm": "3D-VAR"
}
```

---

## 🛡️ 安全配置

### JWT密钥配置
```bash
# 必须设置环境变量
export JWT_SECRET=your_32_character_minimum_secret_key

# 验证配置
curl http://localhost:8080/api/admin/circuit-breaker/health
```

### 数据库密码
```bash
# 必须设置环境变量
export DB_PASSWORD=your_secure_password
```

---

## 📊 熔断器管理

### 查看熔断器状态
```bash
curl http://localhost:8080/api/admin/circuit-breaker/status
```

### 查看详情
```bash
curl http://localhost:8080/api/admin/circuit-breaker/details/meteor-forecast-service
```

### 手动触发熔断
```bash
curl -X POST http://localhost:8080/api/admin/circuit-breaker/trip/meteor-forecast-service
```

### 重置熔断器
```bash
curl -X POST http://localhost:8080/api/admin/circuit-breaker/reset/meteor-forecast-service
```

---

## 🔍 故障排查

### 服务无法启动
```bash
# 检查端口占用
netstat -ano | findstr 8080

# 检查依赖服务
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 数据库连接失败
```bash
# 检查MySQL
docker-compose exec mysql mysql -u root -p

# 检查连接配置
cat src/main/resources/application.yml | grep -A 10 datasource
```

### 熔断器打开
```bash
# 查看状态
curl http://localhost:8080/api/admin/circuit-breaker/details/service-name

# 检查日志
docker-compose logs | grep "CircuitBreaker"

# 手动重置
curl -X POST http://localhost:8080/api/admin/circuit-breaker/reset/service-name
```

---

## 📈 监控查询

### Prometheus查询
```promql
# CPU使用率
cpu_usage_percent

# 请求率
rate(http_requests_total[5m])

# 错误率
rate(http_requests_total{status=~"5.."}[5m])

# P95延迟
http_request_duration_seconds{quantile="0.95"}

# 熔断器状态
resilience4j_circuitbreaker_state
```

### Grafana仪表板
- System Overview - 系统整体状态
- Application Performance - 应用性能
- Circuit Breaker Status - 熔断器状态
- Business Metrics - 业务指标

---

## 🔄 部署

### 开发环境
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 生产环境
```bash
# Kubernetes
kubectl apply -f deployments/kubernetes/

# 检查部署状态
kubectl get pods -n uav-platform
```

---

## 📝 日志查看

### 应用日志
```bash
# 查看所有日志
docker-compose logs -f

# 查看特定服务
docker-compose logs -f api-gateway

# 查看最近日志
docker-compose logs --tail=100 service-name
```

### Elasticsearch日志查询
```
# Kibana Dev Tools
GET uav-logs-*/_search
{
  "query": {
    "range": {
      "@timestamp": {
        "gte": "now-1h"
      }
    }
  }
}
```

---

## 🧪 测试

### 运行所有测试
```bash
# Java测试
mvn test

# Python测试
pytest tests/ -v

# 集成测试
pytest tests/integration/ -v
```

### 性能测试
```bash
pytest test_performance.py -v -s
```

---

## 📚 文档索引

| 需要什么 | 查看这个 |
|---------|---------|
| 项目概览 | [README.md](README.md) |
| 部署指南 | [DEPLOYMENT.md](DEPLOYMENT.md) |
| 架构设计 | [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) |
| 熔断器使用 | [docs/CIRCUIT_BREAKER_GUIDE.md](docs/CIRCUIT_BREAKER_GUIDE.md) |
| 监控配置 | [docs/deployments/monitoring/README.md](docs/deployments/monitoring/README.md) |
| 更新日志 | [CHANGELOG.md](CHANGELOG.md) |

---

## 🔗 关键链接

- Grafana: http://localhost:3000 (admin/changeme123)
- Prometheus: http://localhost:9090
- Kibana: http://localhost:5601 (elastic/changeme123)
- Alertmanager: http://localhost:9093
- Jaeger: http://localhost:16686

---

**最后更新**: 2026-05-08  
**版本**: 2.0.0
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
