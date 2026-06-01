import axios from 'axios'
import { message } from 'ant-design-vue'

// Token 刷新状态
let isRefreshing = false
let failedQueue = []

// 处理队列中的请求
const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true // 允许携带 cookies
})

// 请求计数器（用于生成唯一请求ID）
let requestCounter = 0

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加请求ID用于追踪
    config.metadata = { 
      requestId: ++requestCounter,
      startTime: Date.now()
    }
    
    // 为每个请求创建 AbortController
    const controller = new AbortController()
    config.signal = controller.signal
    config.metadata.controller = controller
    
    return config
  },
  (error) => {
    message.error('请求发送失败')
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 记录请求耗时
    const duration = Date.now() - response.config.metadata.startTime
    if (duration > 5000) {
      console.warn(`[API] 慢请求警告: ${response.config.url} 耗时 ${duration}ms`)
    }
    
    return response.data
  },
  async (error) => {
    const { response, config } = error
    
    // 判断是否为后端未连接（Vite dev server 返回 HTML 404 页面）
    const isBackendDown = response && (
      response.status === 404 && typeof response.data === 'string' &&
      (response.data.includes('<!DOCTYPE') || response.data.includes('<html'))
    ) || (
      response && response.status === 404 &&
      config?.url?.startsWith('/v1/')
    )
    
    // 后端未连接时静默处理，让各页面自行降级到演示数据
    if (isBackendDown) {
      console.warn(`[API] 后端服务未连接: ${config?.url}`)
      return Promise.reject(new Error('BACKEND_UNAVAILABLE'))
    }
    
    // 错误分类映射
    const errorMap = {
      400: '请求参数错误',
      401: '登录已过期，请重新登录',
      403: '没有访问权限',
      404: '请求的资源不存在',
      408: '请求超时',
      409: '资源冲突',
      422: '参数验证失败',
      429: '请求过于频繁，请稍后重试',
      500: '服务器内部错误',
      502: '网关错误',
      503: '服务暂时不可用',
      504: '网关超时'
    }
    
    // 构建错误消息
    let errorMessage
    if (response) {
      const status = response.status
      errorMessage = response.data?.message || errorMap[status] || `服务器错误 (${status})`
      
      // 401 特殊处理
      if (status === 401) {
        // 如果不是刷新 token 请求，尝试刷新
        if (!config._retry && !config.url?.includes('/auth/refresh')) {
          if (isRefreshing) {
            // 如果正在刷新，将请求加入队列
            return new Promise((resolve, reject) => {
              failedQueue.push({ resolve, reject })
            }).then(token => {
              // 刷新成功后重新请求
              return api(config)
            }).catch(err => {
              return Promise.reject(err)
            })
          }
          
          config._retry = true
          isRefreshing = true
          
          try {
            // 尝试刷新 token
            await api.post('/v1/auth/refresh')
            processQueue(null)
            // 刷新成功后重新请求
            return api(config)
          } catch (refreshError) {
            // 刷新失败，清除状态并跳转登录
            processQueue(refreshError, null)
            localStorage.removeItem('user')
            if (!window.location.pathname.includes('/login')) {
              message.error({
                content: '登录已过期，请重新登录',
                duration: 3,
                key: 'auth-expired'
              })
              setTimeout(() => {
                window.location.href = '/login'
              }, 1500)
            }
            return Promise.reject(refreshError)
          } finally {
            isRefreshing = false
          }
        } else if (config._retry) {
          // 已经重试过，直接跳转
          localStorage.removeItem('user')
          if (!window.location.pathname.includes('/login')) {
            message.error({
              content: '登录已过期，请重新登录',
              duration: 3,
              key: 'auth-expired'
            })
            setTimeout(() => {
              window.location.href = '/login'
            }, 1500)
          }
        } else {
          // 没有 token 时的 401，静默处理
          console.warn(`[API] 需要认证: ${config?.url}，请登录或使用演示数据`)
          return Promise.reject(new Error('AUTH_REQUIRED'))
        }
      }
    } else if (error.code === 'ECONNABORTED') {
      errorMessage = '请求超时，请检查网络连接'
    } else if (error.message === 'Network Error') {
      console.warn('[API] 网络错误，后端服务可能未启动')
      return Promise.reject(new Error('BACKEND_UNAVAILABLE'))
    } else {
      errorMessage = error.message || '请求失败'
    }
    
    // 显示错误提示
    const messageKey = `api-error-${config?.metadata?.requestId || 'default'}`
    message.error({
      content: errorMessage,
      duration: 5,
      key: messageKey
    })
    
    console.error('[API Error]', {
      url: config?.url,
      method: config?.method,
      status: response?.status,
      message: errorMessage,
      requestId: config?.metadata?.requestId
    })
    
    return Promise.reject(new Error(errorMessage))
  }
)

/**
 * 带重试机制的请求方法
 */
export async function apiWithRetry(requestFn, maxRetries = 3, delay = 1000) {
  let lastError
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn()
    } catch (error) {
      lastError = error
      
      if (error.message?.includes('登录已过期') || 
          error.message?.includes('没有访问权限')) {
        throw error
      }
      
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay * (i + 1)))
      }
    }
  }
  
  throw lastError
}

/**
 * 并发请求管理
 */
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
  constructor() {
    this.pendingRequests = new Map()
  }
  
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
    this.pendingRequests.forEach(controller => controller.abort())
    this.pendingRequests.clear()
  }
}

export default api
