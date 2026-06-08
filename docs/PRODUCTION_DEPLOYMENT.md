# 生产环境部署指南

## 1. 概述

本文档提供无人机气象路径规划系统在生产环境中的完整部署配置指南，包括安全配置、性能优化、监控告警和灾难恢复等关键内容。

---

## 2. 环境准备

### 2.1 系统要求

| 资源类型 | 最小配置 | 推荐配置 |
|---------|---------|---------|
| CPU | 8核 | 16核 |
| 内存 | 16GB | 32GB |
| 磁盘 | 100GB SSD | 500GB SSD |
| 网络 | 100Mbps | 1Gbps |

### 2.2 软件依赖

| 软件 | 版本 | 用途 |
|------|------|------|
| Docker Engine | 24.0+ | 容器运行时 |
| Docker Compose | 2.20+ | 容器编排 |
| MySQL | 8.0+ | 数据库 |
| Redis | 7.2+ | 缓存 |
| Nacos | 2.3+ | 服务注册 |
| Kafka | 7.5+ | 消息队列 |

---

## 3. 环境变量配置

### 3.1 必需的环境变量

创建 `.env.production` 文件：

```env
# 数据库配置
DB_PASSWORD=your-strong-db-password
MYSQL_ROOT_PASSWORD=your-root-password

# JWT 密钥（至少32位随机字符串）
JWT_SECRET=your-jwt-secret-key-must-be-at-least-32-characters

# API 认证密钥
FENGLEI_API_KEY=your-fenglei-production-key
TIANZI_API_KEY=your-tianzi-production-key

# 外部服务 API 密钥（可选）
CMA_API_KEY=your-cma-api-key
OWM_API_KEY=your-openweathermap-api-key
ECMWF_API_KEY=your-ecmwf-api-key

# 运行环境
TIANZI_ENV=production
SPRING_PROFILES_ACTIVE=prod
```

### 3.2 密钥管理建议

**生产环境禁止**：
- 直接在 `docker-compose.yml` 中硬编码密钥
- 使用默认的开发密钥
- 将密钥提交到版本控制系统

**推荐做法**：
- 使用 Docker Secrets 或 Kubernetes Secrets
- 使用 HashiCorp Vault 进行密钥管理
- 通过环境变量注入敏感配置

---

## 4. 安全配置

### 4.1 网络安全

```yaml
# docker-compose.prod.yml 网络配置
networks:
  uav-net:
    driver: bridge
    internal: true
  uav-public:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24

services:
  api-gateway:
    networks:
      - uav-net
      - uav-public
    ports:
      - "443:8443"
  
  mysql:
    networks:
      - uav-net
    # 禁止外部访问
```

### 4.2 HTTPS 配置

使用 Nginx 作为反向代理，配置 SSL：

```nginx
server {
    listen 443 ssl;
    server_name uav-platform.example.com;
    
    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://api-gateway:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4.3 服务认证配置

**风雷服务 (FengLei)**：
- API密钥可选配置：未设置 `FENGLEI_API_KEY` 时服务以演示模式运行
- 演示模式下自动使用模拟数据，所有请求不需要认证
- 配置密钥后启用API认证，所有请求必须携带 `X-API-Key` 头
- 提供 `/api/v1/status` 接口供前端查询配置状态

**天资服务 (TianZi)**：
- API密钥可选配置：未设置 `TIANZI_API_KEY` 时服务以演示模式运行
- 演示模式下自动使用模拟数据，所有请求不需要认证
- 配置密钥后启用API认证，所有请求必须携带 `X-API-Key` 头
- 提供 `/api/v1/status` 接口供前端查询配置状态

**WRF处理器服务**：
- 不需要API密钥
- 通过Java后端调用Python脚本处理WRF文件

**状态接口响应格式**：
```json
{
  "service": "fenglei-service",
  "status": "healthy",
  "api_key_configured": false,
  "mode": "demo",
  "message": "API key not configured - running in demo mode",
  "action_required": true,
  "action_message": "Please configure FENGLEI_API_KEY environment variable"
}
```

---

## 5. 性能优化

### 5.1 JVM 配置

```yaml
environment:
  JAVA_TOOL_OPTIONS: >-
    -Xms512m
    -Xmx1024m
    -XX:+UseG1GC
    -XX:MaxGCPauseMillis=200
    -XX:+HeapDumpOnOutOfMemoryError
    -XX:HeapDumpPath=/logs/heapdump.hprof
```

### 5.2 MySQL 优化

```ini
# /etc/mysql/my.cnf
[mysqld]
innodb_buffer_pool_size = 4G
innodb_log_file_size = 1G
innodb_flush_log_at_trx_commit = 1
query_cache_type = 0
query_cache_size = 0
max_connections = 500
```

### 5.3 Redis 优化

```ini
# redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
```

### 5.4 Kafka 配置

```yaml
kafka:
  environment:
    KAFKA_HEAP_OPTS: "-Xms2G -Xmx2G"
    KAFKA_LOG_RETENTION_HOURS: "168"
    KAFKA_NUM_PARTITIONS: "3"
    KAFKA_DEFAULT_REPLICATION_FACTOR: "1"
```

---

## 6. 监控与告警

### 6.1 健康检查配置

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/actuator/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 120s
```

### 6.2 监控指标

| 指标类型 | 监控内容 | 告警阈值 |
|---------|---------|---------|
| 服务健康 | Actuator health endpoint | 连续3次失败 |
| CPU | 容器CPU使用率 | >80%持续5分钟 |
| 内存 | JVM堆内存使用 | >85%持续5分钟 |
| 磁盘 | 磁盘空间使用率 | >90% |
| 网络 | 网络延迟 | >500ms |

### 6.3 日志管理

使用 ELK Stack 进行集中日志管理：

```yaml
services:
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - ES_JAVA_OPTS=-Xms2g -Xmx2g
  
  logstash:
    image: logstash:8.11.0
    volumes:
      - ./logstash/config:/usr/share/logstash/config
      - ./logstash/pipeline:/usr/share/logstash/pipeline
  
  kibana:
    image: kibana:8.11.0
    ports:
      - "5601:5601"
```

---

## 7. 灾难恢复

### 7.1 数据库备份

**每日全量备份**：
```bash
#!/bin/bash
BACKUP_DIR="/backup/mysql"
DATE=$(date +%Y%m%d_%H%M%S)
CONTAINER_NAME="uav-mysql"

mkdir -p $BACKUP_DIR

docker exec $CONTAINER_NAME mysqldump \
  -u root \
  -p${MYSQL_ROOT_PASSWORD} \
  --all-databases \
  --single-transaction \
  --compress \
  > ${BACKUP_DIR}/backup_${DATE}.sql.gz

# 保留最近7天的备份
find $BACKUP_DIR -type f -name "*.sql.gz" -mtime +7 -delete
```

**定时任务配置**：
```bash
# /etc/cron.daily/mysql-backup
0 2 * * * root /usr/local/bin/mysql-backup.sh
```

### 7.2 Redis 备份

```bash
docker exec uav-redis redis-cli BGSAVE
docker cp uav-redis:/data/dump.rdb /backup/redis/dump_$(date +%Y%m%d).rdb
```

### 7.3 服务故障恢复

| 服务 | 恢复策略 | RTO |
|------|---------|-----|
| MySQL | 从备份恢复 | 30分钟 |
| Redis | 从RDB恢复 | 10分钟 |
| Kafka | 重新创建Topic | 5分钟 |
| Nacos | 重新初始化 | 5分钟 |

---

## 8. 部署流程

### 8.1 部署前检查

```bash
# 检查环境变量
cat .env.production

# 检查 Docker 版本
docker --version
docker compose version

# 检查系统资源
free -h
df -h
```

### 8.2 启动命令

```bash
# 使用生产环境配置
docker compose --env-file .env.production -f docker-compose.yml up -d

# 查看启动状态
docker compose ps

# 检查服务健康
docker compose exec api-gateway curl -s http://localhost:8088/actuator/health
```

### 8.3 蓝绿部署策略

```bash
# 启动新版本（蓝环境）
docker compose --env-file .env.production up -d --scale api-gateway=2

# 健康检查通过后切换流量
# 更新负载均衡配置指向新版本

# 停止旧版本（绿环境）
docker compose stop api-gateway-old
```

---

## 9. 运维命令参考

### 9.1 服务管理

```bash
# 查看所有服务状态
docker compose ps

# 查看服务日志
docker compose logs -f <service-name>

# 重启服务
docker compose restart <service-name>

# 查看资源使用
docker stats

# 进入容器
docker exec -it <container-name> /bin/bash
```

### 9.2 数据库操作

```bash
# 进入 MySQL
docker exec -it uav-mysql mysql -u root -p

# 执行 SQL 文件
docker exec -i uav-mysql mysql -u root -p < backup.sql

# 查看 Redis
docker exec -it uav-redis redis-cli
```

### 9.3 Kafka 操作

```bash
# 查看 Topic
docker exec uav-kafka kafka-topics --bootstrap-server localhost:9092 --list

# 创建 Topic
docker exec uav-kafka kafka-topics --create \
  --topic weather-data \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1
```

---

## 10. 安全审计清单

- [ ] 所有敏感配置使用环境变量
- [ ] 数据库密码强度符合要求（至少16位，包含大小写字母、数字、特殊字符）
- [ ] JWT 密钥长度至少32位
- [ ] 使用 HTTPS 加密传输
- [ ] 禁止直接暴露内部服务端口
- [ ] 启用服务认证（FENGLEI_API_KEY, TIANZI_API_KEY）
- [ ] 配置防火墙规则限制外部访问
- [ ] 定期备份数据库和配置
- [ ] 定期更新依赖包
- [ ] 启用审计日志

---

## 附录：服务端口汇总

| 服务 | 内部端口 | 外部端口 | 说明 |
|------|---------|---------|------|
| API Gateway | 8088 | 443 (HTTPS) | 对外统一入口 |
| MySQL | 3306 | - | 内部服务 |
| Redis | 6379 | - | 内部服务 |
| Nacos | 8848 | - | 内部服务 |
| Kafka | 9092 | - | 内部服务 |
| Zookeeper | 2181 | - | 内部服务 |
| Frontend | 80 | 443 (HTTPS) | 前端应用 |

---

**版本**: v1.0  
**最后更新**: 2026-06-08  
**维护者**: DITHIOTHREITOL