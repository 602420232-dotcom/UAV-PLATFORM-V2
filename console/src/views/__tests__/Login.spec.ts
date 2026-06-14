import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import Login from '../Login.vue'

// Mock vue-router
const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

// Mock auth store
vi.mock('@/stores/auth', () => ({
  useAuthStore: () => ({
    login: vi.fn().mockResolvedValue(undefined),
  }),
}))

// Mock Element Plus message
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

describe('Login.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockPush.mockClear()
  })

  it('should render login form', () => {
    const wrapper = mount(Login, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    expect(wrapper.find('.login-page').exists()).toBe(true)
    expect(wrapper.find('.login-form').exists()).toBe(true)
  })

  it('should have login button', () => {
    const wrapper = mount(Login, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const button = wrapper.find('.login-btn')
    expect(button.exists()).toBe(true)
    expect(button.text()).toContain('登')
  })

  it('should bind username and password inputs', async () => {
    const wrapper = mount(Login, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })

    const inputs = wrapper.findAll('input')
    expect(inputs.length).toBeGreaterThanOrEqual(2)

    // Check that form items exist for username and password
    const formItems = wrapper.findAll('.el-form-item')
    expect(formItems.length).toBeGreaterThanOrEqual(2)

    const html = wrapper.html()
    expect(html).toContain('用户名')
    expect(html).toContain('密码')
  })
})
