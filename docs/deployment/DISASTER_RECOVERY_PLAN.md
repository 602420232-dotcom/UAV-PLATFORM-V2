# ============================================================
# 灾备与灾难恢复方案 (Disaster Recovery Plan)
# UAV Path Planning System v1.0
# ============================================================

## 1. 目标定义

| 指标 | 目标值 | 说明 |
|------|--------|------|
| **RTO** (恢复时间目标) | < 30 分钟 | 从故障发生到服务完全恢复 |
| **RPO** (恢复点目标) | < 1 小时 | 可容忍的最大数据丢失窗口 |
| **备份频率** | 每 24 小时（全量） | MySQL + Nacos 配置 |
| **备份保留** | 7 天本地 + 30 天异地 | 多级保留策略 |

## 2. 备份策略

### 2.1 数据库备份 (MySQL)
- **方式**: mysqldump --all-databases + gzip
- **调度**: K8s CronJob 每日 02:00 UTC
- **存储**: PersistentVolumeClaim (50Gi)
- **异地**: rsync 至异地 S3/MinIO 存储（每周）

### 2.2 配置备份 (Nacos)
- **方式**: Nacos API 导出全量配置
- **调度**: K8s CronJob 每日 03:00 UTC
- **格式**: JSON

### 2.3 容器镜像
- **方式**: GitHub Container Registry (ghcr.io)
- **策略**: 保留最后 10 个版本标签

## 3. 跨区域容灾部署

### 3.1 主区域 (Region-A)
- 全部微服务运行
- MySQL 主库 + Redis 主节点
- Nacos 集群 (3 节点)

### 3.2 灾备区域 (Region-B)
- 核心服务最小副本 (api-gateway, uav-platform)
- MySQL 只读副本 (异步复制)
- Nacos 单节点 (配置同步)

### 3.3 故障切换流程
1. 检测: Prometheus AlertManager 触发 PagerDuty
2. 决策: 值班 SRE 评估故障范围
3. 切换: `deployments/multi-region/deployer.py failover --target=region-b`
4. DNS: 更新 Route53/CloudDNS 指向 Region-B 负载均衡器
5. 验证: E2E 冒烟测试套件
6. 回切: 主区域恢复后数据反向同步并切回

## 4. 恢复流程

### 4.1 MySQL 恢复
```bash
kubectl exec -it deploy/mysql -- mysql -u root -p < /backup/mysql-YYYYMMDD.sql
# 或从 K8s CronJob 备份恢复
gunzip -c mysql-YYYYMMDD.sql.gz | kubectl exec -it deploy/mysql -- mysql -u root -p
```

### 4.2 Nacos 配置恢复
```bash
# 通过 Nacos API 导入配置
curl -X POST "http://nacos:8848/nacos/v1/cs/configs" \
  -d "dataId=application&group=DEFAULT_GROUP&content=$(cat config.yaml)"
```

### 4.3 K8s 集群恢复
```bash
# ArgoCD 自动同步 GitOps 仓库
argocd app sync uav-path-planning --prune
# 手动部署
kubectl apply -f deployments/kubernetes/ --recursive
```

## 5. 灾备演练计划

| 频率 | 演练内容 | 参与人 |
|------|----------|--------|
| **月度** | 数据库备份恢复验证 | DevOps |
| **季度** | 单服务故障转移 | SRE + DevOps |
| **半年** | 全区域切换 + 回切 | SRE + DevOps + QA |
| **年度** | 混沌工程全链路测试 | 全员 |

## 6. 监控与告警

- 备份失败 → Prometheus Alert → PagerDuty
- 备份存储使用率 > 80% → Warning
- 主从复制延迟 > 10s → Critical
- 异地备份未同步 > 48h → Warning
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
