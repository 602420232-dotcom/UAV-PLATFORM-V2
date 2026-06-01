# UAV Path Planning System - Project Structure Guide

## 📂 目录结构概览

```
trae/
│
├── 📦 后端服务 (Java Spring Boot)
│   ├── api-gateway/              # API网关 (端口 8088)
│   ├── uav-platform-service/    # 主平台服务 (端口 8080)
│   ├── wrf-processor-service/   # WRF气象处理 (端口 8081)
│   ├── meteor-forecast-service/  # 气象预测服务 (端口 8082)
│   ├── path-planning-service/   # 路径规划服务 (端口 8083)
│   ├── data-assimilation-service/  # 数据同化服务 (端口 8084)
│   ├── uav-weather-collector/  # 气象数据采集 (端口 8086)
│   ├── common-utils/            # 公共工具模块 ⭐
│   └── common-dependencies/    # 公共依赖管理
│
├── 🐍 算法模块 (Python)
│   ├── data-assimilation-platform/  # 贝叶斯同化平台
│   │   ├── algorithm_core/      # 核心算法库
│   │   ├── examples/           # 使用示例
│   │   ├── tests/              # 测试
│   │   └── shared/protos/       # Protocol Buffers
│   ├── edge-cloud-coordinator/ # 边云协同
│   └── wrf-processor/          # WRF数据处理
│
├── 🌐 前端 (Vue3)
│   └── uav-path-planning-system/frontend-vue/
│
├── 🖥️ 边缘计算 (C++/Python)
│   └── uav-edge-sdk/           # 端侧SDK
│
├── 📋 部署配置
│   ├── kubernetes/             # K8s部署
│   ├── docker-compose.yml      # Docker编排
│   ├── monitoring/             # 监控配置
│   ├── service-mesh/            # Istio服务网格
│   └── edge-device/            # 边缘设备部署
│
├── 📖 文档
│   ├── docs/                   # 文档中心
│   ├── README.md               # 项目总览
│   ├── CHANGELOG.md           # 更新日志
│   └── DEPLOYMENT.md          # 部署指南
│
└── 🛠️ 工具
    ├── scripts/                # 构建脚本
    └── tests/                  # 集成测试
```

---

## 📦 Java 后端服务详解

### common-utils ⭐ (公共工具模块)

**路径**: `common-utils/`
**说明**: 所有Java服务的公共依赖，提供通用功能

**核心功能**:
```
common-utils/
├── src/main/java/com/uav/common/
│   ├── audit/                 # 安全审计
│   │   └── SecurityAuditor.java
│   ├── config/                # 配置类
│   │   ├── CommonSecurityConfig.java   # 安全配置
│   │   └── NacosConfigRefresher.java    # 配置刷新
│   ├── dto/                   # 数据传输对象
│   │   ├── AssimilationRequest.java
│   │   ├── ForecastRequest.java
│   │   └── PathPlanningRequest.java
│   ├── exception/             # 异常处理
│   │   ├── BusinessException.java
│   │   ├── GlobalExceptionHandler.java
│   │   └── ServiceUnavailableException.java
│   ├── resilience/            # 弹性机制 ⭐
│   │   ├── ResilienceConfig.java           # 熔断器配置
│   │   ├── CircuitBreakerService.java     # 服务调用封装
│   │   └── CircuitBreakerController.java  # 监控API
│   ├── security/              # 安全认证
│   │   ├── JwtAuthenticationFilter.java
│   │   ├── JwtSecurityConfig.java
│   │   └── CsrfOriginFilter.java
│   └── utils/                # 工具类
│       └── PythonExecutor.java
└── src/main/resources/
    ├── application.yml
    └── resilience4j-circuitbreaker.yml  # 熔断器配置
```

**Maven依赖**:
```xml
<dependency>
    <groupId>com.uav</groupId>
    <artifactId>common-utils</artifactId>
</dependency>
```

### api-gateway (API网关)

**路径**: `api-gateway/`
**端口**: 8088
**技术**: Spring Cloud Gateway

**路由配置**:
```yaml
routes:
  - /api/v1/**              → uav-platform-service:8080
  - /api/wrf/**             → wrf-processor-service:8081
  - /api/forecast/**        → meteor-forecast-service:8082
  - /api/planning/**        → path-planning-service:8083
  - /api/assimilation/**    → data-assimilation-service:8084
```

**熔断器保护**: ✅ 通过 common-utils Resilience4j

### 后端服务端口映射

| 服务 | 端口 | 依赖服务 |
|------|------|---------|
| api-gateway | 8088 | Nacos, Redis |
| uav-platform-service | 8080 | MySQL, Redis |
| wrf-processor-service | 8081 | MySQL |
| meteor-forecast-service | 8082 | MySQL, Redis |
| path-planning-service | 8083 | MySQL, Redis |
| data-assimilation-service | 8084 | MySQL |
| uav-weather-collector | 8086 | MySQL, Redis |

---

## 🐍 Python 算法模块详解

### data-assimilation-platform ⭐

**路径**: `data-assimilation-platform/`
**说明**: 贝叶斯同化核心算法库

**目录结构**:
```
data-assimilation-platform/
├── algorithm_core/              # 核心算法
│   ├── src/
│   │   ├── bayesian_assimilation/  # 贝叶斯同化
│   │   │   ├── models/           # 模型
│   │   │   ├── assimilation/     # 同化算法
│   │   │   └── utils/            # 工具
│   │   └── tests/                # 测试
│   ├── examples/                 # 示例
│   ├── docker/                  # Docker配置
│   └── requirements.txt
│
├── service_spring/              # Java服务封装
│   └── src/
│       ├── main/java/
│       └── test/
│
└── shared/protos/               # Protocol Buffers
    ├── common/
    └── uav/
```

**核心算法**:
- 3D-VAR 同化
- 4D-VAR 同化
- Ensemble Kalman Filter (EnKF)
- 贝叶斯优化

### edge-cloud-coordinator

**路径**: `edge-cloud-coordinator/`
**说明**: 边云协同框架

**功能**:
- WebSocket实时通信
- Kafka消息队列
- 联邦学习支持
- 边缘AI推理

---

## 🌐 前端结构

### Vue3 Web应用

**路径**: `uav-path-planning-system/frontend-vue/`

**技术栈**:
- Vue 3.3+
- Vite 4.0+
- TypeScript 5.0+
- Pinia 状态管理
- Vue Router 4.0

**目录结构**:
```
frontend-vue/
├── src/
│   ├── api/               # API调用
│   ├── components/        # 组件
│   ├── views/            # 页面
│   ├── stores/           # Pinia状态
│   ├── router/           # 路由
│   ├── utils/            # 工具
│   └── assets/           # 静态资源
├── public/               # 公共资源
├── package.json
└── vite.config.ts
```

---

## 🖥️ 边缘SDK结构

### uav-edge-sdk

**路径**: `uav-edge-sdk/`

**语言支持**:
- C++ (核心算法)
- Python (快速原型)
- pybind11 (Python绑定)

**功能**:
- 离线路径规划
- 本地气象处理
- 边缘推理加速

---

## 📋 部署配置详解

### Kubernetes部署

**路径**: `deployments/kubernetes/`

**文件结构**:
```
kubernetes/
├── namespace.yml           # 命名空间
├── secrets.yml             # 密钥
├── configmap.yml           # 配置
├── deployment-*.yml        # 服务部署
├── service-*.yml          # 服务暴露
└── ingress.yml             # 入口配置
```

### Docker Compose

**路径**: `docker-compose.yml`

**服务编排**:
```yaml
services:
  mysql:                    # 数据库
  redis:                   # 缓存
  nacos:                   # 注册中心
  api-gateway:             # 网关
  uav-platform-service:    # 主服务
  # ... 其他服务
```

### 监控栈

**路径**: `deployments/monitoring/`

**组件**:
```
monitoring/
├── docker-compose.monitoring.yml
├── prometheus/             # Prometheus配置
│   ├── prometheus.yml
│   └── alerts.yml
├── grafana/               # Grafana仪表板
├── alertmanager/          # 告警管理
├── logstash/              # 日志处理
│   └── pipeline/
└── alert-webhook/         # 告警Webhook
```

**访问地址**:
| 服务 | URL | 端口 |
|------|-----|------|
| Grafana | http://localhost:3000 | 3000 |
| Prometheus | http://localhost:9090 | 9090 |
| Kibana | http://localhost:5601 | 5601 |
| Alertmanager | http://localhost:9093 | 9093 |
| Jaeger | http://localhost:16686 | 16686 |

---

## 📖 文档结构

### 文档目录

**路径**: `docs/`

```
docs/
├── README.md                    # 文档索引
├── architecture.md             # 架构设计
├── DEPLOYMENT.md              # 部署指南
├── DOCKER.md                  # Docker说明
├── API文档/
│   └── README.md
├── 安全相关/
│   ├── security_audit_report.md
│   ├── CIRCUIT_BREAKER_GUIDE.md
│   └── CIRCUIT_BREAKER_USAGE_EXAMPLES.md
└── 改进相关/
    ├── IMPROVEMENTS_COMPLETED_REPORT.md
    ├── AUTO_FIXES_SUMMARY.md
    └── PROJECT_QUALITY_AUDIT_FINAL_REPORT.md
```

### 关键文档

| 文档 | 说明 | 优先级 |
|------|------|--------|
| README.md | 项目总览和快速开始 | ⭐⭐⭐ |
| DEPLOYMENT.md | 完整部署指南 | ⭐⭐⭐ |
| CHANGELOG.md | 版本更新历史 | ⭐⭐ |
| CIRCUIT_BREAKER_GUIDE.md | 熔断器使用指南 | ⭐⭐⭐ |
| IMPROVEMENTS_COMPLETED_REPORT.md | 改进总结报告 | ⭐⭐ |

---

## 🛠️ 工具和脚本

### scripts/ 目录

**路径**: `scripts/`

```
scripts/
├── build_all.sh               # 构建所有服务
├── deploy.sh                  # 部署脚本
├── backup.sh                  # 备份脚本
├── restore.sh                 # 恢复脚本
├── health_check.sh            # 健康检查
├── monitoring/                # 监控脚本
│   ├── prometheus_check.sh
│   └── grafana_backup.sh
└── Python工具/
    ├── batch_fix_print.ps1           # print语句替换
    ├── auto_generate_tests.py         # 测试生成
    ├── apply_type_annotations.py      # 类型注解
    └── complete_unit_tests.py        # 测试补全
```

---

## 🔧 开发环境配置

### IDE配置

**推荐IDE**:
- IntelliJ IDEA (Java)
- VS Code (Python/全栈)
- PyCharm (Python)

### 环境变量

```bash
# .env 文件
DB_PASSWORD=changeme123
JWT_SECRET=your_jwt_secret_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
NACOS_ADDR=localhost:8848
```

### 构建命令

```bash
# 构建所有Java服务
mvn clean package -DskipTests

# 构建前端
cd uav-path-planning-system/frontend-vue
npm install && npm run build

# 启动所有服务
docker-compose up -d
```

---

## 📊 服务依赖关系图

```
                    ┌─────────────┐
                    │   Client   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ API Gateway │ :8088
                    │  (熔断器)   │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│    Platform   │  │    Meteor     │  │    Path      │
│   Service    │  │   Forecaster   │  │   Planner     │
│   :8080      │  │   :8082       │  │   :8083      │
│  (认证/任务)  │  │  (气象预测)   │  │  (路径规划)   │
└───────────────┘  └───────────────┘  └───────────────┘
        │                  │                  │
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│    MySQL      │  │    Redis      │  │    Python     │
│   Database    │  │    Cache      │  │   Algorithm   │
└───────────────┘  └───────────────┘  └───────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Monitoring │
                    │ Prometheus  │
                    │   Grafana   │
                    │   Jaeger    │
                    └─────────────┘
```

---

## 🎯 快速导航

### 需要添加新服务？

1. 在根目录创建服务文件夹
2. 添加 `pom.xml`
3. 引入 `common-utils` 依赖
4. 创建 `README.md`
5. 添加到 `docker-compose.yml`
6. 配置路由到 `api-gateway`

### 需要修改熔断器配置？

1. 编辑 `common-utils/src/main/resources/resilience4j-circuitbreaker.yml`
2. 重启服务
3. 通过API验证: `GET /api/admin/circuit-breaker/status`

### 需要添加监控指标？

1. 在 Prometheus 配置中添加 scrape job
2. 在 Grafana 中创建仪表板
3. 在 Alertmanager 中添加告警规则

---

## 📚 更多资源

- [项目Wiki](https://wiki.example.com)
- [API文档](docs/api/README.md)
- [部署指南](DEPLOYMENT.md)
- [监控配置](deployments/monitoring/README.md)


---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
