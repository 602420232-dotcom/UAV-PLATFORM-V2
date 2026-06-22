import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

// Mock auth API
vi.mock('@/api/auth', () => ({
  authApi: {
    login: vi.fn().mockResolvedValue({
      token: 'test-jwt-token',
      userId: 1,
      role: 'admin',
      tenantId: 1,
      tenantName: 'Default Tenant',
    }),
  },
}))

// Mock auth utils
vi.mock('@/utils/auth', () => ({
  getToken: vi.fn().mockReturnValue('test-jwt-token'),
  setToken: vi.fn(),
  removeToken: vi.fn(),
  getUserInfo: vi.fn().mockReturnValue({
    id: 1,
    username: 'admin',
    role: 'admin',
    tenantId: 1,
    tenantName: 'Default Tenant',
  }),
  setUserInfo: vi.fn(),
  removeUserInfo: vi.fn(),
}))

// Mock Element Plus
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...(actual as object),
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
    },
  }
})

describe('UserProfile - Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should have auth store with correct initial state', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(true)
    expect(store.username).toBe('admin')
    expect(store.currentTenantId).toBe(1)
    expect(store.currentTenantName).toBe('Default Tenant')
  })

  it('should have token value', () => {
    const store = useAuthStore()
    expect(store.token).toBe('test-jwt-token')
  })

  it('should have user info', () => {
    const store = useAuthStore()
    expect(store.userInfo).not.toBeNull()
    expect(store.userInfo?.id).toBe(1)
    expect(store.userInfo?.role).toBe('admin')
  })

  it('should provide login method', () => {
    const store = useAuthStore()
    expect(typeof store.login).toBe('function')
  })

  it('should provide logout method', () => {
    const store = useAuthStore()
    expect(typeof store.logout).toBe('function')
  })

  it('should provide switchTenant method', () => {
    const store = useAuthStore()
    expect(typeof store.switchTenant).toBe('function')
  })

  it('should call login and update state', async () => {
    const store = useAuthStore()
    await store.login('admin', 'password123')
    expect(store.token).toBe('test-jwt-token')
    expect(store.username).toBe('admin')
  })

  it('should clear state on logout', () => {
    const store = useAuthStore()
    store.logout()
    expect(store.token).toBe('')
    expect(store.userInfo).toBeNull()
    expect(store.isAuthenticated).toBe(false)
  })

  it('should switch tenant correctly', () => {
    const store = useAuthStore()
    store.switchTenant(2, 'New Tenant')
    expect(store.currentTenantId).toBe(2)
    expect(store.currentTenantName).toBe('New Tenant')
  })
})
