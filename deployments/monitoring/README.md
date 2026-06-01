# UAV Platform Monitoring & Logging Guide

## 📊 监控和日志聚合系统

本指南说明了如何配置和使用UAV平台的监控告警和日志聚合系统。

---

## 🚀 快速开始

### 1. 启动监控栈

```bash
# 进入监控目录
cd deployments/monitoring

# 启动所有监控服务
docker-compose -f docker-compose.monitoring.yml up -d

# 检查服务状态
docker-compose -f docker-compose.monitoring.yml ps
```

### 2. 访问监控界面

| 服务 | URL | 默认用户名 | 默认密码 |
|------|-----|----------|---------|
| Grafana | http://localhost:3000 | admin | changeme123 |
| Prometheus | http://localhost:9090 | - | - |
| Kibana | http://localhost:5601 | elastic | changeme123 |
| Alertmanager | http://localhost:9093 | - | - |
| Jaeger | http://localhost:16686 | - | - |

### 3. 配置环境变量

创建 `.env` 文件：

```bash
# Monitoring Configuration
GRAFANA_PASSWORD=your_secure_password
ELASTIC_PASSWORD=your_secure_password

# Slack Integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK

# SMTP Configuration
SMTP_PASSWORD=your_smtp_password
```

---

## 📈 Prometheus 监控

### Prometheus 配置

Prometheus 自动从以下服务收集指标：

1. **Spring Boot 应用**
   - `uav-platform-service:8080/actuator/prometheus`
   - `data-assimilation-service:8081/actuator/prometheus`
   - `meteor-forecast-service:8082/actuator/prometheus`

2. **Python 服务**
   - `path-planning-python:8000/metrics`
   - `data-assimilation-python:8001/metrics`

3. **基础设施**
   - MySQL (端口 9104)
   - Redis (端口 9121)
   - Nginx (端口 9113)
   - cAdvisor (端口 8080)

### 关键指标

#### 系统指标
- `cpu_usage_percent`: CPU使用率
- `memory_usage_percent`: 内存使用率
- `disk_usage_percent`: 磁盘使用率

#### 应用指标
- `http_requests_total`: HTTP请求总数
- `http_request_duration_seconds`: HTTP请求延迟
- `jvm_memory_used_bytes`: JVM内存使用

#### 业务指标
- `weather_data_collection_total`: 气象数据采集数
- `path_planning_requests_total`: 路径规划请求数
- `authentication_failures_total`: 认证失败次数

### 告警规则

告警分为以下级别：

1. **Critical（严重）**
   - 服务宕机
   - 错误率 > 20%
   - CPU/内存使用率 > 95%

2. **Warning（警告）**
   - 高错误率 > 5%
   - 高延迟 > 2秒
   - CPU/内存使用率 > 80%

3. **Info（信息）**
   - 建议扩缩容
   - 性能指标

### 查询示例

```promql
# CPU使用率
cpu_usage_percent

# 错误率
rate(http_requests_total{status=~"5.."}[5m])

# P95延迟
http_request_duration_seconds{quantile="0.95"}

# 请求率
rate(http_requests_total[5m])
```

---

## 📉 Grafana 仪表板

### 导入仪表板

1. 登录 Grafana
2. 点击 "+" → "Import"
3. 上传 `grafana/dashboards/*.json` 文件
4. 选择 Prometheus 数据源

### 预配置仪表板

1. **System Overview**: 系统整体状态
2. **Application Performance**: 应用性能监控
3. **Database Monitoring**: 数据库监控
4. **Business Metrics**: 业务指标
5. **Alert History**: 告警历史

### 创建自定义仪表板

```json
{
  "dashboard": {
    "title": "UAV Platform Custom Dashboard",
    "panels": [
      {
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "cpu_usage_percent",
            "legendFormat": "CPU {{instance}}"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{job}}"
          }
        ]
      }
    ]
  }
}
```

---

## 📋 ELK Stack 日志聚合

### Elasticsearch 索引

日志自动按以下方式索引：

```
uav-logs-YYYY.MM.DD          # 普通日志
uav-logs-error-YYYY.MM.DD    # 错误日志
uav-metrics-YYYY.MM.DD       # 性能指标
```

### Kibana 使用

#### 1. 创建索引模式

1. 进入 Kibana → Management → Index Patterns
2. 创建 `uav-logs-*` 索引模式
3. 设置 `@timestamp` 为时间字段

#### 2. 常用查询

```kibana
# 搜索错误日志
level:ERROR

# 搜索特定应用日志
logger_name:com.uav.platform

# 搜索用户操作
message:*login*

# 组合查询
level:ERROR AND logger_name:com.uav.auth

# 时间范围过滤
@timestamp:[now-1h TO now]
```

#### 3. 可视化

创建以下可视化：
- 错误率时间序列
- 日志级别分布饼图
- Top 10 错误
- 请求延迟热图

### Logstash 管道

日志处理流程：

```
Filebeat/Application → Logstash → Elasticsearch → Kibana
```

自定义处理规则在 `logstash/pipeline/logstash.conf` 中配置。

---

## 🔔 Alertmanager 告警

### 告警流程

```
Prometheus → Alertmanager → Slack/Email/PagerDuty
            ↓
         Webhook
            ↓
      Alert Webhook App → Slack
```

### 配置通知渠道

#### Slack

1. 创建 Slack App
2. 启用 Incoming Webhooks
3. 获取 Webhook URL
4. 配置环境变量 `SLACK_WEBHOOK_URL`

#### Email

在 `alertmanager.yml` 中配置 SMTP：

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@example.com'
  smtp_auth_username: 'alerts@example.com'
  smtp_auth_password: 'your-password'
```

#### PagerDuty

添加 PagerDuty 接收器：

```yaml
- name: 'pagerduty'
  pagerduty_configs:
    - service_key: 'YOUR_PAGERDUTY_KEY'
      severity: critical
```

### 告警抑制

防止告警风暴：
- 相同告警合并
- 抑制低优先级告警
- 重复间隔控制

---

## 🔍 Jaeger 链路追踪

### 配置应用

在 Spring Boot 应用中添加：

```yaml
spring:
  opentracing:
    enabled: true
  jaeger:
    endpoint: http://jaeger:14268/api/traces
```

在 Python 应用中：

```python
from jaeger_client import Config
config = Config(
    config={
        'sampler': {'type': 'const', 'param': 1},
        'local_agent_sample_server': 'jaeger:6831'
    },
    service_name='my-service'
)
tracer = config.initialize_tracer()
```

### 查看链路

1. 访问 http://localhost:16686
2. 选择服务
3. 查看分布式追踪

---

## 📊 性能基准

### 性能目标

| 指标 | 目标值 | 告警阈值 |
|------|--------|---------|
| API响应时间 (P95) | < 200ms | > 2s |
| API响应时间 (P99) | < 500ms | > 5s |
| 错误率 | < 0.1% | > 5% |
| 可用性 | > 99.9% | < 99% |
| CPU使用率 | < 70% | > 80% |
| 内存使用率 | < 80% | > 85% |

### 容量规划

根据当前负载：

- **CPU**: 每100 RPS需要约1核
- **内存**: 每100 RPS需要约512MB
- **磁盘**: 日志保留30天约需50GB

---

## 🛠 故障排查

### Prometheus 不工作

```bash
# 检查 Prometheus 日志
docker-compose logs prometheus

# 检查目标状态
curl http://localhost:9090/api/v1/targets

# 手动触发告警
curl -X POST http://localhost:9093/-/reload
```

### Elasticsearch 不工作

```bash
# 检查健康状态
curl http://localhost:9200/_cluster/health

# 检查索引
curl http://localhost:9200/_cat/indices

# 查看磁盘使用
curl http://localhost:9200/_cat/allocation
```

### Alertmanager 不工作

```bash
# 查看告警状态
curl http://localhost:9093/api/v1/alerts

# 测试 Webhook
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{"alerts": [{"status": "firing", "labels": {"severity": "critical"}}]}'
```

---

## 📚 资源

### 文档链接

- Prometheus: https://prometheus.io/docs/
- Grafana: https://grafana.com/docs/
- Elasticsearch: https://www.elastic.co/guide/
- Kibana: https://www.elastic.co/guide/kibana/
- Alertmanager: https://prometheus.io/docs/alerting/latest/alertmanager/
- Jaeger: https://www.jaegertracing.io/docs/

### 社区

- Prometheus 社区: https://prometheus.io/community/
- Grafana 社区: https://community.grafana.com/
- ELK 社区: https://discuss.elastic.co/

---

## 🔐 安全建议

### 网络安全

1. **限制访问**
   - 仅在需要时暴露端口
   - 使用防火墙规则
   - 启用 HTTPS

2. **认证**
   - 更改默认密码
   - 使用强密码
   - 启用 RBAC

### 数据安全

1. **日志脱敏**
   - 移除敏感信息
   - 加密传输
   - 安全存储

2. **备份**
   - 定期备份 Elasticsearch 数据
   - 备份 Prometheus 数据
   - 测试恢复流程

---

## 📞 支持

如有问题，请查看：
- 项目 Wiki: https://wiki.example.com
- 故障排查指南: `docs/TROUBLESHOOTING.md`
- 联系: support@example.com


---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
