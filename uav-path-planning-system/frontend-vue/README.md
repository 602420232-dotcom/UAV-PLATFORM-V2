# UAV Path Planning Frontend - Vue3 Application

> 基于 WRF 气象驱动的无人机路径规划系统 —— 前端单页应用（**P0 + P1 + P2 全部闭环**：可视化核心 / 运维模块 / 通知系统 / 实验对比 / 数据权限 / 组件文档 / 新增页面：气象站点管理 / 适航性评估 / 参数敏感性分析 / KML导出 / Excel导入 / 多机队形）

---

## 📋 应用概述

Vue 3 + Vite 前端应用，为无人机路径规划系统提供 Web 界面。核心特性：基于角色的权限控制（RBAC）、演示模式（免后端）、多模块业务页面集成、2D/3D 可视化混合支持、NetCDF 气象数据解析与上传、PWA 离线能力、分层缓存策略。

**技术栈**：

| 技术 | 版本 | 用途 |
|------|------|------|
| **Vue** | 3.4.x | 前端框架（Composition API） |
| **Vite** | 5.0.x | 构建工具 |
| **Vue Router** | 4.2.x | 路由管理（含路由守卫 + 动态 import 懒加载） |
| **Pinia** | 2.1.x | 状态管理（Auth / App / 业务模块） |
| **Element Plus** | 2.4.x | UI 组件库（替代 Ant Design Vue） |
| **Axios** | 1.6.x | HTTP 客户端（含分层缓存 + 请求重试 + 并发控制） |
| **ECharts** | 5.6.x | 数据可视化（时间序列 / 热力图 / 3D 剖面） |
| **Leaflet** | 1.9.x | 2D 地图组件（风场矢量 / 气象热力 / 贝叶斯方差 / 路径规划） |
| **Cesium** | 1.119.x | 3D 地理可视化（智能驾驶舱 · 可选，未安装静态资源时自动降级为 Leaflet 2D） |
| **vite-plugin-pwa** | 0.17.x | PWA / Service Worker（可选，`npm install` 清单已配置） |
| **marked** | 18.x | Markdown 文档渲染（DocsView 远程 GitHub 文档同步） |

---

## 🔌 端口 & 环境配置

### 开发服务器端口

- **默认端口**：`3000`
- **实际运行端口**：受宿主机占用情况影响（Vite 自动递增）
- **配置文件**：`vite.config.js`

```javascript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
```

### API 代理配置

| 路径前缀 | 目标地址 | 说明 |
|---------|----------|------|
| `/api` | `http://localhost:8080` | 后端 API 网关代理 |

### 演示模式

- **默认开启**：`demoMode = true`
- **无需后端**：内置默认账号体系，直接登录体验完整 UI
- **持久化**：用户信息、主题、侧边栏状态、缓存条目全部存储于 `localStorage`
- **离线可用**：安装 PWA 后，SW 会拦截请求并回退到缓存数据

---

## 🚀 快速开始

### 环境要求

- **Node.js**：16+（推荐 18.x / 20.x）
- **npm**：8+ 或 **pnpm**：8+

### 安装依赖

```bash
cd uav-path-planning-system/frontend-vue
npm install
# 可选：启用 PWA 插件（默认未安装）
npm install vite-plugin-pwa --save-dev
```

### 启动开发服务器

```bash
# 开发模式（默认端口 3000，被占用时自动递增）
npm run dev

# 生产构建（已验证 ✅ 通过，可输出 dist/ 完整产物）
npm run build

# 预览生产构建
npm run preview
```

### 访问应用

开发服务器启动后，控制台输出类似：

```
➜  Local:   http://localhost:3000/
```

打开浏览器访问该地址即可。

---

## 👥 角色权限系统（RBAC）

### 角色定义

系统共定义 6 种角色，每种角色登录后看到不同的侧边栏菜单：

| 角色 Key | 中文名称 | 典型用户 |
|----------|----------|----------|
| `user` | 普通用户 | 下单/查询任务的终端用户 |
| `production` | 生产人员 | 运维/任务调度人员 |
| `flight` | 飞控人员 | 负责路径规划、飞行控制 |
| `tester` | 测试人员 | 系统功能测试 |
| `deployment` | 部署人员 | 运维部署、服务器状态监控 |
| `admin` | 管理员 | 系统全权限管理 |

### 角色权限矩阵

| 功能页面 | 普通用户 | 生产人员 | 飞控人员 | 测试人员 | 部署人员 | 管理员 |
|---------|---------|---------|---------|---------|---------|-------|
| 项目简介 / 首页 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 气象数据查看（含风场/热力/方差/模型对比/NetCDF 上传） | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 气象站点管理 | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| 下单 / 选择运输地点 | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 智能驾驶舱（3D Cesium / 2D Leaflet 降级） | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| 运输任务管理 | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| 路径规划（拖拽航点 / 调参实时预览 / 多算法对比） | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |
| 适航性评估（全流程5步） | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |
| 数据同化 | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |
| 参数敏感性分析 | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |
| 系统监控面板 | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| 数据库管理 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Docker / 服务器状态 | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| 气象模型 API 配置（天资/风雷/风乌/数据库/边云协同/Model Engine/网关/WRF） | ❌ | ❌ | ❌ | ❌ | 仅查看 | 可修改 |
| 个人设置 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 使用文档（Markdown 渲染 · GitHub 同步） | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### 按钮级权限

除页面级访问控制外，部分页面内部按角色限制操作能力：

| 权限 Key | 允许角色 | 说明 |
|----------|---------|------|
| `api-config:edit` | `admin` | API 配置修改 |
| `api-config:view` | `deployment`, `admin` | API 配置查看 |
| `orders:advanced` | `flight`, `admin` | 下单页高级配置（飞行高度/航路 RNP 约束/载荷参数/禁飞区避让策略） |
| `planning:execute` | `flight`, `tester`, `admin` | 执行路径规划计算 |
| `assimilation:view` | `tester`, `deployment`, `admin` | 查看同化结果列表 |
| `assimilation:execute` | `tester`, `deployment`, `admin` | 执行同化任务 |
| `assimilation:config` | `deployment`, `admin` | 修改同化参数（5DVAR/EnKF 配置） |
| `assimilation:download` | `tester`, `deployment`, `admin` | 下载同化结果文件 |
| `assimilation:delete` | `deployment`, `admin` | 删除历史同化记录 |
| `database:view` | `deployment`, `admin` | 查看数据库状态/表信息 |
| `database:backup` | `deployment`, `admin` | 数据库备份 |
| `database:restore` | `deployment`, `admin` | 数据库恢复（高危操作） |
| `database:config` | `deployment`, `admin` | 修改数据库连接配置 |
| `database:cleanup` | `deployment`, `admin` | 清理过期历史数据 |
| `docker:view` | `deployment`, `admin` | 查看服务/容器状态 |
| `docker:restart` | `deployment`, `admin` | 重启/停止服务容器 |
| `docker:build` | `deployment`, `admin` | 触发镜像构建 |
| `docker:logs` | `deployment`, `admin` | 查看容器日志 |
| `docker:cleanup` | `deployment`, `admin` | 清理无用镜像/容器 |

**使用方式**（组件内）：
```javascript
const authStore = useAuthStore()
const canEditApi = authStore.hasAction('api-config:edit')
```

### Nacos 动态权限矩阵（预留）

- 预留 `api/auth/getPermissionMatrix` 接口（`auth.js` 顶部 `NACOS_PERMISSION_KEY`）
- 登录后 Pinia auth store 可异步拉取权限并与本地矩阵合并
- Nacos 不可达时自动回退到静态 `PERMISSION_MATRIX`
- 便于生产环境动态调整角色权限（P1 计划进一步完善）

### 默认测试账号

演示模式下直接登录使用，无需注册：

| 用户名 | 密码 | 角色 |
|--------|------|------|
| `user01` | `User@123456` | 普通用户 |
| `prod01` | `Prod@123456` | 生产人员 |
| `flight01` | `Flight@123456` | 飞控人员 |
| `test01` | `Test@123456` | 测试人员 |
| `deploy01` | `Deploy@123456` | 部署人员 |
| `admin01` | `Admin@123456` | 管理员 |

**登录方式**：输入用户名 + 密码 → 系统自动识别角色并加载对应菜单。

---

## 📁 项目结构

```
frontend-vue/
├── src/
│   ├── main.js                    # 应用入口（Element Plus + PWA SW 注册）
│   ├── App.vue                    # 根组件
│   ├── index.html                 # HTML 入口
│   │
│   ├── router/
│   │   └── index.js               # 路由配置 + 权限守卫（全部动态 import 懒加载）
│   │
│   ├── stores/                    # Pinia 状态管理
│   │   ├── auth.js                # 认证 + 角色权限核心 Store（6 角色矩阵 + Nacos 预留）
│   │   ├── app.js                 # 应用级状态（主题、语言、侧边栏、默认路由）
│   │   ├── weather.js             # 气象数据 Store
│   │   ├── tasks.js               # 任务管理 Store
│   │   ├── planning.js            # 路径规划 Store
│   │   ├── drones.js              # 无人机 Store
│   │   ├── dataSources.js         # 数据源 Store
│   │   └── system.js              # 系统监控 Store
│   │
│   ├── layouts/
│   │   └── DefaultLayout.vue      # 主布局（侧边栏默认收缩+hover展开 + 顶部演示提示条）
│   │
│   ├── views/                     # 页面视图（按业务模块分组）
│   │   ├── auth/
│   │   │   ├── LoginView.vue      # 登录页（角色选择 + 默认账号）
│   │   │   ├── RegisterView.vue   # 注册页（演示模式免邮箱验证；生产模式按环境切换）
│   │   │   └── ForgotPasswordView.vue  # 密码重置
│   │   ├── dashboard/
│   │   │   └── DashboardView.vue  # 项目简介 / 首页
│   │   ├── weather/
│   │   │   ├── WeatherView.vue    # 气象数据（风场矢量 + 热力图 + 贝叶斯方差 + 多模型误差对比 + 区域时间步长切换）
│   │   │   ├── NetCDFPreview.vue  # NetCDF 上传与 2D/3D 剖面预览（分片上传 + 断点续传）
│   │   │   └── WeatherStationView.vue  # 气象站点管理（站点CRUD + 状态监控）
│   │   ├── airworthiness/
│   │   │   └── AirworthinessView.vue  # 适航性评估全流程（5步：选方案→气象核验→适航检查→风险评估→生成报告）
│   │   ├── sensitivity/
│   │   │   └── SensitivityAnalysisView.vue  # 参数敏感性分析（单因素/Sobol + 雷达图 + 相关性矩阵）
│   │   ├── orders/
│   │   │   └── OrderView.vue      # 下单 / 运输地点选择（普通用户简版 + 飞控高级版）
│   │   ├── cockpit/
│   │   │   └── SmartCockpit.vue   # 智能驾驶舱（Cesium 3D + Leaflet 2D 降级 · 实时轨迹推送 + 时间轴回放）
│   │   ├── operation/
│   │   │   └── TasksView.vue      # 运输任务管理
│   │   ├── planning/
│   │   │   └── PathPlanningView.vue  # 路径规划（拖拽航点 + 调参实时预览 + DE-RRT*/DWA/VRPTW 对比 + 导入Excel/导出KML + 多目标权重雷达图 + 多机队形配置）
│   │   ├── assimilation/
│   │   │   └── DataAssimilationView.vue  # 数据同化
│   │   ├── monitoring/
│   │   │   └── SystemMonitorView.vue   # 系统监控面板
│   │   ├── database/
│   │   │   └── DatabaseManager.vue     # 数据库管理
│   │   ├── deployment/
│   │   │   ├── DockerStatusView.vue    # Docker / 服务器状态
│   │   │   └── DockerBuildView.vue     # Docker 构建可视化（6阶段进度 + 实时日志）
│   │   ├── config/
│   │   │   └── ApiConfigView.vue       # 气象模型 API 配置（8 项生产配置 + Nacos 对接预留）
│   │   ├── permission/
│   │   │   └── PermissionTemplateView.vue  # 权限模板管理（角色组 + 临时授权）
│   │   ├── evaluation/
│   │   │   └── ModelEvaluationView.vue  # 模型评估看板（RMSE/MAE/CRPS/R + ROC曲线）
│   │   ├── params/
│   │   │   └── ParameterTuningView.vue  # 算法参数调优（DE-RRT*/DWA/GPR/3DVAR/5DVAR/EnKF）
│   │   ├── compare/
│   │   │   └── ExperimentCompareView.vue  # 实验对比工具（多方案并排 + 差异高亮）
│   │   ├── utm/
│   │   │   └── UtmIntegrationView.vue   # 低空 UTM 对接
│   │   ├── reports/
│   │   │   └── TaskReportView.vue       # 任务报告中心（CSV/PDF/XLSX 导出）
│   │   ├── settings/
│   │   │   ├── SettingsView.vue        # 个人设置（主题/语言/侧边栏/默认首页）
│   │   │   ├── ThemeCustomizer.vue     # 主题定制（预设/自定义色板/自动日落切换）
│   │   │   └── DocsView.vue            # 使用文档（Markdown 渲染 + GitHub 远程同步）
│   │   ├── debug/
│   │   │   └── PermissionDebugView.vue # 权限调试工具（实时矩阵 + 模拟切换）
│   │   ├── PermissionDenied.vue        # 无权限提示页
│   │   └── NotFound.vue                # 404 页
│   │
│   ├── components/                # 可复用组件
│   │   ├── shared/
│   │   │   ├── NetCDFChunkUploader.vue  # NetCDF 分片上传组件（5MB/片 · 断点续传）
│   │   │   └── ExcelBatchImporter.vue   # Excel 批量导入组件（字段映射 + 数据预览 + 导入确认）
│   │   ├── WeatherCard.vue
│   │   ├── LanguageSwitcher.vue
│   │   └── *.stories.ts           # Storybook 组件定义（P2 计划完善）
│   │
│   ├── api/                       # API 请求封装（带分层缓存 + 请求重试 + 并发控制）
│   │   ├── index.js               # Axios 实例 + 拦截器 + 分层缓存引擎
│   │   ├── cache.js               # 便捷导出：invalidateWeather / invalidateTask / invalidateAllCache ...
│   │   ├── auth.js
│   │   ├── weather.js
│   │   ├── tasks.js
│   │   ├── path.js
│   │   ├── assimilation.js
│   │   ├── datasource.js
│   │   ├── drones.js
│   │   ├── system.js
│   │   └── variance.js
│   │
│   ├── locales/                   # 国际化（i18n）
│   │   ├── index.js
│   │   ├── zh-CN.js
│   │   └── en-US.js
│   │
│   ├── styles/                    # 全局样式
│   │   ├── index.css
│   │   └── theme-dark.css
│   │
│   ├── utils/                     # 工具函数
│   │   ├── validators.js
│   │   ├── demoData.js
│   │   ├── errorHandler.js
│   │   ├── performance.js         # throttle/debounce/缓存/createThrottledStream/batchRaf
│   │   ├── visualization.js
│   │   ├── usePolling.js
│   │   ├── trajectory_4d.js
│   │   ├── enhanced_visualizer.js
│   │   ├── ar_digital_map.js
│   │   ├── kml.js                # KML 格式导出（兼容 PX4/ArduPilot 飞控系统）
│   │   └── indexedDB.js           # IndexedDB 离线大文件缓存
│   │
│   ├── __tests__/                 # Vitest 单元测试
│   └── types/                     # 类型声明
│
├── public/
│   ├── cesium/                    # Cesium 静态资源（构建时自动拷贝）
│   └── service-worker.js          # 手写降级 SW（未安装 vite-plugin-pwa 时可替代使用）
│
├── scripts/
│   └── copy-cesium-assets.cjs     # Cesium 资源拷贝脚本
│
├── vite.config.js                 # Vite 配置（端口 / 代理 / 手动分包 / PWA / 插件降级）
├── vitest.config.js               # 测试配置
├── tsconfig.json
├── nginx.conf                     # 生产部署 Nginx 配置
├── Dockerfile                     # Docker 镜像构建
├── package.json
└── README.md                      # 本文档
```

---

## 🔐 核心模块说明（P0 已实现）

### 1. 路由守卫（Router Guard）

**文件**：`src/router/index.js`

**关键实现**：
- **全部路由使用 `() => import(...)` 动态 import** — 实现路由级代码分割（Vite 分包基础）
- **路由守卫三阶段**：公开路由 → 登录校验 → 角色权限匹配 → 重定向/放行
- **动态侧边栏**：`DefaultLayout.vue` 中读取 `authStore.hasRouteAccess(routeKey)`，仅展示当前角色可访问的菜单

**逻辑流程**：

```
请求路由
   │
   ├── 公共路由（/login、/register、/forgot-password）
   │     └── 已登录用户访问 → 重定向至角色默认首页
   │
   ├── 业务路由（需登录）
   │     ├── 未登录 → 重定向到 /login（携带 redirect 参数）
   │     └── 已登录
   │           ├── 无页面权限 → 跳转 /permission-denied
   │           └── 有权限 → 正常渲染
   │
   └── 未匹配路由 → 渲染 NotFound 页
```

### 2. 认证 Store（Auth Store）

**文件**：`src/stores/auth.js`

**核心状态**：
- `user`：当前用户对象（username、role、displayName 等）
- `demoMode`：是否演示模式
- `demoShownOnce`：演示提示是否已展示

**核心方法**：
- `login(username, password, selectedRole)` — 登录（演示模式内置账号校验）
- `register(username, password, selectedRole)` — 注册
- `resetPassword(...)` — 密码重置
- `hasRouteAccess(routeKey)` — 路由权限判断
- `hasAction(actionKey)` — 按钮级权限判断
- `logout()` — 登出（清空状态 + localStorage）

**持久化 Key**：
- `uav_auth_user` — 用户信息
- `uav_demo_mode` — 演示模式开关
- `uav_demo_shown` — 演示提示显示记录
- `uav_nacos_permission_matrix` — Nacos 下发的权限矩阵（P1 启用后端接口后生效）

### 3. 应用 Store（App Store）

**文件**：`src/stores/app.js`

负责：主题切换（light / dark）、语言切换、侧边栏折叠、默认首页配置。

**持久化 Key**：`uav_app_config`

### 4. 默认布局（DefaultLayout）

**文件**：`src/layouts/DefaultLayout.vue`

**组成部分**：
- **顶部常驻演示提示条**：演示模式时始终可见 + 首次进入 Toast 提示
- **顶部栏**：系统 Logo、角色标签、主题切换、语言切换、用户菜单
- **左侧边栏**：默认收缩状态（仅图标），hover 自动展开；支持手动切换；按角色权限动态渲染菜单

### 5. 分层缓存（Cache Strategy）

**文件**：`src/api/index.js` + `src/api/cache.js`

**策略层级**：

| 策略 Key | 名称 | TTL | 适用路径 |
|----------|------|-----|---------|
| `STATIC_FOREVER` | 静态配置永久缓存 | 永久 | `/api/v1/(data-sources\|api-config\|config)` |
| `WEATHER_1H` | 气象数据 1 小时 | 3,600,000 ms | `/api/v1/weather` |
| `TASK_5MIN` | 任务与规划 5 分钟 | 300,000 ms | `/api/v1/(tasks\|planning\|assimilation)` |
| `NO_CACHE` | 用户认证/敏感写操作 | 0 | 其它请求 |

**实现要点**：
- 基于 `localStorage` 存储，Key 前缀 `uav_cache:`
- 每次 GET 请求：命中策略 → 先读缓存 → 缓存过期或未命中 → 请求网络 → 写回缓存
- `cacheStore.clearByTag(tag)` 或 `invalidateWeather/invalidateTask/invalidateStatic/invalidateAllCache` 手动清除（例如提交任务后刷新列表）
- 容量上限：默认 200 条，超出淘汰最旧
- POST/PUT/DELETE 完全不缓存，确保写操作即时生效

**代码示例**：
```javascript
import { cacheStore, invalidateWeather } from '@/api/cache.js'

// 提交任务后主动失效任务缓存
await api.post('/v1/tasks', payload)
cacheStore.clearByTag('task')     // 或者直接：invalidateTask()
```

### 6. PWA / Service Worker

**文件**：`vite.config.js` 中条件加载 `vite-plugin-pwa`；降级方案：`public/service-worker.js` + `src/main.js` 自动注册。

**策略**：
- **静态资源**：Cache First
- **气象 API**：Stale While Revalidate（后台自动刷新）
- **任务/路径 API**：Network First（5 分钟内回退缓存）
- **跨域资源**：Cache First
- **在线/离线切换**：`window.online`/`offline` 事件 → ElMessage 友好提示

**启用方式**：
```bash
npm install vite-plugin-pwa --save-dev
# 然后 npm run build 即生成 SW 与 manifest
```

未安装时 Vite 会自动跳过 PWA 插件并打印提示，**不阻塞正常构建**。

### 7. NetCDF 分片上传与预览

**文件**：`src/components/shared/NetCDFChunkUploader.vue` + `src/views/weather/NetCDFPreview.vue`

**参数**：
- 分片大小：5 MB
- 支持上传最大 2 GB
- `localStorage` 记录每个文件的分片进度（断点续传）
- 演示模式：本地生成 mock 剖面数据（2D 热力图 / 3D 剖面图），无需后端

**接收方**：后端解析 NetCDF4 文件并回传 JSON（温度/风速/u/v/高度层/经纬度网格）。前端通过 ECharts 2D 热力图 + 3D surface 渲染。

### 8. 高频事件节流（驾驶舱 / 路径规划 / 气象页）

**文件**：`src/utils/performance.js`

**工具**：
- `createThrottledStream(windowMs, onFlush)` — 事件缓冲/批量消费（驾驶舱实时轨迹推送用）
- `batchRaf(fn)` — 把多次 setState 合并到同一帧再执行（地图频繁重绘用）
- `throttle(fn, limit)` — 通用节流（滑块参数调整 / ECharts resize）
- `debounce(fn, wait)` — 输入框搜索 / Tab 切换

**落地场景**：
| 页面 | 节流方式 | 作用 |
|------|----------|------|
| SmartCockpit.vue | `createThrottledStream(100ms)` + `batchRaf` | 模拟 WebSocket 推送合并，减少状态更新与 DOM 重绘 |
| PathPlanningView.vue | `throttle(recompute, 120ms)` | 航点拖拽 / 参数滑块调整时，避免每像素重算路径 |
| WeatherView.vue | `throttle(redraw, 150ms)` | 时间步长/区域/透明度滑块变化时，避免每次变化重建 Leaflet heatmap 与 ECharts |

### 10. 前端 Mock 服务（P2）

**文件**：`src/mock/index.js` + `src/main.js`（在 DEV 下调用）

**设计目标**：在不依赖后端、不引入 MSW / vite-plugin-mock 等额外插件的前提下，为前端开发/演示提供可运行的 mock 数据。

**实现思路**：
- 纯浏览器端 axios request 拦截器：对 URL 前缀为 `/mock-api/` 的请求，匹配已注册路由后由本地 handler 直接返回 JSON，不发起真实网络请求
- `setupMock()` 内部已做 `import.meta.env.DEV` 守卫，生产环境直接短路返回，**不注册任何拦截器、不影响构建产物**
- 支持 `:id` 等动态路径段（如 `/mock-api/tasks/:id`）
- 支持 handler 同步/异步返回（可直接返回对象，也可返回 Promise）

**启用方式**：
```javascript
// src/main.js 已内置如下调用（自动生效）
import { setupMock } from './mock'
if (import.meta.env.DEV) setupMock()
```

**调用方式**（业务代码 / 浏览器控制台均可）：
```javascript
import axios from 'axios'

// 直接请求 /mock-api/* 前缀即可命中本地 mock 数据
const { data } = await axios.get('/mock-api/weather')
const { data } = await axios.post('/mock-api/auth/login', { username: 'admin01' })
const { data } = await axios.get('/mock-api/tasks/1001')
```

**主要接口清单**（共 30+ 条，覆盖全部业务模块）：

| 模块 | 方法 | URL | 说明 |
|------|------|-----|------|
| 认证 | POST | `/mock-api/auth/login` | 登录（自动映射默认账号 → 角色） |
| 认证 | GET | `/mock-api/auth/info` | 当前用户信息 |
| 认证 | POST | `/mock-api/auth/refresh` | 刷新 token |
| 认证 | POST | `/mock-api/auth/logout` | 登出 |
| 认证 | GET | `/mock-api/auth/permission-matrix` | 各角色权限矩阵 |
| 气象 | GET | `/mock-api/weather` | 4 模型 × 24 小时气象时间序列 |
| 气象 | GET | `/mock-api/weather/wind-field` | 经纬度网格风场（u/v/speed） |
| 气象 | GET | `/mock-api/weather/heatmap` | 气象热力点云 |
| 气象 | GET | `/mock-api/weather/variance` | 贝叶斯方差场 + 置信度 |
| 气象 | GET | `/mock-api/weather/models` | WRF / 风乌 / 天资 / 风雷 指标对比 |
| 气象 | POST | `/mock-api/weather/netcdf/upload` | NetCDF 上传与元信息返回 |
| 路径规划 | GET | `/mock-api/planning/path?start=..&end=..` | DE-RRT* / DWA / VRPTW 多方案路径 |
| 路径规划 | POST | `/mock-api/planning/calculate` | 提交规划参数并返回结果 |
| 路径规划 | GET | `/mock-api/planning/algorithms` | 可用算法列表 |
| 任务 | GET/POST | `/mock-api/tasks` | 任务列表 / 新建任务 |
| 任务 | GET/PUT/DELETE | `/mock-api/tasks/:id` | 任务详情 / 更新 / 删除 |
| 无人机 | GET | `/mock-api/drones` | 无人机列表 |
| 无人机 | GET | `/mock-api/drones/:id` | 无人机详情 |
| 同化 | POST | `/mock-api/assimilation/status` | 同化运行状态 |
| 同化 | GET | `/mock-api/assimilation/results` | 同化结果 |
| 同化 | POST | `/mock-api/assimilation/config` | 同化配置更新 |
| 监控 | GET | `/mock-api/metrics` | CPU / 内存 / 磁盘 / 网络等系统指标 |
| 监控 | GET | `/mock-api/system/health` | 服务健康检查列表 |
| 监控 | GET | `/mock-api/system/logs` | 系统日志列表 |
| 评估 | GET | `/mock-api/evaluation/models` | 多模型评估指标 |
| 评估 | GET | `/mock-api/evaluation/curve` | ROC / 命中率曲线 |
| 数据源 | GET | `/mock-api/data-sources` | 外部气象数据源列表 |
| 数据源 | GET | `/mock-api/api-config` | 天资 / 风雷 / 风乌 / WRF 等 API 配置 |
| 审计 | GET | `/mock-api/audit/logs` | 审计日志 |
| 权限模板 | GET | `/mock-api/permission-templates` | 角色权限模板 |
| Docker | GET | `/mock-api/docker/containers` | 容器运行状态 |
| UTM | GET | `/mock-api/utm/status` | 低空 UTM 对接状态 |
| UTM | POST | `/mock-api/utm/submit` | 任务报备提交 |

> 提示：开发环境启动后，在浏览器控制台执行 `window.__MOCK_ENABLED__` 可确认 mock 是否生效；`axios.get('/mock-api/metrics')` 可直接验证响应。

### 11. IndexedDB 离线大文件缓存（第 1 批新增）

**文件**：`src/utils/indexedDB.js` + `src/api/index.js`（升级）+ `public/service-worker.js`（升级）

**设计目标**：localStorage 的 5 MB 容量无法承载 NetCDF 二进制、Cesium 瓦片、离线任务包等大文件。IndexedDB 是浏览器原生的大容量对象存储，适合离线 + 大文件缓存场景。

**实现要点**：
- 原生 IndexedDB API + Promise 封装，**零新依赖**
- 数据库名 `UAV_PATH_PLANNER_CACHE_V1`，版本 1，3 个 object store：
  - `netcdf_cache` — NetCDF 文件（blob + 元信息），TTL 7 天
  - `cesium_tiles` — 地图瓦片（3D/2D），TTL 30 天
  - `task_offline_packages` — 任务离线包（JSON）
- 统一 API：`initDB / put / get / del / keys / clear / clearAll / cleanExpired / isAvailable / getStorageInfo`
- API 层：`cacheStore.getLarge / putLarge / invalidateLarge`，命中后伪造 `adapter` 返回 Blob，未命中走网络并异步回写
- Leaflet 自定义瓦片图层：`CachedTileLayer` 先查 `cesium_tiles`，命中用 `URL.createObjectURL` 返回本地 URL，否则走网络 + 写回
- Service Worker 升级：对 `/v1/weather/*` GET 请求读写 IndexedDB，底层存储从 SW cache 改为 IndexedDB（突破 ~50 MB 容量限制）
- `invalidateWeather / invalidateTask / invalidateAllCache` 同时清理 localStorage + IndexedDB

**快速自检**：在浏览器 console 执行 `(await indexedDB.databases()).map(d => d.name)` 应看到 `UAV_PATH_PLANNER_CACHE_V1`。

### 12. 移动端 / 夜间 / 快捷键 / 引导 Tour（P1-1~P1-4）

**新增文件**：
- `src/composables/useDevice.js` — 设备/方向判断（isMobile / isTablet / isDesktop / orientation）
- `src/composables/useSunTime.js` — 日落/日出估算（简化公式），供夜间模式自动切换
- `src/composables/useHotkeys.js` — 组合键/单键注册，忽略输入框焦点
- `src/components/shared/HotkeyPanel.vue` — Ctrl+/ 呼出的快捷键总览弹窗
- `src/components/shared/FeatureTour.vue` — 分步引导弹窗，按角色差异化脚本

**12.1 移动端适配**
- <768px：DefaultLayout 改为顶部 🍔 汉堡按钮 + el-drawer 抽屉菜单，480px 以下进一步压缩字号
- WeatherView / PathPlanningView / SmartCockpit / ModelEvaluationView / ParameterTuningView 均新增 `@media` 响应式规则，多列栅格在移动端坍为单列
- 任务/订单表格支持横向滚动（overflow-x: auto）

**12.2 夜间作业模式**
- 主题系统新增 `themeMode: 'auto'`，根据 sunTime 自动在 light↔dark 之间切换
- ThemeCustomizer.vue 新增「自动（跟随日落/日出）」预设卡片，展示下一次自动切换时间
- 原有 dark 主题微调：蓝色色温降低，减少视觉疲劳
- 手动切换优先：用户手动选择后保持该主题，直至改回 auto

**12.3 飞控快捷键体系**
- 全局：`R` 刷新，`Ctrl+/` 打开快捷键面板，`F` 全屏，`1~6` 快速切换菜单项
- 驾驶舱：`Space` 暂停/恢复轨迹流，`+/-` 视角缩放，`L` 切换 3D/2D 显示
- 气象页：`+/-` 缩放地图
- 路径规划：`E` 执行规划，`R` 重新计算，`+/-` 缩放地图
- 全部快捷键在 `HotkeyPanel.vue` 中列出，用户可随时查阅

**12.4 首次操作引导 Tour**
- FeatureTour.vue（el-dialog + 分步指示，零新依赖）
- 角色差异化脚本：user→首页/下单；flight→驾驶舱/规划；deployment→监控；admin→配置/权限/调试
- 首次加载自动弹出，完成后写入 `localStorage.tour_completed_${role}`，不再自动触发
- 用户菜单提供「重新引导」入口，可随时再次查看

### 13. 任务通知系统（桌面通知 + 站内信 + 铃铛红点，P1-6）

**新增文件**：
- `src/stores/notification.js` — Pinia 通知状态 store
- `src/components/shared/NotificationDrawer.vue` — 右侧抽屉式通知中心

**核心功能**：
- **多源通知**：任务完成 / 气象预警（风速>15 m/s / 强降雨） / 无人机异常（信号丢失 / 电量<20% / 禁飞区入侵） / 路径规划结果 / 配置变更 / UTM 报备审核 / 系统健康检查
- **桌面通知**：`Notification.requestPermission()` + `new Notification(...)`，可在设置页开关；每类来源独立开关
- **站内信抽屉**：DefaultLayout 顶栏 🔔 + el-badge 未读数 → 点击弹出抽屉（搜索框、来源筛选、通知卡片、标记全部已读、清空、订阅设置弹窗）
- **持久化**：`localStorage.uav_notifications_v1`，最多保留 200 条
- **离线补发**：演示模式下每 2 分钟 push 一条健康检查，用于展示系统在线状态

**已接入的通知源**：
- TasksView.vue（任务完成 / 失败 / 新增）
- OrderView.vue（订单提交）
- SmartCockpit.vue（无人机异常 × 3）
- WeatherView.vue（风速 > 15 / 强降雨预警）
- PathPlanningView.vue（规划完成 / 失败）
- ApiConfigView.vue（配置保存 / 环境切换）
- UtmIntegrationView.vue（报备通过 / 驳回 / 待人工）

### 14. 实验对比工具（多方案并排 + 差异高亮 + 导出报告，P1-20）

**文件**：`src/views/compare/ExperimentCompareView.vue`

**页面结构**
- 顶部栏：对比维度（气象模型 / 路径规划算法 / 数据同化方案）+ 添加方案 + 保存对比组 + 导出报告 + 「仅显示差异」开关
- 左栏 30%：方案卡片列表（2–4 个，颜色圆点区分，可删除）
- 右栏 70%（4 Tab）：
  - **指标对比**：横向表格，单元格差异>10%红色高亮，最优值绿色高亮
  - **曲线对比**：ECharts 多折线图（24 小时时间轴，y 指标可切换）
  - **差异摘要**：方案 A vs B 的 Top 10 差异条目（百分比排序，绿色=优化，红色=劣化）
  - **原始数据**：各方案参数 JSON 只读

**Mock 数据生成**
- 气象模型：温/风/压 24h 模拟 + RMSE/MAE/CRPS/R/Bias
- 路径规划算法：距离/时长/能耗/风险/平均转弯角度
- 数据同化方案：RMSE / 计算时长 / 迭代收敛残差 / 观测覆盖率
- 参数变更会在相同基线上叠加扰动（确定性 hash seed），保证同样参数返回同样结果

**持久化**：`localStorage.uav_compare_groups_v1`（对比组保存/加载）

### 15. 数据权限（个人 / 团队 / 全部三级过滤，P1-16）

**新增文件**：`src/components/shared/DataScopeBadge.vue`

**核心实现**：
- `authStore.user` 新增 `team`（team-a/b/c）、`dataScope`（personal/team/all）
- `canSee(ownerId, itemTeam)`：返回当前数据范围下是否可见
- 过滤页面：`TasksView.vue` / `OrderView.vue` / `TaskReportView.vue` / `SmartCockpit.vue`
  - personal → 仅自己创建的任务/订单
  - team → 同团队所有成员的数据
  - all → 全部（管理员默认）
- `DataScopeBadge`：顶栏/任务页顶部显示当前范围（el-tag，颜色区分）
- DefaultLayout 用户下拉新增：团队切换 + 数据范围切换
- PermissionTemplateView 创建用户表单新增团队/数据范围字段
- 审计日志 `CHANGE_TEAM / CHANGE_DATA_SCOPE` 自动记录权限变更

### 16. Docker 构建可视化（实时流 + 进度条 + 卡住检测，P1-9）

**文件**：`src/views/deployment/DockerBuildView.vue`

**页面结构**：
- 顶部栏：环境下拉（dev/test/prod）、镜像名（默认 uav-frontend）、版本号（默认 v1.0.0）、开始/停止/历史按钮、状态标签（idle/building/success/failed）
- 构建进度区：大进度条 + 6 阶段卡片（拉取基础镜像 / 安装依赖 / 构建应用 / 优化产物 / 打包镜像 / 上传镜像），每阶段含状态、子进度、耗时
- 日志区：深色容器（320px 固定高），每行带时间戳 + 级别；ERROR 红、WARNING 橙、INFO 灰；自动滚动开关、清空、下载 .txt
- 卡住检测：30 秒无新日志 → 顶部 alert 提示并 push 通知

**演示模式模拟流程**：每阶段约 1.5 秒（总约 10 秒）；第 4 阶段 20% 概率注入 `npm ERR!` 以模拟失败分支；成功/失败均入历史并推送桌面通知；历史保存最近 5 次。

### 17. Vite 构建分包

**文件**：`vite.config.js`

通过 `rollupOptions.output.manualChunks` 分离代码：
- `vendor`：vue/vue-router/pinia/axios
- `ui`：element-plus
- `chart`：echarts
- `map`：leaflet

配合路由级 `import()` 动态加载，首屏可按需加载仅需要的模块。

---

## 🔗 API 集成

### Axios 配置

**文件**：`src/api/index.js`

```javascript
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true
})

// 请求拦截器：缓存命中直接返回
api.interceptors.request.use(config => {
  const strategy = matchStrategy(config)
  if (strategy) {
    const cached = readCache(cacheKey(config))
    if (cached !== null) {
      return { ...config, __uav_cached__: true,
        adapter: () => Promise.resolve({ data: cached, status: 200, config, headers: { 'x-cache': 'HIT' } })
      }
    }
  }
  return config
})

// 响应拦截器：写入缓存 / 401 自动重试 / 错误分类
api.interceptors.response.use(res => {
  if (!res.config.__uav_cached__ && res.config.method.toLowerCase() === 'get') {
    const strategy = matchStrategy(res.config)
    if (strategy) writeCache(cacheKey(res.config), res.data, strategy)
  }
  return res.data
}, err => {
  // 401 / 超时 / 网络错误处理与自动重试（详见源码）
})
```

### 请求重试与并发控制

- `apiWithRetry(fn, maxRetries = 3, delay = 1000)`：指数退避重试非敏感请求
- `apiBatch(requests, concurrency = 3)`：并发请求受控执行，避免浏览器并发上限
- `RequestCanceler`：组件卸载 / 导航切换时，清理未完成请求

### 业务 API 模块

| 文件 | 用途 |
|------|------|
| `api/auth.js` | 登录 / 注册 / 登出 / 权限矩阵（P1 Nacos） |
| `api/weather.js` | 气象预报 / WRF 数据 / NetCDF 上传 |
| `api/tasks.js` | 任务 CRUD |
| `api/path.js` | 路径规划计算 |
| `api/assimilation.js` | 数据同化 |
| `api/drones.js` | 无人机管理 |
| `api/datasource.js` | 数据源管理 |
| `api/system.js` | 系统监控 / 健康检查 |
| `api/variance.js` | 方差 / 模型对比 |

---

## 🎯 核心页面功能清单（P0 + P1 + P2 已实现）

### 登录 / 注册 / 忘记密码

- 支持用户名 + 密码登录（演示模式自动识别角色）
- 支持显式选择用户类型（注册流程）
- 表单校验：用户名长度、密码强度、确认密码一致性
- 登录成功后自动重定向至角色默认首页

### 项目简介 / 首页（Dashboard）

- 系统概述、各模块入口卡片
- 角色相关的快速操作区
- 数据源 / 技术文档 / 合规文档外部链接

### 气象数据（WeatherView · 5 个子视图）

1. **气象概览** — 温度/风速/气压/湿度 4 张指标卡 + ECharts 时间序列
2. **风场矢量图** — Leaflet + 自定义 Canvas 图层绘制经纬度网格的风向箭头，颜色与长度区分风速等级
3. **气象热力图** — Leaflet + leaflet.heat；变量切换（温度/气压/降水/湍流强度）+ 透明度滑块
4. **贝叶斯方差场** — 方差热力图，顶部可信度（1 - 方差/最大方差）动态提示
5. **多模型误差对比** — ECharts 4 条平滑折线（WRF/风乌/天资/风雷），平均 RMSE 与最佳模型自动标注

### NetCDF 上传与剖面预览（WeatherView / NetCDFPreview）

- 左栏 `NetCDFChunkUploader`：拖放上传 · 进度条 · 分片数 · 速度与 ETA · 断点续传
- 右栏 Tab 1 **2D 水平剖面**（ECharts heatmap），可切换高度层
- Tab 2 **3D 垂直剖面**（ECharts surface）
- Tab 3 **原始信息**（文件名/大小/变量列表/网格坐标范围）
- "加载演示数据" 按钮：无后端也可即时查看 NetCDF 效果

### 下单（OrdersView）

- **普通用户**：起点 / 终点选点、货物重量、优先级
- **飞控 / 管理员**：额外高级配置（飞行高度、航路 RNP 约束、载荷参数、禁飞区避让策略）
- 按钮级权限控制（`orders:advanced`）
- 表单校验 + 提交成功反馈

### 智能驾驶舱（SmartCockpit）

- **3 核心指标**：实时气象 / 任务执行状态 / 路径规划耗时（顶部栏）
- **Cesium 3D 主视图**：城市三维地图 + 无人机实时轨迹 + 禁飞区多边形 + 时间轴回放（可拖拽 scrubber）
- **降级策略**：未部署 Cesium 静态资源或离线环境自动切换为 Leaflet 2D 视图（不失功能）
- **右栏面板**：无人机列表 / 选中无人机详情（坐标、航向、电池、信号、ETA）/ 禁飞区列表 / 回放控制
- **事件节流**：`createThrottledStream(100ms)` + `batchRaf` 合并推送

### 运输任务管理（TasksView）

- 任务列表 / 搜索 / 筛选
- 任务状态流转
- 角色相关的数据可见范围控制

### 路径规划（PathPlanningView）

- **左栏**：航点列表（可拖拽排序）+ 新增航点 + 气象权重 / 避障权重 / 能耗权重滑块
- **中栏**：Leaflet 地图，起/终/中间航点 marker 可**直接拖拽**；路径折线实时更新；显示总距离、预计时间、能耗、风险评分
- **右栏**：3 算法对比（DE-RRT* / DWA / VRPTW），点击卡片选中方案后，地图折线加粗高亮；自动标记"最佳方案"（风险评分最低者）
- **增强功能**：多目标权重 ECharts 雷达图可视化 + 多机协同队形配置面板（线性/V字/菱形/圆形）
- **导入导出**：Excel 批量导入航点（字段映射 + 预览）+ KML 格式导出（兼容 PX4/ArduPilot）
- 事件节流：参数调整 / 航点拖拽 `throttle(recompute, 120ms)`

### 气象站点管理（WeatherStationView）

- 站点列表展示（名称/编码/经纬度/海拔/类型/状态）
- 新增/编辑/删除站点表单
- 站点类型标签（自动站/人工站/气象雷达/探空站）
- 在线/离线状态监控
- 数据统计面板（站点总数/在线数/类型数）

### 适航性评估（AirworthinessView）

- **5 步流程**：选择方案 → 气象核验 → 适航检查 → 风险评估 → 生成报告
- 方案卡片（A/B/C 级）选择
- 气象条件核验（风速/能见度/云量/降水概率）
- 飞行器适航检查表格（电池/螺旋桨/电机/GPS/遥控/摄像头）
- ECharts 雷达图综合风险评估
- 评估报告预览 + 下载 + 放飞确认

### 参数敏感性分析（SensitivityAnalysisView）

- 待分析参数配置（气象权重/避障权重/能耗权重/最大高度/最小间距/巡航速度）
- 单因素分析 / Sobol 全局敏感度分析
- ECharts 敏感性柱状图（敏感度排名）
- 参数相关性热力图矩阵
- 分析结论 + 推荐调参方向

### 数据同化（DataAssimilationView）

- 观测数据接入
- 同化参数配置
- 同化结果可视化对比

### 系统监控面板（SystemMonitorView）

- CPU / 内存 / 磁盘 / 网络实时指标
- 服务健康检查列表
- 仅 `tester` / `deployment` / `admin` 可见

### 数据库管理（DatabaseManager）

- 仅 `admin` 可访问
- 连接状态、表概览、基础查询入口（预留）

### Docker / 服务器状态（DockerStatusView）

- 容器列表 / 状态 / 资源占用
- `deployment` / `admin` 可见

### Docker 构建可视化（DockerBuildView · P1-9 新增）

- **6 阶段构建进度**：拉取基础镜像 → 安装依赖 → 构建应用 → 优化产物 → 打包镜像 → 上传镜像
- **实时日志流**：黑色滚动容器，ERROR/WARNING 自动高亮；自动滚动开关；支持下载 .txt 日志
- **卡住检测**：30 秒无新日志自动 alert，并推送桌面通知
- **演示模式模拟流程**：每阶段约 1.5 秒，第 4 阶段 20% 概率注入失败分支；历史保存最近 5 次

### 气象模型 API 配置（ApiConfigView · 8 项生产配置 + 备份/切换）

- **天资**（CMA 公共服务 API Key）
- **风雷**（雷达 / 临近预报）
- **风乌**（上海 AI Lab 模型推理）
- **数据库**（MySQL / Redis / Nacos 独立配置卡）
- **边云协同**（Kafka Topic / Group、WebSocket 连接）
- **Model Engine**（GPU 地址 / 模型路径 / 推理设备）
- **API 网关**（限流阈值 / 熔断阈值 / Nacos DataId & Group）
- **WRF**（NetCDF4 输出目录 / 时间步长）

按钮级权限：`deployment` 仅查看，`admin` 可修改。

**新增（P1）**：配置一键备份为快照 + 加载快照 + 一键导出/导入 JSON + 环境下拉切换（开发/测试/生产）。

### 权限模板管理（PermissionTemplateView · P1 新增）

- 左侧模板列表：按角色过滤；系统模板不可删但可复制；自定义模板可编辑/删除/复制
- 中部编辑区：路由多选 + 动作多选（orders:advanced / api-config:edit / planning:execute 等）
- 右侧临时授权区：用户名绑定/过期时间/撤销管理
- 「基于模板创建用户」：直接把模板路由+动作应用到新用户
- admin 角色可见，其他角色无权限

### 模型评估看板（ModelEvaluationView · P1 新增）

- 4 个模型卡片：WRF / 风乌 / 天资 / 风雷，每卡 6 项指标（RMSE / MAE / CRPS / 相关系数 R / Bias / 命中率），最佳模型绿色高亮
- 时间序列 Tab：ECharts 多折线，顶部切换指标，可点击 legend 过滤模型
- 决策效能曲线 Tab：ROC 风格图 + AUC 卡片
- 右栏：模型多选、预测步长滑块（6/12/18/24h）、对比模式、刷新评估、CSV 导出

### 算法参数调优（ParameterTuningView · P1 新增）

- 6 类算法：DE-RRT* / DWA / GPR / 3DVAR / 5DVAR / EnKF，每类 5+ 项参数
- 左栏参数编辑（el-input-number / el-slider / el-select / el-radio），通用参数单独分组
- 右栏 4 Tab：当前配置 JSON 摘要、运行历史、收敛曲线（ECharts）、参数敏感性雷达图
- 支持保存模板、加载模板、导出 JSON

### 低空 UTM 对接（UtmIntegrationView · P1 新增）

- 左栏任务报备表单：任务编号、空域类型（低空/微型/小型）、起降时间/高度/坐标、航线/无人机型号/运营者
- 中栏报备列表：状态（待审核/已通过/已驳回/已取消）、审核时间、操作（详情/撤回/重提）；支持按编号/状态过滤
- 右栏状态监控：心跳数、最后同步时间、对接错误数；最近 20 条日志（实时推送）；模拟心跳丢失 / 模拟 UTM 推送按钮
- 提交后自动流转：70% 通过 / 20% 驳回 / 10% 待人工；flight/admin/production 角色可见

### 任务报告中心（TaskReportView · P1 新增）

- 顶部：报告类型（任务清单/气象评估/路径规划摘要）、时间范围、生成、导出 CSV / PDF（window.print 样式优化）/ XLSX
- 左栏筛选、右栏 6 张摘要卡片 + ECharts 柱状图/折线图 + 明细表
- 数据权限过滤（personal/team/all），报告仅汇总当前用户可见任务

### 个人设置（SettingsView）

- 主题（浅色 / 深色）切换
- 语言（中 / 英）切换
- 侧边栏折叠偏好
- 默认进入页面配置（可选择角色可访问的任一页面）
- **新增（P1）**：通知订阅 — 每个来源单独开关 + 桌面通知总开关 + 请求权限按钮 + 清空通知按钮

### 使用文档（DocsView）

- **Markdown 渲染**：`marked` 解析
- **GitHub 远程同步**：配置 `VITE_DOCS_URL` 或默认 URL 拉取最新文档；失败回退到内置内容
- **同步状态展示**：下拉显示文档版本 / 最后更新时间

### 主题定制（ThemeCustomizerView · P2 新增）

- **5 套预设**：浅色 / 深色 / 品牌（橙）/ 高对比度 / **自动**（跟随日落/日出）
- 左栏 40%：预设卡片（色块预览 + 一键切换）
- 右栏 60%：9 个颜色选择器（主色/背景/表面/文字/边框/成功/警告/危险/信息）+ 圆角滑块 + 阴影强度滑块
- 「应用自定义色板」按钮：覆盖 CSS 变量，写入 localStorage，下次加载保持
- 「重置为默认」：清除自定义值，恢复默认主题
- 自动模式：根据当前时间自动切换 light/dark；展示下一次自动切换时间

### 权限调试工具（PermissionDebugView · P2 新增）

- **顶部栏**：当前实际角色展示 + 「切换到模拟角色」下拉 + 应用/退出模拟按钮
- **左栏 30%**：权限矩阵表格（路由 × 当前模拟角色），显示 ✅/❌；顶部按路由键过滤
- **中栏 40%**：当前模拟角色可访问路由（el-tag 分组）+ 动作权限表格（orders:advanced / api-config.edit / planning.execute 等）
- **右栏 30%**：
  - 调试控制台（变更记录 textarea，含时间戳）
  - 清空日志 / 导出 JSON / 复制矩阵到剪贴板
  - Nacos 权限矩阵状态显示
  - authStore.token / user 概览（演示模式下）
- admin 角色独家可见

---

## 🎨 首页链接与导航配置

首页（Dashboard）包含以下外链入口：

| 类别 | 链接 | 说明 |
|------|------|------|
| 数据源 | http://www.cma.gov.cn | 中国气象局 |
| 数据源 | https://data.cma.cn/ | 国家气象科学数据中心 |
| 数据源 | https://www.shlab.org.cn/ | 上海人工智能实验室 |
| 技术 | WRF 官方文档（https://www.mmm.ucar.edu/models/wrf） | 气象研究与预报模型 |
| 技术 | NetCDF 官方文档（https://www.unidata.ucar.edu/software/netcdf/） | WRF 数据格式参考 |
| 技术 | ONNX Runtime 官方文档 | 风乌模型推理技术参考 |
| 技术 | Nacos 官方文档 | 配置中心 |
| 技术 | 项目 GitHub（https://github.com/602420232-dotcom/weather） | 代码仓库 |
| 技术 | Docker Hub（https://hub.docker.com/repositories/dithiothreitollf） | 预构建镜像 |
| 合规 | 中国民用航空局低空经济专栏（http://www.caac.gov.cn/ztzl/kongdi/） | 行业合规参考 |
| 合规 | MIT License（https://opensource.org/licenses/MIT） | 开源协议说明 |

---

## 🐳 Docker 部署

### 生产环境构建

```bash
# 构建镜像
docker build -t uav-frontend:latest ./frontend-vue

# 运行容器
docker run -d -p 3000:80 uav-frontend:latest
```

**生产环境端口（Nginx）**：`80`（容器内），映射到宿主机 `3000`

### Nginx 配置（`nginx.conf`）

- 启用 Gzip 压缩
- `/api/` 路径反向代理到后端服务
- Vue Router History 模式支持（`try_files` 回退到 `index.html`）
- 静态资源长缓存

---

## 🔧 常用命令

| 命令 | 说明 |
|------|------|
| `npm install` | 安装依赖 |
| `npm run dev` | 启动开发服务器 |
| `npm run build` | 生产构建（输出到 `dist/`，已验证通过 ✅） |
| `npm run preview` | 本地预览生产构建 |
| `npm run test` | 运行 Vitest 单元测试 |
| `npm install vite-plugin-pwa --save-dev` | 启用 PWA（可选） |

---

## 📊 已验证构建结果

最近一次构建（2026-06-09）输出概要：

- ✓ 2205 模块转换
- ✓ 315 业务模块（`NotFound`、`PermissionDenied`、`LoginView`、`RegisterView`、`WeatherView`、`PathPlanningView`、`SmartCockpit`、`ApiConfigView`、`NetCDFPreview` ...）
- 主要 chunk：
  - `vendor` 110 KB
  - `map` 150 KB
  - `ui` ~937 KB（Element Plus）
  - `chart` ~1,036 KB（ECharts）
- 构建时间：约 14s（视机器配置浮动）

---

## ⚠️ 重构与历史记录

### P0 阶段主要改动（2026-05 ~ 2026-06）

1. **UI 库迁移**：Ant Design Vue → Element Plus
2. **API 模块重构**：`api/index.js` 加入分层缓存 / 请求重试 / 并发控制
3. **8 项生产 API 配置补全**：天资 / 风雷 / 风乌 / 数据库 / 边云协同 / Model Engine / 网关 / WRF
4. **路径规划页**：航点拖拽 + 调参实时预览 + 多算法对比
5. **NetCDF 分片上传与预览**：新增组件与独立页面
6. **Cesium 3D 驾驶舱**：实时轨迹 + 禁飞区 + 时间轴回放 + Leaflet 2D 降级
7. **PWA + manifest**：离线/在线切换提示；条件加载 vite-plugin-pwa，未安装不阻塞构建
8. **高频事件节流**：驾驶舱 / 路径规划 / 气象页统一 `createThrottledStream` / `batchRaf` / `throttle`
9. **侧边栏默认收缩 + hover 展开**：用户偏好持久化
10. **DocsView 升级**：Markdown 渲染 + GitHub 远程同步

### 文件清理

- 移除重复的 `ForgotPassword.vue`（保留 `ForgotPasswordView.vue`）
- 移除旧版 `views/data/` 目录下废弃页面

---

## 📌 下一步计划（P1 / P2）

### ✅ P0 —— 已闭环

- ✅ 8 项生产 API 配置
- ✅ 风场矢量图 / 气象热力图 / 贝叶斯方差场 / 多模型误差对比
- ✅ 路径规划：拖拽航点 + 调参实时预览 + 多算法（DE-RRT*/DWA/VRPTW）方案对比
- ✅ NetCDF 分片上传 + 预览（2D 热力图 / 3D 剖面）
- ✅ Cesium 3D 驾驶舱（实时轨迹 + 禁飞区 + 时间轴回放）+ Leaflet 2D 降级
- ✅ 分层缓存（静态永久 / 气象 1h / 任务 5min）
- ✅ PWA（vite-plugin-pwa 可选安装 · 手写 SW 降级）
- ✅ 路由懒加载 + Vite 手动分包
- ✅ 高频事件节流（驾驶舱推送 / 路径拖拽 / 气象滑块）
- ✅ 构建验证：`npm run build` 成功输出 `dist/`

---

### 🚧 P1 —— 体验 & 运维 & 研究扩展（进行中 / 规划中）

- **移动端适配**（响应式栅格、触摸友好）
- **夜间作业模式**（暗色主题加强版 · 低对比度环境友好）
- **飞控快捷键**（全局键盘操作）
- **智能错误提示 + 请求自动重试**（已有基础框架，需在各业务页完善降级 UI）
- **任务报告一键导出 PDF / Excel**
- **微服务监控大盘**（服务健康 / 吞吐 / 延迟曲线）
- **配置一键备份 / 环境切换**（演示↔生产）
- **角色组批量权限管理 + 权限模板快速新建角色 + 临时授权**（P1 首位优先）
- **模型评估看板**（RMSE / CRPS / 决策效能曲线 · 多模型对比可视化）
- **算法参数调优页**（DE-RRT*/DWA/GPR/同化参数配置；支持 3DVAR/5DVAR/EnKF 切换）
- **低空 UTM 对接模块**（任务报备 / 合规审核 / 对接状态监控）
- **操作审计日志 + 前端错误自动上报**
- **敏感操作二次确认 + Token 自动续期**（已在 `api/index.js` 预留 `401 refresh` 逻辑框架）

### 🚧 P2 —— 生态迭代

- **中英双语国际化**（i18n 基础已搭建，需在各页面替换硬编码中文文案）
- **自定义主题**（品牌色 / 高对比度 / 打印友好）
- **Storybook 组件文档**（已有 `*.stories.ts` 文件目录）
- ✅ **前端 Mock 服务**（浏览器端 axios 拦截器实现，URL 前缀 `/mock-api/*`，30+ 条接口覆盖全部业务模块，已完成）
- **权限调试工具**（实时查看当前角色矩阵 / 命中权限 / 调试模拟切换角色）

---

## 📌 P1 / P2 进度与下一阶段建议

### ✅ 已完成（全部 P1/P2 模块已完成）

| 阶段 | 模块 |
|--------|------|
| **P1** | 权限模板管理页、模型评估看板、算法参数调优页、低空 UTM 对接、审计日志、Token 自动续期、敏感操作二次确认、系统监控大盘升级、API 配置备份与环境切换、任务报告中心（CSV/PDF/XLSX 导出）、智能错误提示升级、任务通知系统（桌面通知 + 站内信 + 铃铛红点）、数据权限（个人/团队/全部）、Docker 构建可视化（实时流 + 进度条 + 卡住检测）、实验对比工具、移动端适配、夜间作业模式（自动跟随日落/日出）、飞控快捷键体系、首次操作引导 Tour |
| **P2** | 国际化词条骨架（zh-CN / en-US 结构对齐）、全局 `$t()` 与 `setLocale()` 暴露、**前端 Mock 服务（URL 前缀 `/mock-api/*`，30+ 条接口、浏览器端 axios 拦截器实现、零外部插件）、自定义主题（浅色/深色/品牌色/高对比度 + 自定义色板 + 自动）、Storybook 组件文档（5 个核心组件）、权限调试工具页（实时角色矩阵 + 模拟切换）、IndexedDB 离线大文件缓存（NetCDF 分片 + Cesium 瓦片 + 任务离线包） |

### ⏳ 未完成 / 规划中

| 阶段 | 模块 |
|--------|------|
| **P3** | PX4/ArduPilot 飞控对接（MAVLink 协议）、端侧离线 SDK（离线状态面板、离线任务包） |

### ✅ 近期已完成的关键任务

| 任务 | 说明 |
|------|------|
| **Vite 配置更新** | 添加代理指向 api-gateway，配置多个后端服务路由 |
| **JWT 自动刷新机制** | 在 `stores/auth.js` 中实现定时刷新，处理刷新失败自动重试 |
| **API 层真实对接** | 更新各业务 API 模块，支持从 Mock 切换到真实后端 |
| **Docker 服务面板** | 对接真实 API，支持容器状态查看、重启、停止操作 |
| **系统监控页面** | 添加真实 API 调用，根据环境模式选择数据源 |
| **MyPanel 独立部署配置** | 更新 nginx.conf、Dockerfile、环境变量配置 |
| **国际化优化** | 完善 zh-CN/en-US 词条，更新布局组件支持国际化 |

### 🔜 下一阶段建议

1. **PX4/ArduPilot 飞控对接**：实现 MAVLink 协议对接，支持无人机实时状态获取和指令下发
2. **端侧离线 SDK**：完善离线状态面板、离线任务包功能，提升无网环境下的作业能力
3. **前端 Mock 服务升级**：接入 MSW / vite-plugin-mock 标准方案，脱离 axios 拦截器依赖
4. **端到端测试**：围绕主要业务流程加 Playwright / Cypress，防止后续回归

---

## 🧩 组件文档（Storybook · P2 已完成）

已在 `src/stories/` 中新增 5 套 Storybook 故事：

| 组件 | 路径 | 说明 |
|------|------|------|
| StatCard | `src/components/shared/StatCard.vue` | 数字统计卡片 |
| GaugePanel | `src/components/shared/GaugePanel.vue` | 仪表盘（CPU/内存/磁盘/网络指标） |
| WeatherCard | `src/components/shared/WeatherCard.vue` | 气象卡片（温度/风向/风速/气压/湿度） |
| RolePermissionMatrix | `src/components/shared/RolePermissionMatrix.vue` | 角色 × 页面权限矩阵 |
| ThemePreview | `src/components/shared/ThemePreview.vue` | 主题色板预览 |

### 运行 Storybook

```bash
npm install @storybook/vue3-vite @storybook/addon-essentials @storybook/addon-interactions --save-dev
npm install storybook --save-dev
npx storybook dev -p 6006
```

配置文件已预置：

- `.storybook/main.js`
- `.storybook/preview.js`（Element Plus + theme-vars.css + 主题切换 toolbar）
- `.storybook/vite.config.js`

---

> **最后更新**：2026-06-09  
> **当前版本**：3.1（P0 + P1 + P2 全部闭环 · 新增页面：气象站点管理 / 适航性评估 / 参数敏感性分析 / 路径规划增强：KML导出/Excel导入/多目标权重雷达图/多机队形配置）  
> **维护者**：DITHIOTHREITOL
