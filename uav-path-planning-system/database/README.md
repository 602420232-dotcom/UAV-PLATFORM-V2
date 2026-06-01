# Database - 数据库脚本

## 📋 概述

无人机路径规划系统的数据库脚本，包括初始化脚本、迁移脚本和备份。

**数据库**: MySQL 8.0+  
**最后更新**: 2026-05-08

---

## 📁 目录结构

```
database/
├── init.sql              # 数据库初始化脚本
├── migrations/           # 数据库迁移脚本
│   ├── V001__initial_schema.sql
│   ├── V002__add_user_roles.sql
│   └── V003__add_performance_indexes.sql
├── backups/            # 备份文件
│   ├── 2026-01-01/
│   └── 2026-05-08/
├── schema/            # 数据库Schema
│   ├── users.sql
│   ├── tasks.sql
│   └── drones.sql
└── README.md         # 本文档
```

---

## 🚀 快速开始

### 初始化数据库

```bash
# 连接到MySQL
mysql -h localhost -u root -p

# 创建数据库
CREATE DATABASE uav_platform;
USE uav_platform;

# 执行初始化脚本
SOURCE database/init.sql;
```

### 运行迁移

```bash
# 使用Flyway
mvn flyway:migrate

# 或手动执行
mysql -h localhost -u root -p uav_platform < database/migrations/V001__initial_schema.sql
```

---

## 📊 数据库Schema

### 主要表

| 表名 | 说明 | 主要字段 |
|------|------|---------|
| **users** | 用户表 | id, username, email, password_hash, role |
| **tasks** | 任务表 | id, name, status, created_at, user_id |
| **drones** | 无人机表 | id, name, status, position, capacity |
| **routes** | 路径表 | id, task_id, waypoints, distance |
| **weather_cache** | 气象缓存 | id, location, data, timestamp |

---

## 🔄 数据库迁移

### Flyway 配置

```yaml
# application.yml
spring:
  flyway:
    enabled: true
    locations: classpath:db/migration
    baseline-on-migrate: true
```

### 创建新迁移

```sql
-- V004__add_new_feature.sql
CREATE TABLE new_feature (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 💾 备份与恢复

### 备份

```bash
# 全量备份
mysqldump -h localhost -u root -p uav_platform > backup.sql

# 仅结构
mysqldump -h localhost -u root -p --no-data uav_platform > schema.sql

# 仅数据
mysqldump -h localhost -u root -p --no-create-info uav_platform > data.sql
```

### 恢复

```bash
# 从备份恢复
mysql -h localhost -u root -p uav_platform < backup.sql
```

---

## 🛡️ 安全配置

### 用户权限

```sql
-- 创建应用用户
CREATE USER 'uav_app'@'localhost' IDENTIFIED BY 'strong_password';

-- 授予最小权限
GRANT SELECT, INSERT, UPDATE, DELETE ON uav_platform.* TO 'uav_app'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;
```

### 密码策略

```sql
-- 设置密码策略
ALTER USER 'root'@'localhost' IDENTIFIED BY 'NewStrongPassword123!';
```

---

## 📈 性能优化

### 索引

```sql
-- 添加性能索引
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_drones_status ON drones(status);
```

### 查询优化

```sql
-- 分析查询性能
EXPLAIN SELECT * FROM tasks WHERE user_id = 1 AND status = 'active';

-- 优化建议
OPTIMIZE TABLE tasks;
```

---

## 🧪 测试数据库

### H2 内存数据库

```yaml
# test配置
spring:
  datasource:
    url: jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1
    driver-class-name: org.h2.Driver
  jpa:
    hibernate:
      ddl-auto: create-drop
```

---

## 📚 相关文档

- [MySQL 官方文档](https://dev.mysql.com/doc/)
- [Flyway 文档](https://flywaydb.org/documentation/)

---

**最后更新**: 2026-05-08
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
