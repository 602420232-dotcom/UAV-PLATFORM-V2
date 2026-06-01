# 生产环境配置指南

## 🚀 重要安全配置

本指南说明了如何为生产环境配置关键的安全凭证。

---

## 1. JWT密钥配置

### 重要性
- JWT密钥用于签名和验证JSON Web Tokens
- 密钥必须足够强（至少32字符）
- 生产环境绝对不能使用默认密钥或空密钥

### 配置方法

#### Spring Boot应用
在 `application-prod.yml` 或环境变量中配置：

```yaml
uav:
  jwt:
    enabled: true
    secret: ${JWT_SECRET}  # 必需：至少32字符的强密钥
    expiration: 86400000   # 24小时过期（毫秒）
```

#### 环境变量（推荐）
```bash
# 生成强密钥
export JWT_SECRET=$(openssl rand -base64 32)

# 或使用Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 密钥生成示例

```python
import secrets

# 生成32字符的URL安全密钥
jwt_secret = secrets.token_urlsafe(32)
print(jwt_secret)
# 输出示例: xK9mP2vL8nQ5rT7wY3zA1bC4dE6fG0hJ

# 生成64字符的更安全密钥
jwt_secret = secrets.token_urlsafe(64)
```

---

## 2. 数据库密码配置

### 重要性
- 数据库密码保护所有业务数据
- 必须使用强密码（包含大小写字母、数字、特殊字符）
- 绝对不能在代码中硬编码密码

### 配置方法

#### Spring Boot应用
```yaml
spring:
  datasource:
    url: jdbc:mysql://${DB_HOST}:${DB_PORT}/${DB_NAME}?useSSL=true
    username: ${DB_USERNAME}
    password: ${DB_PASSWORD}  # 必需：强密码
```

#### Docker Compose
```yaml
services:
  mysql:
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}  # 必需
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}            # 必需
    ports:
      - "${DB_PORT}:3306"
```

#### Kubernetes Secret
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secrets
type: Opaque
stringData:
  db-password: ${DB_PASSWORD}
  db-root-password: ${MYSQL_ROOT_PASSWORD}
```

### 密码生成示例

```python
import secrets
import string

# 生成16字符的强密码
alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
password = ''.join(secrets.choice(alphabet) for i in range(16))
print(password)
# 输出示例: K9mP2vL8nQ5rT7w

# 生成32字符的更安全密码
password = secrets.token_urlsafe(24)  # 生成24字节 = 32字符
print(password)
```

---

## 3. Redis密码配置

### 配置方法

#### Spring Boot应用
```yaml
spring:
  redis:
    host: ${REDIS_HOST}
    port: ${REDIS_PORT}
    password: ${REDIS_PASSWORD}  # 推荐：设置密码
    ssl: true  # 生产环境建议启用SSL
```

#### Docker Compose
```yaml
services:
  redis:
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "${REDIS_PORT}:6379"
```

---

## 4. 环境变量配置脚本

### Linux/macOS (.env文件)

```bash
# .env.production
# =================

# JWT配置
JWT_SECRET=xK9mP2vL8nQ5rT7wY3zA1bC4dE6fG0hJ

# 数据库配置
DB_HOST=prod-db.example.com
DB_PORT=3306
DB_NAME=uav_platform
DB_USERNAME=uav_app
DB_PASSWORD=K9mP2vL8nQ5rT7wY3zA1b

# Redis配置
REDIS_HOST=prod-redis.example.com
REDIS_PORT=6379
REDIS_PASSWORD=A1b2C3d4E5f6G7h8

# 天气API密钥
WEATHER_API_KEY=wx_a1b2c3d4e5f6g7h8i9j0
```

### Windows (PowerShell)

```powershell
# 设置环境变量
$env:JWT_SECRET = "xK9mP2vL8nQ5rT7wY3zA1bC4dE6fG0hJ"
$env:DB_PASSWORD = "K9mP2vL8nQ5rT7wY3zA1b"

# 持久化环境变量
[System.Environment]::SetEnvironmentVariable("JWT_SECRET", "xK9mP2vL8nQ5rT7wY3zA1bC4dE6fG0hJ", [System.EnvironmentVariableTarget]::Machine)
```

---

## 5. Kubernetes配置

### Secret对象

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: uav-secrets
  namespace: production
type: Opaque
stringData:
  # Base64编码的值（在生产中应使用加密）
  jwt-secret: eEs5bVAycjhOZVE3d1kzQTF3YkM0ZEU2ZjBHMGhK
  db-password: SzltUDJ2TDhOcVE1clQ3d1kzemExYg==
  redis-password: QTF6YjJDM2Q0RTVmNkc3aDg=
```

### ConfigMap对象

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: uav-config
  namespace: production
data:
  DB_HOST: "prod-db.example.com"
  DB_PORT: "3306"
  DB_NAME: "uav_platform"
  REDIS_HOST: "prod-redis.example.com"
  REDIS_PORT: "6379"
```

---

## 6. Docker配置

### docker-compose.prod.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    environment:
      - SPRING_PROFILES_ACTIVE=prod
      - JWT_SECRET=${JWT_SECRET}
      - DB_HOST=${DB_HOST}
      - DB_PORT=${DB_PORT}
      - DB_NAME=${DB_NAME}
      - DB_USERNAME=${DB_USERNAME}
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_HOST=${REDIS_HOST}
      - REDIS_PORT=${REDIS_PORT}
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    secrets:
      - db_password
      - jwt_secret

secrets:
  db_password:
    file: ./secrets/db_password.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt
```

### .dockerignore

```bash
# 排除敏感文件
.env*
*.pem
*.key
secrets/
```

---

## 7. 自动化配置脚本

### 生成所有密钥的脚本

```python
#!/usr/bin/env python3
"""
Production Secrets Generator
自动生成生产环境所需的全部密钥
"""

import secrets
import string
import json
from datetime import datetime

def generate_strong_password(length=32):
    """生成强密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_jwt_secret():
    """生成JWT密钥（至少32字符）"""
    return secrets.token_urlsafe(48)  # 48字节 = 64字符

def generate_api_key():
    """生成API密钥"""
    return f"uav_{secrets.token_urlsafe(32)}"

def main():
    print("=" * 60)
    print("Production Secrets Generator")
    print("=" * 60)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    secrets_dict = {
        "JWT_SECRET": generate_jwt_secret(),
        "DB_PASSWORD": generate_strong_password(32),
        "DB_ROOT_PASSWORD": generate_strong_password(48),
        "REDIS_PASSWORD": generate_strong_password(24),
        "WEATHER_API_KEY": generate_api_key(),
    }
    
    # 输出到终端
    print("Generated Secrets:")
    print("-" * 60)
    for key, value in secrets_dict.items():
        print(f"{key}:")
        print(f"  {value}\n")
    
    # 保存到JSON文件（仅用于演示，实际生产中不要保存）
    output_file = "generated_secrets.json"
    with open(output_file, 'w') as f:
        json.dump(secrets_dict, f, indent=2)
    
    print(f"Secrets saved to: {output_file}")
    print("\n⚠️  警告: 请立即将这些密钥配置到生产环境，")
    print("   然后删除此文件和生成的JSON文件！")
    print("=" * 60)

if __name__ == '__main__':
    main()
```

### 运行密钥生成器

```bash
cd scripts
python generate_secrets.py

# 输出示例:
# ============================================================
# Production Secrets Generator
# ============================================================
# Generated: 2026-05-08 13:30:00
# 
# Generated Secrets:
# ------------------------------------------------------------
# JWT_SECRET:
#   xK9mP2vL8nQ5rT7wY3zA1bC4dE6fG0hJ2kL4mN6oP8qR0sT2
# 
# DB_PASSWORD:
#   K9mP2vL8nQ5rT7wY3zA1bC4dE6fG0hJ
# 
# ...
```

---

## 8. 安全最佳实践

### ✅ 应该做的

1. **使用环境变量**
   - 所有敏感配置通过环境变量注入
   - 永不将密钥提交到代码仓库

2. **定期轮换密钥**
   - 建议每90天更换一次JWT密钥
   - 数据库密码每60天更换一次

3. **使用密钥管理服务**
   - AWS Secrets Manager
   - Azure Key Vault
   - HashiCorp Vault
   - Kubernetes Secrets

4. **启用审计日志**
   - 记录所有密钥访问
   - 监控异常访问模式

### ❌ 不应该做的

1. **不要硬编码密钥**
   ```python
   # ❌ 错误
   password = "admin123"
   
   # ✅ 正确
   password = os.getenv("DB_PASSWORD")
   ```

2. **不要将密钥提交到Git**
   ```bash
   # .gitignore
   .env
   *.pem
   secrets/
   ```

3. **不要在日志中打印密钥**
   ```python
   # ❌ 错误
   logger.info(f"Password: {password}")
   
   # ✅ 正确
   logger.info("Password configured: ***")
   ```

4. **不要使用弱密钥**
   ```python
   # ❌ 错误
   secret = "123456"
   
   # ✅ 正确
   secret = secrets.token_urlsafe(32)
   ```

---

## 9. 验证配置

### 检查脚本

```python
#!/usr/bin/env python3
"""
Verify Production Configuration
验证生产环境配置是否正确
"""

import os
import re

def check_jwt_secret():
    """检查JWT密钥"""
    secret = os.getenv("JWT_SECRET")
    
    if not secret:
        return False, "JWT_SECRET not set"
    
    if len(secret) < 32:
        return False, f"JWT_SECRET too short: {len(secret)} chars (min: 32)"
    
    return True, "JWT_SECRET configured"

def check_db_password():
    """检查数据库密码"""
    password = os.getenv("DB_PASSWORD")
    
    if not password:
        return False, "DB_PASSWORD not set"
    
    if len(password) < 12:
        return False, f"DB_PASSWORD too short: {len(password)} chars (min: 12)"
    
    return True, "DB_PASSWORD configured"

def check_all():
    """检查所有配置"""
    checks = [
        ("JWT Secret", check_jwt_secret),
        ("Database Password", check_db_password),
    ]
    
    print("=" * 60)
    print("Production Configuration Verification")
    print("=" * 60)
    
    all_passed = True
    for name, check_func in checks:
        passed, message = check_func()
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {message}")
        
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("✅ All checks passed!")
    else:
        print("❌ Some checks failed. Please fix before deployment.")
    
    return all_passed

if __name__ == '__main__':
    check_all()
```

---

## 10. 快速参考

### 必需的环境变量

```bash
# JWT配置
JWT_SECRET=<至少32字符的强密钥>

# 数据库配置
DB_HOST=<数据库主机>
DB_PORT=<数据库端口，默认3306>
DB_NAME=<数据库名称>
DB_USERNAME=<数据库用户名>
DB_PASSWORD=<数据库密码>

# Redis配置
REDIS_HOST=<Redis主机>
REDIS_PORT=<Redis端口，默认6379>
REDIS_PASSWORD=<Redis密码>

# 可选
WEATHER_API_KEY=<天气API密钥>
```

### 联系信息

如有问题，请查看:
- 项目文档: `docs/`
- 配置指南: `docs/CONFIGURATION_GUIDE.md`
- 安全报告: `docs/SECURITY_REPORT.md`

---

**生成时间**: 2026-05-08 13:30  
**版本**: 1.0.0  
**状态**: ✅ 完成
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
