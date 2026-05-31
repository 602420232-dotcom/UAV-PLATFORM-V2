# Docker 配置重构说明

## 概述

本次重构通过统一基础镜像和标准化Dockerfile配置，解决了原系统中7个微服务Docker配置重复的问题。

## 文件结构

```
docker/
├── base/
│   ├── Dockerfile          # 统一基础镜像（uav-base）
│   └── python/
│       └── Dockerfile      # Python支持镜像（uav-python）
└── README.md               # 本文档

scripts/
├── build-all.ps1           # Windows PowerShell构建脚本
└── build-all.sh            # Linux/Mac bash构建脚本
```

## 使用方法

### Windows环境

```powershell
cd scripts
.\build-all.ps1
```

### Linux/Mac环境

```bash
cd scripts
chmod +x build-all.sh
./build-all.sh
```

### 手动构建

#### 1. 构建基础镜像

```bash
# 构建基础Java镜像
docker build -t uav-base:latest -f docker/base/Dockerfile .

# 构建Python支持镜像
docker build -t uav-python:latest -f docker/base/python/Dockerfile .
```

#### 2. 构建服务镜像

```bash
# API Gateway
docker build -t uav-api-gateway:latest -f api-gateway/Dockerfile.runtime api-gateway/

# 数据同化服务
docker build -t uav-data-assimilation-service:latest -f data-assimilation-service/Dockerfile.runtime data-assimilation-service/

# 气象预报服务
docker build -t uav-meteor-forecast-service:latest -f meteor-forecast-service/Dockerfile.runtime meteor-forecast-service/

# 路径规划服务
docker build -t uav-path-planning-service:latest -f path-planning-service/Dockerfile.runtime path-planning-service/

# WRF处理服务
docker build -t uav-wrf-processor-service:latest -f wrf-processor-service/Dockerfile.runtime wrf-processor-service/

# UAV平台服务
docker build -t uav-uav-platform-service:latest -f uav-platform-service/Dockerfile.runtime uav-platform-service/

# UAV气象收集器
docker build -t uav-uav-weather-collector:latest -f uav-weather-collector/Dockerfile.runtime uav-weather-collector/
```

## 架构说明

### 镜像层次

```
eclipse-temurin:17-jre
    └── uav-base:latest (基础Java镜像)
            ├── uav-python:latest (Python支持)
            ├── api-gateway
            ├── uav-platform-service
            └── uav-weather-collector
    uav-python:latest
            ├── data-assimilation-service
            ├── meteor-forecast-service
            ├── path-planning-service
            └── wrf-processor-service (含netcdf-bin)
```

### 服务分类

**纯Java服务**：使用uav-base镜像
- api-gateway
- uav-platform-service
- uav-weather-collector

**Python支持服务**：使用uav-python镜像
- data-assimilation-service
- meteor-forecast-service
- path-planning-service
- wrf-processor-service（含额外netcdf-bin依赖）

## 优势

1. **维护简化**：公共配置只需修改一处
2. **构建加速**：利用Docker层缓存，基础镜像层复用
3. **一致性保证**：所有服务使用统一的JVM参数和基础环境
4. **易于扩展**：新增服务可直接基于现有基础镜像

## 注意事项

- 确保Docker已正确安装和运行
- 首次构建需要较长时间，后续构建会利用缓存加速
- 如需修改基础配置，只需更新`docker/base/Dockerfile`并重新构建基础镜像
