# UAV路径规划前端优化执行计划

> **版本**: v1.0  
> **创建日期**: 2026-06-09  
> **状态**: 待审阅  
> **后端服务状态**: ✅ 全部18个服务已运行

---

## 目录

1. [项目现状分析](#1-项目现状分析)
2. [Phase 1: 后端API真实对接](#2-phase-1-后端api真实对接)
3. [Phase 2: 高级功能扩展](#3-phase-2-高级功能扩展)
4. [Phase 3: MyPanel集成](#4-phase-3-mypanel集成)
5. [Phase 4: 体验优化](#5-phase-4-体验优化)
6. [任务优先级排序](#6-任务优先级排序)
7. [资源需求](#7-资源需求)

---

## 1. 项目现状分析

### 1.1 后端服务健康状态

| 序号 | 服务名 | 端口 | 状态 |
|------|--------|------|------|
| 1 | mysql | 3306 | ✅ 正常 |
| 2 | redis | 6379 | ✅ 正常 |
| 3 | nacos | 8848 | ✅ 正常 |
| 4 | api-gateway | 8088 | ✅ 正常 |
| 5 | wrf-processor | 8081 | ✅ 正常 |
| 6 | data-assimilation | 8084 | ✅ 正常 |
| 7 | meteor-forecast | 8082 | ✅ 正常 |
| 8 | path-planning | 8083 | ✅ 正常 |
| 9 | uav-platform | 8080 | ✅ 正常 |
| 10 | uav-weather-collector | 8086 | ✅ 正常 |
| 11 | edge-cloud-coordinator | 8000 | ✅ 正常 |
| 12 | fengwu-service | 8085 | ✅ 正常 |
| 13 | model-engine | 8087 | ✅ 正常 |
| 14 | tianzi-service | 8090 | ✅ 正常 |
| 15 | fenglei-service | 8091 | ✅ 正常 |
| 16 | kafka | 9092 | ✅ 正常 |
| 17 | zookeeper | 2181 | ✅ 正常 |
| 18 | frontend | 3000 | ✅ 正常 |

### 1.2 前端现状

| 维度 | 状态 | 说明 |
|------|------|------|
| 页面功能 | ✅ 完整 | 30+页面已实现 |
| API调用 | ❌ Mock | 全部使用模拟数据 |
| 数据可视化 | ✅ 完整 | ECharts/Cesium/Leaflet |
| 权限系统 | ✅ 完整 | RBAC按钮级权限 |

---

## 2. Phase 1: 后端API真实对接

**目标**: 将前端从演示模式切换到真实API调用

### 2.1 1-1 Docker服务管理面板重构

| 任务 | 描述 | 文件路径 | 预计工作量 |
|------|------|----------|-----------|
| 1.1.1 | 集成dockerode客户端 | `src/utils/docker.js` | 2h |
| 1.1.2 | 实现容器列表获取API | `src/api/docker.js` | 2h |
| 1.1.3 | 对接18服务健康检查 | `src/api/system.js` | 3h |
| 1.1.4 | 更新DockerStatusView | `src/views/deployment/DockerStatusView.vue` | 3h |

### 2.2 1-2 系统监控真实对接

| 任务 | 描述 | 文件路径 | 预计工作量 |
|------|------|----------|-----------|
| 1.2.1 | 对接Prometheus API | `src/api/monitoring.js` | 2h |
| 1.2.2 | 更新监控面板数据 | `src/views/monitoring/SystemMonitorView.vue` | 3h |
| 1.2.3 | 实现实时数据流 | `src/utils/usePolling.js` | 2h |

### 2.3 1-3 API层改造

| 任务 | 描述 | 文件路径 | 预计工作量 |
|------|------|----------|-----------|
| 1.3.1 | 修改Vite代理配置 | `vite.config.js` | 1h |
| 1.3.2 | 实现JWT自动刷新 | `src/utils/auth.js` | 3h |
| 1.3.3 | 替换Mock API调用 | `src/api/*.js` | 8h |

**Phase 1 总计**: 约 26h

---

## 3. Phase 2: 高级功能扩展

**目标**: 实现离线SDK和边云协同

### 3.1 2-1 端侧离线SDK

| 任务 | 描述 | 文件路径 | 预计工作量 |
|------|------|----------|-----------|
| 2.1.1 | 实现IndexedDB离线存储 | `src/utils/indexedDB.js` | 4h |
| 2.1.2 | 离线路径规划算法 | `src/utils/offline/planner.js` | 8h |
| 2.1.3 | 本地气象风险判断 | `src/utils/offline/risk.js` | 4h |
| 2.1.4 | 离线状态面板 | `src/components/shared/OfflineBadge.vue` | 2h |
| 2.1.5 | 离线任务包管理 | `src/views/offline/OfflineTaskView.vue` | 4h |

### 3.2 2-2 边云协同Kafka对接

| 任务 | 描述 | 文件路径 | 预计工作量 |
|------|------|----------|-----------|
| 2.2.1 | WebSocket连接封装 | `src/utils/websocket.js` | 3h |
| 2.2.2 | Kafka事件订阅 | `src/api/kafka.js` | 4h |
| 2.2.3 | 实时事件流可视化 | `src/views/cockpit/SmartCockpit.vue` | 4h |

### 3.3 2-3 PX4/ArduPilot对接（后置）

| 任务 | 描述 | 文件路径 | 预计工作量 |
|------|------|----------|-----------|
| 2.3.1 | MAVLink协议解析 | `src/utils/mavlink.js` | 12h |
| 2.3.2 | 任务上传功能 | `src/utils/fc/upload.js` | 6h |
| 2.3.3 | 飞行状态回传 | `src/utils/fc/status.js` | 6h |

**Phase 2 总计**: 离线SDK约22h，Kafka约11h，飞控对接约24h

---

## 4. Phase 3: MyPanel集成

**目标**: 将MyPanel作为独立服务部署

| 任务 | 描述 | 文件路径 | 预计工作量 |
|------|------|----------|-----------|
| 3.1.1 | 配置MyPanel独立部署 | `tools/mypanel/package.json` | 1h |
| 3.1.2 | 更新docker-compose添加mypanel服务 | `docker-compose.yml` | 1h |
| 3.1.3 | 前端添加MyPanel入口链接 | `src/layouts/DefaultLayout.vue` | 1h |

**Phase 3 总计**: 约 3h

---

## 5. Phase 4: 体验优化

**目标**: 提升用户体验和性能

### 5.1 4-1 国际化(i18n)落地

| 任务 | 描述 | 文件路径 | 预计工作量 |
|------|------|----------|-----------|
| 4.1.1 | 替换硬编码中文 | 全局搜索替换 | 8h |
| 4.1.2 | 补充en-US词条 | `src/locale/en-US.js` | 4h |
| 4.1.3 | 语言切换实时生效 | `src/stores/locale.js` | 2h |

### 5.2 4-2 错误处理规范化

| 任务 | 描述 | 文件路径 | 预计工作量 |
|------|------|----------|-----------|
| 4.2.1 | 统一错误处理 | `src/utils/errorHandler.js` | 3h |
| 4.2.2 | 网络异常友好提示 | `src/components/shared/ErrorBoundary.vue` | 2h |

### 5.3 4-3 性能优化

| 任务 | 描述 | 文件路径 | 预计工作量 |
|------|------|----------|-----------|
| 4.3.1 | ECharts按需引入 | `src/main.js` | 2h |
| 4.3.2 | 路由懒加载增强 | `src/router/index.js` | 2h |

**Phase 4 总计**: 约 23h

---

## 6. 任务优先级排序

| 优先级 | Phase | 任务 | 说明 |
|--------|-------|------|------|
| P0 | 1 | Docker服务管理面板重构 | 核心运维功能 |
| P0 | 1 | API层改造 | 基础架构 |
| P0 | 1 | 系统监控对接 | 核心运维功能 |
| P1 | 3 | MyPanel集成 | 独立部署工作量小 |
| P1 | 2 | 端侧离线SDK | 核心功能 |
| P2 | 4 | 国际化落地 | 用户体验 |
| P2 | 4 | 错误处理规范化 | 稳定性 |
| P2 | 4 | 性能优化 | 用户体验 |
| P3 | 2 | Kafka对接 | 实时功能 |
| P4 | 2 | PX4/ArduPilot对接 | 后置任务 |

---

## 7. 资源需求

| 资源 | 需求 |
|------|------|
| 后端 | 18个服务已就绪 |
| 开发环境 | Node.js 18+, npm 9+ |
| Docker | 用于MyPanel独立部署 |
| 浏览器 | Chrome/Firefox (WebSocket支持) |

---

## 8. 里程碑

| 里程碑 | 预计时间 | 交付物 |
|--------|----------|--------|
| Phase 1完成 | 1-2周 | 前端切换到真实API |
| Phase 3完成 | 第2周 | MyPanel独立部署 |
| Phase 4完成 | 第3周 | 体验优化完成 |
| Phase 2(离线SDK) | 第4周 | 离线功能上线 |
| Phase 2(飞控对接) | 第5-6周 | 飞控集成完成 |

---

**审批**: _________________________  
**日期**: _________________________