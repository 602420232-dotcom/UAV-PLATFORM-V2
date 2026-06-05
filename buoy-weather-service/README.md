# Buoy Weather Service

## 概述

浮标气象数据服务，负责收集、处理和提供海洋浮标观测的气象数据，包括风速、风向、温度、湿度、气压等参数，为无人机路径规划提供实时海上气象信息。

## 技术栈

| 技术 | 版本 | 用途 |
|------|:----:|------|
| Java | 17 | 运行环境 |
| Spring Boot | 3.x | Web 框架 |
| MySQL | 8.x | 数据存储 |
| Redis | 7.x | 缓存 |

## 项目结构

```
buoy-weather-service/
├── src/main/java/com/uav/buoy/weather/
│   ├── controller/       # REST 控制器
│   ├── service/          # 业务逻辑
│   ├── repository/       # 数据访问
│   ├── entity/           # 实体类
│   └── config/           # 配置类
├── src/main/resources/
│   └── application.yml   # 配置文件
├── pom.xml               # Maven 配置
└── README.md             # 本文件
```

## 服务端口

| 端口 | 协议 | 说明 |
|:----:|------|------|
| TBD | HTTP | REST API 服务端口 |

## API 端点

### 健康检查

```
GET /actuator/health
```

### 浮标数据查询

```
GET /api/buoy/weather/{buoyId}
GET /api/buoy/weather/recent
```

### 数据上传

```
POST /api/buoy/weather
```

## Docker 部署

### 构建镜像

```bash
cd buoy-weather-service
mvn clean package -DskipTests
docker build -t uav/buoy-weather-service:latest .
```

### 运行容器

```bash
docker run -d \
  --name buoy-weather-service \
  -p <PORT>:<PORT> \
  -e SPRING_PROFILES_ACTIVE=prod \
  uav/buoy-weather-service:latest
```

## 开发指南

### 安装依赖

```bash
cd buoy-weather-service
mvn clean install
```

### 启动开发服务器

```bash
mvn spring-boot:run
```

## 相关文档

- [根项目 README](../README.md)
- [端口配置总表](../docs/PORTS_CONFIGURATION.md)
- [项目架构文档](../docs/architecture.md)

---

> **最后更新**: 2026-06-05
> **版本**: 1.0
> **维护者**: UAV Platform Team
