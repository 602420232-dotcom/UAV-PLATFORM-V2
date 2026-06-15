# UAV Platform V2 运维手册

> 最后更新：2026-06-15

## 1. 服务健康检查

### 1.1 一键健康检查脚本

```bash
#!/bin/bash
# health-check.sh - UAV Platform V2 全服务健康检查

echo "=== UAV Platform V2 Health Check ==="
echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

FAIL_COUNT=0

check_service() {
    local name=$1
    local port=$2
    local path=$3

    if [ "$path" = "/health" ]; then
        status=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:$port$path" 2>/dev/null)
    else
        status=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:$port$path" 2>/dev/null)
    fi

    if [ "$status" = "200" ]; then
        printf "  [OK]    %-25s port=%-5s\n" "$name" "$port"
    else
        printf "  [FAIL]  %-25s port=%-5s status=%s\n" "$name" "$port" "$status"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

# Java 微服务
check_service "API Gateway"       8258 "/actuator/health"
check_service "Platform API"      8251 "/actuator/health"
check_service "Weather API"       8252 "/actuator/health"
check_service "Assimilation API"  8253 "/actuator/health"
check_service "Risk API"          8254 "/actuator/health"
check_service "Observation API"   8255 "/actuator/health"
check_service "Planning API"      8256 "/actuator/health"
check_service "UTM API"           8259 "/actuator/health"

# Python 算法引擎
check_service "Algorithm Engine"  9095 "/health"

# 前端控制台
check_service "Console"           3000 "/"

# 基础设施
check_service "Nacos"            8950 "/nacos/v1/ns/operator/metrics"
check_service "Prometheus"       19091 "/-/healthy"
check_service "Grafana"          3001 "/api/health"
check_service "AlertManager"      19093 "/-/healthy"

echo ""
if [ $FAIL_COUNT -eq 0 ]; then
    echo "All services healthy."
else
    echo "WARNING: $FAIL_COUNT service(s) unhealthy!"
    exit 1
fi
```

### 1.2 Docker 容器状态

```bash
# 查看全部容器状态
docker compose ps

# 仅查看异常容器
docker compose ps | grep -v "running\|Up"

# 查看容器资源使用
docker stats --no-stream
```

### 1.3 K8s 健康检查

```bash
# 查看 Pod 状态
kubectl get pods -n uav-platform

# 查看异常 Pod
kubectl get pods -n uav-platform | grep -v Running

# 查看事件
kubectl get events -n uav-platform --sort-by='.lastTimestamp'

# 查看服务端点
kubectl get endpoints -n uav-platform
```

## 2. 日志查看

### 2.1 Docker Compose 日志

```bash
# 查看全部服务日志（实时跟踪）
docker compose logs -f

# 查看指定服务日志
docker compose logs -f algorithm-engine
docker compose logs -f api-gateway

# 查看最近 100 行
docker compose logs --tail 100 algorithm-engine

# 查看指定时间之后的日志
docker compose logs --since 30m algorithm-engine

# 只看错误日志
docker compose logs algorithm-engine 2>&1 | grep -i "error\|exception\|traceback"
```

### 2.2 Java 微服务日志级别

```bash
# 动态调整日志级别（Spring Boot Actuator）
curl -X POST http://localhost:8252/actuator/loggers/com.uav.weather \
  -H "Content-Type: application/json" \
  -d '{"configuredLevel": "DEBUG"}'

# 查看当前日志级别
curl http://localhost:8252/actuator/loggers/com.uav.weather
```

### 2.3 Python 算法引擎日志

```bash
# 查看算法引擎日志
docker compose logs -f algorithm-engine

# 调整日志级别（通过环境变量）
ALGORITHM_ENGINE_LOG_LEVEL=DEBUG docker compose up -d algorithm-engine

# 常见日志模式
docker compose logs algorithm-engine 2>&1 | grep -E "ERROR|WARNING|task_id"
```

### 2.4 K8s 日志

```bash
# 查看 Pod 日志
kubectl logs -f deployment/algorithm-engine -n uav-platform

# 查看上一个容器的日志（崩溃后）
kubectl logs deployment/algorithm-engine -n uav-platform --previous

# 查看多个 Pod 日志
kubectl logs -l app=weather-api -n uav-platform --all-containers
```

## 3. 常见故障排查

### 3.1 服务启动失败

**现象**：容器反复重启，`docker compose ps` 显示 `restarting`

```bash
# 1. 查看容器退出日志
docker compose logs --tail 200 <service_name>

# 2. 常见原因排查
#    - 端口被占用: netstat -ano | findstr :PORT
#    - 内存不足: 检查 JVM -Xmx 是否超过容器限制
#    - 配置错误: 检查环境变量是否正确
#    - 依赖不可用: 检查 MySQL/Redis/Kafka 是否健康
```

### 3.2 API Gateway 502 Bad Gateway

**现象**：通过 Gateway 访问后端服务返回 502

```bash
# 1. 检查目标服务是否运行
docker compose ps weather-api

# 2. 直接访问目标服务（绕过 Gateway）
curl http://localhost:8252/actuator/health

# 3. 检查 Gateway 路由配置
docker compose logs api-gateway --tail 50 | grep -i route

# 4. 检查 Redis 连接（Gateway 依赖 Redis）
docker compose exec api-gateway curl -sf http://redis:6379/ping
```

### 3.3 算法任务超时

**现象**：规划/同化任务长时间处于 RUNNING 状态

```bash
# 1. 检查算法引擎健康
curl http://localhost:9095/health

# 2. 检查 Kafka 消息积压
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 --describe --all-groups

# 3. 检查算法引擎日志
docker compose logs algorithm-engine --tail 100 | grep -i "error\|timeout"

# 4. 检查算法执行指标
curl -sf http://localhost:9095/metrics | grep algorithm_engine
```

### 3.4 数据库连接池耗尽

**现象**：服务日志报 `HikariPool-1 - Connection is not available`

```bash
# 1. 查看当前连接数
docker compose exec mysql mysql -uroot -prootpass \
  -e "SHOW STATUS LIKE 'Threads_connected'"

# 2. 查看活跃连接
docker compose exec mysql mysql -uroot -prootpass \
  -e "SHOW PROCESSLIST"

# 3. 检查是否有长时间运行的查询
docker compose exec mysql mysql -uroot -prootpass \
  -e "SELECT * FROM information_schema.PROCESSLIST WHERE TIME > 60 ORDER BY TIME DESC"

# 4. 临时方案：增大连接池
# 在 docker-compose.yml 中添加 JAVA_OPTS 环境变量
```

### 3.5 Redis 内存满

**现象**：Redis 告警或缓存失效

```bash
# 1. 检查 Redis 内存使用
docker compose exec redis redis-cli info memory | grep used_memory_human

# 2. 检查 maxmemory 设置
docker compose exec redis redis-cli config get maxmemory

# 3. 查看键空间
docker compose exec redis redis-cli info keyspace

# 4. 清理过期键
docker compose exec redis redis-cli --scan --pattern "*" | head 100 | xargs redis-cli del
```

## 4. 扩缩容操作

### 4.1 Docker Compose 扩缩容

```bash
# 扩展 API Gateway 到 3 副本
docker compose up -d --scale api-gateway=3

# 扩展算法引擎到 3 副本
docker compose up -d --scale algorithm-engine=3

# 注意：Docker Compose 不支持内置负载均衡，
# 多副本需要配合 Nginx/HAProxy 或使用 K8s。
```

### 4.2 K8s 扩缩容

```bash
# 手动扩缩容
kubectl scale deployment api-gateway --replicas=5 -n uav-platform
kubectl scale deployment algorithm-engine --replicas=3 -n uav-platform

# 查看 HPA 状态
kubectl get hpa -n uav-platform

# 查看 HPA 详细事件
kubectl describe hpa api-gateway -n uav-platform

# 临时禁用 HPA 自动扩缩容
kubectl scale deployment api-gateway --replicas=3 -n uav-platform
kubectl patch hpa api-gateway -n uav-platform -p '{"spec":{"minReplicas":3,"maxReplicas":3}}'
```

### 4.3 扩缩容决策参考

| 指标 | 扩容阈值 | 缩容阈值 | 说明 |
|------|---------|---------|------|
| CPU 使用率 | > 70% | < 30% | 持续 5 分钟 |
| 内存使用率 | > 85% | < 50% | 持续 5 分钟 |
| P99 延迟 | > 2s | < 500ms | 持续 10 分钟 |
| Kafka 消费者 lag | > 1000 | < 100 | 持续 5 分钟 |
| 活跃连接数 | > 80% 最大值 | < 30% | 持续 5 分钟 |

## 5. 备份恢复

### 5.1 MySQL 备份

```bash
# 全库备份
docker compose exec mysql mysqldump -uroot -prootpass \
  --all-databases --single-transaction --routines --triggers \
  > backup_$(date +%Y%m%d_%H%M%S).sql

# 单库备份
docker compose exec mysql mysqldump -uroot -prootpass \
  --single-transaction uav_platform > uav_platform_backup.sql
docker compose exec mysql mysqldump -uroot -prootpass \
  --single-transaction uav_planning > uav_planning_backup.sql

# 定时备份（crontab，每天凌晨 2 点）
# 0 2 * * * docker exec uav-mysql mysqldump -uroot -prootpass \
#   --all-databases --single-transaction > /backup/mysql/daily_$(date +\%Y\%m\%d).sql
```

### 5.2 MySQL 恢复

```bash
# 恢复全库
docker compose exec -T mysql mysql -uroot -prootpass < backup_20260615.sql

# 恢复单库
docker compose exec -T mysql mysql -uroot -prootpass uav_platform < uav_platform_backup.sql

# 恢复前确认备份文件完整性
head -20 backup_20260615.sql
```

### 5.3 Redis 备份

```bash
# 手动触发 RDB 快照
docker compose exec redis redis-cli BGSAVE

# 备份 RDB 文件
docker cp uav-redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb

# 备份 AOF 文件（如果启用）
docker cp uav-redis:/data/appendonly.aof ./redis_aof_backup_$(date +%Y%m%d).aof
```

### 5.4 Grafana 备份

```bash
# 备份 Grafana 数据库
docker cp uav-grafana:/var/lib/grafana/grafana.db ./grafana_backup_$(date +%Y%m%d).db

# 备份 Dashboard 配置
docker cp uav-grafana:/var/lib/grafana/dashboards ./grafana_dashboards_backup/
```

### 5.5 Nacos 配置备份

```bash
# 导出 Nacos 配置
curl -s "http://localhost:8950/nacos/v1/cs/configs?export=true&group=&dataId=&tenant=" \
  -o nacos_config_backup_$(date +%Y%m%d).zip
```

### 5.6 备份验证

```bash
# 恢复到测试环境验证
docker compose -f docker-compose.yml -f docker-compose.staging.yml exec -T mysql \
  mysql -uroot -prootpass < backup_20260615.sql

# 验证表数量
docker compose exec mysql mysql -uroot -prootpass \
  -e "SELECT table_schema, COUNT(*) FROM information_schema.tables GROUP BY table_schema"
```

## 6. 应急响应流程

### 6.1 服务不可用

```
1. 确认影响范围（哪些服务、哪些用户）
2. 检查 Prometheus 告警
3. 查看服务日志
4. 判断是否需要回滚
5. 执行恢复操作
6. 验证恢复结果
7. 记录故障报告
```

### 6.2 数据库故障

```
1. 确认 MySQL 容器状态
2. 检查磁盘空间
3. 查看 MySQL 错误日志
4. 尝试重启 MySQL 容器
5. 如数据损坏，从最近备份恢复
6. 验证数据完整性
```

### 6.3 Kafka 故障

```
1. 检查 Kafka Broker 状态
2. 检查 Zookeeper 状态
3. 查看消费者 lag
4. 算法引擎自动重连（确认日志）
5. 如消息丢失，确认是否需要手动补偿
```

## 7. 运维检查清单

### 7.1 每日检查

- [ ] 全服务健康检查通过
- [ ] Prometheus 无 critical 告警
- [ ] Kafka 消费者 lag < 100
- [ ] 磁盘使用率 < 80%

### 7.2 每周检查

- [ ] 慢查询分析
- [ ] 数据库连接池使用率
- [ ] Redis 内存使用率
- [ ] 备份完整性验证
- [ ] 证书有效期检查

### 7.3 每月检查

- [ ] 数据归档执行
- [ ] 索引使用分析
- [ ] 日志轮转正常
- [ ] 容量规划评估
- [ ] 安全补丁更新
