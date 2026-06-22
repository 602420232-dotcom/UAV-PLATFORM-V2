/**
 * 角色枚举和权限定义
 * 用于前端多角色权限系统的核心配置
 */

/** 用户角色枚举 */
export enum UserRole {
  /** 超级管理员 - 拥有所有权限 */
  SUPER_ADMIN = 'SUPER_ADMIN',
  /** 租户管理员 - 管理租户内的用户和资源 */
  TENANT_ADMIN = 'TENANT_ADMIN',
  /** 操作员 - 可执行业务操作 */
  OPERATOR = 'OPERATOR',
  /** 观察员 - 只读权限，仅可查看数据 */
  OBSERVER = 'OBSERVER',
  /** 算法管理员 - 管理算法和沙箱 */
  ALGORITHM_ADMIN = 'ALGORITHM_ADMIN',
}

/** 每个角色可访问的菜单名称列表 */
export const roleMenuMap: Record<UserRole, string[]> = {
  [UserRole.SUPER_ADMIN]: [
    'dashboard',
    // API 运营管理子菜单
    'api-ops-entry', 'api-ops-dashboard', 'api-keys-ops', 'tenants-ops', 'usage', 'health', 'alerts',
    // 科研平台子菜单
    'research-entry', 'research-sandbox', 'algorithm-lab', 'experiments', 'reports',
    // 业务服务
    'weather', 'planning', 'assimilation', 'risk', 'observation', 'utm',
    // 系统管理
    'tenants', 'api-keys', 'users', 'roles', 'database',
  ],
  [UserRole.TENANT_ADMIN]: [
    'dashboard',
    // API 运营管理子菜单
    'api-ops-entry', 'api-ops-dashboard', 'api-keys-ops', 'tenants-ops', 'usage', 'health', 'alerts',
    // 业务服务
    'weather', 'planning', 'assimilation', 'risk', 'observation', 'utm',
  ],
  [UserRole.OPERATOR]: [
    'dashboard',
    // 科研平台子菜单
    'research-entry', 'research-sandbox', 'algorithm-lab', 'experiments', 'reports',
    // 业务服务
    'weather', 'planning', 'assimilation', 'risk', 'observation', 'utm',
  ],
  [UserRole.OBSERVER]: [
    'dashboard',
    // 业务服务（只读）
    'weather', 'planning', 'assimilation', 'risk', 'observation', 'utm',
  ],
  [UserRole.ALGORITHM_ADMIN]: [
    'dashboard',
    // 科研平台子菜单
    'research-entry', 'research-sandbox', 'algorithm-lab', 'experiments', 'reports',
    'algorithms',
  ],
}

/** 权限级别枚举 */
export enum Permission {
  /** 读取权限 */
  READ = 'read',
  /** 写入权限 */
  WRITE = 'write',
  /** 删除权限 */
  DELETE = 'delete',
  /** 审批权限 */
  APPROVE = 'approve',
  /** 管理权限 */
  MANAGE = 'manage',
}

/** 每个角色拥有的权限列表 */
export const rolePermissionMap: Record<UserRole, string[]> = {
  [UserRole.SUPER_ADMIN]: [
    Permission.READ, Permission.WRITE, Permission.DELETE,
    Permission.APPROVE, Permission.MANAGE,
  ],
  [UserRole.TENANT_ADMIN]: [
    Permission.READ, Permission.WRITE, Permission.DELETE,
    Permission.APPROVE, Permission.MANAGE,
  ],
  [UserRole.OPERATOR]: [
    Permission.READ, Permission.WRITE,
  ],
  [UserRole.OBSERVER]: [
    Permission.READ,
  ],
  [UserRole.ALGORITHM_ADMIN]: [
    Permission.READ, Permission.WRITE, Permission.DELETE, Permission.MANAGE,
  ],
}

/** 角色中文显示名称 */
export const roleLabelMap: Record<UserRole, string> = {
  [UserRole.SUPER_ADMIN]: '超级管理员',
  [UserRole.TENANT_ADMIN]: '租户管理员',
  [UserRole.OPERATOR]: '操作员',
  [UserRole.OBSERVER]: '观察员',
  [UserRole.ALGORITHM_ADMIN]: '算法管理员',
}
