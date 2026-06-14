import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import AlgorithmList from '../AlgorithmList.vue'

// Mock algorithm API
vi.mock('@/api/algorithm', () => ({
  algorithmApi: {
    list: vi.fn().mockResolvedValue({
      records: [
        {
          id: 1,
          name: 'Test Algorithm',
          category: 'planning',
          version: '1.0.0',
          status: 'ACTIVE',
          description: 'A test algorithm',
          registeredAt: '2024-01-01',
          lastRunAt: null,
          runCount: 0,
          config: null,
        },
      ],
      total: 1,
      size: 20,
      current: 1,
      pages: 1,
    }),
    getCategoryStats: vi.fn().mockResolvedValue({
      total: 10,
      assimilation: 2,
      planning: 3,
      model_engine: 2,
      edge: 1,
      risk: 1,
      observation: 1,
    }),
    execute: vi.fn(),
    getDetail: vi.fn(),
    listByCategory: vi.fn(),
  },
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

describe('AlgorithmList.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render algorithm list page', () => {
    const wrapper = mount(AlgorithmList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    expect(wrapper.find('.algorithm-page').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toContain('算法管理')
  })

  it('should render category filter select', () => {
    const wrapper = mount(AlgorithmList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const select = wrapper.find('.el-select')
    expect(select.exists()).toBe(true)
  })

  it('should render search input', () => {
    const wrapper = mount(AlgorithmList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const inputs = wrapper.findAll('.el-input')
    expect(inputs.length).toBeGreaterThanOrEqual(1)
  })
})
