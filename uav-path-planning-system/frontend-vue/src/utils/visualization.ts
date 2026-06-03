// 可视化工具类

import * as echarts from 'echarts'
import L from 'leaflet'
import 'leaflet.heat'

// ── Type Definitions ──────────────────────────────────────────────────────────

interface DroneData {
  id: string
  latitude: number
  longitude: number
  status: string
  batteryLevel: number
  [key: string]: any
}

interface TaskData {
  id: number | string
  location: [number, number]
  demand: string
  startTime: string
  endTime: string
  [key: string]: any
}

interface ObstacleData {
  location: [number, number]
  radius: number
  [key: string]: any
}

interface NoFlyZone {
  id?: string | number
  name?: string
  center?: [number, number]
  radius?: number
  type: 'circle' | 'polygon'
  points?: Array<[number, number]>
}

type HeatmapDataPoint = [number, number, number]

interface PathSegment {
  points: Array<[number, number]>
  risk: number
}

interface RiskPathResult {
  layers: L.Polyline[]
  legend: L.Control
}

interface MapOptions {
  center?: [number, number]
  zoom?: number
  minZoom?: number
  maxZoom?: number
}

interface PathOptions {
  color?: string
  weight?: number
  opacity?: number
}

interface HeatmapOptions {
  radius?: number
  blur?: number
  maxZoom?: number
  gradient?: Record<number, string>
}

// ECharts 图表实例注册表 (用于正确清理 resize 事件)
const chartRegistry = new Map<echarts.ECharts, () => void>()

function registerChart(chart: echarts.ECharts): echarts.ECharts {
  const resizeHandler = () => {
    try { chart.resize() } catch (e) { /* chart already disposed */ }
  }
  chartRegistry.set(chart, resizeHandler)
  window.addEventListener('resize', resizeHandler)
  return chart
}

function unregisterChart(chart: echarts.ECharts): void {
  const resizeHandler = chartRegistry.get(chart)
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
    chartRegistry.delete(chart)
  }
}

/**
 * 初始化地图
 * @param containerId - 容器ID
 * @param options - 配置选项
 */
export function initMap(containerId: string, options: MapOptions = {}): L.Map {
  const defaultOptions: MapOptions = {
    center: [39.9042, 116.4074],
    zoom: 13,
    minZoom: 10,
    maxZoom: 18
  }

  const mergedOptions = { ...defaultOptions, ...options }

  const map = L.map(containerId).setView(mergedOptions.center!, mergedOptions.zoom!)

  // 添加底图
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map)

  return map
}

/**
 * 添加无人机标记
 * @param map - 地图实例
 * @param drone - 无人机数据
 */
export function addDroneMarker(map: L.Map, drone: DroneData): L.Marker {
  const icon = L.divIcon({
    className: 'drone-marker',
    html: `<div style="width: 30px; height: 30px; background: #1890ff; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">${drone.id.charAt(0)}</div>`,
    iconSize: [30, 30]
  })

  const marker = L.marker([drone.latitude, drone.longitude], { icon })
    .addTo(map)
    .bindPopup(`<b>无人机 ${drone.id}</b><br>状态: ${drone.status}<br>电量: ${drone.batteryLevel}%`)

  return marker
}

/**
 * 添加路径
 * @param map - 地图实例
 * @param path - 路径点数组
 * @param options - 配置选项
 */
export function addPath(map: L.Map, path: Array<[number, number]>, options: PathOptions = {}): L.Polyline {
  const defaultOptions: PathOptions = {
    color: '#1890ff',
    weight: 3,
    opacity: 0.8
  }

  const mergedOptions = { ...defaultOptions, ...options }

  const polyline = L.polyline(path, mergedOptions).addTo(map)

  return polyline
}

/**
 * 添加任务点
 * @param map - 地图实例
 * @param task - 任务数据
 */
export function addTaskMarker(map: L.Map, task: TaskData): L.Marker {
  const icon = L.divIcon({
    className: 'task-marker',
    html: `<div style="width: 20px; height: 20px; background: #52c41a; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">${String(task.id).charAt(0)}</div>`,
    iconSize: [20, 20]
  })

  const marker = L.marker([task.location[0], task.location[1]], { icon })
    .addTo(map)
    .bindPopup(`<b>任务 ${task.id}</b><br>需求: ${task.demand}<br>时间窗: ${task.startTime} - ${task.endTime}`)

  return marker
}

/**
 * 添加障碍物
 * @param map - 地图实例
 * @param obstacle - 障碍物数据
 */
export function addObstacle(map: L.Map, obstacle: ObstacleData): L.Circle {
  const circle = L.circle([obstacle.location[0], obstacle.location[1]], {
    color: '#ff4d4f',
    fillColor: '#ff4d4f',
    fillOpacity: 0.5,
    radius: obstacle.radius
  }).addTo(map)
    .bindPopup(`<b>障碍物</b><br>半径: ${obstacle.radius}m`)

  return circle
}

/**
 * 初始化折线图
 * @param containerId - 容器ID
 * @param options - 配置选项
 */
export function initLineChart(containerId: string, options: echarts.EChartsOption = {}): echarts.ECharts {
  const chart = echarts.init(document.getElementById(containerId)!)

  const defaultOptions: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['数据']
    },
    xAxis: {
      type: 'category',
      data: []
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      name: '数据',
      type: 'line',
      data: []
    }]
  }

  const mergedOptions = { ...defaultOptions, ...options }
  chart.setOption(mergedOptions)

  return registerChart(chart)
}

/**
 * 初始化柱状图
 * @param containerId - 容器ID
 * @param options - 配置选项
 */
export function initBarChart(containerId: string, options: echarts.EChartsOption = {}): echarts.ECharts {
  const chart = echarts.init(document.getElementById(containerId)!)

  const defaultOptions: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['数据']
    },
    xAxis: {
      type: 'category',
      data: []
    },
    yAxis: {
      type: 'value'
    },
    series: [{
      name: '数据',
      type: 'bar',
      data: []
    }]
  }

  const mergedOptions = { ...defaultOptions, ...options }
  chart.setOption(mergedOptions)

  return registerChart(chart)
}

/**
 * 初始化饼图
 * @param containerId - 容器ID
 * @param options - 配置选项
 */
export function initPieChart(containerId: string, options: echarts.EChartsOption = {}): echarts.ECharts {
  const chart = echarts.init(document.getElementById(containerId)!)

  const defaultOptions: echarts.EChartsOption = {
    tooltip: {
      trigger: 'item'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [{
      name: '数据',
      type: 'pie',
      radius: '50%',
      data: [],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }

  const mergedOptions = { ...defaultOptions, ...options }
  chart.setOption(mergedOptions)

  return registerChart(chart)
}

/**
 * 初始化热力图
 * @param containerId - 容器ID
 * @param options - 配置选项
 */
export function initHeatmapChart(containerId: string, options: echarts.EChartsOption = {}): echarts.ECharts {
  const chart = echarts.init(document.getElementById(containerId)!)

  const defaultOptions: echarts.EChartsOption = {
    tooltip: {
      position: 'top'
    },
    grid: {
      height: '50%',
      top: '10%'
    },
    xAxis: {
      type: 'category',
      data: [],
      splitArea: {
        show: true
      }
    },
    yAxis: {
      type: 'category',
      data: [],
      splitArea: {
        show: true
      }
    },
    visualMap: {
      min: 0,
      max: 100,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '5%'
    },
    series: [{
      name: '热力图',
      type: 'heatmap',
      data: [],
      label: {
        show: true
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }

  const mergedOptions = { ...defaultOptions, ...options }
  chart.setOption(mergedOptions)

  return registerChart(chart)
}

/**
 * 初始化雷达图
 * @param containerId - 容器ID
 * @param options - 配置选项
 */
export function initRadarChart(containerId: string, options: echarts.EChartsOption = {}): echarts.ECharts {
  const chart = echarts.init(document.getElementById(containerId)!)

  const defaultOptions: echarts.EChartsOption = {
    tooltip: {},
    legend: {
      data: ['数据']
    },
    radar: {
      indicator: []
    },
    series: [{
      name: '数据',
      type: 'radar',
      data: []
    }]
  }

  const mergedOptions = { ...defaultOptions, ...options }
  chart.setOption(mergedOptions)

  return registerChart(chart)
}

/**
 * 初始化仪表盘
 * @param containerId - 容器ID
 * @param options - 配置选项
 */
export function initGaugeChart(containerId: string, options: echarts.EChartsOption = {}): echarts.ECharts {
  const chart = echarts.init(document.getElementById(containerId)!)

  const defaultOptions: echarts.EChartsOption = {
    series: [{
      type: 'gauge',
      startAngle: 180,
      endAngle: 0,
      min: 0,
      max: 100,
      splitNumber: 8,
      axisLine: {
        lineStyle: {
          width: 6,
          color: [[0.3, '#67e0e3'], [0.7, '#37a2da'], [1, '#67e0e3']]
        }
      },
      pointer: {
        icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
        length: '12%',
        width: 20,
        offsetCenter: [0, '-60%'],
        itemStyle: {
          color: 'inherit'
        }
      },
      axisTick: {
        length: 12,
        lineStyle: {
          color: 'inherit',
          width: 2
        }
      },
      splitLine: {
        length: 20,
        lineStyle: {
          color: 'inherit',
          width: 5
        }
      },
      axisLabel: {
        color: '#464646',
        fontSize: 16,
        distance: -60,
        formatter: function (value: number) {
          if (value === 0 || value === 100) {
            return value;
          }
          return '';
        }
      },
      title: {
        offsetCenter: [0, '-10%'],
        fontSize: 20
      },
      detail: {
        fontSize: 30,
        offsetCenter: [0, '-35%'],
        valueAnimation: true,
        formatter: function (value: number) {
          return Math.round(value) + '%';
        },
        color: 'inherit'
      },
      data: [{
        value: 50,
        name: '数据'
      }]
    }]
  }

  const mergedOptions = { ...defaultOptions, ...options }
  chart.setOption(mergedOptions)

  return registerChart(chart)
}

// ──────────────────────────────────────────────
// Feature 1: 禁飞区可视化
// ──────────────────────────────────────────────

/**
 * 添加禁飞区
 * @param map - 地图实例
 * @param zone - 禁飞区数据 { id, name, center: [lat,lng], radius, type: 'circle'|'polygon', points }
 */
export function addNoFlyZone(map: L.Map, zone: NoFlyZone): L.Circle | L.Polygon | undefined {
  let layer: L.Circle | L.Polygon | undefined
  const baseOptions = {
    color: '#ff0000',
    fillColor: '#ff0000',
    fillOpacity: 0.2,
    weight: 2
  }

  if (zone.type === 'circle') {
    layer = L.circle(zone.center!, {
      ...baseOptions,
      radius: zone.radius
    }).addTo(map)
  } else if (zone.type === 'polygon') {
    layer = L.polygon(zone.points!, baseOptions).addTo(map)
  }

  if (layer) {
    layer.bindPopup([
      '<b>🚫 禁飞区: ' + (zone.name || '未命名') + '</b>',
      '<hr>',
      '<b>ID:</b> ' + (zone.id || '-'),
      '<b>类型:</b> ' + (zone.type === 'circle' ? '圆形' : '多边形'),
      '<b>限制:</b> 禁止无人机飞入'
    ].join('<br>'))
  }

  return layer
}

// ──────────────────────────────────────────────
// Feature 2: 气象热力图
// ──────────────────────────────────────────────

/**
 * 添加气象热力图
 * @param map - 地图实例
 * @param data - 热力图数据 [[lat, lng, intensity], ...]
 * @param options - 配置选项 { radius, blur, maxZoom, gradient }
 */
export function addWeatherHeatmap(map: L.Map, data: HeatmapDataPoint[], options: HeatmapOptions = {}): L.HeatLayer {
  const defaultOptions: HeatmapOptions = {
    radius: 25,
    blur: 15,
    maxZoom: 17,
    gradient: {
      0.0: '#00ff00',
      0.3: '#ffff00',
      0.6: '#ff8800',
      0.9: '#ff0000',
      1.0: '#880000'
    }
  }

  const mergedOptions = { ...defaultOptions, ...options }

  const heatLayer = L.heatLayer(data, mergedOptions).addTo(map)

  return heatLayer
}

// ──────────────────────────────────────────────
// Feature 3: 风险标注路径
// ──────────────────────────────────────────────

/**
 * 获取风险等级对应颜色
 * @param risk - 风险值 0-10
 */
function getRiskColor(risk: number): string {
  if (risk < 3) return '#52c41a'
  if (risk < 6) return '#fa8c16'
  if (risk < 8) return '#f5222d'
  return '#a8071a'
}

/**
 * 获取风险等级文本
 * @param risk - 风险值 0-10
 */
function getRiskLevelText(risk: number): string {
  if (risk < 3) return '低'
  if (risk < 6) return '中'
  if (risk < 8) return '高'
  return '极高'
}

/**
 * 添加风险标注路径
 * @param map - 地图实例
 * @param segments - 路径段数组 [{ points: [[lat,lng],...], risk: number }]
 * @param options - 配置选项（预留）
 */
export function addRiskPath(map: L.Map, segments: PathSegment[], options: Record<string, any> = {}): RiskPathResult {
  const layers: L.Polyline[] = []

  // 渲染每个路径段
  segments.forEach((segment) => {
    const risk = Math.max(0, Math.min(10, segment.risk))
    const color = getRiskColor(risk)
    const weight = 2 + risk / 3

    const polyline = L.polyline(segment.points, {
      color: color,
      weight: weight,
      opacity: 0.8
    }).addTo(map)

    polyline.bindPopup([
      '<b>路径段</b>',
      '<b>风险等级:</b> ' + risk.toFixed(1) + '/10',
      '<b>风险级别:</b> ' + getRiskLevelText(risk)
    ].join('<br>'))

    layers.push(polyline)
  })

  // 创建图例控件
  const LegendControl = L.Control.extend({
    onAdd: function () {
      const div = L.DomUtil.create('div', 'risk-legend')
      div.style.cssText = [
        'background: white',
        'padding: 10px',
        'border-radius: 4px',
        'box-shadow: 0 2px 6px rgba(0,0,0,0.3)',
        'font-size: 13px',
        'line-height: 1.6'
      ].join(';')
      div.innerHTML = [
        '<div style="font-weight:bold;margin-bottom:6px;">风险等级</div>',
        '<div><span style="display:inline-block;width:16px;height:16px;background:#52c41a;margin-right:6px;border-radius:2px;vertical-align:middle;"></span>0-3 低风险</div>',
        '<div><span style="display:inline-block;width:16px;height:16px;background:#fa8c16;margin-right:6px;border-radius:2px;vertical-align:middle;"></span>3-6 中风险</div>',
        '<div><span style="display:inline-block;width:16px;height:16px;background:#f5222d;margin-right:6px;border-radius:2px;vertical-align:middle;"></span>6-8 高风险</div>',
        '<div><span style="display:inline-block;width:16px;height:16px;background:#a8071a;margin-right:6px;border-radius:2px;vertical-align:middle;"></span>8-10 极高风险</div>'
      ].join('')
      return div
    }
  })

  const legend = new LegendControl({ position: 'bottomright' })
  legend.addTo(map)

  return { layers: layers, legend: legend }
}

/**
 * 销毁图表
 * @param chart - 图表实例
 */
export function destroyChart(chart: echarts.ECharts): void {
  if (chart) {
    unregisterChart(chart)
    chart.dispose()
  }
}

/**
 * 销毁地图
 * @param map - 地图实例
 */
export function destroyMap(map: L.Map): void {
  if (map) {
    map.remove()
  }
}
