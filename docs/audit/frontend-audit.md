# 🛡️ 前端/移动端深度审计报告

**审计日期**: 2026-05-31  
**审计范围**: `uav-mobile-app/` (Flutter/Dart) + `uav-path-planning-system/frontend-vue/` (Vue.js)  
**执行者**: OpenClaw 审计子代理

---

## 📋 目录

- [1. 审计摘要](#1-审计摘要)
- [2. Flutter/Dart 审计](#2-flutterdart-审计)
- [3. Vue.js 前端审计](#3-vuejs-前端审计)
- [4. nginx 配置审计](#4-nginx-配置审计)
- [5. 平台配置审计](#5-平台配置审计)
- [6. 自动修复记录](#6-自动修复记录)
- [7. 改进建议优先级](#7-改进建议优先级)

---

## 1. 审计摘要

| 严重级别 | Flutter | Vue.js | 合计 |
|---------|---------|--------|------|
| 🔴 严重 (Critical) | 2 | 2 | 4 |
| 🟠 高 (High) | 2 | 3 | 5 |
| 🟡 中 (Medium) | 4 | 4 | 8 |
| 🟢 低 (Low) | 3 | 5 | 8 |
| **总计** | **11** | **14** | **25** |

**总体评估**: 代码结构良好，架构清晰（Flutter 使用 Riverpod + clean architecture，Vue 使用 Pinia + router）。核心安全问题已自动修复，大部分问题为改进建议类。

---

## 2. Flutter/Dart 审计

### 🔴 严重问题

#### 2.1 [已修复] 证书校验全局禁用 — `api_client.dart:40`

```dart
client.badCertificateCallback =
    (X509Certificate cert, String host, int port) => true;  // ❌ 接受所有证书！
```

**风险**: 允许所有 HTTPS 证书，导致 Man-in-the-Middle 攻击完全可行。攻击者可以拦截所有 API 通信。

**修复**: 改为仅在 debug 模式下生效（通过 `assert` 包裹），release 构建时自动失效：
```dart
assert(() {
  client.badCertificateCallback = ...;
  return true;
}());
```

#### 2.2 [已修复] 硬编码凭证 — `login_page.dart:16-17`

```dart
final _usernameController = TextEditingController(text: 'admin');
final _passwordController = TextEditingController(text: 'admin123');
```

**风险**: 预填管理员凭证，任何人安装后可直接登录。若发布到应用商店这会构成严重安全事故。

**修复**: 已清除预填值，改为空控制器。

### 🟠 高优先级

#### 2.3 [已修复] 边缘服务硬编码URL — `edge_coordinator_service.dart:70`

```dart
static const String edgeBaseUrl = 'http://localhost:8000';  // ❌ 硬编码
```

**修复**: 改为从 `AppConfig.apiEndpoints` 读取，支持运行时配置。

#### 2.4 Android `usesCleartextTraffic="true"` — `AndroidManifest.xml`

```xml
<application android:usesCleartextTraffic="true">
```

**风险**: 全局允许明码 HTTP 流量，Release 版本应禁用。应在 `network_security_config.xml` 中只对特定域名豁免。

**建议**: 创建 `res/xml/network_security_config.xml`，仅对 `localhost`/`10.0.2.2` 开启明文。

### 🟡 中优先级

#### 2.5 Logger 级别在生产环境为 `debug` — `logger.dart:8`

```dart
level: Level.debug,
```

**风险**: 生产环境输出过多调试日志，可能泄露内部信息和性能下降。

**建议**: 使用 `kReleaseMode` 动态判断：
```dart
level: kReleaseMode ? Level.warning : Level.debug,
```

#### 2.6 `SecureStorage` 与 `LocalStorage` 存在重复的 server URL 存储

`SecureStorage` 和 `LocalStorage` 都保存了 `server_url`，可能导致数据和权限不一致。

**建议**: 统一到 `LocalStorage`（SharedPreferences），仅 token 类敏感数据放 `SecureStorage`。

#### 2.7 API 路径使用绝对路径，绕过 `AppConfig.api()` 抽象

**涉及文件**: `auth_service.dart`, `drone_service.dart`, `task_service.dart`, `weather_service.dart` 等

所有 service 中使用硬编码路径如 `/api/v1/auth/login`，未使用 `AppConfig.api('platform')` 方法。

**建议**: 统一使用 `AppConfig.api()` 生成 API URL，便于多环境切换。

#### 2.8 缺少 Token 自动刷新机制

`api_interceptor.dart` 在收到 401 时仅清除 token，未尝试自动刷新：
```dart
void onError(...) {
    if (err.response?.statusCode == 401) {
      _secureStorage.clearToken();  // 只清除，不刷新
    }
}
```

### 🟢 低优先级

#### 2.9 iOS Info.plist 缺少位置权限声明

`Info.plist` 中没有 `NSLocationWhenInUseUsageDescription`。Flutter Map 使用了地图功能但未声明权限。

**建议**: 添加位置使用说明键值。

#### 2.10 Android 缺少 ACCESS_FINE_LOCATION 权限

`AndroidManifest.xml` 只有 `INTERNET` / `ACCESS_NETWORK_STATE` / `ACCESS_WIFI_STATE`，缺少位置权限。

**建议**: 添加 `<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>`

#### 2.11 `flutter_riverpod` 使用 `StateProvider` 而非 `NotifierProvider`

`app_providers.dart` 中大量使用 `StateProvider` 管理复杂对象状态（如 `planningResultProvider`），易导致状态不一致。

**建议**: 复杂对象使用 `NotifierProvider` 封装业务逻辑。

---

## 3. Vue.js 前端审计

### 🔴 严重问题

#### 3.1 [已修复] API 路径重复前缀 — 所有 API 模块

**问题**: `axios.create({ baseURL: '/api' })` 已设置基础路径，但 API 模块又拼接了 `/api/...` 导致实际请求为 `/api/api/v1/...`。

| 文件 | 修复前 | 修复后 |
|------|--------|--------|
| `auth.js` | `/api/v1/auth/login` | `/v1/auth/login` |
| `drones.js` | `BASE = '/api/v1/drones'` | `BASE = '/v1/drones'` |
| `tasks.js` | `BASE = '/api/v1/tasks'` | `BASE = '/v1/tasks'` |
| `system.js` | `BASE = '/api/v1'` | `BASE = '/v1'` |
| `weather.js` | `const BASE = '/api/v1/weather'` + 模板字符串 | 改为直接使用完整路径 |

**影响**: 若 Vite dev server proxy 配置为 `/api -> localhost:8080`，则实际 URL 变为 `/api/api/v1/...`，后端可能 404。

#### 3.2 Token 存储在 `localStorage` — `auth.js:5`

```javascript
localStorage.setItem('token', token)           // ❌ XSS 可读
localStorage.setItem('user', JSON.stringify(res.user))  // ❌ 用户信息泄露
```

**风险**: `localStorage` 可被任何同源 JavaScript 读取，XSS 攻击可直接窃取 token 和用户信息。

**建议**: 
- Token 改用 `httpOnly` Cookie（需后端配合 `Set-Cookie` 头）
- 或至少使用 `sessionStorage` (关闭标签页后清除)
- 先用 `js-cookie` 包过渡

### 🟠 高优先级

#### 3.3 `HistoryView.vue` 使用 `alert()` — 已修复

修复前使用了原生 `alert('导出功能已触发')`，用户体验差。已改为 `message.info()`。

#### 3.4 `MonitoringView.vue` 定时器泄漏风险

```javascript
onMounted(loadMonitoring)
setInterval(loadMonitoring, 60000)  // ❌ 组件卸载时不清理
```

`setInterval` 在组件生命周期外运行，HMR 热更新时会累积多个定时器。

**建议**: 
```javascript
const timer = ref(null)
onMounted(() => {
  loadMonitoring()
  timer.value = setInterval(loadMonitoring, 60000)
})
onUnmounted(() => clearInterval(timer.value))
```

#### 3.5 混合真实API与演示数据 — 多个Views

`DronesView`, `TasksView`, `WeatherView`, `HistoryView`, `PathPlanningView` 中混合了 API 调用和 demo 数据回退逻辑。每个视图都独立实现了演示数据。

**建议**: 提取到统一的 `demoData.js` fixture 文件和 store action 中。

### 🟡 中优先级

#### 3.6 Cesium Ion Token 占位符 — `.env` / `.env.production`

```env
VITE_CESIUM_ION_TOKEN=your_cesium_ion_token_here
```

生产构建时未替换为真实 token，3D 地球功能将不可用。

#### 3.7 Leaflet CSS 从 CDN 加载 — `index.html`

```html
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
```

**风险**: 依赖外部 CDN，离线环境或 CDN 故障时地图样式丢失。

**建议**: 将 leaflet.css 打包进项目依赖。

#### 3.8 `ExampleView.vue` ECharts/Leaflet 实例未完全清理

- `onMounted` 注册了 `handleResize` 但 `onUnmounted` 未移除
- 页面切换时 ECharts 实例和 Leaflet map 可能残留

#### 3.9 菜单配置在 `App.vue` 中重复

桌面端菜单和移动端抽屉菜单的 items 完全重复，维护成本高。

**建议**: 提取为共享数组 `menuItems`。

### 🟢 低优先级

#### 3.10 开发日志未移除 — 已修复

| 文件 | 修复前 | 修复后 |
|------|--------|--------|
| `DronesView.vue` | `console.log('[DronesView] 使用演示数据')` | `console.error` 仅在实际失败时 |
| `TasksView.vue` | `console.log('[TasksView] 使用演示数据')` | `console.error` 仅在实际失败时 |
| `WeatherView.vue` | `console.log(...)` | 改为条件判断 |
| `HistoryView.vue` | `console.log('表格变化:...')` + `alert()` | 移除日志+改用 `message.info` |

#### 3.11 `DataSourceView.vue` 有 2 个 TODO 未实现

```javascript
// TODO: 实现删除逻辑
// TODO: 实现保存逻辑
```

#### 3.12 `router/index.js` 中 webpack chunk name 注释无效

```javascript
/* webpackChunkName: "planning" */
```

项目使用 Vite 而非 webpack，该注释不生效。Vite 分包应通过 `rollupOptions.output.manualChunks` 配置（已在 `vite.config.js` 中实现）。

#### 3.13 缺少 `.env.development` 文件

仅 `.env` 和 `.env.production`，建议添加 `.env.development` 明确开发环境配置。

---

## 4. nginx 配置审计

### 4.1 移动端 `nginx.conf`

```nginx
location /api/ {
    proxy_pass http://uav-gateway:8088/;   # 末尾 / 会剥离 /api/ 前缀
}
```

- ✅ Gzip 已启用
- ✅ 静态资源缓存已配置
- ⚠️ 缺少安全头 (`X-Frame-Options`, `X-Content-Type-Options`, `Content-Security-Policy`)
- ⚠️ 缺少 `proxy_set_header X-Forwarded-For`

### 4.2 Vue 前端 `nginx.conf`

```nginx
location /api/ {
    proxy_pass http://uav-gateway:8088/api/;  # 末尾 /api/ 保留前缀
}
```

- ✅ 正确保留了 `/api/` 前缀（与 Flutter nginx 不同——Vue 的 API 请求以 `/api/` 开头）
- ✅ `X-Forwarded-For` 和 `X-Forwarded-Proto` 已配置
- ⚠️ 同样缺少安全头

### 4.3 不一致问题

两个 `nginx.conf` 的 API 代理行为不同：

| 配置 | `/api/v1/foo` 转发到 |
|------|---------------------|
| Flutter | `http://uav-gateway:8088/v1/foo` (剥离) |
| Vue | `http://uav-gateway:8088/api/v1/foo` (保留) |

**建议**: 统一使用一种方式。推荐 Vue 方式（保留前缀），因为后端 Gateway 的路由可能包含 `/api/` 前缀。

---

## 5. 平台配置审计

### 5.1 Android (`AndroidManifest.xml`)

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 权限合理性 | ⚠️ | `usesCleartextTraffic=true` 全局开启，需限制 |
| 缺少位置权限 | ❌ | 地图功能需要 `ACCESS_FINE_LOCATION` |
| `taskAffinity=""` | ⚠️ | 空值可能影响多任务切换 |
| debug manifest | ✅ | 仅声明 INTERNET，无安全泄露 |

### 5.2 iOS (`Info.plist`)

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 位置权限描述 | ❌ | 缺少 `NSLocationWhenInUseUsageDescription` |
| 相机/相册权限 | ✅ | 未使用，已正确排除 |
| `UIBackgroundModes` | ✅ | 未声明，合理（非后台飞行关键应用） |
| App Transport Security | ⚠️ | 未配置例外；开发环境连接 localhost 可能需要 |

### 5.3 macOS (`Info.plist`)

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 沙盒权限 | ⚠️ | 未声明网络客户端权限 |

---

## 6. 自动修复记录

以下问题已通过代码修改自动修复：

| # | 文件 | 问题 | 操作 |
|---|------|------|------|
| 1 | `api_client.dart` | 证书校验全局禁用 | 改为 assert 包裹（仅 debug 生效） |
| 2 | `login_page.dart` | 硬编码凭证 `admin`/`admin123` | 清除预填值 |
| 3 | `edge_coordinator_service.dart` | 硬编码边缘服务 URL | 改为从 AppConfig 读取 |
| 4 | `auth.js` | API 路径重复 `/api/api/v1/...` | 改为 `/v1/...` |
| 5 | `drones.js` | API 路径重复前缀 | `BASE` 改为 `/v1/drones` |
| 6 | `tasks.js` | API 路径重复前缀 | `BASE` 改为 `/v1/tasks` |
| 7 | `system.js` | API 路径重复前缀 | `BASE` 改为 `/v1` |
| 8 | `weather.js` | API 路径重复前缀 | 直接使用完整路径 |
| 9 | `DronesView.vue` | `console.log` 调试输出 | 改为条件判断 |
| 10 | `TasksView.vue` | `console.log` 调试输出 | 改为条件判断 |
| 11 | `WeatherView.vue` | `console.log` 调试输出 | 改为条件判断 |
| 12 | `HistoryView.vue` | `console.log` + `alert()` | 改为 `message.info` |

---

## 7. 改进建议优先级

### 立即处理 (本周)

1. **[P0]** 检查后端 Gateway 路由，确认 `/api/v1/...` 实际路径（可能与前端不一致）
2. **[P0]** 配置 Android `network_security_config.xml` 限制 cleartext 范围
3. **[P0]** 为 iOS 添加 `NSLocationWhenInUseUsageDescription`
4. **[P1]** 替换 `localStorage` 中的 token 存储为 `httpOnly` Cookie

### 短期 (本迭代)

5. **[P1]** Logger 级别改为根据 `kReleaseMode` 动态切换
6. **[P1]** MonitoringView.vue 的 setInterval 添加清理逻辑
7. **[P2]** 提取共享菜单配置到独立文件
8. **[P2]** 提取演示数据到 fixture 文件
9. **[P2]** 统一 Bundle leaflet.css（不再从 CDN 加载）
10. **[P2]** 实现 Token 自动刷新（401 前尝试 refresh_token）

### 长期 (下个迭代)

11. **[P3]** 添加安全头到 nginx 配置 (`X-Frame-Options`, `CSP` 等)
12. **[P3]** 统一两个 nginx.conf 的 API 代理规则
13. **[P3]** 实现 DataSourceView 的保存/删除逻辑
14. **[P3]** 将 StateProvider 迁移到 NotifierProvider 封装复杂业务
15. **[P3]** 为 Vue 组件添加请求取消控制器 (`AbortController`)

---

## 📊 代码质量评分

| 维度 | Flutter | Vue.js | 说明 |
|------|---------|--------|------|
| 架构设计 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Flutter 分层清晰；Vue 有重复代码 |
| 安全性 | ⭐⭐⭐ | ⭐⭐⭐ | 证书校验/硬编码凭证已修复；token 存储需改善 |
| 错误处理 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | API 错误分类完善；降级演示数据设计合理 |
| 代码规范 | ⭐⭐⭐⭐ | ⭐⭐⭐ | analysis_options 完善；Vue 有少量 console.log |
| 可维护性 | ⭐⭐⭐⭐ | ⭐⭐⭐ | 依赖注入清晰；Vue 缺少统一配置 |
| 性能 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Dio/axios 超时合理；ECharts/Map 清理需完善 |
| 文档 | ⭐⭐⭐ | ⭐⭐ | 代码内注释较充分；缺少架构设计文档 |

**综合评分**: 3.6 / 5.0 (良好，有明确的改进空间)

---

*本报告由 OpenClaw 审计子代理自动生成。人工复查建议关注标记为 🔴 和 🟠 的项目。*
