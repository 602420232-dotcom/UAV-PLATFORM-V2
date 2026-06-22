<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { dashboardApi, type GlobalStats } from '@/api/dashboard'
import { useDemoModeStore } from '@/stores/demoMode'
import { formatNumber } from '@/utils/format'

const router = useRouter()
const demoModeStore = useDemoModeStore()

// ========== KPI 数据 ==========
const globalStats = ref<GlobalStats>({
  totalTenants: 0,
  activeApiKeys: 0,
  todayApiCalls: 0,
  runningExperiments: 0,
})

// ========== API 运营摘要 ==========
const apiOpsStats = ref({
  activeServices: 0,
  todayFailedRequests: 0,
  peakCalls7d: 0,
})

// ========== 科研摘要 ==========
const researchStats = ref({
  running: 0,
  completed: 0,
  fiveDVarExecutions: 0,
})

// ========== 服务健康 ==========
const healthyServices = ref(0)
const totalServices = ref(6)

// ========== Mock 数据 ==========
const mockGlobalStats: GlobalStats = {
  totalTenants: 5,
  activeApiKeys: 23,
  todayApiCalls: 15832,
  runningExperiments: 7,
}

const mockApiOpsStats = {
  activeServices: 6,
  todayFailedRequests: 12,
  peakCalls7d: 23456,
}

const mockResearchStats = {
  running: 3,
  completed: 42,
  fiveDVarExecutions: 18,
}

// ========== 加载数据 ==========
async function loadDashboard() {
  if (demoModeStore.isDemoMode) {
    // 演示模式：直接加载完整 mock 数据，不调用后端 API
    globalStats.value = mockGlobalStats
    apiOpsStats.value = mockApiOpsStats
    researchStats.value = mockResearchStats
    healthyServices.value = mockApiOpsStats.activeServices
    totalServices.value = 6
    return
  }

  // 生产模式：正常调用后端 API
  try {
    const [globalResult, apiOpsResult, researchResult] = await Promise.allSettled([
      dashboardApi.getGlobalStats(),
      dashboardApi.getApiOpsDashboard(),
      dashboardApi.getResearchDashboard(),
    ])

    if (globalResult.status === 'fulfilled') {
      globalStats.value = globalResult.value
    }
    if (apiOpsResult.status === 'fulfilled') {
      apiOpsStats.value = {
        activeServices: apiOpsResult.value.stats.activeServices,
        todayFailedRequests: apiOpsResult.value.stats.todayFailedRequests,
        peakCalls7d: apiOpsResult.value.stats.peakCalls7d,
      }
      // 统计健康服务数
      const healthList = apiOpsResult.value.serviceHealth || []
      totalServices.value = healthList.length || 6
      healthyServices.value = healthList.filter((s) => s.status === 'UP').length
    }
    if (researchResult.status === 'fulfilled') {
      researchStats.value = {
        running: researchResult.value.stats.running,
        completed: researchResult.value.stats.completed,
        fiveDVarExecutions: researchResult.value.stats.fiveDVarExecutions,
      }
    }
  } catch {
    // 静默处理，使用默认值
  }
}

// ========== 跳转 ==========
function goToApiOps() {
  router.push('/api-ops/dashboard')
}

function goToResearch() {
  router.push('/research/sandbox')
}

// ========== 监听演示模式切换 ==========
watch(() => demoModeStore.isDemoMode, () => {
  loadDashboard()
})

onMounted(async () => {
  await demoModeStore.fetchStatus()
  loadDashboard()
})
</script>

<template>
  <div class="dashboard-page">
    <!-- ==================== 顶部：4 个极简 KPI 卡片 ==================== -->
    <el-row :gutter="16" class="kpi-row">
      <el-col :span="6">
        <div class="kpi-card kpi-blue">
          <el-icon :size="28" class="kpi-icon"><Document /></el-icon>
          <div class="kpi-content">
            <div class="kpi-value">{{ formatNumber(globalStats.totalTenants) }}</div>
            <div class="kpi-label">总租户数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="kpi-card kpi-green">
          <el-icon :size="28" class="kpi-icon"><Key /></el-icon>
          <div class="kpi-content">
            <div class="kpi-value">{{ formatNumber(globalStats.activeApiKeys) }}</div>
            <div class="kpi-label">有效 API Key</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="kpi-card kpi-pink">
          <el-icon :size="28" class="kpi-icon"><TrendCharts /></el-icon>
          <div class="kpi-content">
            <div class="kpi-value">{{ formatNumber(globalStats.todayApiCalls) }}</div>
            <div class="kpi-label">今日总调用量</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="kpi-card kpi-orange">
          <el-icon :size="28" class="kpi-icon"><VideoPlay /></el-icon>
          <div class="kpi-content">
            <div class="kpi-value">{{ formatNumber(globalStats.runningExperiments) }}</div>
            <div class="kpi-label">运行中实验</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- ==================== 主体：两大入口卡片 ==================== -->
    <el-row :gutter="16" class="entry-row">
      <!-- 左侧：API 运营入口 -->
      <el-col :span="12">
        <div class="entry-card entry-api-ops">
          <div class="entry-title">
            <el-icon :size="20" color="#3498db"><Monitor /></el-icon>
            <span>API 运营控制台</span>
          </div>
          <div class="entry-tags">
            <el-tag size="small" effect="plain" type="info">
              活跃服务：{{ apiOpsStats.activeServices }} 个
            </el-tag>
            <el-tag size="small" effect="plain" type="info">
              今日失败请求：{{ formatNumber(apiOpsStats.todayFailedRequests) }}
            </el-tag>
            <el-tag size="small" effect="plain" type="info">
              7 日峰值调用：{{ formatNumber(apiOpsStats.peakCalls7d) }}
            </el-tag>
          </div>
          <div class="entry-action">
            <el-button type="primary" size="large" @click="goToApiOps">
              进入完整 API 运营控制台
            </el-button>
          </div>
        </div>
      </el-col>

      <!-- 右侧：科研算法平台入口 -->
      <el-col :span="12">
        <div class="entry-card entry-research">
          <div class="entry-title">
            <el-icon :size="20" color="#2ecc71"><SetUp /></el-icon>
            <span>科研算法平台</span>
          </div>
          <div class="entry-tags">
            <el-tag size="small" effect="plain" type="info">
              正在运行实验：{{ researchStats.running }}
            </el-tag>
            <el-tag size="small" effect="plain" type="info">
              已完成实验：{{ researchStats.completed }}
            </el-tag>
            <el-tag size="small" effect="plain" type="info">
              5D-VAR 执行次数：{{ researchStats.fiveDVarExecutions }}
            </el-tag>
          </div>
          <div class="entry-action">
            <el-button type="success" size="large" @click="goToResearch">
              进入完整科研平台
            </el-button>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- ==================== 底部：全平台简易状态条 ==================== -->
    <div class="status-bar">
      <span class="status-text">
        服务健康 {{ healthyServices }}/{{ totalServices }} 个在线
        <span class="status-divider">|</span>
        无告警
      </span>
    </div>
  </div>
</template>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 24px;
}

/* ========== KPI 卡片 ========== */
.kpi-row {
  margin-bottom: 0;
}

.kpi-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  border-radius: 10px;
  background: #1a1a2e;
  border: 1px solid #2a2a40;
  height: 80px;
  box-sizing: border-box;
}

.kpi-icon {
  flex-shrink: 0;
}

.kpi-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.kpi-value {
  font-size: 22px;
  font-weight: 700;
  color: #e0e0e0;
  line-height: 1.2;
}

.kpi-label {
  font-size: 12px;
  color: #a0a0b0;
}

.kpi-blue .kpi-icon {
  color: #3498db;
}

.kpi-green .kpi-icon {
  color: #2ecc71;
}

.kpi-pink .kpi-icon {
  color: #e94560;
}

.kpi-orange .kpi-icon {
  color: #f39c12;
}

/* ========== 入口卡片 ========== */
.entry-row {
  margin-bottom: 0;
}

.entry-card {
  position: relative;
  border-radius: 12px;
  padding: 24px;
  height: 280px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  border: 1px solid #2a2a40;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  overflow: hidden;
}

.entry-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.entry-api-ops {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

.entry-research {
  background: linear-gradient(135deg, #1a1a2e 0%, #0d2137 100%);
}

.entry-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #e0e0e0;
  margin-bottom: 20px;
}

.entry-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.entry-tags :deep(.el-tag) {
  background-color: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.1);
  color: #a0a0b0;
}

.entry-action {
  position: absolute;
  bottom: 24px;
  right: 24px;
}

/* ========== 底部状态条 ========== */
.status-bar {
  text-align: center;
  padding: 12px 0;
}

.status-text {
  font-size: 13px;
  color: #6a6a80;
}

.status-divider {
  margin: 0 12px;
  color: #3a3a50;
}

/* ========== 响应式 ========== */
@media (max-width: 1200px) {
  .entry-row .el-col {
    max-width: 100% !important;
    flex: 0 0 100% !important;
  }
}

@media (max-width: 768px) {
  .kpi-row .el-col {
    max-width: 50% !important;
    flex: 0 0 50% !important;
  }
  .entry-card {
    height: auto;
    min-height: 200px;
  }
  .entry-action {
    position: static;
    margin-top: 16px;
  }
}
</style>
