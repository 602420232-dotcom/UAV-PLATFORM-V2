import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import RiskView from '../RiskView.vue'

// Mock risk API
vi.mock('@/api/risk', () => ({
  riskApi: {
    getHistory: vi.fn().mockResolvedValue([
      {
        id: 1,
        type: 'weather',
        riskLevel: 'LOW',
        score: 0.25,
        factors: [],
        lon: 116.4,
        lat: 39.9,
        altitude: 100,
        assessedAt: '2024-01-01T10:00:00Z',
      },
      {
        id: 2,
        type: 'terrain',
        riskLevel: 'HIGH',
        score: 0.85,
        factors: [
          { name: '风速', value: 15, weight: 0.3, level: 'HIGH' },
        ],
        lon: 117.0,
        lat: 40.0,
        altitude: 200,
        assessedAt: '2024-01-02T14:00:00Z',
      },
      {
        id: 3,
        type: 'airspace',
        riskLevel: 'MEDIUM',
        score: 0.55,
        factors: [],
        lon: 116.5,
        lat: 39.5,
        altitude: 150,
        assessedAt: '2024-01-03T08:00:00Z',
      },
    ]),
    assess: vi.fn().mockResolvedValue({
      id: 4,
      type: 'weather',
      riskLevel: 'MEDIUM',
      score: 0.55,
      factors: [
        { name: '风速', value: 10, weight: 0.3, level: 'MEDIUM' },
        { name: '能见度', value: 5, weight: 0.2, level: 'LOW' },
      ],
      lon: 116.4,
      lat: 39.9,
      altitude: 100,
      assessedAt: '2024-01-04T12:00:00Z',
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
    },
  }
})

describe('RiskView.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render risk page correctly', () => {
    const wrapper = mount(RiskView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    expect(wrapper.find('.risk-page').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toContain('风险/适航评估')
  })

  it('should render risk level statistics', () => {
    const wrapper = mount(RiskView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const html = wrapper.html()
    expect(html).toContain('低风险')
    expect(html).toContain('中风险')
    expect(html).toContain('高风险')
  })

  it('should render stats row with stat cards', () => {
    const wrapper = mount(RiskView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const statsRow = wrapper.find('.stats-row')
    expect(statsRow.exists()).toBe(true)
    const statCards = wrapper.findAll('.stat-card')
    expect(statCards.length).toBe(3)
  })

  it('should render assessment history table card', () => {
    const wrapper = mount(RiskView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const html = wrapper.html()
    expect(html).toContain('评估历史')
  })

  it('should render create assessment button', () => {
    const wrapper = mount(RiskView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const buttons = wrapper.findAll('.el-button')
    const assessButton = buttons.find(b => b.text().includes('发起评估'))
    expect(assessButton).toBeTruthy()
  })

  it('should render el-table component', () => {
    const wrapper = mount(RiskView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const tables = wrapper.findAll('.el-table')
    expect(tables.length).toBeGreaterThanOrEqual(1)
  })
})
