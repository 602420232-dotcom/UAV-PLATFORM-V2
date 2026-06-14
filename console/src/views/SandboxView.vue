<script setup lang="ts">
import { onMounted, onUnmounted, ref, shallowRef, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts/core'
import {
  RadarChart as RadarChartSeries,
  HeatmapChart as HeatmapChartSeries,
  LineChart as LineChartSeries,
  ScatterChart as ScatterChartSeries,
} from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  VisualMapComponent,
  RadarComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatDateTime } from '@/utils/format'

echarts.use([
  RadarChartSeries,
  HeatmapChartSeries,
  LineChartSeries,
  ScatterChartSeries,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  VisualMapComponent,
  RadarComponent,
  CanvasRenderer,
])

// ============================================================
// 类型定义
// ============================================================

interface Experiment {
  id: number
  name: string
  description: string
  status: 'running' | 'completed' | 'failed'
  algorithm: string
  algorithmCategory: string
  params: Record<string, unknown>
  createdAt: string
  completedAt: string | null
  executionTime: number
  accuracy: number
  resourceUsage: number
}

interface AlgorithmOption {
  id: number
  name: string
  category: string
  version: string
}

// ============================================================
// 实验管理
// ============================================================

const experiments = ref<Experiment[]>([
  {
    id: 1,
    name: 'A* 路径规划基准测试',
    description: '使用 A* 算法在 100 个随机场景下进行路径规划基准测试',
    status: 'completed',
    algorithm: 'astar_path_planning',
    algorithmCategory: 'planning',
    params: { grid_size: 100, obstacle_density: 0.3 },
    createdAt: '2026-06-12T10:30:00Z',
    completedAt: '2026-06-12T10:35:22Z',
    executionTime: 322,
    accuracy: 0.95,
    resourceUsage: 45,
  },
  {
    id: 2,
    name: '3DVAR 数据同化实验',
    description: '使用 3DVAR 方法对气象场进行数据同化，对比分析同化前后 RMSE',
    status: 'running',
    algorithm: '3dvar_assimilation',
    algorithmCategory: 'assimilation',
    params: { iterations: 10, window_size: 6 },
    createdAt: '2026-06-14T08:00:00Z',
    completedAt: null,
    executionTime: 0,
    accuracy: 0,
    resourceUsage: 72,
  },
  {
    id: 3,
    name: 'RRT* 动态避障对比',
    description: '对比 RRT 和 RRT* 在动态障碍物环境下的路径规划性能',
    status: 'failed',
    algorithm: 'rrt_star_planning',
    algorithmCategory: 'planning',
    params: { max_iter: 5000, step_size: 2.0 },
    createdAt: '2026-06-13T14:20:00Z',
    completedAt: '2026-06-13T14:21:05Z',
    executionTime: 65,
    accuracy: 0,
    resourceUsage: 30,
  },
  {
    id: 4,
    name: 'LSTM 气象预测验证',
    description: '使用 LSTM 模型对 24 小时气象场进行预测验证',
    status: 'completed',
    algorithm: 'lstm_weather_pred',
    algorithmCategory: 'model_engine',
    params: { seq_length: 12, pred_hours: 24, hidden_size: 128 },
    createdAt: '2026-06-11T09:00:00Z',
    completedAt: '2026-06-11T09:15:38Z',
    executionTime: 938,
    accuracy: 0.87,
    resourceUsage: 88,
  },
  {
    id: 5,
    name: '信息增益观测优化',
    description: '基于信息增益的 UAV 观测点优化选择实验',
    status: 'completed',
    algorithm: 'info_gain_observation',
    algorithmCategory: 'observation',
    params: { budget: 10, resolution: 0.5 },
    createdAt: '2026-06-10T16:45:00Z',
    completedAt: '2026-06-10T16:48:12Z',
    executionTime: 192,
    accuracy: 0.92,
    resourceUsage: 35,
  },
])

const experimentStats = computed(() => {
  const total = experiments.value.length
  const running = experiments.value.filter((e) => e.status === 'running').length
  const completed = experiments.value.filter((e) => e.status === 'completed').length
  const failed = experiments.value.filter((e) => e.status === 'failed').length
  return { total, running, completed, failed }
})

// ============================================================
// 创建实验对话框
// ============================================================

const createDialogVisible = ref(false)
const createForm = reactive({
  name: '',
  description: '',
  algorithmId: null as number | null,
  params: '',
})
const createLoading = ref(false)

const algorithmOptions: AlgorithmOption[] = [
  { id: 1, name: 'A* 路径规划', category: 'planning', version: 'v2.1' },
  { id: 2, name: 'RRT* 路径规划', category: 'planning', version: 'v1.3' },
  { id: 3, name: '3DVAR 数据同化', category: 'assimilation', version: 'v2.0' },
  { id: 4, name: 'LSTM 气象预测', category: 'model_engine', version: 'v1.5' },
  { id: 5, name: '信息增益观测', category: 'observation', version: 'v1.2' },
  { id: 6, name: '风险评估模型', category: 'risk', version: 'v1.0' },
]

function openCreateDialog() {
  createForm.name = ''
  createForm.description = ''
  createForm.algorithmId = null
  createForm.params = ''
  createDialogVisible.value = true
}

async function handleCreateExperiment() {
  if (!createForm.name || !createForm.algorithmId) {
    ElMessage.warning('请填写实验名称并选择算法')
    return
  }
  createLoading.value = true
  try {
    let parsedParams: Record<string, unknown> = {}
    if (createForm.params.trim()) {
      parsedParams = JSON.parse(createForm.params)
    }
    const algo = algorithmOptions.find((a) => a.id === createForm.algorithmId)
    const newExperiment: Experiment = {
      id: experiments.value.length + 1,
      name: createForm.name,
      description: createForm.description,
      status: 'running',
      algorithm: algo?.name ?? '',
      algorithmCategory: algo?.category ?? '',
      params: parsedParams,
      createdAt: new Date().toISOString(),
      completedAt: null,
      executionTime: 0,
      accuracy: 0,
      resourceUsage: 50,
    }
    experiments.value.unshift(newExperiment)
    createDialogVisible.value = false
    ElMessage.success('实验创建成功')
  } catch {
    ElMessage.error('参数 JSON 格式错误')
  } finally {
    createLoading.value = false
  }
}

// ============================================================
// 算法对比面板
// ============================================================

const compareAlgorithms = ref<number[]>([])

const comparisonData = [
  { name: 'A* 路径规划', executionTime: 322, accuracy: 0.95, resourceUsage: 45 },
  { name: 'RRT* 路径规划', executionTime: 580, accuracy: 0.97, resourceUsage: 62 },
  { name: 'LSTM 气象预测', executionTime: 938, accuracy: 0.87, resourceUsage: 88 },
  { name: '3DVAR 数据同化', executionTime: 450, accuracy: 0.91, resourceUsage: 55 },
]

const selectedComparison = computed(() => {
  return comparisonData.filter((_, i) => compareAlgorithms.value.includes(i))
})

const radarChartRef = ref<HTMLDivElement>()
const radarChartInstance = shallowRef<echarts.ECharts>()

function initRadarChart() {
  if (!radarChartRef.value || selectedComparison.value.length < 2) return
  radarChartInstance.value = echarts.init(radarChartRef.value)

  const indicators = [
    { name: '执行时间', max: 100 },
    { name: '精度', max: 100 },
    { name: '资源效率', max: 100 },
  ]

  const colors = ['#e94560', '#3498db', '#2ecc71', '#f39c12']

  const seriesData = selectedComparison.value.map((item, i) => ({
    value: [
      Math.max(0, 100 - (item.executionTime / 10)),
      item.accuracy * 100,
      Math.max(0, 100 - item.resourceUsage),
    ],
    name: item.name,
    areaStyle: { opacity: 0.15 },
    lineStyle: { width: 2 },
    itemStyle: { color: colors[i % colors.length] },
  }))

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    title: {
      text: '算法对比雷达图',
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
      data: selectedComparison.value.map((item) => item.name),
      bottom: 10,
      textStyle: { color: '#a0a0b0', fontSize: 12 },
    },
    radar: {
      indicator: indicators,
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#a0a0b0', fontSize: 12 },
      splitLine: { lineStyle: { color: '#3a3a55' } },
      splitArea: { areaStyle: { color: ['rgba(42,42,64,0.3)', 'rgba(42,42,64,0.1)'] } },
      axisLine: { lineStyle: { color: '#3a3a55' } },
      center: ['50%', '55%'],
      radius: '60%',
    },
    series: [
      {
        type: 'radar',
        data: seriesData,
      },
    ],
  }

  radarChartInstance.value.setOption(option, true)
}

function handleCompareToggle(index: number) {
  const idx = compareAlgorithms.value.indexOf(index)
  if (idx >= 0) {
    compareAlgorithms.value.splice(idx, 1)
  } else {
    if (compareAlgorithms.value.length >= 4) {
      ElMessage.warning('最多选择 4 个算法进行对比')
      return
    }
    compareAlgorithms.value.push(index)
  }
  initRadarChart()
}

// ============================================================
// 数据可视化 - 气象场热力图
// ============================================================

const heatmapChartRef = ref<HTMLDivElement>()
const heatmapChartInstance = shallowRef<echarts.ECharts>()

function initHeatmapChart() {
  if (!heatmapChartRef.value) return
  heatmapChartInstance.value = echarts.init(heatmapChartRef.value)

  // 生成模拟气象场数据 (20x20 网格)
  const data: [number, number, number][] = []
  for (let i = 0; i < 20; i++) {
    for (let j = 0; j < 20; j++) {
      const value = Math.round(
        (Math.sin(i / 3) * Math.cos(j / 3) * 30 + 25 + Math.random() * 10) * 10
      ) / 10
      data.push([i, j, value])
    }
  }

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    title: {
      text: '气象场热力图 (模拟数据)',
      textStyle: { color: '#e0e0e0', fontSize: 14 },
      left: 10,
      top: 5,
    },
    tooltip: {
      position: 'top',
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0' },
      formatter: (params: unknown) => {
        const p = params as { data?: [number, number, number] }
        if (p.data) {
          return `坐标: (${p.data[0]}, ${p.data[1]})<br/>温度: ${p.data[2]} C`
        }
        return ''
      },
    },
    grid: {
      top: 50,
      bottom: 50,
      left: 60,
      right: 30,
    },
    xAxis: {
      type: 'category',
      data: Array.from({ length: 20 }, (_, i) => `${i}`),
      splitArea: { show: true },
      axisLabel: { color: '#a0a0b0', fontSize: 10 },
      axisLine: { lineStyle: { color: '#3a3a55' } },
    },
    yAxis: {
      type: 'category',
      data: Array.from({ length: 20 }, (_, i) => `${i}`),
      splitArea: { show: true },
      axisLabel: { color: '#a0a0b0', fontSize: 10 },
      axisLine: { lineStyle: { color: '#3a3a55' } },
    },
    visualMap: {
      min: -5,
      max: 55,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 5,
      textStyle: { color: '#a0a0b0' },
      inRange: {
        color: ['#0f3460', '#1a5276', '#2ecc71', '#f39c12', '#e74c3c'],
      },
    },
    series: [
      {
        type: 'heatmap',
        data: data,
        label: { show: false },
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' },
        },
      },
    ],
  }

  heatmapChartInstance.value.setOption(option)
}

// ============================================================
// 数据可视化 - 路径规划轨迹图
// ============================================================

const trajectoryChartRef = ref<HTMLDivElement>()
const trajectoryChartInstance = shallowRef<echarts.ECharts>()

function initTrajectoryChart() {
  if (!trajectoryChartRef.value) return
  trajectoryChartInstance.value = echarts.init(trajectoryChartRef.value)

  // 生成模拟路径数据
  const generatePath = (startX: number, startY: number, points: number) => {
    const path: [number, number][] = []
    let x = startX
    let y = startY
    for (let i = 0; i < points; i++) {
      x += (Math.random() - 0.4) * 3
      y += (Math.random() - 0.3) * 3
      path.push([Math.round(x * 100) / 100, Math.round(y * 100) / 100])
    }
    return path
  }

  const pathA = generatePath(10, 10, 30)
  const pathB = generatePath(10, 10, 30)
  const pathC = generatePath(10, 10, 30)

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    title: {
      text: '路径规划轨迹对比 (模拟数据)',
      textStyle: { color: '#e0e0e0', fontSize: 14 },
      left: 10,
      top: 5,
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0' },
    },
    legend: {
      data: ['A* 算法', 'RRT* 算法', 'Dijkstra 算法'],
      bottom: 10,
      textStyle: { color: '#a0a0b0', fontSize: 12 },
    },
    grid: {
      top: 50,
      bottom: 50,
      left: 50,
      right: 30,
    },
    xAxis: {
      type: 'value',
      name: 'X (km)',
      nameTextStyle: { color: '#a0a0b0' },
      axisLabel: { color: '#a0a0b0' },
      axisLine: { lineStyle: { color: '#3a3a55' } },
      splitLine: { lineStyle: { color: '#2a2a40' } },
    },
    yAxis: {
      type: 'value',
      name: 'Y (km)',
      nameTextStyle: { color: '#a0a0b0' },
      axisLabel: { color: '#a0a0b0' },
      axisLine: { lineStyle: { color: '#3a3a55' } },
      splitLine: { lineStyle: { color: '#2a2a40' } },
    },
    series: [
      {
        name: 'A* 算法',
        type: 'line',
        data: pathA,
        smooth: false,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { color: '#e94560', width: 2 },
        itemStyle: { color: '#e94560' },
      },
      {
        name: 'RRT* 算法',
        type: 'line',
        data: pathB,
        smooth: false,
        symbol: 'diamond',
        symbolSize: 4,
        lineStyle: { color: '#3498db', width: 2 },
        itemStyle: { color: '#3498db' },
      },
      {
        name: 'Dijkstra 算法',
        type: 'line',
        data: pathC,
        smooth: false,
        symbol: 'triangle',
        symbolSize: 4,
        lineStyle: { color: '#2ecc71', width: 2 },
        itemStyle: { color: '#2ecc71' },
      },
    ],
  }

  trajectoryChartInstance.value.setOption(option)
}

// ============================================================
// 数据可视化 - RMSE 时间序列折线图
// ============================================================

const rmseChartRef = ref<HTMLDivElement>()
const rmseChartInstance = shallowRef<echarts.ECharts>()

function initRmseChart() {
  if (!rmseChartRef.value) return
  rmseChartInstance.value = echarts.init(rmseChartRef.value)

  const hours = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`)

  // 模拟 RMSE 趋势数据
  const rmse3dvar = hours.map((_, i) => {
    return Math.round((5.0 - i * 0.15 + Math.random() * 0.5) * 100) / 100
  })
  const rmseEnkf = hours.map((_, i) => {
    return Math.round((4.5 - i * 0.12 + Math.random() * 0.6) * 100) / 100
  })
  const rmseHybrid = hours.map((_, i) => {
    return Math.round((4.2 - i * 0.18 + Math.random() * 0.4) * 100) / 100
  })

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    title: {
      text: 'RMSE 趋势 (同化后气象场)',
      textStyle: { color: '#e0e0e0', fontSize: 14 },
      left: 10,
      top: 5,
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0' },
    },
    legend: {
      data: ['3DVAR', 'EnKF', 'Hybrid'],
      bottom: 10,
      textStyle: { color: '#a0a0b0', fontSize: 12 },
    },
    grid: {
      top: 50,
      bottom: 50,
      left: 60,
      right: 30,
    },
    xAxis: {
      type: 'category',
      data: hours,
      axisLabel: { color: '#a0a0b0', fontSize: 10, rotate: 45 },
      axisLine: { lineStyle: { color: '#3a3a55' } },
    },
    yAxis: {
      type: 'value',
      name: 'RMSE',
      nameTextStyle: { color: '#a0a0b0' },
      axisLabel: { color: '#a0a0b0' },
      axisLine: { lineStyle: { color: '#3a3a55' } },
      splitLine: { lineStyle: { color: '#2a2a40' } },
    },
    series: [
      {
        name: '3DVAR',
        type: 'line',
        data: rmse3dvar,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#e94560', width: 2 },
        itemStyle: { color: '#e94560' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(233,69,96,0.3)' },
            { offset: 1, color: 'rgba(233,69,96,0.02)' },
          ]),
        },
      },
      {
        name: 'EnKF',
        type: 'line',
        data: rmseEnkf,
        smooth: true,
        symbol: 'diamond',
        symbolSize: 6,
        lineStyle: { color: '#3498db', width: 2 },
        itemStyle: { color: '#3498db' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(52,152,219,0.3)' },
            { offset: 1, color: 'rgba(52,152,219,0.02)' },
          ]),
        },
      },
      {
        name: 'Hybrid',
        type: 'line',
        data: rmseHybrid,
        smooth: true,
        symbol: 'triangle',
        symbolSize: 6,
        lineStyle: { color: '#2ecc71', width: 2 },
        itemStyle: { color: '#2ecc71' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(46,204,113,0.3)' },
            { offset: 1, color: 'rgba(46,204,113,0.02)' },
          ]),
        },
      },
    ],
  }

  rmseChartInstance.value.setOption(option)
}

// ============================================================
// Jupyter 集成区域
// ============================================================

const jupyterUrl = ref('http://localhost:8888/lab')
const jupyterConnected = ref(false)
const jupyterLoading = ref(false)

function launchJupyter() {
  jupyterLoading.value = true
  // 模拟连接检测
  setTimeout(() => {
    jupyterConnected.value = true
    jupyterLoading.value = false
    ElMessage.success('Jupyter Lab 连接成功')
  }, 1500)
}

// ============================================================
// 生命周期
// ============================================================

function handleResize() {
  radarChartInstance.value?.resize()
  heatmapChartInstance.value?.resize()
  trajectoryChartInstance.value?.resize()
  rmseChartInstance.value?.resize()
}

onMounted(() => {
  initHeatmapChart()
  initTrajectoryChart()
  initRmseChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  radarChartInstance.value?.dispose()
  heatmapChartInstance.value?.dispose()
  trajectoryChartInstance.value?.dispose()
  rmseChartInstance.value?.dispose()
})
</script>

<template>
  <div class="sandbox-page">
    <div class="page-header">
      <h2>科研沙箱</h2>
      <el-button type="primary" @click="openCreateDialog">
        创建实验
      </el-button>
    </div>

    <!-- 实验状态卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-title">总实验数</div>
          <div class="stat-value" style="color: #e94560">
            {{ experimentStats.total }}
          </div>
        </div>
        <div class="stat-icon" style="background-color: rgba(233,69,96,0.12)">
          <el-icon :size="22" color="#e94560"><Cpu /></el-icon>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-title">运行中</div>
          <div class="stat-value" style="color: #3498db">
            {{ experimentStats.running }}
          </div>
        </div>
        <div class="stat-icon" style="background-color: rgba(52,152,219,0.12)">
          <el-icon :size="22" color="#3498db"><Loading /></el-icon>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-title">已完成</div>
          <div class="stat-value" style="color: #2ecc71">
            {{ experimentStats.completed }}
          </div>
        </div>
        <div class="stat-icon" style="background-color: rgba(46,204,113,0.12)">
          <el-icon :size="22" color="#2ecc71"><CircleCheck /></el-icon>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-title">失败</div>
          <div class="stat-value" style="color: #e74c3c">
            {{ experimentStats.failed }}
          </div>
        </div>
        <div class="stat-icon" style="background-color: rgba(231,76,60,0.12)">
          <el-icon :size="22" color="#e74c3c"><CircleClose /></el-icon>
        </div>
      </div>
    </div>

    <!-- 实验列表 -->
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>实验列表</span>
        </div>
      </template>
      <el-table :data="experiments" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="实验名称" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <StatusBadge :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="algorithm" label="算法" width="160" show-overflow-tooltip />
        <el-table-column prop="algorithmCategory" label="类别" width="100">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" style="border: none">
              {{ row.algorithmCategory }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="执行时间" width="100">
          <template #default="{ row }">
            {{ row.executionTime > 0 ? `${row.executionTime}s` : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="精度" width="80">
          <template #default="{ row }">
            {{ row.accuracy > 0 ? `${(row.accuracy * 100).toFixed(1)}%` : '-' }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 算法对比面板 -->
    <el-card class="compare-card">
      <template #header>
        <div class="card-header">
          <span>算法对比面板</span>
          <span class="card-hint">选择 2-4 个算法进行对比</span>
        </div>
      </template>
      <div class="compare-content">
        <div class="compare-select">
          <el-checkbox-group>
            <el-checkbox
              v-for="(algo, index) in comparisonData"
              :key="algo.name"
              :model-value="compareAlgorithms.includes(index)"
              @change="handleCompareToggle(index)"
            >
              {{ algo.name }}
            </el-checkbox>
          </el-checkbox-group>
        </div>
        <div v-if="selectedComparison.length >= 2" class="compare-detail">
          <el-table :data="selectedComparison" size="small" stripe style="width: 100%">
            <el-table-column prop="name" label="算法名称" />
            <el-table-column label="执行时间" width="120">
              <template #default="{ row }">
                {{ row.executionTime }}s
              </template>
            </el-table-column>
            <el-table-column label="精度" width="100">
              <template #default="{ row }">
                {{ (row.accuracy * 100).toFixed(1) }}%
              </template>
            </el-table-column>
            <el-table-column label="资源消耗" width="100">
              <template #default="{ row }">
                {{ row.resourceUsage }}%
              </template>
            </el-table-column>
          </el-table>
        </div>
        <div ref="radarChartRef" style="width: 100%; height: 380px"></div>
      </div>
    </el-card>

    <!-- 数据可视化 -->
    <div class="charts-row">
      <el-card class="chart-card">
        <div ref="heatmapChartRef" style="width: 100%; height: 380px"></div>
      </el-card>
      <el-card class="chart-card">
        <div ref="trajectoryChartRef" style="width: 100%; height: 380px"></div>
      </el-card>
    </div>

    <el-card class="chart-card">
      <div ref="rmseChartRef" style="width: 100%; height: 380px"></div>
    </el-card>

    <!-- Jupyter 集成区域 -->
    <el-card class="jupyter-card">
      <template #header>
        <div class="card-header">
          <span>Jupyter Lab 集成</span>
          <el-button
            type="primary"
            size="small"
            :loading="jupyterLoading"
            @click="launchJupyter"
          >
            {{ jupyterConnected ? '已连接' : '快速启动' }}
          </el-button>
        </div>
      </template>
      <div class="jupyter-content">
        <div class="jupyter-config">
          <el-form label-width="100px" size="small">
            <el-form-item label="Jupyter URL">
              <el-input
                v-model="jupyterUrl"
                placeholder="http://localhost:8888/lab"
                style="width: 400px"
              />
            </el-form-item>
          </el-form>
        </div>
        <div class="jupyter-frame">
          <div v-if="!jupyterConnected" class="jupyter-placeholder">
            <el-icon :size="48" color="#3a3a55"><Monitor /></el-icon>
            <p>配置 Jupyter Lab URL 后点击"快速启动"连接</p>
          </div>
          <iframe
            v-else
            :src="jupyterUrl"
            frameborder="0"
            style="width: 100%; height: 500px; border-radius: 4px"
            allow="clipboard-read; clipboard-write"
          />
        </div>
      </div>
    </el-card>

    <!-- 创建实验对话框 -->
    <el-dialog v-model="createDialogVisible" title="创建新实验" width="600px">
      <el-form label-width="100px">
        <el-form-item label="实验名称" required>
          <el-input v-model="createForm.name" placeholder="输入实验名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="输入实验描述"
          />
        </el-form-item>
        <el-form-item label="选择算法" required>
          <el-select
            v-model="createForm.algorithmId"
            placeholder="选择算法"
            style="width: 100%"
          >
            <el-option
              v-for="algo in algorithmOptions"
              :key="algo.id"
              :label="`${algo.name} (${algo.version})`"
              :value="algo.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="参数配置">
          <el-input
            v-model="createForm.params"
            type="textarea"
            :rows="5"
            placeholder='输入 JSON 参数，如: {"grid_size": 100, "iterations": 10}'
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreateExperiment">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.sandbox-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* 统计卡片 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat-card {
  background-color: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: border-color 0.2s;
}

.stat-card:hover {
  border-color: var(--color-border-light);
}

.stat-info {
  flex: 1;
}

.stat-title {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* 卡片 */
.table-card,
.compare-card,
.chart-card,
.jupyter-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-hint {
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* 算法对比 */
.compare-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.compare-select {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

/* 图表 */
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

/* Jupyter */
.jupyter-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.jupyter-frame {
  border: 1px solid var(--color-border);
  border-radius: 4px;
  overflow: hidden;
}

.jupyter-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 500px;
  gap: 12px;
  color: var(--color-text-secondary);
  font-size: 14px;
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
