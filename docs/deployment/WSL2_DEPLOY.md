# WSL2 一键部署指南

> **适用**: Windows 11 + WSL2 + Docker Desktop  
> **维护者**: DITHIOTHREITOL  
> **最后更新**: 2026-05-28

---

## 前置条件

| 组件 | 要求 | 说明 |
|------|------|------|
| Windows | 11 | WSL2 依赖 |
| WSL2 | Ubuntu 24.04 | systemd 启用 |
| RAM | 28GB+ | 宿主机 32GB，WSL2 分配 28GB |
| Docker Desktop | 最新版 | WSL2 后端 |
| GPU | NVIDIA RTX 3060+ (可选) | 风乌模型推理需要 |
| 磁盘 | 20GB+ 空闲 | 镜像 + 数据 |

---

## 第一步：WSL2 配置

在 Windows 的 `%USERPROFILE%\.wslconfig` 中:

```ini
[wsl2]
memory=28GB
processors=8
swap=6GB

[experimental]
hostAddressLoopback=true
autoMemoryReclaim=gradual
```

改完后 PowerShell(管理员): `wsl --shutdown`，重新打开 WSL2。

---

## 第二步：克隆项目

```bash
git clone <your-repo-url>
cd trae
```

---

## 第三步：配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，修改以下字段:
- `DB_PASSWORD` — MySQL 密码
- `JWT_SECRET_KEY` — 生成: `openssl rand -base64 32`
- `ENCRYPTION_KEY` — 生成: `openssl rand -base64 32`

---

## 第四步：编译项目 (仅首次，或在 WSL2 中)

```bash
# 使用 Docker Maven 编译（无需本地安装 JDK 17）
docker run --rm \
  -v "$(pwd)":/app \
  -v "$HOME/.m2":/root/.m2 \
  -w /app \
  maven:3.9-eclipse-temurin-17 \
  mvn clean install -DskipTests -B
```

> 首次编译需下载依赖，约 5-10 分钟。后续增量编译只需 1 分钟。

---

## 第五步：启动全部服务

```bash
docker compose up -d
```

> 首次需构建镜像，约 3-5 分钟。

---

## 第六步：验证健康状态

等待 3 分钟让所有 Spring Boot 服务完全启动:

```bash
for p in 8088 8080 8081 8082 8083 8084 8086 8000; do
  status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$p/actuator/health 2>/dev/null)
  echo "port $p: $status"
done
```

预期全部返回 `200`。

---

## 服务清单

| 服务 | 端口 | 类型 | 说明 |
|------|------|------|------|
| uav-mysql | 3306 | 基础设施 | MySQL 8.0 |
| uav-redis | 6379 | 基础设施 | Redis 6.2 |
| uav-nacos | 8848 | 基础设施 | Nacos 注册中心 |
| uav-kafka | 9092 | 基础设施 | Kafka 消息队列 |
| uav-zookeeper | 2181 | 基础设施 | ZK 协调服务 |
| api-gateway | 8088 | 微服务 | API 网关 |
| uav-platform | 8080 | 微服务 | 主平台 |
| wrf-processor | 8081 | 微服务 | WRF 气象处理 |
| meteor-forecast | 8082 | 微服务 | 气象预测 |
| path-planning | 8083 | 微服务 | 路径规划 |
| data-assimilation | 8084 | 微服务 | 贝叶斯同化 |
| uav-weather | 8086 | 微服务 | 气象采集 |
| edge-cloud | 8000 | 微服务 | 边云协同 |

---

## 常用命令

```bash
# 查看所有服务状态
docker compose ps

# 查看某个服务日志
docker compose logs -f uav-platform

# 重启单个服务
docker compose restart uav-platform

# 停止全部
docker compose down

# 重新构建并启动
docker compose up -d --build

# 进入 MySQL
docker exec -it uav-mysql mysql -u uav -p
```

---

## 常见问题

### 服务反复重启
```bash
docker logs <服务名> 2>&1 | grep "APPLICATION FAILED\|Caused by"
```

### 数据库不存在
```bash
docker exec uav-mysql mysql -uroot -p<密码> -e "
  CREATE DATABASE IF NOT EXISTS wrf_processor;
  CREATE DATABASE IF NOT EXISTS meteor_forecast;
  CREATE DATABASE IF NOT EXISTS path_planning;
  CREATE DATABASE IF NOT EXISTS data_assimilation;
  CREATE DATABASE IF NOT EXISTS uav_weather;
"
```

### Feign Client Bean 冲突
已在 `application.yml` 中配置 `spring.main.allow-bean-definition-overriding=true` 和 `spring.cloud.openfeign.lazy-attributes-resolution=true`。

### Docker 构建失败（Maven 找不到父 POM）
不要用原始 Dockerfile。项目已提供 `Dockerfile.runtime`，只复制编译好的 JAR，不走 Maven：
```bash
# docker-compose.yml 已配置使用 Dockerfile.runtime
docker compose build
```

### GPU 不可用（FengWu 模型）
确认 Docker Desktop 已安装 NVIDIA Container Toolkit：
```bash
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

---

## 监控面板 (可选)

```bash
cd tools/mypanel
npm install
node app.js
# 访问 http://localhost:5577 (账号 admin/admin123)
```

---

> **版本**: v1.0  
> **基于**: 2026-05-28 完整部署实践
