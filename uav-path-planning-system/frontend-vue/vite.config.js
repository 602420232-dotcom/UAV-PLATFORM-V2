import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'

// ===== VitePWA 配置（未安装时跳过，不阻塞构建）
const pwaOptions = {
  registerType: 'autoUpdate',
  includeAssets: ['favicon.ico', 'robots.txt', 'apple-touch-icon.png'],
  manifest: {
    name: '无人机路径规划系统',
    short_name: 'UAV Path Planning',
    description: '基于 WRF 气象驱动的无人机 VRP 智能路径规划系统',
    theme_color: '#409EFF',
    background_color: '#ffffff',
    display: 'standalone',
    start_url: '/',
    lang: 'zh-CN',
    icons: [
      { src: '/vite.svg', sizes: '192x192', type: 'image/svg+xml', purpose: 'any' },
      { src: '/vite.svg', sizes: '512x512', type: 'image/svg+xml', purpose: 'any maskable' }
    ]
  },
  workbox: {
    globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
    runtimeCaching: [
      {
        urlPattern: ({ request }) => ['style', 'script', 'worker', 'image'].includes(request.destination),
        handler: 'CacheFirst',
        options: {
          cacheName: 'uav-static-assets',
          expiration: { maxEntries: 60, maxAgeSeconds: 60 * 60 * 24 * 30 }
        }
      },
      {
        urlPattern: ({ url, request }) => request.method === 'GET' && /\/v1\/weather\b/.test(url.pathname),
        handler: 'StaleWhileRevalidate',
        options: {
          cacheName: 'uav-weather-api',
          expiration: { maxEntries: 50, maxAgeSeconds: 60 * 60 }
        }
      },
      {
        urlPattern: ({ url, request }) => request.method === 'GET' && /\/v1\/(tasks|planning|assimilation)\b/.test(url.pathname),
        handler: 'NetworkFirst',
        options: {
          cacheName: 'uav-task-api',
          expiration: { maxEntries: 30, maxAgeSeconds: 5 * 60 }
        }
      },
      {
        urlPattern: ({ url }) => url.origin !== self.location.origin,
        handler: 'CacheFirst',
        options: {
          cacheName: 'uav-cross-origin',
          expiration: { maxEntries: 30, maxAgeSeconds: 60 * 60 * 24 * 7 }
        }
      }
    ]
  },
  devOptions: { enabled: false }
}

// 条件式加载 vite-plugin-pwa：未安装时静默跳过，不阻塞构建
function tryLoadPwa() {
  try {
    const { VitePWA } = require('vite-plugin-pwa')
    // eslint-disable-next-line no-console
    console.info('[vite] PWA 插件已启用（vite-plugin-pwa）')
    return VitePWA(pwaOptions)
  } catch (_) {
    // eslint-disable-next-line no-console
    console.warn('[vite] vite-plugin-pwa 未安装，跳过 PWA 插件；执行 npm install vite-plugin-pwa --save-dev 后可启用')
    return null
  }
}

export default defineConfig({
  plugins: [vue(), vueJsx(), tryLoadPwa()].filter(Boolean),
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8088',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/actuator': {
        target: 'http://localhost:8080',
        changeOrigin: true
      },
      '/nacos': {
        target: 'http://localhost:8848',
        changeOrigin: true
      }
    }
  },
  build: {
    minify: 'esbuild',
    chunkSizeWarningLimit: 1000,
    target: ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari14'],
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia', 'axios'],
          ui: ['element-plus'],
          chart: ['echarts'],
          map: ['leaflet']
        }
      }
    },
    cacheDir: './node_modules/.vite-cache'
  },
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'axios', 'leaflet', 'echarts', 'element-plus'],
    exclude: []
  }
})

// ===== Storybook 说明（不影响生产构建）=====
// 本项目的组件文档基于 @storybook/vue3-vite 构建，
// 配置文件位于 .storybook/（main.js / preview.js / vite.config.js），
// 组件 stories 位于 src/stories/ 目录下。
// 如需本地启动 Storybook 浏览组件文档，请执行：
//   npm install @storybook/vue3-vite @storybook/addon-essentials @storybook/addon-interactions --save-dev
//   npx storybook init
// 之后直接覆盖 .storybook/ 下的配置文件即可；
// 运行：npx storybook dev -p 6006
// 注：Storybook 相关依赖不纳入 package.json 生产依赖，
//     npm run build 也不会构建 Storybook 本身。
