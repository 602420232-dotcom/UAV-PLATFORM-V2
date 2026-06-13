<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatDateTime } from '@/utils/format'

interface Algorithm {
  id: number
  name: string
  type: string
  version: string
  status: string
  description: string
  registeredAt: string
  lastRunAt: string | null
  runCount: number
  config: string | null
}

const loading = ref(false)
const algorithms = ref<Algorithm[]>([])

// 测试运行对话框
const testDialogVisible = ref(false)
const testForm = ref({
  algorithmId: 0,
  algorithmName: '',
  params: '',
})
const testLoading = ref(false)
const testResult = ref<string | null>(null)

// 模拟加载算法列表（实际应调用后端 API）
async function loadAlgorithms() {
  loading.value = true
  try {
    // TODO: 替换为实际 API 调用
    // const data = await algorithmApi.list()
    algorithms.value = [
      {
        id: 1,
        name: 'A* 路径规划',
        type: 'path_planning',
        version: '1.2.0',
        status: 'ACTIVE',
        description: '基于 A* 算法的无人机路径规划，支持三维空间避障',
        registeredAt: '2025-01-15T10:00:00',
        lastRunAt: '2025-06-12T08:30:00',
        runCount: 1523,
        config: '{"heuristic": "euclidean", "maxIterations": 10000}',
      },
      {
        id: 2,
        name: 'WRF-3DVAR 数据同化',
        type: 'assimilation',
        version: '2.0.1',
        status: 'ACTIVE',
        description: '基于 WRF 模型的三维变分数据同化算法',
        registeredAt: '2025-02-20T14:00:00',
        lastRunAt: '2025-06-11T16:00:00',
        runCount: 856,
        config: '{"outerLoop": 2, "innerLoop": 50}',
      },
      {
        id: 3,
        name: 'RRT 路径规划',
        type: 'path_planning',
        version: '1.0.0',
        status: 'ACTIVE',
        description: '快速随机树路径规划算法，适用于复杂障碍物环境',
        registeredAt: '2025-03-10T09:00:00',
        lastRunAt: '2025-06-10T11:00:00',
        runCount: 432,
        config: '{"maxIterations": 5000, "stepSize": 10}',
      },
      {
        id: 4,
        name: '综合风险评估模型',
        type: 'risk_assessment',
        version: '1.5.0',
        status: 'ACTIVE',
        description: '多因子综合风险评估模型，支持气象、地形、空域等多维度评估',
        registeredAt: '2025-04-01T08:00:00',
        lastRunAt: '2025-06-12T07:00:00',
        runCount: 2341,
        config: '{"factors": ["weather", "terrain", "airspace", "traffic"]}',
      },
      {
        id: 5,
        name: '观测决策优化',
        type: 'observation',
        version: '1.1.0',
        status: 'DEPRECATED',
        description: '基于覆盖率和成本优化的观测决策算法（已弃用）',
        registeredAt: '2025-01-05T10:00:00',
        lastRunAt: null,
        runCount: 120,
        config: null,
      },
    ]
  } finally {
    loading.value = false
  }
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
    // TODO: 替换为实际 API 调用
    // const result = await algorithmApi.testRun(testForm.value.algorithmId, JSON.parse(testForm.value.params))
    await new Promise((resolve) => setTimeout(resolve, 2000))
    testResult.value = JSON.stringify(
      {
        success: true,
        executionTime: '1.23s',
        output: {
          message: '算法测试运行成功',
          algorithmId: testForm.value.algorithmId,
          timestamp: new Date().toISOString(),
        },
      },
      null,
      2
    )
    ElMessage.success('测试运行完成')
  } catch {
    testResult.value = '测试运行失败'
  } finally {
    testLoading.value = false
  }
}

onMounted(() => {
  loadAlgorithms()
})
</script>

<template>
  <div class="algorithm-page">
    <div class="page-header">
      <h2>算法管理</h2>
    </div>

    <el-card class="table-card">
      <el-table v-loading="loading" :data="algorithms" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="算法名称" min-width="150" />
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <StatusBadge :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="runCount" label="运行次数" width="100" />
        <el-table-column prop="lastRunAt" label="最近运行" width="180">
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

.table-card {
  border-radius: 8px;
}

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
</style>
