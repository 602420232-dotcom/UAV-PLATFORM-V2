// 可视化工具类

import * as echarts from 'echarts'
import L from 'leaflet'
import 'leaflet.heat'

// ECharts 图表实例注册表 (用于正确清理 resize 事件)
const chartRegistry = new Map()

function registerChart(chart) {
  const resizeHandler = () => {
    try { chart.resize() } catch (e) { /* chart already disposed */ }
  }
  chartRegistry.set(chart, resizeHandler)
  window.addEventListener('resize', resizeHandler)
  return chart
}

function unregisterChart(chart) {
  const resizeHandler = chartRegistry.get(chart)
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler)
    chartRegistry.delete(chart)
  }
}

/**
 * 初始化地图
 * @param {string} containerId - 容器ID
 * @param {Object} options - 配置选项
 * @returns {L.Map} 地图实例
 */
export function initMap(containerId, options = {}) {
  const defaultOptions = {
    center: [39.9042, 116.4074],
    zoom: 13,
    minZoom: 10,
    maxZoom: 18
  }
  
  const mergedOptions = { ...defaultOptions, ...options }
  
  const map = L.map(containerId).setView(mergedOptions.center, mergedOptions.zoom)
  
  // 添加底图
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map)
  
  return map
}

/**
 * 添加无人机标记
 * @param {L.Map} map - 地图实例
 * @param {Object} drone - 无人机数据
 * @returns {L.Marker} 标记实例
 */
export function addDroneMarker(map, drone) {
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
 * @param {L.Map} map - 地图实例
 * @param {Array} path - 路径点数组
 * @param {Object} options - 配置选项
 * @returns {L.Polyline} 路径实例
 */
export function addPath(map, path, options = {}) {
  const defaultOptions = {
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
 * @param {L.Map} map - 地图实例
 * @param {Object} task - 任务数据
 * @returns {L.Marker} 标记实例
 */
export function addTaskMarker(map, task) {
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
 * @param {L.Map} map - 地图实例
 * @param {Object} obstacle - 障碍物数据
 * @returns {L.Circle} 圆形实例
 */
export function addObstacle(map, obstacle) {
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
 * @param {string} containerId - 容器ID
 * @param {Object} options - 配置选项
 * @returns {echarts.ECharts} 图表实例
 */
export function initLineChart(containerId, options = {}) {
  const chart = echarts.init(document.getElementById(containerId))
  
  const defaultOptions = {
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
 * @param {string} containerId - 容器ID
 * @param {Object} options - 配置选项
 * @returns {echarts.ECharts} 图表实例
 */
export function initBarChart(containerId, options = {}) {
  const chart = echarts.init(document.getElementById(containerId))
  
  const defaultOptions = {
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
 * @param {string} containerId - 容器ID
 * @param {Object} options - 配置选项
 * @returns {echarts.ECharts} 图表实例
 */
export function initPieChart(containerId, options = {}) {
  const chart = echarts.init(document.getElementById(containerId))
  
  const defaultOptions = {
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
 * @param {string} containerId - 容器ID
 * @param {Object} options - 配置选项
 * @returns {echarts.ECharts} 图表实例
 */
export function initHeatmapChart(containerId, options = {}) {
  const chart = echarts.init(document.getElementById(containerId))
  
  const defaultOptions = {
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
 * @param {string} containerId - 容器ID
 * @param {Object} options - 配置选项
 * @returns {echarts.ECharts} 图表实例
 */
export function initRadarChart(containerId, options = {}) {
  const chart = echarts.init(document.getElementById(containerId))
  
  const defaultOptions = {
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
 * @param {string} containerId - 容器ID
 * @param {Object} options - 配置选项
 * @returns {echarts.ECharts} 图表实例
 */
export function initGaugeChart(containerId, options = {}) {
  const chart = echarts.init(document.getElementById(containerId))
  
  const defaultOptions = {
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
        formatter: function (value) {
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
        formatter: function (value) {
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
 * @param {L.Map} map - 地图实例
 * @param {Object} zone - 禁飞区数据 { id, name, center: [lat,lng], radius, type: 'circle'|'polygon', points }
 * @returns {L.Circle|L.Polygon} 图层实例
 */
export function addNoFlyZone(map, zone) {
  let layer
  const baseOptions = {
    color: '#ff0000',
    fillColor: '#ff0000',
    fillOpacity: 0.2,
    weight: 2
  }

  if (zone.type === 'circle') {
    layer = L.circle(zone.center, {
      ...baseOptions,
      radius: zone.radius
    }).addTo(map)
  } else if (zone.type === 'polygon') {
    layer = L.polygon(zone.points, baseOptions).addTo(map)
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
 * @param {L.Map} map - 地图实例
 * @param {Array} data - 热力图数据 [[lat, lng, intensity], ...]
 * @param {Object} options - 配置选项 { radius, blur, maxZoom, gradient }
 * @returns {L.HeatLayer} 热力图实例
 */
export function addWeatherHeatmap(map, data, options = {}) {
  const defaultOptions = {
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
 * @param {number} risk - 风险值 0-10
 * @returns {string} 颜色值
 */
function getRiskColor(risk) {
  if (risk < 3) return '#52c41a'
  if (risk < 6) return '#fa8c16'
  if (risk < 8) return '#f5222d'
  return '#a8071a'
}

/**
 * 获取风险等级文本
 * @param {number} risk - 风险值 0-10
 * @returns {string} 等级描述
 */
function getRiskLevelText(risk) {
  if (risk < 3) return '低'
  if (risk < 6) return '中'
  if (risk < 8) return '高'
  return '极高'
}

/**
 * 添加风险标注路径
 * @param {L.Map} map - 地图实例
 * @param {Array} segments - 路径段数组 [{ points: [[lat,lng],...], risk: number }]
 * @param {Object} options - 配置选项（预留）
 * @returns {Object} { layers: L.Polyline[], legend: L.Control }
 */
export function addRiskPath(map, segments, options = {}) {
  const layers = []

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
 * @param {echarts.ECharts} chart - 图表实例
 */
export function destroyChart(chart) {
  if (chart) {
    unregisterChart(chart)
    chart.dispose()
  }
}

/**
 * 销毁地图
 * @param {L.Map} map - 地图实例
 */
export function destroyMap(map) {
  if (map) {
    map.remove()
  }
}
