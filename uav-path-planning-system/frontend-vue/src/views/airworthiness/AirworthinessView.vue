<template>
  <div class="airworthiness-view">
    <div class="page-header">
      <h2 class="page-title">适航性评估全流程</h2>
      <el-steps :active="currentStep" finish-status="success" size="small" class="steps-bar">
        <el-step title="选择方案" />
        <el-step title="气象核验" />
        <el-step title="适航检查" />
        <el-step title="风险评估" />
        <el-step title="生成报告" />
      </el-steps>
    </div>

    <!-- Step 0: 选择方案 -->
    <div v-if="currentStep === 0" class="step-content">
      <el-card shadow="hover" class="panel">
        <template #header>
          <span class="panel-title">选择评估方案</span>
        </template>
        <el-row :gutter="16">
          <el-col :span="8" v-for="plan in plans" :key="plan.id">
            <div
              class="plan-card"
              :class="{ active: selectedPlan?.id === plan.id }"
              @click="selectedPlan = plan"
            >
              <div class="plan-header">
                <span class="plan-name">{{ plan.name }}</span>
                <el-tag size="small" :type="plan.level === 'A' ? 'success' : plan.level === 'B' ? 'warning' : 'info'">
                  {{ plan.level }}级
                </el-tag>
              </div>
              <div class="plan-desc">{{ plan.description }}</div>
              <div class="plan-metrics">
                <div class="metric-item">
                  <span class="metric-label">最大航程</span>
                  <span class="metric-val">{{ plan.maxRange }} km</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">最大高度</span>
                  <span class="metric-val">{{ plan.maxAltitude }} m</span>
                </div>
                <div class="metric-item">
                  <span class="metric-label">最大载重</span>
                  <span class="metric-val">{{ plan.maxPayload }} kg</span>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
        <div class="step-actions">
          <el-button type="primary" :disabled="!selectedPlan" @click="currentStep = 1">
            下一步：气象核验
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- Step 1: 气象核验 -->
    <div v-if="currentStep === 1" class="step-content">
      <el-card shadow="hover" class="panel">
        <template #header>
          <span class="panel-title">气象条件核验</span>
        </template>
        <div class="weather-check">
          <div class="check-row" v-for="item in weatherChecks" :key="item.label">
            <span class="check-label">{{ item.label }}</span>
            <el-progress
              :percentage="item.value"
              :stroke-width="12"
              :color="item.color"
              style="width: 200px"
            />
            <el-tag size="small" :type="item.passed ? 'success' : 'danger'">
              {{ item.passed ? '通过' : '不通过' }}
            </el-tag>
          </div>
        </div>
        <div class="weather-summary">
          <el-alert
            :title="weatherPassed ? '气象条件满足飞行要求' : '气象条件不满足飞行要求'"
            :type="weatherPassed ? 'success' : 'error'"
            :closable="false"
          />
        </div>
        <div class="step-actions">
          <el-button @click="currentStep = 0">上一步</el-button>
          <el-button type="primary" :disabled="!weatherPassed" @click="currentStep = 2">
            下一步：适航检查
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- Step 2: 适航检查 -->
    <div v-if="currentStep === 2" class="step-content">
      <el-card shadow="hover" class="panel">
        <template #header>
          <span class="panel-title">飞行器适航检查</span>
        </template>
        <el-table :data="aircraftChecks" stripe size="small">
          <el-table-column prop="item" label="检查项目" width="200" />
          <el-table-column prop="standard" label="检查标准" />
          <el-table-column prop="result" label="检查结果" width="120" align="center">
            <template #default="{ row }">
              <el-select v-model="row.result" size="small" style="width: 90px">
                <el-option value="通过" label="通过" />
                <el-option value="不通过" label="不通过" />
                <el-option value="待定" label="待定" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" width="150" />
        </el-table>
        <div class="step-actions">
          <el-button @click="currentStep = 1">上一步</el-button>
          <el-button type="primary" @click="currentStep = 3">
            下一步：风险评估
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- Step 3: 风险评估 -->
    <div v-if="currentStep === 3" class="step-content">
      <el-card shadow="hover" class="panel">
        <template #header>
          <span class="panel-title">综合风险评估</span>
        </template>
        <div class="risk-chart" ref="riskChartRef" />
        <div class="risk-summary">
          <el-row :gutter="16">
            <el-col :span="6" v-for="r in riskItems" :key="r.label">
              <div class="risk-card" :style="{ borderLeftColor: r.color }">
                <div class="risk-val" :style="{ color: r.color }">{{ r.value }}</div>
                <div class="risk-label">{{ r.label }}</div>
              </div>
            </el-col>
          </el-row>
        </div>
        <div class="step-actions">
          <el-button @click="currentStep = 2">上一步</el-button>
          <el-button type="primary" @click="currentStep = 4">
            下一步：生成报告
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- Step 4: 生成报告 -->
    <div v-if="currentStep === 4" class="step-content">
      <el-card shadow="hover" class="panel">
        <template #header>
          <span class="panel-title">适航性评估报告</span>
        </template>
        <div class="report-preview">
          <div class="report-header-section">
            <h3>无人机适航性评估报告</h3>
            <div class="report-meta">
              <span>方案：{{ selectedPlan?.name || '-' }}</span>
              <span>评估时间：{{ new Date().toLocaleString() }}</span>
              <span>评估结果：<el-tag :type="finalPassed ? 'success' : 'danger'" size="small">{{ finalPassed ? '通过' : '不通过' }}</el-tag></span>
            </div>
          </div>
          <div class="report-section">
            <h4>1. 气象核验结论</h4>
            <p>{{ weatherPassed ? '气象条件满足飞行要求，所有指标均达标。' : '气象条件不满足飞行要求，建议推迟任务。' }}</p>
          </div>
          <div class="report-section">
            <h4>2. 适航检查结论</h4>
            <p>共 {{ aircraftChecks.length }} 项检查，{{ passedChecks }} 项通过，{{ failedChecks }} 项不通过。</p>
          </div>
          <div class="report-section">
            <h4>3. 风险评估结论</h4>
            <p>综合风险评分：<strong>{{ overallRiskScore }}</strong>（满分100），风险等级：<strong>{{ riskLevel }}</strong>。</p>
          </div>
        </div>
        <div class="step-actions">
          <el-button @click="currentStep = 3">上一步</el-button>
          <el-button type="primary" @click="handleDownloadReport">
            下载报告
          </el-button>
          <el-button type="success" @click="handleApprove">
            确认放飞
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const currentStep = ref(0)
const selectedPlan = ref(null)
const riskChartRef = ref(null)
let riskChart = null

const plans = [
  { id: 1, name: '短途巡检方案', level: 'A', description: '适用于半径50km以内的短距离巡检任务', maxRange: 50, maxAltitude: 300, maxPayload: 5 },
  { id: 2, name: '中途运输方案', level: 'B', description: '适用于50-200km的中距离运输任务', maxRange: 200, maxAltitude: 500, maxPayload: 15 },
  { id: 3, name: '长途巡航方案', level: 'C', description: '适用于200km以上的长距离巡航任务', maxRange: 500, maxAltitude: 1000, maxPayload: 25 }
]

const weatherChecks = ref([
  { label: '风速 (≤8m/s)', value: 65, color: '#67c23a', passed: true },
  { label: '能见度 (≥5km)', value: 85, color: '#67c23a', passed: true },
  { label: '云量 (<80%)', value: 45, color: '#e6a23c', passed: true },
  { label: '降水概率 (<30%)', value: 20, color: '#67c23a', passed: true }
])

const weatherPassed = computed(() => weatherChecks.value.every(c => c.passed))

const aircraftChecks = ref([
  { item: '电池电量', standard: '≥80%', result: '通过' },
  { item: '螺旋桨状态', standard: '无裂纹、变形', result: '通过' },
  { item: '电机温度', standard: '≤65°C', result: '通过' },
  { item: 'GPS信号', standard: '≥8颗星', result: '通过' },
  { item: '遥控信号', standard: '信号强度≥70%', result: '通过' },
  { item: '摄像头校准', standard: '水平误差≤1°', result: '待定' }
])

const passedChecks = computed(() => aircraftChecks.value.filter(c => c.result === '通过').length)
const failedChecks = computed(() => aircraftChecks.value.filter(c => c.result === '不通过').length)

const riskItems = ref([
  { label: '气象风险', value: '低', color: '#67c23a' },
  { label: '机械风险', value: '中', color: '#e6a23c' },
  { label: '信号风险', value: '低', color: '#67c23a' },
  { label: '整体风险', value: '可控', color: '#409eff' }
])

const overallRiskScore = computed(() => 42)
const riskLevel = computed(() => overallRiskScore.value < 30 ? '低风险' : overallRiskScore.value < 60 ? '中风险' : '高风险')
const finalPassed = computed(() => weatherPassed.value && failedChecks.value === 0 && overallRiskScore.value < 60)

function initRiskChart() {
  if (!riskChartRef.value) return
  riskChart = echarts.init(riskChartRef.value)
  riskChart.setOption({
    radar: {
      indicator: [
        { name: '气象', max: 100 },
        { name: '机械', max: 100 },
        { name: '信号', max: 100 },
        { name: '地形', max: 100 },
        { name: '空域', max: 100 }
      ],
      radius: '65%'
    },
    series: [{
      type: 'radar',
      data: [{
        value: [35, 55, 30, 45, 40],
        name: '风险分布',
        areaStyle: { color: 'rgba(64, 158, 255, 0.25)' },
        lineStyle: { color: '#409eff', width: 2 }
      }]
    }]
  })
}

function handleDownloadReport() {
  ElMessage.success('报告已生成并触发下载')
}

function handleApprove() {
  if (!finalPassed.value) {
    ElMessage.error('评估未通过，无法放飞')
    return
  }
  ElMessage.success('已确认放飞，任务可执行')
}

onMounted(() => {
  nextTick(() => {
    if (currentStep.value === 3) {
      initRiskChart()
    }
  })
})
</script>

<style scoped>
.airworthiness-view {
  padding: 16px;
  background: #f5f7fa;
  min-height: 100%;
  font-size: 13px;
  color: #303133;
}
.page-header {
  margin-bottom: 16px;
}
.steps-bar {
  margin-top: 12px;
}
.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}
.step-content {
  max-width: 1000px;
}
.panel {
  border-radius: 8px;
}
.panel-title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}
.plan-card {
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 12px;
}
.plan-card:hover {
  border-color: #409eff;
}
.plan-card.active {
  border-color: #409eff;
  background: #ecf5ff;
}
.plan-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.plan-name {
  font-weight: 600;
  font-size: 14px;
}
.plan-desc {
  font-size: 12px;
  color: #606266;
  margin-bottom: 12px;
}
.plan-metrics {
  display: flex;
  gap: 12px;
}
.metric-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.metric-label {
  font-size: 11px;
  color: #909399;
}
.metric-val {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}
.step-actions {
  margin-top: 20px;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}
.weather-check {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.check-row {
  display: flex;
  align-items: center;
  gap: 16px;
}
.check-label {
  width: 140px;
  font-size: 13px;
  color: #606266;
}
.weather-summary {
  margin-top: 20px;
}
.risk-chart {
  height: 280px;
  margin-bottom: 20px;
}
.risk-summary {
  margin-top: 10px;
}
.risk-card {
  background: #f5f7fa;
  border-radius: 6px;
  padding: 16px;
  border-left: 4px solid;
}
.risk-val {
  font-size: 20px;
  font-weight: 700;
}
.risk-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
.report-preview {
  background: #fafafa;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 24px;
}
.report-header-section h3 {
  text-align: center;
  margin: 0 0 16px 0;
  color: #303133;
}
.report-meta {
  display: flex;
  gap: 20px;
  justify-content: center;
  font-size: 12px;
  color: #606266;
}
.report-section {
  margin-top: 20px;
}
.report-section h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #303133;
}
.report-section p {
  margin: 0;
  font-size: 13px;
  color: #606266;
}
</style>
