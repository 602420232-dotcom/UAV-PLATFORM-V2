import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import { getToken, setToken, removeToken, getUserInfo, setUserInfo, removeUserInfo } from '@/utils/auth'

export interface UserInfo {
  id: number
  username: string
  role: string
  tenantId?: number
  tenantName?: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(getToken() || '')
  const userInfo = ref<UserInfo | null>(getUserInfo())

  const isAuthenticated = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username ?? '')
  const currentTenantId = computed(() => userInfo.value?.tenantId)
  const currentTenantName = computed(() => userInfo.value?.tenantName ?? '')

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

  return {
    token,
    userInfo,
    isAuthenticated,
    username,
    currentTenantId,
    currentTenantName,
    login,
    logout,
    switchTenant,
  }
})
