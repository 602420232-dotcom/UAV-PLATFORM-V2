import { post } from './request'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  token: string
  userId: number
  role: string
  tenantId?: number
  tenantName?: string
}

export interface RegisterRequest {
  username: string
  password: string
  email?: string
}

export const authApi = {
  /** 登录 */
  login(username: string, password: string): Promise<LoginResponse> {
    return post<LoginResponse>('/v1/platform/auth/login', { username, password })
  },

  /** 注册 */
  register(data: RegisterRequest): Promise<void> {
    return post<void>('/v1/platform/auth/register', data)
  },

  /** 刷新 Token */
  refreshToken(refreshToken: string): Promise<LoginResponse> {
    return post<LoginResponse>('/v1/platform/auth/refresh', { refreshToken })
  },
}
