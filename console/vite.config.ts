import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8258',
        changeOrigin: true,
        // Gateway 已有 /api 前缀路由，前端 baseURL 为 '/api'
        // 请求如 /api/v1/algorithms/list -> 代理到 http://localhost:8258/api/v1/algorithms/list
      },
    },
  },
})
