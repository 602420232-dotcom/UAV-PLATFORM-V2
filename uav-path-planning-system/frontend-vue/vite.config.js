import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
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
    chunkSizeWarningLimit: 1000,
    target: ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari14'],
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia', 'axios'],
          ui: ['ant-design-vue'],
          chart: ['echarts'],
          map: ['leaflet']
        }
      }
    },
    cacheDir: './node_modules/.vite-cache'
  },
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'axios', 'leaflet', 'echarts', 'ant-design-vue'],
    exclude: []
  }
})
