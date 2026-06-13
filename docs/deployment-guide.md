# UAV Platform V2 部署运维手册

> 最后更新：2026-06-14

## 1. 环境要求

| 组件 | 最低版本 | 说明 |
|------|----------|------|
| JDK | 21+ | 主项目 Spring Boot 4.0，Gateway 使用 JDK 17 (standalone) |
| Maven | 3.9+ | 项目构建 |
| Python | 3.12+ | algorithm-engine (FastAPI) |
| Node.js | 20+ | 开发者控制台 (Vue 3) |
| Docker | 24+ | 基础设施容器化 |
| Docker Compose | 2.20+ | 编排 13 个容器 |

**硬件最低要求**: 16GB RAM, 8 CPU cores（推荐 32GB RAM）

## 2. Docker Compose 全栈部署（推荐）

### 2.1 启动全部服务

```bash
# 启动基础设施 + 全部业务服务（13 个容器）
docker compose up -d
```

### 2.2 初始化数据库

```bash
# Nacos schema（首次部署必须执行）
docker cp docker/init-db/nacos-schema.sql uav-mysql:/tmp/
docker compose exec mysql mysql -unacos -pnacos nacos -e "source /tmp/nacos-schema.sql"

# 业务数据库（MySQL 容器启动时通过 MYSQL_DATABASE 自动创建）
# 如需手动初始化：
docker exec -i uav-mysql mysql -uroot -prootpass < scripts/init-db.sql
```

### 2.3 构建 api-gateway（standalone 方式）

api-gateway 使用独立的 Spring Boot 3.4.5 构建（与主项目 Spring Boot 4.0 分离）：

```powershell
cd gateway/api-gateway
powershell -ExecutionPolicy Bypass -File build-standalone.ps1 -SkipTests
```

### 2.4 验证部署状态

```powershell
# 检查全部容器状态
docker compose ps

# 预期输出：13 个容器全部 Up (healthy)
```

## 3. 服务端口清单

### Docker 容器端口映射

| 容器名 | 内部端口 | 宿主机端口 | 说明 |
|--------|----------|-----------|------|
| uav-gateway | 8088 | 8258 | API Gateway (Spring Boot 3.4.5 standalone) |
| uav-platform-api | 8081 | 8251 | 平台管理 |
| uav-weather-api | 8082 | 8252 | 气象数据 |
| uav-assimilation-api | 8083 | 8253 | 数据同化 |
| uav-risk-api | 8084 | 8254 | 风险评估 |
| uav-observation-api | 8085 | 8255 | 观测决策 |
| uav-planning-api | 8086 | 8256 | 航迹规划 |
| uav-utm-api | 8087 | 8259 | UTM 管理 |
| uav-algorithm-engine | 9090 | 9095 | Python 算法引擎 |
| uav-mysql | 3306 | 3306 | MySQL 8.0 |
| uav-redis | 6379 | 6379 | Redis 7 |
| uav-nacos | 8848 | 8950 | Nacos 3.2.0 控制台 |
| uav-kafka | 9092 | - | Kafka（仅容器内部可达） |
| uav-zookeeper | 2181 | - | Zookeeper（仅容器内部可达） |

### 本地开发端口（非 Docker）

| Service | Port | Description |
|---------|------|-------------|
| api-gateway | 8088 | API Gateway (standalone) |
| platform-api | 8081 | Platform management |
| weather-api | 8082 | Weather data |
| assimilation-api | 8083 | Data assimilation |
| risk-api | 8084 | Risk assessment |
| observation-api | 8085 | Observation decision |
| planning-api | 8086 | Path planning |
| utm-api | 8087 | UTM management |
| algorithm-engine | 9090 | Python 算法引擎 |

## 4. 配置说明

### 4.1 Mock 模式开关

- `uav.mock.enabled=true` (default, dev/test)
- `uav.mock.enabled=false` (production, **MUST set**)
- Mock 响应包含 `X-Mock: true` Header

### 4.2 数据库配置

**Docker 环境**（通过环境变量自动注入）：
- URL: `jdbc:mysql://mysql:3306/{database}`
- Root 密码: `rootpass`

**本地开发**：
- URL: `jdbc:mysql://localhost:3306/{database}`
- Root 密码: `rootpass`
- Parameters: `allowPublicKeyRetrieval=true&useSSL=false`

### 4.3 Redis 配置

- Docker: `redis:6379`
- 本地: `localhost:6379`

### 4.4 Kafka 配置

- Docker: `kafka:9092`
- 本地: `localhost:9092`
- Topics: `uav.algorithm.tasks` (Java->Python), `uav.algorithm.results` (Python->Java)

### 4.5 Nacos 配置

- 控制台: `http://localhost:8950/nacos/`
- 默认账号: `nacos / nacos`
- JWT Token: Base64 编码，长度 >= 32 字节（256 bits）

### 4.6 API Gateway 路由

Gateway 使用 `docker` profile，通过 Docker 服务名直接路由（无需 Nacos 服务发现）：

| 路径前缀 | 目标服务 |
|----------|---------|
| `/api/v1/tenants/**`, `/api/v2/tenants/**` | platform-api:8081 |
| `/api/v1/weather/**` | weather-api:8082 |
| `/api/v1/assimilation/**` | assimilation-api:8083 |
| `/api/v1/risk/**` | risk-api:8084 |
| `/api/v1/observation/**` | observation-api:8085 |
| `/api/v1/planning/**` | planning-api:8086 |
| `/api/v1/utm/**`, `/api/v1/flight/**` | utm-api:8087 |
| `/api/v1/algorithms/**`, `/api/v1/tasks/**` | algorithm-engine:9090 |

## 5. Kafka 全链路消息格式

### Java -> Python（任务下发）

Topic: `uav.algorithm.tasks`

```json
{
  "task_id": "uuid",
  "algorithm_id": "a_star",
  "params": {"start": [0,0], "goal": [10,10]},
  "timestamp": "2026-06-14T00:00:00Z",
  "priority": 1
}
```

### Python -> Java（结果回调）

Topic: `uav.algorithm.results`

```json
{
  "task_id": "uuid",
  "algorithm_id": "a_star",
  "status": "success",
  "result": {"path": [...], "cost": 14.2},
  "error": null,
  "completed_at": "2026-06-14T00:00:05Z",
  "progress": 100
}
```

> 注意：消息格式统一使用 snake_case，Java 端通过 `@JsonNaming(SnakeCaseStrategy.class)` 自动转换。

## 6. 常见故障排查

### 6.1 端口被占用

```powershell
netstat -ano | findstr :XXXX
Stop-Process -Id {PID}
```

### 6.2 MySQL 连接失败

```bash
docker exec uav-mysql mysql -uroot -prootpass -e "ALTER USER 'root'@'%' IDENTIFIED BY 'rootpass'; FLUSH PRIVILEGES;"
```

### 6.3 Nacos 启动失败

- **JWT token 太短**: `NACOS_AUTH_TOKEN` 必须 >= 32 字节 Base64 编码（>= 256 bits）
- **数据库表缺失**: 执行 `docker/init-db/nacos-schema.sql` 初始化 13 张表
- **config_gray 迁移失败**: 确认 `config_info_gray` 表已创建

### 6.4 api-gateway 启动失败

Spring Cloud Gateway 与 Spring Boot 4.0 不兼容，必须使用 standalone 构建：

```powershell
cd gateway/api-gateway
powershell -ExecutionPolicy Bypass -File build-standalone.ps1 -SkipTests
```

### 6.5 Kafka 消息反序列化失败

- 确认 Python 端使用 `_sanitize_value()` 清理 Infinity/NaN 值
- 确认 Java 端 `AlgorithmResultMessage` 有 `@JsonNaming(SnakeCaseStrategy.class)` 注解

### 6.6 Zookeeper 端口未映射

Zookeeper 仅容器内部可达（Kafka 依赖），无需映射到宿主机。如需本地调试，修改 `docker-compose.yml` 添加 `ports: "2181:2181"`。

## 7. 健康检查

```powershell
# Docker 容器状态
docker compose ps

# 通过 Gateway 访问算法引擎
Invoke-RestMethod http://localhost:8258/api/v1/algorithms

# Nacos 控制台
Invoke-WebRequest http://localhost:8950/nacos/

# Kafka 消费验证
docker compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic uav.algorithm.results --from-beginning --timeout-ms 5000
```

## 8. 优雅停机

```bash
# 停止全部容器
docker compose down

# 停止并清除数据卷（慎用）
docker compose down -v
```
