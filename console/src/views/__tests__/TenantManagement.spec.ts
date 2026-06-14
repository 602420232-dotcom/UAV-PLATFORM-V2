import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import TenantList from '../TenantList.vue'

// Mock vue-router
const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

// Mock tenant API
vi.mock('@/api/tenant', () => ({
  tenantApi: {
    list: vi.fn().mockResolvedValue({
      records: [
        {
          id: 1,
          name: 'Default Tenant',
          schemaName: 'tenant_default',
          status: 1,
          quotaConfig: '{"maxAlgorithms": 10}',
          createdAt: '2024-01-01T10:00:00Z',
          updatedAt: '2024-01-01T10:00:00Z',
        },
        {
          id: 2,
          name: 'Enterprise Tenant',
          schemaName: 'tenant_enterprise',
          status: 1,
          quotaConfig: '{"maxAlgorithms": 50}',
          createdAt: '2024-02-01T08:00:00Z',
          updatedAt: '2024-02-01T08:00:00Z',
        },
        {
          id: 3,
          name: 'Trial Tenant',
          schemaName: 'tenant_trial',
          status: 0,
          quotaConfig: null,
          createdAt: '2024-03-01T12:00:00Z',
          updatedAt: '2024-03-15T12:00:00Z',
        },
      ],
      total: 3,
      size: 10,
      current: 1,
      pages: 1,
    }),
    create: vi.fn().mockResolvedValue({
      id: 4,
      name: 'New Tenant',
      schemaName: 'tenant_new',
      status: 1,
      quotaConfig: null,
      createdAt: '2024-06-01T10:00:00Z',
      updatedAt: '2024-06-01T10:00:00Z',
    }),
    disable: vi.fn().mockResolvedValue(undefined),
    enable: vi.fn().mockResolvedValue(undefined),
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

describe('TenantList.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    mockPush.mockClear()
  })

  it('should render tenant list page correctly', () => {
    const wrapper = mount(TenantList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    expect(wrapper.find('.tenant-list-page').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toContain('租户管理')
  })

  it('should render create tenant button', () => {
    const wrapper = mount(TenantList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const buttons = wrapper.findAll('.el-button')
    const createButton = buttons.find(b => b.text().includes('新建租户'))
    expect(createButton).toBeTruthy()
  })

  it('should render el-table component', () => {
    const wrapper = mount(TenantList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const tables = wrapper.findAll('.el-table')
    expect(tables.length).toBeGreaterThanOrEqual(1)
  })

  it('should render table card', () => {
    const wrapper = mount(TenantList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const tableCard = wrapper.find('.table-card')
    expect(tableCard.exists()).toBe(true)
  })

  it('should render pagination', () => {
    const wrapper = mount(TenantList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const pagination = wrapper.find('.el-pagination')
    expect(pagination.exists()).toBe(true)
  })

  it('should have header with title and action', () => {
    const wrapper = mount(TenantList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const header = wrapper.find('.page-header')
    expect(header.exists()).toBe(true)
    expect(header.find('h2').exists()).toBe(true)
  })
})
