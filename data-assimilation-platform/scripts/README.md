# Data Assimilation Scripts

## 📋 概述

数据同化平台专用脚本，包含部署、测试、数据处理等工具脚本。

**最后更新**: 2026-05-08

---

## 📁 脚本分类

### 🚀 部署脚本

| 脚本 | 功能 |
|------|------|
| `deploy_dev.sh` | 开发环境部署 |
| `deploy_prod.sh` | 生产环境部署 |
| `rollback.sh` | 回滚脚本 |

### 🧪 测试脚本

| 脚本 | 功能 |
|------|------|
| `run_tests.sh` | 运行所有测试 |
| `run_benchmark.sh` | 运行性能测试 |
| `check_coverage.sh` | 检查测试覆盖率 |

### 🔧 工具脚本

| 脚本 | 功能 |
|------|------|
| `init_db.sh` | 初始化数据库 |
| `backup_db.sh` | 数据库备份 |
| `generate_data.py` | 生成测试数据 |

---

## 🚀 使用方法

### 部署

```bash
cd scripts

# 开发环境部署
./deploy_dev.sh

# 生产环境部署
./deploy_prod.sh --env=production
```

### 测试

```bash
# 运行所有测试
./run_tests.sh

# 运行性能测试
./run_benchmark.sh --iterations=100

# 检查覆盖率
./check_coverage.sh --min=80
```

### 数据库

```bash
# 初始化数据库
./init_db.sh --host=localhost --db=uav_assimilation

# 备份数据库
./backup_db.sh --output=./backups/
```

---

## 📋 前置条件

- Docker
- Kubernetes (生产环境)
- Python 3.8+
- MySQL Client

---

**最后更新**: 2026-05-08
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
