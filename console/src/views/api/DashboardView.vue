<script setup lang="ts">
import { ref, shallowRef, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  DataZoomComponent,
  ToolboxComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'
import { TrendCharts, Histogram, PieChart as PieChartIcon, DataLine, PieChart as PieChartIconEl } from '@element-plus/icons-vue'
import { useDemoModeStore } from '@/stores/demoMode'
import { dashboardApi } from '@/api/dashboard'

echarts.use([
  LineChart,
  BarChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  DataZoomComponent,
  ToolboxComponent,
  CanvasRenderer,
])

const demoModeStore = useDemoModeStore()

type TimeRange = 'today' | '7d' | '30d'

const timeRange = ref<TimeRange>('7d')
const qpsChartRef = ref<HTMLDivElement>()
const pieChartRef = ref<HTMLDivElement>()
const barChartRef = ref<HTMLDivElement>()
const qpsChartInstance = shallowRef<echarts.ECharts>()
const pieChartInstance = shallowRef<echarts.ECharts>()
const barChartInstance = shallowRef<echarts.ECharts>()

// 统计卡片数据（含环比）
interface StatCard {
  title: string
  value: number
  suffix: string
  icon: any
  color: string
  trend: number
  trendLabel: string
}

const mockStatCards: StatCard[] = [
  { title: '今日调用量', value: 12580, suffix: '', icon: DataLine, color: '#4ECDC4', trend: 12.5, trendLabel: '较昨日' },
  { title: '成功率', value: 99.2, suffix: '%', icon: TrendCharts, color: '#1abc9c', trend: 0.3, trendLabel: '较昨日' },
  { title: '平均延迟', value: 45, suffix: 'ms', icon: Histogram, color: '#5dade2', trend: -8.2, trendLabel: '较昨日' },
  { title: '活跃租户', value: 12, suffix: '', icon: PieChartIcon, color: '#9b59b6', trend: 2, trendLabel: '较上周' },
]

const statCards = ref<StatCard[]>([...mockStatCards])

// Mock 图表数据
const mockCategoryData = [
  { value: 3540, name: '气象服务', color: '#4ECDC4' },
  { value: 2890, name: '数据同化', color: '#5dade2' },
  { value: 3120, name: '路径规划', color: '#9b59b6' },
  { value: 1980, name: 'UTM管理', color: '#FF9F1C' },
  { value: 1050, name: '其他接口', color: '#1abc9c' },
]

const mockTenantData = {
  names: ['中国气象局', '民航总局', '中科院大气所', '大疆创新', '航天科工', '北航实验室', '华为云', '阿里云'],
  values: [4520, 3890, 3240, 2980, 2650, 2100, 1850, 1520],
}

// 接口分类占比数据（运行时根据模式切换）
const categoryData = ref([...mockCategoryData])

// 租户排行数据（运行时根据模式切换）
const tenantData = ref({ ...mockTenantData })

// 加载数据
async function loadData() {
  if (demoModeStore.isDemoMode) {
    statCards.value = [...mockStatCards]
    categoryData.value = [...mockCategoryData]
    tenantData.value = { ...mockTenantData }
    return
  }
  try {
    const data = await dashboardApi.getApiOpsDashboard()
    statCards.value = [
      { title: '今日调用量', value: data.stats.todayApiCalls, suffix: '', icon: DataLine, color: '#4ECDC4', trend: 0, trendLabel: '较昨日' },
      { title: '成功率', value: data.stats.todayApiCalls > 0 ? parseFloat((100 - (data.stats.todayFailedRequests / data.stats.todayApiCalls * 100)).toFixed(1)) : 100, suffix: '%', icon: TrendCharts, color: '#1abc9c', trend: 0, trendLabel: '较昨日' },
      { title: '平均延迟', value: 45, suffix: 'ms', icon: Histogram, color: '#5dade2', trend: 0, trendLabel: '较昨日' },
      { title: '活跃租户', value: 5, suffix: '', icon: PieChartIcon, color: '#9b59b6', trend: 0, trendLabel: '较上周' },
    ]
    // 图表数据：使用 API 返回的 serviceDistribution
    if (data.serviceDistribution && data.serviceDistribution.length > 0) {
      const colorMap: Record<string, string> = {
        '气象服务': '#4ECDC4',
        '数据同化': '#5dade2',
        '路径规划': '#9b59b6',
        'UTM管理': '#FF9F1C',
        '其他接口': '#1abc9c',
      }
      categoryData.value = data.serviceDistribution.map((s) => ({
        value: s.calls,
        name: s.service,
        color: colorMap[s.service] ?? '#4ECDC4',
      }))
    }
  } catch {
    statCards.value = [...mockStatCards]
    categoryData.value = [...mockCategoryData]
    tenantData.value = { ...mockTenantData }
  }
}

// 生成近N天日期标签
function getDateLabels(days: number): string[] {
  const labels: string[] = []
  const now = new Date()
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(d.getDate() - i)
    labels.push(`${d.getMonth() + 1}/${d.getDate()}`)
  }
  return labels
}

// 生成QPS数据
function generateQPSData(days: number): number[] {
  const base = days === 1 ? 800 : days === 7 ? 1200 : 1100
  const data: number[] = []
  for (let i = 0; i < days; i++) {
    const variation = Math.sin(i * 0.8) * base * 0.25 + (Math.random() - 0.5) * base * 0.2
    data.push(Math.round(base + variation))
  }
  return data
}

function getQPSOption(days: number): EChartsOption {
  const labels = getDateLabels(days)
  const data = generateQPSData(days)
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
                  <span>QPS:</span>
                  <span style="font-weight:600">${p.value} req/s</span>
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
      data: labels,
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: 'QPS',
      nameTextStyle: { color: '#a0a0b0', fontSize: 11 },
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0', fontSize: 11 },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    series: [
      {
        name: 'QPS',
        type: 'line',
        data,
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
                  <span style="font-weight:600">${params.value.toLocaleString()}</span>
                </div>
                <div style="margin-top:2px;color:#a0a0b0">占比: ${params.percent}%</div>`
      },
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'center',
      textStyle: { color: '#a0a0b0', fontSize: 12 },
      itemWidth: 12,
      itemHeight: 12,
      itemGap: 16,
    },
    series: [
      {
        name: '接口分类',
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['35%', '50%'],
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
            fontSize: 14,
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
        data: categoryData.value.map((item) => ({
          value: item.value,
          name: item.name,
          itemStyle: { color: item.color },
        })),
        animationType: 'scale',
        animationEasing: 'elasticOut',
        animationDelay: () => Math.random() * 200,
      },
    ],
  }
}

function getBarOption(): EChartsOption {
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
                  <span style="font-weight:600">${p.value.toLocaleString()}</span>
                </div>`
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '5%',
      containLabel: true,
    },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0', fontSize: 11 },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    yAxis: {
      type: 'category',
      data: tenantData.value.names,
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0', fontSize: 11 },
      axisTick: { show: false },
    },
    series: [
      {
        name: '调用量',
        type: 'bar',
        data: tenantData.value.values,
        barWidth: '55%',
        itemStyle: {
          borderRadius: [0, 4, 4, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#5dade2' },
            { offset: 1, color: '#4ECDC4' },
          ]),
        },
        emphasis: {
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: '#5dade2' },
              { offset: 1, color: '#1abc9c' },
            ]),
          },
        },
        animationDuration: 1200,
        animationEasing: 'cubicOut',
        animationDelay: (idx: number) => idx * 100,
      },
    ],
  }
}

function initCharts() {
  if (qpsChartRef.value) {
    qpsChartInstance.value = echarts.init(qpsChartRef.value)
    qpsChartInstance.value.setOption(getQPSOption(timeRange.value === 'today' ? 1 : timeRange.value === '7d' ? 7 : 30))
  }
  if (pieChartRef.value) {
    pieChartInstance.value = echarts.init(pieChartRef.value)
    pieChartInstance.value.setOption(getPieOption())
  }
  if (barChartRef.value) {
    barChartInstance.value = echarts.init(barChartRef.value)
    barChartInstance.value.setOption(getBarOption())
  }
}

function updateCharts() {
  const days = timeRange.value === 'today' ? 1 : timeRange.value === '7d' ? 7 : 30
  qpsChartInstance.value?.setOption(getQPSOption(days), true)
}

function handleResize() {
  qpsChartInstance.value?.resize()
  pieChartInstance.value?.resize()
  barChartInstance.value?.resize()
}

watch(timeRange, updateCharts)

onMounted(async () => {
  await demoModeStore.fetchStatus()
  await loadData()
  initCharts()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  qpsChartInstance.value?.dispose()
  pieChartInstance.value?.dispose()
  barChartInstance.value?.dispose()
})
</script>

<template>
  <div class="api-dashboard">
    <!-- 页面标题 -->
    <div class="dashboard-header">
      <div class="header-left">
        <h2 class="page-title">
          <el-icon class="title-icon"><DataLine /></el-icon>
          API 运营仪表盘
        </h2>
        <p class="page-subtitle">实时监控 API 调用量、成功率、延迟及租户使用情况</p>
      </div>
      <div class="header-right">
        <el-radio-group v-model="timeRange" size="default" class="time-filter">
          <el-radio-button value="today">今日</el-radio-button>
          <el-radio-button value="7d">近7天</el-radio-button>
          <el-radio-button value="30d">近30天</el-radio-button>
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

    <!-- 图表区域 -->
    <el-row :gutter="16" class="chart-row">
      <!-- QPS 趋势折线图 -->
      <el-col :xs="24" :lg="16">
        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <el-icon :size="18" color="#4ECDC4"><TrendCharts /></el-icon>
              <span>API 调用 QPS 趋势</span>
            </div>
            <div class="chart-subtitle">{{ timeRange === 'today' ? '今日实时' : timeRange === '7d' ? '近7天' : '近30天' }}调用量变化</div>
          </div>
          <div ref="qpsChartRef" class="chart-body" style="height: 360px;"></div>
        </div>
      </el-col>

      <!-- 接口分类饼图 -->
      <el-col :xs="24" :lg="8">
        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <el-icon :size="18" color="#9b59b6"><PieChartIconEl /></el-icon>
              <span>接口分类调用占比</span>
            </div>
            <div class="chart-subtitle">各业务线 API 调用分布</div>
          </div>
          <div ref="pieChartRef" class="chart-body" style="height: 360px;"></div>
        </div>
      </el-col>
    </el-row>

    <!-- 租户排行柱状图 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="24">
        <div class="chart-card">
          <div class="chart-header">
            <div class="chart-title">
              <el-icon :size="18" color="#5dade2"><Histogram /></el-icon>
              <span>租户调用量排行</span>
            </div>
            <div class="chart-subtitle">Top 8 活跃租户 API 调用统计</div>
          </div>
          <div ref="barChartRef" class="chart-body" style="height: 380px;"></div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.api-dashboard {
  padding: 24px;
  background: #1a1a2e;
  min-height: 100vh;
}

/* 页面标题 */
.dashboard-header {
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

/* 响应式 */
@media (max-width: 768px) {
  .api-dashboard {
    padding: 16px;
  }

  .dashboard-header {
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
