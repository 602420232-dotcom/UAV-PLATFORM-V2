import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import Sidebar from '../layout/Sidebar.vue'

// Mock vue-router
vi.mock('vue-router', () => ({
  useRoute: () => ({
    path: '/dashboard',
  }),
  useRouter: () => ({
    push: vi.fn(),
  }),
}))

// Mock app store
vi.mock('@/stores/app', () => ({
  useAppStore: () => ({
    sidebarCollapsed: false,
  }),
}))

describe('Sidebar.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render sidebar menu items', () => {
    const wrapper = mount(Sidebar, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    expect(wrapper.find('.sidebar').exists()).toBe(true)
    expect(wrapper.find('.sidebar-menu').exists()).toBe(true)

    const html = wrapper.html()
    expect(html).toContain('仪表盘')
    expect(html).toContain('算法管理')
  })

  it('should contain router links for navigation', () => {
    const wrapper = mount(Sidebar, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const menuItems = wrapper.findAll('.el-menu-item')
    expect(menuItems.length).toBeGreaterThanOrEqual(1)

    const subMenus = wrapper.findAll('.el-sub-menu')
    expect(subMenus.length).toBeGreaterThanOrEqual(1)
  })
})
