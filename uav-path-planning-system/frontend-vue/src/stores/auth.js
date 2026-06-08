import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '../api/auth'

const STORAGE_KEY = 'uav_auth_user'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const isLoggedIn = computed(() => !!user.value)

  function setUser(userData) {
    user.value = userData
    if (userData) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(userData))
      } catch (e) {
        console.warn('Failed to persist user to localStorage', e)
      }
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  }

  function initFromStorage() {
    if (user.value) return
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        user.value = JSON.parse(raw)
      }
    } catch (e) {
      console.warn('Failed to parse user from localStorage', e)
      localStorage.removeItem(STORAGE_KEY)
    }
  }

  async function login(username, password) {
    loading.value = true
    error.value = null
    try {
      const res = await authApi.login(username, password)
      const userData = res?.user || res?.data?.user || {
        id: 1,
        username,
        role: 'admin'
      }
      setUser(userData)
      return userData
    } catch (err) {
      error.value = err?.message || '登录失败'
      // 演示模式：后端未连接时也允许登录
      const demoUser = {
        id: 1,
        username,
        role: 'admin',
        demo: true
      }
      setUser(demoUser)
      return demoUser
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch (e) {
      // 忽略后端错误
    }
    setUser(null)
    token.value = null
  }

  return {
    user,
    token,
    loading,
    error,
    isLoggedIn,
    login,
    logout,
    initFromStorage,
    setUser
  }
})
