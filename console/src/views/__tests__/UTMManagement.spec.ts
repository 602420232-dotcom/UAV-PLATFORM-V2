import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import UtmView from '../UtmView.vue'

// Mock UTM API
vi.mock('@/api/utm', () => ({
  utmApi: {
    listAirspaces: vi.fn().mockResolvedValue([
      {
        id: 1,
        name: '禁飞区A',
        type: 'restricted',
        status: 'active',
        minAltitude: 0,
        maxAltitude: 500,
        geometry: null,
        restrictions: ['禁止飞行'],
        createdAt: '2024-01-01T10:00:00Z',
      },
      {
        id: 2,
        name: '限制区B',
        type: 'controlled',
        status: 'active',
        minAltitude: 100,
        maxAltitude: 1000,
        geometry: null,
        restrictions: ['需要审批'],
        createdAt: '2024-01-02T08:00:00Z',
      },
    ]),
    listFlightPlans: vi.fn().mockResolvedValue([
      {
        id: 1,
        uavId: 'UAV-001',
        status: 'approved',
        waypoints: [],
        submittedAt: '2024-01-01T10:00:00Z',
        approvedAt: '2024-01-01T10:30:00Z',
      },
    ]),
    listConflictAlerts: vi.fn().mockResolvedValue([
      {
        id: 1,
        type: 'proximity',
        severity: 'HIGH',
        status: 'active',
        uavId1: 'UAV-001',
        uavId2: 'UAV-002',
        location: { lon: 116.4, lat: 39.9, altitude: 100 },
        timeToConflict: 30,
        createdAt: '2024-01-01T10:00:00Z',
      },
    ]),
    createAirspace: vi.fn().mockResolvedValue({
      id: 3,
      name: '临时空域',
      type: 'temporary',
      status: 'active',
      minAltitude: 0,
      maxAltitude: 300,
      geometry: null,
      restrictions: [],
      createdAt: '2024-01-03T10:00:00Z',
    }),
    checkRestriction: vi.fn().mockResolvedValue(true),
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

describe('UtmView.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render UTM page correctly', () => {
    const wrapper = mount(UtmView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    expect(wrapper.find('.utm-page').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toContain('UTM 空域管理')
  })

  it('should render create airspace button', () => {
    const wrapper = mount(UtmView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const buttons = wrapper.findAll('.el-button')
    const createButton = buttons.find(b => b.text().includes('创建空域'))
    expect(createButton).toBeTruthy()
  })

  it('should render airspace restriction check card', () => {
    const wrapper = mount(UtmView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const html = wrapper.html()
    expect(html).toContain('空域限制检查')
    expect(html).toContain('检查')
  })

  it('should render airspace list card', () => {
    const wrapper = mount(UtmView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const html = wrapper.html()
    expect(html).toContain('空域列表')
  })

  it('should render conflict alerts card', () => {
    const wrapper = mount(UtmView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const html = wrapper.html()
    expect(html).toContain('冲突告警')
  })

  it('should render flight plans card', () => {
    const wrapper = mount(UtmView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const html = wrapper.html()
    expect(html).toContain('飞行计划')
  })
})
