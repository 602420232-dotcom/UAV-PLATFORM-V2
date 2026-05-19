# UAV Path Planning Frontend - Vue3 Application

##  应用概述

Vue3 + Vite 前端应用，为无人机路径规划系统提供 Web 界面。

**技术栈**:
- Vue 3 (Composition API)
- Vite (构建工具)
- Vue Router (路由)
- Pinia (状态管理)
- Axios (HTTP 客户端)
- Ant Design Vue (UI 组件库)
- ECharts (数据可视化)
- Leaflet (2D 地图组件)
- Cesium (3D 地球组件，用于智能驾驶舱 AR 数字地图)

---

##  页面功能一览

| 路由路径 | 页面名称 | 地图类型 | 主要功能 |
|----------|---------|:------:|------|
| `/` | 首页 | — | 系统概览、快捷操作入口、系统介绍 |
| `/smart-cockpit` | 智能驾驶舱 | Cesium 3D | 4×2 态势感知面板（气象/飞行/任务/地理信息/风险预警/资源调度/历史回放），AR 数字地图无人机追踪 |
| `/path-planning` | 路径规划 | Leaflet 2D | 多任务点标记、路径多段线绘制、实时气象数据面板 |
| `/weather` | 气象数据 | Leaflet 2D | 气象热力图、多高度层切换、ECharts 趋势图 |
| `/tasks` | 任务管理 | — | 任务 CRUD、状态筛选、全生命周期管理 |
| `/drones` | 无人机管理 | — | 无人机资产 CRUD、状态筛选 |
| `/history` | 历史记录 | — | 三重过滤查询、历史任务详情 |
| `/data-sources` | 数据源管理 | — | 多源气象数据分类管理 |
| `/monitoring` | 系统监控 | — | CPU/内存/磁盘监控、服务响应时间、任务统计 |
| `/example` | 功能示范 | Leaflet 2D | 路径规划示例、气象数据趋势、真实数据展示 |

---

##  端口配置

### 开发服务器端口

**默认端口**: `3000`

**配置文件**: `vite.config.js`

```javascript
export default defineConfig({
  server: {
    port: 3000,  // 开发服务器端口
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
| `/api` | `http://localhost:8080` | API 网关代理 |

**代理规则**:
- 请求 `/api/v1/**` → `http://localhost:8080/v1/**`
- 请求 `/api/forecast/**` → `http://localhost:8080/forecast/**`
- 请求 `/api/planning/**` → `http://localhost:8080/planning/**`

---

##  快速开始

### 环境要求

- **Node.js**: 16+ (推荐 18.x)
- **npm**: 8+ 或 **pnpm**: 8+

### 启动开发服务器

```bash
cd uav-path-planning-system/frontend-vue
npm install
# 或 pnpm install
```

> **注意**：`npm install` 后首次 `npm run dev` 或 `npm run build` 会自动执行 `node scripts/copy-cesium-assets.cjs`，将 Cesium 的 Workers/Assets/Widgets/ThirdParty 复制到 `public/cesium/` 目录。

```bash
# 开发模式(端口 3000)
npm run dev

# 生产构建
npm run build

# 预览生产构建
npm run preview

# 手动复制 Cesium 静态资源（仅在未自动执行时需要）
npm run copy-cesium
```

### 访问应用

开发服务器启动后访问: **http://localhost:3000**

---

##  项目结构

```
frontend-vue/
├── index.html                      # HTML 入口（含 Cesium CESIUM_BASE_URL 配置）
├── package.json                    # npm 依赖与脚本声明
├── vite.config.js                  # Vite 配置（端口、代理、Cesium 分 chunk）
├── .env                            # 开发环境变量（Cesium Token 等）
├── .env.production                 # 生产环境变量
├── scripts/
│   └── copy-cesium-assets.cjs      # Cesium 静态资源自动复制脚本
├── src/
│   ├── main.js                     # Vue 应用入口（含 Cesium CSS 导入）
│   ├── App.vue                     # 根组件（顶部导航栏 + 路由出口）
│   ├── router/
│   │   └── index.js                # 路由配置（共 10 个路由）
│   ├── views/                      # 页面组件
│   │   ├── HomeView.vue            # 首页/系统概览
│   │   ├── SmartCockpit.vue        # 智能驾驶舱（Cesium 3D AR 数字地图）
│   │   ├── PathPlanningView.vue    # 路径规划（Leaflet 2D 地图）
│   │   ├── WeatherView.vue         # 气象数据（Leaflet + ECharts）
│   │   ├── TasksView.vue           # 任务管理
│   │   ├── DronesView.vue          # 无人机管理
│   │   ├── HistoryView.vue         # 历史记录
│   │   ├── MonitoringView.vue      # 系统监控
│   │   ├── DataSourceView.vue      # 数据源管理
│   │   └── ExampleView.vue         # 功能示范
│   └── utils/                      # 可视化工具类
│       ├── visualization.js        # Leaflet + ECharts 通用封装
│       ├── ar_digital_map.js       # Cesium AR 数字地图（3D 路径/热力图/无人机追踪）
│       ├── trajectory_4d.js        # 4D 轨迹可视化（Cesium 时间轴）
│       ├── enhanced_visualizer.js  # 增强可视化（Cesium 多无人机协同）
│       ├── performance.js          # 性能优化（防抖/节流/缓存）
│       └── errorHandler.js         # 错误处理与容错
└── public/                         # 构建时自动生成的 Cesium 静态资源
    └── cesium/                     # Workers / Assets / Widgets / ThirdParty
```

---

##  配置说明

### 开发环境配置

**端口配置** (`vite.config.js`):
```javascript
server: {
  port: 3000,              // 开发服务器端口
  host: '0.0.0.0',        // 监听所有网卡
  open: true,              // 自动打开浏览器
  cors: true               // 允许跨域
}
```

### 生产环境配置

**构建输出目录**: `dist/`

**环境变量**:
```bash
# .env.production
VITE_API_BASE_URL=/api
VITE_APP_TITLE=UAV Path Planning
VITE_CESIUM_ION_TOKEN=your_cesium_ion_token_here  # 生产环境 Cesium Token
```

---

##  Cesium 3D 地图配置

智能驾驶舱（`/smart-cockpit`）使用 Cesium 实现 3D AR 数字地图，需要额外配置。

### 获取 Cesium Ion Access Token

1. 访问 [https://ion.cesium.com/signin](https://ion.cesium.com/signin) 注册免费账户
2. 登录后进入 **Access Tokens** 页面，复制默认 Token（或创建新 Token）
3. 将该 Token 填入 `.env` 文件：

```bash
# .env（开发环境）
VITE_CESIUM_ION_TOKEN=eyJhbGciOiJIUzI1NiIs...你的真实Token

# .env.production（生产环境）
VITE_CESIUM_ION_TOKEN=eyJhbGciOiJIUzI1NiIs...你的真实Token
```

> **免费账户限制**：基础全球影像底图、3D Tiles 地形等核心服务免费使用。如需高级数据（Bing Maps、高分辨率地形）需升级付费计划。

### Cesium 静态资源复制

Cesium 依赖 `Workers/`、`Assets/`、`Widgets/` 目录中的静态文件。`npm run dev` 和 `npm run build` 会自动执行 `scripts/copy-cesium-assets.cjs` 脚本将这些文件从 `node_modules/cesium/Build/Cesium/` 复制到 `public/cesium/`。

若自动复制未触发，可手动执行：

```bash
npm run copy-cesium
```

### Vite 构建优化（已配置）

以下优化已在 `vite.config.js` 中预置：

| 优化项 | 配置 | 说明 |
|--------|------|------|
| Cesium 独立分 chunk | `manualChunks.cesium: ['cesium']` | Cesium 不会混入 vendor chunk，避免主包过大 |
| chunkSizeWarningLimit | `1500` KB | 提高阈值（Cesium 库体量大） |
| sourcemap | `false` | 生产构建关闭 sourcemap 减小体积 |
| CESIUM_BASE_URL | `/cesium/` | 通过 `define` + `index.html` 全局注入，锁定静态资源路径 |
| Cesium CSS | `main.js` 中 `import 'cesium/Build/Cesium/Widgets/widgets.css'` | 全局导入 Cesium 控件样式 |
| 预构建优化 | `optimizeDeps.include` 含 `cesium` | Vite 开发模式预构建 Cesium，加速冷启动 |

---

##  API 集成

### 后端服务连接

前端通过 API 网关与后端服务通信。

| 后端服务 | 端口 | API 前缀 | 用途 |
|----------|------|----------|------|
| **API Gateway** | 8088 | `/api` | 统一入口 |
| **Platform Service** | 8080 | `/api/v1` | 用户认证、任务管理 |
| **Meteor Forecast** | 8082 | `/api/forecast` | 气象预报 |
| **Path Planning** | 8083 | `/api/planning` | 路径规划 |
| **Data Assimilation** | 8084 | `/api/assimilation` | 数据同化 |

### Axios 配置

**文件**: `src/api/index.js`

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000
})

// 请求拦截器
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      // 处理未授权
      router.push('/login')
    }
    return Promise.reject(error)
  }
)

export default api
```

---

##  Docker 部署

### 开发环境 Docker

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  frontend:
    build:
      context: ./frontend-vue
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"    # 映射到宿主机 3000 端口
    volumes:
      - ./frontend-vue/src:/app/src
    environment:
      - VITE_API_BASE_URL=/api
    command: npm run dev
```

### 生产环境构建

```bash
# 构建镜像
docker build -t uav-frontend:latest ./frontend-vue

# 运行容器
docker run -d -p 3000:80 uav-frontend:latest
```

**生产环境端口**: `80` (Nginx)

---

##  常用命令

| 命令 | 说明 | 端口 |
|------|------|------|
| `npm run dev` | 启动开发服务器 | 3000 |
| `npm run build` | 生产构建 | - |
| `npm run preview` | 预览构建结果 | 4173 |
| `npm run lint` | 代码检查 | - |
| `npm run test` | 运行测试 | - |

---

##  生产部署

### Nginx 配置

```nginx
server {
    listen 80;
    server_name _;
    
    root /usr/share/nginx/html;
    index index.html;
    
    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    
    # API 代理
    location /api/ {
        proxy_pass http://backend:8088/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Vue Router History 模式
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```


---

> **最后更新**: 2026-05-09  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
