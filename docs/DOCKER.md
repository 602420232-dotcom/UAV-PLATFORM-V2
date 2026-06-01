# Docker 部署指南

## 📋 目录

- [前置准备](#前置准备)
- [快速启动](#快速启动)
- [项目说明](#项目说明)
- [常见问题](#常见问题)

## 🚀 前置准备

### 1. 安装 Docker 和 Docker Compose

- Docker Desktop（推荐用于 Windows/Mac）：https://www.docker.com/get-started
- Docker Compose 通常随 Docker Desktop 一起安装

### 2. 验证安装

```bash
docker --version
docker-compose --version
```

### 3. 解决 Maven 依赖问题（重要！）

如果之前遇到 Maven 依赖缺失问题，请先运行：
```bash
# 方法一：运行自动化脚本
fix-maven-deps.bat

# 方法二：手动在任意 Spring Boot 项目目录运行
mvn clean install -U -DskipTests
```

详细说明见 [MAVEN_FIX.md](MAVEN_FIX.md)

## 🏃 快速启动

### 方式一：使用 Docker Compose（推荐）

```bash
# 进入项目根目录
cd trae

# 构建并启动所有服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 停止服务并删除数据卷（谨慎操作！）
docker-compose down -v
```

### 方式二：单独构建和运行

```bash
# 构建单个服务
cd wrf-processor-service
docker build -t wrf-processor:latest .

# 运行单个服务
docker run -p 8081:8081 wrf-processor:latest
```

## 🏗️ 项目说明

### 服务清单

| 服务 | 端口 | 目录 | 说明 |
|------|------|------|------|
| mysql | 3306 | - | MySQL 8.0 数据库 |
| redis | 6379 | - | Redis 6.2 缓存 |
| nacos | 8848 | - | Nacos 服务注册发现 |
| kafka | 9092 | - | Kafka 消息队列 |
| api-gateway | 8088 | api-gateway/ | API 网关（限流/熔断/路由） |
| wrf-processor | 8081 | wrf-processor-service/ | WRF 气象处理服务 |
| data-assimilation | 8084 | data-assimilation-service/ | 贝叶斯同化服务 |
| meteor-forecast | 8082 | meteor-forecast-service/ | 气象预测服务 |
| path-planning | 8083 | path-planning-service/ | 路径规划服务 |
| uav-platform | 8080 | uav-platform-service/ | 主平台服务 |
| uav-weather-collector | 8086 | uav-weather-collector/ | 气象信息收集服务 |
| edge-cloud-coordinator | 8000/8765 | edge-cloud-coordinator/ | 边云协同框架（REST/WebSocket） |

### 访问地址

- API网关：http://localhost:8088
- 主平台：http://localhost:8080
- WRF 服务：http://localhost:8081
- 气象预测：http://localhost:8082
- 路径规划：http://localhost:8083
- 同化服务：http://localhost:8084
- 气象收集：http://localhost:8086
- 边云协同：http://localhost:8000/docs
- Nacos 控制台：http://localhost:8848/nacos

## 📂 项目文件结构

```
trae/
├── docker-compose.yml      # Docker Compose 配置
├── DOCKER.md              # 本文件
├── .dockerignore          # Docker 忽略文件
├── fix-maven-deps.bat     # Maven 依赖修复脚本
├── wrf-processor-service/
│   ├── Dockerfile         # 服务 Dockerfile
│   ├── pom.xml            # Maven 配置
│   └── src/               # 源代码
├── meteor-forecast-service/
│   ├── Dockerfile
│   ├── pom.xml
│   └── src/
├── path-planning-service/
│   ├── Dockerfile
│   ├── pom.xml
│   └── src/
├── uav-platform-service/
│   ├── Dockerfile
│   ├── pom.xml
│   └── src/
└── data-assimilation-service/
    ├── Dockerfile
    ├── pom.xml
    └── src/
```

## 🔧 Dockerfile 说明

所有 Spring Boot 服务使用 **多阶段构建**：

### 第一阶段：Builder 阶段
- 基础镜像：`maven:3.8.6-openjdk-17-slim`
- 下载 Maven 依赖（利用 Docker 缓存）
- 编译打包应用

### 第二阶段：Runtime 阶段
- 基础镜像：`openjdk:17-jre-slim`
- 只包含 JRE，镜像更小
- 从 Builder 阶段复制 JAR 文件

## ⚠️ 常见问题

### 1. Maven 依赖下载慢

参考 [MAVEN_FIX.md](MAVEN_FIX.md) 配置阿里云镜像源。

### 2. 构建时 Maven 依赖缺失

```bash
# 在 Dockerfile 构建前，先在本地下载好依赖
mvn dependency:go-offline
```

### 3. 端口被占用

修改 `docker-compose.yml` 中的端口映射，例如：
```yaml
ports:
  - "8081:8081"  # 改成其他端口，如 "9081:8081"
```

### 4. 数据库初始化失败

确保 `./database/create_tables.sql` 文件存在且内容正确。

### 5. 内存不足

修改 `docker-compose.yml` 中服务的 JVM 参数：
```yaml
environment:
  JAVA_OPTS: "-Xmx256m -Xms128m"  # 减小内存
```

## 📊 健康检查

```bash
# 查看所有容器状态
docker ps

# 查看特定服务日志
docker-compose logs -f wrf-processor

# 进入容器调试
docker exec -it <container_name> /bin/bash
```

## 🛠️ 开发模式

如果需要在本地开发，可以只启动数据库和缓存：

```bash
docker-compose up -d mysql redis
```

然后在 IDE 中运行各个 Spring Boot 服务，连接到 localhost 的 MySQL 和 Redis。

## 📝 更新记录

- v1.1.0 - 添加 API Gateway、气象收集服务、边云协同框架
- v1.0.0 - 初始版本，支持完整部署
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
