<script setup lang="ts">
import { onMounted, onUnmounted, ref, shallowRef, nextTick, computed, watch } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart as LineChartSeries, BarChart as BarChartSeries } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'
import { ElMessage } from 'element-plus'
import { algorithmApi } from '@/api/algorithm'
import type { Algorithm } from '@/api/algorithm'
import { formatDateTime } from '@/utils/format'
import { useDemoModeStore } from '@/stores/demoMode'
import { generateMockAlgorithms } from '@/mock/algorithmData'
const demoModeStore = useDemoModeStore()

echarts.use([
  LineChartSeries,
  BarChartSeries,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  CanvasRenderer,
])

// ==================== 算法分类树 ====================
interface CategoryNode {
  id: string
  label: string
  icon: string
  children: Algorithm[]
}

const categories = ref<CategoryNode[]>([
  { id: 'assimilation', label: '数据同化', icon: 'DataAnalysis', children: [] },
  { id: 'planning', label: '路径规划', icon: 'Guide', children: [] },
  { id: 'risk', label: '风险评估', icon: 'Warning', children: [] },
  { id: 'observation', label: '观测决策', icon: 'View', children: [] },
  { id: 'model_engine', label: '模型引擎', icon: 'Cpu', children: [] },
  { id: 'edge', label: '边缘计算', icon: 'Monitor', children: [] },
])

const expandedKeys = ref<string[]>([])
const selectedAlgorithm = ref<Algorithm | null>(null)
const treeLoading = ref(false)

// ==================== 参数面板 ====================
interface ParamField {
  key: string
  label: string
  type: 'slider' | 'number' | 'select' | 'json'
  min?: number
  max?: number
  step?: number
  options?: Array<{ label: string; value: string | number }>
  default?: unknown
}

const paramFields = ref<ParamField[]>([])
const paramValues = ref<Record<string, unknown>>({})
const jsonEditorContent = ref('')

// ==================== 运行控制 ====================
const isRunning = ref(false)
const runStatus = ref<'idle' | 'running' | 'success' | 'error'>('idle')
const runProgress = ref(0)
const runLog = ref<string[]>([])
let runTimer: ReturnType<typeof setInterval> | null = null

// ==================== 参数调整历史 ====================
interface ParamRecord {
  id: string
  algorithmId: number
  algorithmName: string
  params: Record<string, unknown>
  result: { success: boolean; executionTime: number; accuracy?: number }
  timestamp: string
}

const paramHistory = ref<ParamRecord[]>([])
const compareIds = ref<string[]>([])
const compareVisible = ref(false)

function loadParamHistory() {
  if (!selectedAlgorithm.value) return
  const key = `algo_param_history_${selectedAlgorithm.value.id}`
  try {
    const data = localStorage.getItem(key)
    paramHistory.value = data ? JSON.parse(data) : []
  } catch {
    paramHistory.value = []
  }
  compareIds.value = []
  compareVisible.value = false
}

function saveParamRecord(result: { success: boolean; executionTime: number; accuracy?: number }) {
  if (!selectedAlgorithm.value) return
  const record: ParamRecord = {
    id: Date.now().toString(36),
    algorithmId: selectedAlgorithm.value.id,
    algorithmName: selectedAlgorithm.value.name,
    params: { ...paramValues.value },
    result,
    timestamp: new Date().toISOString(),
  }
  paramHistory.value.unshift(record)
  // 最多保留 50 条
  if (paramHistory.value.length > 50) paramHistory.value = paramHistory.value.slice(0, 50)
  const key = `algo_param_history_${selectedAlgorithm.value.id}`
  localStorage.setItem(key, JSON.stringify(paramHistory.value))
}

function restoreParams(record: ParamRecord) {
  paramValues.value = { ...record.params }
  // 如果有 JSON 类型参数，同步更新 jsonEditorContent
  for (const field of paramFields.value) {
    if (field.type === 'json' && record.params[field.key]) {
      jsonEditorContent.value = JSON.stringify(record.params[field.key], null, 2)
    }
  }
  ElMessage.success('已恢复历史参数')
}

function deleteParamRecord(id: string) {
  paramHistory.value = paramHistory.value.filter(r => r.id !== id)
  compareIds.value = compareIds.value.filter(cid => cid !== id)
  const key = `algo_param_history_${selectedAlgorithm.value?.id}`
  if (key) localStorage.setItem(key, JSON.stringify(paramHistory.value))
}

function clearParamHistory() {
  paramHistory.value = []
  compareIds.value = []
  compareVisible.value = false
  const key = `algo_param_history_${selectedAlgorithm.value?.id}`
  if (key) localStorage.removeItem(key)
}

function toggleCompare(id: string) {
  const idx = compareIds.value.indexOf(id)
  if (idx >= 0) {
    compareIds.value.splice(idx, 1)
  } else {
    if (compareIds.value.length >= 2) {
      ElMessage.warning('最多选择 2 条记录进行对比')
      return
    }
    compareIds.value.push(id)
  }
  if (compareIds.value.length < 2) {
    compareVisible.value = false
  }
}

function showCompare() {
  if (compareIds.value.length === 2) {
    compareVisible.value = true
  }
}

function closeCompare() {
  compareVisible.value = false
}

const compareRecords = computed(() => {
  return compareIds.value
    .map(id => paramHistory.value.find(r => r.id === id))
    .filter((r): r is ParamRecord => !!r)
})

const compareDiff = computed(() => {
  if (compareRecords.value.length !== 2) return []
  const a = compareRecords.value[0]
  const b = compareRecords.value[1]
  if (!a || !b) return []
  const allKeys = Array.from(new Set([...Object.keys(a.params), ...Object.keys(b.params)]))
  return allKeys.map(key => ({
    key,
    valueA: a.params[key],
    valueB: b.params[key],
    changed: JSON.stringify(a.params[key]) !== JSON.stringify(b.params[key]),
  }))
})

function formatHistoryTime(iso: string): string {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

// ==================== 运行结果 ====================
const resultData = ref<Record<string, unknown> | null>(null)
const resultJsonStr = ref('')
const resultChartRef = ref<HTMLDivElement>()
const resultChartInstance = shallowRef<echarts.ECharts>()
const activeResultTab = ref('chart')

// ==================== 算法详情 ====================
const algorithmDetail = ref<Algorithm | null>(null)

// ==================== 方法 ====================

// Mock 算法数据 —— 从共享模块导入


async function loadAlgorithms() {
  treeLoading.value = true
  try {
    let records: Algorithm[] = []
    
    if (demoModeStore.isDemoMode) {
      // 演示模式：使用 mock 数据
      records = generateMockAlgorithms()
    } else {
      // 生产模式：请求后端
      const allAlgos = await algorithmApi.list({ size: 200 })
      records = allAlgos.records ?? []
    }
    
    categories.value.forEach((cat) => {
      cat.children = records.filter((a) => a.category === cat.id || a.type === cat.id)
    })
    
    // 默认展开有算法的分类
    expandedKeys.value = categories.value.filter(c => c.children.length > 0).map(c => c.id)
  } catch {
    if (demoModeStore.isDemoMode) {
      // 演示模式不应该失败
      categories.value.forEach((cat) => { cat.children = [] })
    } else {
      // 生产模式：可能是权限不足
      ElMessage.warning('加载算法列表失败，请检查登录状态或权限')
      categories.value.forEach((cat) => { cat.children = [] })
    }
  } finally {
    treeLoading.value = false
  }
}

function handleSelectAlgorithm(algo: Algorithm) {
  selectedAlgorithm.value = algo
  loadAlgorithmDetail(algo)
  buildParamFields(algo)
  resetRunState()
  loadParamHistory()
}

async function loadAlgorithmDetail(algo: Algorithm) {
  try {
    algorithmDetail.value = await algorithmApi.getDetail(algo.id)
  } catch {
    algorithmDetail.value = algo
  }
}

// ==================== 算法参数映射表 ====================
// ALGO_PARAM_MAP: key 为算法名称前缀，value 为该系列基础参数数组
const ALGO_PARAM_MAP: Record<string, ParamField[]> = {
  // ---- 1. 数据同化系列 ----
  '3D-VAR': [
    { key: 'assimWindow', label: '同化窗口时长 (h)', type: 'slider', min: 1, max: 24, step: 1, default: 6 },
    { key: 'bgErrorScale', label: '背景场误差协方差缩放', type: 'slider', min: 0.5, max: 3.0, step: 0.1, default: 1.0 },
    { key: 'obsErrorScale', label: '观测误差缩放', type: 'slider', min: 0.5, max: 3.0, step: 0.1, default: 1.0 },
    { key: 'minIterations', label: '最小化迭代次数', type: 'number', default: 50 },
    { key: 'analysisVar', label: '变分分析变量', type: 'select', options: [
      { label: '温度', value: 'temperature' },
      { label: '湿度', value: 'humidity' },
      { label: '风', value: 'wind' },
      { label: '全部', value: 'all' },
    ], default: 'all' },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  '4D-VAR': [
    { key: 'assimWindow', label: '同化窗口时长 (h)', type: 'slider', min: 1, max: 24, step: 1, default: 6 },
    { key: 'timeDiscretization', label: '时间离散化步长 (min)', type: 'select', options: [
      { label: '5', value: 5 },
      { label: '10', value: 10 },
      { label: '15', value: 15 },
      { label: '30', value: 30 },
    ], default: 15 },
    { key: 'outerLoopIter', label: '外循环迭代次数', type: 'number', default: 30 },
    { key: 'innerLoopIter', label: '内循环迭代次数', type: 'number', default: 5 },
    { key: 'bgErrorType', label: '背景场误差协方差', type: 'select', options: [
      { label: '静态', value: 'static' },
      { label: '流依赖', value: 'flow_dependent' },
      { label: '混合', value: 'hybrid' },
    ], default: 'hybrid' },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  '5D-VAR': [
    { key: 'assimWindow', label: '同化窗口时长 (h)', type: 'slider', min: 1, max: 48, step: 1, default: 12 },
    { key: 'timeResolution', label: '时间维度分辨率', type: 'select', options: [
      { label: '5min', value: '5min' },
      { label: '10min', value: '10min' },
      { label: '15min', value: '15min' },
      { label: '30min', value: '30min' },
    ], default: '10min' },
    { key: 'physicsConstraint', label: '物理约束强度', type: 'slider', min: 0, max: 1, step: 0.05, default: 0.3 },
    { key: 'digitalFilter', label: '数字滤波强度', type: 'slider', min: 0, max: 1, step: 0.05, default: 0.5 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'EnKF': [
    { key: 'ensembleSize', label: '集合成员数', type: 'slider', min: 10, max: 200, step: 5, default: 50 },
    { key: 'inflationFactor', label: '膨胀因子', type: 'slider', min: 1.0, max: 2.0, step: 0.05, default: 1.1 },
    { key: 'localizationRadius', label: '局地化半径 (km)', type: 'slider', min: 10, max: 500, step: 10, default: 150 },
    { key: 'obsPerturbation', label: '观测扰动', type: 'select', options: [
      { label: '无', value: 'none' },
      { label: '高斯', value: 'gaussian' },
      { label: '随机', value: 'random' },
    ], default: 'gaussian' },
    { key: 'multiVarCoupling', label: '多变量耦合', type: 'select', options: [
      { label: '单变量', value: 'single' },
      { label: '多变量', value: 'multi' },
    ], default: 'multi' },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'Hybrid-EnVar': [
    { key: 'enkfWeight', label: 'EnKF 权重', type: 'slider', min: 0, max: 1, step: 0.05, default: 0.5 },
    { key: 'ensembleSize', label: '集合成员数', type: 'slider', min: 10, max: 100, step: 5, default: 30 },
    { key: 'localizationRadius', label: '局地化半径 (km)', type: 'slider', min: 10, max: 300, step: 10, default: 100 },
    { key: 'varMinIter', label: '变分最小化迭代', type: 'number', default: 30 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'VarBC': [
    { key: 'correctVar', label: '校正变量', type: 'select', options: [
      { label: '温度', value: 'temperature' },
      { label: '湿度', value: 'humidity' },
      { label: '风', value: 'wind' },
      { label: '气压', value: 'pressure' },
      { label: '全部', value: 'all' },
    ], default: 'all' },
    { key: 'timeWindow', label: '时间窗口 (h)', type: 'slider', min: 1, max: 72, step: 1, default: 24 },
    { key: 'slidingWindowSize', label: '滑动窗口大小', type: 'slider', min: 5, max: 60, step: 5, default: 30 },
    { key: 'regressionModel', label: '回归模型', type: 'select', options: [
      { label: '线性', value: 'linear' },
      { label: '多项式', value: 'polynomial' },
      { label: '样条', value: 'spline' },
    ], default: 'linear' },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  '3D-RTPP': [
    { key: 'relaxCoeff', label: '松弛系数 α', type: 'slider', min: 0.01, max: 1.0, step: 0.01, default: 0.1 },
    { key: 'tendencyTimescale', label: '倾向逼近时间尺度 (h)', type: 'slider', min: 1, max: 24, step: 1, default: 6 },
    { key: 'noiseInjection', label: '噪声注入强度', type: 'slider', min: 0, max: 1, step: 0.01, default: 0.15 },
    { key: 'blendWeight', label: '混合权重', type: 'slider', min: 0, max: 1, step: 0.05, default: 0.5 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],

  // ---- 2. 路径规划系列 ----
  'MPC-Path': [
    { key: 'predictHorizon', label: '预测时域 (step)', type: 'slider', min: 5, max: 50, step: 1, default: 20 },
    { key: 'controlStep', label: '控制步长 (m)', type: 'number', default: 5 },
    { key: 'maxSpeed', label: '最大速度 (m/s)', type: 'slider', min: 1, max: 30, step: 1, default: 15 },
    { key: 'obstacleSafeDist', label: '障碍物安全距离 (m)', type: 'slider', min: 1, max: 20, step: 0.5, default: 5 },
    { key: 'weightPath', label: '优化权重-路径', type: 'slider', min: 0, max: 1, step: 0.05, default: 0.6 },
    { key: 'weightEnergy', label: '优化权重-能耗', type: 'slider', min: 0, max: 1, step: 0.05, default: 0.4 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'A-Star': [
    { key: 'gridResolution', label: '网格分辨率 (m)', type: 'select', options: [
      { label: '1', value: 1 },
      { label: '5', value: 5 },
      { label: '10', value: 10 },
      { label: '20', value: 20 },
      { label: '50', value: 50 },
    ], default: 10 },
    { key: 'heuristic', label: '启发式函数', type: 'select', options: [
      { label: '曼哈顿', value: 'manhattan' },
      { label: '欧几里得', value: 'euclidean' },
      { label: '切比雪夫', value: 'chebyshev' },
      { label: '对角', value: 'diagonal' },
    ], default: 'euclidean' },
    { key: 'maxSearchNodes', label: '最大搜索节点数', type: 'number', default: 100000 },
    { key: 'diagonalMove', label: '对角线移动', type: 'select', options: [
      { label: '允许', value: 'allow' },
      { label: '禁止', value: 'forbid' },
    ], default: 'allow' },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'RRT-Connect': [
    { key: 'maxIterations', label: '最大迭代次数', type: 'number', default: 5000 },
    { key: 'stepSize', label: '步长 (m)', type: 'slider', min: 1, max: 20, step: 0.5, default: 5 },
    { key: 'goalBias', label: '目标偏差 (m)', type: 'slider', min: 0.5, max: 10, step: 0.5, default: 2 },
    { key: 'nodeLimit', label: '树节点上限', type: 'number', default: 10000 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'Dijkstra-3D': [
    { key: 'gridResolution', label: '网格分辨率 (m)', type: 'select', options: [
      { label: '1', value: 1 },
      { label: '5', value: 5 },
      { label: '10', value: 10 },
      { label: '20', value: 20 },
      { label: '50', value: 50 },
    ], default: 10 },
    { key: 'altitudeWeight', label: '高度代价权重', type: 'slider', min: 0.5, max: 3.0, step: 0.1, default: 1.5 },
    { key: 'noFlyPenalty', label: '禁飞区惩罚系数', type: 'slider', min: 1, max: 100, step: 1, default: 50 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'GA-Route': [
    { key: 'populationSize', label: '种群大小', type: 'slider', min: 20, max: 500, step: 10, default: 100 },
    { key: 'maxGenerations', label: '最大代数', type: 'number', default: 200 },
    { key: 'crossoverRate', label: '交叉概率', type: 'slider', min: 0.5, max: 1.0, step: 0.05, default: 0.8 },
    { key: 'mutationRate', label: '变异概率', type: 'slider', min: 0.01, max: 0.5, step: 0.01, default: 0.1 },
    { key: 'tournamentSize', label: '锦标赛大小', type: 'slider', min: 2, max: 10, step: 1, default: 5 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'PSO-Opt': [
    { key: 'particleCount', label: '粒子数量', type: 'slider', min: 10, max: 200, step: 5, default: 50 },
    { key: 'maxIterations', label: '最大迭代次数', type: 'number', default: 100 },
    { key: 'inertiaWeight', label: '惯性权重', type: 'slider', min: 0.1, max: 1.0, step: 0.05, default: 0.7 },
    { key: 'learningFactorC1', label: '学习因子 c1', type: 'slider', min: 0.5, max: 3.0, step: 0.1, default: 1.5 },
    { key: 'learningFactorC2', label: '学习因子 c2', type: 'slider', min: 0.5, max: 3.0, step: 0.1, default: 1.5 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],

  // ---- 3. 风险评估系列 ----
  'RiskAssess': [
    { key: 'timeHorizon', label: '预测时域 (h)', type: 'slider', min: 1, max: 72, step: 1, default: 24 },
    { key: 'gridResolution', label: '网格分辨率 (km)', type: 'select', options: [
      { label: '1', value: 1 },
      { label: '3', value: 3 },
      { label: '9', value: 9 },
    ], default: 3 },
    { key: 'confidenceLevel', label: '置信水平', type: 'slider', min: 0.5, max: 0.99, step: 0.01, default: 0.95 },
    { key: 'riskThreshold', label: '风险阈值', type: 'slider', min: 0, max: 1, step: 0.05, default: 0.5 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'AirsafeEval': [
    { key: 'evalRange', label: '评估范围 (km)', type: 'number', default: 500 },
    { key: 'altitudeLayer', label: '高度层 (m)', type: 'select', options: [
      { label: '低空0-1000', value: 'low' },
      { label: '中空1000-5000', value: 'mid' },
      { label: '高空5000+', value: 'high' },
    ], default: 'low' },
    { key: 'meteoElements', label: '气象要素', type: 'select', options: [
      { label: '风', value: 'wind' },
      { label: '温度', value: 'temperature' },
      { label: '湿度', value: 'humidity' },
      { label: '能见度', value: 'visibility' },
      { label: '全部', value: 'all' },
    ], default: 'all' },
    { key: 'safetyStandard', label: '安全等级', type: 'select', options: [
      { label: 'ICAO标准', value: 'icao' },
      { label: '增强标准', value: 'enhanced' },
    ], default: 'icao' },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'TurbulenceDetect': [
    { key: 'detectMethod', label: '湍流检测方法', type: 'select', options: [
      { label: 'TKE', value: 'tke' },
      { label: 'EDR', value: 'edr' },
      { label: '方差', value: 'variance' },
      { label: '综合', value: 'combined' },
    ], default: 'combined' },
    { key: 'timeWindow', label: '时间窗口 (min)', type: 'slider', min: 1, max: 30, step: 1, default: 5 },
    { key: 'spatialResolution', label: '空间分辨率 (km)', type: 'slider', min: 1, max: 50, step: 1, default: 10 },
    { key: 'detectThreshold', label: '检测阈值 (m²/s²)', type: 'slider', min: 0.1, max: 5.0, step: 0.1, default: 0.5 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'IcingPredict': [
    { key: 'iceType', label: '冰型', type: 'select', options: [
      { label: '明冰', value: 'glaze' },
      { label: '混合冰', value: 'mixed' },
      { label: '霜冰', value: 'rime' },
    ], default: 'mixed' },
    { key: 'lwcThreshold', label: '液态水含量阈值 (g/m³)', type: 'slider', min: 0.01, max: 1.0, step: 0.01, default: 0.2 },
    { key: 'tempRange', label: '温度范围 (°C)', type: 'slider', min: -40, max: 0, step: 1, default: -20 },
    { key: 'verticalResolution', label: '垂直分辨率 (m)', type: 'slider', min: 50, max: 500, step: 50, default: 200 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'WindShear': [
    { key: 'detectMethod', label: '检测方法', type: 'select', options: [
      { label: '多普勒', value: 'doppler' },
      { label: '双多普勒', value: 'dual_doppler' },
      { label: '风场梯度', value: 'wind_gradient' },
    ], default: 'doppler' },
    { key: 'altitudeRange', label: '高度范围 (m)', type: 'slider', min: 0, max: 3000, step: 100, default: 1000 },
    { key: 'horizontalResolution', label: '水平分辨率 (km)', type: 'slider', min: 0.5, max: 10, step: 0.5, default: 2 },
    { key: 'fFactorThreshold', label: 'F-factor 阈值', type: 'slider', min: 0, max: 0.2, step: 0.005, default: 0.1 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'ConvectiveRisk': [
    { key: 'convectiveType', label: '对流类型', type: 'select', options: [
      { label: '普通', value: 'ordinary' },
      { label: '强', value: 'severe' },
      { label: '超级单体', value: 'supercell' },
    ], default: 'ordinary' },
    { key: 'capeThreshold', label: 'CAPE 阈值 (J/kg)', type: 'slider', min: 500, max: 5000, step: 100, default: 1500 },
    { key: 'cinThreshold', label: 'CIN 阈值 (J/kg)', type: 'slider', min: -500, max: 0, step: 10, default: -100 },
    { key: 'shearParam', label: '风切变参数', type: 'slider', min: 0, max: 50, step: 1, default: 25 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],

  // ---- 4. 观测决策系列 ----
  'ActiveObs': [
    { key: 'obsPointCount', label: '观测点数量', type: 'slider', min: 1, max: 100, step: 1, default: 20 },
    { key: 'coverageArea', label: '覆盖面积 (km²)', type: 'number', default: 1000 },
    { key: 'sensorType', label: '传感器类型', type: 'select', options: [
      { label: '温度', value: 'temperature' },
      { label: '湿度', value: 'humidity' },
      { label: '风', value: 'wind' },
      { label: '综合', value: 'combined' },
    ], default: 'combined' },
    { key: 'optimizeTarget', label: '优化目标', type: 'select', options: [
      { label: '信息增益', value: 'info_gain' },
      { label: '覆盖最大化', value: 'max_coverage' },
      { label: '误差最小化', value: 'min_error' },
    ], default: 'info_gain' },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'SensorPlace': [
    { key: 'sensorCount', label: '传感器数量', type: 'slider', min: 1, max: 50, step: 1, default: 10 },
    { key: 'layoutStrategy', label: '布局策略', type: 'select', options: [
      { label: '网格', value: 'grid' },
      { label: '随机', value: 'random' },
      { label: '优化', value: 'optimized' },
      { label: '混合', value: 'hybrid' },
    ], default: 'optimized' },
    { key: 'minSpacing', label: '最小间距 (km)', type: 'slider', min: 1, max: 50, step: 1, default: 10 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'AdaptiveSample': [
    { key: 'sampleDensity', label: '采样密度', type: 'select', options: [
      { label: '低', value: 'low' },
      { label: '中', value: 'medium' },
      { label: '高', value: 'high' },
      { label: '自适应', value: 'adaptive' },
    ], default: 'adaptive' },
    { key: 'initialSamples', label: '初始样本数', type: 'number', default: 50 },
    { key: 'maxSamples', label: '最大样本数', type: 'number', default: 500 },
    { key: 'convergenceCriteria', label: '收敛标准', type: 'slider', min: 0.001, max: 0.1, step: 0.001, default: 0.01 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'TargetTrack': [
    { key: 'targetType', label: '目标类型', type: 'select', options: [
      { label: '单目标', value: 'single' },
      { label: '多目标', value: 'multi' },
      { label: '群目标', value: 'swarm' },
    ], default: 'single' },
    { key: 'trackAlgo', label: '跟踪算法', type: 'select', options: [
      { label: '卡尔曼', value: 'kalman' },
      { label: '粒子', value: 'particle' },
      { label: 'JPDA', value: 'jpda' },
    ], default: 'kalman' },
    { key: 'predictSteps', label: '预测步数', type: 'slider', min: 1, max: 20, step: 1, default: 5 },
    { key: 'updateFreq', label: '更新频率 (Hz)', type: 'slider', min: 1, max: 50, step: 1, default: 10 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'UTM-Collision': [
    { key: 'monitorAirspace', label: '监控空域大小 (km²)', type: 'number', default: 10000 },
    { key: 'uavCount', label: 'UAV 数量', type: 'slider', min: 1, max: 200, step: 1, default: 20 },
    { key: 'detectRange', label: '冲突检测范围 (m)', type: 'slider', min: 100, max: 5000, step: 100, default: 500 },
    { key: 'safeSeparation', label: '安全间隔 (m)', type: 'slider', min: 50, max: 500, step: 10, default: 150 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],

  // ---- 5. 模型引擎系列 ----
  'WRF-3km': [
    { key: 'simRegion', label: '模拟区域', type: 'select', options: [
      { label: '华南', value: 'south_china' },
      { label: '华东', value: 'east_china' },
      { label: '华北', value: 'north_china' },
      { label: '西南', value: 'southwest' },
    ], default: 'south_china' },
    { key: 'forecastHours', label: '预报时长 (h)', type: 'slider', min: 1, max: 72, step: 1, default: 24 },
    { key: 'physicsScheme', label: '物理方案', type: 'select', options: [
      { label: 'YSU', value: 'ysu' },
      { label: 'MYJ', value: 'myj' },
      { label: 'MYNN', value: 'mynn' },
      { label: 'SH', value: 'sh' },
    ], default: 'ysu' },
    { key: 'microphysicsScheme', label: '微物理方案', type: 'select', options: [
      { label: 'Lin', value: 'lin' },
      { label: 'WSM6', value: 'wsm6' },
      { label: 'Thompson', value: 'thompson' },
    ], default: 'thompson' },
    { key: 'outputInterval', label: '输出间隔 (min)', type: 'select', options: [
      { label: '5', value: 5 },
      { label: '10', value: 10 },
      { label: '15', value: 15 },
      { label: '30', value: 30 },
      { label: '60', value: 60 },
    ], default: 15 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'WRF-1km': [
    { key: 'simRegion', label: '模拟区域', type: 'select', options: [
      { label: '城市', value: 'city' },
      { label: '机场', value: 'airport' },
      { label: '沿海', value: 'coastal' },
    ], default: 'city' },
    { key: 'forecastHours', label: '预报时长 (h)', type: 'slider', min: 1, max: 24, step: 1, default: 12 },
    { key: 'physicsScheme', label: '物理方案', type: 'select', options: [
      { label: 'YSU', value: 'ysu' },
      { label: 'MYJ', value: 'myj' },
      { label: 'MYNN', value: 'mynn' },
      { label: 'SH', value: 'sh' },
    ], default: 'mynn' },
    { key: 'urbanCanopy', label: '城市冠层方案', type: 'select', options: [
      { label: '关闭', value: 'off' },
      { label: 'UCM', value: 'ucm' },
      { label: 'BEP', value: 'bep' },
    ], default: 'ucm' },
    { key: 'outputInterval', label: '输出间隔 (min)', type: 'select', options: [
      { label: '5', value: 5 },
      { label: '10', value: 10 },
      { label: '15', value: 15 },
    ], default: 10 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'WRF-9km': [
    { key: 'simRegion', label: '模拟区域', type: 'select', options: [
      { label: '中国', value: 'china' },
      { label: '东亚', value: 'east_asia' },
      { label: '全球', value: 'global' },
    ], default: 'china' },
    { key: 'forecastHours', label: '预报时长 (h)', type: 'slider', min: 6, max: 120, step: 6, default: 72 },
    { key: 'physicsScheme', label: '物理方案', type: 'select', options: [
      { label: 'YSU', value: 'ysu' },
      { label: 'MYJ', value: 'myj' },
      { label: 'MYNN', value: 'mynn' },
      { label: 'SH', value: 'sh' },
    ], default: 'ysu' },
    { key: 'initialField', label: '初始场', type: 'select', options: [
      { label: 'GFS', value: 'gfs' },
      { label: 'ERA5', value: 'era5' },
      { label: 'FNL', value: 'fnl' },
    ], default: 'gfs' },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'ML-Surrogate': [
    { key: 'modelArch', label: '模型架构', type: 'select', options: [
      { label: 'CNN', value: 'cnn' },
      { label: 'LSTM', value: 'lstm' },
      { label: 'Transformer', value: 'transformer' },
      { label: 'MLP', value: 'mlp' },
    ], default: 'lstm' },
    { key: 'inputVars', label: '输入变量数', type: 'slider', min: 5, max: 50, step: 1, default: 15 },
    { key: 'hiddenDim', label: '隐藏层维度', type: 'slider', min: 32, max: 512, step: 32, default: 128 },
    { key: 'trainEpochs', label: '训练轮数', type: 'number', default: 100 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'NWP-PostProcess': [
    { key: 'postMethod', label: '后处理方法', type: 'select', options: [
      { label: 'MOS', value: 'mos' },
      { label: 'EM', value: 'em' },
      { label: 'PP', value: 'pp' },
      { label: '偏差校正', value: 'bias_correction' },
    ], default: 'mos' },
    { key: 'trainSamples', label: '训练样本数', type: 'number', default: 1000 },
    { key: 'forecastVar', label: '预报变量', type: 'select', options: [
      { label: '温度', value: 'temperature' },
      { label: '降水', value: 'precipitation' },
      { label: '风', value: 'wind' },
      { label: '全部', value: 'all' },
    ], default: 'all' },
    { key: 'verifyMetric', label: '验证指标', type: 'select', options: [
      { label: 'RMSE', value: 'rmse' },
      { label: 'MAE', value: 'mae' },
      { label: 'ACC', value: 'acc' },
      { label: '全部', value: 'all' },
    ], default: 'all' },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],

  // ---- 6. 边缘计算系列 ----
  'EdgeInfer': [
    { key: 'modelSize', label: '模型大小', type: 'select', options: [
      { label: '小(<10MB)', value: 'small' },
      { label: '中(10-100MB)', value: 'medium' },
      { label: '大(>100MB)', value: 'large' },
    ], default: 'medium' },
    { key: 'edgeDevice', label: '边缘设备', type: 'select', options: [
      { label: 'Jetson Nano', value: 'jetson_nano' },
      { label: 'Jetson Orin', value: 'jetson_orin' },
      { label: '树莓派', value: 'raspberry_pi' },
      { label: '手机', value: 'phone' },
    ], default: 'jetson_nano' },
    { key: 'batchSize', label: '批处理大小', type: 'slider', min: 1, max: 32, step: 1, default: 4 },
    { key: 'quantPrecision', label: '量化精度', type: 'select', options: [
      { label: 'FP32', value: 'fp32' },
      { label: 'FP16', value: 'fp16' },
      { label: 'INT8', value: 'int8' },
    ], default: 'fp16' },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'FederatedLearn': [
    { key: 'nodeCount', label: '参与节点数', type: 'slider', min: 2, max: 50, step: 1, default: 10 },
    { key: 'commRounds', label: '通信轮数', type: 'number', default: 100 },
    { key: 'aggStrategy', label: '聚合策略', type: 'select', options: [
      { label: 'FedAvg', value: 'fedavg' },
      { label: 'FedProx', value: 'fedprox' },
      { label: 'Scaffold', value: 'scaffold' },
    ], default: 'fedavg' },
    { key: 'localEpochs', label: '本地训练轮数', type: 'slider', min: 1, max: 20, step: 1, default: 5 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'SplitCompute': [
    { key: 'splitPoint', label: '分割点', type: 'select', options: [
      { label: '输入层', value: 'input' },
      { label: '中间层', value: 'middle' },
      { label: '输出层', value: 'output' },
      { label: '自适应', value: 'adaptive' },
    ], default: 'middle' },
    { key: 'cloudModelSize', label: '云端模型大小', type: 'select', options: [
      { label: '大', value: 'large' },
      { label: '中', value: 'medium' },
      { label: '小', value: 'small' },
    ], default: 'large' },
    { key: 'edgeModelSize', label: '边缘模型大小', type: 'select', options: [
      { label: '大', value: 'large' },
      { label: '中', value: 'medium' },
      { label: '小', value: 'small' },
    ], default: 'small' },
    { key: 'bandwidthLimit', label: '带宽限制 (Mbps)', type: 'slider', min: 1, max: 100, step: 1, default: 10 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
  'OnDeviceAI': [
    { key: 'deviceType', label: '设备类型', type: 'select', options: [
      { label: '手机', value: 'phone' },
      { label: '平板', value: 'tablet' },
      { label: '嵌入式', value: 'embedded' },
      { label: '无人机', value: 'uav' },
    ], default: 'uav' },
    { key: 'inferFramework', label: '推理框架', type: 'select', options: [
      { label: 'ONNX', value: 'onnx' },
      { label: 'TFLite', value: 'tflite' },
      { label: 'CoreML', value: 'coreml' },
      { label: 'NCNN', value: 'ncnn' },
    ], default: 'onnx' },
    { key: 'inputResolution', label: '输入分辨率', type: 'select', options: [
      { label: '224x224', value: '224x224' },
      { label: '416x416', value: '416x416' },
      { label: '640x640', value: '640x640' },
    ], default: '416x416' },
    { key: 'threadCount', label: '线程数', type: 'slider', min: 1, max: 8, step: 1, default: 4 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ],
}

// ALGO_VARIANT_EXTRA_MAP: key 为完整算法名称（含变体后缀），value 为追加参数数组
const ALGO_VARIANT_EXTRA_MAP: Record<string, ParamField[]> = {
  // ---- 数据同化变体 ----
  '3D-VAR-数据同化 (高性能版)': [
    { key: 'parallelThreads', label: '并行计算线程数', type: 'slider', min: 1, max: 32, step: 1, default: 8 },
    { key: 'gpuAccel', label: 'GPU 加速', type: 'select', options: [
      { label: '关闭', value: 'off' },
      { label: 'CUDA', value: 'cuda' },
      { label: 'OpenCL', value: 'opencl' },
    ], default: 'cuda' },
  ],
  '4D-VAR-数据同化 (高精度版)': [
    { key: 'flowDepBgError', label: '流依赖背景误差', type: 'select', options: [
      { label: '关闭', value: 'off' },
      { label: '3DVarFGAT', value: '3dvar_fgat' },
      { label: 'EnVar', value: 'envar' },
    ], default: '3dvar_fgat' },
    { key: 'localizationRadius', label: '局地化半径 (grid)', type: 'slider', min: 5, max: 50, step: 1, default: 20 },
  ],
  '5D-VAR-数据同化 (快速版)': [
    { key: 'fastOuterLoop', label: '快速外循环', type: 'select', options: [
      { label: '关闭', value: 'off' },
      { label: '开启', value: 'on' },
    ], default: 'on' },
    { key: 'precondMethod', label: '预条件方法', type: 'select', options: [
      { label: '无', value: 'none' },
      { label: '谱滤波', value: 'spectral_filter' },
      { label: '物理滤波', value: 'physics_filter' },
    ], default: 'spectral_filter' },
  ],
  'EnKF-数据同化 (大集合版)': [
    { key: 'ensembleSize', label: '集合成员数', type: 'slider', min: 10, max: 200, step: 5, default: 200 },
  ],
  'Hybrid-EnVar-数据同化 (自适应版)': [
    { key: 'weightAdaptive', label: '权重自适应', type: 'select', options: [
      { label: '关闭', value: 'off' },
      { label: '方差缩放', value: 'variance_scaling' },
      { label: '误差估计', value: 'error_estimation' },
    ], default: 'variance_scaling' },
    { key: 'adaptiveWindow', label: '自适应窗口 (h)', type: 'slider', min: 1, max: 12, step: 1, default: 6 },
  ],
  'VarBC-数据同化 (多变量版)': [
    { key: 'crossVarCorrection', label: '交叉变量校正', type: 'select', options: [
      { label: '关闭', value: 'off' },
      { label: '开启', value: 'on' },
    ], default: 'on' },
    { key: 'regularization', label: '正则化强度', type: 'slider', min: 0, max: 1, step: 0.05, default: 0.1 },
  ],
  '3D-RTPP-数据同化 (增强版)': [
    { key: 'multiScaleRelax', label: '多尺度松弛', type: 'select', options: [
      { label: '单尺度', value: 'single' },
      { label: '双尺度', value: 'dual' },
      { label: '三尺度', value: 'triple' },
    ], default: 'dual' },
    { key: 'flowDepRelax', label: '流依赖松弛', type: 'select', options: [
      { label: '关闭', value: 'off' },
      { label: '开启', value: 'on' },
    ], default: 'on' },
  ],

  // ---- 路径规划变体 ----
  'MPC-Path-路径规划 (实时版)': [
    { key: 'solver', label: '求解器', type: 'select', options: [
      { label: 'QP', value: 'qp' },
      { label: 'OSQP', value: 'osqp' },
      { label: '快速QP', value: 'fast_qp' },
    ], default: 'fast_qp' },
    { key: 'maxSolveTime', label: '最大求解时间 (ms)', type: 'slider', min: 5, max: 100, step: 5, default: 20 },
  ],
  'MPC-Path-路径规划 (多目标版)': [
    { key: 'multiObjStrategy', label: '多目标策略', type: 'select', options: [
      { label: '加权', value: 'weighted' },
      { label: '帕累托', value: 'pareto' },
      { label: '分层', value: 'hierarchical' },
    ], default: 'weighted' },
    { key: 'paretoPoints', label: '帕累托前沿点数', type: 'slider', min: 10, max: 100, step: 5, default: 30 },
  ],
  'A-Star-路径规划 (3D版)': [
    { key: 'altitudeLayers', label: '高度层数', type: 'slider', min: 2, max: 20, step: 1, default: 5 },
    { key: 'altChangeCostWeight', label: '高度变化代价权重', type: 'slider', min: 0.5, max: 3.0, step: 0.1, default: 1.5 },
    { key: 'minSafeAltitude', label: '最小安全高度 (m)', type: 'number', default: 50 },
  ],
  'A-Star-路径规划 (动态避障版)': [
    { key: 'replanInterval', label: '动态重规划间隔 (s)', type: 'slider', min: 0.1, max: 5.0, step: 0.1, default: 1.0 },
    { key: 'obstaclePredictModel', label: '障碍物预测模型', type: 'select', options: [
      { label: '匀速', value: 'constant_velocity' },
      { label: '匀加速', value: 'constant_acceleration' },
      { label: '卡尔曼', value: 'kalman' },
    ], default: 'kalman' },
    { key: 'safetyMargin', label: '安全裕度系数', type: 'slider', min: 1.0, max: 3.0, step: 0.1, default: 1.5 },
  ],
  'RRT-Connect-路径规划 (高速版)': [
    { key: 'parallelTrees', label: '并行树数量', type: 'slider', min: 2, max: 8, step: 1, default: 4 },
    { key: 'sampleStrategy', label: '采样策略', type: 'select', options: [
      { label: '均匀', value: 'uniform' },
      { label: '高斯', value: 'gaussian' },
      { label: '桥接', value: 'bridge' },
    ], default: 'bridge' },
  ],
  'RRT-Connect-路径规划 (窄通道版)': [
    { key: 'narrowThreshold', label: '窄通道检测阈值 (m)', type: 'slider', min: 1, max: 10, step: 0.5, default: 3 },
    { key: 'channelGuidedSampling', label: '通道导向采样', type: 'select', options: [
      { label: '关闭', value: 'off' },
      { label: '开启', value: 'on' },
    ], default: 'on' },
    { key: 'channelRefineIter', label: '通道细化迭代', type: 'number', default: 20 },
  ],
  'Dijkstra-3D-路径规划 (加权版)': [
    { key: 'multiWeightFusion', label: '多权重融合', type: 'select', options: [
      { label: '线性加权', value: 'linear' },
      { label: '指数加权', value: 'exponential' },
      { label: '自定义', value: 'custom' },
    ], default: 'linear' },
    { key: 'customWeights', label: '自定义权重 (JSON)', type: 'json', default: '{"distance": 0.4, "altitude": 0.3, "risk": 0.3}' },
  ],
  'GA-Route-路径规划 (多约束版)': [
    { key: 'constraintType', label: '约束类型', type: 'select', options: [
      { label: '油耗', value: 'fuel' },
      { label: '高度', value: 'altitude' },
      { label: '时间', value: 'time' },
      { label: '综合', value: 'combined' },
    ], default: 'combined' },
    { key: 'violationPenalty', label: '约束违反惩罚', type: 'slider', min: 10, max: 1000, step: 10, default: 100 },
    { key: 'feasibleFirst', label: '可行解优先', type: 'select', options: [
      { label: '关闭', value: 'off' },
      { label: '开启', value: 'on' },
    ], default: 'on' },
  ],
  'PSO-Opt-路径规划 (全局优化版)': [
    { key: 'multiSwarm', label: '多群协作', type: 'select', options: [
      { label: '关闭', value: 'off' },
      { label: '主从', value: 'master_slave' },
      { label: '环形', value: 'ring' },
    ], default: 'master_slave' },
    { key: 'restartStrategy', label: '重启策略', type: 'select', options: [
      { label: '无', value: 'none' },
      { label: '随机', value: 'random' },
      { label: '自适应', value: 'adaptive' },
    ], default: 'adaptive' },
  ],

  // ---- 风险评估变体 ----
  'RiskAssess-风险评估 (综合版)': [
    { key: 'riskType', label: '风险类型', type: 'select', options: [
      { label: '湍流', value: 'turbulence' },
      { label: '积冰', value: 'icing' },
      { label: '风切变', value: 'wind_shear' },
      { label: '综合', value: 'combined' },
    ], default: 'combined' },
    { key: 'timeAggregation', label: '时间聚合', type: 'select', options: [
      { label: '瞬时', value: 'instant' },
      { label: '1h', value: '1h' },
      { label: '3h', value: '3h' },
      { label: '6h', value: '6h' },
    ], default: '1h' },
  ],
  'RiskAssess-风险评估 (实时版)': [
    { key: 'updateFreq', label: '更新频率 (s)', type: 'slider', min: 10, max: 300, step: 10, default: 60 },
    { key: 'historyWindow', label: '历史窗口 (min)', type: 'slider', min: 5, max: 60, step: 5, default: 15 },
  ],
  'AirsafeEval-风险评估 (适航版)': [
    { key: 'airworthiness', label: '适航规章', type: 'select', options: [
      { label: 'CCAR-91', value: 'ccar_91' },
      { label: 'CCAR-135', value: 'ccar_135' },
      { label: 'FAA Part 107', value: 'faa_107' },
    ], default: 'ccar_91' },
    { key: 'continuousAirworthiness', label: '连续适航评估', type: 'select', options: [
      { label: '关闭', value: 'off' },
      { label: '开启', value: 'on' },
    ], default: 'on' },
  ],
  'TurbulenceDetect-风险评估 (预测版)': [
    { key: 'leadTime', label: '预测提前量 (min)', type: 'slider', min: 5, max: 60, step: 5, default: 15 },
    { key: 'predictModel', label: '预测模型', type: 'select', options: [
      { label: 'persistence', value: 'persistence' },
      { label: '统计', value: 'statistical' },
      { label: 'ML', value: 'ml' },
    ], default: 'ml' },
  ],
  'IcingPredict-风险评估 (精确版)': [
    { key: 'cloudMicrophysics', label: '云微物理方案', type: 'select', options: [
      { label: '简化', value: 'simplified' },
      { label: '详细', value: 'detailed' },
      { label: '双参数', value: 'two_moment' },
    ], default: 'detailed' },
    { key: 'timeStep', label: '积分时间步 (s)', type: 'slider', min: 10, max: 300, step: 10, default: 60 },
  ],

  // ---- 观测决策变体 ----
  'ActiveObs-观测决策 (自适应版)': [
    { key: 'adaptiveStrategy', label: '自适应策略', type: 'select', options: [
      { label: '贪心', value: 'greedy' },
      { label: '模拟退火', value: 'simulated_annealing' },
      { label: '遗传算法', value: 'genetic' },
    ], default: 'simulated_annealing' },
    { key: 'replanInterval', label: '重规划间隔 (min)', type: 'slider', min: 5, max: 60, step: 5, default: 15 },
  ],
  'ActiveObs-观测决策 (多目标版)': [
    { key: 'weightInfo', label: '多目标权重-信息', type: 'slider', min: 0, max: 1, step: 0.05, default: 0.5 },
    { key: 'weightCoverage', label: '多目标权重-覆盖', type: 'slider', min: 0, max: 1, step: 0.05, default: 0.3 },
    { key: 'weightCost', label: '多目标权重-成本', type: 'slider', min: 0, max: 1, step: 0.05, default: 0.2 },
  ],
  'SensorPlace-观测决策 (覆盖优化版)': [
    { key: 'coverageTarget', label: '覆盖率目标 (%)', type: 'slider', min: 70, max: 99, step: 1, default: 90 },
    { key: 'terrainWeight', label: '地形权重', type: 'slider', min: 0, max: 1, step: 0.05, default: 0.3 },
  ],
  'AdaptiveSample-观测决策 (在线版)': [
    { key: 'onlineUpdateFreq', label: '在线更新频率 (s)', type: 'slider', min: 1, max: 60, step: 1, default: 10 },
    { key: 'incrementalLearning', label: '增量学习', type: 'select', options: [
      { label: '关闭', value: 'off' },
      { label: '开启', value: 'on' },
    ], default: 'on' },
  ],

  // ---- 模型引擎变体 ----
  'WRF-3km-模型引擎 (快速积分版)': [
    { key: 'timeStep', label: '时间步长 (s)', type: 'slider', min: 5, max: 60, step: 5, default: 15 },
    { key: 'precision', label: '积分精度', type: 'select', options: [
      { label: '单精度', value: 'single' },
      { label: '双精度', value: 'double' },
    ], default: 'single' },
  ],
  'WRF-1km-模型引擎 (城市版)': [
    { key: 'buildingResolution', label: '建筑数据分辨率 (m)', type: 'select', options: [
      { label: '1', value: 1 },
      { label: '3', value: 3 },
      { label: '10', value: 10 },
    ], default: 3 },
    { key: 'anthropogenicHeat', label: '人为热排放', type: 'select', options: [
      { label: '关闭', value: 'off' },
      { label: '简化', value: 'simplified' },
      { label: '详细', value: 'detailed' },
    ], default: 'simplified' },
  ],
  'ML-Surrogate-模型引擎 (深度学习版)': [
    { key: 'attentionMech', label: '注意力机制', type: 'select', options: [
      { label: '关闭', value: 'off' },
      { label: '自注意力', value: 'self_attention' },
      { label: '交叉注意力', value: 'cross_attention' },
    ], default: 'self_attention' },
    { key: 'pretrain', label: '预训练', type: 'select', options: [
      { label: '无', value: 'none' },
      { label: '迁移学习', value: 'transfer_learning' },
      { label: '自监督', value: 'self_supervised' },
    ], default: 'transfer_learning' },
  ],

  // ---- 边缘计算变体 ----
  'EdgeInfer-边缘计算 (轻量版)': [
    { key: 'modelCompression', label: '模型压缩', type: 'select', options: [
      { label: '无', value: 'none' },
      { label: '剪枝', value: 'pruning' },
      { label: '蒸馏', value: 'distillation' },
      { label: '量化', value: 'quantization' },
    ], default: 'quantization' },
    { key: 'compressionRatio', label: '压缩率 (%)', type: 'slider', min: 10, max: 90, step: 5, default: 50 },
  ],
  'SplitCompute-边缘计算 (低延迟版)': [
    { key: 'maxLatency', label: '最大延迟 (ms)', type: 'slider', min: 10, max: 500, step: 10, default: 50 },
    { key: 'cacheStrategy', label: '缓存策略', type: 'select', options: [
      { label: '无', value: 'none' },
      { label: 'LRU', value: 'lru' },
      { label: '预测', value: 'predictive' },
    ], default: 'predictive' },
  ],
}

// 按分类生成兜底通用参数
function buildCategoryDefaultParams(category: string): ParamField[] {
  if (category === 'assimilation') {
    return [
      { key: 'ensembleSize', label: '集合数量', type: 'slider', min: 10, max: 200, step: 5, default: 50 },
      { key: 'inflationFactor', label: '膨胀因子', type: 'slider', min: 1.0, max: 2.0, step: 0.05, default: 1.1 },
      { key: 'localizationRadius', label: '局地化半径 (km)', type: 'number', min: 1, max: 500, default: 150 },
      { key: 'assimilationMethod', label: '同化方法', type: 'select', options: [
        { label: 'EnKF', value: 'enkf' },
        { label: '3DVAR', value: '3dvar' },
        { label: 'Hybrid', value: 'hybrid' },
      ], default: 'enkf' },
      { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
    ]
  } else if (category === 'planning') {
    return [
      { key: 'maxIterations', label: '最大迭代次数', type: 'number', min: 100, max: 10000, default: 1000 },
      { key: 'populationSize', label: '种群大小', type: 'slider', min: 10, max: 200, step: 5, default: 50 },
      { key: 'mutationRate', label: '变异率', type: 'slider', min: 0.01, max: 1.0, step: 0.01, default: 0.1 },
      { key: 'objective', label: '优化目标', type: 'select', options: [
        { label: '最短路径', value: 'shortest' },
        { label: '最小能耗', value: 'energy' },
        { label: '多目标', value: 'multi' },
      ], default: 'shortest' },
      { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
    ]
  } else if (category === 'risk') {
    return [
      { key: 'timeHorizon', label: '预测时域 (h)', type: 'number', min: 1, max: 72, default: 24 },
      { key: 'gridResolution', label: '网格分辨率 (km)', type: 'select', options: [
        { label: '1 km', value: 1 },
        { label: '3 km', value: 3 },
        { label: '9 km', value: 9 },
      ], default: 3 },
      { key: 'confidenceLevel', label: '置信水平', type: 'slider', min: 0.5, max: 0.99, step: 0.01, default: 0.95 },
      { key: 'riskThreshold', label: '风险阈值', type: 'slider', min: 0, max: 1, step: 0.05, default: 0.5 },
      { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
    ]
  } else if (category === 'observation') {
    return [
      { key: 'observationCount', label: '观测点数量', type: 'slider', min: 1, max: 100, step: 1, default: 20 },
      { key: 'coverageArea', label: '覆盖面积 (km2)', type: 'number', min: 1, max: 10000, default: 1000 },
      { key: 'sensorType', label: '传感器类型', type: 'select', options: [
        { label: '温度传感器', value: 'temperature' },
        { label: '湿度传感器', value: 'humidity' },
        { label: '风速传感器', value: 'wind' },
        { label: '综合传感器', value: 'combined' },
      ], default: 'combined' },
      { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
    ]
  } else if (category === 'model_engine') {
    return [
      { key: 'modelResolution', label: '模型分辨率', type: 'select', options: [
        { label: '1 km', value: 1 },
        { label: '3 km', value: 3 },
        { label: '9 km', value: 9 },
        { label: '27 km', value: 27 },
      ], default: 3 },
      { key: 'timeStep', label: '时间步长 (s)', type: 'number', min: 1, max: 3600, default: 60 },
      { key: 'forecastHours', label: '预报时长 (h)', type: 'slider', min: 1, max: 120, step: 1, default: 24 },
      { key: 'physicsScheme', label: '物理方案', type: 'select', options: [
        { label: 'YSU', value: 'ysu' },
        { label: 'MYJ', value: 'myj' },
        { label: 'MYNN', value: 'mynn' },
      ], default: 'ysu' },
      { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
    ]
  } else if (category === 'edge') {
    return [
      { key: 'edgeNodes', label: '边缘节点数', type: 'slider', min: 1, max: 50, step: 1, default: 5 },
      { key: 'bandwidth', label: '带宽限制 (Mbps)', type: 'number', min: 1, max: 1000, default: 100 },
      { key: 'latencyBudget', label: '延迟预算 (ms)', type: 'slider', min: 1, max: 500, step: 5, default: 50 },
      { key: 'computeModel', label: '计算模式', type: 'select', options: [
        { label: '云边协同', value: 'cloud_edge' },
        { label: '纯边缘', value: 'edge_only' },
        { label: '自适应', value: 'adaptive' },
      ], default: 'cloud_edge' },
      { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
    ]
  }
  return [
    { key: 'param1', label: '参数 1', type: 'number', default: 10 },
    { key: 'param2', label: '参数 2', type: 'slider', min: 0, max: 100, step: 1, default: 50 },
    { key: 'advancedConfig', label: '高级配置 (JSON)', type: 'json', default: '{}' },
  ]
}

function buildParamFields(algo: Algorithm) {
  paramFields.value = []
  paramValues.value = {}

  // 1. 按算法名称前缀匹配基础参数（按前缀长度降序匹配，避免短前缀误匹配）
  let fields: ParamField[] = []
  const sortedPrefixes = Object.keys(ALGO_PARAM_MAP).sort((a, b) => b.length - a.length)
  for (const prefix of sortedPrefixes) {
    if (algo.name.startsWith(prefix)) {
      const matched = ALGO_PARAM_MAP[prefix]
      if (matched) { fields = [...matched]; break }
    }
  }

  // 2. 按完整名称匹配变体追加参数
  const extra = ALGO_VARIANT_EXTRA_MAP[algo.name]
  if (extra) {
    fields = [...fields, ...extra]
  }

  // 3. 兜底：按分类生成通用参数
  if (fields.length === 0) {
    fields = buildCategoryDefaultParams(algo.category)
  }

  paramFields.value = fields

  // 初始化参数值
  paramFields.value.forEach((field) => {
    paramValues.value[field.key] = field.default ?? null
    if (field.type === 'json') {
      jsonEditorContent.value = JSON.stringify(field.default ?? {}, null, 2)
    }
  })
}

function resetRunState() {
  runStatus.value = 'idle'
  runProgress.value = 0
  runLog.value = []
  resultData.value = null
  resultJsonStr.value = ''
  isRunning.value = false
  if (runTimer) {
    clearInterval(runTimer)
    runTimer = null
  }
}

async function handleRun() {
  if (!selectedAlgorithm.value) return
  isRunning.value = true
  runStatus.value = 'running'
  runProgress.value = 0
  runLog.value = ['[INFO] 开始执行算法: ' + selectedAlgorithm.value.name]
  resultData.value = null
  resultJsonStr.value = ''

  // 构建参数
  const params: Record<string, unknown> = { ...paramValues.value }
  // 将 JSON 编辑器内容合并
  const jsonField = paramFields.value.find((f) => f.type === 'json')
  if (jsonField) {
    try {
      params[jsonField.key] = JSON.parse(jsonEditorContent.value)
    } catch {
      ElMessage.error('JSON 格式错误，请检查高级配置')
      isRunning.value = false
      runStatus.value = 'error'
      runLog.value.push('[ERROR] JSON 格式错误')
      return
    }
  }

  // 模拟进度
  runTimer = setInterval(() => {
    runProgress.value = Math.min(runProgress.value + Math.random() * 15, 95)
    const step = Math.floor(Math.random() * 3)
    const messages = [
      '[INFO] 正在初始化计算环境...',
      '[INFO] 加载输入数据...',
      '[INFO] 执行核心计算...',
      '[INFO] 正在迭代优化...',
      '[INFO] 计算中间结果...',
      '[INFO] 后处理与验证...',
    ]
    if (step < messages.length && messages[step] !== undefined) {
      runLog.value.push(messages[step]!)
    }
  }, 800)

  try {
    const result = await algorithmApi.execute(selectedAlgorithm.value.id, { params })
    if (runTimer) {
      clearInterval(runTimer)
      runTimer = null
    }
    runProgress.value = 100
    runStatus.value = 'success'
    isRunning.value = false
    runLog.value.push('[SUCCESS] 算法执行完成')
    runLog.value.push(`[INFO] 执行时间: ${result.executionTime}`)
    resultData.value = result.output
    resultJsonStr.value = JSON.stringify(result.output, null, 2)
    ElMessage.success('算法执行成功')
    nextTick(() => initResultChart())
    // 保存参数调整记录
    saveParamRecord({
      success: true,
      executionTime: Number(result.executionTime) || 0,
      accuracy: (result.output as Record<string, unknown>)?.accuracy as number | undefined,
    })
  } catch {
    if (runTimer) {
      clearInterval(runTimer)
      runTimer = null
    }
    runStatus.value = 'error'
    isRunning.value = false
    runLog.value.push('[ERROR] 算法执行失败')
    ElMessage.error('算法执行失败')
    // 保存参数调整记录（失败也记录）
    saveParamRecord({
      success: false,
      executionTime: 0,
    })
  }
}

function handleStop() {
  if (runTimer) {
    clearInterval(runTimer)
    runTimer = null
  }
  isRunning.value = false
  runStatus.value = 'error'
  runLog.value.push('[WARN] 用户手动停止')
  ElMessage.warning('已停止运行')
}

function initResultChart() {
  if (!resultChartRef.value || !resultData.value) return
  resultChartInstance.value = echarts.init(resultChartRef.value)

  // 从结果数据中提取可视化数据
  const output = resultData.value
  let chartData: { xData: string[]; series: Array<{ name: string; data: number[]; color: string }> } = {
    xData: [],
    series: [],
  }

  if (output && typeof output === 'object') {
    // 尝试提取收敛曲线或时间序列数据
    const convergence = output.convergence as Array<{ iteration: number; cost: number }> | undefined
    const timeSeries = output.timeSeries as Array<{ time: string; value: number }> | undefined
    const metrics = output.metrics as Record<string, number> | undefined

    if (Array.isArray(convergence) && convergence.length > 0) {
      chartData.xData = convergence.map((c) => String(c.iteration))
      chartData.series = [
        { name: '代价函数', data: convergence.map((c) => c.cost), color: '#e94560' },
      ]
    } else if (Array.isArray(timeSeries) && timeSeries.length > 0) {
      chartData.xData = timeSeries.map((t) => t.time)
      chartData.series = [
        { name: '数值', data: timeSeries.map((t) => t.value), color: '#3498db' },
      ]
    } else if (metrics) {
      const keys = Object.keys(metrics)
      chartData.xData = keys
      chartData.series = [
        { name: '指标值', data: keys.map((k) => metrics[k] as number), color: '#2ecc71' },
      ]
    } else {
      // 生成模拟数据
      chartData = generateMockChartData()
    }
  } else {
    chartData = generateMockChartData()
  }

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    title: {
      text: '运行结果可视化',
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
      textStyle: { color: '#a0a0b0' },
      top: 30,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: 60,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: chartData.xData,
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0', rotate: 30 },
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0' },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    series: chartData.series.map((s) => ({
      name: s.name,
      type: 'line',
      data: s.data,
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { color: s.color, width: 2 },
      itemStyle: { color: s.color },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: s.color + '40' },
          { offset: 1, color: s.color + '05' },
        ]),
      },
    })),
  }

  resultChartInstance.value.setOption(option)
}

function generateMockChartData() {
  const xData: string[] = []
  const data1: number[] = []
  const data2: number[] = []
  for (let i = 0; i < 20; i++) {
    xData.push(`Step ${i + 1}`)
    data1.push(Math.max(0, 100 * Math.exp(-0.15 * i) + Math.random() * 5))
    data2.push(Math.max(0, 80 * Math.exp(-0.1 * i) + Math.random() * 3))
  }
  return {
    xData,
    series: [
      { name: '代价函数', data: data1, color: '#e94560' },
      { name: 'RMSE', data: data2, color: '#3498db' },
    ],
  }
}

function handleResize() {
  resultChartInstance.value?.resize()
}

// 状态显示
const statusText = computed(() => {
  const map: Record<string, string> = {
    idle: '就绪',
    running: '运行中',
    success: '已完成',
    error: '失败',
  }
  return map[runStatus.value] ?? '未知'
})

const statusType = computed(() => {
  const map: Record<string, string> = {
    idle: 'info',
    running: 'warning',
    success: 'success',
    error: 'danger',
  }
  return map[runStatus.value] ?? 'info'
})

onMounted(async () => {
  await demoModeStore.fetchStatus()
  loadAlgorithms()
  window.addEventListener('resize', handleResize)
})

watch(() => demoModeStore.isDemoMode, () => {
  loadAlgorithms()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  resultChartInstance.value?.dispose()
  if (runTimer) {
    clearInterval(runTimer)
  }
})
</script>

<template>
  <div class="algorithm-lab">
    <div class="lab-container">
      <!-- 左侧：算法分类树 -->
      <el-card class="tree-panel">
        <template #header>
          <div class="panel-header">
            <el-icon><FolderOpened /></el-icon>
            <span>算法分类</span>
          </div>
        </template>
        <div v-loading="treeLoading" class="tree-content">
          <div
            v-for="cat in categories"
            :key="cat.id"
            class="category-group"
          >
            <div
              class="category-header"
              :class="{ expanded: expandedKeys.includes(cat.id) }"
              @click="
                expandedKeys.includes(cat.id)
                  ? expandedKeys = expandedKeys.filter(k => k !== cat.id)
                  : expandedKeys.push(cat.id)
              "
            >
              <el-icon class="arrow-icon">
                <ArrowRight v-if="!expandedKeys.includes(cat.id)" />
                <ArrowDown v-else />
              </el-icon>
              <el-icon class="cat-icon">
                <component :is="cat.icon" />
              </el-icon>
              <span class="cat-label">{{ cat.label }}</span>
              <el-tag size="small" type="info" effect="plain" round>
                {{ cat.children.length }}
              </el-tag>
            </div>
            <div v-show="expandedKeys.includes(cat.id)" class="algorithm-list">
              <div
                v-for="algo in cat.children"
                :key="algo.id"
                class="algorithm-item"
                :class="{ active: selectedAlgorithm?.id === algo.id }"
                @click="handleSelectAlgorithm(algo)"
              >
                <span class="algo-name">{{ algo.name }}</span>
                <el-tag
                  size="small"
                  :type="algo.status === 'ACTIVE' ? 'success' : 'info'"
                  effect="plain"
                >
                  {{ algo.version }}
                </el-tag>
              </div>
              <div v-if="cat.children.length === 0" class="empty-category">
                暂无算法
              </div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 右侧：详情 + 参数 + 运行 + 结果 -->
      <div class="detail-panel">
        <!-- 算法详情卡片 -->
        <el-card v-if="selectedAlgorithm" class="detail-card">
          <template #header>
            <div class="panel-header">
              <el-icon><InfoFilled /></el-icon>
              <span>算法详情</span>
            </div>
          </template>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="算法名称" :span="2">
              {{ algorithmDetail?.name ?? selectedAlgorithm.name }}
            </el-descriptions-item>
            <el-descriptions-item label="分类">
              <el-tag size="small" effect="plain">
                {{ categories.find(c => c.id === selectedAlgorithm?.category)?.label ?? selectedAlgorithm?.category ?? '-' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="版本">
              {{ algorithmDetail?.version ?? selectedAlgorithm.version }}
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag
                size="small"
                :type="selectedAlgorithm.status === 'ACTIVE' ? 'success' : 'warning'"
                effect="plain"
              >
                {{ selectedAlgorithm.status }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="运行次数">
              {{ selectedAlgorithm.runCount }}
            </el-descriptions-item>
            <el-descriptions-item label="最近运行">
              {{ selectedAlgorithm.lastRunAt ? formatDateTime(selectedAlgorithm.lastRunAt) : '从未运行' }}
            </el-descriptions-item>
            <el-descriptions-item label="描述" :span="2">
              {{ algorithmDetail?.description ?? selectedAlgorithm.description ?? '暂无描述' }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 未选择提示 -->
        <el-card v-else class="detail-card empty-detail">
          <el-empty description="请从左侧选择一个算法" />
        </el-card>

        <!-- 参数调整面板 -->
        <el-card v-if="selectedAlgorithm && paramFields.length > 0" class="params-card">
          <template #header>
            <div class="panel-header">
              <el-icon><Setting /></el-icon>
              <span>参数调整</span>
            </div>
          </template>
          <el-form label-width="140px" size="default">
            <template v-for="field in paramFields" :key="field.key">
              <!-- 滑块 -->
              <el-form-item v-if="field.type === 'slider'" :label="field.label">
                <div class="slider-row">
                  <el-slider
                    v-model="paramValues[field.key] as number"
                    :min="field.min"
                    :max="field.max"
                    :step="field.step"
                    :show-input="true"
                    input-size="small"
                    style="flex: 1"
                  />
                </div>
              </el-form-item>
              <!-- 数字输入 -->
              <el-form-item v-else-if="field.type === 'number'" :label="field.label">
                <el-input-number
                  v-model="paramValues[field.key] as number"
                  :min="field.min"
                  :max="field.max"
                  :step="field.step ?? 1"
                  style="width: 200px"
                />
              </el-form-item>
              <!-- 下拉选择 -->
              <el-form-item v-else-if="field.type === 'select'" :label="field.label">
                <el-select v-model="paramValues[field.key]" style="width: 200px">
                  <el-option
                    v-for="opt in field.options"
                    :key="opt.value"
                    :label="opt.label"
                    :value="opt.value"
                  />
                </el-select>
              </el-form-item>
              <!-- JSON 编辑器 -->
              <el-form-item v-else-if="field.type === 'json'" :label="field.label">
                <div class="json-editor-wrapper">
                  <el-input
                    v-model="jsonEditorContent"
                    type="textarea"
                    :rows="4"
                    placeholder="请输入 JSON 格式配置"
                    class="json-editor"
                    spellcheck="false"
                  />
                </div>
              </el-form-item>
            </template>
          </el-form>
        </el-card>

        <!-- 运行控制 -->
        <el-card v-if="selectedAlgorithm" class="run-card">
          <template #header>
            <div class="panel-header">
              <el-icon><VideoPlay /></el-icon>
              <span>运行控制</span>
              <el-tag :type="statusType as any" size="small" effect="dark" class="status-tag">
                {{ statusText }}
              </el-tag>
            </div>
          </template>
          <div class="run-controls">
            <div class="run-buttons">
              <el-button
                type="primary"
                :loading="isRunning"
                :disabled="isRunning"
                @click="handleRun"
              >
                <el-icon><CaretRight /></el-icon>
                运行
              </el-button>
              <el-button
                type="danger"
                :disabled="!isRunning"
                @click="handleStop"
              >
                <el-icon><SwitchButton /></el-icon>
                停止
              </el-button>
            </div>
            <el-progress
              v-if="runStatus === 'running'"
              :percentage="Math.round(runProgress)"
              :stroke-width="10"
              :text-inside="true"
              class="run-progress"
            />
          </div>
          <!-- 运行日志 -->
          <div v-if="runLog.length > 0" class="run-log">
            <div class="log-header">运行日志</div>
            <div class="log-content">
              <div v-for="(log, idx) in runLog" :key="idx" class="log-line" :class="{
                'log-info': log.startsWith('[INFO]'),
                'log-success': log.startsWith('[SUCCESS]'),
                'log-error': log.startsWith('[ERROR]'),
                'log-warn': log.startsWith('[WARN]'),
              }">
                {{ log }}
              </div>
            </div>
          </div>
        </el-card>

        <!-- 运行结果展示区 -->
        <el-card v-if="selectedAlgorithm && (runStatus === 'success' || runStatus === 'error')" class="result-card">
          <template #header>
            <div class="panel-header">
              <el-icon><DataLine /></el-icon>
              <span>运行结果</span>
            </div>
          </template>
          <el-tabs v-model="activeResultTab">
            <el-tab-pane label="图表" name="chart">
              <div ref="resultChartRef" style="width: 100%; height: 350px"></div>
            </el-tab-pane>
            <el-tab-pane label="JSON 结果" name="json">
              <div class="json-result-wrapper">
                <pre class="json-result">{{ resultJsonStr || '无结果数据' }}</pre>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>

        <!-- 参数调整历史 -->
        <el-card v-if="selectedAlgorithm && paramFields.length > 0" shadow="never" class="history-card">
          <template #header>
            <div class="card-header">
              <div class="panel-header">
                <el-icon><Clock /></el-icon>
                <span>参数调整历史</span>
              </div>
              <div style="display: flex; gap: 8px; align-items: center;">
                <el-tag size="small" type="info">{{ paramHistory.length }} 条记录</el-tag>
                <el-button
                  v-if="compareIds.length === 2"
                  size="small"
                  type="warning"
                  plain
                  @click="showCompare"
                >
                  对比选中项
                </el-button>
                <el-button
                  v-if="compareIds.length > 0"
                  size="small"
                  plain
                  @click="compareIds = []; compareVisible = false"
                >
                  取消选择
                </el-button>
                <el-button size="small" type="danger" plain @click="clearParamHistory" :disabled="paramHistory.length === 0">
                  清空
                </el-button>
              </div>
            </div>
          </template>
          <div v-if="paramHistory.length === 0" class="history-empty">
            暂无调整记录，运行算法后自动保存参数快照
          </div>
          <el-timeline v-else>
            <el-timeline-item
              v-for="record in paramHistory"
              :key="record.id"
              :timestamp="formatHistoryTime(record.timestamp)"
              placement="top"
              :type="record.result.success ? 'success' : 'danger'"
              :hollow="false"
            >
              <div class="history-item" :class="{ 'history-item--compare-selected': compareIds.includes(record.id) }">
                <div class="history-item__header">
                  <el-checkbox
                    :model-value="compareIds.includes(record.id)"
                    @change="toggleCompare(record.id)"
                    size="small"
                    class="history-item__compare-check"
                  />
                  <span class="history-item__result" :class="record.result.success ? 'history-item__result--success' : 'history-item__result--fail'">
                    {{ record.result.success ? '成功' : '失败' }}
                  </span>
                  <span class="history-item__time">
                    耗时 {{ record.result.executionTime }}ms
                    <template v-if="record.result.accuracy">
                      &middot; 精度 {{ (record.result.accuracy * 100).toFixed(1) }}%
                    </template>
                  </span>
                </div>
                <div class="history-item__params">
                  <el-collapse>
                    <el-collapse-item :title="`参数 (${Object.keys(record.params).length}项)`">
                      <div v-for="(value, key) in record.params" :key="key" class="history-param-row">
                        <span class="history-param-key">{{ key }}</span>
                        <span class="history-param-value">{{ typeof value === 'object' ? JSON.stringify(value) : value }}</span>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>
                <div class="history-item__actions">
                  <el-button size="small" type="primary" plain @click="restoreParams(record)">
                    加载此参数
                  </el-button>
                  <el-button size="small" type="danger" plain @click="deleteParamRecord(record.id)">
                    删除
                  </el-button>
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>

        <!-- 参数对比对话框 -->
        <el-dialog
          v-model="compareVisible"
          title="参数对比"
          width="700px"
          destroy-on-close
          class="compare-dialog"
        >
          <div v-if="compareRecords.length === 2" class="compare-content">
            <div class="compare-legend">
              <div class="compare-legend-item">
                <span class="compare-legend-dot compare-legend-dot--a"></span>
                <span>{{ formatHistoryTime(compareRecords[0]!.timestamp) }} - {{ compareRecords[0]!.result.success ? '成功' : '失败' }}</span>
              </div>
              <div class="compare-legend-item">
                <span class="compare-legend-dot compare-legend-dot--b"></span>
                <span>{{ formatHistoryTime(compareRecords[1]!.timestamp) }} - {{ compareRecords[1]!.result.success ? '成功' : '失败' }}</span>
              </div>
            </div>
            <el-table :data="compareDiff" border size="small" class="compare-table">
              <el-table-column prop="key" label="参数名" width="180" />
              <el-table-column label="记录 A" min-width="180">
                <template #default="{ row }">
                  <span :class="{ 'compare-value--changed': row.changed }">
                    {{ typeof row.valueA === 'object' ? JSON.stringify(row.valueA) : row.valueA ?? '-' }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="记录 B" min-width="180">
                <template #default="{ row }">
                  <span :class="{ 'compare-value--changed': row.changed }">
                    {{ typeof row.valueB === 'object' ? JSON.stringify(row.valueB) : row.valueB ?? '-' }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column label="差异" width="80" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.changed" type="danger" size="small">不同</el-tag>
                  <el-tag v-else type="success" size="small">相同</el-tag>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <template #footer>
            <el-button @click="closeCompare">关闭</el-button>
          </template>
        </el-dialog>
      </div>
    </div>
  </div>
</template>

<style scoped>
.algorithm-lab {
  display: flex;
  flex-direction: column;
  gap: 0;
  height: 100%;
}

.lab-container {
  display: flex;
  gap: 16px;
  height: 100%;
  min-height: 0;
}

/* 左侧分类树 */
.tree-panel {
  width: 280px;
  min-width: 280px;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.tree-panel :deep(.el-card__body) {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.tree-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.category-group {
  margin-bottom: 2px;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
  user-select: none;
}

.category-header:hover {
  background-color: var(--color-sidebar-hover);
}

.category-header.expanded {
  background-color: var(--color-sidebar-active);
}

.arrow-icon {
  font-size: 12px;
  color: var(--color-text-secondary);
  transition: transform 0.2s;
}

.cat-icon {
  font-size: 16px;
  color: var(--color-primary-light);
}

.cat-label {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.algorithm-list {
  padding-left: 16px;
}

.algorithm-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  margin-bottom: 1px;
}

.algorithm-item:hover {
  background-color: var(--color-sidebar-hover);
}

.algorithm-item.active {
  background-color: var(--color-primary);
  color: #fff;
}

.algo-name {
  font-size: 12px;
  color: var(--color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 140px;
}

.algorithm-item.active .algo-name {
  color: #fff;
}

.empty-category {
  padding: 8px 10px;
  font-size: 12px;
  color: var(--color-text-muted);
}

/* 右侧详情面板 */
.detail-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  overflow-y: auto;
  padding-right: 4px;
}

.detail-card,
.params-card,
.run-card,
.result-card {
  border-radius: 8px;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.status-tag {
  margin-left: auto;
}

.empty-detail {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

/* 参数面板 */
.slider-row {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.json-editor-wrapper {
  width: 100%;
}

.json-editor :deep(.el-textarea__inner) {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;
  background-color: var(--color-bg) !important;
  color: var(--color-text-primary) !important;
}

/* 运行控制 */
.run-controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.run-buttons {
  display: flex;
  gap: 12px;
}

.run-progress {
  max-width: 400px;
}

/* 运行日志 */
.run-log {
  margin-top: 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  overflow: hidden;
}

.log-header {
  padding: 6px 12px;
  background-color: var(--color-sidebar);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  border-bottom: 1px solid var(--color-border);
}

.log-content {
  padding: 8px 12px;
  max-height: 150px;
  overflow-y: auto;
  background-color: var(--color-bg);
}

.log-line {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: var(--color-text-secondary);
}

.log-info {
  color: var(--color-info);
}

.log-success {
  color: var(--color-success);
}

.log-error {
  color: var(--color-danger);
}

.log-warn {
  color: var(--color-warning);
}

/* JSON 结果 */
.json-result-wrapper {
  max-height: 400px;
  overflow: auto;
}

.json-result {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  line-height: 1.6;
  color: var(--color-text-primary);
  background-color: var(--color-bg);
  padding: 12px;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  white-space: pre-wrap;
  word-break: break-all;
}

/* 响应式 */
@media (max-width: 900px) {
  .lab-container {
    flex-direction: column;
  }
  .tree-panel {
    width: 100%;
    min-width: unset;
    max-height: 300px;
  }
}

/* 参数调整历史 */
.history-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.history-empty {
  text-align: center;
  color: var(--color-text-muted);
  padding: 20px;
}

.history-item {
  padding: 4px 0;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.history-item--compare-selected {
  background-color: rgba(230, 162, 60, 0.08);
  border: 1px solid rgba(230, 162, 60, 0.2);
  padding: 4px 8px;
}

.history-item__header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.history-item__compare-check {
  margin-right: 0;
}

.history-item__result {
  font-weight: 600;
  font-size: 13px;
}

.history-item__result--success {
  color: var(--color-success);
}

.history-item__result--fail {
  color: var(--color-danger);
}

.history-item__time {
  font-size: 12px;
  color: var(--color-text-muted);
}

.history-item__params {
  margin-bottom: 8px;
}

.history-param-row {
  display: flex;
  justify-content: space-between;
  padding: 2px 0;
  font-size: 12px;
  border-bottom: 1px solid var(--color-border);
}

.history-param-row:last-child {
  border-bottom: none;
}

.history-param-key {
  color: var(--color-text-secondary);
  font-family: 'Consolas', monospace;
}

.history-param-value {
  color: var(--color-text-primary);
  font-family: 'Consolas', monospace;
  max-width: 60%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-item__actions {
  display: flex;
  gap: 8px;
}

/* 参数对比 */
.compare-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.compare-legend {
  display: flex;
  gap: 24px;
  align-items: center;
}

.compare-legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.compare-legend-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.compare-legend-dot--a {
  background-color: #409eff;
}

.compare-legend-dot--b {
  background-color: #67c23a;
}

.compare-table {
  font-size: 13px;
}

.compare-value--changed {
  color: var(--color-danger);
  font-weight: 600;
}
</style>
