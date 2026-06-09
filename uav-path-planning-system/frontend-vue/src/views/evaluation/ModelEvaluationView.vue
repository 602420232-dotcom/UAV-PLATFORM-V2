<template>
  <div class="model-evaluation">
    <!-- 顶部栏 -->
    <div class="top-bar">
      <div class="top-bar-left">
        <h2 class="page-title">模型评估看板</h2>
        <el-tag type="warning" effect="plain" size="default" class="demo-tag">
          <el-icon><MagicStick /></el-icon>&nbsp;演示模式 · 评估数据为本地模拟
        </el-tag>
      </div>

      <div class="top-bar-controls">
        <el-form :inline="true" size="default" class="control-form">
          <el-form-item label="观测变量">
            <el-select v-model="obsVariable" style="width: 140px">
              <el-option label="温度" value="temperature" />
              <el-option label="风速" value="windSpeed" />
              <el-option label="气压" value="pressure" />
              <el-option label="降水" value="precipitation" />
            </el-select>
          </el-form-item>
          <el-form-item label="评估周期">
            <el-select v-model="evalPeriod" style="width: 160px" @change="refreshData">
              <el-option label="近 7 天" value="7" />
              <el-option label="近 30 天" value="30" />
              <el-option label="自定义" value="custom" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="evalPeriod === 'custom'">
            <el-date-picker
              v-model="customRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="refreshing" @click="refreshData">
              <el-icon><Refresh /></el-icon>&nbsp;刷新评估
            </el-button>
            <el-button type="success" @click="exportCSV">
              <el-icon><Download /></el-icon>&nbsp;导出 CSV
            </el-button>
            <el-switch
              v-model="compareMode"
              active-text="对比模式"
              inactive-text="普通模式"
              style="margin-left: 8px"
            />
          </el-form-item>
        </el-form>
      </div>
    </div>

    <!-- 主体：左 65% / 右 35% -->
    <div class="main-body">
      <!-- 左侧 Tab -->
      <div class="left-panel">
        <el-tabs v-model="activeTab" type="border-card" class="main-tabs">
          <!-- Tab 1 指标对比 -->
          <el-tab-pane label="指标对比" name="metrics">
            <div class="model-cards">
              <div
                v-for="m in models"
                :key="m.key"
                class="model-card"
                :class="{
                  'best-model': m.key === bestModelKey,
                  'hidden': !selectedModels.includes(m.key)
                }"
              >
                <div class="card-header" :style="{ borderTopColor: m.color }">
                  <span class="card-title" :style="{ color: m.color }">{{ m.name }}</span>
                  <el-tag
                    v-if="m.key === bestModelKey"
                    type="success"
                    size="small"
                    effect="dark"
                    class="best-badge"
                  >
                    <el-icon><Star /></el-icon>&nbsp;最佳
                  </el-tag>
                </div>

                <div class="metric-grid">
                  <div
                    v-for="metric in metricKeys"
                    :key="metric"
                    class="metric-cell"
                  >
                    <div class="metric-label">{{ metricLabels[metric] }}</div>
                    <div class="metric-value" :class="metricValueClass(metric, m)">
                      {{ formatMetric(metric, metricsByModel[m.key][metric]) }}
                    </div>
                    <div
                      v-if="compareMode && m.key !== bestModelKey"
                      class="metric-diff"
                      :class="{ 'is-worse': isWorse(metric, m) }"
                    >
                      {{ diffText(metric, m) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- Tab 2 时间序列曲线 -->
          <el-tab-pane label="时间序列曲线" name="timeseries">
            <div class="ts-header">
              <el-select v-model="selectedMetric" style="width: 180px" @change="renderTimeseries">
                <el-option
                  v-for="metric in metricKeys"
                  :key="metric"
                  :label="metricLabels[metric]"
                  :value="metric"
                />
              </el-select>
              <span class="ts-hint">图例可点击切换显示/隐藏对应模型</span>
            </div>
            <div ref="tsChartRef" class="chart-box" style="height: 380px"></div>
          </el-tab-pane>

          <!-- Tab 3 决策效能曲线 -->
          <el-tab-pane label="决策效能曲线" name="roc">
            <div ref="rocChartRef" class="chart-box" style="height: 380px"></div>
            <div class="auc-cards">
              <div
                v-for="m in models"
                :key="'auc-' + m.key"
                class="auc-card"
                :class="{ 'best-model': m.key === bestModelKey, hidden: !selectedModels.includes(m.key) }"
              >
                <span class="auc-label" :style="{ color: m.color }">{{ m.name }}</span>
                <span class="auc-value">AUC {{ (metricsByModel[m.key]?.auc || 0).toFixed(3) }}</span>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 右侧控制面板 -->
      <div class="right-panel">
        <el-card shadow="never" class="control-card">
          <template #header>
            <div class="panel-title">
              <el-icon><Setting /></el-icon>&nbsp;评估控制
            </div>
          </template>

          <div class="control-section">
            <div class="section-title">模型选择</div>
            <el-checkbox-group v-model="selectedModels" @change="onModelChange">
              <div class="check-row" v-for="m in models" :key="'cb-' + m.key">
                <el-checkbox :value="m.key">
                  <span class="check-label" :style="{ color: m.color }">{{ m.name }}</span>
                </el-checkbox>
              </div>
            </el-checkbox-group>
          </div>

          <el-divider />

          <div class="control-section">
            <div class="section-title">
              预测步长筛选
              <span class="section-sub">当前：{{ currentHourLabel }}</span>
            </div>
            <el-slider
              v-model="selectedStep"
              :min="0"
              :max="24"
              :step="6"
              :marks="stepMarks"
              show-stops
              @change="onStepChange"
            />
          </div>

          <el-divider />

          <div class="control-section">
            <div class="section-title">对比模式</div>
            <el-switch
              v-model="compareMode"
              active-text="高亮差值"
              inactive-text="关闭"
            />
            <div class="hint-text">开启后，各模型指标会显示相对于「最佳模型」的差值百分比。</div>
          </div>

          <el-divider />

          <div class="control-section">
            <div class="section-title">快捷操作</div>
            <div class="button-row">
              <el-button type="primary" :loading="refreshing" block @click="refreshData">
                <el-icon><Refresh /></el-icon>&nbsp;刷新评估
              </el-button>
              <el-button type="success" block @click="exportCSV">
                <el-icon><Download /></el-icon>&nbsp;导出 CSV
              </el-button>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import {
  Refresh, Download, Setting, Star, MagicStick
} from '@element-plus/icons-vue'

// ===== 基础配置 =====
const models = [
  { key: 'wrf', name: 'WRF', color: '#409EFF', baseRmse: 1.2 },
  { key: 'fengwu', name: '风乌', color: '#67C23A', baseRmse: 0.8 },
  { key: 'tianzi', name: '天资', color: '#E6A23C', baseRmse: 1.5 },
  { key: 'fenglei', name: '风雷', color: '#F56C6C', baseRmse: 1.1 }
]

const metricKeys = ['rmse', 'mae', 'crps', 'r', 'bias', 'hitRate']
const metricLabels = {
  rmse: 'RMSE',
  mae: 'MAE',
  crps: 'CRPS',
  r: '相关系数 R',
  bias: '偏差 Bias',
  hitRate: '命中率'
}
// lowerIsBetter: 越小越好
const lowerIsBetter = new Set(['rmse', 'mae', 'crps', 'bias'])
// upperIsBetter: 越大越好
const upperIsBetter = new Set(['r', 'hitRate'])

// 指标定义：单位、小数位、范围
const metricMeta = {
  rmse: { decimals: 3, unit: '' },
  mae: { decimals: 3, unit: '' },
  crps: { decimals: 3, unit: '' },
  r: { decimals: 3, unit: '' },
  bias: { decimals: 3, unit: '' },
  hitRate: { decimals: 2, unit: '%' },
  auc: { decimals: 3, unit: '' }
}

// ===== 响应式状态 =====
const activeTab = ref('metrics')
const obsVariable = ref('temperature')
const evalPeriod = ref('7')
const customRange = ref(null)
const compareMode = ref(false)
const refreshing = ref(false)
const selectedModels = ref(models.map(m => m.key))
const selectedStep = ref(12)
const selectedMetric = ref('rmse')

const stepMarks = {
  0: '0h', 6: '6h', 12: '12h', 18: '18h', 24: '24h'
}
const currentHourLabel = computed(() => stepMarks[selectedStep.value])

// 原始/扰动后的数据：按 model -> metric -> hour 存储
// 这里为简化，当前只展示汇总值（汇总按 selectedStep 取）
const rawData = reactive({})

// 当前视图聚合值（按当前步长）
const metricsByModel = reactive({})

function rand(min, max) {
  return Math.random() * (max - min) + min
}

function perturb(val, ratio = 0.08) {
  return val * (1 + rand(-ratio, ratio))
}

function generateOneSet(baseRmse) {
  const rmse = Math.max(0.1, perturb(baseRmse))
  return {
    rmse,
    mae: rmse * rand(0.7, 0.9),
    crps: rmse * rand(0.6, 0.75),
    r: rand(0.7, 0.95),
    bias: rand(-0.3, 0.3),
    hitRate: rand(0.6, 0.95) * 100,
    auc: rand(0.65, 0.95)
  }
}

function initRawData() {
  models.forEach((m) => {
    rawData[m.key] = {}
    for (let h = 0; h <= 24; h += 6) {
      rawData[m.key][h] = generateOneSet(m.baseRmse)
    }
  })
}

function applyCurrentStep() {
  const h = selectedStep.value
  models.forEach((m) => {
    metricsByModel[m.key] = { ...rawData[m.key][h] }
  })
}

function refreshData() {
  refreshing.value = true
  const loading = ElMessage({
    message: '正在重新评估模型...',
    type: 'info',
    duration: 0
  })
  setTimeout(() => {
    initRawData()
    applyCurrentStep()
    nextTick(() => {
      renderTimeseries()
      renderROC()
    })
    loading.close()
    ElMessage.success('评估数据已刷新')
    refreshing.value = false
  }, 1200)
}

onMounted(() => {
  initRawData()
  applyCurrentStep()
  nextTick(() => {
    renderTimeseries()
    renderROC()
  })
})

// ===== 最佳模型识别 =====
// 综合得分：rmse/mae/crps/bias 越小越好，r/hitRate 越大越好
const bestModelKey = computed(() => {
  const keys = Object.keys(metricsByModel).filter(k => selectedModels.value.includes(k))
  if (!keys.length) return null
  let best = keys[0]
  let bestScore = computeScore(best)
  for (let i = 1; i < keys.length; i++) {
    const s = computeScore(keys[i])
    if (s < bestScore) {
      best = keys[i]
      bestScore = s
    }
  }
  return best
})

function computeScore(key) {
  const v = metricsByModel[key]
  // 归一化得分（越小越好）
  const penaltyLow = v.rmse + v.mae + v.crps + Math.abs(v.bias)
  const penaltyHigh = (1 - v.r) + (1 - v.hitRate / 100)
  return penaltyLow + penaltyHigh * 2
}

// ===== 格式化 & 差异 =====
function formatMetric(metric, val) {
  if (val === undefined || val === null || Number.isNaN(val)) return '-'
  const meta = metricMeta[metric] || { decimals: 3, unit: '' }
  return val.toFixed(meta.decimals) + meta.unit
}

function metricValueClass(metric, m) {
  if (m.key === bestModelKey.value) return 'is-best'
  return ''
}

function isWorse(metric, m) {
  if (m.key === bestModelKey.value) return false
  const best = metricsByModel[bestModelKey.value][metric]
  const cur = metricsByModel[m.key][metric]
  if (lowerIsBetter.has(metric)) return cur > best
  if (upperIsBetter.has(metric)) return cur < best
  return false
}

function diffText(metric, m) {
  if (m.key === bestModelKey.value) return '—'
  const best = metricsByModel[bestModelKey.value][metric]
  const cur = metricsByModel[m.key][metric]
  if (!best) return '—'
  const diffPct = ((cur - best) / Math.abs(best || 1)) * 100
  const sign = diffPct >= 0 ? '+' : ''
  return `${sign}${diffPct.toFixed(1)}%`
}

// ===== 交互 =====
function onModelChange() {
  renderTimeseries()
  renderROC()
}

function onStepChange() {
  applyCurrentStep()
  renderTimeseries()
  renderROC()
}

watch([activeTab, compareMode], () => {
  nextTick(() => {
    renderTimeseries()
    renderROC()
  })
})

// ===== ECharts =====
const tsChartRef = ref(null)
const rocChartRef = ref(null)
let tsChart = null
let rocChart = null

function renderTimeseries() {
  if (activeTab.value !== 'timeseries') return
  if (!tsChartRef.value) return
  if (!tsChart) {
    tsChart = echarts.init(tsChartRef.value)
  }
  const metric = selectedMetric.value
  const xAxis = [0, 6, 12, 18, 24].map(h => `${h}h`)
  const series = models
    .filter(m => selectedModels.value.includes(m.key))
    .map((m) => ({
      name: m.name,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      itemStyle: { color: m.color },
      lineStyle: { width: 2, color: m.color },
      areaStyle: { color: m.color, opacity: 0.08 },
      data: [0, 6, 12, 18, 24].map(h => Number((rawData[m.key][h][metric] || 0).toFixed(3)))
    }))
  // 观测基准线（取各模型在 0h 的均值）
  const baseline = models.reduce((sum, m) => sum + (rawData[m.key][0][metric] || 0), 0) / models.length

  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      top: 0,
      icon: 'roundRect'
    },
    grid: {
      left: 40,
      right: 40,
      top: 40,
      bottom: 40
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xAxis,
      name: '预测步长'
    },
    yAxis: [
      {
        type: 'value',
        name: metricLabels[metric],
        splitLine: { lineStyle: { type: 'dashed', color: '#eee' } }
      },
      {
        type: 'value',
        name: '基准线',
        show: false
      }
    ],
    series: [
      ...series,
      {
        name: '观测基准',
        type: 'line',
        symbol: 'none',
        lineStyle: { type: 'dashed', color: '#999', width: 1.5 },
        markLine: {
          silent: true,
          symbol: 'none',
          yAxis: Number(baseline.toFixed(3)),
          label: { formatter: `基准 {c}` },
          lineStyle: { type: 'dashed', color: '#999' }
        },
        data: []
      }
    ]
  }
  tsChart.setOption(option, true)
}

function renderROC() {
  if (activeTab.value !== 'roc') return
  if (!rocChartRef.value) return
  if (!rocChart) {
    rocChart = echarts.init(rocChartRef.value)
  }
  // 生成 ROC 类似曲线（False Alarm Rate vs Hit Rate）
  const points = 20
  const makeCurve = (m) => {
    const auc = metricsByModel[m.key].auc || 0.75
    // 根据 AUC 生成一条单调递增的曲线
    const data = []
    for (let i = 0; i <= points; i++) {
      const x = i / points
      // y = x ^ (1 / k)，k 越大 AUC 越大
      // 用 k 来拟合 AUC：AUC ≈ k / (k + 1) => k = AUC / (1 - AUC)
      const k = Math.max(0.5, auc / (1 - auc))
      const y = Math.pow(x, 1 / k)
      // 加点小扰动使其不太平滑
      const jittered = Math.min(1, Math.max(0, y + (Math.random() - 0.5) * 0.04))
      data.push([Number(x.toFixed(2)), Number(jittered.toFixed(3))])
    }
    return data
  }

  const series = models
    .filter(m => selectedModels.value.includes(m.key))
    .map((m) => ({
      name: m.name,
      type: 'line',
      smooth: true,
      symbol: 'none',
      itemStyle: { color: m.color },
      lineStyle: { width: 2, color: m.color },
      areaStyle: { color: m.color, opacity: 0.05 },
      data: makeCurve(m)
    }))

  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const lines = params.map(p => `${p.marker} ${p.seriesName}: FAR=${p.value[0]}, HR=${p.value[1]}`)
        return lines.join('<br/>')
      }
    },
    legend: { top: 0, icon: 'roundRect' },
    grid: { left: 50, right: 30, top: 40, bottom: 50 },
    xAxis: {
      type: 'value',
      name: 'False Alarm Rate (FAR)',
      min: 0,
      max: 1,
      splitLine: { lineStyle: { type: 'dashed', color: '#eee' } }
    },
    yAxis: {
      type: 'value',
      name: 'Hit Rate (HR)',
      min: 0,
      max: 1,
      splitLine: { lineStyle: { type: 'dashed', color: '#eee' } }
    },
    series: [
      {
        name: '对角线 (随机)',
        type: 'line',
        symbol: 'none',
        lineStyle: { type: 'dashed', color: '#bbb' },
        data: [[0, 0], [1, 1]]
      },
      ...series
    ]
  }
  rocChart.setOption(option, true)
}

window.addEventListener('resize', onResize)
function onResize() {
  tsChart && tsChart.resize()
  rocChart && rocChart.resize()
}

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  tsChart && tsChart.dispose()
  rocChart && rocChart.dispose()
  tsChart = null
  rocChart = null
})

// ===== CSV 导出 =====
function pad(n) { return n < 10 ? '0' + n : '' + n }
function fmtDate(d) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function exportCSV() {
  const rows = []
  rows.push(['模型', 'RMSE', 'MAE', 'CRPS', 'R', 'Bias', 'HitRate'])
  models.forEach((m) => {
    const v = metricsByModel[m.key]
    rows.push([
      m.name,
      v.rmse.toFixed(3),
      v.mae.toFixed(3),
      v.crps.toFixed(3),
      v.r.toFixed(3),
      v.bias.toFixed(3),
      v.hitRate.toFixed(2)
    ])
  })
  const csv = rows.map(r => r.join(',')).join('\n')
  try {
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `model_evaluation_${fmtDate(new Date())}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('CSV 已导出')
  } catch (e) {
    ElMessage.error('导出失败：' + e.message)
  }
}
</script>

<style scoped>
.model-evaluation {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 顶部栏 */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  background: #fff;
  border-radius: 10px;
  padding: 14px 20px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}
.top-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #24292f;
}
.demo-tag {
  font-size: 12px;
}
.top-bar-controls :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 12px;
}

/* 主体 */
.main-body {
  display: grid;
  grid-template-columns: 65% 35%;
  gap: 16px;
}
@media (max-width: 1100px) {
  .main-body {
    grid-template-columns: 1fr;
  }
}

.left-panel .main-tabs {
  min-height: 520px;
}

/* 模型卡片 */
.model-cards {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
@media (max-width: 900px) {
  .model-cards {
    grid-template-columns: 1fr;
  }
}

.model-card {
  background: #fff;
  border: 1px solid #eaecef;
  border-radius: 10px;
  overflow: hidden;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}
.model-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
}
.model-card.hidden {
  opacity: 0.35;
  filter: grayscale(0.3);
}
.model-card.best-model {
  border-color: #52c41a;
  box-shadow: 0 2px 10px rgba(82, 196, 26, 0.15);
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 3px solid #409EFF;
  background: #fafbfc;
}
.card-title {
  font-size: 15px;
  font-weight: 600;
}
.best-badge {
  font-weight: 500;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px;
  background: #eaecef;
}
.metric-cell {
  background: #fff;
  padding: 12px 10px;
  text-align: center;
}
.metric-label {
  font-size: 12px;
  color: #8a8f98;
  margin-bottom: 6px;
}
.metric-value {
  font-size: 18px;
  font-weight: 600;
  color: #24292f;
  font-variant-numeric: tabular-nums;
}
.metric-value.is-best {
  color: #52c41a;
}
.metric-diff {
  margin-top: 4px;
  font-size: 12px;
  color: #52c41a;
  font-variant-numeric: tabular-nums;
}
.metric-diff.is-worse {
  color: #f56c6c;
}

/* 时间序列 */
.ts-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.ts-hint {
  font-size: 12px;
  color: #8a8f98;
}
.chart-box {
  width: 100%;
}

/* AUC 卡片 */
.auc-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 16px;
}
.auc-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: 12px 14px;
  background: #fafbfc;
  border: 1px solid #eaecef;
  border-radius: 8px;
}
.auc-card.best-model {
  border-color: #52c41a;
  background: #f4fff1;
}
.auc-card.hidden {
  opacity: 0.35;
}
.auc-label {
  font-size: 13px;
  font-weight: 500;
}
.auc-value {
  font-size: 16px;
  font-weight: 600;
  color: #24292f;
  font-variant-numeric: tabular-nums;
}

/* 右侧 */
.right-panel .control-card {
  border-radius: 10px;
}
.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #24292f;
}
.control-section {
  margin: 4px 0;
}
.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #57606a;
  margin-bottom: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.section-sub {
  font-size: 12px;
  font-weight: 400;
  color: #8a8f98;
}
.check-row {
  padding: 4px 0;
}
.check-label {
  font-weight: 500;
}
.hint-text {
  margin-top: 8px;
  font-size: 12px;
  color: #8a8f98;
  line-height: 1.5;
}
.button-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
</style>
