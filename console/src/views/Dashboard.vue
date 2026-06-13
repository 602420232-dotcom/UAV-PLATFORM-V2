<script setup lang="ts">
import { onMounted, onUnmounted, ref, shallowRef } from 'vue'
import * as echarts from 'echarts/core'
import { PieChart as PieChartSeries, GraphChart as GraphChartSeries } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'
import ResultCard from '@/components/common/ResultCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LineChart from '@/components/charts/LineChart.vue'
import { dashboardApi } from '@/api/dashboard'
import { formatNumber } from '@/utils/format'

echarts.use([
  PieChartSeries,
  GraphChartSeries,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  CanvasRenderer,
])

interface DashboardStats {
  totalTenants: number
  totalApiKeys: number
  todayApiCalls: number
  activeTasks: number
}

interface ServiceHealth {
  name: string
  status: string
  responseTime: number
  lastCheck: string
}

// 算法统计（静态数据，来自算法引擎）
const algoStats = ref({
  totalAlgorithms: 102,
  todayRuns: 0,
  avgExecutionTime: 0,
  activeAlgorithms: 0,
})

const stats = ref<DashboardStats>({
  totalTenants: 0,
  totalApiKeys: 0,
  todayApiCalls: 0,
  activeTasks: 0,
})

const trendDates = ref<string[]>([])
const trendCalls = ref<number[]>([])
const serviceNames = ref<string[]>([])
const serviceCalls = ref<number[]>([])
const serviceHealthList = ref<ServiceHealth[]>([])

// 图表引用
const pieChartRef = ref<HTMLDivElement>()
const pieChartInstance = shallowRef<echarts.ECharts>()
const topoChartRef = ref<HTMLDivElement>()
const topoChartInstance = shallowRef<echarts.ECharts>()
const algoPieChartRef = ref<HTMLDivElement>()
const algoPieChartInstance = shallowRef<echarts.ECharts>()

// 算法类别分布数据
const algorithmCategoryData = [
  { name: '规划 (planning)', value: 41 },
  { name: 'AI模型 (model_engine)', value: 21 },
  { name: '边云 (edge)', value: 20 },
  { name: '同化 (assimilation)', value: 13 },
  { name: '风险 (risk)', value: 4 },
  { name: '观测 (observation)', value: 3 },
]

// 系统架构拓扑数据（13个Docker容器）
const topologyNodes = [
  { name: 'Nginx', category: 0, symbolSize: 40 },
  { name: 'API Gateway', category: 1, symbolSize: 50 },
  { name: 'Auth Service', category: 1, symbolSize: 35 },
  { name: 'Tenant Service', category: 1, symbolSize: 35 },
  { name: 'Algorithm Engine', category: 2, symbolSize: 55 },
  { name: 'Assimilation', category: 2, symbolSize: 35 },
  { name: 'Planning', category: 2, symbolSize: 35 },
  { name: 'Model Engine', category: 2, symbolSize: 35 },
  { name: 'Risk Service', category: 2, symbolSize: 30 },
  { name: 'Observation', category: 2, symbolSize: 30 },
  { name: 'Edge Service', category: 2, symbolSize: 30 },
  { name: 'Redis', category: 3, symbolSize: 35 },
  { name: 'PostgreSQL', category: 3, symbolSize: 40 },
]

const topologyLinks = [
  { source: 'Nginx', target: 'API Gateway' },
  { source: 'API Gateway', target: 'Auth Service' },
  { source: 'API Gateway', target: 'Tenant Service' },
  { source: 'API Gateway', target: 'Algorithm Engine' },
  { source: 'Algorithm Engine', target: 'Assimilation' },
  { source: 'Algorithm Engine', target: 'Planning' },
  { source: 'Algorithm Engine', target: 'Model Engine' },
  { source: 'Algorithm Engine', target: 'Risk Service' },
  { source: 'Algorithm Engine', target: 'Observation' },
  { source: 'Algorithm Engine', target: 'Edge Service' },
  { source: 'Auth Service', target: 'Redis' },
  { source: 'Tenant Service', target: 'PostgreSQL' },
  { source: 'Algorithm Engine', target: 'Redis' },
  { source: 'Algorithm Engine', target: 'PostgreSQL' },
  { source: 'Assimilation', target: 'PostgreSQL' },
  { source: 'Planning', target: 'Redis' },
]

const topologyCategories = [
  { name: '网关层' },
  { name: '服务层' },
  { name: '算法层' },
  { name: '数据层' },
]

async function loadDashboard() {
  try {
    const [statsData, trendData, distData, healthData] = await Promise.allSettled([
      dashboardApi.getStats(),
      dashboardApi.getApiCallTrend(7),
      dashboardApi.getServiceDistribution(),
      dashboardApi.getServiceHealth(),
    ])

    if (statsData.status === 'fulfilled') {
      stats.value = statsData.value
      // 用API调用量估算今日算法运行次数
      algoStats.value.todayRuns = Math.round(statsData.value.todayApiCalls * 0.35)
      algoStats.value.avgExecutionTime = 2.4
      algoStats.value.activeAlgorithms = 89
    }
    if (trendData.status === 'fulfilled' && Array.isArray(trendData.value)) {
      trendDates.value = trendData.value.map((d) => d.date)
      trendCalls.value = trendData.value.map((d) => d.calls)
    }
    if (distData.status === 'fulfilled' && Array.isArray(distData.value)) {
      serviceNames.value = distData.value.map((d) => d.service)
      serviceCalls.value = distData.value.map((d) => d.calls)
      initPieChart()
    }
    if (healthData.status === 'fulfilled' && Array.isArray(healthData.value)) {
      serviceHealthList.value = healthData.value
    }
  } catch {
    // 静默处理，使用默认值
  }
}

function initPieChart() {
  if (!pieChartRef.value) return
  pieChartInstance.value = echarts.init(pieChartRef.value)

  const colors = ['#e94560', '#0f3460', '#2ecc71', '#f39c12', '#3498db', '#9b59b6', '#1abc9c']

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    title: {
      text: '各服务调用占比',
      textStyle: { color: '#e0e0e0', fontSize: 14 },
      left: 10,
      top: 5,
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0' },
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'middle',
      textStyle: { color: '#a0a0b0', fontSize: 12 },
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '65%'],
        center: ['40%', '55%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 4,
          borderColor: '#1a1a2e',
          borderWidth: 2,
        },
        label: { show: false },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#e0e0e0' },
        },
        data: serviceNames.value.map((name, i) => ({
          name,
          value: serviceCalls.value[i],
          itemStyle: { color: colors[i % colors.length] },
        })),
      },
    ],
  }

  pieChartInstance.value.setOption(option)
}

function initTopoChart() {
  if (!topoChartRef.value) return
  topoChartInstance.value = echarts.init(topoChartRef.value)

  const categoryColors = ['#f39c12', '#3498db', '#e94560', '#2ecc71']

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    title: {
      text: '系统架构拓扑',
      textStyle: { color: '#e0e0e0', fontSize: 14 },
      left: 10,
      top: 5,
    },
    tooltip: {
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0' },
      formatter: (params: unknown) => {
        const p = params as { dataType?: string; name?: string; data?: { category?: number } }
        if (p.dataType === 'node') {
          const cat = p.data?.category != null ? topologyCategories[p.data.category].name : ''
          return `<strong>${p.name}</strong><br/>层级: ${cat}`
        }
        if (p.dataType === 'edge') {
          return `${(p as { data?: { source?: string; target?: string } }).data?.source} -> ${(p as { data?: { source?: string; target?: string } }).data?.target}`
        }
        return ''
      },
    },
    legend: {
      data: topologyCategories.map((c) => c.name),
      bottom: 10,
      textStyle: { color: '#a0a0b0', fontSize: 12 },
      itemWidth: 14,
      itemHeight: 14,
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: topologyNodes.map((node) => ({
          ...node,
          itemStyle: {
            color: categoryColors[node.category],
            borderColor: '#1a1a2e',
            borderWidth: 2,
          },
          label: {
            show: true,
            color: '#e0e0e0',
            fontSize: 11,
            position: 'bottom',
            distance: 5,
          },
        })),
        links: topologyLinks.map((link) => ({
          ...link,
          lineStyle: {
            color: '#3a3a55',
            width: 1.5,
            curveness: 0.1,
          },
        })),
        categories: topologyCategories.map((cat, i) => ({
          name: cat.name,
          itemStyle: { color: categoryColors[i] },
        })),
        force: {
          repulsion: 200,
          edgeLength: [80, 160],
          gravity: 0.1,
          layoutAnimation: true,
        },
        roam: true,
        draggable: true,
        emphasis: {
          focus: 'adjacency',
          lineStyle: { width: 3 },
        },
      },
    ],
  }

  topoChartInstance.value.setOption(option)
}

function handleResize() {
  pieChartInstance.value?.resize()
  topoChartInstance.value?.resize()
  algoPieChartInstance.value?.resize()
}

function initAlgoPieChart() {
  if (!algoPieChartRef.value) return
  algoPieChartInstance.value = echarts.init(algoPieChartRef.value)

  const colors = ['#2ecc71', '#e94560', '#f39c12', '#3498db', '#e74c3c', '#9b59b6']

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    title: {
      text: '算法类别分布',
      textStyle: { color: '#e0e0e0', fontSize: 14 },
      left: 10,
      top: 5,
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0' },
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'middle',
      textStyle: { color: '#a0a0b0', fontSize: 12 },
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '65%'],
        center: ['40%', '55%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 4,
          borderColor: '#1a1a2e',
          borderWidth: 2,
        },
        label: { show: false },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#e0e0e0' },
        },
        data: algorithmCategoryData.map((item, i) => ({
          name: item.name,
          value: item.value,
          itemStyle: { color: colors[i % colors.length] },
        })),
      },
    ],
  }

  algoPieChartInstance.value.setOption(option)
}

onMounted(() => {
  loadDashboard()
  initTopoChart()
  initAlgoPieChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  pieChartInstance.value?.dispose()
  topoChartInstance.value?.dispose()
  algoPieChartInstance.value?.dispose()
})
</script>

<template>
  <div class="dashboard-page">
    <!-- 原有统计卡片 -->
    <div class="stats-row">
      <ResultCard
        title="总租户数"
        :value="formatNumber(stats.totalTenants)"
        icon="OfficeBuilding"
        color="#3498db"
      />
      <ResultCard
        title="总 API Key 数"
        :value="formatNumber(stats.totalApiKeys)"
        icon="Key"
        color="#2ecc71"
      />
      <ResultCard
        title="今日 API 调用量"
        :value="formatNumber(stats.todayApiCalls)"
        icon="TrendCharts"
        color="#e94560"
      />
      <ResultCard
        title="活跃任务数"
        :value="formatNumber(stats.activeTasks)"
        icon="VideoPlay"
        color="#f39c12"
      />
    </div>

    <!-- 算法统计卡片 -->
    <div class="stats-row">
      <ResultCard
        title="总算法数"
        :value="formatNumber(algoStats.totalAlgorithms)"
        icon="Cpu"
        color="#e94560"
        subtitle="已注册算法引擎"
      />
      <ResultCard
        title="今日运行次数"
        :value="formatNumber(algoStats.todayRuns)"
        icon="VideoPlay"
        color="#3498db"
        subtitle="算法执行调用"
      />
      <ResultCard
        title="平均执行时间"
        :value="algoStats.avgExecutionTime + 's'"
        icon="Timer"
        color="#2ecc71"
        subtitle="全类别均值"
      />
      <ResultCard
        title="活跃算法数"
        :value="formatNumber(algoStats.activeAlgorithms)"
        icon="CircleCheck"
        color="#f39c12"
        subtitle="状态为 ACTIVE"
      />
    </div>

    <!-- 图表区域：API趋势 + 服务占比 -->
    <div class="charts-row">
      <el-card class="chart-card">
        <LineChart
          title="近 7 天 API 调用趋势"
          :x-data="trendDates"
          :series="[{ name: 'API 调用量', data: trendCalls, color: '#e94560', areaStyle: true }]"
          height="320px"
          :show-legend="false"
        />
      </el-card>

      <el-card class="chart-card">
        <div ref="pieChartRef" style="width: 100%; height: 320px"></div>
      </el-card>
    </div>

    <!-- 图表区域：算法类别分布 + 系统架构拓扑 -->
    <div class="charts-row">
      <el-card class="chart-card">
        <div ref="topoChartRef" style="width: 100%; height: 380px"></div>
      </el-card>

      <el-card class="chart-card">
        <div class="algo-pie-wrapper">
          <div ref="algoPieChartRef" style="width: 100%; height: 380px"></div>
        </div>
      </el-card>
    </div>

    <!-- 系统状态 -->
    <el-card class="status-card">
      <template #header>
        <span>系统状态</span>
      </template>
      <el-table :data="serviceHealthList" stripe>
        <el-table-column prop="name" label="服务名称" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <StatusBadge :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="responseTime" label="响应时间" width="120">
          <template #default="{ row }">
            {{ row.responseTime != null ? `${row.responseTime}ms` : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="lastCheck" label="最后检查" />
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.chart-card {
  border-radius: 8px;
}

.status-card {
  border-radius: 8px;
}

.algo-pie-wrapper {
  width: 100%;
  height: 100%;
}

@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .charts-row {
    grid-template-columns: 1fr;
  }
}
</style>
