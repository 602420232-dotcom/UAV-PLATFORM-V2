# 项目依赖状态审计报告

> 生成日期：2026-06-03

---

## 前端依赖 (Vue.js)

源文件：`uav-path-planning-system/frontend-vue/package.json`

### 核心框架与构建工具

| 依赖 | 当前版本 | 最新版本 | 状态 | 建议 |
|------|---------|---------|:----:|------|
| vue | ^3.4.0 | 3.5.35 | ✅ 正常 | 语义化版本范围覆盖至 3.5.x，可接收小版本更新 |
| vite | ^5.0.0 | 8.0.0 | ⚠️ 滞后 | **Vite 5 → Vite 8 差距较大**。Vite 8（2026-03）搭载 Rolldown（Rust 打包器），构建速度提升 10~30 倍。建议规划升级至 Vite 8 |
| @vitejs/plugin-vue | ^5.0.0 | 5.x | ⚠️ 需确认 | 当前匹配 Vite 5，升级 Vite 8 时需同步升级插件 |
| vitest | ^4.1.8 | 4.x | ✅ 正常 | 与 Vite 5 配套，升级 Vite 后需同步 |
| @vitejs/plugin-vue-jsx | ^5.1.5 | 5.x | ✅ 正常 | 与 Vite 5 配套 |

### UI 组件库

| 依赖 | 当前版本 | 最新版本 | 状态 | 建议 |
|------|---------|---------|:----:|------|
| ant-design-vue | ^4.0.0 | 4.2.6 | ✅ 正常 | 语义化版本范围覆盖 4.x 最新，无需操作 |
| @ant-design/icons-vue | ^7.0.0 | 7.x | ✅ 正常 | 与 ant-design-vue 4.x 配套 |

### 地图与可视化

| 依赖 | 当前版本 | 最新版本 | 状态 | 建议 |
|------|---------|---------|:----:|------|
| cesium | ^1.119.0 | 1.142 | ⚠️ 滞后 | 约落后 23 个小版本（~1 年）。Cesium 每月发布一次，1.142 新增了矢量瓦片 3D Tiles 支持、MVT 数据提供器等重要功能 |
| echarts | ^5.4.3 | 6.1.0 | ⚠️ 大版本落后 | **ECharts 6 已正式发布**（5.6.0 → 6.0.0+）。当前 5.4.3 仍可接收 5.x 补丁，但建议关注 ECharts 6 的迁移计划 |
| leaflet | ^1.9.4 | 1.9.4 | ✅ 已是最新 | Leaflet 2.0 处于 alpha 阶段，当前稳定版即为 1.9.4 |
| leaflet.heat | ^0.2.0 | 0.2.0 | ⚠️ 长期未更新 | 该插件多年未维护，功能基本稳定，如无问题可继续使用 |

### 状态管理与路由

| 依赖 | 当前版本 | 最新版本 | 状态 | 建议 |
|------|---------|---------|:----:|------|
| pinia | ^2.1.7 | 2.2.x | ✅ 正常 | 范围覆盖最新版本 |
| vue-router | ^4.2.5 | 4.4.x | ✅ 正常 | 范围覆盖最新版本 |

### 网络请求

| 依赖 | 当前版本 | 最新版本 | 状态 | 建议 |
|------|---------|---------|:----:|------|
| axios | ^1.6.2 | 1.7.x | ✅ 正常 | 范围覆盖 1.x 最新版本 |

### 测试

| 依赖 | 当前版本 | 最新版本 | 状态 | 建议 |
|------|---------|---------|:----:|------|
| @vue/test-utils | ^2.4.10 | 2.4.x | ✅ 正常 | 与 Vitest 配套使用 |
| jsdom | ^29.1.1 | 29.x | ✅ 正常 | Vitest 测试环境 |

---

## Flutter 移动端依赖

源文件：`uav-mobile-app/pubspec.yaml`

| 依赖 | 当前版本 | 说明 |
|------|---------|------|
| Dart SDK | >=3.2.0 <4.0.0 | ✅ 范围合理，覆盖 Dart 3.x |
| flutter_riverpod | ^2.4.9 | ✅ 状态管理，版本近期 |
| riverpod_annotation | ^2.3.3 | ✅ 配合 flutter_riverpod |
| dio | ^5.4.0 | ✅ 网络请求库，版本较新 |
| retrofit | ^4.1.0 | ✅ 结合 dio 的 API 代码生成 |
| connectivity_plus | ^5.0.2 | ✅ 网络状态监测 |
| go_router | ^13.0.0 | ✅ 声明式路由 |
| shared_preferences | ^2.2.2 | ✅ 本地键值存储 |
| hive / hive_flutter | ^2.2.3 / ^1.1.0 | ⚠️ Hive 生态趋于稳定，如需轻量存储可继续保持 |
| flutter_secure_storage | ^9.0.0 | ✅ 安全存储 |
| flutter_map | ^6.1.0 | ✅ Flutter 端地图组件 |
| latlong2 | ^0.9.0 | ✅ 经纬度工具 |
| fl_chart | ^0.66.1 | ✅ 图表组件 |
| intl | ^0.20.2 | ✅ 国际化 |
| permission_handler | ^11.2.0 | ✅ 权限管理 |
| json_annotation / json_serializable | ^4.8.1 / ^6.7.1 | ✅ JSON 序列化 |
| freezed / freezed_annotation | ^2.4.7 / ^2.4.1 | ✅ 数据类代码生成 |
| retrofit_generator | ^8.1.0 | ✅ API 代码生成 |
| build_runner | ^2.4.8 | ✅ 代码生成器 |

Flutter 端依赖整体状况良好，无重大版本滞后问题。

---

## 后端依赖 (Java)

| 依赖 | 当前版本 | 说明 |
|------|---------|------|
| Spring Boot | 3.5.14 | ✅ 已是最新 |
| Spring Cloud | 2025.0.0 | ✅ 已是最新 |
| Resilience4j | 2.3.0 | ✅ 已是最新 |
| jjwt | 0.12.6 | ✅ 已是最新 |

---

## Python 依赖

### fengwu-service
- onnxruntime / onnxruntime-gpu — 推理引擎
- fastapi — Web 框架
- pyjwt — JWT 处理

### model-engine
- torch — 深度学习框架
- gpytorch — 高斯过程建模
- numpy / scipy — 科学计算

### path-planning-service
- numpy — 数值计算
- scipy — 科学计算/优化算法

> 注：Python 依赖为顶层列举，具体版本号需查看各服务的 `requirements.txt` 或 `pyproject.toml`。

---

## 关键发现与建议

### 🔴 高风险

1. **Vite 5 → Vite 8 版本差距过大**
   - 当前使用 Vite 5（2024 年发布），最新为 Vite 8（2026-03，搭载 Rolldown Rust 打包器）
   - 升级收益：构建速度提升 10~30 倍、统一的 Rust 打包器、内置 tsconfig paths 支持
   - 建议：制定分步升级计划（5→6→7→8 或直接预研迁移方案）

2. **Cesium 版本滞后约 20+ 小版本**
   - 当前 1.119.0 vs 最新 1.142
   - 新版本带来矢量瓦片 3D Tiles、MVT 数据提供器、高斯泼溅（Gaussian Splatting）支持等关键功能
   - 建议：评估兼容性后逐步升级

### 🟡 中风险

3. **ECharts 5→6 大版本迁移**
   - ECharts 6 已发布，带来了新特性和突破性变更
   - 建议：关注 ECharts 6 API 变更，规划迁移窗口

### 🟢 低风险 / 无需操作

4. **Leaflet 1.9.4** — 已是当前稳定版最新
5. **ant-design-vue 4.x** — 覆盖最新 4.2.6
6. **Flutter 端依赖** — 整体版本健康
7. **Java 后端依赖** — Spring Boot / Spring Cloud 已是最新

---

## 安全建议

1. 所有 `package.json` 中的依赖应定期运行 `npm audit` 检查已知漏洞
2. 建议启用 Dependabot 或 Renovate 自动化依赖更新
3. 对重大版本变更（如 Vite 5→8、ECharts 5→6）需规划迁移路径和测试方案
4. Flutter 端运行 `flutter pub outdated` 定期检查依赖更新
5. 关注 Cesium License 变更（2020 年后从开源转向更严格的商业许可），确认当前使用版本合规
