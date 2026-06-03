import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// ─── Hoisted mocks ───────────────────────────────────────────────
// These must be hoisted above imports so vi.mock factories can reference them.
const HOISTED = vi.hoisted(() => {
  // Leaflet mocks
  const L = {
    circle: vi.fn(),
    polygon: vi.fn(),
    polyline: vi.fn(),
    heatLayer: vi.fn(),
    DomUtil: { create: vi.fn() },
    // extend must return a regular (constructable) function so `new` works
    Control: {
      extend: vi.fn(function (proto) {
        return function (opts) {
          return { addTo: vi.fn(), onAdd: proto && proto.onAdd ? proto.onAdd : function () {} }
        }
      })
    }
  }

  // ECharts mocks
  const echarts = {
    init: vi.fn()
  }

  return { L, echarts }
})

// ─── Module mocks ────────────────────────────────────────────────
vi.mock('leaflet', () => ({ default: HOISTED.L }))

vi.mock('leaflet.heat', () => ({ default: {} }))

// visualization.js uses `import * as echarts from 'echarts'` then calls
// echarts.init(...), so init must be a direct named export of the mock.
vi.mock('echarts', () => HOISTED.echarts)

// Mock onUnmounted from Vue so usePolling doesn't throw in test context
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue')
  return { ...actual, onUnmounted: vi.fn() }
})

// ─── Imports ─────────────────────────────────────────────────────
import {
  destroyChart,
  initLineChart,
  addNoFlyZone,
  addWeatherHeatmap,
  addRiskPath
} from '@/utils/visualization'

import { usePolling } from '@/utils/usePolling'

// ─── Helpers ─────────────────────────────────────────────────────
function createMockChart() {
  const chart = {
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn()
  }
  HOISTED.echarts.init.mockReturnValue(chart)
  return chart
}

function createMockMap() {
  return {
    on: vi.fn(),
    off: vi.fn(),
    addLayer: vi.fn(),
    removeLayer: vi.fn(),
    addTo: vi.fn().mockReturnThis(),
    bindPopup: vi.fn().mockReturnThis(),
    remove: vi.fn()
  }
}

beforeEach(() => {
  vi.clearAllMocks()
  // Reset DOM
  document.body.innerHTML = ''
})

afterEach(() => {
  vi.restoreAllMocks()
})

// ═══════════════════════════════════════════════════════════════════
// 1. registerChart / unregisterChart / destroyChart
// ═══════════════════════════════════════════════════════════════════
describe('registerChart / unregisterChart / destroyChart', () => {
  it('registerChart — initLineChart 调用后 window 应注册 resize 事件', () => {
    const addSpy = vi.spyOn(window, 'addEventListener')
    document.body.innerHTML = '<div id="chart"></div>'
    createMockChart()

    initLineChart('chart')

    expect(addSpy).toHaveBeenCalledWith('resize', expect.any(Function))
    addSpy.mockRestore()
  })

  it('unregisterChart — destroyChart 调用后 window 应移除 resize 事件', () => {
    const addSpy = vi.spyOn(window, 'addEventListener')
    const removeSpy = vi.spyOn(window, 'removeEventListener')

    document.body.innerHTML = '<div id="chart"></div>'
    const chart = createMockChart()
    initLineChart('chart')

    // Capture the handler that was registered
    const registeredHandler = addSpy.mock.calls.find(
      ([event]) => event === 'resize'
    )?.[1]
    expect(registeredHandler).toBeDefined()

    destroyChart(chart)

    expect(removeSpy).toHaveBeenCalledWith('resize', registeredHandler)
    addSpy.mockRestore()
    removeSpy.mockRestore()
  })

  it('destroyChart 应调用 chart.dispose', () => {
    const chart = createMockChart()
    destroyChart(chart)
    expect(chart.dispose).toHaveBeenCalledTimes(1)
  })

  it('destroyChart 传入 null 不应抛出异常', () => {
    expect(() => destroyChart(null)).not.toThrow()
  })

  it('destroyChart 传入 undefined 不应抛出异常', () => {
    expect(() => destroyChart(undefined)).not.toThrow()
  })

  it('destroyChart 对已 dispose 的图表应安全处理', () => {
    const chart = createMockChart()
    destroyChart(chart)
    // 第二次调用不应抛异常
    expect(() => destroyChart(chart)).not.toThrow()
    // dispose 仍应被调用（第二次调用的 dispose 会再次触发）
    expect(chart.dispose).toHaveBeenCalledTimes(2)
  })
})

// ═══════════════════════════════════════════════════════════════════
// 2. addNoFlyZone
// ═══════════════════════════════════════════════════════════════════
describe('addNoFlyZone', () => {
  function setupLeafletReturn() {
    const layer = {
      addTo: vi.fn().mockReturnThis(),
      bindPopup: vi.fn().mockReturnThis()
    }
    HOISTED.L.circle.mockReturnValue(layer)
    HOISTED.L.polygon.mockReturnValue(layer)
    return layer
  }

  it('应接受 circle 类型禁飞区并调用 L.circle', () => {
    const map = createMockMap()
    const layer = setupLeafletReturn()
    const zone = {
      id: 'NFZ-001',
      name: '机场禁飞区',
      type: 'circle',
      center: [39.9042, 116.4074],
      radius: 5000
    }

    const result = addNoFlyZone(map, zone)

    expect(HOISTED.L.circle).toHaveBeenCalledWith(
      [39.9042, 116.4074],
      expect.objectContaining({ radius: 5000 })
    )
    expect(layer.addTo).toHaveBeenCalledWith(map)
    expect(layer.bindPopup).toHaveBeenCalled()
    expect(result).toBe(layer)
  })

  it('应接受 polygon 类型禁飞区并调用 L.polygon', () => {
    const map = createMockMap()
    const layer = setupLeafletReturn()
    const zone = {
      id: 'NFZ-002',
      name: '多边禁飞区',
      type: 'polygon',
      points: [
        [39.90, 116.40],
        [39.91, 116.41],
        [39.92, 116.40]
      ]
    }

    const result = addNoFlyZone(map, zone)

    expect(HOISTED.L.polygon).toHaveBeenCalledWith(
      zone.points,
      expect.objectContaining({ color: '#ff0000', fillOpacity: 0.2 })
    )
    expect(layer.addTo).toHaveBeenCalledWith(map)
    expect(result).toBe(layer)
  })

  it('应处理未知 type 时不添加图层', () => {
    const map = createMockMap()
    const zone = { id: 'NFZ-003', type: 'unknown' }

    const result = addNoFlyZone(map, zone)

    expect(HOISTED.L.circle).not.toHaveBeenCalled()
    expect(HOISTED.L.polygon).not.toHaveBeenCalled()
    expect(result).toBeUndefined()
  })

  it('无名称时 popup 应显示 "未命名"', () => {
    const map = createMockMap()
    const layer = setupLeafletReturn()
    const zone = { id: 'NFZ-004', type: 'circle', center: [39.9, 116.4], radius: 1000 }

    addNoFlyZone(map, zone)

    expect(layer.bindPopup).toHaveBeenCalled()
    const popupHtml = layer.bindPopup.mock.calls[0][0]
    expect(popupHtml).toContain('未命名')
  })

  it('应使用正确的禁飞区样式 (红色, 半透明)', () => {
    const map = createMockMap()
    const layer = setupLeafletReturn()
    const zone = { id: 'NFZ-005', type: 'circle', center: [39.9, 116.4], radius: 2000, name: '测试' }

    addNoFlyZone(map, zone)

    expect(HOISTED.L.circle).toHaveBeenCalledWith(
      expect.any(Array),
      expect.objectContaining({
        color: '#ff0000',
        fillColor: '#ff0000',
        fillOpacity: 0.2,
        weight: 2
      })
    )
  })
})

// ═══════════════════════════════════════════════════════════════════
// 3. addWeatherHeatmap
// ═══════════════════════════════════════════════════════════════════
describe('addWeatherHeatmap', () => {
  it('应调用 L.heatLayer 并传入数据与选项', () => {
    const map = createMockMap()
    const heatLayer = { addTo: vi.fn().mockReturnThis() }
    HOISTED.L.heatLayer.mockReturnValue(heatLayer)

    const data = [
      [39.90, 116.40, 0.5],
      [39.91, 116.41, 0.8]
    ]
    const result = addWeatherHeatmap(map, data, { radius: 30 })

    expect(HOISTED.L.heatLayer).toHaveBeenCalledWith(
      data,
      expect.objectContaining({ radius: 30 })
    )
    expect(heatLayer.addTo).toHaveBeenCalledWith(map)
    expect(result).toBe(heatLayer)
  })

  it('未传 options 时应使用默认选项', () => {
    const map = createMockMap()
    const heatLayer = { addTo: vi.fn().mockReturnThis() }
    HOISTED.L.heatLayer.mockReturnValue(heatLayer)

    addWeatherHeatmap(map, [])

    const defaultOptions = HOISTED.L.heatLayer.mock.calls[0][1]
    expect(defaultOptions.radius).toBe(25)
    expect(defaultOptions.blur).toBe(15)
    expect(defaultOptions.maxZoom).toBe(17)
    expect(defaultOptions.gradient).toBeDefined()
    expect(defaultOptions.gradient[0.0]).toBe('#00ff00')
    expect(defaultOptions.gradient[1.0]).toBe('#880000')
  })
})

// ═══════════════════════════════════════════════════════════════════
// 4. addRiskPath — color mapping
// ═══════════════════════════════════════════════════════════════════
describe('addRiskPath — 风险颜色映射', () => {
  beforeEach(() => {
    // Make L.polyline return a consistent object
    HOISTED.L.polyline.mockReturnValue({
      addTo: vi.fn().mockReturnThis(),
      bindPopup: vi.fn().mockReturnThis()
    })
    HOISTED.L.DomUtil.create.mockReturnValue(document.createElement('div'))
  })

  it('风险 0 — 应使用绿色 (#52c41a)', () => {
    const map = createMockMap()
    const segments = [{ points: [[39.9, 116.4]], risk: 0 }]

    addRiskPath(map, segments)

    const opts = HOISTED.L.polyline.mock.calls[0][1]
    expect(opts.color).toBe('#52c41a')
  })

  it('风险 2.5 — 应使用绿色 (#52c41a)', () => {
    const map = createMockMap()
    const segments = [{ points: [[39.9, 116.4]], risk: 2.5 }]

    addRiskPath(map, segments)

    const opts = HOISTED.L.polyline.mock.calls[0][1]
    expect(opts.color).toBe('#52c41a')
  })

  it('风险 3 — 应使用橙色 (#fa8c16)', () => {
    const map = createMockMap()
    const segments = [{ points: [[39.9, 116.4]], risk: 3 }]

    addRiskPath(map, segments)

    const opts = HOISTED.L.polyline.mock.calls[0][1]
    expect(opts.color).toBe('#fa8c16')
  })

  it('风险 5.5 — 应使用橙色 (#fa8c16)', () => {
    const map = createMockMap()
    const segments = [{ points: [[39.9, 116.4]], risk: 5.5 }]

    addRiskPath(map, segments)

    const opts = HOISTED.L.polyline.mock.calls[0][1]
    expect(opts.color).toBe('#fa8c16')
  })

  it('风险 6 — 应使用红色 (#f5222d)', () => {
    const map = createMockMap()
    const segments = [{ points: [[39.9, 116.4]], risk: 6 }]

    addRiskPath(map, segments)

    const opts = HOISTED.L.polyline.mock.calls[0][1]
    expect(opts.color).toBe('#f5222d')
  })

  it('风险 7.9 — 应使用红色 (#f5222d)', () => {
    const map = createMockMap()
    const segments = [{ points: [[39.9, 116.4]], risk: 7.9 }]

    addRiskPath(map, segments)

    const opts = HOISTED.L.polyline.mock.calls[0][1]
    expect(opts.color).toBe('#f5222d')
  })

  it('风险 8 — 应使用深红色 (#a8071a)', () => {
    const map = createMockMap()
    const segments = [{ points: [[39.9, 116.4]], risk: 8 }]

    addRiskPath(map, segments)

    const opts = HOISTED.L.polyline.mock.calls[0][1]
    expect(opts.color).toBe('#a8071a')
  })

  it('风险 10 — 应使用深红色 (#a8071a)', () => {
    const map = createMockMap()
    const segments = [{ points: [[39.9, 116.4]], risk: 10 }]

    addRiskPath(map, segments)

    const opts = HOISTED.L.polyline.mock.calls[0][1]
    expect(opts.color).toBe('#a8071a')
  })

  it('风险值应被限制在 0-10 范围内（负数 clamp 到 0）', () => {
    const map = createMockMap()
    const segments = [{ points: [[39.9, 116.4]], risk: -5 }]

    addRiskPath(map, segments)

    const opts = HOISTED.L.polyline.mock.calls[0][1]
    expect(opts.color).toBe('#52c41a')
  })

  it('风险值应被限制在 0-10 范围内（超过 10 clamp 到 10）', () => {
    const map = createMockMap()
    const segments = [{ points: [[39.9, 116.4]], risk: 20 }]

    addRiskPath(map, segments)

    const opts = HOISTED.L.polyline.mock.calls[0][1]
    expect(opts.color).toBe('#a8071a')
  })

  it('应返回 { layers, legend } 对象', () => {
    const map = createMockMap()
    const segments = [{ points: [[39.9, 116.4]], risk: 3 }]

    const result = addRiskPath(map, segments)

    expect(result).toHaveProperty('layers')
    expect(result).toHaveProperty('legend')
    expect(Array.isArray(result.layers)).toBe(true)
    expect(result.layers).toHaveLength(1)
  })

  it('多段路径时每个段应各自创建 polyline', () => {
    const map = createMockMap()
    const segments = [
      { points: [[39.9, 116.4]], risk: 1 },
      { points: [[39.91, 116.41]], risk: 5 },
      { points: [[39.92, 116.42]], risk: 9 }
    ]

    const result = addRiskPath(map, segments)

    expect(HOISTED.L.polyline).toHaveBeenCalledTimes(3)
    expect(result.layers).toHaveLength(3)
  })

  it('线宽应随风险值增加而增加', () => {
    const map = createMockMap()

    addRiskPath(map, [{ points: [[39.9, 116.4]], risk: 1 }])
    const lightWeight = HOISTED.L.polyline.mock.calls[0][1].weight

    addRiskPath(map, [{ points: [[39.9, 116.4]], risk: 9 }])
    const heavyWeight = HOISTED.L.polyline.mock.calls[1][1].weight

    expect(heavyWeight).toBeGreaterThan(lightWeight)
  })
})

// ═══════════════════════════════════════════════════════════════════
// 5. usePolling
// ═══════════════════════════════════════════════════════════════════
describe('usePolling', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('应返回 { polling, start, stop }', () => {
    const composable = usePolling(() => {})

    expect(composable).toHaveProperty('polling')
    expect(composable).toHaveProperty('start')
    expect(composable).toHaveProperty('stop')
    expect(typeof composable.start).toBe('function')
    expect(typeof composable.stop).toBe('function')
  })

  it('enabled 为 true 且 immediate 为 true 时 polling 应为 true', () => {
    const fn = vi.fn()
    const { polling } = usePolling(fn, { enabled: true, immediate: true })

    // watch with immediate fires synchronously
    expect(polling.value).toBe(true)
    // fetchFn should have been called
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('enabled 为 false 时 polling 应为 false', () => {
    const fn = vi.fn()
    const { polling } = usePolling(fn, { enabled: false, immediate: false })

    expect(polling.value).toBe(false)
    expect(fn).not.toHaveBeenCalled()
  })

  it('start 应将 polling 设为 true', () => {
    const fn = vi.fn()
    const { polling, start } = usePolling(fn, { enabled: false, immediate: false })

    expect(polling.value).toBe(false)
    start()
    expect(polling.value).toBe(true)
  })

  it('stop 应将 polling 设为 false', () => {
    const fn = vi.fn()
    const { polling, stop } = usePolling(fn, { enabled: true, immediate: false })

    expect(polling.value).toBe(true)
    stop()
    expect(polling.value).toBe(false)
  })

  it('多次调用 stop 不应抛出异常', () => {
    const fn = vi.fn()
    const { stop } = usePolling(fn, { enabled: true, immediate: false })

    expect(() => {
      stop()
      stop()
      stop()
    }).not.toThrow()
  })

  it('start 后应立即调用 fetchFn（immediate 为 true）', () => {
    const fn = vi.fn()
    const { start } = usePolling(fn, { enabled: false, immediate: true })

    expect(fn).not.toHaveBeenCalled()
    start()
    expect(fn).toHaveBeenCalledTimes(1)
  })

  it('start 后不应立即调用 fetchFn（immediate 为 false）', () => {
    const fn = vi.fn()
    const { start } = usePolling(fn, { enabled: false, immediate: false })

    start()
    expect(fn).not.toHaveBeenCalled()
  })

  it('start 后应按 interval 周期性调用 fetchFn', () => {
    const fn = vi.fn()
    const { start } = usePolling(fn, { enabled: false, immediate: false, interval: 1000 })

    start()
    expect(fn).not.toHaveBeenCalled() // immediate=false

    vi.advanceTimersByTime(1000)
    expect(fn).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(1000)
    expect(fn).toHaveBeenCalledTimes(2)
  })

  it('stop 后应停止轮询', () => {
    const fn = vi.fn()
    const { start, stop } = usePolling(fn, { enabled: false, immediate: false, interval: 500 })

    start()
    vi.advanceTimersByTime(500)
    expect(fn).toHaveBeenCalledTimes(1)

    stop()
    vi.advanceTimersByTime(2000)
    // 应该只被调用了 1 次（stop 后不再触发）
    expect(fn).toHaveBeenCalledTimes(1)
  })
})
