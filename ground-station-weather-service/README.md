# 地面站气象数据服务

## 概述

地面站气象数据服务（ground-station-weather-service）负责收集、处理和存储来自各个地面气象站的观测数据。该服务提供 REST API 接口，支持地面气象数据的采集、查询和统计分析，为无人机路径规划和气象预测提供实时地面气象观测数据。

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
ground-station-weather-service/
├── src/
│   ├── main/
│   │   ├── java/com/uav/groundstation/weather/
│   │   │   ├── GroundStationWeatherApplication.java  # 应用入口
│   │   │   ├── controller/                          # REST 控制器
│   │   │   ├── service/                             # 业务逻辑
│   │   │   ├── repository/                          # 数据访问层
│   │   │   ├── entity/                              # 实体类
│   │   │   ├── dto/                                 # 数据传输对象
│   │   │   └── config/                              # 配置类
│   │   └── resources/
│   │       ├── application.yml                      # 应用配置
│   │       └── bootstrap.yml                        # 引导配置
│   └── test/
├── pom.xml                                          # Maven 配置
└── README.md                                        # 本文件
```

## 服务端口

| 端口 | 协议 | 说明 |
|:----:|------|------|
| 8087 | HTTP | REST API 服务端口 |

## API 端点

### 健康检查

```
GET /actuator/health
GET /actuator/info
```

### 地面气象站管理

```
GET /api/ground-station/stations
POST /api/ground-station/stations
GET /api/ground-station/stations/{id}
PUT /api/ground-station/stations/{id}
DELETE /api/ground-station/stations/{id}
```

### 气象数据采集

```
POST /api/ground-station/data
批量上传地面气象站观测数据
```

**请求体:**
```json
{
  "stationId": "STATION-001",
  "observationTime": "2026-06-05T12:00:00Z",
  "temperature": 25.5,
  "humidity": 65.0,
  "pressure": 1013.25,
  "windSpeed": 5.2,
  "windDirection": 180,
  "precipitation": 0.0,
  "solarRadiation": 850.0
}
```

### 气象数据查询

```
GET /api/ground-station/data
按条件查询地面气象数据
```

**查询参数:**
- `stationId`: 气象站 ID
- `startTime`: 开始时间
- `endTime`: 结束时间
- `page`: 页码（默认 0）
- `size`: 每页大小（默认 20）

### 统计分析

```
GET /api/ground-station/data/statistics
获取指定时间段内的气象数据统计
```

**查询参数:**
- `stationId`: 气象站 ID（可选，不传则查询所有）
- `startTime`: 开始时间
- `endTime`: 结束时间

## Docker 部署

### 构建镜像

```bash
mvn clean package -DskipTests
docker build -t uav/ground-station-weather-service:latest -f ../docker/Dockerfile .
```

### 运行容器

```bash
docker run -d \
  --name ground-station-weather-service \
  -p 8087:8087 \
  -e SPRING_DATASOURCE_URL=jdbc:mysql://mysql:3306/meteor_data \
  -e SPRING_DATASOURCE_USERNAME=root \
  -e SPRING_DATASOURCE_PASSWORD=your_password \
  -e SPRING_CLOUD_NACOS_SERVER_ADDR=nacos:8848 \
  uav/ground-station-weather-service:latest
```

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SERVER_PORT` | `8087` | 服务端口 |
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

启动后访问: http://localhost:8087/swagger-ui.html (SpringDoc 自动生成的 OpenAPI 文档)

### 数据库初始化

应用启动时会自动创建所需的数据库表结构。如需手动初始化，请参考 `src/main/resources/db/` 目录下的 SQL 脚本（如存在）。

## 相关文档

- [根项目 README](../README.md)
- [端口配置总表](../docs/PORTS_CONFIGURATION.md)
- [项目架构文档](../docs/architecture.md)
- [气象数据采集文档](../docs/api/uav-weather-collector/README.md)

---

> **最后更新**: 2026-06-05
> **版本**: 1.0
> **维护者**: UAV Platform Team
