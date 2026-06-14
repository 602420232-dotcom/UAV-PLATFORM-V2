import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import SandboxView from '../SandboxView.vue'

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
  RadarChart: vi.fn(),
  HeatmapChart: vi.fn(),
  LineChart: vi.fn(),
  ScatterChart: vi.fn(),
}))

vi.mock('echarts/components', () => ({
  TitleComponent: vi.fn(),
  TooltipComponent: vi.fn(),
  LegendComponent: vi.fn(),
  GridComponent: vi.fn(),
  VisualMapComponent: vi.fn(),
  RadarComponent: vi.fn(),
}))

vi.mock('echarts/renderers', () => ({
  CanvasRenderer: vi.fn(),
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

describe('SandboxView.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render sandbox page correctly', () => {
    const wrapper = mount(SandboxView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    expect(wrapper.find('.sandbox-page').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toContain('科研沙箱')
  })

  it('should render experiment statistics cards', () => {
    const wrapper = mount(SandboxView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const html = wrapper.html()
    expect(html).toContain('总实验数')
    expect(html).toContain('运行中')
    expect(html).toContain('已完成')
    expect(html).toContain('失败')
  })

  it('should render create experiment button', () => {
    const wrapper = mount(SandboxView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const buttons = wrapper.findAll('.el-button')
    const createButton = buttons.find(b => b.text().includes('创建实验'))
    expect(createButton).toBeTruthy()
  })

  it('should render experiment list card', () => {
    const wrapper = mount(SandboxView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const html = wrapper.html()
    expect(html).toContain('实验列表')
  })

  it('should render algorithm comparison panel', () => {
    const wrapper = mount(SandboxView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const html = wrapper.html()
    expect(html).toContain('算法对比面板')
    expect(html).toContain('选择 2-4 个算法进行对比')
  })

  it('should render Jupyter Lab integration section', () => {
    const wrapper = mount(SandboxView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const html = wrapper.html()
    expect(html).toContain('Jupyter Lab 集成')
    expect(html).toContain('快速启动')
  })

  it('should render chart containers', () => {
    const wrapper = mount(SandboxView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const chartCards = wrapper.findAll('.chart-card')
    expect(chartCards.length).toBeGreaterThanOrEqual(2)
  })
})
