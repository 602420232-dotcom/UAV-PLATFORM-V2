# 密钥轮换与安全加固指南

> **文档版本**: v1.0  
> **最后更新**: 2026-06-01  
> **适用组件**: 全系统安全配置  
> **安全等级**: Critical (P0)

---

## 目录

1. [概述](#1-概述)
2. [密钥类型与风险评估](#2-密钥类型与风险评估)
3. [密钥生成方法](#3-密钥生成方法)
4. [密钥轮换流程](#4-密钥轮换流程)
5. [配置管理](#5-配置管理)
6. [Git历史清理](#6-git历史清理)
7. [监控与告警](#7-监控与告警)
8. [应急响应](#8-应急响应)

---

## 1. 概述

### 1.1 背景

根据项目审计报告，以下密钥可能存在泄露风险：

| 密钥类型 | 风险等级 | 状态 |
|---------|---------|------|
| JWT_SECRET_KEY | Critical | ⚠️ 需轮换 |
| ENCRYPTION_KEY | Critical | ⚠️ 需轮换 |
| DB_PASSWORD | High | ⚠️ 需轮换 |
| API Keys | High | ⚠️ 需检查 |
| Grafana/ELK 密码 | Medium | ⚠️ 需配置Secrets |

### 1.2 轮换原则

| 原则 | 说明 |
|------|------|
| **定期轮换** | 生产环境建议每90天轮换一次 |
| **紧急轮换** | 发现泄露后立即轮换 |
| **零停机** | 使用热更新机制，无需重启服务 |
| **可追溯** | 记录所有密钥变更操作 |

---

## 2. 密钥类型与风险评估

### 2.1 系统密钥

| 密钥名称 | 用途 | 位置 | 风险 |
|---------|------|------|------|
| JWT_SECRET_KEY | JWT Token 签名 | `.env` | Critical |
| ENCRYPTION_KEY | 数据加密 | `.env` | Critical |
| OAUTH2_CLIENT_SECRET | OAuth2客户端 | `.env` | High |

### 2.2 数据库密钥

| 密钥名称 | 用途 | 位置 | 风险 |
|---------|------|------|------|
| DB_PASSWORD | MySQL root | `.env` | Critical |
| DB_PASSWORD | 应用数据库用户 | `.env` | High |
| REDIS_PASSWORD | Redis认证 | `.env` | Medium |

### 2.3 第三方服务密钥

| 密钥名称 | 用途 | 位置 | 风险 |
|---------|------|------|------|
| Cesium Token | 地图服务 | `.env` | Medium |
| HuggingFace Token | 模型下载 | `.env` | Medium |
| FENGWU_API_KEY | FengWu服务认证 | `.env` | High |

---

## 3. 密钥生成方法

### 3.1 强随机密钥

**使用 OpenSSL** (推荐):

```bash
# 生成 JWT 密钥 (至少 32 字符)
openssl rand -base64 32

# 生成加密密钥 (32 字符 = 256位)
openssl rand -base64 32

# 生成 64 字符超长密钥
openssl rand -base64 64
```

**使用 Python**:

```python
import secrets
import base64

# JWT 密钥
jwt_secret = base64.b64encode(secrets.token_bytes(32)).decode()
print(f"JWT_SECRET_KEY={jwt_secret}")

# 加密密钥
encryption_key = base64.b64encode(secrets.token_bytes(32)).decode()
print(f"ENCRYPTION_KEY={encryption_key}")
```

**使用 PowerShell** (Windows):

```powershell
# 生成 32 字符密钥
$key = [Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
Write-Host "Generated Key: $key"
```

### 3.2 数据库密码

```bash
# 使用 pwgen (Linux/macOS)
pwgen -s 32 1

# 或使用随机字符串
openssl rand -base64 24
```

### 3.3 API Keys

**FengWu API Key**:

```bash
# 生成安全的 API Key
openssl rand -hex 32
# 输出: a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd
```

---

## 4. 密钥轮换流程

### 4.1 轮换前准备

1. **备份当前密钥**
   ```bash
   # 备份 .env 文件
   cp .env .env.backup.$(date +%Y%m%d)
   
   # 备份到安全的密钥保管库
   aws secretsmanager create-secret --name uav/jwt-secret --secret-string "$(cat .env | grep JWT_SECRET)"
   ```

2. **通知相关团队**
   - 告知密钥轮换计划
   - 确认维护窗口时间
   - 准备回滚方案

3. **准备新密钥**
   ```bash
   # 生成新密钥
   NEW_JWT_SECRET=$(openssl rand -base64 32)
   NEW_ENCRYPTION_KEY=$(openssl rand -base64 32)
   NEW_DB_PASSWORD=$(openssl rand -base64 24)
   ```

### 4.2 JWT 密钥轮换

#### 步骤 1: 更新配置文件

```bash
# 编辑 .env 文件
nano .env

# 修改 JWT_SECRET_KEY
JWT_SECRET_KEY=新的base64编码密钥

# 同时更新 JWT_REFRESH_SECRET (可选)
JWT_REFRESH_SECRET=新的base64编码刷新密钥
```

#### 步骤 2: 重启服务

```bash
# Docker Compose
docker-compose restart backend-spring
docker-compose restart uav-platform-service

# 或 Kubernetes
kubectl rollout restart deployment/backend-spring
```

#### 步骤 3: 验证

```bash
# 测试新密钥是否生效
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 检查日志无错误
docker-compose logs -f backend-spring | grep -i "jwt\|secret"
```

### 4.3 数据库密码轮换

#### 步骤 1: MySQL 密码更新

```sql
-- 连接 MySQL
mysql -u root -p

-- 修改 root 密码
ALTER USER 'root'@'localhost' IDENTIFIED BY 'new_secure_password';
FLUSH PRIVILEGES;

-- 修改应用用户密码
ALTER USER 'uav_user'@'%' IDENTIFIED BY 'new_secure_password';
FLUSH PRIVILEGES;
```

#### 步骤 2: 更新配置

```bash
# 更新 .env 文件
DB_PASSWORD=new_secure_password

# 重启服务
docker-compose restart mysql
docker-compose restart uav-platform-service
```

#### 步骤 3: 验证连接

```bash
# 测试数据库连接
docker-compose exec uav-platform-service mysql -h mysql -u uav_user -p

# 检查应用日志
docker-compose logs -f uav-platform-service | grep -i "mysql\|database"
```

### 4.4 加密密钥轮换

**警告**: 加密密钥轮换会导致已加密数据无法解密！

#### 需要解密所有数据 (推荐方案):

```python
# decrypt_data.py
import base64
from cryptography.fernet import Fernet

# 使用旧密钥解密
old_key = base64.b64decode(OLD_ENCRYPTION_KEY)
fernet_old = Fernet(base64.b64encode(old_key[:32]))

# 使用新密钥重新加密
new_key = base64.b64decode(NEW_ENCRYPTION_KEY)
fernet_new = Fernet(base64.b64encode(new_key[:32]))

# 遍历数据库中的加密字段
for row in db.query("SELECT id, encrypted_data FROM sensitive_table"):
    decrypted = fernet_old.decrypt(row.encrypted_data)
    encrypted = fernet_new.encrypt(decrypted)
    db.update("UPDATE sensitive_table SET encrypted_data = ? WHERE id = ?", 
               encrypted, row.id)
```

#### 或使用双密钥方案 (无需解密):

```yaml
# application.yml
encryption:
  primary-key: ${NEW_ENCRYPTION_KEY}
  legacy-keys:
    - ${OLD_ENCRYPTION_KEY_1}
    - ${OLD_ENCRYPTION_KEY_2}
```

---

## 5. 配置管理

### 5.1 环境变量管理

**开发环境** (`.env.development`):
```bash
JWT_SECRET_KEY=dev-secret-key-not-for-production
ENCRYPTION_KEY=dev-encryption-key-not-for-production
DB_PASSWORD=dev_password
```

**生产环境** (`.env.production`):
```bash
# 生产密钥必须通过安全渠道获取
# 建议使用密钥管理服务 (KMS)
JWT_SECRET_KEY=${JWT_SECRET_KEY_PROD}
ENCRYPTION_KEY=${ENCRYPTION_KEY_PROD}
DB_PASSWORD=${DB_PASSWORD_PROD}
```

### 5.2 Docker Secrets (Swarm)

```yaml
# docker-compose.yml
services:
  backend:
    image: uav-backend:latest
    secrets:
      - jwt_secret
      - db_password
    environment:
      - JWT_SECRET_KEY_FILE=/run/secrets/jwt_secret
      - DB_PASSWORD_FILE=/run/secrets/db_password

secrets:
  jwt_secret:
    file: ./secrets/jwt_secret.txt
  db_password:
    file: ./secrets/db_password.txt
```

### 5.3 Kubernetes Secrets

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: uav-secrets
  namespace: uav-platform
type: Opaque
stringData:
  JWT_SECRET_KEY: "your-jwt-secret-key-here"
  ENCRYPTION_KEY: "your-encryption-key-here"
  DB_PASSWORD: "your-database-password"
---
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: uav-backend
spec:
  template:
    spec:
      containers:
      - name: backend
        envFrom:
        - secretRef:
            name: uav-secrets
```

### 5.4 HashiCorp Vault 集成

```bash
# 启动 Vault
vault server -dev

# 存储密钥
vault kv put secret/uav/jwt key="$(openssl rand -base64 32)"
vault kv put secret/uav/db password="secure-db-password"

# 应用配置
export JWT_SECRET_KEY=$(vault kv get -field=key secret/uav/jwt)
export DB_PASSWORD=$(vault kv get -field=password secret/uav/db)
```

---

## 6. Git 历史清理

### 6.1 检查泄露

```bash
# 检查 Git 历史中的密钥
git log --all --source --remotes --grep="JWT_SECRET" --oneline
git log --all --source --remotes --grep="DB_PASSWORD" --oneline
git log --all --source --remotes --grep="ENCRYPTION_KEY" --oneline

# 使用 gitrob 或 gitleaks
docker run -it --rm wwseclabs/gitleaks:latest --repo-path .
```

### 6.2 清理策略

#### BFG Repo-Cleaner (推荐)

```bash
# 安装 BFG
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar

# 清理敏感文件
java -jar bfg.jar --delete-files ".env" --repo .
java -jar bfg.jar --delete-files "*.pem" --repo .
java -jar bfg.jar --replace-text passwords.txt --repo .

# 清理敏感内容
java -jar bfg.jar --replace-text secret-replacement.txt --repo .

# 推送清理后的历史
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push --force --all
```

#### git-filter-branch

```bash
# 删除特定提交中的文件
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env' \
  --prune-empty --tag-name-filter cat -- --all

# 推送
git push origin --force --all
git push origin --force --tags
```

### 6.3 后续措施

1. **通知团队**: 告知仓库历史已清理
2. **更新本地副本**: 
   ```bash
   git fetch origin
   git reset --hard origin/main
   ```
3. **强化 .gitignore**:
   ```gitignore
   # 环境文件
   .env
   .env.local
   .env.*.local
   
   # 密钥文件
   *.pem
   *.key
   secrets/
   credentials/
   ```

---

## 7. 监控与告警

### 7.1 密钥使用监控

**JWT 密钥验证失败监控**:

```yaml
# Prometheus 告警规则
groups:
- name: authentication
  rules:
  - alert: HighJWTFailureRate
    expr: |
      rate(auth_jwt_validation_errors_total[5m]) / 
      rate(auth_jwt_validations_total[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High JWT validation failure rate"
      description: "JWT validation failures exceed 10%"

  - alert: SecretKeyRotationDue
    expr: |
      time() - auth_last_secret_rotation_timestamp_seconds > 90 * 24 * 3600
    labels:
      severity: warning
    annotations:
      summary: "Secret key rotation due"
      description: "No secret key rotation in the last 90 days"
```

### 7.2 数据库访问监控

```sql
-- MySQL 审计查询
SELECT 
  user,
  host,
  command,
  argument,
  start_time
FROM mysql.general_log
WHERE command_type = 'Connect'
  AND argument LIKE '%failed%'
ORDER BY event_time DESC
LIMIT 100;
```

### 7.3 日志聚合

```yaml
# Fluentd 配置
<filter uav-backend>
  @type grep
  <exclude>
    key message
    pattern (JWT_SECRET|DB_PASSWORD|ENCRYPTION_KEY)
  </exclude>
</filter>

<filter uav-backend>
  @type prometheus
  <counter>
    facet level
    facet service
  </counter>
</filter>
```

---

## 8. 应急响应

### 8.1 密钥泄露响应流程

```
发现泄露 (1小时内)
    ↓
启动应急响应团队
    ↓
立即轮换密钥 (4小时内)
    ↓
检查未授权访问
    ↓
修复漏洞
    ↓
加强监控
    ↓
事后复盘
```

### 8.2 紧急轮换脚本

```bash
#!/bin/bash
# emergency_key_rotation.sh

set -e

echo "⚠️  Emergency Key Rotation Script"
echo "=================================="

# 生成新密钥
NEW_JWT_SECRET=$(openssl rand -base64 32)
NEW_DB_PASSWORD=$(openssl rand -base64 24)

# 备份当前配置
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# 更新 .env 文件
sed -i "s/^JWT_SECRET_KEY=.*/JWT_SECRET_KEY=${NEW_JWT_SECRET}/" .env
sed -i "s/^DB_PASSWORD=.*/DB_PASSWORD=${NEW_DB_PASSWORD}/" .env

# 更新数据库密码
mysql -u root -p <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY '${NEW_DB_PASSWORD}';
FLUSH PRIVILEGES;
EOF

# 重启所有服务
docker-compose restart

# 验证服务健康
sleep 10
docker-compose ps

# 发送通知
echo "Key rotation completed at $(date)" | mail -s "UAV System: Emergency Key Rotation" admin@company.com

echo "✅ Emergency key rotation completed"
```

### 8.3 泄露后检查清单

| 检查项 | 说明 | 状态 |
|--------|------|------|
| 撤销所有活跃会话 | 使所有当前 Token 失效 | ☐ |
| 轮换所有密钥 | 包括 JWT、数据库、API Keys | ☐ |
| 检查异常登录 | 查看是否有未授权访问 | ☐ |
| 检查数据泄露 | 查看敏感数据是否被访问 | ☐ |
| 修复漏洞 | 找出并修复密钥泄露路径 | ☐ |
| 更新监控 | 添加更强的异常检测 | ☐ |
| 安全培训 | 强化团队安全意识 | ☐ |

---

## 附录 A: 密钥清单模板

| 密钥名称 | 用途 | 轮换周期 | 最后轮换日期 | 负责人 | 备注 |
|---------|------|---------|-------------|--------|------|
| JWT_SECRET_KEY | JWT签名 | 90天 | - | - | - |
| JWT_REFRESH_SECRET | Refresh Token | 90天 | - | - | - |
| ENCRYPTION_KEY | 数据加密 | 180天 | - | - | 高风险 |
| DB_PASSWORD | MySQL | 90天 | - | - | - |
| REDIS_PASSWORD | Redis | 180天 | - | - | - |
| FENGWU_API_KEY | 服务认证 | 180天 | - | - | - |
| CESIUM_TOKEN | 地图服务 | 365天 | - | - | - |

---

## 附录 B: 相关工具

| 工具名称 | 用途 | 链接 |
|---------|------|------|
| HashiCorp Vault | 密钥管理 | https://www.vaultproject.io/ |
| AWS Secrets Manager | AWS密钥管理 | https://aws.amazon.com/secrets-manager/ |
| Azure Key Vault | Azure密钥管理 | https://azure.microsoft.com/services/key-vault/ |
| Gitleaks | Git密钥扫描 | https://github.com/gitleaks/gitleaks |
| BFG Repo-Cleaner | Git历史清理 | https://rtyley.github.io/bfg-repo-cleaner/ |

---

## 附录 C: 密钥生成脚本

创建 `scripts/generate-secrets.sh`:

```bash
#!/bin/bash
# generate-secrets.sh - 生成安全的随机密钥

echo "Generating secure keys for UAV Platform..."
echo "=========================================="
echo ""

# JWT 密钥
JWT_SECRET=$(openssl rand -base64 32)
echo "JWT_SECRET_KEY=${JWT_SECRET}"

# 加密密钥
ENCRYPTION_SECRET=$(openssl rand -base64 32)
echo "ENCRYPTION_KEY=${ENCRYPTION_SECRET}"

# 数据库密码
DB_PASSWORD=$(openssl rand -base64 24)
echo "DB_PASSWORD=${DB_PASSWORD}"

# API Key
API_KEY=$(openssl rand -hex 32)
echo "FENGWU_API_KEY=${API_KEY}"

echo ""
echo "Copy these keys to your .env file and keep them secure!"
```

---

> **维护者**: UAV Platform Security Team  
> **文档版本**: 1.0  
> **创建日期**: 2026-05-31
> **下次审查**: 2026-08-31
