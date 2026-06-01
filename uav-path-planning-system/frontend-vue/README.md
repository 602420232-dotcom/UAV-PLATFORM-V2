# UAV Path Planning Frontend - Vue3 Application

## 📋 应用概述

Vue3 + Vite 前端应用，为无人机路径规划系统提供 Web 界面。

**技术栈**:
- Vue 3 (Composition API)
- Vite (构建工具)
- Vue Router (路由)
- Pinia (状态管理)
- Axios (HTTP 客户端)
- Ant Design Vue (UI 组件库)
- ECharts (数据可视化)
- Leaflet (地图组件)

---

## 🔌 端口配置

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

## 🚀 快速开始

### 环境要求

- **Node.js**: 16+ (推荐 18.x)
- **npm**: 8+ 或 **pnpm**: 8+

### 安装依赖

```bash
cd uav-path-planning-system/frontend-vue
npm install
# 或
pnpm install
```

### 启动开发服务器

```bash
# 开发模式 (端口 3000)
npm run dev

# 生产构建
npm run build

# 预览生产构建
npm run preview
```

### 访问应用

开发服务器启动后，访问: **http://localhost:3000**

---

## 📁 项目结构

```
frontend-vue/
├── src/
│   ├── components/      # Vue 组件
│   ├── views/          # 页面视图
│   ├── stores/         # Pinia 状态管理
│   ├── api/            # API 调用
│   ├── router/         # Vue Router 配置
│   ├── App.vue         # 根组件
│   └── main.js         # 应用入口
├── public/            # 静态资源
├── index.html         # HTML 入口
├── vite.config.js     # Vite 配置 (端口配置)
├── package.json
└── README.md
```

---

## ⚙️ 配置说明

### 开发环境配置

**端口配置** (`vite.config.js`):
```javascript
server: {
  port: 3000,              // 开发服务器端口
  host: '0.0.0.0',        // 监听所有网卡
  open: true,             // 自动打开浏览器
  cors: true              // 允许跨域
}
```

### 生产环境配置

**构建输出目录**: `dist/`

**环境变量**:
```bash
# .env.production
VITE_API_BASE_URL=/api
VITE_APP_TITLE=UAV Path Planning
```

---

## 🔗 API 集成

### 后端服务连接

前端通过 API 网关与后端服务通信：

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

## 🐳 Docker 部署

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

## 🔧 常用命令

| 命令 | 说明 | 端口 |
|------|------|------|
| `npm run dev` | 启动开发服务器 | 3000 |
| `npm run build` | 生产构建 | - |
| `npm run preview` | 预览构建结果 | 4173 |
| `npm run lint` | 代码检查 | - |
| `npm run test` | 运行测试 | - |

---

## 🌐 生产部署

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

> **最后更新**: 2026-05-08  
> **版本**: 2.1  
> **维护者**: DITHIOTHREITOL
