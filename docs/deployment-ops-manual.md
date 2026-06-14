# UAV Platform V2 部署运维手册

> 最后更新：2026-06-14

## 1. 环境要求

### 1.1 软件依赖

| 组件 | 最低版本 | 推荐版本 | 说明 |
|------|---------|---------|------|
| Docker | 24.0+ | 25.0+ | 容器运行时 |
| Docker Compose | 2.20+ | 2.30+ | 容器编排（V2 插件） |
| JDK | 21+ | Eclipse Temurin 21 | 主项目 Spring Boot 4.0 |
| Maven | 3.9+ | 3.9.6 | Java 项目构建 |
| Python | 3.12+ | 3.12.x | algorithm-engine (FastAPI) |
| Node.js | 20+ | 20 LTS | 前端控制台 (Vue 3 + Vite 7) |
| Git | 2.40+ | 2.45+ | 代码管理 |

### 1.2 硬件要求

| 环境 | CPU | 内存 | 磁盘 | 说明 |
|------|-----|------|------|------|
| 开发环境 | 4 核 | 16 GB | 50 GB SSD | 可运行全部服务 |
| Staging | 8 核 | 32 GB | 200 GB SSD | 含监控组件 |
| 生产环境 | 16 核 | 64 GB | 500 GB SSD | 含副本扩容 |

### 1.3 操作系统

- Ubuntu 22.04 LTS / 24.04 LTS（推荐）
- CentOS Stream 9 / Rocky Linux 9
- Windows Server 2022（仅限开发环境）

## 2. 快速启动

### 2.1 一键启动全栈

```bash
# 克隆项目
git clone https://github.com/your-org/uav-platform-v2.git
cd uav-platform-v2

# 构建并启动全部 16 个容器
docker compose up -d

# 查看启动状态
docker compose ps
```

### 2.2 仅启动基础设施

```bash
docker compose up -d mysql redis kafka zookeeper nacos
```

### 2.3 验证部署

```bash
# API Gateway 健康检查
curl -sf http://localhost:8258/actuator/health | jq .

# Nacos 控制台
curl -sf http://localhost:8950/nacos/ | head -5

# Prometheus
curl -sf http://localhost:19091/-/healthy

# Grafana
curl -sf http://localhost:3001/api/health

# 前端控制台
curl -sf http://localhost:3000/ | head -5
```

## 3. 环境变量说明

### 3.1 基础设施

| 服务 | 环境变量 | 默认值 | 说明 |
|------|---------|--------|------|
| MySQL | `MYSQL_ROOT_PASSWORD` | `rootpass` | root 密码 |
| MySQL | `MYSQL_DATABASE` | `nacos` | 默认数据库 |
| MySQL | `MYSQL_USER` / `MYSQL_PASSWORD` | `nacos` / `nacos` | Nacos 专用账号 |
| Redis | (command 参数) | `--appendonly yes --maxmemory 512mb` | 持久化 + 内存限制 |
| Nacos | `MODE` | `standalone` | 运行模式 |
| Nacos | `NACOS_AUTH_TOKEN` | Base64 编码 | JWT Token（>= 32 字节） |
| Kafka | `KAFKA_BROKER_ID` | `1` | Broker ID |
| Kafka | `KAFKA_LOG_RETENTION_HOURS` | `24` | 日志保留时间 |

### 3.2 Java 微服务（通用）

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `SPRING_PROFILES_ACTIVE` | `docker` | Spring Profile |
| `NACOS_SERVER_ADDR` | `nacos:8848` | Nacos 地址 |
| `SPRING_DATASOURCE_URL` | `jdbc:mysql://mysql:3306/{db}` | 数据库连接 |
| `MYSQL_HOST` / `MYSQL_PORT` | `mysql` / `3306` | MySQL 地址 |
| `MYSQL_USER` / `MYSQL_PASSWORD` | `root` / `rootpass` | MySQL 凭证 |
| `REDIS_HOST` / `REDIS_PORT` | `redis` / `6379` | Redis 地址 |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka 地址 |
| `KAFKA_MOCK` | `false` | Mock 模式开关（生产必须 false） |
| `ALGORITHM_ENGINE_URL` | `http://algorithm-engine:9090` | 算法引擎地址 |
| `JAVA_OPTS` | `-Xms256m -Xmx512m -XX:+UseG1GC` | JVM 参数 |

### 3.3 API Gateway

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `SPRING_DATA_REDIS_HOST` | `redis` | Redis 地址 |
| `SPRING_DATA_REDIS_PORT` | `6379` | Redis 端口 |

### 3.4 Python 算法引擎

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `ALGORITHM_ENGINE_KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka 地址 |
| `ALGORITHM_ENGINE_REDIS_URL` | `redis://redis:6379/0` | Redis URL |
| `ALGORITHM_ENGINE_NACOS_HOST` | `nacos` | Nacos 主机 |
| `ALGORITHM_ENGINE_NACOS_PORT` | `8848` | Nacos 端口 |
| `LOG_LEVEL` | `INFO` | 日志级别 |

### 3.5 前端控制台

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| (无额外环境变量) | -- | 通过 Nginx 反向代理 |

### 3.6 监控组件

| 服务 | 环境变量 | 默认值 | 说明 |
|------|---------|--------|------|
| Grafana | `GF_SECURITY_ADMIN_USER` | `admin` | 管理员用户名 |
| Grafana | `GF_SECURITY_ADMIN_PASSWORD` | `admin123` | 管理员密码 |
| Grafana | `GF_USERS_ALLOW_SIGN_UP` | `false` | 禁止注册 |

## 4. 服务端口映射表

### 4.1 Docker 容器端口

| 容器名 | 内部端口 | 宿主机端口 | 协议 | 说明 |
|--------|---------|-----------|------|------|
| uav-gateway | 8088 | 8258 | HTTP | API Gateway |
| uav-platform-api | 8081 | 8251 | HTTP | 平台管理服务 |
| uav-weather-api | 8082 | 8252 | HTTP | 气象数据服务 |
| uav-assimilation-api | 8083 | 8253 | HTTP | 数据同化服务 |
| uav-risk-api | 8084 | 8254 | HTTP | 风险评估服务 |
| uav-observation-api | 8085 | 8255 | HTTP | 观测决策服务 |
| uav-planning-api | 8086 | 8256 | HTTP | 航迹规划服务 |
| uav-utm-api | 8087 | 8259 | HTTP | UTM 管理服务 |
| uav-algorithm-engine | 9090 | 9095 | HTTP | Python 算法引擎 |
| uav-console | 80 | 3000 | HTTP | 前端控制台 |
| uav-mysql | 3306 | 3306 | TCP | MySQL 数据库 |
| uav-redis | 6379 | 6379 | TCP | Redis 缓存 |
| uav-nacos | 8848 | 8950 | HTTP | Nacos 控制台 |
| uav-kafka | 9092 | 19092 | TCP | Kafka Broker |
| uav-prometheus | 9090 | 19091 | HTTP | Prometheus 监控 |
| uav-grafana | 3000 | 3001 | HTTP | Grafana 可视化 |
| uav-alertmanager | 9093 | 19093 | HTTP | AlertManager 告警 |
| uav-zookeeper | 2181 | -- | TCP | Zookeeper（仅容器内部） |

### 4.2 API Gateway 路由

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

## 5. 健康检查端点

| 服务 | 端点 | 预期响应 | 说明 |
|------|------|---------|------|
| API Gateway | `GET /actuator/health` | `{"status":"UP"}` | Spring Boot Actuator |
| platform-api | `GET /actuator/health` | `{"status":"UP"}` | -- |
| weather-api | `GET /actuator/health` | `{"status":"UP"}` | -- |
| assimilation-api | `GET /actuator/health` | `{"status":"UP"}` | -- |
| risk-api | `GET /actuator/health` | `{"status":"UP"}` | -- |
| observation-api | `GET /actuator/health` | `{"status":"UP"}` | -- |
| planning-api | `GET /actuator/health` | `{"status":"UP"}` | -- |
| utm-api | `GET /actuator/health` | `{"status":"UP"}` | -- |
| algorithm-engine | `GET /health` | `{"status":"ok"}` | FastAPI |
| console | `GET /` | HTML 页面 | Nginx |
| MySQL | `mysqladmin ping` | `mysqld is alive` | Docker healthcheck |
| Redis | `redis-cli ping` | `PONG` | Docker healthcheck |
| Nacos | `GET /nacos/v1/ns/operator/metrics` | JSON 指标 | Docker healthcheck |
| Prometheus | `GET /-/healthy` | `Prometheus is Healthy.` | Docker healthcheck |
| Grafana | `GET /api/health` | `{"commit":"...","database":"ok"}` | Docker healthcheck |
| AlertManager | `GET /-/healthy` | `OK` | Docker healthcheck |

快速检查脚本：

```bash
#!/bin/bash
echo "=== UAV Platform V2 Health Check ==="
for svc in gateway:8258 platform-api:8251 weather-api:8252 \
           assimilation-api:8253 risk-api:8254 observation-api:8255 \
           planning-api:8256 utm-api:8259 algorithm-engine:9095; do
  name=${svc%%:*}; port=${svc##*:};
  status=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:$port/actuator/health 2>/dev/null \
    || curl -sf -o /dev/null -w "%{http_code}" http://localhost:$port/health 2>/dev/null \
    || echo "000")
  printf "  %-25s %s\n" "$name" "$([ "$status" = "200" ] && echo OK || echo FAIL($status))"
done
```

## 6. 常见故障排查

### 6.1 MySQL 连接失败

**现象**：服务启动日志报 `Communications link failure` 或 `Access denied`

**排查步骤**：

```bash
# 1. 检查 MySQL 容器状态
docker compose ps mysql

# 2. 检查 MySQL 日志
docker compose logs mysql --tail 50

# 3. 手动连接测试
docker compose exec mysql mysql -uroot -prootpass -e "SELECT 1"

# 4. 检查网络连通性
docker compose exec platform-api ping -c 1 mysql

# 5. 修复远程访问权限
docker compose exec mysql mysql -uroot -prootpass -e \
  "ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY 'rootpass'; FLUSH PRIVILEGES;"
```

**常见原因**：
- MySQL 未完全启动（等待 healthcheck 通过）
- `allowPublicKeyRetrieval=true` 未配置
- 密码或用户名不匹配
- 网络不通（检查 Docker 网络配置）

### 6.2 Kafka 消息积压

**现象**：算法任务长时间处于 pending 状态，消费者 lag 持续增长

**排查步骤**：

```bash
# 1. 检查 Kafka Broker 状态
docker compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# 2. 查看 Topic 列表
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

# 3. 查看消费者 lag
docker compose exec kafka kafka-consumer-groups --bootstrap-server localhost:9092 --describe --all-groups

# 4. 检查算法引擎日志
docker compose logs algorithm-engine --tail 100 | grep -i error

# 5. 检查算法引擎 Kafka 连接
docker compose exec algorithm-engine python -c "
from app.transport.kafka_consumer import get_consumer
print('Kafka connection OK')
"
```

**常见原因**：
- 算法引擎未启动或 Kafka 连接失败
- 消费者处理速度慢（检查算法执行耗时）
- Topic 分区数不足
- `KAFKA_MOCK=true` 导致消息未真正发送

### 6.3 Redis 连接超时

**现象**：服务日志报 `RedisConnectionException` 或 `Connection timed out`

**排查步骤**：

```bash
# 1. 检查 Redis 容器状态
docker compose ps redis

# 2. 检查 Redis 内存使用
docker compose exec redis redis-cli info memory | grep used_memory_human

# 3. 检查 Redis 连接数
docker compose exec redis redis-cli info clients

# 4. 测试连通性
docker compose exec platform-api python -c "
import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())
" 2>/dev/null || docker compose exec redis redis-cli ping

# 5. 检查是否触发 maxmemory 限制
docker compose exec redis redis-cli info memory | grep -E "used_memory|maxmemory"
```

**常见原因**：
- Redis 内存达到 `maxmemory` 限制（默认 512MB），触发 LRU 淘汰
- 连接数耗尽
- 网络抖动

### 6.4 Nacos 不可用

**现象**：服务注册失败，日志报 `NacosException` 或 `Connection refused`

**排查步骤**：

```bash
# 1. 检查 Nacos 容器状态
docker compose ps nacos

# 2. 检查 Nacos 日志
docker compose logs nacos --tail 100

# 3. 检查 Nacos 健康端点
curl -sf http://localhost:8950/nacos/v1/ns/operator/metrics

# 4. 访问 Nacos 控制台
# 浏览器打开 http://localhost:8950/nacos/ (nacos/nacos)

# 5. 检查 JWT Token 长度
docker compose exec nacos env | grep NACOS_AUTH_TOKEN
# 确保长度 >= 32 字节 Base64 编码（>= 256 bits）
```

**常见原因**：
- `NACOS_AUTH_TOKEN` 长度不足（必须 >= 32 字节）
- MySQL 中 Nacos schema 未初始化（13 张表缺失）
- Nacos 依赖的 MySQL 未就绪

### 6.5 API Gateway 启动失败

**现象**：Gateway 容器反复重启

**排查步骤**：

```bash
# 1. 查看 Gateway 日志
docker compose logs api-gateway --tail 200

# 2. 常见原因：Spring Cloud Gateway 与 Spring Boot 4.0 不兼容
# 解决：使用 standalone 方式构建 Gateway
cd gateway/api-gateway
powershell -ExecutionPolicy Bypass -File build-standalone.ps1 -SkipTests
```

### 6.6 Prometheus 抓取失败

**现象**：Grafana Dashboard 无数据，Prometheus targets 页面显示 DOWN

**排查步骤**：

```bash
# 1. 检查 Prometheus targets
curl -sf http://localhost:19091/api/v1/targets | python -m json.tool

# 2. 确认目标服务暴露了 Prometheus 端点
curl -sf http://localhost:8258/actuator/prometheus | head -5

# 3. 检查 Prometheus 配置
docker compose exec prometheus cat /etc/prometheus/prometheus.yml

# 4. 检查 Prometheus 日志
docker compose logs prometheus --tail 50
```

## 7. 数据备份与恢复

### 7.1 MySQL 备份

```bash
# 全库备份
docker compose exec mysql mysqldump -uroot -prootpass --all-databases \
  --single-transaction --routines --triggers > backup_$(date +%Y%m%d_%H%M%S).sql

# 单库备份
docker compose exec mysql mysqldump -uroot -prootpass uav_platform > uav_platform_backup.sql
docker compose exec mysql mysqldump -uroot -prootpass uav_assimilation > uav_assimilation_backup.sql
docker compose exec mysql mysqldump -uroot -prootpass uav_planning > uav_planning_backup.sql
docker compose exec mysql mysqldump -uroot -prootpass uav_observation > uav_observation_backup.sql
docker compose exec mysql mysqldump -uroot -prootpass uav_utm > uav_utm_backup.sql

# 定时备份（crontab）
# 每天凌晨 2 点全量备份
0 2 * * * docker exec uav-mysql mysqldump -uroot -prootpass --all-databases --single-transaction > /backup/mysql/daily_$(date +\%Y\%m\%d).sql
```

### 7.2 MySQL 恢复

```bash
# 恢复全库
docker compose exec -T mysql mysql -uroot -prootpass < backup_20260614.sql

# 恢复单库
docker compose exec -T mysql mysql -uroot -prootpass uav_platform < uav_platform_backup.sql
```

### 7.3 Redis 备份

```bash
# Redis 使用 AOF 持久化，数据存储在 Docker Volume 中
# 手动触发 RDB 快照
docker compose exec redis redis-cli BGSAVE

# 备份 RDB 文件
docker cp uav-redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

### 7.4 Grafana 备份

```bash
# Grafana 数据存储在 Docker Volume 中
docker cp uav-grafana:/var/lib/grafana/grafana.db ./grafana_backup_$(date +%Y%m%d).db

# 备份 Dashboard 配置
docker cp uav-grafana:/var/lib/grafana/dashboards ./grafana_dashboards_backup/
```

## 8. 滚动更新与回滚

### 8.1 滚动更新（零停机）

```bash
# 更新单个服务（不重建依赖）
docker compose up -d --no-deps --build api-gateway

# 更新全部业务服务（保留基础设施）
docker compose up -d --no-deps --build \
  api-gateway platform-api weather-api assimilation-api \
  risk-api observation-api planning-api utm-api \
  algorithm-engine console

# 等待健康检查通过
timeout 120 bash -c 'until docker compose ps | grep -v "unhealthy\|starting" | grep -q "running"; do sleep 5; done'
docker compose ps
```

### 8.2 Staging 环境更新

```bash
docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d --build
```

### 8.3 生产环境更新

```bash
# 生产环境更新（必须使用 prod 配置）
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# 验证 Mock 已关闭
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec platform-api env | grep MOCK
# 预期: KAFKA_MOCK=false
```

### 8.4 回滚

```bash
# 回滚到上一版本（使用 git）
git checkout HEAD~1
docker compose up -d --build

# 回滚特定服务
docker compose up -d --no-deps --build api-gateway

# 紧急回滚（停止并使用备份镜像）
docker compose stop api-gateway
docker tag uav-platform-v2-api-gateway:previous uav-platform-v2-api-gateway:latest
docker compose up -d api-gateway
```

## 9. 监控告警说明

### 9.1 Prometheus 配置

配置文件：`monitoring/prometheus.yml`

抓取目标：

| Job | Target | 端口 | 指标路径 |
|-----|--------|------|---------|
| `gateway` | `api-gateway:8088` | 8088 | `/actuator/prometheus` |
| `platform-api` | `platform-api:8081` | 8081 | `/actuator/prometheus` |
| `weather-api` | `weather-api:8082` | 8082 | `/actuator/prometheus` |
| `planning-api` | `planning-api:8086` | 8086 | `/actuator/prometheus` |
| `algorithm-engine` | `algorithm-engine:9090` | 9090 | `/metrics` |

Prometheus 访问：`http://localhost:19091`

### 9.2 Grafana Dashboard

访问地址：`http://localhost:3001`（admin / admin123）

Dashboard 通过 provisioning 自动加载（`monitoring/grafana/provisioning/dashboards/`）。

推荐 Dashboard：

| Dashboard | 说明 | 关键面板 |
|-----------|------|---------|
| JVM Micrometer | Java 服务 JVM 指标 | 堆内存、GC 暂停、线程数 |
| Spring Boot | Spring Boot 应用指标 | HTTP 请求量、P99 延迟、错误率 |
| Algorithm Engine | Python 算法引擎 | 任务成功率、执行耗时、活跃任务数 |
| Kafka Exporter | Kafka 消息队列 | 消费者 lag、消息吞吐量 |
| Node Exporter | 主机资源 | CPU、内存、磁盘 I/O、网络 |

### 9.3 AlertManager 告警

配置文件：`monitoring/alertmanager.yml`

访问地址：`http://localhost:19093`

默认告警规则：

| 告警名称 | 级别 | 触发条件 | 持续时间 | 通知方式 |
|----------|------|---------|---------|---------|
| ServiceDown | critical | 健康检查失败 | 2 min | PagerDuty / 钉钉 |
| HighErrorRate | warning | HTTP 5xx > 5% | 5 min | 邮件 |
| HighLatency | warning | P99 > 2s | 5 min | 邮件 |
| KafkaLag | warning | 消费者 lag > 1000 | 10 min | 邮件 |
| AlgorithmEngineDown | critical | 算法引擎不可用 | 2 min | PagerDuty / 钉钉 |
| AlgorithmExecutionFail | warning | 执行失败率 > 10% | 5 min | 邮件 |
| HighMemoryUsage | warning | JVM 堆使用 > 85% | 5 min | 邮件 |

### 9.4 算法引擎 Prometheus 指标

| 指标名 | 类型 | 标签 | 说明 |
|--------|------|------|------|
| `algorithm_engine_tasks_total` | Counter | `status`, `algorithm_id` | 任务总数 |
| `algorithm_engine_execution_duration_seconds` | Histogram | `algorithm_id` | 执行耗时分布 |
| `algorithm_engine_active_tasks` | Gauge | -- | 当前活跃任务数 |
| `algorithm_engine_registered_algorithms` | Gauge | -- | 已注册算法数量 |
| `algorithm_engine_kafka_consumer_lag` | Gauge | `topic` | Kafka 消费者 lag |
| `algorithm_engine_errors_total` | Counter | `error_type` | 错误总数 |

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

## 10. 多环境部署

### 10.1 环境对照表

| 环境 | 配置文件 | Profile | Mock | 监控 | Debug | 镜像标签 |
|------|---------|---------|------|------|-------|---------|
| dev | `docker-compose.override.yml` | `dev,docker` | true | 可选 | 开启 | build |
| staging | `docker-compose.staging.yml` | `staging,docker` | false | 启用 | 关闭 | release |
| prod | `docker-compose.prod.yml` | `prod,docker` | false | 启用 | 关闭 | latest |

### 10.2 环境变量覆盖

通过 `.env` 文件覆盖默认配置：

```bash
# .env.prod
MYSQL_ROOT_PASSWORD=<strong_password>
NACOS_AUTH_TOKEN=<base64_encoded_token_min_32_bytes>
GF_SECURITY_ADMIN_PASSWORD=<grafana_password>
SPRING_PROFILES_ACTIVE=prod
KAFKA_MOCK=false
SECURITY_RBAC_ENABLED=true
```

## 11. 优雅停机

```bash
# 停止全部容器
docker compose down

# 停止并清除数据卷（慎用！会删除所有数据）
docker compose down -v

# 仅停止业务服务（保留基础设施）
docker compose stop api-gateway platform-api weather-api assimilation-api \
  risk-api observation-api planning-api utm-api algorithm-engine console

# 强制停止（容器无响应时）
docker compose kill <service_name>
```
