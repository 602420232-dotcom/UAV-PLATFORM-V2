<template>
  <div class="sensitivity-view">
    <div class="page-header">
      <h2 class="page-title">参数敏感性分析</h2>
      <div class="header-actions">
        <el-select v-model="selectedAlgorithm" size="small" style="width: 140px">
          <el-option value="de_rrt_star" label="DE-RRT*" />
          <el-option value="dwa" label="DWA" />
          <el-option value="vrptw" label="VRPTW" />
        </el-select>
        <el-button type="primary" size="small" @click="handleRunAnalysis">
          <span class="btn-icon">🔬</span> 运行分析
        </el-button>
      </div>
    </div>

    <el-row :gutter="16" class="main-row">
      <!-- 左侧：参数配置 -->
      <el-col :span="6">
        <el-card shadow="hover" class="panel">
          <template #header>
            <span class="panel-title">待分析参数</span>
          </template>
          <div class="param-list">
            <div
              v-for="param in analysisParams"
              :key="param.name"
              class="param-item"
              :class="{ active: param.enabled }"
              @click="param.enabled = !param.enabled"
            >
              <el-checkbox v-model="param.enabled" @click.stop />
              <div class="param-info">
                <span class="param-name">{{ param.label }}</span>
                <span class="param-range">范围: {{ param.min }} ~ {{ param.max }}</span>
              </div>
            </div>
          </div>
        </el-card>

        <el-card shadow="hover" class="panel mt-12">
          <template #header>
            <span class="panel-title">分析配置</span>
          </template>
          <el-form :model="analysisConfig" label-width="90px" size="small">
            <el-form-item label="采样点数">
              <el-input-number v-model="analysisConfig.sampleCount" :min="5" :max="50" :step="5" style="width: 100%" />
            </el-form-item>
            <el-form-item label="目标指标">
              <el-select v-model="analysisConfig.targetMetric" style="width: 100%">
                <el-option value="distance" label="路径距离" />
                <el-option value="duration" label="飞行时间" />
                <el-option value="energy" label="能耗" />
                <el-option value="risk" label="风险评分" />
              </el-select>
            </el-form-item>
            <el-form-item label="分析类型">
              <el-select v-model="analysisConfig.analysisType" style="width: 100%">
                <el-option value="one-way" label="单因素分析" />
                <el-option value="sobol" label="Sobol全局敏感度" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 中间：结果图表 -->
      <el-col :span="12">
        <el-card shadow="hover" class="panel">
          <template #header>
            <div class="panel-head">
              <span class="panel-title">敏感性分析结果</span>
              <el-tag size="small" type="info">{{ selectedAlgorithm }} - {{ analysisConfig.targetMetric }}</el-tag>
            </div>
          </template>
          <div ref="sensitivityChartRef" class="sensitivity-chart" />
        </el-card>

        <el-card shadow="hover" class="panel mt-12">
          <template #header>
            <span class="panel-title">参数-指标相关性矩阵</span>
          </template>
          <div ref="correlationMatrixRef" class="correlation-matrix" />
        </el-card>
      </el-col>

      <!-- 右侧：敏感度排名 -->
      <el-col :span="6">
        <el-card shadow="hover" class="panel">
          <template #header>
            <span class="panel-title">敏感度排名</span>
          </template>
          <div class="rank-list">
            <div
              v-for="(item, idx) in sensitivityRank"
              :key="item.param"
              class="rank-item"
            >
              <div class="rank-badge" :class="`rank-${idx + 1}`">{{ idx + 1 }}</div>
              <div class="rank-info">
                <span class="rank-param">{{ item.label }}</span>
                <span class="rank-value">敏感度: {{ item.sensitivity.toFixed(3) }}</span>
              </div>
              <el-progress
                :percentage="(item.sensitivity / maxSensitivity * 100)"
                :stroke-width="8"
                :color="progressColor(idx)"
                style="width: 80px"
              />
            </div>
          </div>
        </el-card>

        <el-card shadow="hover" class="panel mt-12">
          <template #header>
            <span class="panel-title">分析结论</span>
          </template>
          <div class="conclusion">
            <el-alert
              v-for="c in conclusions"
              :key="c.type"
              :title="c.title"
              :type="c.type"
              :description="c.desc"
              :closable="false"
              show-icon
              class="conclusion-item"
            />
          </div>
        </el-card>

        <el-card shadow="hover" class="panel mt-12">
          <template #header>
            <span class="panel-title">推荐调参方向</span>
          </template>
          <div class="recommendation">
            <div v-for="rec in recommendations" :key="rec.param" class="rec-item">
              <el-tag size="small" type="primary">{{ rec.param }}</el-tag>
              <span class="rec-desc">{{ rec.direction }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const selectedAlgorithm = ref('de_rrt_star')
const sensitivityChartRef = ref(null)
const correlationMatrixRef = ref(null)
let sensitivityChart = null
let correlationChart = null

const analysisParams = ref([
  { name: 'weatherWeight', label: '气象权重', min: 0, max: 100, enabled: true },
  { name: 'obstacleWeight', label: '避障权重', min: 0, max: 100, enabled: true },
  { name: 'energyWeight', label: '能耗权重', min: 0, max: 100, enabled: true },
  { name: 'maxAltitude', label: '最大高度', min: 100, max: 3000, enabled: true },
  { name: 'minGap', label: '最小间距', min: 1, max: 50, enabled: false },
  { name: 'cruiseSpeed', label: '巡航速度', min: 40, max: 120, enabled: false }
])

const analysisConfig = reactive({
  sampleCount: 20,
  targetMetric: 'risk',
  analysisType: 'one-way'
})

const sensitivityRank = ref([
  { param: 'weatherWeight', label: '气象权重', sensitivity: 0.854 },
  { param: 'obstacleWeight', label: '避障权重', sensitivity: 0.721 },
  { param: 'maxAltitude', label: '最大高度', sensitivity: 0.432 },
  { param: 'energyWeight', label: '能耗权重', sensitivity: 0.318 }
])

const maxSensitivity = computed(() => Math.max(...sensitivityRank.value.map(r => r.sensitivity)))

const conclusions = ref([
  { type: 'warning', title: '气象权重敏感性最高', desc: '气象权重对风险评分影响最为显著，建议优先优化' },
  { type: 'info', title: '避障权重次之', desc: '避障权重敏感性较高，可作为次要调参方向' }
])

const recommendations = ref([
  { param: '气象权重', direction: '建议降低5-10，可减少气象风险评分' },
  { param: '避障权重', direction: '建议提高10-15，增强路径安全性' }
])

function progressColor(idx) {
  return idx === 0 ? '#f56c6c' : idx === 1 ? '#e6a23c' : idx === 2 ? '#409eff' : '#67c23a'
}

function initSensitivityChart() {
  if (!sensitivityChartRef.value) return
  sensitivityChart = echarts.init(sensitivityChartRef.value)
  const enabledParams = analysisParams.value.filter(p => p.enabled)
  const data = enabledParams.map(p => {
    const rankItem = sensitivityRank.value.find(r => r.param === p.name)
    return {
      param: p.label,
      sensitivity: rankItem ? rankItem.sensitivity : 0,
      range: [p.min, p.max]
    }
  })
  sensitivityChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'value', name: '敏感度', max: 1 },
    yAxis: { type: 'category', data: data.map(d => d.param), axisLabel: { fontSize: 11 } },
    series: [{
      type: 'bar',
      data: data.map((d, idx) => ({
        value: d.sensitivity,
        itemStyle: { color: progressColor(idx) }
      })),
      label: { show: true, position: 'right', formatter: '{c}' }
    }]
  })
}

function initCorrelationChart() {
  if (!correlationMatrixRef.value) return
  correlationChart = echarts.init(correlationMatrixRef.value)
  const params = ['气象', '避障', '能耗', '高度', '间距']
  const matrix = [
    [1.00, 0.32, 0.15, 0.08, 0.05],
    [0.32, 1.00, 0.21, 0.12, 0.18],
    [0.15, 0.21, 1.00, 0.09, 0.06],
    [0.08, 0.12, 0.09, 1.00, 0.14],
    [0.05, 0.18, 0.06, 0.14, 1.00]
  ]
  correlationChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (p) => `${params[p.dataIndex]} vs ${params[p.seriesIndex]}: ${p.value.toFixed(2)}`
    },
    grid: { left: '2%', right: '10%', bottom: '2%', containLabel: true },
    xAxis: { type: 'category', data: params, axisLabel: { fontSize: 10, rotate: 30 } },
    yAxis: { type: 'category', data: params, axisLabel: { fontSize: 10 } },
    visualMap: { min: 0, max: 1, calculable: true, right: 0, top: 0 },
    series: [{
      type: 'heatmap',
      data: matrix.map((row, i) => row.map((val, j) => [j, i, val])),
      label: { show: true, fontSize: 9 },
      emphasis: { itemStyle: { shadowBlur: 10 } }
    }]
  })
}

function handleRunAnalysis() {
  ElMessage.success('开始运行敏感性分析...')
  setTimeout(() => {
    initSensitivityChart()
    initCorrelationChart()
    ElMessage.success('分析完成')
  }, 1000)
}

watch(selectedAlgorithm, () => {
  nextTick(() => {
    if (sensitivityChart) initSensitivityChart()
    if (correlationChart) initCorrelationChart()
  })
})

onMounted(() => {
  nextTick(() => {
    initSensitivityChart()
    initCorrelationChart()
  })
})

onBeforeUnmount(() => {
  if (sensitivityChart) {
    sensitivityChart.dispose()
    sensitivityChart = null
  }
  if (correlationChart) {
    correlationChart.dispose()
    correlationChart = null
  }
})
</script>

<style scoped>
.sensitivity-view {
  padding: 16px;
  background: #f5f7fa;
  min-height: 100%;
  font-size: 13px;
  color: #303133;
}
.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.header-actions {
  margin-left: auto;
  display: flex;
  gap: 10px;
}
.btn-icon {
  margin-right: 4px;
}
.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}
.main-row {
  align-items: stretch;
}
.panel {
  border-radius: 8px;
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.panel-title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}
.mt-12 {
  margin-top: 12px;
}
.param-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.param-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}
.param-item:hover {
  background: #f5f7fa;
}
.param-item.active {
  background: #ecf5ff;
}
.param-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.param-name {
  font-size: 13px;
  font-weight: 500;
}
.param-range {
  font-size: 11px;
  color: #909399;
}
.sensitivity-chart {
  height: 300px;
}
.correlation-matrix {
  height: 220px;
}
.rank-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.rank-item {
  display: flex;
  align-items: center;
  gap: 10px;
}
.rank-badge {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
}
.rank-1 { background: #f56c6c; }
.rank-2 { background: #e6a23c; }
.rank-3 { background: #409eff; }
.rank-4 { background: #67c23a; }
.rank-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.rank-param {
  font-size: 12px;
  font-weight: 500;
}
.rank-value {
  font-size: 11px;
  color: #909399;
}
.conclusion {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.conclusion-item {
  margin-bottom: 0;
}
.rec-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;
}
.rec-item:last-child {
  border-bottom: none;
}
.rec-desc {
  font-size: 12px;
  color: #606266;
}
</style>
