import axios from 'axios'
import { message } from 'ant-design-vue'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求计数器（用于生成唯一请求ID）
let requestCounter = 0

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加认证令牌
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // 添加请求ID用于追踪
    config.metadata = { 
      requestId: ++requestCounter,
      startTime: Date.now()
    }
    
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
  (error) => {
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
      // 服务器返回错误状态码
      const status = response.status
      errorMessage = response.data?.message || errorMap[status] || `服务器错误 (${status})`
      
      // 401 特殊处理：仅在真正有 token 且后端返回 401 时才触发
      if (status === 401 && localStorage.getItem('token')) {
        localStorage.removeItem('token')
        // 避免重复提示
        if (!window.location.pathname.includes('/login')) {
          message.error({
            content: '登录已过期，请重新登录',
            duration: 3,
            key: 'auth-expired'
          })
          // 延迟跳转，让用户看到提示
          setTimeout(() => {
            window.location.href = '/login'
          }, 1500)
        }
      } else if (status === 401) {
        // 没有 token 时的 401，静默处理（页面自行降级）
        console.warn(`[API] 需要认证: ${config?.url}，请登录或使用演示数据`)
        return Promise.reject(new Error('AUTH_REQUIRED'))
      }
    } else if (error.code === 'ECONNABORTED') {
      // 请求超时
      errorMessage = '请求超时，请检查网络连接'
    } else if (error.message === 'Network Error') {
      // 网络错误 - 后端未启动，静默处理
      console.warn('[API] 网络错误，后端服务可能未启动')
      return Promise.reject(new Error('BACKEND_UNAVAILABLE'))
    } else {
      // 其他错误
      errorMessage = error.message || '请求失败'
    }
    
    // 显示错误提示（避免重复）
    const messageKey = `api-error-${config?.metadata?.requestId || 'default'}`
    message.error({
      content: errorMessage,
      duration: 5,
      key: messageKey
    })
    
    // 记录错误日志
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
 * @param {Function} requestFn - 返回 Promise 的请求函数
 * @param {number} maxRetries - 最大重试次数
 * @param {number} delay - 重试延迟（毫秒）
 * @returns {Promise} 请求结果
 */
export async function apiWithRetry(requestFn, maxRetries = 3, delay = 1000) {
  let lastError
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn()
    } catch (error) {
      lastError = error
      
      // 不重试的情况
      if (error.message?.includes('登录已过期') || 
          error.message?.includes('没有访问权限')) {
        throw error
      }
      
      // 最后一次重试不再等待
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay * (i + 1)))
      }
    }
  }
  
  throw lastError
}

/**
 * 并发请求管理
 * @param {Array} requests - 请求数组
 * @param {number} concurrency - 并发数
 * @returns {Promise<Array>} 所有请求结果
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

/**
 * 取消请求控制器
 */
export class RequestCanceler {
  constructor() {
    this.pendingRequests = new Map()
  }
  
  /**
   * 添加请求
   */
  addRequest(config) {
    const controller = new AbortController()
    config.signal = controller.signal
    this.pendingRequests.set(config.metadata.requestId, controller)
    return controller
  }
  
  /**
   * 取消指定请求
   */
  cancel(requestId) {
    const controller = this.pendingRequests.get(requestId)
    if (controller) {
      controller.abort()
      this.pendingRequests.delete(requestId)
    }
  }
  
  /**
   * 取消所有请求
   */
  cancelAll() {
    this.pendingRequests.forEach(controller => controller.abort())
    this.pendingRequests.clear()
  }
}

export default api
