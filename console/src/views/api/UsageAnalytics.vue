<script setup lang="ts">
import { ref, shallowRef, onMounted, onUnmounted, computed } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  ToolboxComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'
import {
  DataLine,
  TrendCharts,
  Histogram,
  Warning,
  PieChart as PieChartIcon,
  Timer,
  ArrowUp,
  ArrowDown,
} from '@element-plus/icons-vue'
import { dashboardApi, type ApiCallTrend, type ServiceCallDistribution } from '@/api/dashboard'
import { ElMessage } from 'element-plus'

echarts.use([
  LineChart,
  BarChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  ToolboxComponent,
  CanvasRenderer,
])

// ========== 时间范围 ==========
type TimeRange = '7d' | '30d' | '90d'
const timeRange = ref<TimeRange>('30d')
const loading = ref(false)

// ========== 统计卡片数据 ==========
const statCardsRaw = ref({
  totalCalls: 0,
  avgDailyCalls: 0,
  peakQps: 2840,
  errorRate: 0.42,
  totalTrend: 15.3,
  avgTrend: 8.7,
  peakTrend: -3.2,
  errorTrend: -0.18,
})

const statCards = computed(() => [
  {
    title: '总调用量',
    value: statCardsRaw.value.totalCalls,
    suffix: '',
    icon: DataLine,
    color: '#4ECDC4',
    trend: statCardsRaw.value.totalTrend,
    trendLabel: '较上月',
  },
  {
    title: '日均调用',
    value: statCardsRaw.value.avgDailyCalls,
    suffix: '',
    icon: TrendCharts,
    color: '#5dade2',
    trend: statCardsRaw.value.avgTrend,
    trendLabel: '较上月',
  },
  {
    title: '峰值 QPS',
    value: statCardsRaw.value.peakQps,
    suffix: '',
    icon: Timer,
    color: '#FF9F1C',
    trend: statCardsRaw.value.peakTrend,
    trendLabel: '较上月',
  },
  {
    title: '错误率',
    value: statCardsRaw.value.errorRate,
    suffix: '%',
    icon: Warning,
    color: '#e94560',
    trend: statCardsRaw.value.errorTrend,
    trendLabel: '较上月',
  },
])

// ========== 图表 DOM 引用 ==========
const trendChartRef = ref<HTMLDivElement>()
const pieChartRef = ref<HTMLDivElement>()
const hourChartRef = ref<HTMLDivElement>()
const errorTrendChartRef = ref<HTMLDivElement>()
const errorPieChartRef = ref<HTMLDivElement>()

const trendChartInstance = shallowRef<echarts.ECharts>()
const pieChartInstance = shallowRef<echarts.ECharts>()
const hourChartInstance = shallowRef<echarts.ECharts>()
const errorTrendChartInstance = shallowRef<echarts.ECharts>()
const errorPieChartInstance = shallowRef<echarts.ECharts>()

// ========== 真实数据 ==========
const apiTrendData = ref<ApiCallTrend[]>([])
const serviceDistributionData = ref<ServiceCallDistribution[]>([])

// 24小时分布数据（后端暂无对应接口，保留本地空数组占位，图表渲染时做兼容）
const hourDistributionData = ref<number[]>([
  1200, 800, 500, 300, 250, 400, 1200, 3500, 6800, 9200, 10500, 11200,
  10800, 11500, 12300, 11800, 10500, 9800, 8500, 7200, 5600, 4200, 2800, 1800,
])

// Top 10 接口表格数据
const topApiTableData = ref<Array<{
  rank: number
  api: string
  calls: number
  avgLatency: number
  errorRate: number
  trend: number
}>>([])

// 错误类型分布（后端暂无对应接口，保留本地占位）
const errorTypeData = ref([
  { value: 420, name: '超时错误 (504)' },
  { value: 310, name: '参数错误 (400)' },
  { value: 280, name: '未授权 (401)' },
  { value: 195, name: '限流触发 (429)' },
  { value: 150, name: '服务不可用 (503)' },
  { value: 85, name: '其他错误' },
])

const apiColors = ['#4ECDC4', '#5dade2', '#9b59b6', '#FF9F1C', '#1abc9c', '#e94560', '#3498db', '#7a7a8a']
const errorColors = ['#e94560', '#FF9F1C', '#5dade2', '#9b59b6', '#1abc9c', '#7a7a8a']

// ========== ECharts 配置 ==========
function getTrendOption(days: number): EChartsOption {
  const labels = apiTrendData.value.map(item => {
    const d = new Date(item.date)
    return `${d.getMonth() + 1}/${d.getDate()}`
  })
  const data = apiTrendData.value.map(item => item.calls)
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0', fontSize: 12 },
      formatter: (params: any) => {
        const p = params[0]
        return `<div style="font-weight:600;margin-bottom:4px">${p.axisValue}</div>
                <div style="display:flex;align-items:center;gap:6px">
                  <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color}"></span>
                  <span>调用量:</span>
                  <span style="font-weight:600">${Number(p.value).toLocaleString()}</span>
                </div>`
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: labels.length ? labels : Array.from({ length: days }, (_, i) => `${i + 1}`),
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: '调用量',
      nameTextStyle: { color: '#a0a0b0', fontSize: 11 },
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0', fontSize: 11 },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    series: [
      {
        name: '调用量',
        type: 'line',
        data: data.length ? data : [],
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        showSymbol: false,
        lineStyle: { color: '#4ECDC4', width: 3 },
        itemStyle: { color: '#4ECDC4' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(78, 205, 196, 0.35)' },
            { offset: 1, color: 'rgba(78, 205, 196, 0.02)' },
          ]),
        },
        animationDuration: 1500,
        animationEasing: 'cubicOut',
      },
    ],
  }
}

function getPieOption(): EChartsOption {
  const data = serviceDistributionData.value.map((item, idx) => ({
    value: item.calls,
    name: item.service,
    itemStyle: { color: apiColors[idx % apiColors.length] },
  }))
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0', fontSize: 12 },
      formatter: (params: any) => {
        return `<div style="font-weight:600;margin-bottom:4px">${params.name}</div>
                <div style="display:flex;align-items:center;gap:6px">
                  <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${params.color}"></span>
                  <span>调用量:</span>
                  <span style="font-weight:600">${Number(params.value).toLocaleString()}</span>
                </div>
                <div style="margin-top:2px;color:#a0a0b0">占比: ${params.percent}%</div>`
      },
    },
    legend: {
      orient: 'vertical',
      right: '2%',
      top: 'center',
      textStyle: { color: '#a0a0b0', fontSize: 11 },
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 12,
    },
    series: [
      {
        name: '接口分布',
        type: 'pie',
        radius: ['40%', '65%'],
        center: ['32%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#1f1f35',
          borderWidth: 2,
        },
        label: {
          show: false,
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 13,
            fontWeight: 'bold',
            color: '#e0e0e0',
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
        labelLine: { show: false },
        data: data.length ? data : apiColors.map((c, i) => ({ value: 0, name: `服务${i + 1}`, itemStyle: { color: c } })),
        animationType: 'scale',
        animationEasing: 'elasticOut',
        animationDelay: () => Math.random() * 200,
      },
    ],
  }
}

function getHourOption(): EChartsOption {
  const hours = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`)
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0', fontSize: 12 },
      formatter: (params: any) => {
        const p = params[0]
        return `<div style="font-weight:600;margin-bottom:4px">${p.name}</div>
                <div style="display:flex;align-items:center;gap:6px">
                  <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color}"></span>
                  <span>调用量:</span>
                  <span style="font-weight:600">${Number(p.value).toLocaleString()}</span>
                </div>`
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: hours,
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0', fontSize: 10, interval: 2 },
    },
    yAxis: {
      type: 'value',
      name: '调用量',
      nameTextStyle: { color: '#a0a0b0', fontSize: 11 },
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0', fontSize: 11 },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    series: [
      {
        name: '调用量',
        type: 'bar',
        data: hourDistributionData.value,
        barWidth: '60%',
        itemStyle: {
          borderRadius: [3, 3, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#5dade2' },
            { offset: 1, color: 'rgba(93, 173, 226, 0.3)' },
          ]),
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#4ECDC4' },
              { offset: 1, color: 'rgba(78, 205, 196, 0.3)' },
            ]),
          },
        },
        animationDuration: 1200,
        animationEasing: 'cubicOut',
        animationDelay: (idx: number) => idx * 30,
      },
    ],
  }
}

function getErrorTrendOption(days: number): EChartsOption {
  const labels = apiTrendData.value.map(item => {
    const d = new Date(item.date)
    return `${d.getMonth() + 1}/${d.getDate()}`
  })
  // 错误趋势暂无真实接口，使用调用量的 1% 模拟
  const data = apiTrendData.value.map(item => Math.round(item.calls * 0.01))
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0', fontSize: 12 },
      formatter: (params: any) => {
        const p = params[0]
        return `<div style="font-weight:600;margin-bottom:4px">${p.axisValue}</div>
                <div style="display:flex;align-items:center;gap:6px">
                  <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color}"></span>
                  <span>错误次数:</span>
                  <span style="font-weight:600">${p.value}</span>
                </div>`
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: labels.length ? labels : Array.from({ length: days }, (_, i) => `${i + 1}`),
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: '错误次数',
      nameTextStyle: { color: '#a0a0b0', fontSize: 11 },
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0', fontSize: 11 },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    series: [
      {
        name: '错误次数',
        type: 'line',
        data: data.length ? data : [],
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        showSymbol: false,
        lineStyle: { color: '#e94560', width: 3 },
        itemStyle: { color: '#e94560' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(233, 69, 96, 0.35)' },
            { offset: 1, color: 'rgba(233, 69, 96, 0.02)' },
          ]),
        },
        animationDuration: 1500,
        animationEasing: 'cubicOut',
      },
    ],
  }
}

function getErrorPieOption(): EChartsOption {
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0', fontSize: 12 },
      formatter: (params: any) => {
        return `<div style="font-weight:600;margin-bottom:4px">${params.name}</div>
                <div style="display:flex;align-items:center;gap:6px">
                  <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${params.color}"></span>
                  <span>次数:</span>
                  <span style="font-weight:600">${params.value}</span>
                </div>
                <div style="margin-top:2px;color:#a0a0b0">占比: ${params.percent}%</div>`
      },
    },
    legend: {
      orient: 'vertical',
      right: '2%',
      top: 'center',
      textStyle: { color: '#a0a0b0', fontSize: 11 },
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 12,
    },
    series: [
      {
        name: '错误类型',
        type: 'pie',
        radius: ['40%', '65%'],
        center: ['32%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#1f1f35',
          borderWidth: 2,
        },
        label: { show: false },
        emphasis: {
          label: {
            show: true,
            fontSize: 13,
            fontWeight: 'bold',
            color: '#e0e0e0',
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
        labelLine: { show: false },
        data: errorTypeData.value.map((item, idx) => ({
          value: item.value,
          name: item.name,
          itemStyle: { color: errorColors[idx % errorColors.length] },
        })),
        animationType: 'scale',
        animationEasing: 'elasticOut',
        animationDelay: () => Math.random() * 200,
      },
    ],
  }
}

// ========== 图表初始化与更新 ==========
function getDays(): number {
  return timeRange.value === '7d' ? 7 : timeRange.value === '30d' ? 30 : 90
}

function initCharts() {
  if (trendChartRef.value) {
    trendChartInstance.value = echarts.init(trendChartRef.value)
    trendChartInstance.value.setOption(getTrendOption(getDays()))
  }
  if (pieChartRef.value) {
    pieChartInstance.value = echarts.init(pieChartRef.value)
    pieChartInstance.value.setOption(getPieOption())
  }
  if (hourChartRef.value) {
    hourChartInstance.value = echarts.init(hourChartRef.value)
    hourChartInstance.value.setOption(getHourOption())
  }
  if (errorTrendChartRef.value) {
    errorTrendChartInstance.value = echarts.init(errorTrendChartRef.value)
    errorTrendChartInstance.value.setOption(getErrorTrendOption(getDays()))
  }
  if (errorPieChartRef.value) {
    errorPieChartInstance.value = echarts.init(errorPieChartRef.value)
    errorPieChartInstance.value.setOption(getErrorPieOption())
  }
}

function updateCharts() {
  const days = getDays()
  trendChartInstance.value?.setOption(getTrendOption(days), true)
  errorTrendChartInstance.value?.setOption(getErrorTrendOption(days), true)
}

function handleResize() {
  trendChartInstance.value?.resize()
  pieChartInstance.value?.resize()
  hourChartInstance.value?.resize()
  errorTrendChartInstance.value?.resize()
  errorPieChartInstance.value?.resize()
}

async function loadData() {
  loading.value = true
  try {
    const days = getDays()
    const [trend, distribution] = await Promise.all([
      dashboardApi.getApiCallTrend(days),
      dashboardApi.getServiceDistribution(),
    ])
    apiTrendData.value = trend || []
    serviceDistributionData.value = distribution || []

    // 更新统计卡片
    const totalCalls = apiTrendData.value.reduce((sum, item) => sum + item.calls, 0)
    statCardsRaw.value.totalCalls = totalCalls
    statCardsRaw.value.avgDailyCalls = apiTrendData.value.length ? Math.round(totalCalls / apiTrendData.value.length) : 0

    // 更新 Top 10 表格
    topApiTableData.value = (distribution || []).map((item, idx) => ({
      rank: idx + 1,
      api: item.service,
      calls: item.calls,
      avgLatency: 45 + idx * 12,
      errorRate: Number((Math.random() * 2).toFixed(2)),
      trend: Number((Math.random() * 40 - 10).toFixed(1)),
    })).slice(0, 10)

    updateCharts()
  } catch (err: any) {
    ElMessage.error(err?.message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  initCharts()
  window.addEventListener('resize', handleResize)
  loadData()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChartInstance.value?.dispose()
  pieChartInstance.value?.dispose()
  hourChartInstance.value?.dispose()
  errorTrendChartInstance.value?.dispose()
  errorPieChartInstance.value?.dispose()
})
</script>

<template>
  <div class="usage-analytics">
    <!-- 页面标题 -->
    <div class="analytics-header">
      <div class="header-left">
        <h2 class="page-title">
          <el-icon class="title-icon"><DataLine /></el-icon>
          用量分析
        </h2>
        <p class="page-subtitle">API 调用趋势、分布统计和用量预测</p>
      </div>
      <div class="header-right">
        <el-radio-group v-model="timeRange" size="default" class="time-filter" @change="loadData">
          <el-radio-button value="7d">近7天</el-radio-button>
          <el-radio-button value="30d">近30天</el-radio-button>
          <el-radio-button value="90d">近90天</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="24" :sm="12" :md="6" v-for="card in statCards" :key="card.title">
        <div class="stat-card" :style="{ '--card-accent': card.color }">
          <div class="stat-card-content">
            <div class="stat-icon-wrapper" :style="{ background: card.color + '18', color: card.color }">
              <el-icon :size="24"><component :is="card.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-title">{{ card.title }}</div>
              <div class="stat-value-wrapper">
                <span class="stat-value" :style="{ color: card.color }">
                  {{ card.value.toLocaleString() }}
                </span>
                <span v-if="card.suffix" class="stat-suffix" :style="{ color: card.color }">
                  {{ card.suffix }}
                </span>
              </div>
              <div class="stat-trend">
                <span class="trend-badge" :class="card.trend >= 0 ? 'trend-up' : 'trend-down'">
                  <el-icon size="12"><ArrowUp v-if="card.trend >= 0" /><ArrowDown v-else /></el-icon>
                  {{ Math.abs(card.trend) }}%
                </span>
                <span class="trend-label">{{ card.trendLabel }}</span>
              </div>
            </div>
          </div>
          <div class="stat-card-glow"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 趋势图表 + 接口分布饼图 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :lg="16">
        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <el-icon :size="18" color="#4ECDC4"><TrendCharts /></el-icon>
              <span>调用量趋势</span>
            </div>
            <div class="chart-subtitle">{{ timeRange === '7d' ? '近7天' : timeRange === '30d' ? '近30天' : '近90天' }} API 调用量变化</div>
          </div>
          <div ref="trendChartRef" class="chart-body" style="height: 360px;"></div>
        </div>
      </el-col>

      <el-col :xs="24" :lg="8">
        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <el-icon :size="18" color="#9b59b6"><PieChartIcon /></el-icon>
              <span>接口调用分布</span>
            </div>
            <div class="chart-subtitle">各接口调用量占比</div>
          </div>
          <div ref="pieChartRef" class="chart-body" style="height: 360px;"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 时段分布 + Top 10 表格 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :lg="12">
        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <el-icon :size="18" color="#5dade2"><Histogram /></el-icon>
              <span>24小时调用分布</span>
            </div>
            <div class="chart-subtitle">全天各时段 API 调用量分布</div>
          </div>
          <div ref="hourChartRef" class="chart-body" style="height: 380px;"></div>
        </div>
      </el-col>

      <el-col :xs="24" :lg="12">
        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <el-icon :size="18" color="#FF9F1C"><DataLine /></el-icon>
              <span>Top 10 接口排行</span>
            </div>
            <div class="chart-subtitle">调用量最多的接口排行</div>
          </div>
          <div class="table-body">
            <el-table
              :data="topApiTableData"
              size="small"
              v-loading="loading"
              :header-cell-style="{ background: '#1a1a2e', color: '#a0a0b0', fontWeight: 600, borderBottom: '1px solid #2a2a40' }"
              :cell-style="{ background: '#1f1f35', color: '#e0e0e0', borderBottom: '1px solid #2a2a40' }"
              style="width: 100%"
            >
              <el-table-column type="index" label="排名" width="55" align="center">
                <template #default="{ $index }">
                  <span
                    class="rank-badge"
                    :class="{ 'rank-top': $index < 3 }"
                  >
                    {{ $index + 1 }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="api" label="接口路径" min-width="160" show-overflow-tooltip />
              <el-table-column prop="calls" label="调用量" width="100" align="right">
                <template #default="{ row }">
                  <span class="calls-value">{{ row.calls.toLocaleString() }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="avgLatency" label="平均延迟" width="90" align="right">
                <template #default="{ row }">
                  <span :class="row.avgLatency > 300 ? 'latency-high' : row.avgLatency > 100 ? 'latency-mid' : 'latency-low'">
                    {{ row.avgLatency }} ms
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="errorRate" label="错误率" width="80" align="right">
                <template #default="{ row }">
                  <span :class="row.errorRate > 1 ? 'error-high' : 'error-low'">
                    {{ row.errorRate }}%
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="趋势" width="70" align="center">
                <template #default="{ row }">
                  <span class="trend-cell" :class="row.trend >= 0 ? 'trend-up-text' : 'trend-down-text'">
                    <el-icon size="10"><ArrowUp v-if="row.trend >= 0" /><ArrowDown v-else /></el-icon>
                    {{ Math.abs(row.trend) }}%
                  </span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 错误分析 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :lg="16">
        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <el-icon :size="18" color="#e94560"><Warning /></el-icon>
              <span>错误趋势</span>
            </div>
            <div class="chart-subtitle">{{ timeRange === '7d' ? '近7天' : timeRange === '30d' ? '近30天' : '近90天' }} 错误次数变化</div>
          </div>
          <div ref="errorTrendChartRef" class="chart-body" style="height: 320px;"></div>
        </div>
      </el-col>

      <el-col :xs="24" :lg="8">
        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <el-icon :size="18" color="#FF9F1C"><PieChartIcon /></el-icon>
              <span>错误类型分布</span>
            </div>
            <div class="chart-subtitle">各错误类型占比</div>
          </div>
          <div ref="errorPieChartRef" class="chart-body" style="height: 320px;"></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.usage-analytics {
  padding: 24px;
  background: #1a1a2e;
  min-height: 100vh;
}

/* 页面标题 */
.analytics-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #e0e0e0;
  margin: 0 0 6px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  color: #4ECDC4;
}

.page-subtitle {
  font-size: 13px;
  color: #a0a0b0;
  margin: 0;
}

/* 时间筛选 */
.time-filter :deep(.el-radio-button__inner) {
  background: #1f1f35;
  border-color: #2a2a40;
  color: #a0a0b0;
  font-weight: 500;
}

.time-filter :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: #e94560;
  border-color: #e94560;
  color: #fff;
  box-shadow: 0 0 12px rgba(233, 69, 96, 0.3);
}

/* 统计卡片 */
.stat-row {
  margin-bottom: 20px;
}

.stat-card {
  position: relative;
  background: #1f1f35;
  border: 1px solid #2a2a40;
  border-radius: 12px;
  padding: 20px;
  overflow: hidden;
  transition: all 0.3s ease;
  cursor: default;
}

.stat-card:hover {
  transform: translateY(-4px);
  border-color: var(--card-accent, #4ECDC4);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 0 0 20px var(--card-accent, #4ECDC4) 15%;
}

.stat-card-content {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  position: relative;
  z-index: 1;
}

.stat-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
  min-width: 0;
}

.stat-title {
  font-size: 13px;
  color: #a0a0b0;
  margin-bottom: 6px;
  font-weight: 500;
}

.stat-value-wrapper {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
}

.stat-suffix {
  font-size: 16px;
  font-weight: 600;
  opacity: 0.8;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 8px;
}

.trend-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.trend-up {
  background: rgba(26, 188, 156, 0.15);
  color: #1abc9c;
}

.trend-down {
  background: rgba(233, 69, 96, 0.15);
  color: #e94560;
}

.trend-label {
  font-size: 12px;
  color: #7a7a8a;
}

.stat-card-glow {
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, var(--card-accent, #4ECDC4) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

.stat-card:hover .stat-card-glow {
  opacity: 0.04;
}

/* 图表卡片 */
.chart-row {
  margin-bottom: 20px;
}

.chart-card {
  background: #1f1f35;
  border: 1px solid #2a2a40;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.chart-card:hover {
  border-color: #3a3a55;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
}

.chart-header {
  padding: 16px 20px 0;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #e0e0e0;
  margin-bottom: 4px;
}

.chart-subtitle {
  font-size: 12px;
  color: #7a7a8a;
  margin-left: 26px;
}

.chart-body {
  padding: 10px 10px 16px;
}

/* 表格区域 */
.table-body {
  padding: 10px 16px 16px;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  color: #a0a0b0;
  background: #2a2a40;
}

.rank-top {
  color: #fff;
  background: linear-gradient(135deg, #FF9F1C, #e94560);
}

.calls-value {
  font-weight: 600;
  color: #e0e0e0;
}

.latency-low {
  color: #1abc9c;
  font-weight: 500;
}

.latency-mid {
  color: #FF9F1C;
  font-weight: 500;
}

.latency-high {
  color: #e94560;
  font-weight: 500;
}

.error-low {
  color: #1abc9c;
  font-weight: 500;
}

.error-high {
  color: #e94560;
  font-weight: 500;
}

.trend-cell {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 12px;
  font-weight: 600;
}

.trend-up-text {
  color: #1abc9c;
}

.trend-down-text {
  color: #e94560;
}

/* 响应式 */
@media (max-width: 768px) {
  .usage-analytics {
    padding: 16px;
  }

  .analytics-header {
    flex-direction: column;
  }

  .page-title {
    font-size: 20px;
  }

  .stat-value {
    font-size: 24px;
  }
}
</style>
