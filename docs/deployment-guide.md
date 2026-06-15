# UAV Platform V2 部署手册

> 最后更新：2026-06-15

## 1. 环境要求

| 组件 | 最低版本 | 推荐版本 | 说明 |
|------|---------|---------|------|
| JDK | 21+ | Eclipse Temurin 21 | 主项目 Spring Boot 4.0 |
| Maven | 3.9+ | 3.9.6 | Java 项目构建 |
| Python | 3.12+ | 3.12.x | algorithm-engine (FastAPI) |
| Node.js | 20+ | 20 LTS | 开发者控制台 (Vue 3 + Vite 7) |
| Docker | 24+ | 25.0+ | 基础设施容器化 |
| Docker Compose | 2.20+ | 2.30+ | 编排 16 个容器 |
| kubectl | 1.28+ | 1.30+ | K8s 部署（可选） |
| Helm | 3.14+ | 3.15+ | K8s 包管理（可选） |

**硬件最低要求**: 16GB RAM, 8 CPU cores（推荐 32GB RAM）

## 2. 本地开发环境搭建

### 2.1 前置条件

```bash
# 检查各组件版本
java -version      # JDK 21+
mvn -version        # Maven 3.9+
python --version    # Python 3.12+
node -v             # Node.js 20+
docker --version    # Docker 24+
docker compose version  # Docker Compose 2.20+
```

### 2.2 克隆项目并构建

```bash
git clone https://github.com/your-org/uav-platform-v2.git
cd uav-platform-v2

# 构建 Java 微服务（跳过测试加速）
mvn clean package -DskipTests

# 构建 API Gateway（standalone 方式）
cd gateway/api-gateway
powershell -ExecutionPolicy Bypass -File build-standalone.ps1 -SkipTests
cd ../..

# 安装前端依赖
cd console
npm ci
cd ..
```

### 2.3 启动基础设施

```bash
# 仅启动 MySQL、Redis、Kafka、Zookeeper、Nacos
docker compose up -d mysql redis kafka zookeeper nacos

# 等待健康检查通过
docker compose ps
```

### 2.4 初始化数据库

```bash
# Nacos schema（首次部署必须执行）
docker cp docker/init-db/nacos-schema.sql uav-mysql:/tmp/
docker compose exec mysql mysql -unacos -pnacos nacos -e "source /tmp/nacos-schema.sql"

# 业务数据库（MySQL 容器启动时通过 init-db.sql 自动创建）
```

### 2.5 启动业务服务

```bash
# 终端 1: API Gateway
cd gateway/api-gateway
java -jar target/api-gateway-2.0.0.jar --spring.profiles.active=dev

# 终端 2: 启动需要的 Java 微服务（IDE 或命令行）
java -jar services/weather-api/target/weather-api-2.0.0.jar --spring.profiles.active=dev
java -jar services/planning-api/target/planning-api-2.0.0.jar --spring.profiles.active=dev

# 终端 3: Python 算法引擎
cd python/algorithm-engine
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 9090 --reload

# 终端 4: 前端控制台
cd console
npm run dev  # http://localhost:3000
```

## 3. Docker Compose 全栈部署（推荐）

### 2.1 启动全部服务

```bash
# 启动基础设施 + 全部业务服务（16 个容器）
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
# 检查全部容器状态（预期 16 个容器全部 Up）
docker compose ps

# 预期容器列表：
# uav-nacos, uav-mysql, uav-redis, uav-kafka, uav-zookeeper
# uav-gateway, uav-platform-api, uav-weather-api, uav-assimilation-api
# uav-risk-api, uav-observation-api, uav-planning-api, uav-utm-api
# uav-algorithm-engine, uav-console
# uav-prometheus, uav-grafana, uav-alertmanager
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
| uav-console | 80 | 3000 | 前端控制台 (Vue 3) |
| uav-mysql | 3306 | 3306 | MySQL 8.0 |
| uav-redis | 6379 | 6379 | Redis 7 |
| uav-nacos | 8848 | 8950 | Nacos 3.2.0 控制台 |
| uav-kafka | 9092 | 19092 | Kafka |
| uav-prometheus | 9090 | 19091 | Prometheus 监控 |
| uav-grafana | 3000 | 3001 | Grafana 可视化 |
| uav-alertmanager | 9093 | 19093 | AlertManager 告警 |
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
| console (dev) | 3000 | Vite dev server |

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

### 4.7 前端开发代理

Vite 开发服务器将 `/api` 代理到 API Gateway (`http://localhost:8258`)：

```typescript
// vite.config.ts
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8258',
      changeOrigin: true,
    },
  },
}
```

## 5. RBAC 配置

### 5.1 数据库初始化

首次部署需执行 RBAC 相关表初始化（包含在 `scripts/init-db.sql` 中）：

```sql
-- 角色表
CREATE TABLE IF NOT EXISTS sys_role (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  role_code VARCHAR(64) NOT NULL UNIQUE,
  role_name VARCHAR(128) NOT NULL,
  description VARCHAR(256),
  status TINYINT DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 用户角色关联表
CREATE TABLE IF NOT EXISTS sys_user_role (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  role_id BIGINT NOT NULL,
  tenant_id BIGINT,
  UNIQUE KEY uk_user_role (user_id, role_id)
);

-- 权限表
CREATE TABLE IF NOT EXISTS sys_permission (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  permission_code VARCHAR(128) NOT NULL UNIQUE,
  permission_name VARCHAR(128) NOT NULL,
  resource_type VARCHAR(32),
  parent_id BIGINT DEFAULT 0
);

-- 角色权限关联表
CREATE TABLE IF NOT EXISTS sys_role_permission (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  role_id BIGINT NOT NULL,
  permission_id BIGINT NOT NULL,
  UNIQUE KEY uk_role_permission (role_id, permission_id)
);
```

### 5.2 预置角色

| 角色编码 | 角色名称 | 说明 |
|----------|---------|------|
| `SUPER_ADMIN` | 超级管理员 | 全部权限，可管理租户、用户、系统配置 |
| `TENANT_ADMIN` | 租户管理员 | 租户内全部权限，可管理租户内用户和资源 |
| `OPERATOR` | 操作员 | 可执行飞行计划、查看气象数据、提交规划任务 |
| `OBSERVER` | 观察员 | 只读权限，可查看仪表盘、气象数据、任务状态 |
| `ALGORITHM_ADMIN` | 算法管理员 | 管理算法注册、执行、监控算法引擎指标 |

### 5.3 角色分配

```sql
-- 创建超级管理员
INSERT INTO sys_role (role_code, role_name, description) VALUES
('SUPER_ADMIN', '超级管理员', '系统最高权限'),
('TENANT_ADMIN', '租户管理员', '租户内全部权限'),
('OPERATOR', '操作员', '可执行飞行计划和查看数据'),
('OBSERVER', '观察员', '只读权限'),
('ALGORITHM_ADMIN', '算法管理员', '管理算法引擎');

-- 为用户分配角色（示例）
INSERT INTO sys_user_role (user_id, role_id) VALUES (1, 1);  -- user_id=1 -> SUPER_ADMIN
```

### 5.4 API Key HMAC 签名

前端请求通过 HMAC-SHA256 签名认证，签名流程：

1. 请求拦截器获取用户 `apiKeySecret`
2. 计算请求体 SHA-256 哈希（GET 请求跳过）
3. 签名原文：`timestamp + METHOD + path + bodyHash`
4. 使用 `apiKeySecret` 对签名原文进行 HMAC-SHA256
5. 附加 Header：`X-Timestamp`, `X-Signature`, `X-Signature-Method`, `X-Body-Hash`

## 6. 监控操作手册

### 6.1 Prometheus 配置

配置文件位于 `monitoring/prometheus.yml`，已配置以下抓取目标：

| Job | 目标 | 端口 | 说明 |
|-----|------|------|------|
| `gateway` | `api-gateway:8088` | 8088 | API Gateway 指标 |
| `platform-api` | `platform-api:8081` | 8081 | 平台管理指标 |
| `weather-api` | `weather-api:8082` | 8082 | 气象服务指标 |
| `planning-api` | `planning-api:8086` | 8086 | 规划服务指标 |
| `algorithm-engine` | `algorithm-engine:9090` | 9090 | Python 算法引擎指标 |

访问 Prometheus：`http://localhost:19091`

### 6.2 Grafana 访问

- 地址：`http://localhost:3001`
- 默认账号：`admin / admin123`
- 数据源：已自动配置 Prometheus 数据源（通过 provisioning）

### 6.3 Dashboard 导入

Grafana Dashboard 通过 provisioning 自动加载（`monitoring/grafana/provisioning/dashboards/`）。

手动导入步骤：
1. 打开 Grafana -> Dashboards -> Import
2. 输入 Dashboard JSON 或上传文件
3. 选择 Prometheus 数据源
4. 点击 Import

推荐 Dashboard：

| Dashboard | 说明 |
|-----------|------|
| JVM Micrometer | Java 服务 JVM 指标（内存、GC、线程） |
| Spring Boot | Spring Boot 应用指标（HTTP 请求、健康检查） |
| Algorithm Engine | Python 算法引擎专属指标 |
| Kafka Exporter | Kafka 消息队列指标 |
| Node Exporter | 主机资源使用（CPU、内存、磁盘、网络） |

### 6.4 告警配置

AlertManager 配置位于 `monitoring/alertmanager.yml`。

默认告警规则（Prometheus rules）：

| 告警名称 | 级别 | 条件 | 说明 |
|----------|------|------|------|
| ServiceDown | critical | 服务健康检查失败超过 2 分钟 | 服务不可用 |
| HighErrorRate | warning | HTTP 5xx 错误率 > 5% | 服务异常 |
| HighLatency | warning | P99 延迟 > 2s | 性能劣化 |
| KafkaLag | warning | 消费者 lag > 1000 | 消息积压 |
| AlgorithmEngineDown | critical | 算法引擎健康检查失败 | 算法服务不可用 |
| AlgorithmExecutionFail | warning | 算法执行失败率 > 10% | 算法异常 |

### 6.5 算法引擎指标说明

Python 算法引擎暴露以下 Prometheus 指标：

| 指标名 | 类型 | 说明 |
|--------|------|------|
| `algorithm_engine_tasks_total` | Counter | 算法任务总数（按 status 标签分类） |
| `algorithm_engine_execution_duration_seconds` | Histogram | 算法执行耗时分布 |
| `algorithm_engine_active_tasks` | Gauge | 当前正在执行的任务数 |
| `algorithm_engine_registered_algorithms` | Gauge | 已注册算法数量 |
| `algorithm_engine_kafka_consumer_lag` | Gauge | Kafka 消费者 lag |
| `algorithm_engine_errors_total` | Counter | 错误总数（按 error_type 标签分类） |

PromQL 查询示例：

```promql
# 算法执行成功率
sum(rate(algorithm_engine_tasks_total{status="success"}[5m])) /
sum(rate(algorithm_engine_tasks_total[5m]))

# P95 执行耗时
histogram_quantile(0.95, sum(rate(algorithm_engine_execution_duration_seconds_bucket[5m])) by (le))

# 当前活跃任务数
algorithm_engine_active_tasks

# 已注册算法数
algorithm_engine_registered_algorithms
```

## 7. Kafka 全链路消息格式

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

## 8. 多环境部署

### 8.1 环境区分

| 环境 | 配置文件 | Profile | Mock | 监控 | Debug | 说明 |
|------|---------|---------|------|------|-------|------|
| dev | `docker-compose.override.yml`（自动加载） | `dev,docker` | true | 可选（`--profile monitoring`） | 开启（JDWP :5005） | 本地开发，挂载源码卷热重载 |
| staging | `docker-compose.staging.yml` | `staging,docker` | false | 启用 | 关闭 | 灰度环境，release 镜像标签 |
| prod | `docker-compose.prod.yml` | `prod,docker` | false | 启用 | 关闭 | 生产环境，资源限制 + 副本数 |

### 8.2 Dev 环境（本地开发）

```bash
# 方式一：直接启动（docker-compose.override.yml 自动合并）
docker compose up -d

# 方式二：显式排除 override（使用原始 docker-compose.yml）
docker compose -f docker-compose.yml up -d

# 启动时同时开启监控
docker compose --profile monitoring up -d

# 仅启动基础设施（不启动业务服务）
docker compose up -d mysql redis kafka zookeeper nacos

# 启动 API Gateway（standalone）
cd gateway/api-gateway
java -jar target/api-gateway-2.0.0.jar --spring.profiles.active=dev

# 启动需要的业务服务（IDE 或命令行）
java -jar services/weather-api/target/weather-api-2.0.0.jar --spring.profiles.active=dev

# 启动 Python 算法引擎
cd python/algorithm-engine
uvicorn app.main:app --host 0.0.0.0 --port 9090

# 启动前端
cd console
npm run dev  # http://localhost:3000
```

Dev 环境特性：
- 本地源码卷挂载（热重载）
- Java Debug 端口（JDWP :5005）
- Python Debug 端口（debugpy :5678）
- 降低 JVM 内存（-Xmx256m）
- Mock 模式开启

### 8.3 Staging 环境（灰度/预发布）

```bash
# 使用 staging 配置文件启动
docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d

# 重新构建并启动
docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d --build

# 仅重启业务服务（保留基础设施）
docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d api-gateway platform-api weather-api assimilation-api risk-api observation-api planning-api utm-api algorithm-engine

# 查看服务状态
docker compose -f docker-compose.yml -f docker-compose.staging.yml ps

# 停止
docker compose -f docker-compose.yml -f docker-compose.staging.yml down
```

Staging 环境特性：
- 使用 `release` 镜像标签
- 内存限制（Java: 768M, Algorithm Engine: 1024M）
- Mock 模式关闭
- RBAC 启用
- Prometheus / Grafana 全部启用
- `restart: on-failure`

### 8.4 Prod 环境（生产）

```bash
# 生产环境部署（必须关闭 Mock）
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 滚动更新（零停机）
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps --build api-gateway

# 扩缩容（示例：将 platform-api 扩展到 3 副本）
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale platform-api=3

# 验证 Mock 已关闭
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec platform-api env | grep MOCK
# 预期: KAFKA_MOCK=false

# 查看服务状态
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# 停止全部服务
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# 停止并清除数据卷（慎用）
docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v
```

Prod 环境特性：
- 使用 `latest` 镜像标签
- 资源限制（CPU + 内存）
- 副本数配置（api-gateway: 2, algorithm-engine: 2）
- 日志驱动 `json-file` + 大小限制（100m / 5 files）
- `restart: always`
- JVM OOM 自动 HeapDump
- Mock 模式关闭
- RBAC 启用

### 8.5 环境变量覆盖

通过 `.env` 文件或环境变量覆盖默认配置：

```bash
# .env.prod
MYSQL_ROOT_PASSWORD=<strong_password>
NACOS_AUTH_TOKEN=<base64_encoded_token_min_32_bytes>
GF_SECURITY_ADMIN_PASSWORD=<grafana_password>
SPRING_PROFILES_ACTIVE=prod
KAFKA_MOCK=false
SECURITY_RBAC_ENABLED=true
```

### 8.6 多环境配置文件对照表

| 配置文件 | 触发方式 | 镜像标签 | JVM 内存 | Debug | Mock | 监控 | restart |
|----------|---------|---------|---------|-------|------|------|---------|
| `docker-compose.override.yml` | 自动合并 | (build) | 256m | 开启 | true | 可选 | 默认 |
| `docker-compose.staging.yml` | `-f` 指定 | release | 512m | 关闭 | false | 启用 | on-failure |
| `docker-compose.prod.yml` | `-f` 指定 | latest | 1024m | 关闭 | false | 启用 | always |

## 9. 常见故障排查

### 9.1 端口被占用

```powershell
netstat -ano | findstr :XXXX
Stop-Process -Id {PID}
```

### 9.2 MySQL 连接失败

```bash
docker exec uav-mysql mysql -uroot -prootpass -e "ALTER USER 'root'@'%' IDENTIFIED BY 'rootpass'; FLUSH PRIVILEGES;"
```

### 9.3 Nacos 启动失败

- **JWT token 太短**: `NACOS_AUTH_TOKEN` 必须 >= 32 字节 Base64 编码（>= 256 bits）
- **数据库表缺失**: 执行 `docker/init-db/nacos-schema.sql` 初始化 13 张表
- **config_gray 迁移失败**: 确认 `config_info_gray` 表已创建

### 9.4 api-gateway 启动失败

Spring Cloud Gateway 与 Spring Boot 4.0 不兼容，必须使用 standalone 构建：

```powershell
cd gateway/api-gateway
powershell -ExecutionPolicy Bypass -File build-standalone.ps1 -SkipTests
```

### 9.5 Kafka 消息反序列化失败

- 确认 Python 端使用 `_sanitize_value()` 清理 Infinity/NaN 值
- 确认 Java 端 `AlgorithmResultMessage` 有 `@JsonNaming(SnakeCaseStrategy.class)` 注解

### 9.6 Zookeeper 端口未映射

Zookeeper 仅容器内部可达（Kafka 依赖），无需映射到宿主机。如需本地调试，修改 `docker-compose.yml` 添加 `ports: "2181:2181"`。

### 9.7 Prometheus 抓取失败

- 确认目标服务已暴露 `/actuator/prometheus` 端点
- 确认 `management.endpoints.web.exposure.include=prometheus,health` 已配置
- 检查 Prometheus targets 页面：`http://localhost:19091/targets`

### 9.8 Grafana 数据源连接失败

- 确认 Prometheus 容器健康：`docker compose ps prometheus`
- 检查 provisioning 文件路径是否正确
- 手动测试数据源：Grafana -> Configuration -> Data Sources -> Test

### 9.9 前端请求 404

- 确认 API Gateway 正在运行：`curl http://localhost:8258/actuator/health`
- 确认 Vite 代理配置指向 `http://localhost:8258`
- 检查请求路径是否匹配 Gateway 路由规则（见 4.6 节）

### 9.10 算法引擎无响应

```bash
# 检查算法引擎健康状态
curl http://localhost:9095/health

# 检查 Kafka 连接
docker compose exec algorithm-engine python -c "
from app.core.kafka_client import get_kafka_producer
print('Kafka connection OK')
"

# 检查 Redis 连接
docker compose exec algorithm-engine python -c "
import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())
"
```

## 10. 健康检查

```powershell
# Docker 容器状态（16 个容器）
docker compose ps

# API Gateway
Invoke-RestMethod http://localhost:8258/actuator/health

# 通过 Gateway 访问算法引擎
Invoke-RestMethod http://localhost:8258/api/v1/algorithms/list

# Nacos 控制台
Invoke-WebRequest http://localhost:8950/nacos/

# Prometheus
Invoke-RestMethod http://localhost:19091/api/v1/targets

# Grafana
Invoke-WebRequest http://localhost:3001/api/health

# Kafka 消费验证
docker compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic uav.algorithm.results --from-beginning --timeout-ms 5000
```

## 11. 优雅停机

```bash
# 停止全部容器
docker compose down

# 停止并清除数据卷（慎用）
docker compose down -v

# 仅停止业务服务（保留基础设施）
docker compose stop api-gateway platform-api weather-api assimilation-api risk-api observation-api planning-api utm-api algorithm-engine console
```

## 12. Kubernetes 部署（Helm）

### 12.1 前置条件

- Kubernetes 集群 1.28+
- kubectl 已配置并连接到目标集群
- Helm 3.14+
- 容器镜像已推送到镜像仓库

### 12.2 镜像构建与推送

```bash
# 设置镜像仓库地址
export REGISTRY=ghcr.io/602420232-dotcom
export TAG=v2.0.0

# 构建并推送 Java 微服务镜像
mvn clean package -DskipTests
docker build -f Dockerfile.jre --build-arg JAR_FILE=services/weather-api/target/weather-api-2.0.0.jar --build-arg SERVICE_NAME=weather-api -t ${REGISTRY}/weather-api:${TAG} .
docker push ${REGISTRY}/weather-api:${TAG}

# 对其他服务重复上述步骤...

# 构建并推送 Python 算法引擎
docker build -f python/algorithm-engine/Dockerfile -t ${REGISTRY}/algorithm-engine:${TAG} ./python/algorithm-engine
docker push ${REGISTRY}/algorithm-engine:${TAG}

# 构建并推送前端控制台
docker build -f console/Dockerfile -t ${REGISTRY}/console:${TAG} ./console
docker push ${REGISTRY}/console:${TAG}
```

### 12.3 使用 Helm 部署

```bash
# 创建命名空间
kubectl create namespace uav-platform

# 查看可配置项
helm show values helm/uav-platform

# 使用默认值部署
helm install uav-platform helm/uav-platform \
  --namespace uav-platform \
  --set secrets.mysqlPassword=<strong_password> \
  --set secrets.redisPassword=<redis_password> \
  --set secrets.jwtSecret=<jwt_secret> \
  --set secrets.nacosPassword=<nacos_password>

# 使用 staging 配置部署
helm install uav-platform helm/uav-platform \
  --namespace uav-platform \
  -f helm/uav-platform/values-staging.yaml \
  --set secrets.mysqlPassword=<strong_password>

# 使用 production 配置部署
helm install uav-platform helm/uav-platform \
  --namespace uav-platform \
  -f helm/uav-platform/values-prod.yaml \
  --set secrets.mysqlPassword=<strong_password>
```

### 12.4 Helm 常用操作

```bash
# 查看部署状态
helm status uav-platform -n uav-platform

# 查看所有 Pod 状态
kubectl get pods -n uav-platform

# 升级部署
helm upgrade uav-platform helm/uav-platform \
  --namespace uav-platform \
  --set global.imageTag=v2.0.1

# 回滚到上一版本
helm rollback uav-platform -n uav-platform

# 卸载
helm uninstall uav-platform -n uav-platform
```

### 12.5 K8s 资源说明

Helm Chart 会创建以下资源：

| 资源类型 | 数量 | 说明 |
|---------|------|------|
| Deployment | 9 | 各微服务 + 算法引擎 |
| Service | 9 | ClusterIP 服务 |
| Ingress | 1 | Nginx Ingress 入口 |
| HPA | 3 | API Gateway、Platform API、Algorithm Engine 自动扩缩容 |
| ConfigMap | 1 | 全局配置 |
| Secret | 1 | 敏感信息（密码、Token） |

### 12.6 环境变量覆盖

通过 Helm values 覆盖环境变量：

```yaml
# my-values.yaml
global:
  imageRegistry: my-registry.example.com
  imageTag: "v2.0.0"
  springProfilesActive: "prod"

secrets:
  mysqlPassword: "prod-mysql-password"
  redisPassword: "prod-redis-password"
  jwtSecret: "prod-jwt-secret"

apiGateway:
  replicaCount: 3

algorithmEngine:
  replicaCount: 2
```

```bash
helm install uav-platform helm/uav-platform \
  -n uav-platform \
  -f my-values.yaml
```
