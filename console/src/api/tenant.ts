import { get, post, put, del } from './request'
import type { PageResult } from './request'

export interface Tenant {
  id: number
  name: string
  schemaName: string
  status: number
  quotaConfig: string | null
  createdAt: string
  updatedAt: string
}

export interface CreateTenantRequest {
  name: string
  schemaName: string
  quotaConfig?: string
}

export interface UpdateTenantRequest {
  name?: string
  quotaConfig?: string
}

export const tenantApi = {
  /** 获取租户列表（分页） */
  list(current = 1, size = 10): Promise<PageResult<Tenant>> {
    return get<PageResult<Tenant>>('/v1/tenants', { current, size })
  },

  /** 获取租户详情 */
  getById(id: number): Promise<Tenant> {
    return get<Tenant>(`/v1/tenants/${id}`)
  },

  /** 创建租户 */
  create(data: CreateTenantRequest): Promise<Tenant> {
    return post<Tenant>('/v1/tenants', data)
  },

  /** 更新租户 */
  update(id: number, data: UpdateTenantRequest): Promise<void> {
    return put<void>(`/v1/tenants/${id}`, data)
  },

  /** 禁用租户 */
  disable(id: number): Promise<void> {
    return post<void>(`/v1/tenants/${id}/disable`)
  },

  /** 启用租户 */
  enable(id: number): Promise<void> {
    return post<void>(`/v1/tenants/${id}/enable`)
  },

  /** 删除租户 */
  remove(id: number): Promise<void> {
    return del<void>(`/v1/tenants/${id}`)
  },
}
