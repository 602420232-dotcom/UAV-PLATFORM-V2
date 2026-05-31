# 架构设计文档

> 最后更新: 2026-05-31 (v2.3)

## 模块边界定义

本项目采用微服务分层架构，模块边界清晰定义如下：

### 新增模块 (v2.3)

| 模块 | 路径 | 说明 |
|------|------|------|
| **errors** | [common-utils/src/main/python/errors.py](../common-utils/src/main/python/errors.py) | 统一错误码/AppError/Result |
| **planners** | [path-planning-service/src/main/python/planners/](../path-planning-service/src/main/python/planners/) | 模块化路径规划器 |
| **security_validation** | [edge-cloud-coordinator/security_validation.py](../edge-cloud-coordinator/security_validation.py) | 安全输入验证 |
| **docker/base** | [docker/base/](../docker/base/) | Docker 统一基础镜像 |
| **mypanel/backend** | [tools/mypanel/backend/](../tools/mypanel/backend/) | 监控面板后端模块化 |

### 模块分层

```
┌─────────────────────────────────────────────────────────┐
│              common-dependencies  统一依赖管理BOM          │
├─────────────────────────────────────────────────────────┤
│              common-utils          共享工具库              │
│              (安全/审计/执行器)                             │
├──────────────────┬──────────────────────────────────────┤
│   api-gateway    │   uav-platform-service  编排(8080)    │
│   网关(8088)      │   职责：服务编排、数据源管理              │
├──────────────────┼──────────────────────────────────────┤
│ wrf-processor-service        领域(端口8081)               │
│ meteor-forecast-service      领域(端口8082)               │
│ path-planning-service        领域(端口8083)               │
│ data-assimilation-service    领域(端口8084)               │
│ fengwu-service               领域(端口8085)               │
│ uav-weather-collector        领域(端口8086)               │
├──────────────────┼──────────────────────────────────────┤
│   edge-cloud-coordinator     边云协同(端口8000/8765)       │
│   职责：边云同步、WebSocket、联邦学习                        │
└──────────────────┴──────────────────────────────────────┘
```

### 模块边界定义

| 模块 | 端口 | 职责边界 |
|------|:---:|---------|
| **common-dependencies** | N/A | 统一BOM，集中管理所有依赖版本，各子模块引入此POM即可获得全部通用依赖 |
| **common-utils** | N/A | 共享工具库：PythonExecutor、JWT过滤器、SecurityAuditor审计、NacosConfigRefresher、CsrfOriginFilter |
| **api-gateway** | 8088 | API网关，路由转发，限流熔断 |
| **uav-platform-service** | 8080 | 平台编排，服务间编排调用链，数据源CRUD，实时数据获取 |
| **fengwu-service** | 8085 | 风乌 AI 全球天气预报服务，基于 ONNX 深度学习推理引擎 |
| **edge-cloud-coordinator** | 8000 | 边云协同框架，WebSocket 实时通信，联邦学习支持 |
| **领域服务** | 8081-8086 | 各领域微服务，处理各自领域的核心算法和业务逻辑 |

### 架构决策记录

**ADR-001**: fengwu-service 使用端口8085，作为 AI 全球天气预报服务独立部署，通过 ONNX Runtime 提供深度学习推理，与 WRF 数值天气预报服务形成互补。

**ADR-002**: edge-cloud-coordinator 使用端口8000 (REST) + 8765 (WebSocket) 双通道，负责边云协同通信与联邦学习调度。

**ADR-003**: 所有公共工具和组件统一收归 common-utils。SecurityAuditor 为唯一审计实现，各模块通过 SecurityAuditConfig 委托调用。

**ADR-004**: common-dependencies 为BOM型POM，集中管理所有通用依赖版本。子模块引入 common-dependencies 即可获得全部标准化依赖，无需在各自pom中重复声明。

---

> **最后更新**: 2026-05-30
> **版本**: 2.3
> **维护者**: DITHIOTHREITOL
