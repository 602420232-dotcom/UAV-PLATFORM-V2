<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch, shallowRef } from 'vue'
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
  xData: string[]
  series: Array<{
    name: string
    data: number[]
    color?: string
    smooth?: boolean
    areaStyle?: boolean
  }>
  height?: string
  showLegend?: boolean
  showDataZoom?: boolean
}>(), {
  title: '',
  height: '350px',
  showLegend: true,
  showDataZoom: false,
})

const chartRef = ref<HTMLDivElement>()
const chartInstance = shallowRef<echarts.ECharts>()

function initChart() {
  if (!chartRef.value) return
  chartInstance.value = echarts.init(chartRef.value)
  updateChart()
}

function updateChart() {
  if (!chartInstance.value) return

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
      textStyle: { color: '#e0e0e0' },
    },
    legend: props.showLegend
      ? {
          textStyle: { color: '#a0a0b0' },
          top: props.title ? 30 : 5,
        }
      : undefined,
    grid: {
      left: '3%',
      right: '4%',
      bottom: props.showDataZoom ? '15%' : '3%',
      top: props.title ? 60 : 40,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: props.xData,
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0' },
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0' },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    dataZoom: props.showDataZoom
      ? [
          {
            type: 'inside',
            start: 0,
            end: 100,
          },
          {
            type: 'slider',
            start: 0,
            end: 100,
            backgroundColor: '#1a1a2e',
            borderColor: '#2a2a40',
            fillerColor: 'rgba(15, 52, 96, 0.3)',
            textStyle: { color: '#a0a0b0' },
          },
        ]
      : undefined,
    series: props.series.map((s) => ({
      name: s.name,
      type: 'line',
      data: s.data,
      smooth: s.smooth ?? true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { color: s.color || '#e94560', width: 2 },
      itemStyle: { color: s.color || '#e94560' },
      areaStyle: s.areaStyle
        ? {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: (s.color || '#e94560') + '40' },
              { offset: 1, color: (s.color || '#e94560') + '05' },
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

watch(
  () => [props.xData, props.series],
  () => {
    updateChart()
  },
  { deep: true }
)

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance.value?.dispose()
})
</script>

<template>
  <div ref="chartRef" :style="{ width: '100%', height }"></div>
</template>
