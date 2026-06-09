import axios from 'axios'
import idb, { STORE_NETCDF, STORE_TILES, STORE_OFFLINE } from '../utils/indexedDB'

// ============ 分层缓存系统（Cache Strategy）============
// 策略：
//   - STATIC_FOREVER：静态配置（API 配置、数据源元信息）——永不过期
//   - WEATHER_1H：气象数据（预报/热力图）——1 小时
//   - TASK_5MIN：任务与路径规划状态 ——5 分钟
//   - NO_CACHE：用户认证、敏感写操作 ——不缓存

export const CACHE_STRATEGIES = {
  STATIC_FOREVER: { ttl: Infinity, tag: 'static' },
  WEATHER_1H:     { ttl: 60 * 60 * 1000, tag: 'weather' },
  TASK_5MIN:      { ttl: 5 * 60 * 1000, tag: 'task' },
  NO_CACHE:       { ttl: 0, tag: 'none' }
}

// URL 前缀 → 缓存策略映射（拦截器自动命中）
export const CACHE_RULES = [
  { pattern: /^\/?api\/v1\/(data-sources|api-config|config)\b/, strategy: 'STATIC_FOREVER', method: 'GET' },
  { pattern: /^\/?api\/v1\/weather\b/,                         strategy: 'WEATHER_1H',    method: 'GET' },
  { pattern: /^\/?api\/v1\/(tasks|planning|assimilation)\b/,   strategy: 'TASK_5MIN',     method: 'GET' }
]

// 大文件 / 二进制 → IndexedDB 路由：netcdf / tiles / offline-package
// key 前缀 → store 名 + ttl
const LARGE_ROUTES = [
  { tag: 'weather',      pattern: /\.(nc|nc4|grb|grib2?)(\?|$)|netcdf|weather\/(tiles|data)/i,   store: STORE_NETCDF,  ttl: 24 * 60 * 60 * 1000 },
  { tag: 'task',         pattern: /tasks\/.+\/offline|offline-package|/i,                          store: STORE_OFFLINE, ttl: 7 * 24 * 60 * 60 * 1000 },
  { tag: 'static',       pattern: /tile[s]?\/|\/cesium\/|openstreetmap|mapbox|tile/i,              store: STORE_TILES,   ttl: 30 * 24 * 60 * 60 * 1000 }
]

function matchLargeRoute(url) {
  if (!url) return null
  for (const r of LARGE_ROUTES) {
    if (r.pattern.test(url)) return r
  }
  return null
}

const CACHE_KEY_PREFIX = 'uav_cache:'
const MAX_CACHE_ITEMS = 200
const LARGE_KEY_PREFIX = 'large:'

export function cacheKey(config) {
  const qs = typeof config.params === 'object' && config.params
    ? JSON.stringify(config.params)
    : ''
  return `${CACHE_KEY_PREFIX}${config.method || 'get'}:${config.url}${qs ? '?' + qs : ''}`
}

function largeKey(config) {
  const url = (config && config.url) || ''
  return `${LARGE_KEY_PREFIX}${url}`
}

export function matchStrategy(config) {
  if (!config || (config.method && config.method.toLowerCase() !== 'get')) return null
  const url = (config.url || '').replace(/^\/api\//, '/api/')
  for (const rule of CACHE_RULES) {
    if (rule.pattern.test(url)) return rule.strategy
  }
  return null
}

// ============ localStorage 小文件缓存（保持不变） ============
export const cacheStore = {
  getAll() {
    try {
      const out = {}
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i)
        if (k && k.startsWith(CACHE_KEY_PREFIX)) {
          const raw = localStorage.getItem(k)
          try { out[k] = JSON.parse(raw) } catch (_) {}
        }
      }
      return out
    } catch (e) { return {} }
  },
  clearByTag(tag) {
    try {
      const keys = []
      for (let i = 0; i < localStorage.length; i++) {
        const k = localStorage.key(i)
        if (k && k.startsWith(CACHE_KEY_PREFIX)) keys.push(k)
      }
      keys.forEach((k) => {
        if (!tag) return localStorage.removeItem(k)
        try {
          const v = JSON.parse(localStorage.getItem(k))
          if (v && v.tag === tag) localStorage.removeItem(k)
        } catch (_) {}
      })
    } catch (e) {}
  },
  clearAll() { this.clearByTag(null) },

  // ======== 新增：IndexedDB 大文件缓存 ========
  async getLarge(key) {
    try {
      if (!idb.isAvailable()) return null
      // 优先根据 URL 命中路由；若 key 本身就是 URL，也尝试识别
      const route = matchLargeRoute(key)
      if (!route) return null
      const rec = await idb.get(route.store, key)
      if (!rec || !rec.blob) return null
      if (rec.expireAt && rec.expireAt !== Infinity && rec.expireAt < Date.now()) {
        try { idb.del(route.store, key).catch(() => {}) } catch (_) {}
        return null
      }
      return rec
    } catch (e) {
      return null
    }
  },
  async putLarge(key, blob, ttlMs) {
    try {
      if (!idb.isAvailable()) return false
      const route = matchLargeRoute(key) || { store: STORE_NETCDF, ttl: ttlMs || 7 * 24 * 60 * 60 * 1000 }
      const store = route.store
      const ttl = ttlMs || route.ttl || 7 * 24 * 60 * 60 * 1000
      const value = {
        blob: blob instanceof Blob ? blob : new Blob([blob], { type: 'application/octet-stream' }),
        contentType: (blob && blob.type) || 'application/octet-stream',
        expireAt: Date.now() + ttl,
        fetchedAt: Date.now()
      }
      await idb.put(store, key, value)
      return true
    } catch (e) {
      return false
    }
  },
  async invalidateLarge(tag) {
    try {
      if (!idb.isAvailable()) return
      const map = { weather: STORE_NETCDF, task: STORE_OFFLINE, static: STORE_TILES }
      if (!tag) {
        await idb.clearAll().catch(() => {})
        return
      }
      const store = map[tag]
      if (store) await idb.clear(store).catch(() => {})
    } catch (_) {}
  }
}

function readCache(key) {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return null
    const data = JSON.parse(raw)
    if (!data || !data.expireAt) return null
    if (data.expireAt !== Infinity && Date.now() > data.expireAt) {
      localStorage.removeItem(key)
      return null
    }
    return data.payload
  } catch (e) { return null }
}

function writeCache(key, payload, strategyName) {
  try {
    const strat = CACHE_STRATEGIES[strategyName] || CACHE_STRATEGIES.NO_CACHE
    if (strat.ttl <= 0) return
    const expireAt = strat.ttl === Infinity ? Infinity : Date.now() + strat.ttl
    const blob = { payload, expireAt, tag: strat.tag, createdAt: Date.now() }
    if (localStorage.length >= MAX_CACHE_ITEMS) {
      const oldestKey = localStorage.key(0)
      if (oldestKey && oldestKey.startsWith(CACHE_KEY_PREFIX)) localStorage.removeItem(oldestKey)
    }
    localStorage.setItem(key, JSON.stringify(blob))
  } catch (e) {
    try { localStorage.removeItem(key) } catch (_) {}
  }
}

// 联合清理（localStorage + IndexedDB）
export function invalidateWeather() {
  cacheStore.clearByTag('weather')
  cacheStore.invalidateLarge('weather').catch(() => {})
}
export function invalidateTask() {
  cacheStore.clearByTag('task')
  cacheStore.invalidateLarge('task').catch(() => {})
}
export function invalidateStatic() {
  cacheStore.clearByTag('static')
  cacheStore.invalidateLarge('static').catch(() => {})
}
export function invalidateAllCache() {
  cacheStore.clearAll()
  cacheStore.invalidateLarge(null).catch(() => {})
}

// ============= 请求/响应拦截器 =============
// Token 刷新状态（保留原逻辑）
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) prom.reject(error)
    else prom.resolve(token)
  })
  failedQueue = []
}

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true
})

// 请求计数器（用于生成唯一请求 ID）
let requestCounter = 0

// 错误分类（与 errorHandler.js 保持一致的轻量副本，避免循环依赖）
function classifyError(err) {
  if (!err || typeof err !== 'object') return 'UNKNOWN'
  if (
    err.code === 'ECONNABORTED' ||
    (typeof err.message === 'string' && /timeout/i.test(err.message))
  ) return 'TIMEOUT'
  if (err.message === 'Network Error' || err.code === 'NETWORK_ERROR') return 'NETWORK_ERROR'
  if (!err.response) return 'NETWORK_ERROR'
  const status = err.response.status
  if (status === 401) return 'UNAUTHORIZED'
  if (status === 403) return 'FORBIDDEN'
  if (status === 404) return 'NOT_FOUND'
  if (status === 429) return 'TOO_MANY_REQUESTS'
  if (status >= 400 && status < 500) return 'CLIENT_ERROR'
  if (status >= 500 && status < 600) return 'SERVER_ERROR'
  return 'UNKNOWN'
}

// 指数退避：1s / 2s / 4s
function backoffDelay(retryCount) {
  return Math.pow(2, retryCount) * 1000
}

// 判断请求是否属于"大文件 / 二进制"（netcdf / tiles / offline-package）
function _isLargeBinaryRequest(config) {
  if (!config) return false
  const url = config.url || ''
  const accept = (config.headers && (config.headers.Accept || config.headers.accept)) || ''
  const rt = (config.responseType || '').toLowerCase()
  if (rt === 'blob' || rt === 'arraybuffer') return true
  if (/netcdf|tiles?|offline-package|\.(nc|nc4|grb|grib2?)(\?|$)/i.test(url)) return true
  if (/application\/octet|image\/|application\/x-netcdf/i.test(accept)) return true
  return false
}

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    config.metadata = {
      requestId: ++requestCounter,
      startTime: Date.now()
    }

    // 1) 命中 localStorage 小文件缓存策略且为 GET → 先读本地缓存
    const strategy = matchStrategy(config)
    if (strategy) {
      const key = cacheKey(config)
      const cached = readCache(key)
      if (cached !== null) {
        return {
          ...config,
          __uav_cached__: true,
          adapter: () => Promise.resolve({
            data: cached,
            status: 200,
            statusText: 'OK (from-cache)',
            headers: { 'x-cache': 'HIT' },
            config
          })
        }
      }
    }

    // 2) 大文件 / 二进制 → 查 IndexedDB，命中直接伪造 Blob 返回
    if (config.method && config.method.toLowerCase() === 'get' && _isLargeBinaryRequest(config)) {
      const lkey = largeKey(config)
      return cacheStore.getLarge(lkey).then((rec) => {
        if (rec && rec.blob) {
          return {
            ...config,
            __uav_cached__: true,
            __uav_large_hit__: true,
            adapter: () => Promise.resolve({
              data: rec.blob,
              status: 200,
              statusText: 'OK (from-indexeddb)',
              headers: { 'x-cache': 'HIT-IDB', 'content-type': rec.contentType || 'application/octet-stream' },
              config
            })
          }
        }
        // 未命中 → 给 config 打标，后续响应时写回 IndexedDB
        config.__uav_large_pending__ = lkey
        return config
      }).catch(() => config)
    }

    return config
  },
  (error) => {
    // 请求发送阶段错误（例如配置不合法）
    import('../utils/errorHandler')
      .then(m => m.handleApiError(error))
      .catch(() => {
        console.error('[API] 请求发送失败', error)
      })
    return Promise.reject(error)
  }
)

// 响应拦截器（含重试 + 分级提示 + 保留 token refresh 逻辑）
api.interceptors.response.use(
  (response) => {
    const duration = Date.now() - response.config.metadata.startTime
    if (duration > 5000) {
      console.warn(`[API] 慢请求警告: ${response.config.url} 耗时 ${duration}ms`)
    }

    // 写入大文件缓存（IndexedDB）：命中 pending 标记且 data 是 Blob 或二进制
    if (!response.config?.__uav_cached__ && response.config?.__uav_large_pending__) {
      const lkey = response.config.__uav_large_pending__
      const data = response.data
      if (data instanceof Blob) {
        cacheStore.putLarge(lkey, data).catch(() => {})
      } else if (data instanceof ArrayBuffer) {
        cacheStore.putLarge(lkey, new Blob([data], { type: 'application/octet-stream' })).catch(() => {})
      }
    }

    // 写入缓存（仅限 GET + 命中策略且状态码正常）
    if (!response.config?.__uav_cached__ && response.config?.method?.toLowerCase() === 'get') {
      const strategy = matchStrategy(response.config)
      if (strategy) writeCache(cacheKey(response.config), response.data, strategy)
    }
    return response.data
  },
  async (error) => {
    const { response, config } = error

    // 判断是否为后端未连接（Vite dev server 返回 HTML 404 页面）
    const isBackendDown = (
      response && response.status === 404 && typeof response.data === 'string' &&
      (response.data.includes('<!DOCTYPE') || response.data.includes('<html'))
    ) || (
      response && response.status === 404 && config?.url?.startsWith('/v1/')
    )

    if (isBackendDown) {
      console.warn(`[API] 后端服务未连接: ${config?.url}`)
      return Promise.reject(new Error('BACKEND_UNAVAILABLE'))
    }

    const kind = classifyError(error)
    const status = response ? response.status : null

    // ---- 401 / token 过期：保留原有的 refresh 逻辑 ----
    if (
      kind === 'UNAUTHORIZED' ||
      (response && (response.data && (response.data.__token_expired__ || response.data.code === 'TOKEN_EXPIRED')))
    ) {
      if (!config._retry && !config.url?.includes('/auth/refresh')) {
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject })
          }).then(() => api(config)).catch(err => Promise.reject(err))
        }
        config._retry = true
        isRefreshing = true
        try {
          const authMod = await import('../stores/auth')
          const authStore = authMod.useAuthStore()
          await authStore.refreshToken()
          processQueue(null)
          return api(config)
        } catch (refreshError) {
          processQueue(refreshError, null)
          try {
            const authMod2 = await import('../stores/auth')
            const authStore2 = authMod2.useAuthStore()
            authStore2.logout && authStore2.logout()
          } catch (e) {}
          localStorage.removeItem('user')
          if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
            try {
              const elMsg = (await import('element-plus')).ElMessage
              elMsg && elMsg.error({
                message: '登录已过期，请重新登录',
                duration: 3000,
                key: 'auth-expired'
              })
            } catch (_) {}
            setTimeout(() => { window.location.href = '/login' }, 1500)
          }
          return Promise.reject(refreshError)
        } finally {
          isRefreshing = false
        }
      } else if (config._retry) {
        // 已重试过 → 直接跳登录
        localStorage.removeItem('user')
        if (typeof window !== 'undefined' && !window.location.pathname.includes('/login')) {
          try {
            import('element-plus').then(m => m.ElMessage && m.ElMessage.error({
              message: '登录已过期，请重新登录', duration: 3000, key: 'auth-expired'
            }))
          } catch (_) {}
          setTimeout(() => { window.location.href = '/login' }, 1500)
        }
        return Promise.reject(error)
      } else {
        // 没有 token 时的 401：静默降级
        console.warn(`[API] 需要认证: ${config?.url}，请登录或使用演示数据`)
        return Promise.reject(new Error('AUTH_REQUIRED'))
      }
    }

    // ---- 自动重试：超时 (>=10s) 或 5xx，最多 3 次，指数退避 1s/2s/4s ----
    const retryable = (kind === 'TIMEOUT' && (config?.timeout || 0) >= 10000) || kind === 'SERVER_ERROR'
    config.__retryCount = config.__retryCount || 0
    if (retryable && config.__retryCount < 3) {
      config.__retryCount += 1
      const delay = backoffDelay(config.__retryCount - 1)
      console.warn(`[API] 自动重试 #${config.__retryCount} ${config.method} ${config.url}（${kind}，延迟 ${delay}ms）`)
      await new Promise(resolve => setTimeout(resolve, delay))
      return api(config)
    }

    // ---- 统一错误提示 + 日志 ----
    try {
      const mod = await import('../utils/errorHandler')
      mod.handleApiError(error)
    } catch (e) {
      // 降级：直接 console + element-plus ElMessage
      console.error('[API Error fallback]', error)
      try {
        const { ElMessage } = await import('element-plus')
        if (ElMessage) ElMessage.error({ message: '请求失败，请稍后再试', duration: 3000 })
      } catch (_) {}
    }

    // 以带状态码的 Error reject，方便上游判断
    const msg =
      (response && response.data && (response.data.message || response.data.error)) ||
      (error && error.message) ||
      `请求失败 (${status || '-'})`
    const finalErr = new Error(msg)
    finalErr.status = status
    finalErr.kind = kind
    finalErr.url = config && config.url
    return Promise.reject(finalErr)
  }
)

// ============ 带重试机制的请求方法（兼容旧调用）============
export async function apiWithRetry(requestFn, maxRetries = 3, delayMs = 1000) {
  let lastError
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn()
    } catch (error) {
      lastError = error
      if (
        (error && error.message && error.message.includes('登录已过期')) ||
        (error && error.message && error.message.includes('没有访问权限'))
      ) {
        throw error
      }
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delayMs * (i + 1)))
      }
    }
  }
  throw lastError
}

// ============ 并发请求管理 ============
export async function apiBatch(requests, concurrency = 3) {
  const results = []
  const queue = [...requests]
  async function processQueue() {
    while (queue.length > 0) {
      const request = queue.shift()
      try {
        const result = await request()
        results.push({ success: true, data: result })
      } catch (error) {
        results.push({ success: false, error: error.message })
      }
    }
  }
  const workers = Array(Math.min(concurrency, requests.length))
    .fill(null)
    .map(() => processQueue())
  await Promise.all(workers)
  return results
}

export class RequestCanceler {
  constructor() { this.pendingRequests = new Map() }
  addRequest(config) {
    const controller = new AbortController()
    config.signal = controller.signal
    this.pendingRequests.set(config.metadata.requestId, controller)
    return controller
  }
  cancel(requestId) {
    const controller = this.pendingRequests.get(requestId)
    if (controller) {
      controller.abort()
      this.pendingRequests.delete(requestId)
    }
  }
  cancelAll() {
    this.pendingRequests.forEach(c => c.abort())
    this.pendingRequests.clear()
  }
}

export { api }
export default api
