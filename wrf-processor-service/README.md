# WRF 气象数据处理服务

## 概述

WRF 气象数据处理服务用于解析和处理 WRF（Weather Research and Forecasting）模型输出的 NetCDF4 格式气象数据，提取低空气象参数供路径规划使用。

## 技术栈

- **框架**: Spring Boot 3.2.0
- **语言**: Java 17 + Python 3.8+
- **构建工具**: Maven
- **数据格式**: NetCDF4
- **算法引擎**: Python (wrf_processor.py)

## 服务信息

- **服务端口**: 8081
- **服务名称**: wrf-processor-service

## 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/wrf/parse` | POST | 解析 WRF 输出文件（Multipart） |
| `/api/wrf/data` | GET | 获取处理后的气象数据 |
| `/api/wrf/stats` | GET | 获取数据统计信息 |

## Python 依赖

| 包 | 版本 | 用途 |
|---|------|------|
| netCDF4 | >=1.6.0 | NetCDF4 文件解析 |
| numpy | >=1.24.0 | 数值计算 |

## 输入文件格式

- **格式**: NetCDF4 (.nc)
- **字段要求**: 需包含 temperature、humidity、wind_speed、pressure 等气象变量

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_PASSWORD` | （必填） | 数据库密码 |
| `wrf.python-script` | `src/main/python/wrf_processor.py` | Python 脚本路径 |
| `wrf.data-path` | `/data/wrf` | WRF 数据存储路径 |
| `SERVER_PORT` | `8081` | 服务端口 |

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
