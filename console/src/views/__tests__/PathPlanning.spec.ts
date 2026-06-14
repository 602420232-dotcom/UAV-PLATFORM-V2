import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import PlanningView from '../PlanningView.vue'

// Mock echarts
vi.mock('echarts/core', () => ({
  use: vi.fn(),
  init: vi.fn(() => ({
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn(),
  })),
  graphic: {
    LinearGradient: vi.fn(),
  },
}))

vi.mock('echarts/charts', () => ({
  LineChart: vi.fn(),
  ScatterChart: vi.fn(),
}))

vi.mock('echarts/components', () => ({
  TitleComponent: vi.fn(),
  TooltipComponent: vi.fn(),
  GridComponent: vi.fn(),
  LegendComponent: vi.fn(),
  MarkPointComponent: vi.fn(),
  MarkLineComponent: vi.fn(),
}))

vi.mock('echarts/renderers', () => ({
  CanvasRenderer: vi.fn(),
}))

// Mock planning API
vi.mock('@/api/planning', () => ({
  planningApi: {
    listTasks: vi.fn().mockResolvedValue([
      {
        id: 1,
        type: 'A*',
        status: 'COMPLETED',
        createdAt: '2024-01-01T10:00:00Z',
        completedAt: '2024-01-01T10:05:00Z',
        errorMessage: null,
      },
      {
        id: 2,
        type: 'RRT*',
        status: 'RUNNING',
        createdAt: '2024-01-02T08:00:00Z',
        completedAt: null,
        errorMessage: null,
      },
    ]),
    planPath: vi.fn().mockResolvedValue({
      id: 3,
      type: 'A*',
      status: 'PENDING',
      createdAt: '2024-01-03T10:00:00Z',
      completedAt: null,
      errorMessage: null,
    }),
    getPathResult: vi.fn().mockResolvedValue({
      taskId: 1,
      waypoints: [
        { lon: 116.3, lat: 39.9, altitude: 100, speed: 10, timestamp: '2024-01-01T10:00:00Z' },
        { lon: 116.5, lat: 39.95, altitude: 120, speed: 12, timestamp: '2024-01-01T10:02:00Z' },
        { lon: 117.0, lat: 40.0, altitude: 100, speed: 10, timestamp: '2024-01-01T10:05:00Z' },
      ],
      totalDistance: 85.5,
      estimatedTime: 8,
      fuelConsumption: 2.3,
    }),
    cancelTask: vi.fn().mockResolvedValue(undefined),
  },
}))

// Mock algorithm API
vi.mock('@/api/algorithm', () => ({
  algorithmApi: {
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
    ElMessageBox: {
      confirm: vi.fn().mockResolvedValue(true),
    },
  }
})

describe('PlanningView.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render planning page correctly', () => {
    const wrapper = mount(PlanningView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    expect(wrapper.find('.planning-page').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toContain('飞行计划管理')
  })

  it('should render create path planning button', () => {
    const wrapper = mount(PlanningView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const buttons = wrapper.findAll('.el-button')
    const createButton = buttons.find(b => b.text().includes('新建路径规划'))
    expect(createButton).toBeTruthy()
  })

  it('should render flight plan list card', () => {
    const wrapper = mount(PlanningView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const html = wrapper.html()
    expect(html).toContain('飞行计划列表')
  })

  it('should render planning task list card', () => {
    const wrapper = mount(PlanningView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const html = wrapper.html()
    expect(html).toContain('规划任务')
  })

  it('should render el-table components', () => {
    const wrapper = mount(PlanningView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const tables = wrapper.findAll('.el-table')
    expect(tables.length).toBeGreaterThanOrEqual(2)
  })
})
