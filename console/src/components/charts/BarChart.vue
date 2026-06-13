<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch, shallowRef } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart as BarChartSeries } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'

echarts.use([
  BarChartSeries,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  CanvasRenderer,
])

const props = withDefaults(defineProps<{
  title?: string
  xData: string[]
  series: Array<{
    name: string
    data: number[]
    color?: string
  }>
  height?: string
  showLegend?: boolean
  horizontal?: boolean
}>(), {
  title: '',
  height: '350px',
  showLegend: true,
  horizontal: false,
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
      axisPointer: { type: 'shadow' },
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
      bottom: '3%',
      top: props.title ? 60 : 40,
      containLabel: true,
    },
    xAxis: props.horizontal
      ? {
          type: 'value',
          axisLine: { lineStyle: { color: '#2a2a40' } },
          axisLabel: { color: '#a0a0b0' },
          splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
        }
      : {
          type: 'category',
          data: props.xData,
          axisLine: { lineStyle: { color: '#2a2a40' } },
          axisLabel: { color: '#a0a0b0' },
        },
    yAxis: props.horizontal
      ? {
          type: 'category',
          data: props.xData,
          axisLine: { lineStyle: { color: '#2a2a40' } },
          axisLabel: { color: '#a0a0b0' },
        }
      : {
          type: 'value',
          axisLine: { lineStyle: { color: '#2a2a40' } },
          axisLabel: { color: '#a0a0b0' },
          splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
        },
    series: props.series.map((s) => ({
      name: s.name,
      type: 'bar',
      data: s.data,
      barMaxWidth: 40,
      itemStyle: {
        color: s.color || '#0f3460',
        borderRadius: props.horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0],
      },
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
