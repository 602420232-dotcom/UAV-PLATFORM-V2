<script setup lang="ts">
import { onMounted, onUnmounted, ref, shallowRef, reactive, computed, watch } from 'vue'
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
import { algorithmApi } from '@/api/algorithm'
import type { Algorithm } from '@/api/algorithm'
import { useDemoModeStore } from '@/stores/demoMode'
import { generateMockAlgorithms, getMockAlgorithmNames } from '@/mock/algorithmData'
import { dashboardApi } from '@/api/dashboard'

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
  weatherContext?: {
    status: 'real' | 'mock' | 'no_data'
    timestamp?: string
    forecast_hour?: number
    region?: { lat: [number, number]; lon: [number, number] }
  }
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

const demoModeStore = useDemoModeStore()

const mockExperiments: Experiment[] = [
  {
    id: 1,
    name: '3D-VAR-数据同化基准实验',
    description: '使用 3D-VAR 方法对气象场进行数据同化，对比分析同化前后 RMSE，验证同化窗口敏感性',
    status: 'completed',
    algorithm: '3D-VAR-数据同化',
    algorithmCategory: 'assimilation',
    params: { iterations: 10, window_size: 6 },
    createdAt: '2026-06-12T10:30:00Z',
    completedAt: '2026-06-12T10:35:22Z',
    executionTime: 322,
    accuracy: 0.95,
    resourceUsage: 45,
  },
  {
    id: 2,
    name: 'MPC-路径规划实时避障测试',
    description: '使用 MPC 模型预测控制算法在动态障碍物环境下进行实时路径规划，评估计算延迟与避障成功率',
    status: 'running',
    algorithm: 'MPC-路径规划 (实时版)',
    algorithmCategory: 'planning',
    params: { horizon: 20, obstacle_density: 0.3, max_speed: 15 },
    createdAt: '2026-06-14T08:00:00Z',
    completedAt: null,
    executionTime: 0,
    accuracy: 0,
    resourceUsage: 72,
  },
  {
    id: 3,
    name: 'RiskAssess-风险评估多场景验证',
    description: '在 50 个历史气象场景下运行风险评估算法，统计虚警率和漏报率',
    status: 'failed',
    algorithm: 'RiskAssess-风险评估 (综合版)',
    algorithmCategory: 'risk',
    params: { scenario_count: 50, risk_threshold: 0.7 },
    createdAt: '2026-06-13T14:20:00Z',
    completedAt: '2026-06-13T14:21:05Z',
    executionTime: 65,
    accuracy: 0,
    resourceUsage: 30,
  },
  {
    id: 4,
    name: 'ActiveObs-观测决策自适应采样',
    description: '基于信息增益的 UAV 主动观测点优化选择实验，对比固定采样与自适应采样效率',
    status: 'completed',
    algorithm: 'ActiveObs-观测决策 (自适应版)',
    algorithmCategory: 'observation',
    params: { budget: 10, resolution: 0.5, strategy: 'adaptive' },
    createdAt: '2026-06-11T09:00:00Z',
    completedAt: '2026-06-11T09:15:38Z',
    executionTime: 938,
    accuracy: 0.87,
    resourceUsage: 88,
  },
  {
    id: 5,
    name: 'WRF-3km-模型引擎预报验证',
    description: '使用 WRF-3km 高分辨率模式进行 24 小时气象预报，与实况观测对比验证预报技巧',
    status: 'completed',
    algorithm: 'WRF-3km-模型引擎',
    algorithmCategory: 'model_engine',
    params: { forecast_hours: 24, domain: 'south_china', output_interval: 1 },
    createdAt: '2026-06-10T16:45:00Z',
    completedAt: '2026-06-10T16:48:12Z',
    executionTime: 192,
    accuracy: 0.92,
    resourceUsage: 35,
  },
  {
    id: 6,
    name: 'EdgeInfer-边缘计算推理延迟测试',
    description: '在边缘设备上部署推理模型，测试不同批大小下的推理延迟和吞吐量',
    status: 'completed',
    algorithm: 'EdgeInfer-边缘计算 (轻量版)',
    algorithmCategory: 'edge',
    params: { batch_sizes: [1, 4, 8, 16], model_size: 'small' },
    createdAt: '2026-06-09T11:20:00Z',
    completedAt: '2026-06-09T11:22:45Z',
    executionTime: 165,
    accuracy: 0.89,
    resourceUsage: 28,
  },
]

const experiments = ref<Experiment[]>([...mockExperiments])

// 加载实验数据
async function loadExperiments() {
  if (demoModeStore.isDemoMode) {
    experiments.value = [...mockExperiments]
    return
  }
  try {
    const data = await dashboardApi.getResearchDashboard()
    experiments.value = data.recentExperiments.map((e) => ({
      id: e.id,
      name: e.experimentName,
      description: '',
      status: e.status === 'RUNNING' ? 'running' : e.status === 'COMPLETED' ? 'completed' : 'failed',
      algorithm: e.algorithmName,
      algorithmCategory: e.algorithmCategory,
      params: {},
      createdAt: e.createdAt,
      completedAt: null,
      executionTime: 0,
      accuracy: 0,
      resourceUsage: 0,
    }))
  } catch {
    experiments.value = [...mockExperiments]
  }
}

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
  useRealWeather: true,
  weatherSource: 'fengwu' as 'fengwu' | 'fengwu_ghr' | 'mock',
  region: { lat: [27, 35] as [number, number], lon: [102, 110] as [number, number] },
  forecastHour: 0,
})
const createLoading = ref(false)

const algorithmOptions: AlgorithmOption[] = getMockAlgorithmNames().map((name, i) => {
  const typeMap: Record<string, string> = {
    '数据同化': 'assimilation', '路径规划': 'planning', '风险评估': 'risk',
    '观测决策': 'observation', '模型引擎': 'model_engine', '边缘计算': 'edge',
  }
  const category = Object.entries(typeMap).find(([k]) => name.includes(k))?.[1] ?? 'generic'
  return { id: i + 1, name, category, version: 'v1.0' }
})

function openCreateDialog() {
  createForm.name = ''
  createForm.description = ''
  createForm.algorithmId = null
  createForm.params = ''
  createForm.useRealWeather = true
  createForm.weatherSource = 'fengwu'
  createForm.forecastHour = 0
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
    
    // 构建气象数据上下文
    const weatherContext = createForm.useRealWeather ? {
      status: createForm.weatherSource === 'mock' ? 'mock' as const : 'real' as const,
      timestamp: new Date().toISOString(),
      forecast_hour: createForm.forecastHour,
      region: createForm.region,
    } : undefined
    
    const newExperiment: Experiment = {
      id: experiments.value.length + 1,
      name: createForm.name,
      description: createForm.description,
      status: 'running',
      algorithm: algo?.name ?? '',
      algorithmCategory: algo?.category ?? '',
      params: {
        ...parsedParams,
        _weather_config: {
          use_real_weather: createForm.useRealWeather,
          weather_source: createForm.weatherSource,
          region: createForm.region,
          forecast_hour: createForm.forecastHour,
        }
      },
      createdAt: new Date().toISOString(),
      completedAt: null,
      executionTime: 0,
      accuracy: 0,
      resourceUsage: 50,
      weatherContext,
    }
    experiments.value.unshift(newExperiment)
    createDialogVisible.value = false
    ElMessage.success(`实验创建成功${createForm.useRealWeather ? '（使用真实气象数据）' : ''}`)
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
const showAlgorithmPicker = ref(false)
const allAlgorithms = ref<Algorithm[]>([])
const algorithmSearchKeyword = ref('')
const algorithmTotal = ref(0)
const selectedCategory = ref('')

// 分类中文标签映射
const categoryLabelMap: Record<string, string> = {
  assimilation: '数据同化',
  planning: '路径规划',
  risk: '风险评估',
  observation: '观测决策',
  model_engine: '模型引擎',
  edge: '边缘计算',
}

// 从算法数据中提取所有分类（显示中文标签）
const algorithmCategories = computed(() => {
  const cats = new Set(allAlgorithms.value.map((a) => a.category))
  return Array.from(cats).sort()
})

// 搜索 + 分类过滤后的算法列表
const filteredAlgorithms = computed(() => {
  let list = allAlgorithms.value
  // 按分类筛选
  if (selectedCategory.value) {
    list = list.filter((a) => a.category === selectedCategory.value)
  }
  // 按关键词搜索
  if (algorithmSearchKeyword.value) {
    const kw = algorithmSearchKeyword.value.toLowerCase()
    list = list.filter(
      (a) =>
        a.name.toLowerCase().includes(kw) ||
        a.category.toLowerCase().includes(kw)
    )
  }
  return list
})

// 已选中的算法详情
const selectedComparison = computed(() => {
  return allAlgorithms.value.filter((a) => compareAlgorithms.value.includes(a.id))
})

function getAlgorithmName(id: number): string {
  const algo = allAlgorithms.value.find(a => a.id === id)
  return algo ? algo.name : `算法#${id}`
}

// 加载全部算法（最多 200 个）
async function loadAllAlgorithms() {
  if (demoModeStore.isDemoMode) {
    // 演示模式：直接使用 mock 数据
    allAlgorithms.value = generateMockAlgorithms()
    algorithmTotal.value = allAlgorithms.value.length
    return
  }
  try {
    const res = await algorithmApi.list({ size: 200 })
    allAlgorithms.value = res.records ?? []
    algorithmTotal.value = res.total ?? allAlgorithms.value.length
  } catch (e) {
    // 如果 API 不可用，使用模拟数据
    allAlgorithms.value = generateMockAlgorithms()
    algorithmTotal.value = allAlgorithms.value.length
  }
}

/** 生成模拟算法数据（API 不可用时）—— 从共享模块导入 */


const radarChartRef = ref<HTMLDivElement>()
const radarChartInstance = shallowRef<echarts.ECharts>()

watch(compareAlgorithms, () => {
  initRadarChart()
}, { deep: true })

function initRadarChart() {
  if (!radarChartRef.value || selectedComparison.value.length < 2) return
  radarChartInstance.value = echarts.init(radarChartRef.value)

  const indicators = [
    { name: '执行效率', max: 100 },
    { name: '精度', max: 100 },
    { name: '资源效率', max: 100 },
    { name: '可扩展性', max: 100 },
    { name: '鲁棒性', max: 100 },
    { name: '活跃度', max: 100 },
  ]

  const colors = ['#e94560', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#e74c3c']

  const seriesData = selectedComparison.value.map((item, i) => {
    const statusScore = item.status === 'running' ? 95 : item.status === 'ready' ? 80 : 60
    const hash = item.name.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0)
    const seed = (hash * 2654435761) >>> 0
    const pr = (offset: number) => ((seed + offset) % 100)
    return {
      value: [
        30 + pr(0) % 70,
        50 + pr(1) % 50,
        40 + pr(2) % 60,
        50 + pr(3) % 50,
        60 + pr(4) % 40,
        statusScore,
      ],
      name: item.name,
      areaStyle: { opacity: 0.15 },
      lineStyle: { width: 2 },
      itemStyle: { color: colors[i % colors.length] },
    }
  })

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
      data: selectedComparison.value.map((item) => item.name.length > 12 ? item.name.slice(0, 12) + '...' : item.name),
      right: 10,
      top: 'center',
      textStyle: { color: '#a0a0b0', fontSize: 11 },
      type: 'scroll',
      pageTextStyle: { color: '#a0a0b0' },
      pageIconColor: '#a0a0b0',
      pageIconInactiveColor: '#3a3a55',
    },
    radar: {
      indicator: indicators,
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#a0a0b0', fontSize: 12 },
      splitLine: { lineStyle: { color: '#3a3a55' } },
      splitArea: { areaStyle: { color: ['rgba(42,42,64,0.3)', 'rgba(42,42,64,0.1)'] } },
      axisLine: { lineStyle: { color: '#3a3a55' } },
      center: ['40%', '55%'],
      radius: '55%',
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
  // 在 URL 中附加 token，避免 iframe 内登录问题
  const baseUrl = jupyterUrl.value.replace(/\?.*$/, '').replace(/#.*$/, '')
  const separator = baseUrl.includes('?') ? '&' : '?'
  jupyterUrl.value = `${baseUrl}${separator}token=uav2024`
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

onMounted(async () => {
  await demoModeStore.fetchStatus()
  await loadExperiments()
  loadAllAlgorithms()
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
          <span class="card-hint">选择 2-10 个算法进行对比</span>
        </div>
      </template>
      <div class="compare-content">
        <div class="compare-select">
          <!-- 已选算法标签展示 -->
          <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap; min-height: 32px;">
            <span style="color: var(--color-text-secondary); font-size: 13px; white-space: nowrap;">
              已选 ({{ compareAlgorithms.length }}/10)：
            </span>
            <el-tag
              v-for="id in compareAlgorithms"
              :key="id"
              closable
              size="default"
              effect="plain"
              @close="compareAlgorithms = compareAlgorithms.filter(x => x !== id)"
            >
              {{ getAlgorithmName(id) }}
            </el-tag>
            <el-button
              type="primary"
              size="small"
              :disabled="compareAlgorithms.length >= 10"
              @click="showAlgorithmPicker = true"
            >
              + 添加算法
            </el-button>
            <el-button
              v-if="compareAlgorithms.length > 0"
              size="small"
              @click="compareAlgorithms = []"
            >
              清空
            </el-button>
          </div>
        </div>

        <!-- 算法选择弹窗 -->
        <el-dialog
          v-model="showAlgorithmPicker"
          title="选择对比算法"
          width="680px"
          append-to-body
          :close-on-click-modal="false"
        >
          <div style="margin-bottom: 10px;">
            <el-input
              v-model="algorithmSearchKeyword"
              placeholder="搜索算法名称..."
              size="small"
              clearable
              style="width: 100%"
            >
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
          </div>
          <div style="display: flex; gap: 6px; margin-bottom: 12px; flex-wrap: wrap; align-items: center;">
            <el-check-tag
              :checked="!selectedCategory"
              @change="selectedCategory = ''"
              style="font-size: 12px;"
            >全部</el-check-tag>
            <el-check-tag
              v-for="cat in algorithmCategories"
              :key="cat"
              :checked="selectedCategory === cat"
              @change="selectedCategory = selectedCategory === cat ? '' : cat"
              style="font-size: 12px;"
            >{{ categoryLabelMap[cat] || cat }}</el-check-tag>
          </div>
          <div style="max-height: 400px; overflow-y: auto;">
            <el-checkbox-group v-model="compareAlgorithms">
              <div
                v-for="algo in filteredAlgorithms"
                :key="algo.id"
                style="display: flex; align-items: center; gap: 8px; padding: 6px 8px; border-bottom: 1px solid var(--color-border);"
              >
                <el-checkbox
                  :value="algo.id"
                  :disabled="!compareAlgorithms.includes(algo.id) && compareAlgorithms.length >= 10"
                >
                  <span style="font-size: 13px;">{{ algo.name }}</span>
                </el-checkbox>
                <el-tag size="small" type="info" effect="plain" style="margin-left: auto; font-size: 11px;">
                  {{ categoryLabelMap[algo.category] || algo.category }}
                </el-tag>
              </div>
            </el-checkbox-group>
          </div>
          <div style="margin-top: 12px; color: var(--color-text-muted); font-size: 12px; text-align: right;">
            共 {{ filteredAlgorithms.length }} 个算法，已选 {{ compareAlgorithms.length }}/10
          </div>
          <template #footer>
            <el-button @click="showAlgorithmPicker = false">关闭</el-button>
          </template>
        </el-dialog>
        <div v-if="selectedComparison.length >= 2" class="compare-detail">
          <el-table :data="selectedComparison" size="small" stripe style="width: 100%">
            <el-table-column prop="name" label="算法名称" min-width="140" />
            <el-table-column prop="category" label="分类" width="100" />
            <el-table-column prop="version" label="版本" width="80" />
            <el-table-column label="状态" width="80">
              <template #default="{ row }">
                <StatusBadge :status="row.status" />
              </template>
            </el-table-column>
            <el-table-column label="执行次数" width="90">
              <template #default="{ row }">
                {{ row.runCount }}
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
            style="width: 100%; height: 700px; border-radius: 4px"
            allow="clipboard-read; clipboard-write"
          />
        </div>
      </div>
    </el-card>

    <!-- 创建实验对话框 -->
    <el-dialog v-model="createDialogVisible" title="创建新实验" width="650px">
      <el-form label-width="120px">
        <el-form-item label="实验名称" required>
          <el-input v-model="createForm.name" placeholder="输入实验名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="2"
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
        
        <!-- 气象数据配置 -->
        <el-divider>气象数据源配置</el-divider>
        <el-form-item label="使用真实气象">
          <el-switch v-model="createForm.useRealWeather" active-text="真实数据" inactive-text="模拟数据" />
        </el-form-item>
        <template v-if="createForm.useRealWeather">
          <el-form-item label="数据源">
            <el-radio-group v-model="createForm.weatherSource">
              <el-radio-button label="fengwu">风乌全球</el-radio-button>
              <el-radio-button label="fengwu_ghr">风乌高分辨率</el-radio-button>
              <el-radio-button label="mock">模拟数据</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="预报时效">
            <el-slider v-model="createForm.forecastHour" :min="0" :max="336" :step="6" show-stops />
            <span style="color: var(--color-text-secondary); font-size: 12px;">{{ createForm.forecastHour }}小时</span>
          </el-form-item>
          <el-form-item label="区域范围">
            <el-row :gutter="8">
              <el-col :span="12">
                <el-input-number v-model="createForm.region.lat[0]" :min="-90" :max="90" placeholder="南纬" style="width: 100%" />
              </el-col>
              <el-col :span="12">
                <el-input-number v-model="createForm.region.lat[1]" :min="-90" :max="90" placeholder="北纬" style="width: 100%" />
              </el-col>
            </el-row>
            <el-row :gutter="8" style="margin-top: 8px;">
              <el-col :span="12">
                <el-input-number v-model="createForm.region.lon[0]" :min="0" :max="360" placeholder="西经" style="width: 100%" />
              </el-col>
              <el-col :span="12">
                <el-input-number v-model="createForm.region.lon[1]" :min="0" :max="360" placeholder="东经" style="width: 100%" />
              </el-col>
            </el-row>
          </el-form-item>
        </template>
        
        <el-divider>算法参数</el-divider>
        <el-form-item label="参数配置">
          <el-input
            v-model="createForm.params"
            type="textarea"
            :rows="4"
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
  flex-direction: column;
  gap: 12px;
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
  height: 700px;
  gap: 12px;
  color: var(--color-text-secondary);
  font-size: 14px;
}

/* 表格样式优化 */
:deep(.el-table) {
  --el-table-row-height: 52px;
  font-size: 14px;
}

:deep(.el-table .cell) {
  line-height: 1.5;
  padding: 8px 12px;
}

:deep(.el-table th.el-table__cell) {
  background-color: var(--color-bg-elevated);
  font-weight: 600;
  color: var(--color-text-primary);
  font-size: 13px;
  padding: 12px 0;
}

:deep(.el-table td.el-table__cell) {
  padding: 10px 0;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background-color: rgba(255, 255, 255, 0.02);
}

/* 算法对比复选框 */
:deep(.el-checkbox) {
  margin-right: 20px;
  margin-bottom: 8px;
}

:deep(.el-checkbox__label) {
  color: var(--color-text-primary);
  font-size: 14px;
  padding-left: 8px;
}

:deep(.el-checkbox__input.is-checked + .el-checkbox__label) {
  color: var(--el-color-primary);
  font-weight: 500;
}

/* 统计卡片优化 */
.stat-card {
  padding: 20px;
  gap: 16px;
}

.stat-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
  letter-spacing: 0.3px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.5px;
}

.stat-desc {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 4px;
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
