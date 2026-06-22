<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDateTime, formatNumber } from '@/utils/format'
import { algorithmApi } from '@/api/algorithm'
import type { Algorithm, AlgorithmCategoryStats, AlgorithmExecuteResult } from '@/api/algorithm'
import { useDemoModeStore } from '@/stores/demoMode'
import { generateMockAlgorithms } from '@/mock/algorithmData'
const demoModeStore = useDemoModeStore()

// 分类选项
const categoryOptions = [
  { label: '全部', value: '' },
  { label: '同化', value: 'assimilation' },
  { label: '规划', value: 'planning' },
  { label: '风险', value: 'risk' },
  { label: '观测', value: 'observation' },
  { label: '天气', value: 'weather' },
  { label: '融合', value: 'fusion' },
  { label: '通用', value: 'generic' },
]

// 分类标签颜色映射
const categoryColorMap: Record<string, string> = {
  assimilation: '#3498db',
  planning: '#2ecc71',
  model_engine: '#e94560',
  edge: '#f39c12',
  risk: '#e74c3c',
  observation: '#9b59b6',
  weather: '#1abc9c',
  fusion: '#e67e22',
  generic: '#95a5a6',
}

const categoryLabelMap: Record<string, string> = {
  assimilation: '同化',
  planning: '规划',
  model_engine: 'AI模型',
  edge: '边云',
  risk: '风险',
  observation: '观测',
  weather: '天气',
  fusion: '融合',
  generic: '通用',
}

// 列表状态
const loading = ref(false)
const algorithms = ref<Algorithm[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const selectedCategory = ref('')
const searchKeyword = ref('')

// 算法类型筛选（系列）
const selectedType = ref('')
const typeOptions = [
  { label: '全部类型', value: '' },
  { label: '3D-VAR 系列', value: '3dvar' },
  { label: '4D-VAR 系列', value: '4dvar' },
  { label: '5D-VAR 系列', value: '5dvar' },
  { label: 'MPC 规划', value: 'mpc' },
  { label: '风险适航', value: 'risk_assessment' },
  { label: '主动观测', value: 'active_observation' },
  { label: '边缘推理', value: 'edge_inference' },
  { label: '气象模型', value: 'weather_model' },
  { label: '数据融合', value: 'data_fusion' },
]

// 算法等级筛选
const selectedLevel = ref('')
const levelOptions = [
  { label: '全部等级', value: '' },
  { label: '标准版', value: 'standard' },
  { label: '增强版', value: 'enhanced' },
  { label: '轻量化版', value: 'lightweight' },
  { label: '高精度版', value: 'high_precision' },
]

// 分类统计
const categoryStats = ref<AlgorithmCategoryStats>({
  total: 0,
  assimilation: 0,
  planning: 0,
  model_engine: 0,
  edge: 0,
  risk: 0,
  observation: 0,
  weather: 0,
  fusion: 0,
  generic: 0,
})



function generateMockStats(): AlgorithmCategoryStats {
  const all = generateMockAlgorithms()
  const stats: AlgorithmCategoryStats = { total: all.length, assimilation: 0, planning: 0, model_engine: 0, edge: 0, risk: 0, observation: 0, weather: 0, fusion: 0, generic: 0 }
  for (const a of all) {
    const t = a.type ?? a.category
    if (t && t in stats) { const v = (stats as Record<string, number>)[t]; if (v !== undefined) (stats as Record<string, number>)[t] = v + 1 }
  }
  return stats
}

// 测试运行对话框
const testDialogVisible = ref(false)
const testForm = ref({
  algorithmId: 0,
  algorithmName: '',
  params: '',
})
const testLoading = ref(false)
const testResult = ref<AlgorithmExecuteResult | null>(null)

// 算法详情弹窗
const detailDialogVisible = ref(false)
const detailAlgorithm = ref<Algorithm | null>(null)

function showAlgoDetail(row: Algorithm) {
  detailAlgorithm.value = row
  detailDialogVisible.value = true
}

// 状态切换 loading map
const statusLoadingMap = ref<Record<number, boolean>>({})

// 统计卡片数据
const statsCards = computed(() => [
  { title: '全部算法', value: categoryStats.value.total, color: '#e94560', icon: 'Cpu' },
  { title: '同化', value: categoryStats.value.assimilation ?? 0, color: '#3498db', icon: 'Connection' },
  { title: '规划', value: categoryStats.value.planning ?? 0, color: '#2ecc71', icon: 'Guide' },
  { title: '风险', value: categoryStats.value.risk ?? 0, color: '#e74c3c', icon: 'Warning' },
  { title: '观测', value: categoryStats.value.observation ?? 0, color: '#9b59b6', icon: 'View' },
  { title: '天气', value: categoryStats.value.weather ?? 0, color: '#1abc9c', icon: 'Cloudy' },
  { title: '融合', value: categoryStats.value.fusion ?? 0, color: '#e67e22', icon: 'Share' },
])

async function loadAlgorithms() {
  loading.value = true
  try {
    if (demoModeStore.isDemoMode) {
      const all = generateMockAlgorithms()
      // 应用筛选
      let filtered = all
      if (selectedCategory.value) {
        filtered = filtered.filter(a => a.type === selectedCategory.value || a.category === selectedCategory.value)
      }
      if (searchKeyword.value) {
        const kw = searchKeyword.value.toLowerCase()
        filtered = filtered.filter(a => a.name.toLowerCase().includes(kw) || (a.description ?? '').toLowerCase().includes(kw))
      }
      total.value = filtered.length
      const start = (currentPage.value - 1) * pageSize.value
      algorithms.value = filtered.slice(start, start + pageSize.value)
      return
    }
    const data = await algorithmApi.list({
      category: selectedCategory.value || undefined,
      keyword: searchKeyword.value || undefined,
      algorithmType: selectedType.value || undefined,
      algorithmLevel: selectedLevel.value || undefined,
      page: currentPage.value,
      size: pageSize.value,
    })
    if (Array.isArray(data)) {
      algorithms.value = data as Algorithm[]
      total.value = data.length
    } else if (data && typeof data === 'object') {
      algorithms.value = (data as { records?: Algorithm[] }).records ?? []
      total.value = (data as { total?: number }).total ?? algorithms.value.length
    }
  } catch (error) {
    console.error('Failed to load algorithms:', error)
  } finally {
    loading.value = false
  }
}

async function loadCategoryStats() {
  if (demoModeStore.isDemoMode) {
    categoryStats.value = generateMockStats()
    return
  }
  try {
    const data = await algorithmApi.getRegistryStats()
    if (data && typeof data === 'object') {
      categoryStats.value = data
    }
  } catch {
    // 静默处理，使用默认值
  }
}

function handleCategoryChange() {
  currentPage.value = 1
  loadAlgorithms()
}

function handleTypeChange() {
  currentPage.value = 1
  loadAlgorithms()
}

function handleLevelChange() {
  currentPage.value = 1
  loadAlgorithms()
}

function handleResetFilter() {
  selectedCategory.value = ''
  selectedType.value = ''
  selectedLevel.value = ''
  searchKeyword.value = ''
  currentPage.value = 1
  loadAlgorithms()
  loadCategoryStats()
}

function handleSearch() {
  currentPage.value = 1
  loadAlgorithms()
}

function handlePageChange(page: number) {
  currentPage.value = page
  loadAlgorithms()
}

function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  loadAlgorithms()
}

function handleTest(row: Algorithm) {
  testForm.value = {
    algorithmId: row.id,
    algorithmName: row.name,
    params: '',
  }
  testResult.value = null
  testDialogVisible.value = true
}

async function runTest() {
  testLoading.value = true
  testResult.value = null
  try {
    if (demoModeStore.isDemoMode) {
      // 演示模式：模拟测试运行
      await new Promise(r => setTimeout(r, 1500))
      testResult.value = {
        success: true,
        executionTime: `${(Math.random() * 3 + 0.5).toFixed(2)}s`,
        output: { result: '模拟运行成功', metrics: { rmse: (Math.random() * 0.3 + 0.05).toFixed(4) } },
        error: '',
      }
      ElMessage.success('测试运行完成（演示模式）')
      return
    }
    let params: Record<string, unknown> | undefined
    if (testForm.value.params.trim()) {
      params = JSON.parse(testForm.value.params)
    }
    const result = await algorithmApi.testAlgorithm(testForm.value.algorithmId, params)
    testResult.value = result
    if (result.success) {
      ElMessage.success('测试运行完成')
    } else {
      ElMessage.warning('测试运行返回失败')
    }
  } catch {
    testResult.value = {
      success: false,
      executionTime: '-',
      output: {},
      error: '请求失败，请检查算法服务是否可用',
    }
  } finally {
    testLoading.value = false
  }
}

function isAlgorithmEnabled(row: Algorithm): boolean {
  return row.status === 1 || row.status === 'ACTIVE' || row.status === 'ENABLED'
}

async function handleToggleStatus(row: Algorithm) {
  const enabled = isAlgorithmEnabled(row)
  const action = enabled ? '禁用' : '启用'

  try {
    await ElMessageBox.confirm(
      `确定要${action}算法 "${row.name}" 吗？`,
      `${action}确认`,
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return // 用户取消
  }

  statusLoadingMap.value[row.id] = true
  try {
    await algorithmApi.toggleStatus(row.id, !enabled)
    ElMessage.success(`算法已${action}`)
    // 刷新列表和统计
    await Promise.all([loadAlgorithms(), loadCategoryStats()])
  } catch {
    // 错误已在拦截器中处理
  } finally {
    statusLoadingMap.value[row.id] = false
  }
}


onMounted(async () => {
  await demoModeStore.fetchStatus()
  loadAlgorithms()
  loadCategoryStats()
})

watch(() => demoModeStore.isDemoMode, () => {
  loadAlgorithms()
  loadCategoryStats()
})
</script>

<template>
  <div class="algorithm-page">
    <div class="page-header">
      <h2>算法管理</h2>
    </div>

    <!-- 分类统计卡片 -->
    <div class="stats-row">
      <div
        v-for="card in statsCards"
        :key="card.title"
        class="stat-card"
      >
        <div class="stat-info">
          <div class="stat-title">{{ card.title }}</div>
          <div class="stat-value" :style="{ color: card.color }">
            {{ formatNumber(card.value) }}
          </div>
        </div>
        <div class="stat-icon" :style="{ backgroundColor: card.color + '20' }">
          <el-icon :size="22" :color="card.color">
            <component :is="card.icon" />
          </el-icon>
        </div>
      </div>
    </div>

    <!-- 筛选和搜索 -->
    <el-card class="filter-card">
      <div class="filter-row">
        <div class="filter-left">
          <!-- 算法分类下拉 -->
          <el-select v-model="selectedCategory" placeholder="分类筛选" style="width: 130px" @change="handleCategoryChange">
            <el-option v-for="opt in categoryOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
          <!-- 算法类型下拉 -->
          <el-select v-model="selectedType" placeholder="算法类型" style="width: 140px; margin-left: 10px" @change="handleTypeChange">
            <el-option v-for="opt in typeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
          <!-- 算法等级下拉 -->
          <el-select v-model="selectedLevel" placeholder="算法等级" style="width: 130px; margin-left: 10px" @change="handleLevelChange">
            <el-option v-for="opt in levelOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
          <!-- 搜索框 -->
          <el-input v-model="searchKeyword" placeholder="搜索算法名称" clearable style="width: 200px; margin-left: 10px" @keyup.enter="handleSearch" @clear="handleSearch">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <!-- 查询按钮 -->
          <el-button type="primary" style="margin-left: 10px" @click="handleSearch">查询</el-button>
          <!-- 重置按钮 -->
          <el-button style="margin-left: 6px" @click="handleResetFilter">重置筛选</el-button>
        </div>
        <div class="filter-right">
          <span class="total-text">共 {{ formatNumber(total) }} 个算法</span>
        </div>
      </div>
    </el-card>

    <!-- 算法列表 -->
    <el-card class="table-card">
      <el-table v-loading="loading" :data="algorithms" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="算法名称" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="algo-name-link" @click="showAlgoDetail(row)">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="分类" width="100">
          <template #default="{ row }">
            <el-tag
              size="small"
              effect="plain"
              :color="categoryColorMap[row.type] || categoryColorMap[row.category] || '#6c6c80'"
              style="color: #fff; border: none"
            >
              {{ categoryLabelMap[row.type] || categoryLabelMap[row.category] || row.type || row.category }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <div class="status-cell">
              <el-switch
                :model-value="isAlgorithmEnabled(row)"
                :loading="statusLoadingMap[row.id]"
                inline-prompt
                active-text="启用"
                inactive-text="禁用"
                size="small"
                @change="handleToggleStatus(row)"
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="runCount" label="运行次数" width="100">
          <template #default="{ row }">
            {{ formatNumber(row.runCount) }}
          </template>
        </el-table-column>
        <el-table-column prop="lastRunAt" label="最近运行" width="170">
          <template #default="{ row }">
            {{ row.lastRunAt ? formatDateTime(row.lastRunAt) : '从未运行' }}
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click="handleTest(row)"
            >
              测试运行
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!loading && algorithms.length === 0" description="当前条件下无匹配算法，请更换筛选条件" />

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <!-- 算法详情弹窗 -->
    <el-dialog v-model="detailDialogVisible" :title="detailAlgorithm?.name ?? '算法详情'" width="560px">
      <div v-if="detailAlgorithm" class="algo-detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="算法名称">{{ detailAlgorithm.name }}</el-descriptions-item>
          <el-descriptions-item label="版本">{{ detailAlgorithm.version }}</el-descriptions-item>
          <el-descriptions-item label="分类">
            <el-tag size="small" effect="plain" :color="categoryColorMap[detailAlgorithm.type] || categoryColorMap[detailAlgorithm.category] || '#6c6c80'" style="color: #fff; border: none;">
              {{ categoryLabelMap[detailAlgorithm.type] || categoryLabelMap[detailAlgorithm.category] || detailAlgorithm.type }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="运行次数">{{ formatNumber(detailAlgorithm.runCount) }}</el-descriptions-item>
          <el-descriptions-item label="最近运行">{{ detailAlgorithm.lastRunAt ? formatDateTime(detailAlgorithm.lastRunAt) : '从未运行' }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ formatDateTime(detailAlgorithm.registeredAt || detailAlgorithm.createdAt) }}</el-descriptions-item>
        </el-descriptions>
        <div class="algo-detail-desc">
          <div class="param-label">算法介绍</div>
          <p>{{ detailAlgorithm.description }}</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="detailDialogVisible = false; handleTest(detailAlgorithm!)">测试运行</el-button>
      </template>
    </el-dialog>

    <!-- 测试运行对话框 -->
    <el-dialog v-model="testDialogVisible" title="算法测试运行" width="640px">
      <div class="test-info">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="算法">{{ testForm.algorithmName }}</el-descriptions-item>
          <el-descriptions-item label="ID">{{ testForm.algorithmId }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <div class="mt-16">
        <label class="param-label">输入参数 (JSON)</label>
        <el-input
          v-model="testForm.params"
          type="textarea"
          :rows="6"
          placeholder='输入测试参数，如: {"start": [116.4, 39.9], "end": [117.0, 40.0]}'
        />
      </div>
      <div v-if="testResult" class="mt-16">
        <label class="param-label">
          运行结果
          <el-tag
            v-if="testResult"
            :type="testResult.success ? 'success' : 'danger'"
            size="small"
            style="margin-left: 8px"
          >
            {{ testResult.success ? '成功' : '失败' }}
          </el-tag>
          <span v-if="testResult?.executionTime" class="exec-time">
            耗时: {{ testResult.executionTime }}
          </span>
        </label>
        <pre class="result-output">{{ JSON.stringify(testResult, null, 2) }}</pre>
      </div>
      <template #footer>
        <el-button @click="testDialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="testLoading" @click="runTest">
          {{ testLoading ? '运行中...' : '运行测试' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.algorithm-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* 统计卡片 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
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

/* 筛选栏 */
.filter-card {
  border-radius: 8px;
}

.filter-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.filter-left {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0;
}

.filter-right {
  display: flex;
  align-items: center;
}

.total-text {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* 表格 */
.table-card {
  border-radius: 8px;
}

.status-cell {
  display: flex;
  align-items: center;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
}

/* 对话框 */
.param-label {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.exec-time {
  margin-left: 8px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

/* 算法名称链接 */
.algo-name-link {
  color: var(--el-color-primary);
  cursor: pointer;
  transition: color 0.2s;
}
.algo-name-link:hover {
  color: var(--el-color-primary-light-3);
  text-decoration: underline;
}

/* 算法详情弹窗 */
.algo-detail-desc {
  margin-top: 16px;
}
.algo-detail-desc p {
  color: var(--color-text-primary);
  font-size: 14px;
  line-height: 1.8;
  margin: 0;
}

.result-output {
  padding: 12px;
  background-color: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 12px;
  color: var(--color-text-primary);
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

@media (max-width: 1400px) {
  .stats-row {
    grid-template-columns: repeat(4, 1fr);
  }
}

@media (max-width: 900px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
