import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, removeToken, getUserInfo } from '@/utils/auth'
import router from '@/router'
import { useDemoModeStore } from '@/stores/demoMode'

/** 后端统一响应结构 Result<T> */
export interface Result<T = unknown> {
  code: number
  message: string
  data: T
  requestId: string
  timestamp: number
}

/** 分页结构 */
export interface PageResult<T> {
  records: T[]
  total: number
  size: number
  current: number
  pages: number
}

/**
 * HMAC-SHA256 签名工具
 * 用于 API Gateway 的请求认证
 */
async function hmacSha256(key: string, message: string): Promise<string> {
  const encoder = new TextEncoder()
  const keyData = encoder.encode(key)
  const msgData = encoder.encode(message)
  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    keyData,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  )
  const signature = await crypto.subtle.sign('HMAC', cryptoKey, msgData)
  return Array.from(new Uint8Array(signature))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

/**
 * 生成 HMAC 签名头
 * 签名内容: timestamp + method + path + (body hash)
 */
async function generateHmacHeaders(
  method: string,
  url: string,
  data?: unknown
): Promise<Record<string, string>> {
  const timestamp = Math.floor(Date.now() / 1000).toString()
  const userInfo = getUserInfo()
  const apiKeySecret = userInfo?.apiKeySecret || ''

  if (!apiKeySecret) {
    return { 'X-Timestamp': timestamp }
  }

  // 计算请求体 SHA-256 哈希
  let bodyHash = ''
  if (data && method !== 'GET') {
    const bodyStr = typeof data === 'string' ? data : JSON.stringify(data)
    const encoder = new TextEncoder()
    const hashBuffer = await crypto.subtle.digest('SHA-256', encoder.encode(bodyStr))
    bodyHash = Array.from(new Uint8Array(hashBuffer))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('')
  }

  // 签名原文: timestamp + method + url path + bodyHash
  const urlObj = new URL(url, 'http://localhost')
  const path = urlObj.pathname + urlObj.search
  const signContent = `${timestamp}${method.toUpperCase()}${path}${bodyHash}`
  const signature = await hmacSha256(apiKeySecret, signContent)

  const headers: Record<string, string> = {
    'X-Timestamp': timestamp,
    'X-Signature': signature,
    'X-Signature-Method': 'HMAC-SHA256',
  }
  if (bodyHash) {
    headers['X-Body-Hash'] = bodyHash
  }
  return headers
}

const service: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/** 不需要登录即可访问的公开接口 */
const PUBLIC_PATHS = [
  '/v1/auth/',
  '/v1/dashboard/global',
  '/v1/dashboard/api-ops',
  '/v1/dashboard/research',
  '/v1/system/config/demo-mode',
]

function isPublicPath(url: string): boolean {
  return PUBLIC_PATHS.some(path => url.includes(path))
}

// 请求拦截器
service.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // 添加 API 版本 Header
    config.headers['X-API-Version'] = '1.0'

    // 添加 Token
    const token = getToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }

    // 未登录且非公开接口
    const url = config.url || ''
    if (!token && !isPublicPath(url)) {
      return Promise.reject(new Error('UNAUTHORIZED_SKIP'))
    }

    // 附加 HMAC 签名（如果用户有 API Key Secret）
    const method = (config.method || 'GET').toUpperCase()
    const fullUrl = (config.baseURL || '') + url
    const hmacHeaders = await generateHmacHeaders(method, fullUrl, config.data)
    Object.entries(hmacHeaders).forEach(([key, value]) => {
      if (value !== undefined) {
        config.headers[key] = value
      }
    })

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：解包 Result<T>
service.interceptors.response.use(
  (response: AxiosResponse<Result>) => {
    const res = response.data

    // 业务成功，直接返回 data
    if (res.code === 0 || res.code === 200) {
      return res.data as unknown as AxiosResponse
    }

    // 业务错误
    ElMessage.error(res.message || '请求失败')
    return Promise.reject(new Error(res.message || '请求失败'))
  },
  (error) => {
    // 静默跳过未登录时的非公开接口请求（避免 403 弹窗轰炸）
    if (error.message === 'UNAUTHORIZED_SKIP') {
      return Promise.reject(error)
    }

    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        removeToken()
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
      } else if (status === 403) {
        // 演示模式下静默处理 403，不弹窗
        try {
          const demoModeStore = useDemoModeStore()
          if (demoModeStore.isDemoMode) {
            return Promise.reject(error)
          }
        } catch { /* ignore */ }
        ElMessage.error('没有权限执行此操作')
      } else if (status === 404) {
        ElMessage.error('请求的资源不存在')
      } else if (status === 429) {
        ElMessage.error('请求过于频繁，请稍后重试')
      } else if (status >= 500) {
        ElMessage.error(`服务器内部错误 (${data?.requestId || ''})`)
      } else {
        ElMessage.error(data?.message || '请求失败')
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请检查网络连接')
    } else {
      ElMessage.error('网络连接异常')
    }
    return Promise.reject(error)
  }
)

/** 封装请求方法 */
export function request<T = unknown>(config: AxiosRequestConfig): Promise<T> {
  return service(config) as unknown as Promise<T>
}

export function get<T = unknown>(url: string, params?: Record<string, unknown>): Promise<T> {
  return request<T>({ method: 'GET', url, params })
}

export function post<T = unknown>(url: string, data?: unknown): Promise<T> {
  return request<T>({ method: 'POST', url, data })
}

export function put<T = unknown>(url: string, data?: unknown): Promise<T> {
  return request<T>({ method: 'PUT', url, data })
}

export function del<T = unknown>(url: string): Promise<T> {
  return request<T>({ method: 'DELETE', url })
}

export default service
