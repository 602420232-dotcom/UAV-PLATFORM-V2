import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { getToken, removeToken } from '@/utils/auth'
import router from '@/router'

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

const service: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 添加 API 版本 Header
    config.headers['X-API-Version'] = '1.0'

    // 添加 Token
    const token = getToken()
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }

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
    if (error.response) {
      const { status } = error.response
      if (status === 401) {
        removeToken()
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
      } else if (status === 403) {
        ElMessage.error('没有权限执行此操作')
      } else if (status === 404) {
        ElMessage.error('请求的资源不存在')
      } else if (status >= 500) {
        ElMessage.error('服务器内部错误')
      } else {
        ElMessage.error(error.response.data?.message || '请求失败')
      }
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
