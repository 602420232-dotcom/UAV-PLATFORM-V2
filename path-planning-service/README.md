# 路径规划服务

## 概述

路径规划服务实现 VRPTW + DE-RRT\* + DWA 三层路径规划架构，为多无人机提供高效、安全的飞行路径。

## 三层架构

```
┌─────────────────────────────────────┐
│  顶层: VRPTW 任务调度                 │
│  多无人机分配 | 时间窗约束 | 载重约束   │
├─────────────────────────────────────┤
│  中层: DE-RRT* 全局路径规划           │
│  三维空间搜索 | 禁飞区避让 | 障碍物规避  │
├─────────────────────────────────────┤
│  底层: DWA 实时避障                    │
│  速度/角速度采样 | 轨迹评分 | 风场补偿   │
└─────────────────────────────────────┘
```

## 技术栈

- **框架**: Spring Boot 3.2.0
- **语言**: Java 17 + Python 3.8+
- **构建工具**: Maven
- **算法引擎**: Python (three_layer_planner.py)

## 服务信息

- **服务端口**: 8083
- **服务名称**: path-planning-service

## 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/planning/vrptw` | POST | VRPTW 任务调度 |
| `/api/planning/astar` | POST | A\* 全局路径规划 |
| `/api/planning/dwa` | POST | DWA 实时避障 |
| `/api/planning/full` | POST | 完整三层路径规划 |

## Python 依赖

| 包 | 版本 | 用途 |
|---|------|------|
| numpy | >=1.24.0 | 数值计算 |
| scipy | >=1.11.0 | 科学计算 |
| deap | >=1.4.0 | DE-RRT\* 差分进化 |

## 算法参数

| 参数 | 默认值 | 说明 |
|------|:------:|------|
| VRPTW 最大迭代次数 | 1000 | 任务分配优化迭代 |
| DE-RRT\* 最大迭代 | 5000 | 路径搜索迭代 |
| DWA 预测时间 | 3.0s | 轨迹预测窗口 |
| 动态重规划时间 | <5s | 气象突变响应时间 |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_PASSWORD` | （必填） | 数据库密码 |
| `planning.python-script` | `src/main/python/three_layer_planner.py` | Python 脚本路径 |
| `SERVER_PORT` | `8083` | 服务端口 |

## 构建与运行

```bash
# 构建
mvn clean package -DskipTests

# 运行
mvn spring-boot:run
```

## 配置

详见 `src/main/resources/application.yml`
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
