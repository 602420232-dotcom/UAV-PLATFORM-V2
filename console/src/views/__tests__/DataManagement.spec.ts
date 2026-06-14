import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import ApiKeyList from '../ApiKeyList.vue'

// Mock API Key API
vi.mock('@/api/apiKey', () => ({
  apiKeyApi: {
    listByTenant: vi.fn().mockResolvedValue([
      {
        id: 1,
        tenantId: 1,
        keyValue: 'uav-plat-ak-abc123456789xyz',
        secret: 'uav-plat-sk-secret123456789',
        name: 'Production Key',
        status: 1,
        rateLimit: 100,
        createdAt: '2024-01-01T10:00:00Z',
        expiresAt: '2025-01-01T10:00:00Z',
      },
      {
        id: 2,
        tenantId: 1,
        keyValue: 'uav-plat-ak-test987654321abc',
        secret: 'uav-plat-sk-testsecret98765',
        name: 'Development Key',
        status: 1,
        rateLimit: null,
        createdAt: '2024-02-01T08:00:00Z',
        expiresAt: null,
      },
      {
        id: 3,
        tenantId: 1,
        keyValue: 'uav-plat-ak-disabled555555',
        secret: 'uav-plat-sk-disabled55555',
        name: 'Old Key',
        status: 0,
        rateLimit: 50,
        createdAt: '2023-06-01T12:00:00Z',
        expiresAt: '2024-06-01T12:00:00Z',
      },
    ]),
    generate: vi.fn().mockResolvedValue({
      id: 4,
      tenantId: 1,
      keyValue: 'uav-plat-ak-newkey12345678',
      secret: 'uav-plat-sk-newsecret12345',
      name: 'New Key',
      status: 1,
      rateLimit: null,
      createdAt: '2024-06-15T10:00:00Z',
      expiresAt: null,
    }),
    enable: vi.fn().mockResolvedValue(undefined),
    disable: vi.fn().mockResolvedValue(undefined),
    remove: vi.fn().mockResolvedValue(undefined),
  },
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
    ElMessageBox: {
      confirm: vi.fn().mockResolvedValue(true),
    },
  }
})

describe('ApiKeyList.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render API key list page correctly', () => {
    const wrapper = mount(ApiKeyList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    expect(wrapper.find('.api-key-list-page').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toContain('API Key 管理')
  })

  it('should render create API key button', () => {
    const wrapper = mount(ApiKeyList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const buttons = wrapper.findAll('.el-button')
    const createButton = buttons.find(b => b.text().includes('创建 API Key'))
    expect(createButton).toBeTruthy()
  })

  it('should render el-table component', () => {
    const wrapper = mount(ApiKeyList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const tables = wrapper.findAll('.el-table')
    expect(tables.length).toBeGreaterThanOrEqual(1)
  })

  it('should render table card', () => {
    const wrapper = mount(ApiKeyList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const tableCard = wrapper.find('.table-card')
    expect(tableCard.exists()).toBe(true)
  })

  it('should have header with title and action', () => {
    const wrapper = mount(ApiKeyList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const header = wrapper.find('.page-header')
    expect(header.exists()).toBe(true)
    expect(header.find('h2').exists()).toBe(true)
  })

  it('should have page structure', () => {
    const wrapper = mount(ApiKeyList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    expect(wrapper.find('.api-key-list-page').exists()).toBe(true)
    expect(wrapper.find('.page-header').exists()).toBe(true)
    expect(wrapper.find('.table-card').exists()).toBe(true)
  })
})
