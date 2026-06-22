import { get, post, put, del } from './request'
import type { PageResult } from './request'

export interface User {
  id: number
  username: string
  realName?: string
  email?: string
  phone?: string
  status: number
  role: string
  roleName?: string
  tenantId?: number
  tenantName?: string
  createdAt: string
  lastLoginAt?: string
}

export interface Role {
  id: number
  code: string
  name: string
  description?: string
  permissions: string[]
  userCount?: number
}

export interface Permission {
  id: number
  code: string
  name: string
  resourceType: string
  description?: string
}

export interface UserListParams {
  current?: number
  size?: number
  keyword?: string
  role?: string
  status?: number
}

/** 用户管理 API */
export const userApi = {
  /** 获取用户列表（分页） */
  list(params: UserListParams = {}): Promise<PageResult<User>> {
    return get<PageResult<User>>('/v1/users', params as Record<string, unknown>)
  },

  /** 获取用户详情 */
  getById(id: number): Promise<User> {
    return get<User>(`/v1/users/${id}`)
  },

  /** 创建用户 */
  create(data: Partial<User> & { password: string }): Promise<User> {
    return post<User>('/v1/users', data)
  },

  /** 更新用户 */
  update(id: number, data: Partial<User>): Promise<void> {
    return put<void>(`/v1/users/${id}`, data)
  },

  /** 删除用户 */
  remove(id: number): Promise<void> {
    return del<void>(`/v1/users/${id}`)
  },

  /** 重置用户密码 */
  resetPassword(id: number, data: { newPassword: string }): Promise<void> {
    return post<void>(`/v1/users/${id}/reset-password`, data)
  },

  /** 分配用户角色 */
  assignRole(id: number, data: { roleCode: string }): Promise<void> {
    return post<void>(`/v1/users/${id}/assign-role`, data)
  },
}

/** 角色管理 API */
export const roleApi = {
  /** 获取角色列表 */
  list(): Promise<Role[]> {
    return get<Role[]>('/v1/roles')
  },

  /** 获取角色详情 */
  getById(id: number): Promise<Role> {
    return get<Role>(`/v1/roles/${id}`)
  },

  /** 创建角色 */
  create(data: Partial<Role>): Promise<Role> {
    return post<Role>('/v1/roles', data)
  },

  /** 更新角色 */
  update(id: number, data: Partial<Role>): Promise<void> {
    return put<void>(`/v1/roles/${id}`, data)
  },

  /** 删除角色 */
  remove(id: number): Promise<void> {
    return del<void>(`/v1/roles/${id}`)
  },
}

/** 权限管理 API */
export const permissionApi = {
  /** 获取权限列表 */
  list(): Promise<Permission[]> {
    return get<Permission[]>('/v1/permissions')
  },
}
