# 基于WRF气象驱动的无人机VRP智能路径规划系统

本项目面向城市低空物流、电力巡检、应急救援、农林植保、城市管理等场景，构建一套集高精度低空气象预报、多约束智能路径规划、全栈Web可视化管理于一体的无人机智能调度系统。

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     UAV Path Planning System                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Frontend   │  │   Platform   │  │  Monitoring  │          │
│  │    Vue3      │  │   Service    │  │  Dashboard   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │     WRF      │  │    Bayes     │  │   Meteor     │          │
│  │  Processor   │  │ Assimilator  │  │  Forecaster  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                          │                                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Model-Engine (v2, 8087)                    │    │
│  │  CMA数据 → CNN订正 → U-Net降尺度 → GPR风险场 → 融合    │    │
│  │  兼容原 LSTM/XGBoost/ConvLSTM/GPR (桥接引用, 零改动)    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                    ┌──────────────┐                            │
│                    │    Path      │                            │
│                    │  Planner     │                            │
│                    └──────────────┘                            │
├─────────────────────────────────────────────────────────────────┤
│                     Edge SDK (Offline)                           │
└─────────────────────────────────────────────────────────────────┘
```

## 📂 项目结构

```
trae/                           # 项目根目录
├── api-gateway/                 # API 网关（Spring Cloud Gateway）
├── common-utils/               # 公共工具模块（JWT/熔断器/异常处理）
├── data-assimilation-platform/ # 贝叶斯同化平台（Python）
│   ├── algorithm_core/          # 核心算法库（130+ Python文件）
│   ├── service_python/         # Python API 服务
│   └── shared/protos/           # Protocol Buffers 共享定义
├── data-assimilation-service/  # 贝叶斯同化服务（Java，端口8084）
├── edge-cloud-coordinator/     # 边云协同框架（Python，Kafka/WebSocket/联邦学习）
├── fengwu-service/             # 风乌气象模型推理服务
├── meteor-forecast-service/    # 气象预测服务（Java，端口8082）
├── path-planning-service/      # 路径规划服务（Java，端口8083）
├── uav-platform-service/       # 主平台服务（Java，端口8080）
├── uav-weather-collector/      # 气象收集服务（Java，端口8086）
├── wrf-processor-service/      # WRF 气象数据处理服务（Java，端口8081）
├── uav-edge-sdk/              # 端侧 SDK（C++/Python/pybind11）
├── uav-path-planning-system/   # 旧版项目（含frontend-vue）
│   └── frontend-vue/           # 前端Vue3 (端口3000)
├── deployments/                # 部署配置
│   ├── kubernetes/             # K8s 部署清单
│   ├── monitoring/             # Prometheus/Grafana 监控
│   ├── service-mesh/           # Istio 服务网格
│   ├── observability/          # 可观测性配置
│   ├── argo/                   # ArgoCD GitOps
│   ├── streaming/              # Kafka+Flink
│   └── edge-device/            # 边缘设备部署
├── docs/                       # 文档中心
│   ├── api/                    # API 接口文档
│   ├── architecture.md         # 架构设计
│   ├── DEPLOYMENT.md           # 部署指南
│   └── DOCKER.md               # Docker 说明
├── tests/                      # 集成测试
├── scripts/                    # 构建脚本
└── tools/                      # 辅助工具
```

## 🚀 快速开始

### 环境要求

- **Docker & Docker Compose**: 容器化部署
- **Java 17+**: 后端服务
- **Python 3.8+**: 算法模块
- **Node.js 16+**: 前端开发
- **MySQL 8.0+**: 数据存储
- **Redis 6.2+**: 缓存服务

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

### 3. 启动服务

```bash
# 开发环境
docker-compose up -d --build

# 生产环境（Kubernetes）
cd deployments/kubernetes
kubectl apply -f namespace.yml
kubectl apply -f secrets.yaml
kubectl apply -f .
```

## 📚 各模块文档

### 🔬 核心算法模块

| 模块 | 路径 | 说明 |
|------|------|------|
| **algorithm_core** | [README](data-assimilation-platform/algorithm_core/README.md) | 贝叶斯同化核心算法库 |
| **Docker 部署** | [README](data-assimilation-platform/algorithm_core/docker/README.md) | 容器化部署指南 |

### ☁️ 后端服务

| 服务 | 端口 | 说明 | 熔断器 |
|------|:----:|------|:------:|
| **API Gateway** | 8088 | 统一入口（限流/熔断/路由） | ✅ |
| **WRF Processor** | 8081 | WRF 气象数据处理 | ✅ |
| **Bayes Assimilator** | 8084 | 贝叶斯同化计算（3D-VAR/4D-VAR/EnKF） | ✅ |
| **Meteor Forecaster** | 8082 | 气象预测与订正（ConvLSTM+XGBoost） | ✅ |
| **Path Planner** | 8083 | VRPTW+DE-RRT*+DWA 路径规划 | ✅ |
| **Platform Service** | 8080 | 主平台服务（认证/任务/无人机管理） | ✅ |
| **Weather Collector** | 8086 | 多源气象数据采集与融合 | ✅ |
| **FengWu Service** | - | 风乌气象模型推理服务（ONNX Runtime） | ✅ |
| **Edge-Cloud Coordinator** | 8000/8765 | 边云协同（联邦学习/WebSocket/Kafka） | ✅ |
| **common-utils** | - | 公共工具模块（JWT/熔断器/异常处理） | ⭐ |

### 🖥️ 前端与 SDK

| 组件 | 端口 | 路径 | 说明 |
|------|:----:|------|------|
| **Frontend** | 3000 | `uav-path-planning-system/frontend-vue/` | Vue3 Web 应用 |
| **Edge SDK** | - | `uav-edge-sdk/` | 端侧离线路径规划 |

## 📖 详细文档

| 文档 | 说明 | 优先级 |
|------|------|--------|
| [部署指南](DEPLOYMENT.md) | 完整的部署与运维手册 | ⭐⭐⭐ |
| [快速参考](QUICK_REFERENCE.md) | 常用命令和API速查 | ⭐⭐⭐ |
| [项目结构](docs/PROJECT_STRUCTURE.md) | 详细目录结构说明 | ⭐⭐ |
| [熔断器指南](docs/CIRCUIT_BREAKER_GUIDE.md) | 熔断器使用指南 | ⭐⭐⭐ |
| [改进报告](docs/IMPROVEMENTS_COMPLETED_REPORT.md) | 最新改进总结 | ⭐⭐ |
| [更新日志](CHANGELOG.md) | 版本更新历史 | ⭐⭐ |

## 🔧 开发指南

### 本地开发

```bash
# 启动数据库和缓存
docker-compose up -d mysql redis

# 启动各服务
cd uav-platform-service && mvn spring-boot:run

# 启动前端
cd frontend-vue && npm install && npm run dev
```

### 代码规范

```bash
# Python 代码格式化
cd data-assimilation-platform/algorithm_core
pip install -e .[dev]
black src/
flake8 src/

# Java 代码格式化
mvn spotless:apply
```

## 📊 系统功能

| 功能 | 说明 |
|------|------|
| **气象预报** | WRF + AI 双引擎，5分钟级高频更新 |
| **数据同化** | 3D-VAR/4D-VAR/EnKF 多算法融合 |
| **路径规划** | VRPTW + DE-RRT* + DWA 三层架构 |
| **风险评估** | 贝叶斯不确定性分析 |
| **动态重规划** | 5秒内响应气象突变 |

## 🎯 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| **气象** | WRF, 贝叶斯同化, GPR, NetCDF4 | - |
| **AI/ML** | ConvLSTM, XGBoost, GPR, 联邦学习(FedAvg) | - |
| **路径规划** | VRPTW, DE-RRT*, DWA, NSGA-II, 熵权法 | - |
| **后端** | Spring Boot, Spring Cloud Gateway, MyBatis-Plus, gRPC, Nacos | 3.5.x |
| **前端** | Vue3, Leaflet, ECharts, Cesium (4D轨迹) | - |
| **边缘计算** | C++, pybind11, ONNX Runtime, WebSocket, Kafka | - |
| **安全** | mTLS, JWT, 数据加密 | - |
| **部署** | Docker, Kubernetes, ArgoCD, Istio, Prometheus+Grafana | - |
| **语言** | Java 17, Python 3.8+, Dart/Flutter | - |

## 📝 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 👥 团队

成都大学无人机路径规划系统团队

## 📚 文档索引

所有模块的详细文档都已在对应目录中维护：

| 模块 | 文档路径 | 状态 |
|------|---------|------|
| **data-assimilation-platform** | [README](data-assimilation-platform/README.md) | ✅ 最新 |
| **algorithm_core** | [README](data-assimilation-platform/algorithm_core/README.md) | ✅ 最新 |
| **service_python** | [README](data-assimilation-platform/service_python/README.md) | ✅ 最新 |
| **edge-cloud-coordinator** | [README](edge-cloud-coordinator/README.md) | ✅ 最新 |
| **fengwu-service** | [README](fengwu-service/README.md) | ✅ 最新 |
| **uav-mobile-app** | [README](uav-mobile-app/README.md) | ✅ 最新 |
| **uav-edge-sdk** | [README](uav-edge-sdk/README.md) | ✅ 最新 |
| **api-gateway** | [README](api-gateway/README.md) | ✅ 最新 |
| **common-utils** | [README](common-utils/README.md) | ✅ 最新 |

### 📖 详细文档

| 文档 | 路径 | 说明 |
|------|------|------|
| **部署指南** | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | 完整部署与运维手册 |
| **快速参考** | [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) | 常用命令和API速查 |
| **架构设计** | [docs/architecture.md](docs/architecture.md) | 系统架构说明 |
| **项目结构** | [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) | 详细目录结构 |
| **更新日志** | [docs/CHANGELOG.md](docs/CHANGELOG.md) | 版本更新历史 |
| **Docker说明** | [docs/DOCKER.md](docs/DOCKER.md) | Docker部署指南 |

---

> 💡 **提示**: 如需了解特定模块的详细信息，请查看对应目录下的 README.md 文件。
---

> **最后更新**: 2026-06-03  
> **版本**: 2.3  
> **维护者**: DITHIOTHREITOL
