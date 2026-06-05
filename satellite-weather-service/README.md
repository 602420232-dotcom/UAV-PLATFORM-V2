# 卫星气象数据服务

## 概述

卫星气象数据服务（satellite-weather-service）负责处理卫星云图和遥感数据。该服务提供 REST API 接口，支持卫星数据的接收、存储、处理和查询，包括云图分析、云量计算、温度反演等功能，为气象预测和无人机路径规划提供卫星观测数据支持。

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
satellite-weather-service/
├── src/
│   ├── main/
│   │   ├── java/com/uav/satellite/weather/
│   │   │   ├── SatelliteWeatherApplication.java  # 应用入口
│   │   │   ├── controller/                       # REST 控制器
│   │   │   ├── service/                          # 业务逻辑
│   │   │   ├── repository/                       # 数据访问层
│   │   │   ├── entity/                           # 实体类
│   │   │   ├── dto/                              # 数据传输对象
│   │   │   └── config/                           # 配置类
│   │   └── resources/
│   │       ├── application.yml                   # 应用配置
│   │       └── bootstrap.yml                     # 引导配置
│   └── test/
├── pom.xml                                       # Maven 配置
└── README.md                                     # 本文件
```

## 服务端口

| 端口 | 协议 | 说明 |
|:----:|------|------|
| 8089 | HTTP | REST API 服务端口 |

## API 端点

### 健康检查

```
GET /actuator/health
GET /actuator/info
```

### 卫星数据源管理

```
GET /api/satellite/sources
POST /api/satellite/sources
GET /api/satellite/sources/{id}
PUT /api/satellite/sources/{id}
DELETE /api/satellite/sources/{id}
```

### 卫星数据上传

```
POST /api/satellite/data
上传卫星云图或遥感数据
```

**请求体:**
```json
{
  "sourceId": "SAT-001",
  "observationTime": "2026-06-05T12:00:00Z",
  "dataType": "CLOUD_IMAGE",
  "area": {
    "minLat": 20.0,
    "maxLat": 40.0,
    "minLon": 100.0,
    "maxLon": 120.0
  },
  "resolution": "1KM",
  "dataUrl": "s3://bucket/satellite/data/20260605T120000.tif",
  "metadata": {
    "sensor": "VIS",
    "channel": "IR1",
    "cloudCover": 0.35
  }
}
```

### 卫星数据查询

```
GET /api/satellite/data
按条件查询卫星数据
```

**查询参数:**
- `sourceId`: 数据源 ID
- `dataType`: 数据类型（CLOUD_IMAGE, TEMPERATURE, HUMIDITY 等）
- `startTime`: 开始时间
- `endTime`: 结束时间
- `minLat`, `maxLat`, `minLon`, `maxLon`: 区域范围
- `page`: 页码（默认 0）
- `size`: 每页大小（默认 20）

### 云图分析

```
POST /api/satellite/analysis/cloud-cover
分析指定区域的云量分布
```

**请求体:**
```json
{
  "area": {
    "minLat": 20.0,
    "maxLat": 40.0,
    "minLon": 100.0,
    "maxLon": 120.0
  },
  "observationTime": "2026-06-05T12:00:00Z"
}
```

### 温度反演

```
POST /api/satellite/analysis/temperature
从卫星数据反演地表/大气温度
```

## Docker 部署

### 构建镜像

```bash
mvn clean package -DskipTests
docker build -t uav/satellite-weather-service:latest -f ../docker/Dockerfile .
```

### 运行容器

```bash
docker run -d \
  --name satellite-weather-service \
  -p 8089:8089 \
  -e SPRING_DATASOURCE_URL=jdbc:mysql://mysql:3306/meteor_data \
  -e SPRING_DATASOURCE_USERNAME=root \
  -e SPRING_DATASOURCE_PASSWORD=your_password \
  -e SPRING_CLOUD_NACOS_SERVER_ADDR=nacos:8848 \
  uav/satellite-weather-service:latest
```

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SERVER_PORT` | `8089` | 服务端口 |
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

启动后访问: http://localhost:8089/swagger-ui.html (SpringDoc 自动生成的 OpenAPI 文档)

## 相关文档

- [根项目 README](../README.md)
- [端口配置总表](../docs/PORTS_CONFIGURATION.md)
- [项目架构文档](../docs/architecture.md)
- [气象数据采集文档](../docs/api/uav-weather-collector/README.md)

---

> **最后更新**: 2026-06-05
> **版本**: 1.0
> **维护者**: UAV Platform Team
