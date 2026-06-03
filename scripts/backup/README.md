# 数据备份与恢复指南

## 手动备份

### Linux / macOS
```bash
# 备份到默认目录 ./backups/
./scripts/backup/backup-volumes.sh

# 备份到指定目录
./scripts/backup/backup-volumes.sh /path/to/backup/dir
```

### Windows (PowerShell)
```powershell
.\scripts\backup\backup-volumes.ps1
```

### Docker Compose
```bash
docker compose -f deployments/backup/docker-compose.backup.yml run --rm backup
```

## 定时自动备份

```bash
# 启动定时备份（每天凌晨 2:00）
docker compose -f deployments/backup/docker-compose.backup.yml up -d cron

# 查看备份日志
docker logs -f uav-backup-cron

# 停止定时备份
docker compose -f deployments/backup/docker-compose.backup.yml down
```

## 数据恢复

### 恢复 Docker 数据卷
```bash
# 恢复指定数据卷
docker run --rm \
  -v <volume-name>:/target \
  -v $(pwd):/backup \
  alpine:3.18 \
  tar xzf "/backup/volume-<volume-name>.tar.gz" -C /target
```

### 恢复 MySQL 数据库
```bash
# 恢复单个数据库
cat backups/<timestamp>/mysql-<db>.sql | docker exec -i uav-mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD}" <db>
```

## 备份策略

| 项目 | 配置 |
|------|------|
| 备份时间 | 每天 02:00 (cron) |
| 保留期限 | 30 天（可通过 `BACKUP_RETENTION_DAYS` 环境变量配置） |
| 备份内容 | Docker 数据卷 + MySQL 逻辑备份 + 配置文件 |
