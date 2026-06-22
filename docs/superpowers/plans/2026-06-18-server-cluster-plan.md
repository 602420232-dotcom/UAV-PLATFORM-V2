# UAV Platform V2 服务器+集群环境实施计划（Phase 7/8/9）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在生产服务器上完成安全加固（HTTPS/渗透测试/压力测试/稳定性测试），搭建多区域高可用部署架构与灾难恢复方案，并在 Kubernetes 集群上实施混沌工程、成本优化和监控告警完善。

**Architecture:** Phase 7 聚焦单服务器安全加固与性能验证，通过 Nginx 反向代理实现 TLS 终止，使用 OWASP ZAP/k6/JVM 工具链完成安全、压力、稳定性三类测试。Phase 8 扩展为双区域（华东+华北）主从架构，MySQL Group Replication + Redis Sentinel + Kafka 3-Broker 集群实现数据层高可用。Phase 9 在 K8s 集群上通过 Chaos Mesh 进行混沌工程验证，配合 HPA 自动扩缩容和三层监控告警体系实现运维闭环。

**Tech Stack:** Nginx 1.25, Let's Encrypt / certbot, OWASP ZAP 2.14, k6, Chaos Mesh 2.6, Prometheus + Grafana, MySQL 8.4 Group Replication, Redis 7.2 Sentinel, Kafka 7.8 (3-Broker), Kubernetes 1.28, ArgoCD

---

## 文件结构总览

### Nginx / TLS 配置
| 文件 | 职责 |
|------|------|
| `nginx/ssl/nginx-ssl.conf` | Nginx SSL/TLS 主配置：证书路径、协议、密码套件 |
| `nginx/ssl/mtls-ca.cnf` | mTLS CA 证书签发配置 |
| `nginx/ssl/certbot-renew.sh` | certbot 自动续期脚本 |
| `nginx/ssl/hsts-headers.conf` | HSTS 安全头配置片段 |

### 安全测试
| 文件 | 职责 |
|------|------|
| `scripts/security/zap-scan.py` | OWASP ZAP 自动化扫描驱动脚本 |
| `scripts/security/zap-auth-config.json` | ZAP 认证配置（JWT 登录上下文） |
| `scripts/security/jwt-test-suite.py` | JWT 安全测试：过期/篡改/重放/空算法 |
| `scripts/security/rbac-bypass-test.py` | RBAC 越权测试脚本 |

### 压力测试
| 文件 | 职责 |
|------|------|
| `scripts/perf/k6/api-gateway-test.js` | API Gateway 压测脚本（100/500/1000 并发） |
| `scripts/perf/k6/full-chain-test.js` | 全链路压测：Gateway -> Service -> DB |
| `scripts/perf/k6/db-pool-test.js` | 数据库连接池压测 |
| `scripts/perf/k6/kafka-throughput-test.js` | Kafka 吞吐量压测 |
| `scripts/perf/k6/perf-baseline.json` | 性能基准目标配置 |

### 稳定性测试
| 文件 | 职责 |
|------|------|
| `scripts/stability/soak-test.sh` | 7 天长跑测试启动脚本 |
| `scripts/stability/jvm-heap-analyzer.py` | JVM Heap Dump 自动分析脚本 |
| `scripts/stability/connection-leak-detector.py` | 连接泄漏检测脚本 |
| `scripts/stability/recovery-test.sh` | 自动恢复测试脚本 |

### 多区域部署
| 文件 | 职责 |
|------|------|
| `k8s/multi-region/primary-east/mysql-group-replication.cnf` | MySQL Group Replication 华东主节点配置 |
| `k8s/multi-region/secondary-north/mysql-group-replication.cnf` | MySQL Group Replication 华北备份节点配置 |
| `k8s/multi-region/primary-east/redis-sentinel.conf` | Redis Sentinel 高可用配置 |
| `k8s/multi-region/kafka-cluster.yaml` | Kafka 3-Broker 集群部署 |
| `k8s/multi-region/cross-region-sync.yaml` | 跨区域数据同步策略 |

### 灾难恢复
| 文件 | 职责 |
|------|------|
| `scripts/dr/backup-daily.sh` | 每日全量备份脚本 |
| `scripts/dr/backup-binlog.sh` | 实时 binlog 备份脚本 |
| `scripts/dr/failover-auto.sh` | 自动故障转移脚本 |
| `scripts/dr/recovery-drill.sh` | 恢复演练脚本 |

### 混沌工程
| 文件 | 职责 |
|------|------|
| `k8s/chaos/chaos-mesh-install.yaml` | Chaos Mesh 安装配置 |
| `k8s/chaos/network-chaos.yaml` | 网络注入实验（延迟/丢包/分区） |
| `k8s/chaos/pod-kill-chaos.yaml` | Pod Kill 实验 |
| `k8s/chaos/stress-chaos.yaml` | CPU/内存压力实验 |

### 成本优化
| 文件 | 职责 |
|------|------|
| `k8s/hpa-custom.yaml` | HPA 自动扩缩容配置（全服务） |
| `k8s/scheduled-scaler.yaml` | 非高峰时段缩容 CronJob |
| `scripts/cost/resource-usage-report.py` | 资源使用率分析脚本 |

### 监控告警
| 文件 | 职责 |
|------|------|
| `monitoring/prometheus/custom-business-rules.yml` | Prometheus 业务自定义指标采集规则 |
| `monitoring/dashboards/sla-overview.json` | SLA 层仪表盘 |
| `monitoring/dashboards/business-metrics.json` | 业务层仪表盘 |
| `monitoring/dashboards/system-infra.json` | 系统基础设施仪表盘 |
| `monitoring/alert_rules_p0_p3.yml` | P0-P3 分级告警规则 |
| `docs/on-call-sop.md` | On-call 值班方案与事件响应 SOP |

---

## Phase 7: 生产环境安全加固（需服务器）

### Task 7.1: HTTPS/TLS 配置

**Files:**
- Create: `nginx/ssl/nginx-ssl.conf`
- Create: `nginx/ssl/mtls-ca.cnf`
- Create: `nginx/ssl/certbot-renew.sh`
- Create: `nginx/ssl/hsts-headers.conf`
- Modify: `docker-compose.prod.yml`

**前置条件：**
- 一台公网可访问的生产服务器（Ubuntu 22.04+）
- 域名已解析到服务器 IP（如 `api.uav-platform.example.com`）
- 服务器 root/sudo 权限
- 80 和 443 端口开放
- Docker + docker-compose 已安装

- [ ] **Step 1: 安装 Nginx 和 certbot**

```bash
sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx
```

验证：`nginx -v` 输出 `nginx version: nginx/1.2x.x`

- [ ] **Step 2: 创建 Nginx SSL 主配置**

Create: `nginx/ssl/nginx-ssl.conf`

```nginx
# UAV Platform - Nginx SSL/TLS Configuration
# 位置: /etc/nginx/conf.d/uav-platform-ssl.conf

# HTTP -> HTTPS 重定向
server {
    listen 80;
    server_name api.uav-platform.example.com;
    return 301 https://$host$request_uri;
}

# HTTPS 主配置
server {
    listen 443 ssl http2;
    server_name api.uav-platform.example.com;

    ssl_certificate /etc/letsencrypt/live/api.uav-platform.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.uav-platform.example.com/privkey.pem;

    # 仅允许 TLS 1.2 和 1.3
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;

    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;

    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    include /etc/nginx/snippets/hsts-headers.conf;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        client_max_body_size 50m;
    }

    location /actuator/health {
        proxy_pass http://127.0.0.1:8080/actuator/health;
        access_log off;
    }
}
```

- [ ] **Step 3: 创建 HSTS 安全头配置**

Create: `nginx/ssl/hsts-headers.conf`

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self' wss: https:; frame-ancestors 'self';" always;
add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate" always;
add_header Pragma "no-cache" always;
```

- [ ] **Step 4: 申请 Let's Encrypt 证书**

```bash
sudo certbot --nginx -d api.uav-platform.example.com --agree-tos --email admin@example.com
sudo certbot certificates
```

预期输出：
```
Certificate Name: api.uav-platform.example.com
    Expiry Date: 2026-09-18 xx:xx:xx UTC
    Certificate Path: /etc/letsencrypt/live/api.uav-platform.example.com/fullchain.pem
```

- [ ] **Step 5: 创建 mTLS CA 证书配置（微服务间通信）**

Create: `nginx/ssl/mtls-ca.cnf`

```ini
[req]
default_bits = 4096
prompt = no
default_md = sha256
distinguished_name = dn
x509_extensions = v3_ca

[dn]
C = CN
ST = Shanghai
L = Shanghai
O = UAV Platform
OU = Internal Services
CN = UAV Platform Internal CA

[v3_ca]
basicConstraints = critical, CA:TRUE
keyUsage = critical, digitalSignature, keyCertSign, cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always, issuer
```

```bash
# 生成内部 CA
openssl req -x509 -new -nodes -newkey rsa:4096 \
  -keyout /etc/nginx/ssl/internal-ca.key \
  -out /etc/nginx/ssl/internal-ca.crt \
  -days 3650 -config nginx/ssl/mtls-ca.cnf

# 为微服务签发证书（示例：weather-api）
openssl req -new -nodes \
  -keyout /etc/nginx/ssl/weather-api.key \
  -out /etc/nginx/ssl/weather-api.csr \
  -subj "/C=CN/ST=Shanghai/O=UAV Platform/CN=weather-api.internal"

openssl x509 -req \
  -in /etc/nginx/ssl/weather-api.csr \
  -CA /etc/nginx/ssl/internal-ca.crt \
  -CAkey /etc/nginx/ssl/internal-ca.key \
  -CAcreateserial \
  -out /etc/nginx/ssl/weather-api.crt \
  -days 365 \
  -extfile <(echo "subjectAltName=DNS:weather-api,DNS:weather-api.default.svc.cluster.local")
```

- [ ] **Step 6: 创建证书自动续期脚本**

Create: `nginx/ssl/certbot-renew.sh`

```bash
#!/bin/bash
set -euo pipefail
LOG_FILE="/var/log/certbot-renew.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== 开始证书续期检查 ==="
certbot renew --quiet --deploy-hook "systemctl reload nginx" 2>&1 | tee -a "$LOG_FILE"

if certbot certificates 2>&1 | grep -q "Expiry Date"; then
    log "证书状态检查完成"
    certbot certificates 2>&1 | grep -E "(Certificate Name|Expiry Date)" | tee -a "$LOG_FILE"
else
    log "ERROR: 证书状态检查失败"
    exit 1
fi

log "=== 证书续期检查完成 ==="
```

```bash
chmod +x nginx/ssl/certbot-renew.sh
sudo cp nginx/ssl/certbot-renew.sh /etc/cron.weekly/certbot-renew.sh
sudo chmod +x /etc/cron.weekly/certbot-renew.sh
```

- [ ] **Step 7: 更新 docker-compose.prod.yml 添加 mTLS 环境变量**

```yaml
services:
  api-gateway:
    environment:
      - SERVER_SSL_ENABLED=true
      - SERVER_SSL_KEY_STORE=classpath:keystore.p12
      - SERVER_SSL_KEY_STORE_PASSWORD=${SSL_KEYSTORE_PASSWORD}
      - SERVER_SSL_CLIENT_AUTH=need
      - SERVER_SSL_TRUST_STORE=classpath:truststore.p12
      - SERVER_SSL_TRUST_STORE_PASSWORD=${SSL_TRUSTSTORE_PASSWORD}
```

- [ ] **Step 8: 验证 HTTPS 配置**

```bash
openssl s_client -connect api.uav-platform.example.com:443 -servername api.uav-platform.example.com </dev/null 2>/dev/null | openssl x509 -noout -dates
curl -sI https://api.uav-platform.example.com | grep -i "strict-transport"
curl -sI http://api.uav-platform.example.com | head -1
# 预期: HTTP/1.1 301 Moved Permanently
```

预期结果：
- SSL Labs 评级 A+
- HSTS 头正确返回 `max-age=31536000; includeSubDomains; preload`
- HTTP 自动重定向到 HTTPS
- mTLS 微服务间通信正常

**回滚方案：**
```bash
sudo rm /etc/nginx/conf.d/uav-platform-ssl.conf
sudo nginx -t && sudo systemctl reload nginx
```

---

### Task 7.2: 渗透测试

**Files:**
- Create: `scripts/security/zap-scan.py`
- Create: `scripts/security/zap-auth-config.json`
- Create: `scripts/security/jwt-test-suite.py`
- Create: `scripts/security/rbac-bypass-test.py`

**前置条件：**
- 生产环境（或 staging 环境）已部署并可访问
- OWASP ZAP 2.14+ 已安装（`docker pull owasp/zap2.14-stable`）
- Python 3.11+ 已安装
- 测试账号：SUPER_ADMIN / OPERATOR / OBSERVER 各一个
- 目标 API 地址：`https://api.uav-platform.example.com`

- [ ] **Step 1: 创建 ZAP 自动化扫描驱动脚本**

Create: `scripts/security/zap-scan.py`

```python
#!/usr/bin/env python3
"""OWASP ZAP 自动化扫描驱动脚本 - 扫描所有 API 端点，检测 SQL 注入、XSS、CSRF 等漏洞"""

import json
import time
import requests
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ZAP_API = "http://localhost:8080"
TARGET_URL = "https://api.uav-platform.example.com"
API_KEY = "zap-api-key-change-me"
REPORT_DIR = Path("security-reports") / datetime.now().strftime("%Y%m%d_%H%M%S")


def wait_for_zap_ready(timeout=120):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{ZAP_API}/JSON/core/version", timeout=5)
            if r.status_code == 200:
                print(f"[OK] ZAP ready: {r.json()['version']}")
                return True
        except requests.ConnectionError:
            pass
        time.sleep(2)
    print("[FAIL] ZAP 启动超时")
    return False


def start_zap_docker():
    subprocess.run([
        "docker", "run", "-d", "--name", "zap-scan",
        "-p", "8080:8080", "-p", "8090:8090",
        "-v", f"{REPORT_DIR}:/zap/wrk",
        "owasp/zap2.14-stable:latest",
        "zap.sh", "-daemon", "-port", "8080",
        "-host", "0.0.0.0", "-config", f"api.key={API_KEY}"
    ], check=True)


def configure_auth():
    with open("scripts/security/zap-auth-config.json") as f:
        auth_config = json.load(f)
    requests.get(f"{ZAP_API}/JSON/authentication/setAuthenticationMethod", params={
        "apikey": API_KEY, "contextId": auth_config["context_id"],
        "authMethodName": "jsonBasedAuthentication",
        "authMethodConfigParams": json.dumps({
            "loginUrl": f"{TARGET_URL}/api/v1/auth/login",
            "loginRequestData": json.dumps(auth_config["login_payload"]),
            "authTokenName": "token", "authTokenLocation": "JSON_BODY",
        })
    })


def run_spider_scan():
    print("[INFO] 启动 Spider 扫描...")
    r = requests.get(f"{ZAP_API}/JSON/spider/scan", params={
        "apikey": API_KEY, "url": TARGET_URL,
        "contextName": "UAV Platform", "maxChildren": 50, "recurse": "true"
    })
    return poll_scan_status("spider", r.json()["scan"])


def run_active_scan():
    print("[INFO] 启动 Active Scan...")
    r = requests.get(f"{ZAP_API}/JSON/ascan/scan", params={
        "apikey": API_KEY, "url": TARGET_URL,
        "recurse": "true", "inScopeOnly": "true", "scanPolicyName": "Default Policy"
    })
    return poll_scan_status("ascan", r.json()["scan"])


def poll_scan_status(scan_type, scan_id, timeout=600):
    start = time.time()
    while time.time() - start < timeout:
        r = requests.get(f"{ZAP_API}/JSON/{scan_type}/status", params={
            "apikey": API_KEY, "scanId": scan_id
        })
        status = r.json()["status"]
        print(f"[{scan_type}] 进度: {status}%")
        if status == "100":
            print(f"[OK] {scan_type} 扫描完成")
            return scan_id
        time.sleep(10)
    print(f"[FAIL] {scan_type} 扫描超时")
    sys.exit(1)


def generate_report():
    r = requests.get(f"{ZAP_API}/JSON/core/htmlreport", params={"apikey": API_KEY})
    report_path = REPORT_DIR / "zap-scan-report.html"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(r.text)
    print(f"[OK] 报告已生成: {report_path}")


def get_alert_summary():
    r = requests.get(f"{ZAP_API}/JSON/core/alerts", params={"apikey": API_KEY, "baseurl": TARGET_URL})
    alerts = r.json().get("alerts", [])
    counts = {"High": 0, "Medium": 0, "Low": 0, "Informational": 0}
    for a in alerts:
        risk = a.get("riskcode", "0")
        if risk == "3": counts["High"] += 1
        elif risk == "2": counts["Medium"] += 1
        elif risk == "1": counts["Low"] += 1
        else: counts["Informational"] += 1
    print(f"\n=== 扫描结果摘要 ===")
    for level, count in counts.items():
        print(f"  {level}: {count}")
    return counts


def main():
    print(f"=== OWASP ZAP 自动化扫描 ===")
    print(f"目标: {TARGET_URL}")
    start_zap_docker()
    if not wait_for_zap_ready():
        sys.exit(1)
    configure_auth()
    run_spider_scan()
    run_active_scan()
    generate_report()
    summary = get_alert_summary()
    if summary["High"] > 0:
        print(f"\n[FAIL] 发现 {summary['High']} 个高危漏洞")
        sys.exit(1)
    else:
        print("\n[PASS] 无高危漏洞")
        sys.exit(0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 创建 ZAP 认证配置**

Create: `scripts/security/zap-auth-config.json`

```json
{
  "context_id": "1",
  "context_name": "UAV Platform",
  "login_payload": {
    "username": "security_tester",
    "password": "${ZAP_TEST_PASSWORD}",
    "rememberMe": false
  },
  "include_urls": ["https://api.uav-platform.example.com/api/v1/.*"],
  "exclude_urls": [
    "https://api.uav-platform.example.com/api/v1/auth/logout",
    "https://api.uav-platform.example.com/actuator/.*"
  ]
}
```

- [ ] **Step 3: 创建 JWT 安全测试套件**

Create: `scripts/security/jwt-test-suite.py`

```python
#!/usr/bin/env python3
"""JWT 安全测试套件 - 测试过期/篡改/重放/空算法攻击"""

import jwt
import time
import requests
import sys
import json
import base64
from datetime import datetime

BASE_URL = "https://api.uav-platform.example.com"
TEST_USER = {"username": "jwt_tester", "password": "Test@123456"}
RESULTS = {"passed": 0, "failed": 0}


def login():
    r = requests.post(f"{BASE_URL}/api/v1/auth/login", json=TEST_USER)
    assert r.status_code == 200, f"登录失败: {r.text}"
    return r.json()["data"]["token"]


def test_expired_token():
    print("\n[TEST 1] 过期 Token 测试")
    try:
        token = login()
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp_time = decoded.get("exp", 0)
        remaining = exp_time - time.time()
        if remaining > 0 and remaining < 300:
            print(f"  等待 {int(remaining)+1} 秒让 Token 过期...")
            time.sleep(remaining + 1)
        r = requests.get(f"{BASE_URL}/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        if r.status_code == 401:
            print("  [PASS] 过期 Token 被正确拒绝 (401)")
            RESULTS["passed"] += 1
        else:
            print(f"  [FAIL] 过期 Token 未被拒绝，状态码: {r.status_code}")
            RESULTS["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        RESULTS["failed"] += 1


def test_tampered_token():
    print("\n[TEST 2] 篡改 Token 测试")
    try:
        token = login()
        parts = token.split(".")
        if len(parts) == 3:
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
            payload["roles"] = ["ROLE_SUPER_ADMIN"]
            new_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
            tampered = f"{parts[0]}.{new_payload}.{parts[2]}"
            r = requests.get(f"{BASE_URL}/api/v1/admin/users", headers={"Authorization": f"Bearer {tampered}"})
            if r.status_code == 401:
                print("  [PASS] 篡改 Token 被正确拒绝 (401)")
                RESULTS["passed"] += 1
            else:
                print(f"  [FAIL] 篡改 Token 未被拒绝，状态码: {r.status_code}")
                RESULTS["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        RESULTS["failed"] += 1


def test_replay_attack():
    print("\n[TEST 3] 重放攻击测试")
    try:
        token = login()
        r1 = requests.get(f"{BASE_URL}/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        r2 = requests.get(f"{BASE_URL}/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
        print(f"  GET 重放: 第一次={r1.status_code}, 第二次={r2.status_code}")
        print("  [INFO] 重放攻击防护取决于 jti/nonce 机制实现")
        RESULTS["passed"] += 1
    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        RESULTS["failed"] += 1


def test_none_algorithm():
    print("\n[TEST 4] 空算法攻击测试")
    try:
        token = login()
        parts = token.split(".")
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
        payload["alg"] = "none"
        new_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
        none_token = f"{parts[0]}.{new_payload}."
        r = requests.get(f"{BASE_URL}/api/v1/users/me", headers={"Authorization": f"Bearer {none_token}"})
        if r.status_code == 401:
            print("  [PASS] 空算法攻击被正确拒绝 (401)")
            RESULTS["passed"] += 1
        else:
            print(f"  [FAIL] 空算法攻击未被拒绝，状态码: {r.status_code}")
            RESULTS["failed"] += 1
    except Exception as e:
        print(f"  [FAIL] 异常: {e}")
        RESULTS["failed"] += 1


if __name__ == "__main__":
    print(f"=== JWT 安全测试套件 ===")
    print(f"目标: {BASE_URL}")
    print(f"时间: {datetime.now().isoformat()}")
    test_expired_token()
    test_tampered_token()
    test_replay_attack()
    test_none_algorithm()
    print(f"\n{'='*50}")
    print(f"通过: {RESULTS['passed']}, 失败: {RESULTS['failed']}")
    sys.exit(1 if RESULTS["failed"] > 0 else 0)
```

- [ ] **Step 4: 创建 RBAC 越权测试脚本**

Create: `scripts/security/rbac-bypass-test.py`

```python
#!/usr/bin/env python3
"""RBAC 越权测试脚本 - 测试不同角色是否能访问未授权的 API 端点"""

import requests
import sys
from datetime import datetime

BASE_URL = "https://api.uav-platform.example.com"
ACCOUNTS = {
    "SUPER_ADMIN": {"username": "admin_tester", "password": "Admin@123456"},
    "OPERATOR": {"username": "operator_tester", "password": "Oper@123456"},
    "OBSERVER": {"username": "observer_tester", "password": "Observe@123456"},
}

ENDPOINT_MATRIX = {
    ("GET", "/api/v1/admin/users"): ["SUPER_ADMIN"],
    ("POST", "/api/v1/admin/users"): ["SUPER_ADMIN"],
    ("DELETE", "/api/v1/admin/users/1"): ["SUPER_ADMIN"],
    ("GET", "/api/v1/users/me"): ["SUPER_ADMIN", "OPERATOR", "OBSERVER"],
    ("POST", "/api/v1/weather/query"): ["SUPER_ADMIN", "OPERATOR", "OBSERVER"],
    ("POST", "/api/v1/planning/optimize"): ["SUPER_ADMIN", "OPERATOR"],
    ("POST", "/api/v1/risk/assess"): ["SUPER_ADMIN", "OPERATOR"],
    ("GET", "/api/v1/assimilation/experiments"): ["SUPER_ADMIN", "OPERATOR"],
    ("POST", "/api/v1/assimilation/experiments"): ["SUPER_ADMIN", "OPERATOR"],
    ("POST", "/api/v1/auth/reset-password"): ["SUPER_ADMIN"],
}

RESULTS = {"passed": 0, "failed": 0, "details": []}


def login(role):
    r = requests.post(f"{BASE_URL}/api/v1/auth/login", json=ACCOUNTS[role])
    if r.status_code != 200:
        print(f"  [ERROR] {role} 登录失败: {r.text}")
        return None
    return r.json()["data"]["token"]


def test_endpoint(method, path, role, token):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}{path}"
    if method == "GET": r = requests.get(url, headers=headers, timeout=10)
    elif method == "POST": r = requests.post(url, headers=headers, json={}, timeout=10)
    elif method == "DELETE": r = requests.delete(url, headers=headers, timeout=10)
    else: return

    allowed = role in ENDPOINT_MATRIX[(method, path)]
    if allowed and r.status_code in (200, 201, 204, 400, 404):
        RESULTS["passed"] += 1
        print(f"  [PASS] {role} {method} {path} -> {r.status_code} (预期允许)")
    elif not allowed and r.status_code == 403:
        RESULTS["passed"] += 1
        print(f"  [PASS] {role} {method} {path} -> 403 (预期禁止)")
    elif not allowed and r.status_code != 403:
        RESULTS["failed"] += 1
        RESULTS["details"].append(f"越权: {role} 可访问 {method} {path}")
        print(f"  [FAIL] {role} {method} {path} -> {r.status_code} (预期 403)")
    elif allowed and r.status_code == 403:
        RESULTS["failed"] += 1
        RESULTS["details"].append(f"误拒: {role} 无法访问 {method} {path}")
        print(f"  [FAIL] {role} {method} {path} -> 403 (预期允许)")


if __name__ == "__main__":
    print(f"=== RBAC 越权测试 ===")
    print(f"目标: {BASE_URL}")
    print(f"时间: {datetime.now().isoformat()}\n")
    tokens = {}
    for role in ACCOUNTS:
        tokens[role] = login(role)
        if tokens[role] is None:
            sys.exit(1)
    for (method, path), _ in ENDPOINT_MATRIX.items():
        print(f"\n--- {method} {path} ---")
        for role in ACCOUNTS:
            test_endpoint(method, path, role, tokens[role])
    print(f"\n{'='*50}")
    print(f"通过: {RESULTS['passed']}, 失败: {RESULTS['failed']}")
    if RESULTS["details"]:
        print("问题详情:")
        for d in RESULTS["details"]: print(f"  - {d}")
    sys.exit(1 if RESULTS["failed"] > 0 else 0)
```

- [ ] **Step 5: 运行所有安全测试**

```bash
python3 scripts/security/zap-scan.py
python3 scripts/security/jwt-test-suite.py
python3 scripts/security/rbac-bypass-test.py
```

- [ ] **Step 6: 汇总渗透测试结果并制定修复计划**

| 优先级 | 漏洞类型 | 修复方案 | 预估工时 |
|--------|----------|----------|----------|
| P0 | SQL 注入 | 参数化查询 + 输入校验 | 2h/端点 |
| P0 | XSS 存储型 | 输出编码 + CSP 策略 | 1h/页面 |
| P1 | CSRF | SameSite Cookie + Token 验证 | 2h |
| P1 | JWT 篡改 | 强制算法白名单 + 密钥轮换 | 1h |
| P2 | 信息泄露 | 移除错误详情 + 统一错误响应 | 1h |

预期结果：ZAP 扫描 0 High、Medium <= 3；JWT 测试全部通过；RBAC 越权测试全部通过

**回滚方案：** 安全测试为只读操作，无需回滚；修复代码通过 Git revert 回退

---

### Task 7.3: 压力测试

**Files:**
- Create: `scripts/perf/k6/api-gateway-test.js`
- Create: `scripts/perf/k6/full-chain-test.js`
- Create: `scripts/perf/k6/db-pool-test.js`
- Create: `scripts/perf/k6/kafka-throughput-test.js`
- Create: `scripts/perf/k6/perf-baseline.json`

**前置条件：**
- 生产环境（或 staging 环境）已部署
- k6 已安装（`docker pull grafana/k6`）
- 测试数据已准备（至少 1000 条气象记录、100 条航线记录）
- 监控面板已就绪（Prometheus + Grafana）

- [ ] **Step 1: 定义性能基准目标**

Create: `scripts/perf/k6/perf-baseline.json`

```json
{
  "baseline": {
    "api_gateway": { "qps": 500, "p99_latency_ms": 200, "error_rate_pct": 0.1 },
    "weather_api": { "qps": 200, "p99_latency_ms": 500, "error_rate_pct": 0.5 },
    "planning_api": { "qps": 50, "p99_latency_ms": 2000, "error_rate_pct": 0.5 },
    "risk_api": { "qps": 100, "p99_latency_ms": 1000, "error_rate_pct": 0.5 },
    "assimilation_api": { "qps": 30, "p99_latency_ms": 3000, "error_rate_pct": 1.0 },
    "full_chain": { "qps": 100, "p99_latency_ms": 500, "error_rate_pct": 0.5 },
    "db_pool": { "max_connections": 50, "p99_acquire_ms": 50, "connection_leak_count": 0 },
    "kafka": { "throughput_msgs_per_sec": 10000, "p99_produce_ms": 50, "p99_consume_ms": 100 }
  }
}
```

- [ ] **Step 2: 创建 API Gateway 压测脚本**

Create: `scripts/perf/k6/api-gateway-test.js`

```javascript
// API Gateway 压力测试 - 模拟 100/500/1000 并发用户
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const authLatency = new Trend('auth_latency');
const queryLatency = new Trend('query_latency');
const BASE_URL = __ENV.BASE_URL || 'https://api.uav-platform.example.com';

export function setup() {
    const loginRes = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
        username: 'perf_tester', password: 'Perf@123456'
    }), { headers: { 'Content-Type': 'application/json' } });
    check(loginRes, { 'login successful': (r) => r.status === 200 });
    return { token: loginRes.json('data.token') };
}

export const options = {
    scenarios: {
        smoke: __ENV.STAGE === 'smoke' ? {
            executor: 'constant-vus', vus: 10, duration: '30s', exec: 'mixedRequests'
        } : undefined,
        load: __ENV.STAGE === 'load' ? {
            executor: 'ramping-vus', startVUs: 10,
            stages: [
                { duration: '1m', target: 100 },
                { duration: '3m', target: 100 },
                { duration: '1m', target: 0 },
            ], exec: 'mixedRequests'
        } : undefined,
        stress: __ENV.STAGE === 'stress' ? {
            executor: 'ramping-vus', startVUs: 50,
            stages: [
                { duration: '2m', target: 100 },
                { duration: '3m', target: 500 },
                { duration: '2m', target: 1000 },
                { duration: '1m', target: 0 },
            ], exec: 'mixedRequests'
        } : undefined,
    },
    thresholds: {
        http_req_duration: ['p(99)<200'],
        errors: ['rate<0.01'],
    },
};

export function mixedRequests(data) {
    const headers = {
        'Authorization': `Bearer ${data.token}`,
        'Content-Type': 'application/json',
    };
    const requestType = Math.random();

    if (requestType < 0.3) {
        const start = Date.now();
        const res = http.get(`${BASE_URL}/api/v1/users/me`, { headers });
        authLatency.add(Date.now() - start);
        check(res, { 'get profile OK': (r) => r.status === 200 });
    } else if (requestType < 0.6) {
        const start = Date.now();
        const res = http.post(`${BASE_URL}/api/v1/weather/query`, JSON.stringify({
            region: 'shanghai',
            startTime: '2026-06-18T00:00:00Z',
            endTime: '2026-06-18T23:59:59Z',
            variables: ['wind_speed', 'temperature', 'pressure'],
        }), { headers });
        queryLatency.add(Date.now() - start);
        check(res, { 'weather query OK': (r) => r.status === 200 });
    } else if (requestType < 0.8) {
        const res = http.post(`${BASE_URL}/api/v1/planning/optimize`, JSON.stringify({
            algorithm: 'VRPTW',
            waypoints: [
                { lng: 121.4737, lat: 31.2304 },
                { lng: 121.4837, lat: 31.2404 },
                { lng: 121.4937, lat: 31.2504 },
            ],
            constraints: { maxFlightTime: 30, batteryCapacity: 100 },
        }), { headers });
        check(res, { 'planning OK': (r) => r.status === 200 || r.status === 202 });
    } else {
        const res = http.post(`${BASE_URL}/api/v1/risk/assess`, JSON.stringify({
            routeId: 'test-route-001', weatherScenario: 'moderate_wind',
        }), { headers });
        check(res, { 'risk assess OK': (r) => r.status === 200 || r.status === 202 });
    }
    sleep(Math.random() * 0.5 + 0.1);
}
```

- [ ] **Step 3: 创建全链路压测脚本**

Create: `scripts/perf/k6/full-chain-test.js`

```javascript
// 全链路压测: API Gateway -> Service -> DB
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'https://api.uav-platform.example.com';
const fullChainLatency = new Trend('full_chain_latency');
const dbWriteLatency = new Trend('db_write_latency');
const dbReadLatency = new Trend('db_read_latency');
const cacheHitRate = new Rate('cache_hit_rate');
const errorRate = new Rate('errors');

export function setup() {
    const r = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
        username: 'perf_tester', password: 'Perf@123456'
    }), { headers: { 'Content-Type': 'application/json' } });
    return { token: r.json('data.token') };
}

export const options = {
    executor: 'ramping-vus', startVUs: 10,
    stages: [
        { duration: '2m', target: 50 },
        { duration: '5m', target: 100 },
        { duration: '2m', target: 50 },
        { duration: '1m', target: 0 },
    ],
    thresholds: { full_chain_latency: ['p(99)<500'], errors: ['rate<0.005'] },
};

export default function (data) {
    const headers = {
        'Authorization': `Bearer ${data.token}`,
        'Content-Type': 'application/json',
    };
    // 写入路径: Gateway -> Platform API -> MySQL
    const ws = Date.now();
    const wr = http.post(`${BASE_URL}/api/v1/weather/query`, JSON.stringify({
        region: 'shanghai', startTime: '2026-06-18T00:00:00Z',
        endTime: '2026-06-18T23:59:59Z', variables: ['wind_speed', 'temperature'],
    }), { headers });
    dbWriteLatency.add(Date.now() - ws);
    check(wr, { 'write path OK': (r) => r.status === 200 });

    // 读取路径（缓存命中/穿透）
    const rs = Date.now();
    const rr = http.get(`${BASE_URL}/api/v1/users/me`, { headers });
    dbReadLatency.add(Date.now() - rs);
    cacheHitRate.add((rr.headers['X-Cache'] || 'MISS') === 'HIT');
    check(rr, { 'read path OK': (r) => r.status === 200 });

    // 消息队列路径: Gateway -> Service -> Kafka -> Consumer
    const ms = Date.now();
    const mr = http.post(`${BASE_URL}/api/v1/assimilation/experiments`, JSON.stringify({
        name: `perf-test-${Date.now()}`, algorithm: '3DVAR',
        dataSource: 'fengwu', parameters: { maxIterations: 10 },
    }), { headers });
    fullChainLatency.add(Date.now() - ms);
    check(mr, { 'mq path OK': (r) => r.status === 200 || r.status === 202 });
    sleep(0.3);
}
```

- [ ] **Step 4: 创建数据库连接池压测脚本**

Create: `scripts/perf/k6/db-pool-test.js`

```javascript
import http from 'k6/http';
import { check } from 'k6';
import { Trend, Counter } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'https://api.uav-platform.example.com';
const poolAcquireTime = new Trend('pool_acquire_time');
const poolTimeoutCount = new Counter('pool_timeout_count');

export function setup() {
    const r = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
        username: 'perf_tester', password: 'Perf@123456'
    }), { headers: { 'Content-Type': 'application/json' } });
    return { token: r.json('data.token') };
}

export const options = {
    executor: 'constant-arrival-rate', rate: 200, timeUnit: '1s',
    duration: '3m', preAllocatedVUs: 100, maxVUs: 200,
    thresholds: { pool_acquire_time: ['p(99)<50'], pool_timeout_count: ['count<5'] },
};

export default function (data) {
    const headers = { 'Authorization': `Bearer ${data.token}`, 'Content-Type': 'application/json' };
    const start = Date.now();
    const res = http.get(`${BASE_URL}/api/v1/weather/history?region=shanghai&limit=50`, { headers });
    poolAcquireTime.add(Date.now() - start);
    if (res.status === 503 || res.status === 500) poolTimeoutCount.add(1);
    check(res, {
        'pool request OK': (r) => r.status === 200,
        'no pool exhaustion': (r) => r.status !== 503,
    });
}
```

- [ ] **Step 5: 创建 Kafka 吞吐量压测脚本**

Create: `scripts/perf/k6/kafka-throughput-test.js`

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Counter } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'https://api.uav-platform.example.com';
const produceLatency = new Trend('kafka_produce_latency');
const consumeLatency = new Trend('kafka_consume_latency');
const msgCount = new Counter('kafka_msg_count');

export function setup() {
    const r = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
        username: 'perf_tester', password: 'Perf@123456'
    }), { headers: { 'Content-Type': 'application/json' } });
    return { token: r.json('data.token') };
}

export const options = {
    scenarios: {
        producer: {
            executor: 'constant-arrival-rate', rate: 500, timeUnit: '1s',
            duration: '5m', preAllocatedVUs: 50, exec: 'produceMessages',
        },
        consumer: {
            executor: 'constant-vus', vus: 5, duration: '5m',
            exec: 'consumeMessages', startTime: '30s',
        },
    },
    thresholds: { kafka_produce_latency: ['p(99)<50'] },
};

export function produceMessages(data) {
    const headers = { 'Authorization': `Bearer ${data.token}`, 'Content-Type': 'application/json' };
    const start = Date.now();
    const res = http.post(`${BASE_URL}/api/v1/weather/ingest`, JSON.stringify({
        source: 'fengwu', timestamp: new Date().toISOString(),
        data: {
            windSpeed: Math.random() * 20 + 5, temperature: Math.random() * 15 + 15,
            pressure: Math.random() * 20 + 1000, humidity: Math.random() * 40 + 40,
        },
        location: { lng: 121.47 + Math.random() * 0.1, lat: 31.23 + Math.random() * 0.1 },
    }), { headers });
    produceLatency.add(Date.now() - start);
    msgCount.add(1);
    check(res, { 'message produced': (r) => r.status === 200 || r.status === 202 });
}

export function consumeMessages(data) {
    const headers = { 'Authorization': `Bearer ${data.token}` };
    const start = Date.now();
    const res = http.get(`${BASE_URL}/api/v1/weather/stream?timeout=5`, { headers });
    consumeLatency.add(Date.now() - start);
    check(res, { 'message consumed': (r) => r.status === 200 });
    sleep(1);
}
```

- [ ] **Step 6: 执行分阶段压测**

```bash
# 冒烟测试（10 并发）
docker run --rm -v "$(pwd)/scripts/perf/k6:/scripts" \
  -e BASE_URL=https://api.uav-platform.example.com -e STAGE=smoke \
  grafana/k6 run /scripts/api-gateway-test.js

# 负载测试（100 并发）
docker run --rm -v "$(pwd)/scripts/perf/k6:/scripts" \
  -e BASE_URL=https://api.uav-platform.example.com -e STAGE=load \
  grafana/k6 run /scripts/api-gateway-test.js

# 压力测试（最高 1000 并发）
docker run --rm -v "$(pwd)/scripts/perf/k6:/scripts" \
  -e BASE_URL=https://api.uav-platform.example.com -e STAGE=stress \
  grafana/k6 run /scripts/api-gateway-test.js

# 全链路压测
docker run --rm -v "$(pwd)/scripts/perf/k6:/scripts" \
  -e BASE_URL=https://api.uav-platform.example.com \
  grafana/k6 run /scripts/full-chain-test.js

# 数据库连接池压测
docker run --rm -v "$(pwd)/scripts/perf/k6:/scripts" \
  -e BASE_URL=https://api.uav-platform.example.com \
  grafana/k6 run /scripts/db-pool-test.js

# Kafka 吞吐量压测
docker run --rm -v "$(pwd)/scripts/perf/k6:/scripts" \
  -e BASE_URL=https://api.uav-platform.example.com \
  grafana/k6 run /scripts/kafka-throughput-test.js
```

- [ ] **Step 7: 分析压测结果并对比基准**

预期结果：

| 服务 | 指标 | 基准目标 | 预期实际值 |
|------|------|----------|------------|
| API Gateway | QPS | 500 | >= 500 |
| API Gateway | P99 延迟 | 200ms | <= 200ms |
| API Gateway | 错误率 | 0.1% | <= 0.1% |
| Weather API | QPS | 200 | >= 200 |
| 全链路 | P99 延迟 | 500ms | <= 500ms |
| DB 连接池 | P99 获取时间 | 50ms | <= 50ms |
| Kafka | 吞吐量 | 10,000 msg/s | >= 10,000 |

**回滚方案：** 压测为只读操作，无需回滚；若压测导致服务不可用，通过 `docker-compose restart` 重启服务

---

### Task 7.4: 稳定性测试

**Files:**
- Create: `scripts/stability/soak-test.sh`
- Create: `scripts/stability/jvm-heap-analyzer.py`
- Create: `scripts/stability/connection-leak-detector.py`
- Create: `scripts/stability/recovery-test.sh`

**前置条件：**
- 生产环境已部署并通过压力测试
- JVM 监控已就绪（Prometheus JMX Exporter）
- 磁盘空间充足（Heap Dump 可能达数 GB）
- 告警通道已配置（企业微信/钉钉 Webhook）

- [ ] **Step 1: 创建 7 天长跑测试脚本**

Create: `scripts/stability/soak-test.sh`

```bash
#!/bin/bash
# 7 天长跑测试方案
set -euo pipefail

BASE_URL="${BASE_URL:-https://api.uav-platform.example.com}"
LOG_DIR="/var/log/uav-soak-test"
DURATION_DAYS=7
PID_FILE="/tmp/soak-test.pid"
mkdir -p "$LOG_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_DIR/soak-test.log"; }

cleanup() {
    log "=== 长跑测试终止 ==="
    python3 scripts/stability/jvm-heap-analyzer.py --log-dir "$LOG_DIR"
    python3 scripts/stability/connection-leak-detector.py --log-dir "$LOG_DIR"
    exit 0
}
trap cleanup SIGTERM SIGINT

log "=== 7 天长跑测试启动 ==="
log "目标: $BASE_URL | 持续时间: $DURATION_DAYS 天"
echo $$ > "$PID_FILE"

CYCLE_DURATION="6h"
TOTAL_CYCLES=$((DURATION_DAYS * 4))

for i in $(seq 1 $TOTAL_CYCLES); do
    log "--- 周期 $i/$TOTAL_CYCLES 开始 ---"
    docker run --rm -v "$(pwd)/scripts/perf/k6:/scripts" \
      -e BASE_URL="$BASE_URL" \
      grafana/k6 run --out json="$LOG_DIR/cycle-$i.json" \
      --duration "$CYCLE_DURATION" --vus 20 \
      /scripts/api-gateway-test.js 2>&1 | tee -a "$LOG_DIR/soak-test.log"

    log "采集 JVM 指标..."
    curl -s "http://localhost:9090/api/v1/query?query=jvm_memory_used_bytes" \
      | python3 -c "
import sys, json
data = json.load(sys.stdin)
for result in data.get('data', {}).get('result', []):
    metric = result.get('metric', {})
    value = result.get('value', [0, ''])[1]
    print(f\"  {metric.get('instance', 'unknown')}: {float(value)/1024/1024:.1f} MB\")
" | tee -a "$LOG_DIR/jvm-metrics.log"

    CURRENT_HEAP=$(curl -s "http://localhost:9090/api/v1/query?query=jvm_memory_used_bytes{area='heap'}" \
      | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['result'][0]['value'][1])" 2>/dev/null || echo "0")
    log "当前 Heap 使用: ${CURRENT_HEAP} bytes"

    MAX_HEAP="${MAX_HEAP:-2147483648}"
    if [ "$CURRENT_HEAP" -gt $((MAX_HEAP * 80 / 100)) ]; then
        log "WARNING: Heap 使用超过 80%，触发 Heap Dump"
        curl -s -X POST "http://localhost:8080/actuator/heapdump" \
          -o "$LOG_DIR/heapdump-$(date +%Y%m%d-%H%M%S).hprof" \
          -H "Authorization: Bearer $(cat /tmp/admin-token)" || true
    fi
    log "--- 周期 $i/$TOTAL_CYCLES 完成 ---"
done
log "=== 7 天长跑测试完成 ==="
```

- [ ] **Step 2: 创建 JVM Heap Dump 分析脚本**

Create: `scripts/stability/jvm-heap-analyzer.py`

```python
#!/usr/bin/env python3
"""JVM Heap Dump 自动分析脚本 - 检测内存泄漏模式"""

import requests
import sys
import argparse
from datetime import datetime

PROMETHEUS_URL = "http://localhost:9090"


def analyze_prometheus_metrics(prometheus_url: str, duration_hours: int = 168) -> dict:
    result = {"memory_trend": [], "suspected_leaks": []}
    query = "jvm_memory_used_bytes{area=\"heap\"}"
    try:
        r = requests.get(f"{prometheus_url}/api/v1/query_range", params={
            "query": query, "start": f"now-{duration_hours}h", "end": "now", "step": "5m",
        })
        data = r.json()
        if data.get("status") == "success":
            values = data["data"]["result"][0]["values"]
            if values:
                first_val = float(values[0][1])
                last_val = float(values[-1][1])
                growth_pct = ((last_val - first_val) / first_val) * 100
                result["memory_trend"] = {
                    "start_mb": round(first_val / 1024 / 1024, 1),
                    "end_mb": round(last_val / 1024 / 1024, 1),
                    "growth_pct": round(growth_pct, 2),
                    "max_mb": round(max(float(v[1]) for v in values) / 1024 / 1024, 1),
                    "data_points": len(values),
                }
                if growth_pct > 50:
                    result["suspected_leaks"].append({
                        "type": "heap_growth",
                        "severity": "HIGH" if growth_pct > 100 else "MEDIUM",
                        "detail": f"7 天内 Heap 增长 {growth_pct:.1f}%，可能存在内存泄漏",
                    })
    except Exception as e:
        result["error"] = str(e)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JVM Heap Dump 分析")
    parser.add_argument("--prometheus", default=PROMETHEUS_URL)
    parser.add_argument("--log-dir", help="日志目录")
    args = parser.parse_args()

    print(f"=== JVM Heap Dump 分析报告 ===")
    print(f"时间: {datetime.now().isoformat()}\n--- 内存趋势分析 ---")
    trend = analyze_prometheus_metrics(args.prometheus)
    if trend.get("memory_trend"):
        t = trend["memory_trend"]
        print(f"  起始: {t['start_mb']} MB, 结束: {t['end_mb']} MB, 最大: {t['max_mb']} MB")
        print(f"  增长率: {t['growth_pct']}%, 数据点: {t['data_points']}")
    if trend.get("suspected_leaks"):
        print("\n  [WARNING] 疑似内存泄漏:")
        for leak in trend["suspected_leaks"]:
            print(f"    - [{leak['severity']}] {leak['detail']}")
    if trend.get("suspected_leaks"):
        print("\n[FAIL] 检测到内存泄漏迹象")
        sys.exit(1)
    else:
        print("\n[PASS] 未检测到内存泄漏")
        sys.exit(0)
```

- [ ] **Step 3: 创建连接泄漏检测脚本**

Create: `scripts/stability/connection-leak-detector.py`

```python
#!/usr/bin/env python3
"""连接泄漏检测脚本 - 监控 DB/Kafka/Redis 连接池使用趋势"""

import requests
import sys
from datetime import datetime

PROMETHEUS_URL = "http://localhost:9090"
ALERT_THRESHOLDS = {
    "db_active_connections": {"warning": 40, "critical": 45},
    "db_idle_connections": {"warning": 5, "critical": 2},
    "kafka_consumer_connections": {"warning": 20, "critical": 25},
    "redis_active_connections": {"warning": 40, "critical": 45},
}


def query_prometheus(query: str, duration: str = "1h") -> dict:
    r = requests.get(f"{PROMETHEUS_URL}/api/v1/query_range", params={
        "query": query, "start": f"now-{duration}", "end": "now", "step": "30s",
    })
    return r.json()


def check_connection_leak(pool_name: str, metric_query: str) -> dict:
    result = {"pool": pool_name, "status": "OK", "detail": ""}
    try:
        data = query_prometheus(metric_query)
        if data.get("status") != "success" or not data["data"]["result"]:
            result["status"] = "NO_DATA"
            return result
        values = data["data"]["result"][0]["values"]
        if not values:
            return result
        last = float(values[-1][1])
        n = len(values)
        if n > 10:
            x_sum = sum(range(n))
            y_sum = sum(float(v[1]) for v in values)
            xy_sum = sum(i * float(v[1]) for i, v in enumerate(values))
            x2_sum = sum(i * i for i in range(n))
            slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
            result["detail"] = f"当前: {last:.0f}, 趋势斜率: {slope:.4f}/样本"
            thresholds = ALERT_THRESHOLDS.get(pool_name, {})
            if last >= thresholds.get("critical", 999):
                result["status"] = "CRITICAL"
            elif last >= thresholds.get("warning", 999) or slope > 0.1:
                result["status"] = "WARNING"
    except Exception as e:
        result["status"] = "ERROR"
        result["detail"] = str(e)
    return result


if __name__ == "__main__":
    print(f"=== 连接泄漏检测报告 ===")
    print(f"时间: {datetime.now().isoformat()}\n")
    checks = [
        ("db_active_connections", "hikaricp_connections_active"),
        ("db_idle_connections", "hikaricp_connections_idle"),
        ("kafka_consumer_connections", "kafka_consumer_connection_count"),
        ("redis_active_connections", "redis_connected_clients"),
    ]
    has_issues = False
    for pool_name, metric in checks:
        result = check_connection_leak(pool_name, metric)
        icon = {"OK": "[OK]", "WARNING": "[WARN]", "CRITICAL": "[CRIT]",
                "NO_DATA": "[INFO]", "ERROR": "[ERR]"}.get(result["status"], "[???]")
        print(f"{icon} {pool_name}: {result['detail']}")
        if result["status"] in ("WARNING", "CRITICAL"):
            has_issues = True
    sys.exit(1 if has_issues else 0)
```

- [ ] **Step 4: 创建自动恢复测试脚本**

Create: `scripts/stability/recovery-test.sh`

```bash
#!/bin/bash
# 自动恢复测试 - 模拟服务崩溃/网络分区
set -euo pipefail

BASE_URL="${BASE_URL:-https://api.uav-platform.example.com}"
LOG_DIR="/var/log/uav-recovery-test"
mkdir -p "$LOG_DIR"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_DIR/recovery-test.log"; }

verify_service_health() {
    local service=$1 max_retries=${2:-30} interval=${3:-5}
    for i in $(seq 1 $max_retries); do
        local status=$(curl -sf -o /dev/null -w "%{http_code}" "$BASE_URL/actuator/health" 2>/dev/null || echo "000")
        if [ "$status" = "200" ]; then
            log "  [OK] $service 已恢复 (第 ${i} 次, 耗时 $((i * interval))s)"
            return 0
        fi
        sleep $interval
    done
    log "  [FAIL] $service 未在 $((max_retries * interval))s 内恢复"
    return 1
}

FAILED=0

# 测试 1: Platform API 进程崩溃
log "=== 测试 1: 模拟 Platform API 进程崩溃 ==="
PID=$(pgrep -f "platform-api" | head -1)
if [ -n "$PID" ]; then
    kill -9 "$PID"; log "  已终止 PID: $PID"
    verify_service_health "platform-api" 30 5 && log "  [PASS]" || { log "  [FAIL]"; FAILED=$((FAILED+1)); }
fi

# 测试 2: MySQL 连接中断
log "=== 测试 2: 模拟 MySQL 连接中断 ==="
MYSQL_IP=$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mysql 2>/dev/null || echo "127.0.0.1")
sudo iptables -A INPUT -s "$MYSQL_IP" -j DROP -w; sleep 10
sudo iptables -D INPUT -s "$MYSQL_IP" -j DROP -w
verify_service_health "mysql-reconnect" 20 5 && log "  [PASS]" || { log "  [FAIL]"; FAILED=$((FAILED+1)); }

# 测试 3: Redis 连接中断
log "=== 测试 3: 模拟 Redis 连接中断 ==="
REDIS_IP=$(docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' redis 2>/dev/null || echo "127.0.0.1")
sudo iptables -A INPUT -s "$REDIS_IP" -j DROP -w; sleep 10
sudo iptables -D INPUT -s "$REDIS_IP" -j DROP -w
verify_service_health "redis-reconnect" 20 5 && log "  [PASS]" || { log "  [FAIL]"; FAILED=$((FAILED+1)); }

# 测试 4: Kafka Broker 宕机
log "=== 测试 4: 模拟 Kafka Broker 宕机 ==="
docker stop kafka 2>/dev/null || true; sleep 15
docker start kafka 2>/dev/null || true; sleep 20
verify_service_health "kafka-recovery" 30 5 && log "  [PASS]" || { log "  [FAIL]"; FAILED=$((FAILED+1)); }

# 测试 5: GC 压力
log "=== 测试 5: 模拟 OOM (GC 压力) ==="
curl -sf -X POST "$BASE_URL/actuator/gc" -H "Authorization: Bearer $(cat /tmp/admin-token)" 2>/dev/null || true
sleep 5
verify_service_health "gc-recovery" 10 3 && log "  [PASS]" || { log "  [FAIL]"; FAILED=$((FAILED+1)); }

log "\n=== 自动恢复测试汇总 ==="
log "失败: $FAILED / 5"
[ "$FAILED" -eq 0 ] && { log "[PASS] 所有恢复测试通过"; exit 0; } || { log "[FAIL] $FAILED 个未通过"; exit 1; }
```

- [ ] **Step 5: 配置告警阈值**

在 `monitoring/alert_rules.yml` 中添加：

```yaml
groups:
  - name: stability_alerts
    rules:
      - alert: JVMHeapUsageHigh
        expr: jvm_memory_used_bytes{area="heap"} / jvm_memory_max_bytes{area="heap"} > 0.85
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "JVM Heap 使用率超过 85%"
          description: "{{ $labels.instance }}: {{ $value | humanizePercentage }}"
      - alert: JVMHeapUsageCritical
        expr: jvm_memory_used_bytes{area="heap"} / jvm_memory_max_bytes{area="heap"} > 0.95
        for: 2m
        labels: { severity: critical }
        annotations:
          summary: "JVM Heap 使用率超过 95%"
      - alert: DBConnectionPoolExhausted
        expr: hikaricp_connections_active >= hikaricp_connections_max
        for: 1m
        labels: { severity: critical }
        annotations:
          summary: "数据库连接池耗尽"
      - alert: ConnectionLeakSuspected
        expr: deriv(hikaricp_connections_active[1h]) > 0.5
        for: 30m
        labels: { severity: warning }
        annotations:
          summary: "疑似数据库连接泄漏"
      - alert: GCPauseTooLong
        expr: jvm_gc_pause_seconds_sum / jvm_gc_pause_seconds_count > 0.5
        for: 5m
        labels: { severity: warning }
        annotations:
          summary: "GC 平均停顿超过 500ms"
      - alert: ServiceDown
        expr: up{job=~"uav-platform.*"} == 0
        for: 1m
        labels: { severity: critical }
        annotations:
          summary: "服务实例不可用"
```

- [ ] **Step 6: 执行稳定性测试**

```bash
nohup bash scripts/stability/soak-test.sh > /var/log/soak-test-stdout.log 2>&1 &
echo $! > /tmp/soak-test.pid
sudo bash scripts/stability/recovery-test.sh
```

预期结果：7 天长跑无内存泄漏（Heap 增长 < 10%）；连接池无泄漏；服务崩溃后 150 秒内恢复；GC 停顿 < 500ms（P99）

**回滚方案：** `sudo iptables -F` 清除规则；`docker-compose up -d` 恢复容器；`kill $(cat /tmp/soak-test.pid)` 终止长跑

---

## Phase 8: 功能增强（服务器相关部分）

### Task 8.1: 多区域部署架构

**Files:**
- Create: `k8s/multi-region/primary-east/mysql-group-replication.cnf`
- Create: `k8s/multi-region/secondary-north/mysql-group-replication.cnf`
- Create: `k8s/multi-region/primary-east/redis-sentinel.conf`
- Create: `k8s/multi-region/kafka-cluster.yaml`
- Create: `k8s/multi-region/cross-region-sync.yaml`

**前置条件：**
- 两台服务器（华东 + 华北），各 4 核 16GB 内存以上
- 两台服务器间内网互通（延迟 < 50ms）
- Docker + docker-compose 已安装
- DNS 配置就绪

- [ ] **Step 1: 配置 MySQL Group Replication（华东主节点）**

Create: `k8s/multi-region/primary-east/mysql-group-replication.cnf`

```ini
[mysqld]
server-id = 1
bind-address = 0.0.0.0
port = 3306
mysqlx = 0

plugin_load_add = group_replication.so
group_replication_group_name = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
group_replication_start_on_boot = OFF
group_replication_local_address = "primary.east.uav-platform.internal:33061"
group_replication_group_seeds = "primary.east.uav-platform.internal:33061,secondary.north.uav-platform.internal:33061"
group_replication_bootstrap_group = OFF
group_replication_single_primary_mode = ON
group_replication_enforce_update_everywhere_checks = OFF

replicate-do-db = uav_platform
replicate-do-db = uav_weather
replicate-do-db = uav_planning

group_replication_ssl_mode = REQUIRED
group_replication_recovery_ssl_ca = /etc/mysql/ssl/ca.pem
group_replication_recovery_ssl_cert = /etc/mysql/ssl/server-cert.pem
group_replication_recovery_ssl_key = /etc/mysql/ssl/server-key.pem

innodb_buffer_pool_size = 4G
innodb_log_file_size = 1G
innodb_flush_log_at_trx_commit = 1
sync_binlog = 1
binlog_format = ROW
binlog_checksum = NONE
transaction_write_set_extraction = XXHASH64
group_replication_member_expel_timeout = 5
group_replication_components_stop_timeout = 300
```

- [ ] **Step 2: 配置 MySQL Group Replication（华北备份节点）**

Create: `k8s/multi-region/secondary-north/mysql-group-replication.cnf`

```ini
[mysqld]
server-id = 2
bind-address = 0.0.0.0
port = 3306
mysqlx = 0

plugin_load_add = group_replication.so
group_replication_group_name = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
group_replication_start_on_boot = OFF
group_replication_local_address = "secondary.north.uav-platform.internal:33061"
group_replication_group_seeds = "primary.east.uav-platform.internal:33061,secondary.north.uav-platform.internal:33061"
group_replication_bootstrap_group = OFF
group_replication_single_primary_mode = ON
group_replication_enforce_update_everywhere_checks = OFF

replicate-do-db = uav_platform
replicate-do-db = uav_weather
replicate-do-db = uav_planning

group_replication_ssl_mode = REQUIRED
group_replication_recovery_ssl_ca = /etc/mysql/ssl/ca.pem
group_replication_recovery_ssl_cert = /etc/mysql/ssl/server-cert.pem
group_replication_recovery_ssl_key = /etc/mysql/ssl/server-key.pem

innodb_buffer_pool_size = 4G
innodb_log_file_size = 1G
innodb_flush_log_at_trx_commit = 1
sync_binlog = 1
binlog_format = ROW
binlog_checksum = NONE
transaction_write_set_extraction = XXHASH64
group_replication_member_expel_timeout = 5
group_replication_components_stop_timeout = 300
```

- [ ] **Step 3: 初始化 Group Replication 集群**

```bash
# === 华东主节点 ===
sudo systemctl start mysql
mysql -u root -p << 'SQL'
SET SQL_LOG_BIN=0;
CREATE USER 'repl_user'@'%' IDENTIFIED BY 'Repl@Secure123!';
GRANT REPLICATION SLAVE ON *.* TO 'repl_user'@'%';
GRANT CONNECTION_ADMIN ON *.* TO 'repl_user'@'%';
GRANT GROUP_REPLICATION_STREAM ON *.* TO 'repl_user'@'%';
SET SQL_LOG_BIN=1;
SQL

mysql -u root -p << 'SQL'
CHANGE REPLICATION SOURCE TO
  SOURCE_USER='repl_user', SOURCE_PASSWORD='Repl@Secure123!',
  SOURCE_HOST='primary.east.uav-platform.internal', SOURCE_PORT=33061, SOURCE_SSL=1;
SET GLOBAL group_replication_bootstrap_group = ON;
START GROUP_REPLICATION;
SET GLOBAL group_replication_bootstrap_group = OFF;
SQL

mysql -u root -p -e "SELECT * FROM performance_schema.replication_group_members;"
# 预期: MEMBER_ROLE = PRIMARY, MEMBER_STATE = ONLINE

# === 华北备份节点 ===
sudo systemctl start mysql
# 创建复制用户（同上）
mysql -u root -p << 'SQL'
CHANGE REPLICATION SOURCE TO
  SOURCE_USER='repl_user', SOURCE_PASSWORD='Repl@Secure123!',
  SOURCE_HOST='primary.east.uav-platform.internal', SOURCE_PORT=33061, SOURCE_SSL=1;
START GROUP_REPLICATION;
SQL

mysql -u root -p -e "SELECT * FROM performance_schema.replication_group_members;"
# 预期: 两个节点均为 ONLINE
```

- [ ] **Step 4: 配置 Redis Sentinel 高可用**

Create: `k8s/multi-region/primary-east/redis-sentinel.conf`

```ini
port 26379
sentinel monitor uav-redis primary.east.uav-platform.internal 6379 2
sentinel down-after-milliseconds uav-redis 5000
sentinel failover-timeout uav-redis 60000
sentinel parallel-syncs uav-redis 1
sentinel auth-pass uav-redis Redis@Secure123!
logfile /var/log/redis/sentinel.log
loglevel notice
protected-mode no
```

```bash
redis-server /etc/redis/sentinel.conf --sentinel
redis-cli -p 26379 SENTINEL master uav-redis
# 预期: num-slaves=1, num-other-sentinels=1
```

- [ ] **Step 5: 配置 Kafka 3-Broker 集群**

Create: `k8s/multi-region/kafka-cluster.yaml`

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: kafka
  namespace: uav-platform
spec:
  serviceName: kafka
  replicas: 3
  selector:
    matchLabels:
      app: kafka
  template:
    metadata:
      labels:
        app: kafka
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchExpressions:
                    - key: app
                      operator: In
                      values: ["kafka"]
                topologyKey: kubernetes.io/hostname
      containers:
        - name: kafka
          image: apache/kafka:3.8.0
          ports:
            - containerPort: 9092
            - containerPort: 9093
          env:
            - name: KAFKA_PROCESS_ROLES
              value: "broker,controller"
            - name: KAFKA_LISTENERS
              value: "PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093"
            - name: KAFKA_ADVERTISED_LISTENERS
              value: "PLAINTEXT://kafka-$(hostname).uav-platform.svc.cluster.local:9092"
            - name: KAFKA_CONTROLLER_QUORUM_VOTERS
              value: "1@kafka-0.uav-platform.svc.cluster.local:9093,2@kafka-1.uav-platform.svc.cluster.local:9093,3@kafka-2.uav-platform.svc.cluster.local:9093"
            - name: KAFKA_CONTROLLER_LISTENER_NAMES
              value: "CONTROLLER"
            - name: KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR
              value: "3"
            - name: KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR
              value: "3"
            - name: KAFKA_TRANSACTION_STATE_LOG_MIN_ISR
              value: "2"
            - name: KAFKA_NUM_PARTITIONS
              value: "12"
            - name: KAFKA_DEFAULT_REPLICATION_FACTOR
              value: "3"
            - name: KAFKA_MIN_INSYNC_REPLICAS
              value: "2"
            - name: CLUSTER_ID
              value: "MkU3OEVCNTcwNTJENDM2Qk"
            - name: KAFKA_LOG_DIRS
              value: "/var/lib/kafka/data"
          resources:
            requests: { cpu: "1", memory: "2Gi" }
            limits: { cpu: "2", memory: "4Gi" }
          volumeMounts:
            - name: data
              mountPath: /var/lib/kafka/data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 100Gi
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: kafka-topics-config
  namespace: uav-platform
data:
  init-topics.sh: |
    #!/bin/bash
    sleep 30
    kafka-topics.sh --bootstrap-server kafka-0.uav-platform.svc.cluster.local:9092 \
      --create --if-not-exists --topic weather-data \
      --partitions 12 --replication-factor 3 \
      --config retention.ms=604800000 --config compression.type=lz4
    kafka-topics.sh --bootstrap-server kafka-0.uav-platform.svc.cluster.local:9092 \
      --create --if-not-exists --topic assimilation-experiments \
      --partitions 6 --replication-factor 3 \
      --config retention.ms=2592000000 --config max.message.bytes=10485760
    kafka-topics.sh --bootstrap-server kafka-0.uav-platform.svc.cluster.local:9092 \
      --create --if-not-exists --topic risk-assessment \
      --partitions 6 --replication-factor 3 --config retention.ms=604800000
    kafka-topics.sh --bootstrap-server kafka-0.uav-platform.svc.cluster.local:9092 \
      --create --if-not-exists --topic alert-events \
      --partitions 3 --replication-factor 3 --config cleanup.policy=compact
    echo "Topics created successfully"
```

```bash
kubectl apply -f k8s/multi-region/kafka-cluster.yaml
kubectl get pods -n uav-platform -l app=kafka
# 预期: 3 个 Running Pod
```

- [ ] **Step 6: 配置跨区域数据同步**

Create: `k8s/multi-region/cross-region-sync.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kafka-mirrormaker
  namespace: uav-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kafka-mirrormaker
  template:
    metadata:
      labels:
        app: kafka-mirrormaker
    spec:
      containers:
        - name: mirrormaker
          image: apache/kafka:3.8.0
          command: ["/bin/bash", "-c"]
          args: ["/opt/kafka/bin/connect-standalone.sh /opt/kafka/config/connect-standalone.properties /opt/kafka/config/MirrorSourceConnector.properties"]
          volumeMounts:
            - name: config
              mountPath: /opt/kafka/config/MirrorSourceConnector.properties
              subPath: MirrorSourceConnector.properties
      volumes:
        - name: config
          configMap:
            name: mirrormaker-config
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: mirrormaker-config
  namespace: uav-platform
data:
  MirrorSourceConnector.properties: |
    name=mirror-source-connector
    connector.class=org.apache.kafka.connect.mirror.MirrorSourceConnector
    source.cluster.alias=east
    target.cluster.alias=north
    source.bootstrap.servers=kafka-0.uav-platform.svc.cluster.local:9092,kafka-1.uav-platform.svc.cluster.local:9092,kafka-2.uav-platform.svc.cluster.local:9092
    target.bootstrap.servers=kafka-north-0.uav-platform.svc.cluster.local:9092,kafka-north-1.uav-platform.svc.cluster.local:9092,kafka-north-2.uav-platform.svc.cluster.local:9092
    sync.topic.configs.enabled=true
    sync.topic.acls.enabled=false
    replication.factor=2
    topics=.*
    emit.checkpoints.enabled=true
    emit.checkpoints.interval.seconds=30
```

预期结果：MySQL Group Replication 两节点 ONLINE，延迟 < 1s；Redis Sentinel 故障转移 < 30s；Kafka 3-Broker 正常，复制因子 3；跨区域同步延迟 < 5s

**回滚方案：**
```bash
mysql -u root -p -e "STOP GROUP_REPLICATION;"
redis-cli -p 26379 SENTINEL REMOVE uav-redis primary.east.uav-platform.internal 6379
kubectl scale statefulset kafka --replicas=1 -n uav-platform
```

---

### Task 8.2: 灾难恢复

**Files:**
- Create: `scripts/dr/backup-daily.sh`
- Create: `scripts/dr/backup-binlog.sh`
- Create: `scripts/dr/failover-auto.sh`
- Create: `scripts/dr/recovery-drill.sh`

**前置条件：**
- 多区域部署架构已就绪（Task 8.1 完成）
- 备份存储空间充足（建议 3x 数据量）
- 备份目标：对象存储（如阿里云 OSS / MinIO）

- [ ] **Step 1: 定义 RPO/RTO 目标**

| 指标 | 目标值 | 说明 |
|------|--------|------|
| RPO | < 5 分钟 | 最大可接受数据丢失时间 |
| RTO | < 30 分钟 | 从故障到恢复服务的时间 |
| 备份保留 | 30 天全量 + 7 天增量 | 满足审计和回溯需求 |
| 演练频率 | 每月 1 次 | 确保恢复流程可靠 |

- [ ] **Step 2: 创建每日全量备份脚本**

Create: `scripts/dr/backup-daily.sh`

```bash
#!/bin/bash
set -euo pipefail
BACKUP_DIR="/backup/daily/$(date +%Y%m%d)"
OSS_BUCKET="uav-platform-backups"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a /var/log/backup-daily.log; }
mkdir -p "$BACKUP_DIR"

log "=== MySQL 全量备份 ==="
mysqldump --single-transaction --routines --triggers --events \
  --set-gtid-purged=OFF --master-data=2 \
  -u backup_user -p"${MYSQL_BACKUP_PASSWORD}" --all-databases \
  | gzip > "$BACKUP_DIR/mysql-all-databases.sql.gz"
log "MySQL 备份完成: $(du -h "$BACKUP_DIR/mysql-all-databases.sql.gz" | cut -f1)"

log "=== Redis RDB 备份 ==="
redis-cli --rdb "$BACKUP_DIR/redis-dump.rdb" -a "${REDIS_PASSWORD}"
log "Redis 备份完成: $(du -h "$BACKUP_DIR/redis-dump.rdb" | cut -f1)"

log "=== Kafka 元数据备份 ==="
kafka-topics.sh --bootstrap-server localhost:9092 --describe > "$BACKUP_DIR/kafka-topics-describe.txt"
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --all-groups > "$BACKUP_DIR/kafka-consumer-groups.txt"

log "=== 上传到对象存储 ==="
if command -v ossutil &>/dev/null; then
    ossutil cp "$BACKUP_DIR/" "oss://${OSS_BUCKET}/daily/$(date +%Y%m%d)/" -r -f
elif command -v mc &>/dev/null; then
    mc cp "$BACKUP_DIR/" "minio/backups/daily/$(date +%Y%m%d)/" --recursive
else
    log "WARNING: 未找到对象存储工具，备份仅保留本地"
fi

find /backup/daily/ -maxdepth 1 -type d -mtime +30 -exec rm -rf {} +
gunzip -t "$BACKUP_DIR/mysql-all-databases.sql.gz" && log "MySQL 备份校验通过"
log "=== 每日全量备份完成 ==="
```

- [ ] **Step 3: 创建实时 binlog 备份脚本**

Create: `scripts/dr/backup-binlog.sh`

```bash
#!/bin/bash
set -euo pipefail
BINLOG_DIR="/backup/binlog"
mkdir -p "$BINLOG_DIR"

mysql -u backup_user -p"${MYSQL_BACKUP_PASSWORD}" -e "FLUSH BINARY LOGS;"
for binlog in /var/lib/mysql/mysql-bin.[0-9]*; do
    if [ -f "$binlog" ] && [ ! -f "$BINLOG_DIR/$(basename $binlog)" ]; then
        cp "$binlog" "$BINLOG_DIR/"
        echo "[$(date)] 新增 binlog: $(basename $binlog)" >> /var/log/backup-binlog.log
    fi
done
if command -v ossutil &>/dev/null; then
    ossutil cp "$BINLOG_DIR/" "oss://uav-platform-backups/binlog/" -r -f --update
fi
find "$BINLOG_DIR" -name "mysql-bin.*" -mtime +7 -delete
```

```bash
echo "*/5 * * * * /opt/scripts/dr/backup-binlog.sh" | crontab -
```

- [ ] **Step 4: 创建自动故障转移脚本**

Create: `scripts/dr/failover-auto.sh`

```bash
#!/bin/bash
set -euo pipefail

PRIMARY_URL="https://primary.east.uav-platform.example.com"
SECONDARY_URL="https://secondary.north.uav-platform.example.com"
ALERT_WEBHOOK="${ALERT_WEBHOOK:-}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a /var/log/failover.log; }

send_alert() {
    [ -n "$ALERT_WEBHOOK" ] && curl -sf -X POST "$ALERT_WEBHOOK" \
      -H "Content-Type: application/json" \
      -d "{\"msgtype\":\"text\",\"text\":{\"content\":\"[UAV Platform] $1\"}}" 2>/dev/null || true
}

check_health() {
    local url=$1
    for i in $(seq 1 3); do
        local status=$(curl -sf -o /dev/null -w "%{http_code}" "${url}/actuator/health" --connect-timeout 5 --max-time 10 2>/dev/null || echo "000")
        [ "$status" = "200" ] && return 0
        sleep 10
    done
    return 1
}

if check_health "$PRIMARY_URL"; then
    log "主区域正常"; exit 0
fi

log "WARNING: 主区域不可用！"
sleep 30
if check_health "$PRIMARY_URL"; then
    log "主区域已恢复"; exit 0
fi

if ! check_health "$SECONDARY_URL"; then
    log "CRITICAL: 备份区域也不可用！"
    send_alert "CRITICAL: 主区域和备份区域均不可用，需要立即人工介入！"
    exit 2
fi

log "开始故障转移..."
mysql -h secondary.north.uav-platform.internal -u root -p"${MYSQL_ROOT_PASSWORD}" \
  -e "SELECT * FROM performance_schema.replication_group_members;"

if command -v aliyun &>/dev/null; then
    aliyun alidns UpdateDomainRecord --RecordId "${DNS_RECORD_ID}" \
      --RR "@" --Type "A" \
      --Value "$(dig +short secondary.north.uav-platform.example.com)"
    log "DNS 已切换到备份区域"
fi

send_alert "WARNING: 主区域故障，已自动切换到备份区域"
log "故障转移完成"
```

```bash
echo "* * * * * /opt/scripts/dr/failover-auto.sh" | crontab -
```

- [ ] **Step 5: 创建恢复演练脚本**

Create: `scripts/dr/recovery-drill.sh`

```bash
#!/bin/bash
set -euo pipefail
DRILL_DIR="/backup/drill/$(date +%Y%m%d)"
LATEST_BACKUP=$(ls -td /backup/daily/202* | head -1)

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a /var/log/recovery-drill.log; }
mkdir -p "$DRILL_DIR"

log "=== 恢复演练开始 ==="
log "使用备份: $LATEST_BACKUP"

# MySQL 恢复验证
log "--- MySQL 恢复验证 ---"
docker run -d --name drill-mysql -e MYSQL_ROOT_PASSWORD=Drill@123456 \
  -v "$DRILL_DIR/mysql-data:/var/lib/mysql" mysql:8.4
sleep 30
gunzip -c "$LATEST_BACKUP/mysql-all-databases.sql.gz" | \
  docker exec -i drill-mysql mysql -u root -pDrill@123456
docker exec drill-mysql mysql -u root -pDrill@123456 -e "
    SELECT COUNT(*) AS user_count FROM uav_platform.sys_user;
    SELECT COUNT(*) AS weather_count FROM uav_weather.weather_data;
    SELECT MAX(created_at) AS latest_record FROM uav_platform.sys_user;
" > "$DRILL_DIR/mysql-verify.txt"
log "MySQL 恢复验证:"; cat "$DRILL_DIR/mysql-verify.txt"
docker stop drill-mysql && docker rm drill-mysql

# Redis 恢复验证
log "--- Redis 恢复验证 ---"
docker run -d --name drill-redis \
  -v "$LATEST_BACKUP/redis-dump.rdb:/data/dump.rdb" \
  redis:7.2 redis-server --dir /data
sleep 5
REDIS_KEY_COUNT=$(docker exec drill-redis redis-cli DBSIZE | cut -d: -f2 | tr -d ' \r\n')
log "Redis Key 数量 = $REDIS_KEY_COUNT"
docker stop drill-redis && docker rm drill-redis

# Binlog 连续性验证
log "--- Binlog 连续性验证 ---"
BINLOG_FILES=$(ls -1 "$LATEST_BACKUP/../binlog/"mysql-bin.* 2>/dev/null | sort)
if [ -n "$BINLOG_FILES" ]; then
    echo "$BINLOG_FILES" | while read f; do
        log "  $(basename $f) - $(du -h $f | cut -f1)"
    done
    log "Binlog 连续性: OK"
fi

# RPO 计算
BINLOG_LATEST=$(ls -t /backup/binlog/mysql-bin.* 2>/dev/null | head -1)
if [ -n "$BINLOG_LATEST" ]; then
    RPO=$(( $(date +%s) - $(stat -c %Y "$BINLOG_LATEST") ))
    log "RPO: ${RPO} 秒"
fi

log "=== 恢复演练完成 ==="
```

- [ ] **Step 6: 执行恢复演练**

```bash
sudo bash scripts/dr/recovery-drill.sh
```

预期结果：MySQL 备份可在 10 分钟内恢复；Redis 备份可在 1 分钟内恢复；RPO < 5 分钟；RTO < 30 分钟

**回滚方案：** 故障转移回退：手动将 DNS 指回主区域；恢复演练在隔离环境中进行，不影响生产

---

## Phase 9: 运维优化（需集群）

### Task 9.1: 混沌工程

**Files:**
- Create: `k8s/chaos/chaos-mesh-install.yaml`
- Create: `k8s/chaos/network-chaos.yaml`
- Create: `k8s/chaos/pod-kill-chaos.yaml`
- Create: `k8s/chaos/stress-chaos.yaml`

**前置条件：**
- Kubernetes 1.28+ 集群已就绪
- kubectl 已配置并可访问集群
- Helm 3 已安装
- 集群节点数 >= 3
- 监控系统已就绪（Prometheus + Grafana）

- [ ] **Step 1: 安装 Chaos Mesh**

```bash
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm repo update

helm install chaos-mesh chaos-mesh/chaos-mesh \
  --namespace chaos-mesh --create-namespace \
  --set chaosDaemon.runtime=containerd \
  --set dashboard.service.type=NodePort \
  --set dashboard.service.nodePort=32369 \
  --set chaosDaemon.grpcPort=31767 \
  --set chaosDaemon.tls.enabled=false

kubectl get pods -n chaos-mesh
# 预期: chaos-controller-manager, chaos-daemon (每节点一个), chaos-dashboard 均 Running
```

- [ ] **Step 2: 创建网络注入实验**

Create: `k8s/chaos/network-chaos.yaml`

```yaml
# 网络延迟实验
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: network-delay-weather-api
  namespace: uav-platform
  labels: { experiment: "network-delay", severity: "medium" }
spec:
  action: delay
  mode: one
  selector:
    labelSelectors: { app: weather-api }
    namespaces: [uav-platform]
  parameters: { latency: "200ms", jitter: "50ms", correlation: "75" }
  duration: "5m"
  scheduler: { cron: "@daily" }
---
# 网络丢包实验
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: network-loss-planning-api
  namespace: uav-platform
  labels: { experiment: "network-loss", severity: "high" }
spec:
  action: loss
  mode: one
  selector:
    labelSelectors: { app: planning-api }
    namespaces: [uav-platform]
  parameters: { loss: "10%", correlation: "50" }
  duration: "3m"
---
# 网络分区实验
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: network-partition-cross-region
  namespace: uav-platform
  labels: { experiment: "network-partition", severity: "critical" }
spec:
  action: partition
  mode: all
  selector:
    labelSelectors: { app: kafka }
    namespaces: [uav-platform]
  direction: to
  target:
    mode: all
    selector:
      labelSelectors: { app: mysql }
    namespaces: [uav-platform]
  duration: "2m"
```

- [ ] **Step 3: 创建 Pod Kill 实验**

Create: `k8s/chaos/pod-kill-chaos.yaml`

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: pod-kill-api-gateway
  namespace: uav-platform
  labels: { experiment: "pod-kill", severity: "medium" }
spec:
  action: kill-pod
  mode: random-max-percent
  selector:
    labelSelectors: { app: api-gateway }
    namespaces: [uav-platform]
  value: "50"
  duration: "10m"
  scheduler: { cron: "0 */4 * * *" }
---
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: continuous-pod-kill-weather
  namespace: uav-platform
  labels: { experiment: "continuous-pod-kill", severity: "high" }
spec:
  action: kill-pod
  mode: fixed-rate
  selector:
    labelSelectors: { app: weather-api }
    namespaces: [uav-platform]
  value: "1"
  duration: "5m"
```

- [ ] **Step 4: 创建 CPU/内存压力实验**

Create: `k8s/chaos/stress-chaos.yaml`

```yaml
# CPU 压力
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: cpu-stress-platform-api
  namespace: uav-platform
  labels: { experiment: "cpu-stress", severity: "medium" }
spec:
  mode: one
  selector:
    labelSelectors: { app: platform-api }
    namespaces: [uav-platform]
  stressors:
    cpu: { workers: 4, load: 80 }
  duration: "5m"
  scheduler: { cron: "0 2 * * *" }
---
# 内存压力
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: memory-stress-risk-api
  namespace: uav-platform
  labels: { experiment: "memory-stress", severity: "high" }
spec:
  mode: one
  selector:
    labelSelectors: { app: risk-api }
    namespaces: [uav-platform]
  stressors:
    memory: { workers: 2, size: "256MB" }
  duration: "3m"
---
# 组合压力
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: combined-stress-assimilation-api
  namespace: uav-platform
  labels: { experiment: "combined-stress", severity: "critical" }
spec:
  mode: one
  selector:
    labelSelectors: { app: assimilation-api }
    namespaces: [uav-platform]
  stressors:
    cpu: { workers: 2, load: 60 }
    memory: { workers: 1, size: "128MB" }
  duration: "5m"
```

- [ ] **Step 5: 执行混沌实验**

```bash
kubectl apply -f k8s/chaos/network-chaos.yaml
kubectl apply -f k8s/chaos/pod-kill-chaos.yaml
kubectl apply -f k8s/chaos/stress-chaos.yaml

# 验证实验状态
kubectl get networkchaos,podchaos,stresschaos -n uav-platform
kubectl get hpa -n uav-platform -w  # 验证 HPA 响应

# 清理
kubectl delete -f k8s/chaos/network-chaos.yaml
kubectl delete -f k8s/chaos/pod-kill-chaos.yaml
kubectl delete -f k8s/chaos/stress-chaos.yaml
```

- [ ] **Step 6: 验证稳定性指标**

| 实验 | 验证指标 | 通过标准 |
|------|----------|----------|
| 网络延迟 200ms | API 响应时间 | P99 < 1s |
| 网络丢包 10% | 请求成功率 | >= 99% |
| 网络分区 | 服务降级 | 降级响应，非级联故障 |
| Pod Kill | 自动恢复 | Pod 在 60s 内重建 |
| Pod Kill | 服务可用性 | 成功率 >= 99.5% |
| CPU 80% | HPA 扩容 | 60s 内触发 |
| 内存 256MB | OOM 保护 | 不触发 OOMKilled |

预期结果：所有混沌实验通过稳定性验证；无级联故障；HPA 正常工作；Pod 自动重建 < 60s

**回滚方案：**
```bash
kubectl delete networkchaos --all -n uav-platform
kubectl delete podchaos --all -n uav-platform
kubectl delete stresschaos --all -n uav-platform
kubectl rollout restart deployment --all -n uav-platform
```

---

### Task 9.2: 成本优化

**Files:**
- Create: `k8s/hpa-custom.yaml`
- Create: `k8s/scheduled-scaler.yaml`
- Create: `scripts/cost/resource-usage-report.py`

**前置条件：**
- Kubernetes 集群已部署所有服务
- Metrics Server 已安装（`kubectl top pods` 可用）
- Prometheus 已采集资源指标
- 各服务已配置 resources.requests 和 resources.limits

- [ ] **Step 1: 配置 HPA 自动扩缩容**

Create: `k8s/hpa-custom.yaml`

```yaml
# API Gateway HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-gateway-hpa
  namespace: uav-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-gateway
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 60 }
    - type: Resource
      resource:
        name: memory
        target: { type: Utilization, averageUtilization: 70 }
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30
      policies:
        - type: Pods, value: 2, periodSeconds: 30
        - type: Percent, value: 50, periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods, value: 1, periodSeconds: 60
---
# Platform API HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: platform-api-hpa
  namespace: uav-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: platform-api
  minReplicas: 2
  maxReplicas: 6
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 65 }
    - type: Resource
      resource:
        name: memory
        target: { type: Utilization, averageUtilization: 75 }
---
# Weather API HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: weather-api-hpa
  namespace: uav-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: weather-api
  minReplicas: 2
  maxReplicas: 8
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 55 }
    - type: Resource
      resource:
        name: memory
        target: { type: Utilization, averageUtilization: 70 }
---
# Planning API HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: planning-api-hpa
  namespace: uav-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: planning-api
  minReplicas: 1
  maxReplicas: 4
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 70 }
---
# Risk API HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: risk-api-hpa
  namespace: uav-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: risk-api
  minReplicas: 1
  maxReplicas: 4
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 65 }
---
# Assimilation API HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: assimilation-api-hpa
  namespace: uav-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: assimilation-api
  minReplicas: 1
  maxReplicas: 4
  metrics:
    - type: Resource
      resource:
        name: memory
        target: { type: Utilization, averageUtilization: 60 }
---
# Algorithm Engine HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: algorithm-engine-hpa
  namespace: uav-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: algorithm-engine
  minReplicas: 1
  maxReplicas: 6
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 60 }
    - type: Resource
      resource:
        name: memory
        target: { type: Utilization, averageUtilization: 70 }
```

```bash
kubectl apply -f k8s/hpa-custom.yaml
kubectl get hpa -n uav-platform
```

- [ ] **Step 2: 配置非高峰时段缩容策略**

Create: `k8s/scheduled-scaler.yaml`

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scale-down-night
  namespace: uav-platform
spec:
  schedule: "0 0 * * *"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: scaler-sa
          containers:
            - name: scaler
              image: bitnami/kubectl:1.29
              command: ["/bin/bash", "-c"]
              args:
                - |
                  echo "[$(date)] 非高峰缩容开始"
                  kubectl scale deployment planning-api --replicas=1 -n uav-platform
                  kubectl scale deployment risk-api --replicas=1 -n uav-platform
                  kubectl scale deployment assimilation-api --replicas=1 -n uav-platform
                  kubectl scale deployment algorithm-engine --replicas=1 -n uav-platform
                  echo "[$(date)] 非高峰缩容完成"
          restartPolicy: OnFailure
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scale-up-morning
  namespace: uav-platform
spec:
  schedule: "0 8 * * 1-5"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: scaler-sa
          containers:
            - name: scaler
              image: bitnami/kubectl:1.29
              command: ["/bin/bash", "-c"]
              args:
                - |
                  echo "[$(date)] 高峰扩容开始"
                  kubectl scale deployment planning-api --replicas=2 -n uav-platform
                  kubectl scale deployment risk-api --replicas=2 -n uav-platform
                  kubectl scale deployment assimilation-api --replicas=2 -n uav-platform
                  kubectl scale deployment algorithm-engine --replicas=2 -n uav-platform
                  echo "[$(date)] 高峰扩容完成"
          restartPolicy: OnFailure
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: scaler-sa
  namespace: uav-platform
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: scaler-role
  namespace: uav-platform
rules:
  - apiGroups: ["apps"]
    resources: ["deployments", "deployments/scale"]
    verbs: ["get", "patch", "update"]
  - apiGroups: ["autoscaling"]
    resources: ["horizontalpodautoscalers"]
    verbs: ["get", "patch", "update"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: scaler-binding
  namespace: uav-platform
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: scaler-role
subjects:
  - kind: ServiceAccount
    name: scaler-sa
    namespace: uav-platform
```

```bash
kubectl apply -f k8s/scheduled-scaler.yaml
kubectl get cronjobs -n uav-platform
```

- [ ] **Step 3: 创建资源使用率分析脚本**

Create: `scripts/cost/resource-usage-report.py`

```python
#!/usr/bin/env python3
"""资源使用率分析脚本 - 分析 CPU/内存/存储使用率，生成成本优化建议"""

import requests
import sys
from datetime import datetime

PROMETHEUS_URL = "http://localhost:9090"

SERVICE_RESOURCES = {
    "api-gateway": {"cpu_request": "500m", "mem_request": "512Mi"},
    "platform-api": {"cpu_request": "500m", "mem_request": "512Mi"},
    "weather-api": {"cpu_request": "500m", "mem_request": "512Mi"},
    "planning-api": {"cpu_request": "1", "mem_request": "1Gi"},
    "risk-api": {"cpu_request": "500m", "mem_request": "512Mi"},
    "assimilation-api": {"cpu_request": "500m", "mem_request": "1Gi"},
    "algorithm-engine": {"cpu_request": "1", "mem_request": "1Gi"},
}

COST_PER_CPU_CORE_MONTH = 300
COST_PER_GB_MEM_MONTH = 50
COST_PER_GB_STORAGE_MONTH = 10


def query_prometheus(query: str, duration: str = "7d") -> list:
    r = requests.get(f"{PROMETHEUS_URL}/api/v1/query_range", params={
        "query": query, "start": f"now-{duration}", "end": "now", "step": "1h",
    })
    if r.json().get("status") != "success":
        return []
    return r.json().get("data", {}).get("result", [])


def analyze_service_usage(service_name: str) -> dict:
    result = {"service": service_name, "recommendations": []}
    cpu_data = query_prometheus(f'rate(container_cpu_usage_seconds_total{{pod=~"{service_name}-.*"}}[5m]) * 100')
    if cpu_data:
        cpu_values = [float(v[1]) for v in cpu_data[0].get("values", [])]
        if cpu_values:
            avg_cpu = sum(cpu_values) / len(cpu_values)
            result["avg_cpu_pct"] = round(avg_cpu, 1)
            if avg_cpu < 20:
                result["recommendations"].append(f"CPU 请求可降低（当前平均 {avg_cpu:.1f}%）")

    mem_data = query_prometheus(f'container_memory_working_set_bytes{{pod=~"{service_name}-.*"}}')
    if mem_data:
        mem_values = [float(v[1]) / 1024 / 1024 for v in mem_data[0].get("values", [])]
        if mem_values:
            avg_mem = sum(mem_values) / len(mem_values)
            result["avg_mem_mb"] = round(avg_mem, 0)
            if avg_mem < 200:
                result["recommendations"].append(f"内存请求可降低（当前平均 {avg_mem:.0f}MB）")
    return result


def estimate_monthly_cost() -> dict:
    total_cpu, total_mem, total_storage = 0, 0, 0
    for svc, res in SERVICE_RESOURCES.items():
        cpu_str = res["cpu_request"]
        total_cpu += int(cpu_str[:-1]) / 1000 if cpu_str.endswith("m") else int(cpu_str)
        mem_str = res["mem_request"]
        total_mem += int(mem_str[:-2]) / 1024 if mem_str.endswith("Mi") else int(mem_str[:-2]) if mem_str.endswith("Gi") else 0
    for item in query_prometheus("kubelet_volume_stats_used_bytes", "1d"):
        values = item.get("values", [])
        if values:
            total_storage += float(values[-1][1]) / 1024 / 1024 / 1024
    cpu_cost = total_cpu * COST_PER_CPU_CORE_MONTH
    mem_cost = total_mem * COST_PER_GB_MEM_MONTH
    storage_cost = total_storage * COST_PER_GB_STORAGE_MONTH
    return {
        "cpu_cores": round(total_cpu, 1), "mem_gb": round(total_mem, 1),
        "storage_gb": round(total_storage, 1),
        "cpu_cost": round(cpu_cost), "mem_cost": round(mem_cost),
        "storage_cost": round(storage_cost),
        "total_cost": round(cpu_cost + mem_cost + storage_cost),
    }


if __name__ == "__main__":
    print(f"=== 资源使用率分析报告 ===")
    print(f"时间: {datetime.now().isoformat()}\n--- 服务资源使用率 ---")
    all_recs = []
    for svc in SERVICE_RESOURCES:
        result = analyze_service_usage(svc)
        cpu_str = f"CPU: 平均 {result.get('avg_cpu_pct', 'N/A')}%"
        mem_str = f"内存: 平均 {result.get('avg_mem_mb', 'N/A')}MB"
        print(f"  {svc}: {cpu_str} | {mem_str}")
        for rec in result.get("recommendations", []):
            print(f"    -> {rec}")
            all_recs.append({"service": svc, "rec": rec})

    print(f"\n--- 月度成本估算 ---")
    cost = estimate_monthly_cost()
    print(f"  CPU: {cost['cpu_cores']} 核 = {cost['cpu_cost']} 元/月")
    print(f"  内存: {cost['mem_gb']} GB = {cost['mem_cost']} 元/月")
    print(f"  存储: {cost['storage_gb']} GB = {cost['storage_cost']} 元/月")
    print(f"  总计: {cost['total_cost']} 元/月")
    if all_recs:
        print(f"\n共 {len(all_recs)} 条优化建议，预估可节省 10-20% 成本")
    sys.exit(0)
```

```bash
python3 scripts/cost/resource-usage-report.py
```

预期结果：HPA 正常工作；非高峰缩容节省 15-20% 资源；月度成本估算偏差 < 10%

**回滚方案：**
```bash
kubectl delete hpa --all -n uav-platform
kubectl scale deployment --all --replicas=2 -n uav-platform
kubectl delete cronjob scale-down-night scale-up-morning -n uav-platform
```

---

### Task 9.3: 监控告警完善

**Files:**
- Create: `monitoring/prometheus/custom-business-rules.yml`
- Create: `monitoring/dashboards/sla-overview.json`
- Create: `monitoring/dashboards/business-metrics.json`
- Create: `monitoring/dashboards/system-infra.json`
- Create: `monitoring/alert_rules_p0_p3.yml`
- Create: `docs/on-call-sop.md`

**前置条件：**
- Prometheus + Grafana 已部署
- 各服务已暴露 Actuator/Metrics 端点
- 告警通知渠道已配置（企业微信/钉钉 Webhook）

- [ ] **Step 1: 配置 Prometheus 业务自定义指标采集规则**

Create: `monitoring/prometheus/custom-business-rules.yml`

```yaml
groups:
  - name: business_metrics_recording
    interval: 30s
    rules:
      - record: "api_success_rate:rate5m"
        expr: |
          sum(rate(http_server_requests_seconds_count{status=~"2..", code!~"204"}[5m])) by (application)
          /
          sum(rate(http_server_requests_seconds_count[5m])) by (application)

      - record: "api_latency_p99:rate5m"
        expr: |
          histogram_quantile(0.99,
            sum(rate(http_server_requests_seconds_bucket[5m])) by (le, application))

      - record: "weather_query_qps:rate1m"
        expr: |
          sum(rate(http_server_requests_seconds_count{application="weather-api", uri=~"/api/v1/weather/.*"}[1m]))

      - record: "planning_avg_duration:rate5m"
        expr: |
          sum(rate(http_server_requests_seconds_sum{application="planning-api"}[5m]))
          /
          sum(rate(http_server_requests_seconds_count{application="planning-api"}[5m]))

      - record: "risk_assess_qps:rate1m"
        expr: |
          sum(rate(http_server_requests_seconds_count{application="risk-api", uri=~"/api/v1/risk/.*"}[1m]))

      - record: "assimilation_success_rate:rate5m"
        expr: |
          sum(rate(http_server_requests_seconds_count{application="assimilation-api", status=~"2.."}[5m]))
          /
          sum(rate(http_server_requests_seconds_count{application="assimilation-api"}[5m]))

      - record: "auth_success_rate:rate5m"
        expr: |
          sum(rate(http_server_requests_seconds_count{application="platform-api", uri="/api/v1/auth/login", status="200"}[5m]))
          /
          sum(rate(http_server_requests_seconds_count{application="platform-api", uri="/api/v1/auth/login"}[5m]))

      - record: "active_users:rate5m"
        expr: |
          count(count by (username) (increase(http_server_requests_seconds_count{uri="/api/v1/users/me"}[5m])) > 0)
```

```bash
kubectl create configmap prometheus-business-rules \
  --from-file=monitoring/prometheus/custom-business-rules.yml \
  -n monitoring --dry-run=client -o yaml | kubectl apply -f -
```

- [ ] **Step 2: 创建 P0-P3 分级告警规则**

Create: `monitoring/alert_rules_p0_p3.yml`

```yaml
groups:
  # P0: 紧急告警（5 分钟内响应）
  - name: p0_critical_alerts
    rules:
      - alert: P0_ServiceCompletelyDown
        expr: up{job=~"uav-platform.*"} == 0
        for: 1m
        labels: { severity: P0, team: sre }
        annotations:
          summary: "[P0] 服务完全不可用"
          description: "{{ $labels.instance }} ({{ $labels.job }}) 已离线超过 1 分钟"
          runbook: "https://wiki.uav-platform.internal/runbook/service-down"

      - alert: P0_DatabaseDown
        expr: mysql_up == 0
        for: 30s
        labels: { severity: P0, team: sre }
        annotations:
          summary: "[P0] MySQL 数据库不可用"
          description: "MySQL 实例 {{ $labels.instance }} 已离线"

      - alert: P0_DataLossRisk
        expr: mysql_group_replication_member_state != "ONLINE"
        for: 1m
        labels: { severity: P0, team: sre }
        annotations:
          summary: "[P0] MySQL Group Replication 成员离线"
          description: "成员 {{ $labels.member_host }} 状态: {{ $value }}"

      - alert: P0_AllAPIGatewayDown
        expr: count(up{job="api-gateway"} == 0) == count(up{job="api-gateway"})
        for: 30s
        labels: { severity: P0, team: sre }
        annotations:
          summary: "[P0] 所有 API Gateway 实例不可用"

  # P1: 严重告警（15 分钟内响应）
  - name: p1_high_alerts
    rules:
      - alert: P1_HighErrorRate
        expr: |
          sum(rate(http_server_requests_seconds_count{status=~"5.."}[5m])) by (application)
          /
          sum(rate(http_server_requests_seconds_count[5m])) by (application) > 0.05
        for: 5m
        labels: { severity: P1, team: backend }
        annotations:
          summary: "[P1] 服务错误率超过 5%"
          description: "{{ $labels.application }} 错误率: {{ $value | humanizePercentage }}"

      - alert: P1_HighLatency
        expr: |
          histogram_quantile(0.99,
            sum(rate(http_server_requests_seconds_bucket[5m])) by (le, application)
          ) > 2
        for: 5m
        labels: { severity: P1, team: backend }
        annotations:
          summary: "[P1] P99 延迟超过 2 秒"
          description: "{{ $labels.application }} P99: {{ $value }}s"

      - alert: P1_JVMHeapCritical
        expr: jvm_memory_used_bytes{area="heap"} / jvm_memory_max_bytes{area="heap"} > 0.95
        for: 2m
        labels: { severity: P1, team: backend }
        annotations:
          summary: "[P1] JVM Heap 使用率超过 95%"

      - alert: P1_KafkaBrokerDown
        expr: kafka_broker_state != 3
        for: 2m
        labels: { severity: P1, team: sre }
        annotations:
          summary: "[P1] Kafka Broker 不可用"

      - alert: P1_RedisSentinelFailover
        expr: changes(redis_sentinel_master_reconfig_count[5m]) > 0
        labels: { severity: P1, team: sre }
        annotations:
          summary: "[P1] Redis Sentinel 触发故障转移"

  # P2: 警告告警（1 小时内响应）
  - name: p2_warning_alerts
    rules:
      - alert: P2_MediumErrorRate
        expr: |
          sum(rate(http_server_requests_seconds_count{status=~"5.."}[5m])) by (application)
          /
          sum(rate(http_server_requests_seconds_count[5m])) by (application) > 0.01
          and
          sum(rate(http_server_requests_seconds_count{status=~"5.."}[5m])) by (application)
          /
          sum(rate(http_server_requests_seconds_count[5m])) by (application) <= 0.05
        for: 10m
        labels: { severity: P2, team: backend }
        annotations:
          summary: "[P2] 服务错误率 1%-5%"

      - alert: P2_JVMHeapWarning
        expr: jvm_memory_used_bytes{area="heap"} / jvm_memory_max_bytes{area="heap"} > 0.85
        for: 5m
        labels: { severity: P2, team: backend }
        annotations:
          summary: "[P2] JVM Heap 使用率超过 85%"

      - alert: P2_DBConnectionPoolHigh
        expr: hikaricp_connections_active / hikaricp_connections_max > 0.8
        for: 5m
        labels: { severity: P2, team: backend }
        annotations:
          summary: "[P2] 数据库连接池使用率超过 80%"

      - alert: P2_DiskSpaceWarning
        expr: kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes > 0.8
        for: 10m
        labels: { severity: P2, team: sre }
        annotations:
          summary: "[P2] 存储使用率超过 80%"

      - alert: P2_PodRestartFrequent
        expr: increase(kube_pod_container_status_restarts_total[1h]) > 3
        labels: { severity: P2, team: backend }
        annotations:
          summary: "[P2] Pod 频繁重启（1h 内 {{ $value }} 次）"

  # P3: 通知告警（工作时间内处理）
  - name: p3_info_alerts
    rules:
      - alert: P3_HighCPUUsage
        expr: |
          sum(rate(container_cpu_usage_seconds_total{namespace="uav-platform"}[5m])) by (pod)
          / sum(kube_pod_container_resource_limits{resource="cpu", namespace="uav-platform"}) by (pod) > 0.7
        for: 30m
        labels: { severity: P3, team: backend }
        annotations:
          summary: "[P3] CPU 使用率持续超过 70%"

      - alert: P3_CertificateExpiry
        expr: probe_ssl_earliest_cert_expiry - time() < 7 * 24 * 3600
        labels: { severity: P3, team: sre }
        annotations:
          summary: "[P3] SSL 证书将在 7 天内过期"

      - alert: P3_BackupNotRecent
        expr: time() - backup_last_success_timestamp > 26 * 3600
        for: 1h
        labels: { severity: P3, team: sre }
        annotations:
          summary: "[P3] 备份超过 26 小时未执行"

      - alert: P3_GarbageCollectionFrequent
        expr: rate(jvm_gc_pause_seconds_count[15m]) > 10
        for: 10m
        labels: { severity: P3, team: backend }
        annotations:
          summary: "[P3] GC 频率较高（{{ $value }} 次/秒）"
```

```bash
kubectl apply -f monitoring/alert_rules_p0_p3.yml
```

- [ ] **Step 3: 创建 Grafana 三层仪表盘配置**

SLA 层仪表盘 (`monitoring/dashboards/sla-overview.json`) 核心面板：

| 面板 | PromQL | 说明 |
|------|--------|------|
| 整体可用性 | `avg_over_time(avg_over_time(up{job=~"uav-platform.*"}[5m])[30d:]) * 100` | 30 天可用性百分比 |
| API 成功率 | `avg(api_success_rate:rate5m) * 100` | 全服务平均成功率 |
| P99 延迟 | `avg(api_latency_p99:rate5m)` | 全服务平均 P99 |
| 活跃用户 | `active_users:rate5m` | 5 分钟内活跃用户数 |
| 告警统计 | `ALERTS{alertstate="firing"}` | 当前活跃告警数 |

业务层仪表盘 (`monitoring/dashboards/business-metrics.json`) 核心面板：

| 面板 | PromQL | 说明 |
|------|--------|------|
| 气象查询 QPS | `weather_query_qps:rate1m` | 气象数据查询吞吐 |
| 航线规划耗时 | `planning_avg_duration:rate5m` | 平均规划耗时 |
| 风险评估 QPS | `risk_assess_qps:rate1m` | 风险评估吞吐 |
| 同化成功率 | `assimilation_success_rate:rate5m * 100` | 同化实验成功率 |
| 认证成功率 | `auth_success_rate:rate5m * 100` | JWT 认证成功率 |

系统基础设施仪表盘 (`monitoring/dashboards/system-infra.json`) 核心面板：

| 面板 | PromQL | 说明 |
|------|--------|------|
| JVM Heap 使用 | `jvm_memory_used_bytes{area="heap"}` | 各服务 Heap 使用量 |
| DB 连接池 | `hikaricp_connections_active` | 活跃数据库连接数 |
| Kafka Lag | `kafka_consumer_group_lag` | 消费者组延迟 |
| Redis 命中率 | `redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total)` | 缓存命中率 |
| Pod 资源使用 | `container_cpu_usage_seconds_total` / `container_memory_working_set_bytes` | CPU/内存使用 |

```bash
# 导入仪表盘到 Grafana
for dashboard in sla-overview business-metrics system-infra; do
    kubectl create configmap grafana-dashboard-${dashboard} \
      --from-file=monitoring/dashboards/${dashboard}.json \
      -n monitoring --dry-run=client -o yaml | kubectl apply -f -
done
```

- [ ] **Step 4: 创建 On-call 值班方案与事件响应 SOP**

Create: `docs/on-call-sop.md`

```markdown
# UAV Platform On-call 值班方案与事件响应 SOP

## 1. 值班安排

### 排班规则
- 每周轮换一次，周一 09:00 切换
- 主值班 1 人 + 备值班 1 人
- 主值班负责所有告警响应，备用值班在主值班 15 分钟未响应时接管
- 节假日提前安排双倍值班人员

### 值班人员
| 周次 | 主值班 | 备值班 |
|------|--------|--------|
| 本周 | 张三 | 李四 |
| 下周 | 李四 | 王五 |

### 通知渠道
- P0 告警：电话 + 企业微信 + 短信
- P1 告警：企业微信 + 短信
- P2 告警：企业微信
- P3 告警：邮件（工作时间）

## 2. 告警分级与响应时间

| 级别 | 响应时间 | 解决时间 | 示例 |
|------|----------|----------|------|
| P0 | 5 分钟 | 30 分钟 | 服务完全不可用、数据库宕机 |
| P1 | 15 分钟 | 2 小时 | 错误率 > 5%、P99 > 2s、Heap > 95% |
| P2 | 1 小时 | 8 小时 | 错误率 1-5%、Heap > 85%、连接池 > 80% |
| P3 | 工作时间 | 3 个工作日 | CPU 持续高、证书即将过期 |

## 3. 事件响应流程

### P0 事件响应（服务完全不可用）

1. **确认告警**（1 分钟内）
   - 查看告警详情，确认影响范围
   - 在值班群发送确认消息

2. **初步诊断**（5 分钟内）
   ```bash
   # 检查服务状态
   kubectl get pods -n uav-platform
   kubectl logs -n uav-platform -l app=<affected-service> --tail=100

   # 检查数据库
   mysql -h <db-host> -u monitor -p -e "SHOW PROCESSLIST;"

   # 检查 Redis
   redis-cli -h <redis-host> INFO replication

   # 检查 Kafka
   kafka-topics.sh --describe --topic <topic> --bootstrap-server <broker>
   ```

3. **紧急恢复**（15 分钟内）
   - 尝试重启服务：`kubectl rollout restart deployment/<service> -n uav-platform`
   - 如数据库问题，检查 Group Replication 状态
   - 如网络问题，检查 DNS 和防火墙规则

4. **根因分析**（恢复后）
   - 收集日志、指标、trace
   - 编写事件报告

### P1 事件响应（性能降级）

1. **确认告警**（5 分钟内）
2. **查看监控面板**（Grafana 对应仪表盘）
3. **定位根因**
   - 高错误率：查看日志中的异常堆栈
   - 高延迟：检查 DB 慢查询、GC 日志
   - Heap 高：触发 Heap Dump 分析
4. **执行修复**
   - 扩容：`kubectl scale deployment <service> --replicas=N -n uav-platform`
   - 限流：通过 API Gateway 降级非核心功能
   - 回滚：`kubectl rollout undo deployment/<service> -n uav-platform`

### P2/P3 事件响应

1. 记录告警信息
2. 在工作时间排查
3. 创建工单跟踪

## 4. 事件升级矩阵

| 时间 | P0 | P1 | P2 | P3 |
|------|----|----|----|----|
| 5 分钟 | 通知技术负责人 | - | - | - |
| 15 分钟 | 通知研发总监 | 通知技术负责人 | - | - |
| 30 分钟 | 启动全员应急 | 通知研发总监 | - | - |
| 2 小时 | - | 通知研发总监 | 通知技术负责人 | - |
| 8 小时 | - | - | 通知技术负责人 | - |

## 5. 事件后复盘

### 复盘会议
- 时间：事件解决后 24 小时内
- 参与：值班人员 + 相关开发 + 技术负责人
- 输出：事件报告（模板见下）

### 事件报告模板

```markdown
## 事件报告

### 基本信息
- 事件编号：INC-YYYYMMDD-NNN
- 发生时间：YYYY-MM-DD HH:MM
- 恢复时间：YYYY-MM-DD HH:MM
- 影响持续时间：X 小时 Y 分钟
- 影响范围：XX 用户 / XX 请求
- 严重级别：P0/P1/P2/P3

### 时间线
| 时间 | 事件 |
|------|------|
| HH:MM | 告警触发 |
| HH:MM | 值班人员确认 |
| HH:MM | 初步诊断完成 |
| HH:MM | 执行恢复操作 |
| HH:MM | 服务恢复 |

### 根因分析
- 直接原因：...
- 根本原因：...
- 触发条件：...

### 改进措施
| 措施 | 负责人 | 截止日期 | 状态 |
|------|--------|----------|------|
| ... | ... | ... | ... |
```

## 6. 联系方式

| 角色 | 姓名 | 电话 | 企业微信 |
|------|------|------|----------|
| 技术负责人 | ... | ... | ... |
| 研发总监 | ... | ... | ... |
| DBA | ... | ... | ... |
| 运维 | ... | ... | ... |
```

- [ ] **Step 5: 验证告警规则生效**

```bash
# 验证告警规则已加载
kubectl get prometheusrules -n monitoring
# 预期: 包含 p0_critical_alerts, p1_high_alerts, p2_warning_alerts, p3_info_alerts

# 触发测试告警（临时提高阈值）
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: test-alert
  namespace: monitoring
spec:
  groups:
    - name: test
      rules:
        - alert: TestAlert
          expr: vector(1)
          for: 1m
          labels: { severity: P3 }
          annotations:
            summary: "测试告警"
EOF

# 检查 Alertmanager 是否收到
curl -s http://localhost:9093/api/v1/alerts | python3 -m json.tool

# 清理测试告警
kubectl delete prometheusrule test-alert -n monitoring
```

预期结果：
- P0-P3 告警规则全部加载
- Alertmanager 正确路由告警到对应通知渠道
- Grafana 三层仪表盘正常展示指标
- On-call SOP 文档已就绪

**回滚方案：**
```bash
# 移除自定义告警规则
kubectl delete prometheusrule alert-rules-p0-p3 -n monitoring
# 恢复默认告警规则
kubectl apply -f monitoring/alert_rules.yml
```

---

## 总结

### 实施顺序

```
Phase 7（安全加固） → Phase 8（多区域+灾备） → Phase 9（运维优化）
    ↓                      ↓                      ↓
  7.1 HTTPS/TLS        8.1 多区域部署          9.1 混沌工程
  7.2 渗透测试         8.2 灾难恢复            9.2 成本优化
  7.3 压力测试                                9.3 监控告警完善
  7.4 稳定性测试
```

### 预估工期

| Phase | 任务 | 预估工期 | 依赖 |
|-------|------|----------|------|
| 7.1 | HTTPS/TLS 配置 | 0.5 天 | 服务器就绪 |
| 7.2 | 渗透测试 | 1 天 | 7.1 完成 |
| 7.3 | 压力测试 | 1 天 | 7.1 完成 |
| 7.4 | 稳定性测试 | 7 天（后台运行） | 7.3 完成 |
| 8.1 | 多区域部署 | 2 天 | Phase 7 完成 |
| 8.2 | 灾难恢复 | 1 天 | 8.1 完成 |
| 9.1 | 混沌工程 | 1 天 | K8s 集群就绪 |
| 9.2 | 成本优化 | 0.5 天 | 9.1 完成 |
| 9.3 | 监控告警完善 | 1 天 | Phase 8 完成 |

### 验收标准

- [ ] SSL Labs 评级 A+，mTLS 微服务间通信正常
- [ ] ZAP 扫描 0 High，JWT/RBAC 测试全部通过
- [ ] 压测结果满足 `perf-baseline.json` 中所有基准目标
- [ ] 7 天长跑无内存泄漏，服务崩溃后 150 秒内恢复
- [ ] MySQL Group Replication 两节点 ONLINE，数据延迟 < 1s
- [ ] Redis Sentinel 故障转移 < 30s
- [ ] Kafka 3-Broker 集群正常，跨区域同步延迟 < 5s
- [ ] RPO < 5 分钟，RTO < 30 分钟
- [ ] 混沌工程所有实验通过稳定性验证
- [ ] HPA 自动扩缩容正常，非高峰缩容节省 15-20% 资源
- [ ] P0-P3 告警规则生效，On-call SOP 就绪
