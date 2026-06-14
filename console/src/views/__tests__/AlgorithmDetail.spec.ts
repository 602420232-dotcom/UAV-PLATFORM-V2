import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import AlgorithmList from '../AlgorithmList.vue'

// Mock algorithm API with detailed data
vi.mock('@/api/algorithm', () => ({
  algorithmApi: {
    list: vi.fn().mockResolvedValue({
      records: [
        {
          id: 1,
          name: 'A* Path Planning',
          category: 'planning',
          version: '2.1.0',
          status: 'ACTIVE',
          description: 'A* algorithm for UAV path planning',
          registeredAt: '2024-01-01',
          lastRunAt: '2024-06-01T10:00:00Z',
          runCount: 150,
          config: null,
        },
        {
          id: 2,
          name: '3DVAR Assimilation',
          category: 'assimilation',
          version: '1.5.0',
          status: 'ACTIVE',
          description: '3DVAR data assimilation for weather',
          registeredAt: '2024-02-01',
          lastRunAt: null,
          runCount: 0,
          config: null,
        },
        {
          id: 3,
          name: 'LSTM Weather',
          category: 'model_engine',
          version: '1.0.0',
          status: 'INACTIVE',
          description: 'LSTM model for weather prediction',
          registeredAt: '2024-03-01',
          lastRunAt: '2024-05-15T08:00:00Z',
          runCount: 45,
          config: null,
        },
      ],
      total: 3,
      size: 20,
      current: 1,
      pages: 1,
    }),
    getCategoryStats: vi.fn().mockResolvedValue({
      total: 3,
      assimilation: 1,
      planning: 1,
      model_engine: 1,
      edge: 0,
      risk: 0,
      observation: 0,
    }),
    execute: vi.fn().mockResolvedValue({
      taskId: 100,
      status: 'COMPLETED',
      result: { distance: 85.5, time: 8 },
    }),
    getDetail: vi.fn().mockResolvedValue({
      id: 1,
      name: 'A* Path Planning',
      category: 'planning',
      version: '2.1.0',
      status: 'ACTIVE',
      description: 'A* algorithm for UAV path planning',
      registeredAt: '2024-01-01',
      lastRunAt: '2024-06-01T10:00:00Z',
      runCount: 150,
      config: { grid_size: 100, heuristic: 'euclidean' },
    }),
    listByCategory: vi.fn().mockResolvedValue([]),
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
  }
})

describe('AlgorithmList.vue - Detail Functionality', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render algorithm page', () => {
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
    const selects = wrapper.findAll('.el-select')
    expect(selects.length).toBeGreaterThanOrEqual(1)
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

  it('should render search button', () => {
    const wrapper = mount(AlgorithmList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const buttons = wrapper.findAll('.el-button')
    const searchButton = buttons.find(b => b.text().includes('搜索'))
    expect(searchButton).toBeTruthy()
  })

  it('should render stats cards for categories', () => {
    const wrapper = mount(AlgorithmList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const html = wrapper.html()
    expect(html).toContain('全部算法')
    expect(html).toContain('同化')
    expect(html).toContain('规划')
    expect(html).toContain('AI模型')
  })

  it('should render pagination', () => {
    const wrapper = mount(AlgorithmList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const pagination = wrapper.find('.el-pagination')
    expect(pagination.exists()).toBe(true)
  })

  it('should render total algorithm count text', () => {
    const wrapper = mount(AlgorithmList, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const html = wrapper.html()
    expect(html).toContain('个算法')
  })
})
