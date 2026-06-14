import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import WeatherView from '../WeatherView.vue'

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
  ScatterChart: vi.fn(),
  HeatmapChart: vi.fn(),
  EffectScatterChart: vi.fn(),
}))

vi.mock('echarts/components', () => ({
  TitleComponent: vi.fn(),
  TooltipComponent: vi.fn(),
  VisualMapComponent: vi.fn(),
  GeoComponent: vi.fn(),
  GridComponent: vi.fn(),
  LegendComponent: vi.fn(),
  ToolboxComponent: vi.fn(),
}))

vi.mock('echarts/renderers', () => ({
  CanvasRenderer: vi.fn(),
}))

// Mock weather API
vi.mock('@/api/weather', () => ({
  weatherApi: {
    queryPoint: vi.fn().mockResolvedValue({
      lon: 116.4,
      lat: 39.9,
      altitude: 100,
      windSpeed: 5.2,
      windDirection: 180,
      temperature: 25.3,
      humidity: 60.5,
      pressure: 1013,
      visibility: 10.0,
      weatherCode: 0,
      source: 'GFS',
      forecastTime: '2024-01-01T00:00:00Z',
    }),
    queryRegion: vi.fn().mockResolvedValue([
      {
        lon: 116.0,
        lat: 39.0,
        altitude: 100,
        windSpeed: 5.0,
        windDirection: 180,
        temperature: 25.0,
        humidity: 60.0,
        pressure: 1013,
        visibility: 10.0,
        weatherCode: 0,
        source: 'GFS',
        forecastTime: '2024-01-01T00:00:00Z',
      },
      {
        lon: 117.0,
        lat: 40.0,
        altitude: 100,
        windSpeed: 6.0,
        windDirection: 200,
        temperature: 26.0,
        humidity: 55.0,
        pressure: 1012,
        visibility: 9.0,
        weatherCode: 1,
        source: 'GFS',
        forecastTime: '2024-01-01T00:00:00Z',
      },
    ]),
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

describe('WeatherView.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render weather page correctly', () => {
    const wrapper = mount(WeatherView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    expect(wrapper.find('.weather-page').exists()).toBe(true)
    expect(wrapper.find('h2').text()).toContain('气象数据')
  })

  it('should render visualization mode switch', () => {
    const wrapper = mount(WeatherView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const radioGroup = wrapper.find('.viz-mode-switch')
    expect(radioGroup.exists()).toBe(true)

    const html = wrapper.html()
    expect(html).toContain('风场')
    expect(html).toContain('温度')
    expect(html).toContain('湿度')
  })

  it('should render chart container', () => {
    const wrapper = mount(WeatherView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const chartContainer = wrapper.find('.chart-container')
    expect(chartContainer.exists()).toBe(true)
  })

  it('should render query tabs for point and region', () => {
    const wrapper = mount(WeatherView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const html = wrapper.html()
    expect(html).toContain('单点查询')
    expect(html).toContain('区域查询')
  })

  it('should render point query form fields', () => {
    const wrapper = mount(WeatherView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const html = wrapper.html()
    expect(html).toContain('经度')
    expect(html).toContain('纬度')
    expect(html).toContain('高度(m)')
    expect(html).toContain('数据源')
    expect(html).toContain('预报时间')
  })

  it('should render query button', () => {
    const wrapper = mount(WeatherView, {
      global: {
        plugins: [createPinia(), ElementPlus],
      },
    })
    const buttons = wrapper.findAll('.el-button')
    const queryButton = buttons.find(b => b.text().includes('查询'))
    expect(queryButton).toBeTruthy()
  })
})
