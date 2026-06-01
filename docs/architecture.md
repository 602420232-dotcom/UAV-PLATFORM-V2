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
│  uav-weather-collector   领域层 (端口8086)        │
├─────────────────────────────────────────────────┤
│  backend-spring        独立服务 (端口8089)        │
│  职责：路径规划系统后端（含认证/授权/历史管理）      │
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
| **领域服务** | 8081-8086 | 各领域微服务：处理各自领域的核心算法和业务逻辑 |

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
---

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
