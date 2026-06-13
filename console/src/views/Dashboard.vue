<script setup lang="ts">
import { onMounted, ref, shallowRef } from 'vue'
import * as echarts from 'echarts/core'
import { PieChart as PieChartSeries } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'
import ResultCard from '@/components/common/ResultCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LineChart from '@/components/charts/LineChart.vue'
import { dashboardApi } from '@/api/dashboard'
import { formatNumber } from '@/utils/format'

echarts.use([PieChartSeries, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer])

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

const pieChartRef = ref<HTMLDivElement>()
const pieChartInstance = shallowRef<echarts.ECharts>()

async function loadDashboard() {
  try {
    // 并行请求仪表盘数据
    const [statsData, trendData, distData, healthData] = await Promise.allSettled([
      dashboardApi.getStats(),
      dashboardApi.getApiCallTrend(7),
      dashboardApi.getServiceDistribution(),
      dashboardApi.getServiceHealth(),
    ])

    if (statsData.status === 'fulfilled') {
      stats.value = statsData.value
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

function handleResize() {
  pieChartInstance.value?.resize()
}

onMounted(() => {
  loadDashboard()
  window.addEventListener('resize', handleResize)
})
</script>

<template>
  <div class="dashboard-page">
    <!-- 统计卡片 -->
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

    <!-- 图表区域 -->
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

@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .charts-row {
    grid-template-columns: 1fr;
  }
}
</style>
