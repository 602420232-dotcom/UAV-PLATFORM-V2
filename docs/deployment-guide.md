# UAV Platform V2 部署运维手册

## 1. 环境要求

| 组件 | 最低版本 | 说明 |
|------|----------|------|
| JDK | 21+ | 主项目 Spring Boot 4.0，Gateway Spring Boot 3.4.x |
| Maven | 3.9+ | 项目构建 |
| Node.js | 20+ | 开发者控制台 (Vue 3) |
| Docker | 24+ | 基础设施容器化 |
| Docker Compose | 2.20+ | 编排 MySQL/Redis/Kafka/Zookeeper |

**硬件最低要求**: 8GB RAM, 4 CPU cores

## 2. 快速启动（开发环境）

### 2.1 启动基础设施

```bash
docker compose up -d mysql redis kafka zookeeper
```

### 2.2 初始化数据库

```bash
docker exec -i uav-mysql mysql -uroot -prootpass < scripts/init-db.sql
```

### 2.3 编译项目

```bash
mvn clean install -DskipTests
```

### 2.4 启动服务

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start-services.ps1
```

### 2.5 启动网关（独立构建）

```powershell
cd gateway/api-gateway
powershell -ExecutionPolicy Bypass -File build-standalone.ps1
java -jar target/api-gateway-2.0.0.jar --server.port=18080 --spring.profiles.active=local
```

## 3. 服务端口清单

| Service | Port | Description |
|---------|------|-------------|
| api-gateway | 18080 | API Gateway (Spring Boot 3.4.x) |
| platform-api | 18081 | Platform management |
| weather-api | 18082 | Weather data |
| assimilation-api | 18083 | Data assimilation |
| risk-api | 18084 | Risk assessment (含适航评估) |
| observation-api | 18085 | Observation decision |
| planning-api | 18086 | Path planning |
| utm-api | 18087 | UTM management |
| MySQL | 3306 | Database |
| Redis | 6379 | Cache |
| Kafka | 19092 | Message queue |

## 4. 配置说明

### 4.1 Mock 模式开关

- `uav.mock.enabled=true` (default, dev/test)
- `uav.mock.enabled=false` (production, **MUST set**)
- Mock 响应包含 `X-Mock: true` Header

### 4.2 数据库配置

所有依赖 MySQL 的服务使用统一配置：

- URL: `jdbc:mysql://localhost:3306/{database}`
- Username: `root`
- Password: `rootpass`
- Parameters: `allowPublicKeyRetrieval=true&useSSL=false`

### 4.3 Redis 配置

- Host: `localhost:6379`

### 4.4 Kafka 配置

- Bootstrap servers: `localhost:19092`

## 5. 常见故障排查

### 5.1 端口被占用

- **现象**: `Port XXXX was already in use`
- **解决**: 查找占用进程并终止

```powershell
netstat -ano | findstr :XXXX
Stop-Process -Id {PID}
```

### 5.2 MySQL 连接失败

- **现象**: `Access denied for user 'root'@'172.19.0.1'`
- **原因**: Docker NAT 导致认证 IP 不匹配
- **解决**:

```bash
docker exec uav-mysql mysql -uroot -prootpass -e "ALTER USER 'root'@'%' IDENTIFIED BY 'rootpass'; FLUSH PRIVILEGES;"
```

### 5.3 Gateway 启动失败

- **现象**: Spring Cloud Gateway 与 Spring Boot 4.0 不兼容
- **解决**: 使用独立构建方式

```powershell
cd gateway/api-gateway
powershell -ExecutionPolicy Bypass -File build-standalone.ps1
```

### 5.4 Kafka 连接超时

- **现象**: `Connection to node -1 could not be established`
- **解决**: 检查 Zookeeper 和 Kafka 是否正常运行

```powershell
docker ps | findstr kafka
```

## 6. 健康检查

```powershell
# 检查所有服务端口
foreach ($p in 18080..18087) { Test-NetConnection localhost -Port $p }

# 运行 E2E 测试
python scripts/e2e-test.py --mock
```

## 7. 优雅停机

```powershell
# 停止所有 Java 服务
Stop-Process -Name "java" -Force

# 停止基础设施容器
docker compose down
```
