# HashiCorp Vault 安装与配置指南

## 目录

- [1. 概述](#1-概述)
- [2. Vault 安装](#2-vault-安装)
- [3. Vault 初始化与解封](#3-vault-初始化与解封)
- [4. 密钥引擎配置](#4-密钥引擎配置)
- [5. 密钥路径规划](#5-密钥路径规划)
- [6. 访问策略配置](#6-访问策略配置)
- [7. 认证方法配置](#7-认证方法配置)
- [8. 与 Spring Boot 集成](#8-与-spring-boot-集成)
- [9. Kubernetes 集成](#9-kubernetes-集成)
- [10. 运维与监控](#10-运维与监控)
- [11. 故障排查](#11-故障排查)

---

## 1. 概述

本指南介绍如何在 UAV Platform V2 中部署和配置 HashiCorp Vault，用于集中管理敏感密钥（JWT_SECRET、DB_PASSWORD、REDIS_PASSWORD 等）。

### 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                      UAV Platform V2                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  API Gateway │  │  Services   │  │  VaultSecretProvider│  │
│  │  (SSL/TLS)   │  │  (mTLS)     │  │  (密钥缓存/回退)      │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                      │             │
│         └────────────────┼──────────────────────┘             │
│                          │                                    │
│  ┌───────────────────────┴──────────────────────────────┐     │
│  │              HashiCorp Vault Cluster                 │     │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │     │
│  │  │  Vault Node │  │  Vault Node │  │  Vault Node │  │     │
│  │  │   (Leader)  │  │  (Follower) │  │  (Follower) │  │     │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │     │
│  └──────────────────────────────────────────────────────┘     │
│                          │                                    │
│  ┌───────────────────────┴──────────────────────────────┐     │
│  │              后端存储 (Consul / Raft / PostgreSQL)    │     │
│  └──────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 环境规划

| 环境 | Vault 地址 | 存储后端 | 高可用 |
|------|-----------|---------|--------|
| dev | http://localhost:8200 | 文件 (dev mode) | 否 |
| staging | https://vault-staging.uav-platform.com | Raft | 3 节点 |
| production | https://vault.uav-platform.com | Raft | 5 节点 |

---

## 2. Vault 安装

### 2.1 使用 Docker 安装（开发环境）

```bash
# 创建 Vault 数据目录
mkdir -p ~/vault/data
mkdir -p ~/vault/config

# 创建 Vault 配置文件
cat > ~/vault/config/vault.hcl << 'EOF'
storage "file" {
  path = "/vault/data"
}

listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = "true"
}

api_addr = "http://127.0.0.1:8200"
ui = true
EOF

# 启动 Vault 容器
docker run -d \
  --name vault \
  --cap-add=IPC_LOCK \
  -p 8200:8200 \
  -v ~/vault/data:/vault/data \
  -v ~/vault/config:/vault/config \
  -e VAULT_ADDR='http://0.0.0.0:8200' \
  hashicorp/vault:1.18.0 server

# 查看日志
docker logs vault
```

### 2.2 使用二进制安装（生产环境）

```bash
# 下载 Vault
VAULT_VERSION="1.18.0"
wget https://releases.hashicorp.com/vault/${VAULT_VERSION}/vault_${VAULT_VERSION}_linux_amd64.zip
unzip vault_${VAULT_VERSION}_linux_amd64.zip
sudo mv vault /usr/local/bin/

# 验证安装
vault --version

# 创建 Vault 用户
sudo useradd --system --home /etc/vault --shell /bin/false vault

# 创建目录
sudo mkdir -p /etc/vault /var/lib/vault /var/log/vault
sudo chown -R vault:vault /etc/vault /var/lib/vault /var/log/vault
```

### 2.3 生产环境配置（Raft 后端 + TLS）

```bash
sudo tee /etc/vault/vault.hcl << 'EOF'
# 存储后端：Raft（集成式存储）
storage "raft" {
  path    = "/var/lib/vault"
  node_id = "vault-node-1"

  retry_leader_election = true
}

# 集群地址
cluster_addr = "https://10.0.0.1:8201"
api_addr     = "https://vault.uav-platform.com:8200"

# 监听器（HTTPS）
listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_cert_file = "/etc/vault/certs/server.crt"
  tls_key_file  = "/etc/vault/certs/server.key"
  tls_min_version = "tls12"
}

# 集群通信监听器
listener "tcp" {
  address       = "0.0.0.0:8201"
  tls_cert_file = "/etc/vault/certs/server.crt"
  tls_key_file  = "/etc/vault/certs/server.key"
  tls_min_version = "tls12"
}

# 启用 UI
ui = true

# 性能调优
disable_mlock = false
default_lease_ttl = "768h"
max_lease_ttl = "8760h"
EOF

# 创建 systemd 服务
sudo tee /etc/systemd/system/vault.service << 'EOF'
[Unit]
Description=HashiCorp Vault
Documentation=https://www.vaultproject.io/docs/
Requires=network-online.target
After=network-online.target

[Service]
User=vault
Group=vault
ProtectSystem=full
ProtectHome=read-only
PrivateTmp=yes
PrivateDevices=yes
SecureBits=keep-caps
AmbientCapabilities=CAP_IPC_LOCK
CapabilityBoundingSet=CAP_SYSLOG CAP_IPC_LOCK
NoNewPrivileges=yes
ExecStart=/usr/local/bin/vault server -config=/etc/vault/vault.hcl
ExecReload=/bin/kill --signal HUP $MAINPID
KillMode=process
KillSignal=SIGINT
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
StartLimitInterval=60
StartLimitBurst=3
LimitNOFILE=65536
LimitMEMLOCK=infinity

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable vault
sudo systemctl start vault
```

---

## 3. Vault 初始化与解封

### 3.1 初始化 Vault

```bash
export VAULT_ADDR='http://localhost:8200'

# 初始化（生成 5 个 unseal key 和 1 个 root token）
vault operator init -key-shares=5 -key-threshold=3

# 输出示例：
# Unseal Key 1: abcdef1234567890...
# Unseal Key 2: bcdef1234567890a...
# Unseal Key 3: cdef1234567890ab...
# Unseal Key 4: def1234567890abc...
# Unseal Key 5: ef1234567890abcd...
# Initial Root Token: hvs.XXXXXXXXXXXXXXXXXXXX

# 保存到安全位置！！！
# 建议使用 Shamir 秘密共享方案分发 unseal key
```

### 3.2 解封 Vault

```bash
# 需要至少 3 个 unseal key 来解封
vault operator unseal <Unseal Key 1>
vault operator unseal <Unseal Key 2>
vault operator unseal <Unseal Key 3>

# 检查状态
vault status

# 登录
vault login <Initial Root Token>
```

### 3.3 自动解封（可选）

```bash
# 配置自动解封（使用云 KMS，如 AWS KMS、Azure Key Vault、GCP CKM）
# 以 AWS KMS 为例：

vault write sys/config/auto-unseal \
  type=awskms \
  region=us-east-1 \
  kms_key_id=arn:aws:kms:us-east-1:123456789:key/abcd-1234-efgh-5678
```

---

## 4. 密钥引擎配置

### 4.1 启用 KV v2 密钥引擎

```bash
# 启用 KV v2 引擎（推荐用于 UAV Platform）
vault secrets enable -version=2 -path=secret kv-v2

# 或启用命名路径
vault secrets enable -version=2 -path=secret/uav-platform kv-v2
```

### 4.2 验证引擎状态

```bash
vault secrets list
vault secrets list -detailed
```

---

## 5. 密钥路径规划

### 5.1 密钥路径结构

```
secret/
└── uav-platform/
    ├── dev/
    │   ├── jwt
    │   ├── db
    │   ├── redis
    │   ├── kafka
    │   └── utm
    ├── staging/
    │   ├── jwt
    │   ├── db
    │   ├── redis
    │   ├── kafka
    │   └── utm
    └── prod/
        ├── jwt
        ├── db
        ├── redis
        ├── kafka
        └── utm
```

### 5.2 写入密钥

```bash
# 开发环境密钥
vault kv put secret/uav-platform/dev/jwt \
  JWT_SECRET="dev-jwt-secret-key-change-in-production" \
  JWT_EXPIRATION="86400000"

vault kv put secret/uav-platform/dev/db \
  DB_PASSWORD="dev_db_password" \
  DB_URL="jdbc:mysql://localhost:3306/uav_platform"

vault kv put secret/uav-platform/dev/redis \
  REDIS_PASSWORD="dev_redis_password" \
  REDIS_HOST="localhost" \
  REDIS_PORT="6379"

vault kv put secret/uav-platform/dev/kafka \
  KAFKA_PASSWORD="dev_kafka_password" \
  KAFKA_SASL_USERNAME="uav-platform"

vault kv put secret/uav-platform/dev/utm \
  UTM_SECRET="dev-utm-secret-key" \
  UTM_API_KEY="dev-utm-api-key"

# 生产环境密钥（使用更强的密码）
vault kv put secret/uav-platform/prod/jwt \
  JWT_SECRET="$(openssl rand -base64 64)" \
  JWT_EXPIRATION="3600000"

vault kv put secret/uav-platform/prod/db \
  DB_PASSWORD="$(openssl rand -base64 32)" \
  DB_URL="jdbc:mysql://prod-db.uav-platform.com:3306/uav_platform"

vault kv put secret/uav-platform/prod/redis \
  REDIS_PASSWORD="$(openssl rand -base64 32)" \
  REDIS_HOST="prod-redis.uav-platform.com"

vault kv put secret/uav-platform/prod/kafka \
  KAFKA_PASSWORD="$(openssl rand -base64 32)" \
  KAFKA_SASL_USERNAME="uav-platform-prod"

vault kv put secret/uav-platform/prod/utm \
  UTM_SECRET="$(openssl rand -base64 32)" \
  UTM_API_KEY="$(openssl rand -base64 32)"
```

### 5.3 读取密钥

```bash
# 读取密钥
vault kv get secret/uav-platform/dev/jwt
vault kv get -format=json secret/uav-platform/dev/jwt

# 读取特定字段
vault kv get -field=JWT_SECRET secret/uav-platform/dev/jwt

# 列出路径下的所有密钥
vault kv list secret/uav-platform/dev/
```

### 5.4 密钥版本管理

```bash
# 查看密钥版本历史
vault kv get -version=1 secret/uav-platform/dev/jwt

# 回滚到特定版本
vault kv rollback -version=1 secret/uav-platform/dev/jwt

# 删除密钥（创建删除标记）
vault kv delete secret/uav-platform/dev/jwt

# 恢复已删除的密钥
vault kv undelete secret/uav-platform/dev/jwt

# 永久销毁密钥版本
vault kv destroy -versions=2 secret/uav-platform/dev/jwt
```

---

## 6. 访问策略配置

### 6.1 创建策略

```bash
# 1. 网关服务策略（只读 JWT 和 UTM 密钥）
cat > /tmp/gateway-policy.hcl << 'EOF'
# 读取 JWT 密钥
path "secret/data/uav-platform/{{environment}}/jwt" {
  capabilities = ["read"]
}

# 读取 UTM 密钥
path "secret/data/uav-platform/{{environment}}/utm" {
  capabilities = ["read"]
}

# 读取 Redis 密钥（用于 session/token 缓存）
path "secret/data/uav-platform/{{environment}}/redis" {
  capabilities = ["read"]
}
EOF

# 2. 平台服务策略（数据库 + Redis）
cat > /tmp/platform-policy.hcl << 'EOF'
# 读取数据库密钥
path "secret/data/uav-platform/{{environment}}/db" {
  capabilities = ["read"]
}

# 读取 Redis 密钥
path "secret/data/uav-platform/{{environment}}/redis" {
  capabilities = ["read"]
}

# 读取 Kafka 密钥
path "secret/data/uav-platform/{{environment}}/kafka" {
  capabilities = ["read"]
}
EOF

# 3. 数据库管理员策略（读写数据库密钥）
cat > /tmp/db-admin-policy.hcl << 'EOF'
# 管理数据库密钥
path "secret/data/uav-platform/{{environment}}/db" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# 管理数据库连接字符串
path "secret/data/uav-platform/{{environment}}/db/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
EOF

# 4. 只读审计策略（安全审计使用）
cat > /tmp/audit-policy.hcl << 'EOF'
# 只读访问所有密钥（审计用途）
path "secret/data/uav-platform/{{environment}}/*" {
  capabilities = ["read", "list"]
}

# 读取系统状态
path "sys/metrics" {
  capabilities = ["read"]
}
EOF

# 写入策略
vault policy write uav-gateway /tmp/gateway-policy.hcl
vault policy write uav-platform /tmp/platform-policy.hcl
vault policy write uav-db-admin /tmp/db-admin-policy.hcl
vault policy write uav-audit /tmp/audit-policy.hcl

# 验证策略
vault policy read uav-gateway
vault policy list
```

### 6.2 策略模板变量

```bash
# 使用模板变量实现按环境隔离
cat > /tmp/templated-policy.hcl << 'EOF'
# 使用 identity.entity.aliases.auth_method_xxx.name 作为环境变量
path "secret/data/uav-platform/{{identity.entity.aliases.auth_jwt_xxxx.name}}/*" {
  capabilities = ["read", "list"]
}
EOF
```

---

## 7. 认证方法配置

### 7.1 启用 Kubernetes 认证（K8s 环境推荐）

```bash
# 启用 Kubernetes 认证
vault auth enable kubernetes

# 配置 Kubernetes 认证
vault write auth/kubernetes/config \
  token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
  kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443" \
  kubernetes_ca_cert="$(cat /var/run/secrets/kubernetes.io/serviceaccount/ca.crt)" \
  issuer="https://kubernetes.default.svc.cluster.local"

# 创建服务账户角色
cat > /tmp/k8s-gateway-role.json << 'EOF'
{
  "bound_service_account_names": ["api-gateway"],
  "bound_service_account_namespaces": ["uav-platform"],
  "policies": ["uav-gateway"],
  "ttl": "1h",
  "max_ttl": "24h"
}
EOF

vault write auth/kubernetes/role/api-gateway \
  bound_service_account_names="api-gateway" \
  bound_service_account_namespaces="uav-platform" \
  policies="uav-gateway" \
  ttl=1h \
  max_ttl=24h

vault write auth/kubernetes/role/platform-api \
  bound_service_account_names="platform-api" \
  bound_service_account_namespaces="uav-platform" \
  policies="uav-platform" \
  ttl=1h \
  max_ttl=24h
```

### 7.2 启用 AppRole 认证（非 K8s 环境）

```bash
# 启用 AppRole 认证
vault auth enable approle

# 创建 AppRole
cat > /tmp/approle-gateway.json << 'EOF'
{
  "policies": ["uav-gateway"],
  "token_ttl": "1h",
  "token_max_ttl": "24h",
  "secret_id_ttl": "720h",
  "secret_id_num_uses": 100
}
EOF

vault write auth/approle/role/api-gateway \
  policies="uav-gateway" \
  token_ttl=1h \
  token_max_ttl=24h \
  secret_id_ttl=720h \
  secret_id_num_uses=100

vault write auth/approle/role/platform-api \
  policies="uav-platform" \
  token_ttl=1h \
  token_max_ttl=24h \
  secret_id_ttl=720h \
  secret_id_num_uses=100

# 获取 RoleID
vault read auth/approle/role/api-gateway/role-id

# 生成 SecretID
vault write -f auth/approle/role/api-gateway/secret-id

# 登录（使用 RoleID + SecretID）
vault write auth/approle/login \
  role_id="<role-id>" \
  secret_id="<secret-id>"
```

### 7.3 启用 JWT/OIDC 认证（可选）

```bash
# 启用 JWT 认证
vault auth enable jwt

# 配置 JWT 验证（以 Keycloak 为例）
vault write auth/jwt/config \
  oidc_discovery_url="https://keycloak.uav-platform.com/realms/uav-platform" \
  oidc_client_id="vault-client" \
  oidc_client_secret="<client-secret>" \
  default_role="uav-user"

# 创建 JWT 角色
vault write auth/jwt/role/uav-user \
  role_type="oidc" \
  policies="uav-gateway" \
  user_claim="sub" \
  groups_claim="groups" \
  bound_audiences="vault-client" \
  ttl=1h \
  max_ttl=24h
```

---

## 8. 与 Spring Boot 集成

### 8.1 添加依赖

在 `pom.xml` 中添加 Spring Cloud Vault 依赖：

```xml
<!-- Spring Cloud Vault -->
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-vault-config</artifactId>
    <version>4.2.0</version>
</dependency>

<!-- Spring Vault Core -->
<dependency>
    <groupId>org.springframework.vault</groupId>
    <artifactId>spring-vault-core</artifactId>
    <version>3.2.0</version>
</dependency>
```

### 8.2 bootstrap.yml / application.yml 配置

```yaml
# Vault 配置
spring:
  cloud:
    vault:
      enabled: ${VAULT_ENABLED:false}
      host: ${VAULT_HOST:localhost}
      port: ${VAULT_PORT:8200}
      scheme: ${VAULT_SCHEME:http}
      uri: ${VAULT_ADDR:http://localhost:8200}
      namespace: ${VAULT_NAMESPACE:}
      authentication: ${VAULT_AUTH_METHOD:token}
      token: ${VAULT_TOKEN:}
      
      # AppRole 认证配置
      app-role:
        role-id: ${VAULT_ROLE_ID:}
        secret-id: ${VAULT_SECRET_ID:}
        role: ${VAULT_APPROLE_NAME:}
      
      # Kubernetes 认证配置
      kubernetes:
        role: ${VAULT_K8S_ROLE:}
        service-account-token-file: /var/run/secrets/kubernetes.io/serviceaccount/token
      
      # 密钥路径配置
      kv:
        enabled: true
        backend: secret
        default-context: uav-platform/${spring.profiles.active:dev}
        profile-separator: '/'
        
      # 通用配置
      connection-timeout: 5000
      read-timeout: 15000
      fail-fast: false
      
  config:
    import: optional:vault://

# 自定义 VaultSecretProvider 配置（直接 API 调用）
vault:
  provider:
    enabled: ${VAULT_ENABLED:false}
    addr: ${VAULT_ADDR:http://localhost:8200}
    token: ${VAULT_TOKEN:}
    namespace: ${VAULT_NAMESPACE:}
    secret-path-prefix: secret/uav-platform
    cache-ttl-minutes: 5
    fallback-file: classpath:vault-secrets.json
```

### 8.3 使用 VaultSecretProvider

```java
import com.uav.common.core.vault.VaultSecretProvider;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class DatabaseConfigService {

    @Autowired
    private VaultSecretProvider vaultSecretProvider;

    public void configureDatabase() {
        // 从 Vault 获取数据库密码
        String dbPassword = vaultSecretProvider.getSecret("db", "DB_PASSWORD");
        String dbUrl = vaultSecretProvider.getSecret("db", "DB_URL");
        
        // 获取 Redis 密码
        String redisPassword = vaultSecretProvider.getSecret("redis", "REDIS_PASSWORD");
        
        // 获取 JWT 密钥
        String jwtSecret = vaultSecretProvider.getSecret("jwt", "JWT_SECRET");
        
        // 批量获取
        Map<String, String> kafkaSecrets = vaultSecretProvider.getSecrets("kafka", 
            "KAFKA_PASSWORD", "KAFKA_SASL_USERNAME");
    }
}
```

### 8.4 回退文件模板（vault-secrets.json）

```json
{
  "dev": {
    "jwt": {
      "JWT_SECRET": "dev-jwt-secret-change-me",
      "JWT_EXPIRATION": "86400000"
    },
    "db": {
      "DB_PASSWORD": "dev_db_password",
      "DB_URL": "jdbc:mysql://localhost:3306/uav_platform"
    },
    "redis": {
      "REDIS_PASSWORD": "dev_redis_password",
      "REDIS_HOST": "localhost",
      "REDIS_PORT": "6379"
    },
    "kafka": {
      "KAFKA_PASSWORD": "dev_kafka_password",
      "KAFKA_SASL_USERNAME": "uav-platform"
    },
    "utm": {
      "UTM_SECRET": "dev-utm-secret",
      "UTM_API_KEY": "dev-utm-api-key"
    }
  },
  "staging": {
    "jwt": {
      "JWT_SECRET": "staging-jwt-secret",
      "JWT_EXPIRATION": "3600000"
    },
    "db": {
      "DB_PASSWORD": "staging_db_password",
      "DB_URL": "jdbc:mysql://staging-db:3306/uav_platform"
    },
    "redis": {
      "REDIS_PASSWORD": "staging_redis_password",
      "REDIS_HOST": "staging-redis",
      "REDIS_PORT": "6379"
    },
    "kafka": {
      "KAFKA_PASSWORD": "staging_kafka_password",
      "KAFKA_SASL_USERNAME": "uav-platform-staging"
    },
    "utm": {
      "UTM_SECRET": "staging-utm-secret",
      "UTM_API_KEY": "staging-utm-api-key"
    }
  }
}
```

---

## 9. Kubernetes 集成

### 9.1 Vault Agent Sidecar 注入

```yaml
# vault-agent-injector 配置
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: uav-platform
spec:
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "api-gateway"
        vault.hashicorp.com/agent-inject-secret-jwt: "secret/data/uav-platform/prod/jwt"
        vault.hashicorp.com/agent-inject-template-jwt: |
          {{ with secret "secret/data/uav-platform/prod/jwt" -}}
          export JWT_SECRET="{{ .Data.data.JWT_SECRET }}"
          export JWT_EXPIRATION="{{ .Data.data.JWT_EXPIRATION }}"
          {{- end }}
        vault.hashicorp.com/agent-inject-secret-db: "secret/data/uav-platform/prod/db"
        vault.hashicorp.com/agent-inject-template-db: |
          {{ with secret "secret/data/uav-platform/prod/db" -}}
          export DB_PASSWORD="{{ .Data.data.DB_PASSWORD }}"
          export DB_URL="{{ .Data.data.DB_URL }}"
          {{- end }}
    spec:
      serviceAccountName: api-gateway
      containers:
        - name: api-gateway
          image: uav-platform/api-gateway:2.0.0
          env:
            - name: VAULT_ENABLED
              value: "true"
```

### 9.2 Kubernetes 外部 Vault 配置

```bash
# 创建 ServiceAccount
kubectl create serviceaccount api-gateway -n uav-platform
kubectl create serviceaccount platform-api -n uav-platform

# 创建 Vault 认证配置
kubectl exec -it vault-0 -- vault write auth/kubernetes/config \
  token_reviewer_jwt="$(kubectl get secret vault-token -n uav-platform -o jsonpath='{.data.token}' | base64 -d)" \
  kubernetes_host="https://kubernetes.default.svc" \
  kubernetes_ca_cert="$(kubectl config view --raw --minify --flatten -o jsonpath='{.clusters[0].cluster.certificate-authority-data}' | base64 -d)"

# 绑定角色
kubectl exec -it vault-0 -- vault write auth/kubernetes/role/api-gateway \
  bound_service_account_names="api-gateway" \
  bound_service_account_namespaces="uav-platform" \
  policies="uav-gateway" \
  ttl=1h
```

---

## 10. 运维与监控

### 10.1 启用审计日志

```bash
# 启用文件审计日志
vault audit enable file file_path=/var/log/vault/audit.log

# 启用 Syslog 审计日志
vault audit enable syslog tag="vault-audit" facility="AUTH"

# 查看审计设备
vault audit list
vault audit list -detailed
```

### 10.2 监控指标

```bash
# 启用 Prometheus 指标导出
vault write sys/config/telemetry \
  prometheus_retention_time="30s" \
  disable_hostname=true

# 获取指标
curl -H "X-Vault-Token: $VAULT_TOKEN" \
  http://localhost:8200/v1/sys/metrics?format=prometheus
```

### 10.3 备份与恢复

```bash
# 创建快照（Raft 后端）
vault operator raft snapshot save /backup/vault-snapshot-$(date +%Y%m%d).snap

# 恢复快照
vault operator raft snapshot restore /backup/vault-snapshot-20240101.snap

# 自动备份脚本
#!/bin/bash
SNAPSHOT_DIR="/backup/vault"
RETENTION_DAYS=30

vault operator raft snapshot save "$SNAPSHOT_DIR/vault-snapshot-$(date +%Y%m%d-%H%M%S).snap"
find "$SNAPSHOT_DIR" -name "vault-snapshot-*.snap" -mtime +$RETENTION_DAYS -delete
```

---

## 11. 故障排查

### 11.1 常见问题

```bash
# 1. Vault 无法解封
vault status
vault operator unseal <key>

# 2. 权限不足
vault token capabilities secret/uav-platform/dev/jwt
vault token lookup

# 3. 密钥路径不存在
vault kv list secret/uav-platform/dev/
vault kv get secret/uav-platform/dev/jwt

# 4. 网络连接问题
curl -v $VAULT_ADDR/v1/sys/health
vault read sys/health

# 5. 查看 Vault 日志
journalctl -u vault -f
docker logs vault
```

### 11.2 健康检查端点

```bash
# 系统健康
curl http://localhost:8200/v1/sys/health

# 领导者状态
curl -H "X-Vault-Token: $VAULT_TOKEN" http://localhost:8200/v1/sys/leader

# Raft 状态
curl -H "X-Vault-Token: $VAULT_TOKEN" http://localhost:8200/v1/sys/storage/raft/configuration
```

### 11.3 紧急恢复

```bash
# 如果 Vault 完全不可用，使用回退文件
# 1. 确保 vault-secrets.json 存在且最新
# 2. 设置 VAULT_ENABLED=false
# 3. 重启应用服务
# 4. 应用将使用本地回退文件中的密钥

# 生成新的 root token（需要 unseal key）
vault operator generate-root -init
vault operator generate-root -nonce=<nonce> <unseal-key>
```

---

## 附录 A：环境变量清单

| 变量名 | 说明 | 示例 |
|--------|------|------|
| VAULT_ENABLED | 启用 Vault 集成 | true |
| VAULT_ADDR | Vault 地址 | https://vault.uav-platform.com:8200 |
| VAULT_TOKEN | Vault Token | hvs.XXXXXXXX |
| VAULT_NAMESPACE | Vault 命名空间（企业版） | uav-platform |
| VAULT_AUTH_METHOD | 认证方法 | token / kubernetes / approle |
| VAULT_ROLE_ID | AppRole RoleID | - |
| VAULT_SECRET_ID | AppRole SecretID | - |
| VAULT_K8S_ROLE | Kubernetes 角色名 | api-gateway |
| VAULT_CACHE_TTL_MINUTES | 密钥缓存 TTL | 5 |
| VAULT_FALLBACK_FILE | 回退文件路径 | classpath:vault-secrets.json |

## 附录 B：安全最佳实践

1. **Root Token 管理**：初始化后立即撤销 root token，使用管理员策略创建日常管理 token
2. **Unseal Key 分发**：使用 Shamir 秘密共享，将 5 个 unseal key 分发给不同人员
3. **Token TTL**：设置合理的 token TTL，避免长期有效的 token
4. **审计日志**：启用审计日志并定期审查
5. **TLS 加密**：生产环境必须启用 TLS，使用有效的证书
6. **网络隔离**：Vault 应部署在独立的网络区域，限制访问来源
7. **定期轮换**：定期轮换密钥和 token
8. **监控告警**：设置 Vault 健康状态监控和告警

---

*文档版本: 1.0*
*更新日期: 2026-06-15*
*适用版本: UAV Platform V2.0.0*
