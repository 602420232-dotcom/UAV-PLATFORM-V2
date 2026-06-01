# 主平台服务 - uav-platform-service

## 概述

主平台服务是无人机路径规划系统的核心聚合服务。整合用户管理、任务管理、无人机管理、数据源管理、路径规划和气象数据等功能模块，同时编排 WRF 处理、贝叶斯同化、气象预测和路径规划等下游服务的完整工作流。

## 技术栈

- **框架**: Spring Boot 3.2.0
- **语言**: Java 17
- **构建工具**: Maven
- **安全**: Spring Security + JWT
- **缓存**: Redis
- **数据库**: MySQL 8.0 (MyBatis-Plus / JPA)

## 服务信息

- **服务端口**: 8080
- **服务名称**: uav-platform-service

## 功能模块

| 模块 | 说明 |
|------|------|
| **用户管理** | 用户注册、登录、RABC 权限控制 |
| **任务管理** | 任务的创建、分配、状态跟踪 |
| **无人机管理** | 无人机注册、状态监控、位置追踪 |
| **路径规划** | 编排4个下游服务完成完整路径规划 |
| **数据管理** | 多源数据源的 CRUD、连接测试 |
| **气象数据** | 获取 WRF 处理后的气象数据 |

## 接口

### 认证接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/auth/register` | POST | 用户注册 |
| `/api/v1/auth/refresh` | POST | 刷新令牌 |
| `/api/v1/auth/logout` | POST | 用户登出 |

### 数据源管理

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/data-sources` | GET/POST | 列表/创建数据源 |
| `/api/v1/data-sources/{id}` | GET/PUT/DELETE | 详情/更新/删除 |
| `/api/v1/data-sources/test` | POST | 测试数据源连接 |
| `/api/v1/data-sources/types` | GET | 数据源类型列表 |
| `/api/v1/real-data/ground-station` | GET | 地面站实时数据 |
| `/api/v1/real-data/buoy` | GET | 浮标实时数据 |
| `/api/v1/real-data/status` | GET | 数据源状态监控 |

### 平台编排接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/platform/plan` | POST | 完整路径规划（编排4个服务） |
| `/api/platform/weather` | GET | 获取综合气象数据 |
| `/api/platform/task` | POST | 任务管理 |
| `/api/platform/drones` | GET | 无人机列表 |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_PASSWORD` | （必填） | MySQL 数据库密码 |
| `JWT_SECRET` | （必填，32+字符） | JWT 签名密钥 |
| `REDIS_HOST` | `localhost` | Redis 主机地址 |
| `REDIS_PORT` | `6379` | Redis 端口 |
| `SERVER_PORT` | `8080` | 服务端口 |

## 基础设施依赖

- **MySQL 8.0**: 业务数据持久化
- **Redis 6.2+**: 会话缓存/令牌限流
- **Nacos**: 服务注册发现
- **下游服务**: wrf-processor(8081), meteor-forecast(8082), path-planning(8083), data-assimilation(8084)

## 构建与运行

```bash
# 构建
mvn clean package -DskipTests

# 运行
mvn spring-boot:run
```

## 配置

详见 `src/main/resources/application.yml`。
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
