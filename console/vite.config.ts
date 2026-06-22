import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import compression from 'vite-plugin-compression'

export default defineConfig({
  plugins: [
    vue(),
    compression({
      algorithm: 'gzip',
      ext: '.gz',
      threshold: 10240, // 10KB以上才压缩
      deleteOriginFile: false,
    }),
    compression({
      algorithm: 'brotliCompress',
      ext: '.br',
      threshold: 10240,
      deleteOriginFile: false,
    }),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    port: 3002,
    proxy: {
      '/api': {
        target: 'http://localhost:8258',
        changeOrigin: true,
        // Gateway 已有 /api 前缀路由，前端 baseURL 为 '/api'
        // 请求如 /api/v1/algorithms/list -> 代理到 http://localhost:8258/api/v1/algorithms/list
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('element-plus')) {
            return 'element-plus'
          }
          if (id.includes('vue') || id.includes('pinia') || id.includes('vue-router')) {
            return 'vue-vendor'
          }
          // ECharts 不再单独拆包，随使用它的页面组件一起打包
          // 避免首页预加载 ECharts 导致 passive event listener violation
        },
      },
    },
  },
})
