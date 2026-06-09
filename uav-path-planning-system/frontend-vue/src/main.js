import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'
import './styles/theme-vars.css'
import './styles/index.css'

const savedTheme = localStorage.getItem('uav_theme_v1') || 'light'
document.documentElement.setAttribute('data-theme', savedTheme)
if (savedTheme === 'custom') {
  try {
    const vars = JSON.parse(localStorage.getItem('uav_theme_custom_vars_v1') || '{}')
    Object.entries(vars).forEach(([k, v]) => document.documentElement.style.setProperty(k, v))
  } catch (_) {}
}
import { setElMessage, handleGenericError } from './utils/errorHandler'
import i18n from './locales'
import { setupMock } from './mock'
import idb from './utils/indexedDB'

// 仅在 DEV 环境启用前端 Mock 服务（拦截 /mock-api/* 返回本地 JSON）
// 生产环境 setupMock 内部直接短路返回，不会注册任何拦截器
if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.DEV) {
  setupMock()
}

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.use(i18n)

// 从 Element Plus 取到 ElMessage 后注入到 errorHandler，
// 使 API 拦截器与全局错误处理器共用同一份提示组件
setElMessage(ElementPlus.ElMessage || (typeof ElMessage !== 'undefined' ? ElMessage : null))

// ===== 全局 Vue 错误处理：捕获组件渲染 / 生命周期 / 事件处理异常 =====
app.config.errorHandler = (err, instance, info) => {
  const componentName =
    (instance && instance.$options && instance.$options.name) ||
    (instance && instance.type && instance.type.name) ||
    'UnknownComponent'
  console.error('[Global Error]', {
    message: err && err.message,
    component: componentName,
    info
  }, err)
  handleGenericError(err, { context: `vue:${componentName}:${info || 'render'}` })
}

// ===== 全局未捕获 Promise 错误（浏览器级）=====
if (typeof window !== 'undefined') {
  window.addEventListener('unhandledrejection', (event) => {
    const reason = event && (event.reason || event.detail && event.detail.reason)
    console.warn('[UnhandledRejection]', reason)
    handleGenericError(reason, { context: 'unhandled-promise' })
  })
  window.addEventListener('error', (event) => {
    // 资源加载错误等
    const err = event && event.error
    if (err) {
      console.error('[Window Error]', err)
      handleGenericError(err, { context: 'window-error' })
    }
  })
}

app.mount('#app')

// 全局 t() 函数，方便在浏览器控制台调试（i18n）
window.$t = (key, params) => {
  try { return i18n.global.t(key, params) } catch (e) { return key }
}
window.setLocale = (locale) => {
  i18n.global.locale.value = locale
  localStorage.setItem('locale', locale)
  console.info('[i18n] 语言切换为：', locale)
}

// ============ IndexedDB 初始化（离线缓存底座） ============
if (idb && idb.isAvailable && typeof idb.initDB === 'function') {
  idb.initDB()
    .then(() => {
      if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.DEV) {
        console.info('[main] IndexedDB 已初始化')
      }
      if (idb.getStorageInfo) {
        return idb.getStorageInfo().then((info) => {
          if (info && typeof info.quota === 'number') {
            console.info('[main] 存储配额', {
              quota: (info.quota / 1024 / 1024).toFixed(2) + ' MB',
              usage: (info.usage / 1024 / 1024).toFixed(2) + ' MB',
              usagePercent: info.usagePercent + '%'
            })
          }
        })
      }
    })
    .catch((err) => {
      console.warn('[main] IndexedDB 不可用，降级为纯内存 + localStorage 缓存', err && err.message)
    })
}

// ============ Service Worker 注册（PWA 离线能力） ============
// 双策略：
//   A. 如已安装 vite-plugin-pwa，会在 dist 生成 /sw.js，优先注册
//   B. 若未安装，则注册 /service-worker.js（手写版，提供基础离线能力）
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    const preferredSW = import.meta.env.DEV
      ? '/service-worker.js'
      : '/sw.js'

    const tryRegister = (url, fallbackUrl) => {
      navigator.serviceWorker
        .register(url)
        .then((reg) => {
          if (reg.installing) {
            console.info('[PWA] 新 Service Worker 安装中：', url)
          } else if (reg.waiting) {
            console.info('[PWA] 有新版本待激活：', url)
          } else if (reg.active) {
            console.info('[PWA] Service Worker 已激活：', url)
          }
        })
        .catch((err) => {
          console.warn('[PWA] 注册失败，尝试降级方案：', url, err)
          if (fallbackUrl && fallbackUrl !== url) {
            navigator.serviceWorker.register(fallbackUrl).catch((e) => {
              console.warn('[PWA] 降级方案也失败（不影响主功能）：', e)
            })
          }
        })
    }

    tryRegister(preferredSW, '/service-worker.js')
  })

  // 网络状态变化：友好提示（不阻塞 UI）
  let offlineToastShown = false
  window.addEventListener('online', () => {
    offlineToastShown = false
    try {
      const ElMessage = ElementPlus && ElementPlus.ElMessage
      if (typeof ElMessage === 'function') ElMessage({ type: 'success', message: '网络已恢复', duration: 2000 })
      else console.info('[PWA] 网络已恢复')
    } catch (_) {}
  })
  window.addEventListener('offline', () => {
    if (offlineToastShown) return
    offlineToastShown = true
    try {
      const ElMessage = ElementPlus && ElementPlus.ElMessage
      if (typeof ElMessage === 'function') ElMessage({ type: 'warning', message: '已离线 - 使用本地缓存数据', duration: 3000 })
      else console.warn('[PWA] 已离线，使用本地缓存数据')
    } catch (_) {}
  })
}
