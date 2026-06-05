# 探空气象数据服务

## 概述

探空气象数据服务（radiosonde-weather-service）负责处理探空气球观测数据。该服务提供 REST API 接口，支持探空数据的接收、存储、处理和查询，包括温度廓线、湿度廓线、风场廓线等高空大气数据，为气象预测和无人机路径规划提供高空观测数据支持。

## 技术栈

| 技术 | 版本 | 用途 |
|------|:----:|------|
| Java | 17 | 运行环境 |
| Spring Boot | 3.2.0 | Web 框架 |
| Spring Data JPA | - | ORM 框架 |
| MySQL | 8.0+ | 数据存储 |
| Nacos | 2.x | 服务发现 |
| Undertow | - | 高性能 Web 服务器 |
| Lombok | - | 简化代码 |
| SpringDoc OpenAPI | 2.2.0 | API 文档生成 |

## 项目结构

```
radiosonde-weather-service/
├── src/
│   ├── main/
│   │   ├── java/com/uav/radiosonde/weather/
│   │   │   ├── RadiosondeWeatherApplication.java  # 应用入口
│   │   │   ├── controller/                         # REST 控制器
│   │   │   ├── service/                            # 业务逻辑
│   │   │   ├── repository/                         # 数据访问层
│   │   │   ├── entity/                             # 实体类
│   │   │   ├── dto/                                # 数据传输对象
│   │   │   └── config/                             # 配置类
│   │   └── resources/
│   │       ├── application.yml                     # 应用配置
│   │       └── bootstrap.yml                       # 引导配置
│   └── test/
├── pom.xml                                         # Maven 配置
└── README.md                                       # 本文件
```

## 服务端口

| 端口 | 协议 | 说明 |
|:----:|------|------|
| 8090 | HTTP | REST API 服务端口 |

## API 端点

### 健康检查

```
GET /actuator/health
GET /actuator/info
```

### 探空站管理

```
GET /api/radiosonde/stations
POST /api/radiosonde/stations
GET /api/radiosonde/stations/{id}
PUT /api/radiosonde/stations/{id}
DELETE /api/radiosonde/stations/{id}
```

### 探空数据上传

```
POST /api/radiosonde/data
上传探空气球观测数据
```

**请求体:**
```json
{
  "stationId": "RAD-001",
  "launchTime": "2026-06-05T12:00:00Z",
  "profile": [
    {
      "pressure": 1013.25,
      "height": 0,
      "temperature": 25.5,
      "dewPoint": 20.0,
      "humidity": 65.0,
      "windSpeed": 5.2,
      "windDirection": 180
    },
    {
      "pressure": 850.0,
      "height": 1500,
      "temperature": 18.0,
      "dewPoint": 12.0,
      "humidity": 60.0,
      "windSpeed": 8.5,
      "windDirection": 200
    }
  ],
  "metadata": {
    "balloonType": "RS92",
    "launchCondition": "NORMAL"
  }
}
```

### 探空数据查询

```
GET /api/radiosonde/data
按条件查询探空数据
```

**查询参数:**
- `stationId`: 探空站 ID
- `startTime`: 开始时间
- `endTime`: 结束时间
- `minHeight`, `maxHeight`: 高度范围（米）
- `page`: 页码（默认 0）
- `size`: 每页大小（默认 20）

### 探空廓线分析

```
POST /api/radiosonde/analysis/profile
分析探空廓线数据
```

**请求体:**
```json
{
  "stationId": "RAD-001",
  "observationTime": "2026-06-05T12:00:00Z",
  "parameters": ["temperature", "humidity", "wind"]
}
```

### 稳定性指数计算

```
POST /api/radiosonde/analysis/stability
计算大气稳定性指数（CAPE, CIN, K 指数等）
```

## Docker 部署

### 构建镜像

```bash
mvn clean package -DskipTests
docker build -t uav/radiosonde-weather-service:latest -f ../docker/Dockerfile .
```

### 运行容器

```bash
docker run -d \
  --name radiosonde-weather-service \
  -p 8090:8090 \
  -e SPRING_DATASOURCE_URL=jdbc:mysql://mysql:3306/meteor_data \
  -e SPRING_DATASOURCE_USERNAME=root \
  -e SPRING_DATASOURCE_PASSWORD=your_password \
  -e SPRING_CLOUD_NACOS_SERVER_ADDR=nacos:8848 \
  uav/radiosonde-weather-service:latest
```

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SERVER_PORT` | `8090` | 服务端口 |
| `SPRING_DATASOURCE_URL` | `jdbc:mysql://localhost:3306/meteor_data` | 数据库连接地址 |
| `SPRING_DATASOURCE_USERNAME` | `root` | 数据库用户名 |
| `SPRING_DATASOURCE_PASSWORD` | - | 数据库密码（必填） |
| `SPRING_CLOUD_NACOS_SERVER_ADDR` | `localhost:8848` | Nacos 注册中心地址 |

## 开发指南

### 安装依赖

```bash
mvn clean install
```

### 启动开发服务器

```bash
mvn spring-boot:run
```

### API 文档

启动后访问: http://localhost:8090/swagger-ui.html (SpringDoc 自动生成的 OpenAPI 文档)

## 相关文档

- [根项目 README](../README.md)
- [端口配置总表](../docs/PORTS_CONFIGURATION.md)
- [项目架构文档](../docs/architecture.md)
- [气象数据采集文档](../docs/api/uav-weather-collector/README.md)

---

> **最后更新**: 2026-06-05
> **版本**: 1.0
> **维护者**: UAV Platform Team
