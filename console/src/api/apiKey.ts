import { get, post, del } from './request'

export interface ApiKey {
  id: number
  tenantId: number
  keyValue: string
  secret: string
  name: string
  status: number
  rateLimit: number | null
  createdAt: string
  expiresAt: string | null
}

export interface GenerateApiKeyRequest {
  tenantId: number
  name: string
  rateLimit?: number
  expiresInDays?: number
}

export const apiKeyApi = {
  /** 生成 API Key */
  generate(data: GenerateApiKeyRequest): Promise<ApiKey> {
    return post<ApiKey>('/v1/api-keys', data)
  },

  /** 获取 API Key 详情 */
  getById(id: number): Promise<ApiKey> {
    return get<ApiKey>(`/v1/api-keys/${id}`)
  },

  /** 按租户获取 API Key 列表 */
  listByTenant(tenantId: number): Promise<ApiKey[]> {
    return get<ApiKey[]>(`/v1/api-keys/tenant/${tenantId}`)
  },

  /** 启用 API Key */
  enable(id: number): Promise<void> {
    return post<void>(`/v1/api-keys/${id}/enable`)
  },

  /** 禁用 API Key */
  disable(id: number): Promise<void> {
    return post<void>(`/v1/api-keys/${id}/disable`)
  },

  /** 删除 API Key */
  remove(id: number): Promise<void> {
    return del<void>(`/v1/api-keys/${id}`)
  },
}
