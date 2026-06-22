<script setup lang="ts">
import { ref, shallowRef, onMounted, onUnmounted, watch, computed } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart as LineChartSeries } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  DataZoomComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'

echarts.use([
  LineChartSeries,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  DataZoomComponent,
  CanvasRenderer,
])

const props = withDefaults(defineProps<{
  title?: string
  metricType: 'qps' | 'latency' | 'error-rate' | 'cpu' | 'memory'
  height?: string
  autoRefreshInterval?: number
}>(), {
  title: '',
  height: '350px',
  autoRefreshInterval: 30000,
})

const chartRef = ref<HTMLDivElement>()
const chartInstance = shallowRef<echarts.ECharts>()
const selectedRange = ref('1h')
const refreshTimer = ref<ReturnType<typeof setInterval>>()

const timeRangeOptions = [
  { label: '1h', value: '1h' },
  { label: '6h', value: '6h' },
  { label: '24h', value: '24h' },
  { label: '7d', value: '7d' },
]

const metricConfig: Record<string, {
  label: string
  unit: string
  series: Array<{ name: string; color: string; area?: boolean }>
}> = {
  qps: {
    label: 'QPS (请求/秒)',
    unit: 'req/s',
    series: [{ name: 'QPS', color: '#409eff' }],
  },
  latency: {
    label: '延迟 (ms)',
    unit: 'ms',
    series: [
      { name: 'P50', color: '#67c23a' },
      { name: 'P95', color: '#e6a23c' },
      { name: 'P99', color: '#f56c6c' },
    ],
  },
  'error-rate': {
    label: '错误率 (%)',
    unit: '%',
    series: [{ name: '错误率', color: '#f56c6c' }],
  },
  cpu: {
    label: 'CPU 使用率 (%)',
    unit: '%',
    series: [{ name: 'CPU', color: '#e94560', area: true }],
  },
  memory: {
    label: '内存使用 (GB)',
    unit: 'GB',
    series: [{ name: '内存', color: '#9b59b6', area: true }],
  },
}

const currentConfig = computed(() => metricConfig[props.metricType])

function generateMockData(count: number): { timestamps: string[]; seriesData: number[][] } {
  const timestamps: string[] = []
  const seriesData: number[][] = (currentConfig.value?.series ?? []).map(() => [])
  const now = Date.now()
  const rangeMs = getTimeRangeMs(selectedRange.value)
  const interval = rangeMs / count

  for (let i = 0; i < count; i++) {
    const t = new Date(now - rangeMs + i * interval)
    timestamps.push(t.toLocaleTimeString('zh-CN', { hour12: false }))
    for (let s = 0; s < seriesData.length; s++) {
      const base = getBaseValue(props.metricType, s)
      seriesData[s]?.push(base + (Math.random() - 0.5) * base * 0.3)
    }
  }
  return { timestamps, seriesData }
}

function getBaseValue(type: string, seriesIndex: number): number {
  const bases: Record<string, number[]> = {
    qps: [1200],
    latency: [12, 45, 120],
    'error-rate': [0.5],
    cpu: [65],
    memory: [4.2],
  }
  return (bases[type] || [100])[seriesIndex] || 100
}

function getTimeRangeMs(range: string): number {
  const map: Record<string, number> = {
    '1h': 3600000,
    '6h': 21600000,
    '24h': 86400000,
    '7d': 604800000,
  }
  return map[range] || 3600000
}

function initChart() {
  if (!chartRef.value) return
  chartInstance.value = echarts.init(chartRef.value)
  updateChart()
}

function updateChart() {
  if (!chartInstance.value) return

  const { timestamps, seriesData } = generateMockData(60)
  const config = currentConfig.value!
  if (!config) return

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    title: props.title
      ? {
          text: props.title,
          textStyle: { color: '#e0e0e0', fontSize: 14 },
          left: 10,
          top: 5,
        }
      : undefined,
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0', fontSize: 12 },
      formatter: (params: any) => {
        let html = `<div style="font-weight:600;margin-bottom:4px">${params[0].axisValue}</div>`
        for (const p of params) {
          html += `<div style="display:flex;align-items:center;gap:6px">
            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color}"></span>
            <span>${p.seriesName}:</span>
            <span style="font-weight:600">${p.value.toFixed(2)} ${config?.unit ?? ''}</span>
          </div>`
        }
        return html
      },
    },
    legend: config.series.length > 1
      ? {
          textStyle: { color: '#a0a0b0' },
          top: props.title ? 30 : 5,
        }
      : undefined,
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: props.title ? 60 : 40,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: timestamps,
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: {
        color: '#a0a0b0',
        fontSize: 11,
        interval: 'auto',
        rotate: selectedRange.value === '7d' ? 45 : 0,
      },
    },
    yAxis: {
      type: 'value',
      name: config.unit,
      nameTextStyle: { color: '#a0a0b0', fontSize: 11 },
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0', fontSize: 11 },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    series: (config?.series ?? []).map((s, idx) => ({
      name: s.name,
      type: 'line',
      data: seriesData[idx],
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      showSymbol: false,
      lineStyle: { color: s.color, width: 2 },
      itemStyle: { color: s.color },
      areaStyle: s.area
        ? {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: s.color + '40' },
              { offset: 1, color: s.color + '05' },
            ]),
          }
        : undefined,
    })),
  }

  chartInstance.value.setOption(option, true)
}

function handleResize() {
  chartInstance.value?.resize()
}

function handleRangeChange() {
  updateChart()
}

function startAutoRefresh() {
  stopAutoRefresh()
  if (props.autoRefreshInterval > 0) {
    refreshTimer.value = setInterval(() => {
      updateChart()
    }, props.autoRefreshInterval)
  }
}

function stopAutoRefresh() {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = undefined
  }
}

watch(
  () => props.metricType,
  () => updateChart()
)

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
  window.removeEventListener('resize', handleResize)
  chartInstance.value?.dispose()
})
</script>

<template>
  <div class="metric-chart">
    <div class="chart-toolbar">
      <div class="toolbar-left">
        <span class="metric-label">
          {{ currentConfig?.label ?? '' }}
        </span>
      </div>
      <div class="toolbar-right">
        <el-radio-group
          v-model="selectedRange"
          size="small"
          @change="handleRangeChange"
        >
          <el-radio-button
            v-for="opt in timeRangeOptions"
            :key="opt.value"
            :value="opt.value"
          >
            {{ opt.label }}
          </el-radio-button>
        </el-radio-group>
      </div>
    </div>
    <div ref="chartRef" :style="{ width: '100%', height }"></div>
  </div>
</template>

<style scoped>
.metric-chart {
  background: var(--color-bg-secondary, #1a1a2e);
  border-radius: 8px;
  border: 1px solid var(--color-border, #2a2a40);
  overflow: hidden;
}

.chart-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-border, #2a2a40);
}

.toolbar-left {
  display: flex;
  align-items: center;
}

.metric-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary, #e0e0e0);
}

.toolbar-right :deep(.el-radio-button__inner) {
  background: var(--color-bg-input, #16213e);
  border-color: var(--color-border, #2a2a40);
  color: var(--color-text-secondary, #a0a0b0);
  padding: 5px 12px;
}

.toolbar-right :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: var(--color-primary, #e94560);
  border-color: var(--color-primary, #e94560);
  color: #fff;
}
</style>
