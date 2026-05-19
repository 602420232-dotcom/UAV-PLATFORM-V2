import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  define: {
    CESIUM_BASE_URL: JSON.stringify('/cesium/')
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  build: {
    minify: 'esbuild',
    chunkSizeWarningLimit: 1500,
    target: ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari14'],
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia', 'axios'],
          ui: ['ant-design-vue'],
          chart: ['echarts'],
          map: ['leaflet'],
          cesium: ['cesium']
        }
      }
    },
    cacheDir: './node_modules/.vite-cache',
    sourcemap: false
  },
  optimizeDeps: {
    include: [
      'vue', 'vue-router', 'pinia', 'axios',
      'leaflet', 'echarts', 'ant-design-vue',
      'cesium'
    ],
    exclude: []
  }
})
