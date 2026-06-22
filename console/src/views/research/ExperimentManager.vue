<script setup lang="ts">
import { onMounted, onUnmounted, ref, shallowRef, nextTick, watch } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart as LineChartSeries, RadarChart as RadarChartSeries, BarChart as BarChartSeries } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  RadarComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import { experimentApi } from '@/api/experiment'
import type { Experiment, CompareResult } from '@/api/experiment'
import { formatDateTime } from '@/utils/format'
import { useDemoModeStore } from '@/stores/demoMode'
import { getMockAlgorithmNames } from '@/mock/algorithmData'
const demoModeStore = useDemoModeStore()

echarts.use([
  LineChartSeries,
  RadarChartSeries,
  BarChartSeries,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  RadarComponent,
  CanvasRenderer,
])

// ==================== 统计卡片 ====================
const statsData = ref({
  total: 0,
  running: 0,
  completed: 0,
  failed: 0,
})

// ==================== 筛选 ====================
const loading = ref(false)
const keyword = ref('')
const statusFilter = ref('')
const dateRange = ref<[string, string] | null>(null)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// ==================== 实验列表 ====================
const experiments = ref<Experiment[]>([])
const selectedRows = ref<Experiment[]>([])

// ==================== 详情对话框 ====================
const detailDialogVisible = ref(false)
const currentExperiment = ref<Experiment | null>(null)
const detailMetrics = ref<Record<string, number>>({})
const detailConfig = ref<Record<string, unknown>>({})
const detailResult = ref<Record<string, unknown>>({})
const convergenceChartRef = ref<HTMLDivElement>()
const convergenceChartInstance = shallowRef<echarts.ECharts>()
const rmseChartRef = ref<HTMLDivElement>()
const rmseChartInstance = shallowRef<echarts.ECharts>()
const activeDetailTab = ref('info')

// ==================== 对比对话框 ====================
const compareDialogVisible = ref(false)
const compareData = ref<CompareResult | null>(null)
const radarChartRef = ref<HTMLDivElement>()
const radarChartInstance = shallowRef<echarts.ECharts>()

// ==================== 方法 ====================

function generateMockExperiments(): { records: Experiment[], total: number } {
  const statuses: Array<'RUNNING' | 'COMPLETED' | 'FAILED'> = ['RUNNING', 'COMPLETED', 'FAILED']
  const algoList = getMockAlgorithmNames()
  const records: Experiment[] = []
  
  for (let i = 1; i <= 25; i++) {
    const algo = algoList[i % algoList.length] ?? 'Algo'
    const catMap: Record<string, string> = { '同化': 'assimilation', '规划': 'planning', '风险': 'risk', '观测': 'observation' }
    const cat = Object.entries(catMap).find(([k]) => algo.includes(k))?.[1] ?? 'model_engine'
    records.push({
      id: i,
      experimentName: `实验-${String(i).padStart(3, '0')}`,
      algorithmName: algo.split('-')[0] ?? 'Algo',
      algorithmCategory: cat,
      status: statuses[i % 3] ?? 'COMPLETED',
      configJson: '{}',
      resultJson: '{}',
      metricsJson: '{}',
      snapshotHash: i % 3 === 0 ? `snap-${i}` : '',
      durationMs: Math.floor(Math.random() * 10000) + 1000,
      createdBy: 'admin',
      createdAt: `2026-06-${String(Math.max(1, 18 - Math.floor(i / 5))).padStart(2, '0')}T${String(8 + (i % 12)).padStart(2, '0')}:00:00`,
      updatedAt: `2026-06-18T${String(8 + (i % 12)).padStart(2, '0')}:00:00`,
    })
  }
  return { records, total: 25 }
}

async function loadStats() {
  if (demoModeStore.isDemoMode) {
    const mock = generateMockExperiments()
    const records = mock.records
    statsData.value.total = mock.total
    statsData.value.running = records.filter((e) => e.status === 'RUNNING').length
    statsData.value.completed = records.filter((e) => e.status === 'COMPLETED').length
    statsData.value.failed = records.filter((e) => e.status === 'FAILED').length
    return
  }
  try {
    const data = await experimentApi.list({ page: 1, size: 1 })
    statsData.value.total = data.total ?? 0
  } catch {
    // 静默处理
  }
  // 根据列表数据计算各状态数量
  try {
    const allData = await experimentApi.list({ page: 1, size: 1000 })
    const records = allData.records ?? []
    statsData.value.total = allData.total ?? records.length
    statsData.value.running = records.filter((e) => e.status === 'RUNNING').length
    statsData.value.completed = records.filter((e) => e.status === 'COMPLETED').length
    statsData.value.failed = records.filter((e) => e.status === 'FAILED').length
  } catch {
    // 静默处理
  }
}

async function loadExperiments() {
  loading.value = true
  try {
    if (demoModeStore.isDemoMode) {
      const mock = generateMockExperiments()
      experiments.value = mock.records
      total.value = mock.total
      return
    }
    const params: Record<string, unknown> = {
      page: currentPage.value,
      size: pageSize.value,
    }
    if (keyword.value) params.keyword = keyword.value
    if (statusFilter.value) params.status = statusFilter.value
    if (dateRange.value && dateRange.value[0]) params.startDate = dateRange.value[0]
    if (dateRange.value && dateRange.value[1]) params.endDate = dateRange.value[1]

    const data = await experimentApi.list(params)
    experiments.value = data.records ?? []
    total.value = data.total ?? 0
  } catch {
    ElMessage.error('加载实验列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  loadExperiments()
}

function handleReset() {
  keyword.value = ''
  statusFilter.value = ''
  dateRange.value = null
  currentPage.value = 1
  loadExperiments()
}

function handlePageChange(page: number) {
  currentPage.value = page
  loadExperiments()
}

function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  loadExperiments()
}

function handleSelectionChange(rows: Experiment[]) {
  selectedRows.value = rows
}

// 状态标签
function getStatusType(status: string): 'success' | 'warning' | 'danger' | 'info' {
  const map: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    COMPLETED: 'success',
    RUNNING: 'warning',
    FAILED: 'danger',
    CANCELLED: 'info',
    PENDING: 'info',
  }
  return map[status] ?? 'info'
}

function getStatusLabel(status: string): string {
  const map: Record<string, string> = {
    COMPLETED: '已完成',
    RUNNING: '运行中',
    FAILED: '失败',
    CANCELLED: '已取消',
    PENDING: '等待中',
  }
  return map[status] ?? status
}

function formatDuration(ms: number): string {
  if (ms == null) return '-'
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}min`
}

// ==================== 详情操作 ====================

async function handleViewDetail(row: Experiment) {
  try {
    currentExperiment.value = await experimentApi.getById(row.id)
    // 解析 JSON 字段
    try {
      detailMetrics.value = currentExperiment.value.metricsJson
        ? JSON.parse(currentExperiment.value.metricsJson)
        : {}
    } catch {
      detailMetrics.value = {}
    }
    try {
      detailConfig.value = currentExperiment.value.configJson
        ? JSON.parse(currentExperiment.value.configJson)
        : {}
    } catch {
      detailConfig.value = {}
    }
    try {
      detailResult.value = currentExperiment.value.resultJson
        ? JSON.parse(currentExperiment.value.resultJson)
        : {}
    } catch {
      detailResult.value = {}
    }
    activeDetailTab.value = 'info'
    detailDialogVisible.value = true
    nextTick(() => {
      initConvergenceChart()
      initRmseChart()
    })
  } catch {
    ElMessage.error('获取实验详情失败')
  }
}

async function handleCreateSnapshot(row: Experiment) {
  try {
    await ElMessageBox.confirm(`确定要为实验 "${row.experimentName}" 创建快照吗？`, '创建快照', {
      type: 'info',
    })
    const result = await experimentApi.createSnapshot(row.id)
    ElMessage.success(`快照已创建，哈希值: ${result.hash}`)
    loadExperiments()
  } catch {
    // 用户取消或错误
  }
}

async function handleRestoreSnapshot(row: Experiment) {
  try {
    await ElMessageBox.confirm(
      `确定要恢复实验 "${row.experimentName}" 的快照吗？这将覆盖当前配置。`,
      '恢复快照',
      { type: 'warning' }
    )
    await experimentApi.restore(row.id)
    ElMessage.success('快照已恢复')
    loadExperiments()
  } catch {
    // 用户取消或错误
  }
}

async function handleDelete(row: Experiment) {
  try {
    await ElMessageBox.confirm(`确定要删除实验 "${row.experimentName}" 吗？此操作不可恢复。`, '删除确认', {
      type: 'warning',
    })
    await experimentApi.delete(row.id)
    ElMessage.success('实验已删除')
    loadExperiments()
  } catch {
    // 用户取消或错误
  }
}

// ==================== 对比功能 ====================

async function handleCompare() {
  if (selectedRows.value.length < 2) {
    ElMessage.warning('请至少选择 2 个实验进行对比')
    return
  }
  if (selectedRows.value.length > 10) {
    ElMessage.warning('最多同时对比 10 组实验')
    return
  }

  try {
    const ids = selectedRows.value.map((r) => r.id)
    
    if (demoModeStore.isDemoMode) {
      // 演示模式：生成 mock 对比数据
      compareData.value = {
        experiments: selectedRows.value,
        metrics: [
          {
            name: 'RMSE',
            key: 'rmse',
            values: selectedRows.value.map((r) => ({
              experimentId: r.id,
              experimentName: r.experimentName,
              value: Math.random() * 0.5 + 0.05,
            })),
          },
          {
            name: 'MAE',
            key: 'mae',
            values: selectedRows.value.map((r) => ({
              experimentId: r.id,
              experimentName: r.experimentName,
              value: Math.random() * 0.3 + 0.02,
            })),
          },
          {
            name: '执行耗时(ms)',
            key: 'duration',
            values: selectedRows.value.map((r) => ({
              experimentId: r.id,
              experimentName: r.experimentName,
              value: r.durationMs,
            })),
          },
          {
            name: '收敛迭代数',
            key: 'iterations',
            values: selectedRows.value.map((r) => ({
              experimentId: r.id,
              experimentName: r.experimentName,
              value: Math.floor(Math.random() * 50) + 10,
            })),
          },
        ],
      }
    } else {
      compareData.value = await experimentApi.compare(ids)
    }
    
    compareDialogVisible.value = true
    nextTick(() => initRadarChart())
  } catch {
    ElMessage.error('对比分析失败')
  }
}

// ==================== 导出功能 ====================

async function handleExport(row: Experiment) {
  try {
    const reportContent = await experimentApi.generateReport(row.id, 'csv')
    // 创建下载链接
    const blob = new Blob([reportContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${row.experimentName}_report.csv`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('报告已导出')
  } catch {
    ElMessage.error('导出失败')
  }
}

// ==================== 图表初始化 ====================

function initConvergenceChart() {
  if (!convergenceChartRef.value) return
  convergenceChartInstance.value = echarts.init(convergenceChartRef.value)

  const convergence = detailResult.value.convergence as Array<{ iteration: number; cost: number }> | undefined
  const xData: string[] = []
  const yData: number[] = []

  if (Array.isArray(convergence)) {
    convergence.forEach((c) => {
      xData.push(String(c.iteration))
      yData.push(c.cost)
    })
  } else {
    // 模拟数据
    for (let i = 0; i < 20; i++) {
      xData.push(String(i + 1))
      yData.push(Math.max(0, 100 * Math.exp(-0.15 * i) + Math.random() * 5))
    }
  }

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    title: {
      text: '代价函数收敛曲线',
      textStyle: { color: '#e0e0e0', fontSize: 13 },
      left: 10,
      top: 5,
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0' },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: 50,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: xData,
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0' },
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0' },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    series: [
      {
        name: 'Cost',
        type: 'line',
        data: yData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 5,
        lineStyle: { color: '#e94560', width: 2 },
        itemStyle: { color: '#e94560' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(233, 69, 96, 0.25)' },
            { offset: 1, color: 'rgba(233, 69, 96, 0.02)' },
          ]),
        },
      },
    ],
  }

  convergenceChartInstance.value.setOption(option)
}

function initRmseChart() {
  if (!rmseChartRef.value) return
  rmseChartInstance.value = echarts.init(rmseChartRef.value)

  const rmseData = detailResult.value.rmseComparison as Array<{ label: string; value: number }> | undefined
  const xLabels: string[] = []
  const yValues: number[] = []

  if (Array.isArray(rmseData)) {
    rmseData.forEach((r) => {
      xLabels.push(r.label)
      yValues.push(r.value)
    })
  } else {
    // 模拟数据
    const labels = ['Temperature', 'Humidity', 'Wind Speed', 'Pressure', 'Precipitation']
    labels.forEach((l) => {
      xLabels.push(l)
      yValues.push(+(0.5 + Math.random() * 2).toFixed(2))
    })
  }

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    title: {
      text: 'RMSE 对比',
      textStyle: { color: '#e0e0e0', fontSize: 13 },
      left: 10,
      top: 5,
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0' },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: 50,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: xLabels,
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0', rotate: 30 },
    },
    yAxis: {
      type: 'value',
      name: 'RMSE',
      nameTextStyle: { color: '#a0a0b0' },
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0' },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    series: [
      {
        name: 'RMSE',
        type: 'bar',
        data: yValues,
        barWidth: '40%',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#3498db' },
            { offset: 1, color: 'rgba(52, 152, 219, 0.3)' },
          ]),
          borderRadius: [4, 4, 0, 0],
        },
      },
    ],
  }

  rmseChartInstance.value.setOption(option)
}

function initRadarChart() {
  if (!radarChartRef.value || !compareData.value) return
  radarChartInstance.value = echarts.init(radarChartRef.value)

  const metrics = compareData.value.metrics
  const indicators = metrics.map((m) => ({
    name: m.name,
    max: Math.max(...m.values.map((v) => v.value)) * 1.2 || 100,
  }))

  const colors = ['#e94560', '#3498db', '#2ecc71', '#f39c12', '#9b59b6']
  const series = compareData.value.experiments.map((exp, idx) => {
    const values = metrics.map((m) => {
      const found = m.values.find((v) => v.experimentId === exp.id)
      return found ? found.value : 0
    })
    return {
      value: values,
      name: exp.experimentName,
      lineStyle: { color: colors[idx % colors.length] },
      itemStyle: { color: colors[idx % colors.length] },
      areaStyle: { color: colors[idx % colors.length] + '30' },
    }
  })

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    title: {
      text: '多算法性能雷达图',
      textStyle: { color: '#e0e0e0', fontSize: 14 },
      left: 10,
      top: 5,
    },
    tooltip: {
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0' },
    },
    legend: {
      data: compareData.value.experiments.map((e) => e.experimentName),
      bottom: 10,
      textStyle: { color: '#a0a0b0' },
    },
    radar: {
      indicator: indicators,
      center: ['50%', '55%'],
      radius: '60%',
      axisName: { color: '#a0a0b0', fontSize: 11 },
      splitArea: {
        areaStyle: {
          color: ['rgba(15, 52, 96, 0.1)', 'rgba(15, 52, 96, 0.2)', 'rgba(15, 52, 96, 0.3)', 'rgba(15, 52, 96, 0.4)'],
        },
      },
      splitLine: { lineStyle: { color: '#2a2a40' } },
      axisLine: { lineStyle: { color: '#2a2a40' } },
    },
    series: [
      {
        type: 'radar',
        data: series,
      },
    ],
  }

  radarChartInstance.value.setOption(option)
}

function handleResize() {
  convergenceChartInstance.value?.resize()
  rmseChartInstance.value?.resize()
  radarChartInstance.value?.resize()
}

watch(() => demoModeStore.isDemoMode, () => {
  loadStats()
  loadExperiments()
})

onMounted(async () => {
  await demoModeStore.fetchStatus()
  loadStats()
  loadExperiments()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  convergenceChartInstance.value?.dispose()
  rmseChartInstance.value?.dispose()
  radarChartInstance.value?.dispose()
})
</script>

<template>
  <div class="experiment-manager">
    <!-- 统计卡片 -->
    <div class="stats-row">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon" style="background-color: rgba(52, 152, 219, 0.15);">
            <el-icon size="24" color="#3498db"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statsData.total }}</div>
            <div class="stat-label">总实验数</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon" style="background-color: rgba(243, 156, 18, 0.15);">
            <el-icon size="24" color="#f39c12"><Loading /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statsData.running }}</div>
            <div class="stat-label">运行中</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon" style="background-color: rgba(46, 204, 113, 0.15);">
            <el-icon size="24" color="#2ecc71"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statsData.completed }}</div>
            <div class="stat-label">已完成</div>
          </div>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon" style="background-color: rgba(231, 76, 60, 0.15);">
            <el-icon size="24" color="#e74c3c"><CircleClose /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ statsData.failed }}</div>
            <div class="stat-label">失败</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 筛选栏 -->
    <el-card class="filter-card">
      <div class="filter-row">
        <el-input
          v-model="keyword"
          placeholder="搜索算法名称..."
          clearable
          style="width: 200px"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="width: 140px" @change="handleSearch">
          <el-option label="全部" value="" />
          <el-option label="运行中" value="RUNNING" />
          <el-option label="已完成" value="COMPLETED" />
          <el-option label="失败" value="FAILED" />
          <el-option label="已取消" value="CANCELLED" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="width: 260px"
          @change="handleSearch"
        />
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
        <el-button @click="handleReset">
          <el-icon><Refresh /></el-icon>
          重置
        </el-button>
        <div class="filter-actions">
          <el-button
            type="warning"
            :disabled="selectedRows.length < 2"
            @click="handleCompare"
          >
            <el-icon><DataAnalysis /></el-icon>
            对比 ({{ selectedRows.length }})
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 实验列表 -->
    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="experiments"
        stripe
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="experimentName" label="实验名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="algorithmName" label="算法名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="algorithmCategory" label="分类" width="120">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.algorithmCategory }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small" effect="dark">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="durationMs" label="执行耗时" width="110">
          <template #default="{ row }">
            {{ formatDuration(row.durationMs) }}
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewDetail(row)">
              详情
            </el-button>
            <el-button type="success" link size="small" @click="handleCreateSnapshot(row)">
              快照
            </el-button>
            <el-button
              v-if="row.snapshotHash"
              type="warning"
              link
              size="small"
              @click="handleRestoreSnapshot(row)"
            >
              恢复
            </el-button>
            <el-button type="info" link size="small" @click="handleExport(row)">
              导出
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <!-- 实验详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="`实验详情 - ${currentExperiment?.experimentName ?? ''}`"
      width="800px"
      destroy-on-close
    >
      <div v-if="currentExperiment">
        <el-tabs v-model="activeDetailTab">
          <!-- 基本信息 -->
          <el-tab-pane label="基本信息" name="info">
            <el-descriptions :column="2" border size="small">
              <el-descriptions-item label="实验名称" :span="2">
                {{ currentExperiment.experimentName }}
              </el-descriptions-item>
              <el-descriptions-item label="算法名称">
                {{ currentExperiment.algorithmName }}
              </el-descriptions-item>
              <el-descriptions-item label="分类">
                <el-tag size="small" effect="plain">{{ currentExperiment.algorithmCategory }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusType(currentExperiment.status)" size="small" effect="dark">
                  {{ getStatusLabel(currentExperiment.status) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="执行耗时">
                {{ formatDuration(currentExperiment.durationMs) }}
              </el-descriptions-item>
              <el-descriptions-item label="创建者">
                {{ currentExperiment.createdBy }}
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">
                {{ formatDateTime(currentExperiment.createdAt) }}
              </el-descriptions-item>
              <el-descriptions-item label="更新时间">
                {{ formatDateTime(currentExperiment.updatedAt) }}
              </el-descriptions-item>
              <el-descriptions-item v-if="currentExperiment.snapshotHash" label="快照哈希" :span="2">
                <code class="hash-code">{{ currentExperiment.snapshotHash }}</code>
              </el-descriptions-item>
            </el-descriptions>
          </el-tab-pane>

          <!-- 参数配置 -->
          <el-tab-pane label="参数配置" name="config">
            <div class="json-display">
              <pre>{{ JSON.stringify(detailConfig, null, 2) }}</pre>
            </div>
          </el-tab-pane>

          <!-- 运行结果 -->
          <el-tab-pane label="运行结果" name="result">
            <div class="json-display">
              <pre>{{ JSON.stringify(detailResult, null, 2) }}</pre>
            </div>
          </el-tab-pane>

          <!-- Metrics 指标 -->
          <el-tab-pane label="指标" name="metrics">
            <div v-if="Object.keys(detailMetrics).length > 0" class="metrics-grid">
              <div v-for="(value, key) in detailMetrics" :key="key" class="metric-item">
                <div class="metric-label">{{ key }}</div>
                <div class="metric-value">{{ typeof value === 'number' ? value.toFixed(4) : value }}</div>
              </div>
            </div>
            <el-empty v-else description="暂无指标数据" />
          </el-tab-pane>

          <!-- 图表 -->
          <el-tab-pane label="图表分析" name="charts">
            <div class="charts-grid">
              <div ref="convergenceChartRef" style="width: 100%; height: 300px"></div>
              <div ref="rmseChartRef" style="width: 100%; height: 300px"></div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>

    <!-- 对比对话框 -->
    <el-dialog
      v-model="compareDialogVisible"
      title="实验对比分析"
      width="900px"
      destroy-on-close
    >
      <div v-if="compareData">
        <!-- 雷达图 -->
        <div ref="radarChartRef" style="width: 100%; height: 400px"></div>

        <!-- 指标对比表格 -->
        <el-table :data="compareData.metrics" border size="small" class="compare-table">
          <el-table-column prop="name" label="指标名称" width="150" fixed />
          <el-table-column
            v-for="exp in compareData.experiments"
            :key="exp.id"
            :label="exp.experimentName"
            min-width="120"
          >
            <template #default="{ row }">
              {{ row.values.find((v: any) => v.experimentId === exp.id)?.value?.toFixed(4) ?? '-' }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.compare-hint {
  font-size: 12px;
  color: var(--color-warning);
  margin-left: 8px;
}
.experiment-manager {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 统计卡片 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  border-radius: 8px;
}

.stat-card :deep(.el-card__body) {
  padding: 16px 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

/* 筛选栏 */
.filter-card {
  border-radius: 8px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-actions {
  margin-left: auto;
}

/* 表格 */
.table-card {
  border-radius: 8px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

/* JSON 显示 */
.json-display {
  max-height: 400px;
  overflow: auto;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 12px;
  background-color: var(--color-bg);
}

.json-display pre {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: var(--color-text-primary);
  white-space: pre-wrap;
  word-break: break-all;
}

/* 指标网格 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}

.metric-item {
  background-color: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 12px 16px;
  text-align: center;
}

.metric-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
}

.metric-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-primary-light);
}

/* 图表网格 */
.charts-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 哈希代码 */
.hash-code {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  color: var(--color-info);
  background-color: var(--color-bg);
  padding: 2px 8px;
  border-radius: 4px;
}

/* 对比表格 */
.compare-table {
  margin-top: 16px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }
  .filter-actions {
    margin-left: 0;
  }
}
</style>
