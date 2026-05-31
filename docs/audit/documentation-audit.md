# 文档完整性与一致性审计报告

## 审计时间
2026-05-31 17:30 GMT+8

## 审计范围
项目根目录及 docs/ 下全部 30+ 个 .md 文件 + G:\FILES\weather\paper 论文需求文档

---

## 一、文档端口一致性

| 文档声明端口 | 实际运行 | 状态 |
|-------------|---------|------|
| 8088 API Gateway | ✅ 运行中 | 一致 |
| 8080 Platform Service | ✅ 运行中 | 一致 |
| 8081 WRF Processor | ✅ 运行中 | 一致 |
| 8082 Meteor Forecast | ✅ 运行中 | 一致 |
| 8083 Path Planning | ✅ 运行中 | 一致 |
| 8084 Data Assimilation | ✅ 运行中 | 一致 |
| 8085 FengWu AI | ✅ 运行中 | 一致 |
| 8086 Weather Collector | ✅ 运行中 | 一致 |
| 8000 Edge Cloud | ✅ 运行中 | 一致 |
| 3000 Frontend (nginx) | ✅ 运行中 | 一致 |
| 8899 Adminer | 🆕 新增 | **文档缺少** |
| 4173 Vue Dev Server | ❌ 不可达 | **文档过期** |
| 8848 Nacos | ✅ 运行中 | 文档缺少 |
| 9092 Kafka | ✅ 运行中 | 文档缺少 |

## 二、文档结构一致性

| 文档描述模块 | 实际存在 | 状态 |
|-------------|---------|------|
| api-gateway | ✅ | 一致 |
| uav-platform-service | ✅ | 一致 |
| wrf-processor-service | ✅ | 一致 |
| meteor-forecast-service | ✅ | 一致 |
| path-planning-service | ✅ | 一致 |
| data-assimilation-service | ✅ | 一致 |
| uav-weather-collector | ✅ | 一致 |
| edge-cloud-coordinator | ✅ | 一致 |
| common-utils | ✅ | 一致 |
| fengwu-service | ✅ | 一致 |
| uav-edge-sdk | ✅ | 文档缺少 |
| uav-mobile-app | ✅ | 文档缺少 |
| backend-spring | ❌ 不存在 | **文档过期** |

## 三、Gateway 路由文档 vs 实际

| 文档声明路由 | 实际配置 | 状态 |
|-------------|---------|------|
| `/api/wrf/**` → wrf-processor:8081 | 全部 → uav-platform:8080 (mock dev) | ⚠️ dev 模式 |
| `/api/forecast/**` → meteor:8082 | 全部 → uav-platform:8080 (mock dev) | ⚠️ dev 模式 |
| Nacos 服务发现已禁用 | 已启用 Nacos discovery | **文档过期** |

## 四、需求文档 (paper/) 对照

| 论文需求功能 | 实现状态 | 备注 |
|-------------|---------|------|
| 1. WRF 气象数据 + 短时预报 | ✅ fengwu_v2.onnx 运行中 | 14天/56步预报 |
| 2. 贝叶斯同化方差场 | ⚠️ Python 模块存在 | 未集成到 API |
| 3. LSTM+XGBoost 预测订正 | 🟡 模块框架存在 | 需训练模型 |
| 4. VRPTW 路径规划 | ✅ API 端点就绪 | mock 数据 |
| 5. SpringBoot 后端 | ✅ 15 服务运行 | JWT 已就绪 |
| 6. Web 前端 + 地图 | ✅ Flutter Web (3000) | Leaflet 地图 |
| 7. SQL 数据库管理 | ✅ MySQL + Adminer | 完整 CRUD |
| 8. 多角色管理 | ✅ 4 角色 | admin/dispatcher/operator/user |
| 9. 三层路径规划 (VRPTW/A*/DWA) | ✅ API 端点 | 算法待对接真实 |
| 10. 贝叶斯同化方差场路径集成 | 🟡 论文描述 | 未实现 |
| 11. 5分钟高频更新 | 🟡 框架支持 | 未配置定时 |
| 12. 动态重规划 (<5秒) | 🟡 API 存在 | 未测试 |

## 五、文档过期/错误清单

### P0 (Critical)
- **DOC-C01**: `PORTS_CONFIGURATION.md` 端口 4173 已不可用，指向已删除的 Vue dev server
- **DOC-C02**: `architecture.md` 引用 `backend-spring` 模块不存在
- **DOC-C03**: `TODO_CHECKLIST.md` Grafana/ELK 密码硬编码问题仍未修复

### P1 (High)
- **DOC-H01**: Gateway 路由文档需更新 — 当前 dev 模式全部指向 uav-platform:8080
- **DOC-H02**: Nacos 状态文档需更新 — 已启用服务发现
- **DOC-H03**: 缺少 Adminer (8899) 端口文档
- **DOC-H04**: 缺少 Flutter 移动端 (uav-mobile-app) 文档

### P2 (Medium)
- **DOC-M01**: 所有文档缺少最后更新日期
- **DOC-M02**: 缺少 JWT 认证使用文档
- **DOC-M03**: `DOCKER.md` 未提及 FengWu 模型挂载路径依赖

## 六、缺少的文档

| 缺失文档 | 重要性 | 建议 |
|---------|--------|------|
| JWT 认证使用指南 | High | 新建 docs/JWT_GUIDE.md |
| Adminer 数据库管理 | Medium | 新建 docs/DATABASE_MANAGEMENT.md |
| FengWu 模型部署 | High | 已有 download 脚本，缺文档 |
| Flutter 移动端构建 | Medium | 新建 docs/MOBILE_BUILD.md |
| API 接口文档 (Swagger) | High | 建议启用 SpringDoc |
