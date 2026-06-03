import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'

// A simple weather card component inline for testing
const WeatherCard = {
  props: {
    title: { type: String, default: '' },
    value: { type: [Number, String], default: '' },
    unit: { type: String, default: '' },
    status: { type: String, default: 'normal' }
  },
  template: `
    <div class="weather-card" :class="status">
      <div class="weather-card-title">{{ title }}</div>
      <div class="weather-card-value">
        <span class="value">{{ value }}</span>
        <span class="unit">{{ unit }}</span>
      </div>
    </div>
  `
}

describe('WeatherCard', () => {
  it('should render title and value', () => {
    const wrapper = mount(WeatherCard, {
      props: {
        title: '温度',
        value: 25.5,
        unit: '°C'
      }
    })
    expect(wrapper.text()).toContain('温度')
    expect(wrapper.text()).toContain('25.5')
    expect(wrapper.text()).toContain('°C')
  })

  it('should apply status class', () => {
    const wrapper = mount(WeatherCard, {
      props: {
        title: '风速',
        value: 12,
        unit: 'm/s',
        status: 'warning'
      }
    })
    expect(wrapper.classes()).toContain('weather-card')
    expect(wrapper.classes()).toContain('warning')
  })

  it('should handle zero value', () => {
    const wrapper = mount(WeatherCard, {
      props: {
        title: '降水量',
        value: 0,
        unit: 'mm'
      }
    })
    expect(wrapper.find('.value').text()).toBe('0')
  })
})
