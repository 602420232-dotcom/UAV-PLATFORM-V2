<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatDateTime, formatNumber } from '@/utils/format'
import { algorithmApi } from '@/api/algorithm'
import type { Algorithm, AlgorithmCategoryStats } from '@/api/algorithm'

// 分类选项
const categoryOptions = [
  { label: '全部', value: '' },
  { label: '同化', value: 'assimilation' },
  { label: '规划', value: 'planning' },
  { label: 'AI模型', value: 'model_engine' },
  { label: '边云', value: 'edge' },
  { label: '风险', value: 'risk' },
  { label: '观测', value: 'observation' },
]

// 分类标签颜色映射
const categoryColorMap: Record<string, string> = {
  assimilation: '#3498db',
  planning: '#2ecc71',
  model_engine: '#e94560',
  edge: '#f39c12',
  risk: '#e74c3c',
  observation: '#9b59b6',
}

const categoryLabelMap: Record<string, string> = {
  assimilation: '同化',
  planning: '规划',
  model_engine: 'AI模型',
  edge: '边云',
  risk: '风险',
  observation: '观测',
}

// 列表状态
const loading = ref(false)
const algorithms = ref<Algorithm[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const selectedCategory = ref('')
const searchKeyword = ref('')

// 分类统计
const categoryStats = ref<AlgorithmCategoryStats>({
  total: 0,
  assimilation: 0,
  planning: 0,
  model_engine: 0,
  edge: 0,
  risk: 0,
  observation: 0,
})

// 测试运行对话框
const testDialogVisible = ref(false)
const testForm = ref({
  algorithmId: 0,
  algorithmName: '',
  params: '',
})
const testLoading = ref(false)
const testResult = ref<string | null>(null)

// 统计卡片数据
const statsCards = computed(() => [
  { title: '全部算法', value: categoryStats.value.total, color: '#e94560', icon: 'Cpu' },
  { title: '同化', value: categoryStats.value.assimilation, color: '#3498db', icon: 'Connection' },
  { title: '规划', value: categoryStats.value.planning, color: '#2ecc71', icon: 'Guide' },
  { title: 'AI模型', value: categoryStats.value.model_engine, color: '#e94560', icon: 'MagicStick' },
  { title: '边云', value: categoryStats.value.edge, color: '#f39c12', icon: 'Cloudy' },
  { title: '风险', value: categoryStats.value.risk, color: '#e74c3c', icon: 'Warning' },
  { title: '观测', value: categoryStats.value.observation, color: '#9b59b6', icon: 'View' },
])

async function loadAlgorithms() {
  loading.value = true
  try {
    const data = await algorithmApi.list({
      category: selectedCategory.value || undefined,
      keyword: searchKeyword.value || undefined,
      page: currentPage.value,
      size: pageSize.value,
    })
    // 适配不同返回结构
    if (Array.isArray(data)) {
      algorithms.value = data as Algorithm[]
      total.value = data.length
    } else if (data && typeof data === 'object') {
      algorithms.value = (data as { records?: Algorithm[] }).records ?? []
      total.value = (data as { total?: number }).total ?? 0
    }
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

async function loadCategoryStats() {
  try {
    const data = await algorithmApi.getCategoryStats()
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
    let params: Record<string, unknown> | undefined
    if (testForm.value.params.trim()) {
      params = JSON.parse(testForm.value.params)
    }
    const result = await algorithmApi.execute(testForm.value.algorithmId, { params })
    testResult.value = JSON.stringify(result, null, 2)
    ElMessage.success('测试运行完成')
  } catch {
    testResult.value = '测试运行失败'
  } finally {
    testLoading.value = false
  }
}

onMounted(() => {
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
          <el-select
            v-model="selectedCategory"
            placeholder="分类筛选"
            style="width: 140px"
            @change="handleCategoryChange"
          >
            <el-option
              v-for="opt in categoryOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索算法名称 / ID"
            clearable
            style="width: 260px; margin-left: 12px"
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button type="primary" style="margin-left: 12px" @click="handleSearch">
            搜索
          </el-button>
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
        <el-table-column prop="name" label="算法名称" min-width="180" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="100">
          <template #default="{ row }">
            <el-tag
              size="small"
              effect="plain"
              :color="categoryColorMap[row.category] || '#6c6c80'"
              style="color: #fff; border: none"
            >
              {{ categoryLabelMap[row.category] || row.category }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <StatusBadge :status="row.status" />
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
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'ACTIVE'"
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

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <!-- 测试运行对话框 -->
    <el-dialog v-model="testDialogVisible" title="算法测试运行" width="600px">
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
        <label class="param-label">运行结果</label>
        <pre class="result-output">{{ testResult }}</pre>
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

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
}

/* 对话框 */
.param-label {
  display: block;
  margin-bottom: 8px;
  color: var(--color-text-secondary);
  font-size: 13px;
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
