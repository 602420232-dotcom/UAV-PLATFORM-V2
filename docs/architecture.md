# 架构设计文档

## 模式边界定义

本项目采用**微服务分层架构**，模块边界清晰定义如下：

### 模块分层

```
┌─────────────────────────────────────────────────┐
│  common-dependencies  统一依赖管理（BOM）         │
│  common-utils          共享工具库（安全/审计/执行） │
├─────────────────────────────────────────────────┤
│  api-gateway           网关层 (端口8088)          │
├─────────────────────────────────────────────────┤
│  uav-platform-service  编排层 (端口8080)          │
│  职责：服务编排、数据源管理                         │
├─────────────────────────────────────────────────┤
│  wrf-processor-service  领域层 (端口8081)         │
│  meteor-forecast-service 领域层 (端口8082)        │
│  path-planning-service   领域层 (端口8083)        │
│  data-assimilation-service 领域层 (端口8084)      │
│  fengwu-service (Python) 领域层 (端口8085)        │
│  tianzi-service (Python) 领域层 (端口8090)        │
│  uav-weather-collector   领域层 (端口8086)        │
│  buoy-weather-service  领域层 (端口8087) 📝骨架   │
│  ground-station-weather-service 领域层 (端口8093) 📝骨架 │
│  satellite-weather-service 领域层 (端口8094) 📝骨架   │
│  radiosonde-weather-service 领域层 (端口8095) 📝骨架   │
│  detection-drone-service 领域层 (端口8096) 📝骨架     │
├─────────────────────────────────────────────────┤
│  backend-spring        独立服务 (端口8089)        │
│  职责：路径规划系统后端（含认证/授权/历史管理）      │
├─────────────────────────────────────────────────┤
│  基础设施层                                       │
│  MySQL :3306  Redis :6379  Nacos :8848           │
│  Kafka :9092  Zookeeper :2181                    │
└─────────────────────────────────────────────────┘
```

### 模块边界定义

| 模块 | 端口 | 职责边界 |
|------|:---:|---------|
| **common-dependencies** | N/A | 统一BOM，集中管理所有依赖版本。各子模块引入此POM即可获得全部通用依赖 |
| **common-utils** | N/A | 共享工具库：PythonExecutor、JWT过滤器、SecurityAuditor审计、NacosConfigRefresher、CsrfOriginFilter |
| **api-gateway** | 8088 | API网关：路由转发、限流、熔断 |
| **uav-platform-service** | 8080 | 平台编排：服务间编排调用链、数据源CRUD、实时数据获取。**不含**独立认证/路径规划逻辑 |
| **backend-spring** | 8089 | 独立路径规划系统：用户认证授权、独立路径规划算法调用、路径历史管理。依赖common模块但不参与微服务编排 |
| **wrf-processor-service** | 8081 | WRF气象数据处理：NetCDF解析、数据预处理、质量检查 |
| **meteor-forecast-service** | 8082 | 气象预测服务：ConvLSTM预测、XGBoost订正、气象约束计算 |
| **path-planning-service** | 8083 | 路径规划服务：VRPTW求解、NSGA-II优化、DE-RRT*规划、DWA避障 |
| **data-assimilation-service** | 8084 | 数据同化服务：3D-VAR/4D-VAR/EnKF同化、贝叶斯优化、不确定性量化 |
| **fengwu-service** | 8085 | 风乌气象模型服务：基于 ONNX Runtime 的全球气象预测（Python FastAPI 实现） |
| **tianzi-service** | 8090 | TianZi 高分辨率分析服务：基于深度学习的高分辨率气象分析（最高1km分辨率） |
| **uav-weather-collector** | 8086 | 气象数据采集：多源数据采集与融合 |
| **buoy-weather-service** | 8087 | 浮标气象数据服务 📝骨架，端口已分配，业务逻辑待实现 |
| **ground-station-weather-service** | 8093 | 地面站气象数据服务 📝骨架，端口已分配，业务逻辑待实现 |
| **satellite-weather-service** | 8094 | 卫星气象数据服务 📝骨架，端口已分配，业务逻辑待实现 |
| **radiosonde-weather-service** | 8095 | 探空气象数据服务 📝骨架，端口已分配，业务逻辑待实现 |
| **detection-drone-service** | 8096 | 检测无人机服务 📝骨架，端口已分配，业务逻辑待实现 |

### backend-spring vs uav-platform-service 职责区分

| 职责 | backend-spring | uav-platform-service |
|------|:---:|:---:|
| 用户认证 | ✅ AuthController + JWT + BCrypt | ❌ 使用common基础认证 |
| 角色权限 | ✅ RBAC（ADMIN/DISPATCHER/OPERATOR/USER） | ❌ 仅基础认证 |
| 路径规划 | ✅ PathPlanningController（直接Python调用） | ✅ PlatformController（微服务编排） |
| CSRF保护 | ✅ CookieCsrfTokenRepository | ❌ JWT无状态模式 |
| 数据源管理 | ❌ | ✅ DataSourceController + RealDataSourceController |
| Nacos注册 | ❌ 独立部署 | ✅ Nacos服务发现 |
| 链路追踪 | ❌ | ✅ SkyWalking |

### 架构决策记录

**ADR-001**: backend-spring 为独立路径规划系统，使用端口8089（非8080），不与 uav-platform-service 存在端口冲突。两个模块不共享Controller/Service，由 gateway 根据路由区分访问目标。

**ADR-002**: 所有公共工具、安全组件统一收归 common-utils。SecurityAuditor 为唯一审计实现，各模块通过 SecurityAuditConfig 委托调用。

**ADR-003**: common-dependencies 为BOM型POM，集中管理所有通用依赖版本。子模块引入 common-dependencies 即可获得全部标准化依赖，无需在各自pom中重复声明。

**ADR-004**: fengwu-service 为 Python FastAPI 服务（非 Java），独立于 Spring Cloud 体系。通过 API Gateway 路由 `/api/fengwu/**` 接入。ONNX 模型推理使用 CPU 模式（onnxruntime），生产环境建议配置 GPU 加速。

**ADR-007**: tianzi-service 为 Python FastAPI 服务（非 Java），提供高分辨率气象分析能力（最高1km分辨率）。支持分析、预报、数据同化三种模式，通过 API Gateway 路由 `/api/tianzi/**` 接入。与 fengwu-service 形成互补，fengwu 提供全球覆盖，tianzi 提供局地高分辨率分析。

**ADR-005**: buoy/ground-station/satellite/radiosonde/detection-drone 五个服务当前为骨架模块（仅含目录结构和基础 POM），端口已在 PORTS_CONFIGURATION.md 中分配。完整业务逻辑需根据需求逐步实现。

**ADR-006**: Kafka 依赖 Zookeeper 进行集群协调（端口 2181）。启动顺序必须为 Zookeeper → Kafka，docker-compose.yml 已配置 `depends_on` 和 `healthcheck` 保证启动顺序。

---

> **最后更新**: 2026-06-08  
> **版本**: 3.2  
> **维护者**: DITHIOTHREITOL
