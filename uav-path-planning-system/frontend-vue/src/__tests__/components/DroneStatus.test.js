import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'

const DroneStatus = {
  props: {
    name: { type: String, default: '' },
    status: { type: String, default: '离线' },
    battery: { type: Number, default: 0 },
    altitude: { type: Number, default: 0 },
    speed: { type: Number, default: 0 }
  },
  template: `
    <div class="drone-status">
      <div class="drone-name">{{ name }}</div>
      <div class="drone-metrics">
        <span class="status" :class="status">{{ status }}</span>
        <span class="battery" :style="{ color: battery > 20 ? 'green' : 'red' }">🔋{{ battery }}%</span>
        <span>高度: {{ altitude }}m</span>
        <span>速度: {{ speed }}m/s</span>
      </div>
    </div>
  `
}

describe('DroneStatus', () => {
  it('should render drone info', () => {
    const wrapper = mount(DroneStatus, {
      props: {
        name: 'DJI-M300-01',
        status: '飞行中',
        battery: 85,
        altitude: 120,
        speed: 15
      }
    })
    expect(wrapper.text()).toContain('DJI-M300-01')
    expect(wrapper.text()).toContain('85%')
    expect(wrapper.text()).toContain('120m')
    expect(wrapper.text()).toContain('15m/s')
  })

  it('should show red battery color when low', () => {
    const wrapper = mount(DroneStatus, {
      props: { name: 'Test', battery: 15 }
    })
    const batteryEl = wrapper.find('.battery')
    expect(batteryEl.attributes('style')).toContain('red')
  })

  it('should show green battery when sufficient', () => {
    const wrapper = mount(DroneStatus, {
      props: { name: 'Test', battery: 80 }
    })
    const batteryEl = wrapper.find('.battery')
    expect(batteryEl.attributes('style')).toContain('green')
  })
})
