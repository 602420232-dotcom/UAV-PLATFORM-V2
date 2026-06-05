# 检测无人机服务

## 概述

检测无人机服务（detection-drone-service）负责无人机目标检测功能。该服务提供 REST API 接口，支持无人机探测任务管理、目标检测算法调用、检测结果存储和查询等功能，为无人机路径规划和气象观测提供实时目标检测能力。

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
detection-drone-service/
├── src/
│   ├── main/
│   │   ├── java/com/uav/detection/drone/
│   │   │   ├── DetectionDroneApplication.java  # 应用入口
│   │   │   ├── controller/                      # REST 控制器
│   │   │   ├── service/                         # 业务逻辑
│   │   │   ├── repository/                      # 数据访问层
│   │   │   ├── entity/                          # 实体类
│   │   │   ├── dto/                             # 数据传输对象
│   │   │   └── config/                          # 配置类
│   │   └── resources/
│   │       ├── application.yml                  # 应用配置
│   │       └── bootstrap.yml                    # 引导配置
│   └── test/
├── pom.xml                                      # Maven 配置
└── README.md                                    # 本文件
```

## 服务端口

| 端口 | 协议 | 说明 |
|:----:|------|------|
| 8091 | HTTP | REST API 服务端口 |

## API 端点

### 健康检查

```
GET /actuator/health
GET /actuator/info
```

### 探测任务管理

```
GET /api/detection/tasks
POST /api/detection/tasks
GET /api/detection/tasks/{id}
PUT /api/detection/tasks/{id}
DELETE /api/detection/tasks/{id}
```

### 创建探测任务

```
POST /api/detection/tasks
```

**请求体:**
```json
{
  "taskName": "气象观测探测-001",
  "taskType": "METEOROLOGICAL",
  "area": {
    "minLat": 20.0,
    "maxLat": 40.0,
    "minLon": 100.0,
    "maxLon": 120.0
  },
  "startTime": "2026-06-05T12:00:00Z",
  "endTime": "2026-06-05T18:00:00Z",
  "targetTypes": ["CLOUD", "TEMPERATURE_ANOMALY"],
  "detectionModel": "YOLOv8",
  "confidenceThreshold": 0.7
}
```

### 执行目标检测

```
POST /api/detection/detect
对输入图像或视频帧执行目标检测
```

**请求体:**
```json
{
  "imageData": "base64_encoded_image_data",
  "imageUrl": "https://example.com/image.jpg",
  "model": "YOLOv8",
  "confidenceThreshold": 0.7,
  "targetTypes": ["UAV", "CLOUD"]
}
```

**响应:**
```json
{
  "detectionId": "DET-20260605-001",
  "timestamp": "2026-06-05T12:30:00Z",
  "detections": [
    {
      "type": "CLOUD",
      "confidence": 0.92,
      "boundingBox": {
        "x": 100,
        "y": 200,
        "width": 150,
        "height": 100
      },
      "metadata": {
        "cloudType": "CUMULUS",
        "area": 2500.0
      }
    }
  ]
}
```

### 检测结果查询

```
GET /api/detection/results
按条件查询检测结果
```

**查询参数:**
- `taskId`: 任务 ID
- `startTime`: 开始时间
- `endTime`: 结束时间
- `targetType`: 目标类型
- `minConfidence`: 最小置信度
- `page`: 页码（默认 0）
- `size`: 每页大小（默认 20）

### 统计分析

```
GET /api/detection/statistics
获取检测任务统计信息
```

## Docker 部署

### 构建镜像

```bash
mvn clean package -DskipTests
docker build -t uav/detection-drone-service:latest -f ../docker/Dockerfile .
```

### 运行容器

```bash
docker run -d \
  --name detection-drone-service \
  -p 8091:8091 \
  -e SPRING_DATASOURCE_URL=jdbc:mysql://mysql:3306/uav_platform \
  -e SPRING_DATASOURCE_USERNAME=root \
  -e SPRING_DATASOURCE_PASSWORD=your_password \
  -e SPRING_CLOUD_NACOS_SERVER_ADDR=nacos:8848 \
  -e MODEL_ENGINE_URL=http://model-engine:8092 \
  uav/detection-drone-service:latest
```

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SERVER_PORT` | `8091` | 服务端口 |
| `SPRING_DATASOURCE_URL` | `jdbc:mysql://localhost:3306/uav_platform` | 数据库连接地址 |
| `SPRING_DATASOURCE_USERNAME` | `root` | 数据库用户名 |
| `SPRING_DATASOURCE_PASSWORD` | - | 数据库密码（必填） |
| `SPRING_CLOUD_NACOS_SERVER_ADDR` | `localhost:8848` | Nacos 注册中心地址 |
| `MODEL_ENGINE_URL` | `http://localhost:8092` | 模型引擎服务地址 |

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

启动后访问: http://localhost:8091/swagger-ui.html (SpringDoc 自动生成的 OpenAPI 文档)

## 相关文档

- [根项目 README](../README.md)
- [端口配置总表](../docs/PORTS_CONFIGURATION.md)
- [项目架构文档](../docs/architecture.md)
- [模型引擎文档](./model-engine/README.md)

---

> **最后更新**: 2026-06-05
> **版本**: 1.0
> **维护者**: UAV Platform Team
