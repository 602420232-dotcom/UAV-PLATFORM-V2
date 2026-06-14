import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import ObservationView from '../ObservationView.vue'

// Mock observation API
vi.mock('@/api/observation', () => ({
  observationApi: {
    listTasks: vi.fn().mockResolvedValue([
      {
        id: 1,
        type: 'meteorological',
        status: 'completed',
        priority: 5,
        region: { minLon: 115, minLat: 39, maxLon: 118, maxLat: 41 },
        targetVariables: ['temperature', 'wind', 'humidity'],
        platform: 'UAV-001',
        createdAt: '2024-01-01T10:00:00Z',
        completedAt: '2024-01-01T12:00:00Z',
      },
      {
        id: 2,
        type: 'environmental',
        status: 'pending',
        priority: 8,
        region: { minLon: 116, minLat: 40, maxLon: 117, maxLat: 41 },
        targetVariables: ['temperature', 'pressure'],
        platform: '',
        createdAt: '2024-01-02T08:00:00Z',
        completedAt: null,
      },
    ]),
    createTask: vi.fn().mockResolvedValue({
      id: 3,
      type: 'meteorological',
      status: 'pending',
      priority: 5,
      region: { minLon: 115, minLat: 39, maxLon: 118, maxLat: 41 },
      targetVariables: ['temperature', 'wind'],
      platform: '',
      createdAt: '2024-01-03T10:00:00Z',
      completedAt: null,
    }),
    getDecision: vi.fn().mockResolvedValue({
      id: 1,
      taskId: 1,
      decision: '建议立即执行观测',
      reason: '当前气象条件良好，适合观测',
      suggestedPlatforms: ['UAV-001', 'UAV-002'],
      suggestedTime: '2024-01-03T14:00:00Z',
      coverageScore: 0.85,
      createdAt: '2024-01-03T10:00:00Z',
    }),
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
      warning: vi.fn(),
    },
  }
})

describe('ObservationView.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render observation page correctly', () => {
    const wrapper = mount(ObservationView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    expect(wrapper.find('.observation-page').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toContain('观测决策')
  })

  it('should render header action buttons', () => {
    const wrapper = mount(ObservationView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const html = wrapper.html()
    expect(html).toContain('获取决策建议')
    expect(html).toContain('创建观测任务')
  })

  it('should render task list table card', () => {
    const wrapper = mount(ObservationView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const html = wrapper.html()
    expect(html).toContain('观测任务列表')
  })

  it('should render el-table component', () => {
    const wrapper = mount(ObservationView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const tables = wrapper.findAll('.el-table')
    expect(tables.length).toBeGreaterThanOrEqual(1)
  })

  it('should have create task button', () => {
    const wrapper = mount(ObservationView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const buttons = wrapper.findAll('.el-button')
    const createButton = buttons.find(b => b.text().includes('创建观测任务'))
    expect(createButton).toBeTruthy()
  })

  it('should have decision button', () => {
    const wrapper = mount(ObservationView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const buttons = wrapper.findAll('.el-button')
    const decisionButton = buttons.find(b => b.text().includes('获取决策建议'))
    expect(decisionButton).toBeTruthy()
  })
})
