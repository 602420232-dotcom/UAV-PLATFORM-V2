# 基于WRF气象驱动的无人机VRP智能路径规划系统

本项目面向城市低空物流、电力巡检、应急救援、农林植保、城市管理等场景，构建一套集高精度低空气象预报、多约束智能路径规划、全栈Web可视化管理于一体的无人机智能调度系统。

## 📋 目录

- [系统架构](#系统架构)
- [项目结构](#项目结构)
- [功能特性](#功能特性)
- [四大气象模型](#四大气象模型)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [服务与端口](#服务与端口)
- [详细文档](#详细文档)
- [开发指南](#开发指南)
- [部署指南](#部署指南)
- [故障排除](#故障排除)
- [贡献指南](#贡献指南)
- [许可证](#许可证)
- [团队与联系方式](#团队与联系方式)

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                     UAV Path Planning System                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Frontend   │  │   Platform   │  │  Monitoring  │            │
│  │    Vue3      │  │   Service    │  │  Dashboard   │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │     WRF      │  │    Bayes     │  │   Meteor     │            │
│  │  Processor   │  │ Assimilator  │  │  Forecaster  │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│                          │                                           │
├─────────────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              Model-Engine (v2, 8087)                          │  │
│  │  CMA数据 → CNN订正 → U-Net降尺度 → GPR风险场 → 融合             │  │
│  │  兼容原 LSTM/XGBoost/ConvLSTM/GPR (桥接引用，零改动)            │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                    ┌──────────────┐                                 │
│                    │    Path      │                                 │
│                    │  Planner     │                                 │
│                    └──────────────┘                                 │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Mobile     │  │ Edge SDK     │  │ Edge Cloud   │            │
│  │   App        │  │ (Offline)    │  │ Coordinator  │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

## 📂 项目结构

```
trae/
├── .github/                       # GitHub Actions 工作流
│   └── workflows/                 # CI/CD 配置
│       ├── ci.yml                # 持续集成
│       ├── ci-cd.yml             # 持续集成部署
│       ├── deploy.yml            # 部署流程
│       └── gitops.yml            # GitOps 配置
├── .vscode/                       # VS Code 配置
│   ├── launch.json               # 调试配置
│   └── settings.json             # 编辑器设置
├── api-gateway/                   # API 网关（Spring Cloud Gateway，端口 8088）
│   ├── src/main/resources/       # 配置文件
│   ├── Dockerfile                # 镜像构建
│   ├── Dockerfile.fast           # 快速构建版本
│   ├── Dockerfile.runtime        # 运行时版本
│   ├── pom.xml                   # Maven 配置
│   └── README.md
├── common-utils/                  # 公共工具模块（JWT/熔断器/异常处理）
│   ├── src/main/java/com/uav/common/ # Java 工具类
│   ├── src/main/python/          # Python 工具模块
│   ├── pom.xml
│   └── README.md
├── data-assimilation-platform/    # 贝叶斯同化平台（Python）
│   ├── benchmarks/               # 基准测试
│   ├── deployments/              # 平台部署配置
│   ├── docs/                     # 平台文档
│   ├── scripts/                  # 脚本工具
│   ├── shared/                   # 共享代码
│   ├── service_spring/           # Spring Boot API 服务
│   ├── docker-compose.yml        # 本地开发部署
│   ├── pyproject.toml            # Python 依赖
│   └── README.md
├── data-assimilation-service/     # 贝叶斯同化服务（Java，端口 8084）
│   ├── Dockerfile
│   ├── Dockerfile.runtime
│   ├── pom.xml
│   └── README.md
├── edge-cloud-coordinator/        # 边云协同框架（Python，端口 8000/8765）
│   ├── tests/                    # 测试用例
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── README.md
│   └── *.py                      # 核心代码文件
├── fengwu-service/                # 风乌气象模型推理服务（Python，端口 8085）
│   ├── app.py                    # FastAPI 主应用
│   ├── inference_engine.py       # 模型推理引擎
│   ├── security_middleware.py    # 安全中间件
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── fenglei-service/               # 风雷区域模式数据服务（Python，端口 8091）
│   ├── app.py                    # FastAPI 主应用
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── tianzi-service/                # 天资气象分析服务（Python，端口 8090）
│   ├── app.py                    # FastAPI 主应用
│   ├── inference_engine.py       # 模型推理引擎
│   ├── security_middleware.py    # 安全中间件
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── meteor-forecast-service/       # 气象预测服务（Java，端口 8082）
│   ├── src/main/java/com/uav/meteor/forecast/
│   ├── src/main/python/          # Python 算法引擎
│   ├── Dockerfile
│   ├── Dockerfile.runtime
│   ├── pom.xml
│   └── README.md
├── path-planning-service/         # 路径规划服务（Java，端口 8083）
│   ├── Dockerfile
│   ├── Dockerfile.runtime
│   ├── pom.xml
│   └── README.md
├── wrf-processor-service/         # WRF 气象数据处理服务（Java，端口 8081）
│   ├── src/main/java/com/uav/wrf/processor/
│   ├── src/main/python/          # Python 处理脚本
│   ├── Dockerfile
│   ├── Dockerfile.local
│   ├── Dockerfile.runtime
│   ├── pom.xml
│   └── README.md
├── buoy-weather-service/          # 浮标气象数据服务
│   ├── pom.xml
│   └── README.md
├── ground-station-weather-service/ # 地面站气象数据服务
│   ├── pom.xml
│   └── README.md
├── satellite-weather-service/     # 卫星气象数据服务
│   ├── pom.xml
│   └── README.md
├── radiosonde-weather-service/    # 探空气象数据服务
│   ├── pom.xml
│   └── README.md
├── detection-drone-service/       # 检测无人机服务
│   ├── pom.xml
│   └── README.md
├── uav-platform-service/          # UAV 平台服务（Java，端口 8080）
│   └── 注：该服务包含在 docker-compose.yml 中
├── uav-weather-collector/         # UAV 气象数据采集服务
│   └── 注：该服务包含在 docker-compose.yml 中
├── model-engine/                  # AI 模型训练引擎（Python，端口 8087）
│   ├── api/                      # API 接口
│   ├── data_pipeline/            # 数据处理管道
│   ├── cnn_corrector/            # CNN 订正模块
│   ├── unet_downscaler/          # UNet 降尺度
│   ├── gpr_risk/                 # GPR 风险评估
│   ├── fusion/                   # 数据融合
│   ├── control/                  # 模型预测控制
│   ├── path_planning/            # 路径规划算法
│   ├── multi_uav/                # 多无人机协同
│   ├── active_obs/               # 主动观测
│   ├── integration/              # 集成适配
│   ├── scripts/                  # 训练脚本
│   ├── tests/                    # 测试用例
│   ├── checkpoints/              # 模型检查点
│   ├── Dockerfile
│   ├── PIPELINE.md
│   ├── PIPELINE_VERIFICATION.md
│   ├── README.md
│   ├── pyproject.toml
│   └── requirements.txt
├── uav-edge-sdk/                  # 端侧 SDK（C++/Python/pybind11）
│   ├── edge_sdk/                 # Python SDK
│   ├── include/                  # C++ 头文件
│   ├── src/                      # C++ 源文件
│   ├── tests/                    # 测试用例
│   ├── .github/workflows/
│   ├── CMakeLists.txt
│   ├── README.md
│   └── pyproject.toml
├── uav-mobile-app/                # 跨平台移动应用（Flutter）
│   ├── android/                  # Android 项目
│   ├── ios/                      # iOS 项目
│   ├── linux/                    # Linux 桌面
│   ├── macos/                    # macOS 桌面
│   ├── assets/                   # 资源文件
│   ├── docs/                     # 文档
│   ├── lib/                      # Flutter 代码
│   ├── .env.example
│   ├── Dockerfile.web
│   ├── README.md
│   └── WINDOWS_BUILD_README.md
├── uav-path-planning-system/      # 前端项目
│   └── frontend-vue/              # 前端 Vue3（端口 3000）
│       ├── .storybook/           # Storybook 组件库
│       ├── public/               # 静态资源
│       ├── src/                  # 源代码
│       │   ├── api/             # API 调用
│       │   ├── components/      # 组件
│       │   ├── composables/     # 组合式函数
│       │   ├── locales/         # 国际化
│       │   ├── stores/          # 状态管理
│       │   ├── utils/           # 工具函数
│       │   ├── views/           # 页面视图
│       │   └── App.vue
│       ├── tests/                # 测试
│       ├── nginx.conf
│       ├── package.json
│       └── README.md
├── deployments/                   # 部署配置
│   ├── argo/                     # Argo CD 配置
│   ├── backup/                   # 备份配置
│   ├── database/                 # 数据库脚本
│   ├── edge/                     # 边缘设备部署
│   ├── edge-device/              # 边缘设备 Docker
│   ├── elk/                      # ELK 日志栈
│   ├── kubernetes/               # K8s 部署清单
│   │   ├── *.yml                 # 各服务 K8s 配置
│   │   └── README.md
│   ├── monitoring/               # Prometheus/Grafana 监控
│   ├── multi-region/             # 多区域部署
│   ├── observability/            # 可观测性配置
│   ├── service-mesh/             # Istio 服务网格
│   ├── streaming/                # 流处理配置
│   ├── infrastructure.yml
│   └── README.md
├── docs/                          # 文档中心
│   ├── api/                      # API 接口文档
│   ├── archive/                  # 归档文档
│   ├── deployment/               # 部署文档
│   ├── external/                 # 外部文档
│   ├── guides/                   # 使用指南
│   ├── reports/                  # 项目报告
│   ├── security/                 # 安全文档
│   ├── tests/                    # 测试文档
│   ├── troubleshooting/          # 故障排除
│   ├── *.md                      # 各类文档
│   └── README.md
├── scripts/                       # 构建与管理脚本
│   ├── backup/                   # 备份脚本
│   ├── *.py, *.sh, *.ps1         # 各类工具脚本
│   └── README.md
├── tests/                         # 项目测试
│   ├── e2e/                      # 端到端测试
│   ├── performance/              # 性能测试
│   ├── *.py                      # 测试脚本
│   └── README.md
├── docker/                        # Docker 基础镜像
│   ├── base/                     # 基础镜像
│   └── README.md
├── tools/                         # 工具集
│   └── mypanel/                  # 管理面板工具
├── .env                          # 环境变量（请勿提交）
├── .env.example                  # 环境变量示例
├── .env.dev                      # 开发环境变量
├── .env.ci                       # CI 环境变量
├── .gitignore
├── .gitattributes
├── .pre-commit-config.yaml      # Git 前置钩子配置
├── .flake8                       # Python 代码风格
├── .cursorignore                 # Cursor 索引忽略
├── LICENSE
├── PROJECT_DOCUMENT_INDEX.md    # 文档索引
├── QUICKSTART.md                # 快速开始指南
├── TEAM_SETUP.md                # 团队设置指南
├── checkstyle.xml               # Java 代码风格
├── docker-compose.yml           # 开发环境 Docker Compose
├── docker-compose.dev.yml       # 开发环境覆盖
├── docker-compose.dockerhub.yml # Docker Hub 配置
├── docker-compose.jvm.env       # JVM 环境变量
├── mkdocs.yml                   # MkDocs 文档配置
├── mvnw, mvnw.cmd               # Maven Wrapper
├── package.json                 # Node.js 依赖
├── pom.xml                      # Maven 主配置
├── pyproject.toml               # Python 项目配置
├── pyrightconfig.json           # Pyright 配置
├── qodana.yaml                  # Qodana 代码质量
├── sonar-project.properties     # SonarQube 配置
├── owasp-suppressions.xml       # OWASP 安全扫描配置
└── README.md
```

## ✨ 功能特性

| 功能模块 | 描述 |
|---------|------|
| **气象预报** | WRF + AI 双引擎，5分钟级高频更新，支持ConvLSTM+XGBoost |
| **数据同化** | 3D-VAR/4D-VAR/EnKF 多算法融合，支持GPU加速 |
| **路径规划** | VRPTW + DE-RRT* + DWA 三层架构，考虑气象约束 |
| **风险评估** | 贝叶斯不确定性分析，动态风险场计算 |
| **动态重规划** | 5秒内响应气象突变，实时更新路径 |
| **边云协同** | 离线评估、边缘任务队列、联邦学习 |
| **移动终端** | Flutter跨平台应用（iOS/Android），实时监控 |
| **Web 平台** | Vue3可视化管理，地图、图表、实时监控一体化 |
| **监控告警** | Prometheus+Grafana，ELK日志聚合，SkyWalking链路追踪 |
| **熔断器保护** | Resilience4j 防止级联故障，完善的监控API |

## 🌤️ 四大气象模型

本项目集成了四个核心气象模型，覆盖不同空间分辨率和时间尺度的气象预测需求：

### SWC-WRF（WRF气象数据处理服务）

- **技术栈**: Spring Boot 3.5.14 + Python 3.8+
- **端口**: 8081
- **服务路径**: `wrf-processor-service/`
- **功能**: 解析和处理 WRF（Weather Research and Forecasting）模型输出的 NetCDF4 格式气象数据，提取低空气象参数供路径规划使用
- **输入**: NetCDF4 (.nc) 格式文件，包含 temperature、humidity、wind_speed、pressure 等气象变量
- **部署方式**: Docker Compose / Kubernetes
- **K8s配置**: 单副本部署，支持持久化存储挂载

### FengWu（风乌气象模型推理服务）

- **技术栈**: Python 3.11 + FastAPI + ONNX Runtime
- **端口**: 8085
- **服务路径**: `fengwu-service/`
- **功能**: 基于 ONNX 推理引擎运行深度学习全球天气预报模型，接收 ERA5 大气数据并输出 0~14 天的全球气象预报
- **输入**: T+0h 和 T+6h 时刻的 ERA5 大气数据（69个变量，形状 69×721×1440）
- **部署方式**: Docker Compose / Kubernetes
- **K8s配置**: 单副本部署，支持 GPU 加速推理

### TianZi（天资高分辨率气象分析服务）

- **技术栈**: Python 3.11 + FastAPI + ONNX Runtime
- **端口**: 8090
- **服务路径**: `tianzi-service/`
- **功能**: 基于 TianZi 深度学习模型的高分辨率气象分析服务，支持最高 1km 分辨率分析
- **分析模式**: 分析、预报、数据同化
- **部署方式**: Docker Compose / Kubernetes
- **安全认证**: API Key + JWT 双重认证
- **数据源**: CMA GRAPES_GFS 全球谱模式（0.25° ≈ 25km 分辨率）

### FengLei（风雷区域模式数据服务）

- **技术栈**: Python 3.11 + xarray + requests
- **集成位置**: `model-engine/data_pipeline/`
- **功能**: 基于 CMA GRAPES_MESO 中尺度区域模式，提供高分辨率区域气象预报数据
- **分辨率**: 3km（精细网格）
- **数据源**: CMA API（中国气象局）
- **更新频率**: 每 30 分钟自动更新
- **输入参数**: GRIB 格式数据，包含 6 个气压层（1000~300hPa）

### 四模型融合架构

四个气象模型通过 `model-engine` 进行动态加权融合：

| 模型 | 分辨率 | 权重 | 角色定位 |
|------|--------|:---:|---------|
| **SWC-WRF** | 3km | 0.20 | 区域气象数据基础 |
| **FengWu** | 25km | 0.15 | 全球背景场约束 |
| **TianZi** | 25km | 0.25 | 全球模式参考 |
| **FengLei** | 3km | 0.60 | 区域高分辨率核心 |

### 数据处理流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    四大气象模型输入层                           │
│  [SWC-WRF]  [FengWu]  [TianZi]  [FengLei]                      │
│     3km       25km      25km      3km                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │ 统一重采样到 3km 网格
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    时空配准与异常检测                           │
│  双线性插值 → 地形校正 → 时间偏差加权 → 异常值修复               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    动态加权融合                                 │
│  FengWu(0.15) + TianZi(0.25) + FengLei(0.60) + WRF(0.20)      │
│  → 物理约束检查 → CNN空间订正                                   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    概率 U-Net 降尺度                           │
│  3km → 1km 分辨率，输出均值+方差                               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EnKF 贝叶斯同化                              │
│  融合观测数据（无人机回传/气象站）→ GPR风险场计算               │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Path Planning (8083)│
              │   风险感知路径规划     │
              └───────────────────────┘
```

## 🛠️ 技术栈

| 类别 | 技术 | 版本/说明 |
|------|------|----------|
| **后端框架** | Spring Boot | 3.5.14 |
| **服务发现** | Nacos | 2.x |
| **API 网关** | Spring Cloud Gateway | 2025.0.0 |
| **数据库** | MySQL | 8.0+ |
| **缓存** | Redis | 6.2+ |
| **消息队列** | Kafka | 7.4.0 |
| **持久层** | MyBatis Plus | 3.5.9 |
| **安全认证** | JWT + Spring Security | 0.12.6 |
| **熔断器** | Resilience4j | 2.3.0 |
| **链路追踪** | SkyWalking | 9.2.0 |
| **前端框架** | Vue 3 + TypeScript | - |
| **移动框架** | Flutter/Dart | 3.2.0+ |
| **AI/ML** | PyTorch, XGBoost, ONNX Runtime | - |
| **气象模型** | WRF, FengWu (风乌) | - |
| **容器化** | Docker, Docker Compose | 19.03+ |
| **编排** | Kubernetes, ArgoCD | 1.19+ |
| **监控** | Prometheus, Grafana, Jaeger | - |
| **日志** | ELK Stack (Elasticsearch + Logstash + Kibana) | - |

## 🚀 快速开始

### 环境要求

- **Docker & Docker Compose**: 容器化部署（19.03+ / 1.25+）
- **Java 17+**: 后端服务
- **Python 3.8+**: 算法模块
- **Node.js 16+**: 前端开发
- **MySQL 8.0+**: 数据存储
- **Redis 6.2+**: 缓存服务
- **Maven 3.6+**: 项目构建

### 1. 克隆项目

```bash
git clone https://github.com/602420232-dotcom/weather
cd trae
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库密码、服务端口等
```

### 3. 构建并启动服务（开发环境）

```bash
docker-compose up -d --build
```

### 4. 验证部署

```bash
# 检查服务状态
docker-compose ps

# 访问以下服务
# - 前端应用：http://localhost:3000
# - API 网关：http://localhost:8088/actuator/health
# - Nacos 控制台：http://localhost:8848/nacos
```

### 5. 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f wrf-processor
```

## 📡 服务与端口

| 服务名称 | 端口 | 说明 | 模块路径 | 健康检查 |
|---------|:---:|------|---------|---------|
| **API Gateway** | 8088 | API 网关（限流/熔断/路由） | `api-gateway/` | `/actuator/health` |
| **WRF Processor** | 8081 | WRF 气象数据处理 | `wrf-processor-service/` | `/actuator/health` |
| **Meteor Forecast** | 8082 | 气象预测与订正（ConvLSTM+XGBoost） | `meteor-forecast-service/` | `/actuator/health` |
| **Path Planning** | 8083 | VRPTW+DE-RRT*+DWA 路径规划 | `path-planning-service/` | `/actuator/health` |
| **Data Assimilation** | 8084 | 贝叶斯同化计算（3D-VAR/4D-VAR/EnKF） | `data-assimilation-service/` | `/actuator/health` |
| **FengWu Service** | 8085 | 风乌气象模型推理服务 | `fengwu-service/` | `/health` |
| **TianZi Service** | 8090 | 天资高分辨率气象分析服务 | `tianzi-service/` | `/health` |
| **FengLei Service** | 8091 | 风雷区域模式数据服务 | `fenglei-service/` | `/health` |
| **Edge Cloud Coordinator** | 8000/8765 | 边云协同框架（联邦学习/WebSocket/Kafka） | `edge-cloud-coordinator/` | `/health` |
| **Frontend Vue** | 3000 | Vue3 Web 应用 | `uav-path-planning-system/frontend-vue/` | - |
| **MySQL** | 3306 | 关系型数据库 | 容器服务 | - |
| **Redis** | 6379 | 缓存与消息队列 | 容器服务 | `ping` |
| **Nacos** | 8848 | 服务发现与配置中心 | 容器服务 | `/nacos` |
| **Kafka** | 9092 | 消息流处理 | 容器服务 | - |
| **Zookeeper** | 2181 | Kafka 协调服务 | 容器服务 | - |

## 📚 详细文档

| 文档 | 说明 | 优先级 |
|------|------|--------|
| [部署指南](docs/DEPLOYMENT.md) | 完整的部署与运维手册 | ⭐⭐⭐ |
| [架构设计](docs/architecture.md) | 系统架构设计文档 | ⭐⭐⭐ |
| [项目结构](docs/PROJECT_STRUCTURE.md) | 详细目录结构说明 | ⭐⭐ |
| [快速参考](docs/QUICK_REFERENCE.md) | 常用命令和API速查 | ⭐⭐⭐ |
| [熔断器指南](docs/guides/CIRCUIT_BREAKER_GUIDE.md) | Resilience4j 熔断器使用指南 | ⭐⭐⭐ |
| [API 文档](docs/api/API_DOCUMENTATION.md) | 完整 API 接口文档 | ⭐⭐⭐ |
| [Docker 指南](docs/DOCKER.md) | Docker 使用说明 | ⭐⭐ |
| [K8s 部署](deployments/kubernetes/README.md) | Kubernetes 部署配置 | ⭐⭐⭐ |
| [更新日志](docs/CHANGELOG.md) | 版本更新历史 | ⭐⭐ |
| [端口配置](docs/PORTS_CONFIGURATION.md) | 各服务端口详细说明 | ⭐⭐ |
| [故障排除](docs/guides/TROUBLESHOOTING.md) | 常见问题解答 | ⭐⭐⭐ |
| [生产配置](docs/guides/PRODUCTION_SECRETS_GUIDE.md) | 生产环境配置指南 | ⭐⭐⭐ |

## 👨‍💻 开发指南

### 后端开发

1. **启动基础设施服务**
    ```bash
    docker-compose up -d mysql redis nacos
    ```

2. **构建项目**
    ```bash
    mvn clean install -DskipTests
    ```

3. **启动服务**
    ```bash
    # 启动各个微服务
    cd wrf-processor-service && mvn spring-boot:run
    cd data-assimilation-service && mvn spring-boot:run
    cd meteor-forecast-service && mvn spring-boot:run
    cd path-planning-service && mvn spring-boot:run
    ```

4. **代码格式化**
    ```bash
    mvn spotless:apply
    ```

### 前端开发

```bash
# 安装依赖
cd uav-path-planning-system/frontend-vue
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

### 移动应用开发

```bash
cd uav-mobile-app

# 安装依赖
flutter pub get

# 运行 Android
flutter run -d android

# 运行 iOS
flutter run -d ios

# 测试
flutter test
```

### AI 模型训练

```bash
cd model-engine

# 运行自动化训练
python scripts/train_all.py

# 或者单独运行
python scripts/train_cnn.py
python scripts/train_unet.py
python scripts/train_xgboost.py
```

## 📦 部署指南

详细部署说明请查看 [部署指南](docs/DEPLOYMENT.md)。

### Docker Compose（开发）

```bash
# 完整启动
docker-compose up -d --build

# 仅启动基础设施
docker-compose up -d mysql redis nacos kafka

# 停止所有服务
docker-compose down

# 停止并删除数据（谨慎使用）
docker-compose down -v
```

### Kubernetes（生产）

```bash
cd deployments/kubernetes

# 创建命名空间
kubectl apply -f namespace.yml

# 配置密钥
kubectl apply -f secrets.yaml

# 部署所有服务
kubectl apply -f .

# 查看部署状态
kubectl get pods -n uav-platform
```

## 🔧 故障排除

### 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| **服务启动失败** | 数据库连接失败 | 检查 .env 文件中的 DB 配置 |
| **端口已被占用** | 端口被其他进程占用 | 修改 .env 中的端口配置，或停止占用进程 |
| **Maven 依赖下载失败** | 网络问题或镜像源不可达 | 配置 Maven 镜像源，如阿里云 |
| **Nacos 服务注册失败** | Nacos 未就绪 | 检查 Nacos 状态，等待其完全启动 |
| **前端无法连接后端** | CORS 或网络问题 | 检查 CORS 配置，或启动开发环境代理 |
| **Java 版本不匹配** | 环境使用旧版 Java | 切换到 Java 17+，或使用 Docker |
| **WebSocket 连接失败** | 防火墙或代理问题 | 检查 WebSocket 端口是否开放 |

### 调试命令

```bash
# 查看服务日志
docker-compose logs <service-name> -f

# 进入容器
docker-compose exec <service-name> sh

# 检查网络
docker network ls

# 清理无用镜像
docker image prune -f
```

## 🤝 贡献指南

我们非常欢迎社区贡献！请遵循以下流程：

1. **Fork 本仓库**
2. **创建特性分支** (`git checkout -b feature/AmazingFeature`)
3. **提交更改** (`git commit -m 'Add some AmazingFeature'`)
4. **推送到分支** (`git push origin feature/AmazingFeature`)
5. **创建 Pull Request**

### 开发规范

- **代码风格**：遵循 Java/C++/Python 各语言标准规范
- **提交信息**：使用语义化提交信息
- **测试**：新增功能需包含单元测试
- **文档**：修改代码时同步更新相关文档
- **PR 描述**：详细描述改动内容和相关 Issue

## 📄 许可证

本项目采用 **MIT License** - 详见 [LICENSE](LICENSE) 文件

## 👥 团队与联系方式

- **维护者**: DITHIOTHREITOL
- **团队**: 成都大学无人机路径规划系统团队
- **问题反馈**: 请通过 GitHub Issues 提交问题
- **文档问题**: 如有文档建议，请创建 Issue

## 📚 模块文档索引

所有模块的详细文档：

| 模块 | 文档路径 |
|------|---------|
| **uav-mobile-app** | [README](uav-mobile-app/README.md) |
| **wrf-processor-service** | [README](wrf-processor-service/README.md) |
| **data-assimilation-service** | [README](data-assimilation-service/README.md) |
| **meteor-forecast-service** | [README](meteor-forecast-service/README.md) |
| **path-planning-service** | [README](path-planning-service/README.md) |
| **fengwu-service** | [README](fengwu-service/README.md) |
| **tianzi-service** | [README](tianzi-service/README.md) |
| **fenglei-service** | [README](fenglei-service/README.md) |
| **buoy-weather-service** | [README](buoy-weather-service/README.md) |
| **ground-station-weather-service** | [README](ground-station-weather-service/README.md) |
| **satellite-weather-service** | [README](satellite-weather-service/README.md) |
| **radiosonde-weather-service** | [README](radiosonde-weather-service/README.md) |
| **detection-drone-service** | [README](detection-drone-service/README.md) |
| **edge-cloud-coordinator** | [README](edge-cloud-coordinator/README.md) |
| **model-engine** | [README](model-engine/README.md) |
| **api-gateway** | [README](api-gateway/README.md) |
| **common-utils** | [README](common-utils/README.md) |
| **data-assimilation-platform** | [README](data-assimilation-platform/README.md) |
| **frontend-vue** | [README](uav-path-planning-system/frontend-vue/README.md) |
| **deployments** | [README](deployments/README.md) |
| **docs** | [README](docs/README.md) |

---

## 🌟 致谢

感谢所有为本项目做出贡献的开发者！

---

> **最后更新**: 2026-06-08  
> **版本**: 3.3.0  
> **维护者**: UAV DevOps Team
