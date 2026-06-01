# Adminer 数据库管理指南

> **文档版本**: v1.0  
> **最后更新**: 2026-06-01  
> **适用组件**: Adminer (端口 8899)  
> **依赖服务**: MySQL (端口 3306)

---

## 目录

1. [概述](#1-概述)
2. [访问 Adminer](#2-访问-adminer)
3. [连接数据库](#3-连接数据库)
4. [数据库管理](#4-数据库管理)
5. [表操作](#5-表操作)
6. [数据管理](#6-数据管理)
7. [SQL 查询](#7-sql-查询)
8. [导入导出](#8-导入导出)
9. [用户权限](#9-用户权限)
10. [安全配置](#10-安全配置)
11. [常见问题](#11-常见问题)

---

## 1. 概述

### 1.1 什么是 Adminer

Adminer 是一个用 PHP 编写的轻量级数据库管理工具，比 phpMyAdmin 更简洁、更安全。

**优势**:
- 单文件部署 (约 500KB)
- 支持 MySQL、PostgreSQL、SQLite、MongoDB 等多种数据库
- 界面简洁、直观
- 安全性高

### 1.2 项目集成

本项目通过 Docker Compose 集成 Adminer：

```yaml
# docker-compose.yml
adminer:
  image: adminer:latest
  ports:
    - "8899:8080"
  environment:
    ADMINER_DESIGN: dracula
  depends_on:
    mysql:
      condition: service_healthy
```

---

## 2. 访问 Adminer

### 2.1 访问地址

**本地开发**: http://localhost:8899  
**Docker 环境**: http://localhost:8899  
**生产环境**: https://your-domain.com/adminer

### 2.2 Docker 启动

```bash
# 启动 Adminer
docker-compose up -d adminer

# 查看日志
docker-compose logs -f adminer

# 停止 Adminer
docker-compose stop adminer
```

### 2.3 访问流程

```
1. 打开浏览器访问 http://localhost:8899
2. 选择数据库类型: MySQL
3. 输入连接信息
4. 点击 "登录"
```

---

## 3. 连接数据库

### 3.1 默认连接信息

| 参数 | 值 |
|------|-----|
| **系统** | MySQL |
| **服务器** | mysql |
| **用户名** | root |
| **密码** | (见环境变量 MYSQL_ROOT_PASSWORD) |
| **数据库** | (留空显示所有数据库) |

### 3.2 各服务数据库

| 服务 | 数据库名 | 用途 |
|------|---------|------|
| **Platform Service** | uav_platform | 主平台数据 |
| **Meteor Forecaster** | meteor_forecast | 气象预测数据 |
| **Data Assimilation** | data_assimilation | 数据同化数据 |
| **Path Planning** | path_planning | 路径规划数据 |
| **WRF Processor** | wrf_processor | WRF 处理数据 |
| **Weather Collector** | uav_weather | 气象采集数据 |

### 3.3 Docker 网络连接

在 Docker 环境中:

- **服务器地址**: `mysql` (Docker 内部网络)
- **端口**: `3306`

从宿主机访问:

- **服务器地址**: `localhost`
- **端口**: `3306`

---

## 4. 数据库管理

### 4.1 查看所有数据库

登录后首页显示所有可用数据库:

```
┌─────────────────────────────────┐
│  Databases                      │
├─────────────────────────────────┤
│  information_schema            │
│  mysql                         │
│  performance_schema            │
│  uav_platform                  │
│  meteor_forecast               │
│  data_assimilation             │
│  path_planning                 │
│  wrf_processor                 │
│  uav_weather                   │
└─────────────────────────────────┘
```

### 4.2 创建新数据库

1. 点击左侧 "创建数据库"
2. 输入数据库名称: `new_database`
3. 选择字符集: `utf8mb4_unicode_ci`
4. 点击 "保存"

**SQL 等效**:
```sql
CREATE DATABASE new_database 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;
```

### 4.3 删除数据库

⚠️ **警告**: 删除数据库将永久丢失所有数据!

1. 选择要删除的数据库
2. 点击 "删除数据库"
3. 确认删除

**SQL 等效**:
```sql
DROP DATABASE database_name;
```

### 4.4 切换数据库

点击左侧菜单中的数据库名称即可切换。

---

## 5. 表操作

### 5.1 查看所有表

选择数据库后，右侧显示所有表:

```
┌──────────────────────────────────────┐
│  uav_platform (12 tables)            │
├──────────────────────────────────────┤
│  drones        │ 无人机信息表         │
│  tasks        │ 任务表               │
│  users        │ 用户表               │
│  roles        │ 角色表               │
│  permissions  │ 权限表               │
│  weather_data │ 气象数据表            │
└──────────────────────────────────────┘
```

### 5.2 创建新表

1. 点击 "创建表"
2. 填写表信息:

```
表名: drones
引擎: InnoDB
字符集: utf8mb4

字段:
┌──────────────┬────────────────┬────────────┐
│ 字段名       │ 类型           │ 主键/索引  │
├──────────────┼────────────────┼────────────┤
│ id           │ INT           │ PK, AI     │
│ name         │ VARCHAR(100)  │            │
│ model        │ VARCHAR(100)  │            │
│ status       │ ENUM          │            │
│ battery      │ INT           │            │
│ latitude     │ DECIMAL(10,7) │            │
│ longitude    │ DECIMAL(10,7) │            │
│ created_at   │ TIMESTAMP     │            │
└──────────────┴────────────────┴────────────┘
```

3. 点击 "保存"

**SQL 等效**:
```sql
CREATE TABLE drones (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  model VARCHAR(100),
  status ENUM('idle', 'flying', 'charging', 'maintenance') DEFAULT 'idle',
  battery INT DEFAULT 100,
  latitude DECIMAL(10, 7),
  longitude DECIMAL(10, 7),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 5.3 修改表结构

1. 选择表，点击 "结构"
2. 点击要修改的字段旁的 "更改"
3. 修改字段信息
4. 点击 "保存"

### 5.4 添加索引

1. 在 "结构" 页面
2. 滚动到 "索引" 部分
3. 添加索引:

```
索引名: idx_drones_status
类型: INDEX
字段: status
```

**SQL 等效**:
```sql
ALTER TABLE drones ADD INDEX idx_drones_status (status);
```

### 5.5 删除表

⚠️ **警告**: 删除表将永久丢失所有数据!

1. 选择表
2. 点击 "删除"
3. 确认删除

**SQL 等效**:
```sql
DROP TABLE table_name;
```

---

## 6. 数据管理

### 6.1 浏览数据

选择表后，点击 "选择" 查看所有数据:

```
┌─────────────────────────────────────────────────────────────┐
│ SELECT * FROM drones WHERE 1                                 │
├─────────────────────────────────────────────────────────────┤
│ id │ name      │ model        │ status   │ battery │ lat   │
├────┼───────────┼──────────────┼──────────┼─────────┼───────┤
│ 1  │ UAV-001   │ DJI-Matrice   │ idle     │ 95      │ 31.2  │
│ 2  │ UAV-002   │ DJI-Phantom   │ flying   │ 80      │ 31.3  │
│ 3  │ UAV-003   │ Parrot-Anafi  │ charging │ 45      │ 31.1  │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 添加数据

1. 点击 "新建"
2. 填写表单:

```
name: UAV-004
model: DJI-Matrice 300
status: idle
battery: 100
latitude: 31.2304
longitude: 121.4737
```

3. 点击 "保存"

**SQL 等效**:
```sql
INSERT INTO drones (name, model, status, battery, latitude, longitude)
VALUES ('UAV-004', 'DJI-Matrice 300', 'idle', 100, 31.2304, 121.4737);
```

### 6.3 编辑数据

1. 在数据列表中点击要编辑的行
2. 修改字段值
3. 点击 "保存"

**SQL 等效**:
```sql
UPDATE drones SET battery = 85 WHERE id = 1;
```

### 6.4 删除数据

⚠️ **警告**: 删除数据无法恢复!

1. 在数据列表中勾选要删除的行
2. 点击 "删除"
3. 确认删除

**SQL 等效**:
```sql
DELETE FROM drones WHERE id = 1;
```

### 6.5 批量操作

- **批量插入**: 粘贴多行 CSV 数据
- **批量更新**: 使用 UPDATE 语句
- **批量删除**: 选中多行后删除

---

## 7. SQL 查询

### 7.1 执行 SQL

1. 点击顶部 "SQL 命令"
2. 输入 SQL 语句:

```sql
-- 查询所有无人机
SELECT * FROM drones;

-- 查询正在飞行的无人机
SELECT * FROM drones WHERE status = 'flying';

-- 统计各状态无人机数量
SELECT status, COUNT(*) as count FROM drones GROUP BY status;
```

3. 点击 "执行"

### 7.2 常用查询示例

#### 查询无人机详情

```sql
SELECT 
  d.id,
  d.name,
  d.model,
  d.status,
  d.battery,
  CONCAT(d.latitude, ',', d.longitude) as location,
  t.name as current_task
FROM drones d
LEFT JOIN tasks t ON d.current_task_id = t.id
WHERE d.status = 'flying';
```

#### 查询任务列表

```sql
SELECT 
  t.id,
  t.name,
  t.type,
  t.priority,
  t.status,
  u.username as assigned_to,
  t.created_at
FROM tasks t
LEFT JOIN users u ON t.assigned_user_id = u.id
WHERE t.status IN ('pending', 'in_progress')
ORDER BY t.priority DESC, t.created_at ASC;
```

#### 气象数据统计

```sql
SELECT 
  DATE(observed_at) as date,
  AVG(temperature) as avg_temp,
  MAX(temperature) as max_temp,
  MIN(temperature) as min_temp,
  AVG(humidity) as avg_humidity,
  COUNT(*) as observations
FROM weather_data
WHERE observed_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY DATE(observed_at)
ORDER BY date DESC;
```

### 7.3 查询结果导出

1. 执行查询
2. 点击 "导出"
3. 选择格式 (CSV, SQL, XML, JSON)
4. 下载文件

---

## 8. 导入导出

### 8.1 导入数据

**从 SQL 文件导入**:

1. 点击顶部 "导入"
2. 选择 SQL 文件 (.sql)
3. 点击 "执行"

**从 CSV 导入**:

1. 点击 "导入"
2. 选择 CSV 文件
3. 配置选项:
   - 分隔符: `,`
   - 包围符: `"`
   - 转义符: `\`
   - 首行作为列名: ☑️

**SQL 等效**:
```sql
LOAD DATA INFILE '/path/to/file.csv'
INTO TABLE table_name
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
```

### 8.2 导出数据

**导出整个表**:

1. 选择表
2. 点击 "导出"
3. 选择格式和选项:
   - 格式: SQL / CSV / TSV
   - 包含: 结构 + 数据 / 仅结构 / 仅数据
   - 压缩: 无 / ZIP / GZIP
4. 点击 "导出"

**导出查询结果**:

1. 执行查询
2. 点击 "导出"
3. 选择格式
4. 下载文件

---

## 9. 用户权限

### 9.1 查看用户

```sql
SELECT user, host FROM mysql.user;
```

### 9.2 创建用户

```sql
-- 创建应用用户
CREATE USER 'uav_app'@'%' IDENTIFIED BY 'strong_password';

-- 授权
GRANT SELECT, INSERT, UPDATE, DELETE ON uav_platform.* TO 'uav_app'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON meteor_forecast.* TO 'uav_app'@'%';

-- 刷新权限
FLUSH PRIVILEGES;
```

### 9.3 修改密码

```sql
ALTER USER 'username'@'host' IDENTIFIED BY 'new_password';
FLUSH PRIVILEGES;
```

### 9.4 删除用户

```sql
DROP USER 'username'@'host';
FLUSH PRIVILEGES;
```

---

## 10. 安全配置

### 10.1 Docker 环境变量

```yaml
# docker-compose.yml
adminer:
  image: adminer:latest
  environment:
    ADMINER_DESIGN: dracula
    ADMINER_PLUGINS: ''
  ports:
    - "8899:8080"
  networks:
    - uav-network
  restart: unless-stopped
```

### 10.2 访问控制

**仅本地访问**:

```yaml
adminer:
  ports:
    - "127.0.0.1:8899:8080"
```

**使用反向代理 (Nginx)**:

```nginx
server {
    listen 443 ssl;
    server_name adminer.your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8899;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # 基础认证
    auth_basic "Adminer Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
}
```

### 10.3 定期备份

创建备份脚本:

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/mysql"
DB_HOST="mysql"
DB_USER="root"
DB_PASS="${MYSQL_ROOT_PASSWORD}"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份所有数据库
mysqldump -h $DB_HOST -u $DB_USER -p$DB_PASS --all-databases \
  | gzip > $BACKUP_DIR/all_dbs_$DATE.sql.gz

# 删除 7 天前的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

添加 cron 任务:

```bash
# 每天凌晨 2 点执行备份
0 2 * * * /scripts/backup.sh >> /var/log/backup.log 2>&1
```

---

## 11. 常见问题

### 11.1 连接失败

| 问题 | 解决方案 |
|------|---------|
| `Access denied` | 检查用户名密码 |
| `Can't connect to MySQL server` | 检查 MySQL 是否启动 |
| `Unknown MySQL server host` | 检查服务器地址是否正确 |

### 11.2 导入失败

| 问题 | 解决方案 |
|------|---------|
| 文件太大 | 增加 PHP 上传限制 |
| 编码问题 | 确保文件编码为 UTF-8 |
| 语法错误 | 检查 SQL 文件语法 |

### 11.3 性能问题

| 问题 | 解决方案 |
|------|---------|
| 查询慢 | 添加索引，使用 EXPLAIN 分析 |
| 页面加载慢 | 检查网络连接，减少大数据量查询 |

---

## 附录 A: 数据库表结构

### users 表

```sql
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  email VARCHAR(100),
  role VARCHAR(20) DEFAULT 'user',
  enabled BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### drones 表

```sql
CREATE TABLE drones (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  model VARCHAR(100),
  status ENUM('idle', 'flying', 'charging', 'maintenance') DEFAULT 'idle',
  battery INT DEFAULT 100,
  latitude DECIMAL(10, 7),
  longitude DECIMAL(10, 7),
  current_task_id INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (current_task_id) REFERENCES tasks(id)
);
```

### tasks 表

```sql
CREATE TABLE tasks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  type VARCHAR(50),
  priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
  status ENUM('pending', 'in_progress', 'completed', 'cancelled') DEFAULT 'pending',
  assigned_user_id INT,
  drone_id INT,
  start_lat DECIMAL(10, 7),
  start_lon DECIMAL(10, 7),
  end_lat DECIMAL(10, 7),
  end_lon DECIMAL(10, 7),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (assigned_user_id) REFERENCES users(id),
  FOREIGN KEY (drone_id) REFERENCES drones(id)
);
```

---

## 附录 B: 相关文档

- [Adminer 官方文档](https://www.adminer.org/)
- [MySQL 官方文档](https://dev.mysql.com/doc/)
- [Docker MySQL 镜像](https://hub.docker.com/_/mysql)

---

> **维护者**: UAV Platform Team  
> **文档版本**: 1.0  
> **创建日期**: 2026-05-31
