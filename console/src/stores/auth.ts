import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import { getToken, setToken, removeToken, getUserInfo, setUserInfo, removeUserInfo } from '@/utils/auth'
import type { StoredUserInfo } from '@/utils/auth'
import { UserRole, roleMenuMap, rolePermissionMap } from '@/utils/roles'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(getToken() || '')
  const userInfo = ref<StoredUserInfo | null>(getUserInfo())

  const isAuthenticated = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username ?? '')
  const currentTenantId = computed(() => userInfo.value?.tenantId)
  const currentTenantName = computed(() => userInfo.value?.tenantName ?? '')

  /** 当前用户角色，默认为观察员（最低权限） */
  const currentRole = computed(() => userInfo.value?.role as UserRole ?? UserRole.OBSERVER)

  /** 登录 */
  async function login(username: string, password: string) {
    const data = await authApi.login(username, password)
    token.value = data.token
    setToken(data.token)
    // 登录后获取用户信息（可从 token 解析或调用接口）
    userInfo.value = {
      id: data.userId ?? 0,
      username,
      role: data.role ?? 'admin',
      tenantId: data.tenantId,
      tenantName: data.tenantName,
    }
    setUserInfo(userInfo.value)
  }

  /** 退出登录 */
  function logout() {
    token.value = ''
    userInfo.value = null
    removeToken()
    removeUserInfo()
  }

  /** 切换租户 */
  function switchTenant(tenantId: number, tenantName: string) {
    if (userInfo.value) {
      userInfo.value.tenantId = tenantId
      userInfo.value.tenantName = tenantName
      setUserInfo(userInfo.value)
    }
  }

  /** 检查当前角色是否有菜单访问权限 */
  function hasMenuAccess(menuName: string): boolean {
    const role = currentRole.value
    const allowedMenus = roleMenuMap[role] ?? []
    return allowedMenus.includes(menuName)
  }

  /** 检查当前角色是否拥有指定权限 */
  function hasPermission(permission: string): boolean {
    // 超级管理员拥有所有权限
    if (currentRole.value === UserRole.SUPER_ADMIN) return true
    // 其他角色根据权限映射检查
    const permissions = rolePermissionMap[currentRole.value] ?? []
    return permissions.includes(permission)
  }

  /** 判断当前用户是否为超级管理员 */
  function isSuperAdmin(): boolean {
    return currentRole.value === UserRole.SUPER_ADMIN
  }

  return {
    token,
    userInfo,
    isAuthenticated,
    username,
    currentTenantId,
    currentTenantName,
    currentRole,
    login,
    logout,
    switchTenant,
    hasMenuAccess,
    hasPermission,
    isSuperAdmin,
  }
})
