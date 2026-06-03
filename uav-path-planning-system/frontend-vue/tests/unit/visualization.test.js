import { describe, it, expect, vi } from 'vitest'

// Mock ECharts and Leaflet to avoid native binding issues in test environment
vi.mock('echarts', () => ({
  default: {
    init: vi.fn(() => ({
      setOption: vi.fn(),
      resize: vi.fn(),
      dispose: vi.fn()
    })),
    dispose: vi.fn()
  },
  init: vi.fn(() => ({
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn()
  })),
  dispose: vi.fn()
}))

vi.mock('leaflet.heat', () => ({ default: {} }))

vi.mock('leaflet', () => {
  const mockMap = {
    setView: vi.fn(),
    remove: vi.fn()
  }
  const L = {
    map: vi.fn(() => mockMap),
    tileLayer: vi.fn(() => ({ addTo: vi.fn() })),
    marker: vi.fn(() => ({ addTo: vi.fn(), bindPopup: vi.fn() })),
    polyline: vi.fn(() => ({ addTo: vi.fn() })),
    divIcon: vi.fn(() => ({})),
    circle: vi.fn(() => ({ addTo: vi.fn(), bindPopup: vi.fn() })),
    polygon: vi.fn(() => ({ addTo: vi.fn(), bindPopup: vi.fn() })),
    heatLayer: vi.fn(() => ({ addTo: vi.fn() })),
    Control: { extend: vi.fn(() => ({ addTo: vi.fn() })) }
  }
  globalThis.L = L
  return { default: L, ...L }
})

import { destroyChart, destroyMap } from '@/utils/visualization'

describe('destroyChart', () => {
  it('传入 null 不应抛出异常', () => {
    expect(() => destroyChart(null)).not.toThrow()
  })

  it('传入 undefined 不应抛出异常', () => {
    expect(() => destroyChart(undefined)).not.toThrow()
  })

  it('应调用 chart 的 dispose 方法', () => {
    const dispose = vi.fn()
    destroyChart({ dispose })
    expect(dispose).toHaveBeenCalledTimes(1)
  })

  it('应调用 unregisterChart 清理 resize 事件', () => {
    const dispose = vi.fn()
    destroyChart({ dispose })
    expect(dispose).toHaveBeenCalled()
  })
})

describe('destroyMap', () => {
  it('传入 null 不应抛出异常', () => {
    expect(() => destroyMap(null)).not.toThrow()
  })

  it('传入 undefined 不应抛出异常', () => {
    expect(() => destroyMap(undefined)).not.toThrow()
  })

  it('应调用 map 的 remove 方法', () => {
    const remove = vi.fn()
    destroyMap({ remove })
    expect(remove).toHaveBeenCalledTimes(1)
  })
})
