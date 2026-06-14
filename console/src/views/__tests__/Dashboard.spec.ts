import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import Dashboard from '../Dashboard.vue'

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
  PieChart: vi.fn(),
  GraphChart: vi.fn(),
  LineChart: vi.fn(),
}))

vi.mock('echarts/components', () => ({
  TitleComponent: vi.fn(),
  TooltipComponent: vi.fn(),
  LegendComponent: vi.fn(),
  GridComponent: vi.fn(),
  DataZoomComponent: vi.fn(),
}))

vi.mock('echarts/renderers', () => ({
  CanvasRenderer: vi.fn(),
}))

// Mock dashboard API
vi.mock('@/api/dashboard', () => ({
  dashboardApi: {
    getStats: vi.fn().mockResolvedValue({
      totalTenants: 5,
      totalApiKeys: 12,
      todayApiCalls: 3456,
      activeTasks: 8,
    }),
    getApiCallTrend: vi.fn().mockResolvedValue([
      { date: '2024-01-01', calls: 100 },
      { date: '2024-01-02', calls: 200 },
    ]),
    getServiceDistribution: vi.fn().mockResolvedValue([
      { service: 'Planning', calls: 500 },
      { service: 'Weather', calls: 300 },
    ]),
    getServiceHealth: vi.fn().mockResolvedValue([
      { name: 'API Gateway', status: 'UP', responseTime: 12, lastCheck: '2024-01-01' },
    ]),
  },
}))

describe('Dashboard.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render dashboard page correctly', () => {
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    expect(wrapper.find('.dashboard-page').exists()).toBe(true)
  })

  it('should display algorithm stat cards', () => {
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const cards = wrapper.findAll('.stats-row')
    expect(cards.length).toBeGreaterThanOrEqual(1)

    const html = wrapper.html()
    expect(html).toContain('总算法数')
    expect(html).toContain('今日运行次数')
    expect(html).toContain('平均执行时间')
    expect(html).toContain('活跃算法数')
  })

  it('should contain chart containers', () => {
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const chartCards = wrapper.findAll('.chart-card')
    expect(chartCards.length).toBeGreaterThanOrEqual(2)
  })
})
