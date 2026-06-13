<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { observationApi } from '@/api/observation'
import type { ObservationTask, ObservationDecision } from '@/api/observation'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatDateTime } from '@/utils/format'

const loading = ref(false)
const tasks = ref<ObservationTask[]>([])

// 创建任务对话框
const createDialogVisible = ref(false)
const createForm = ref({
  type: 'meteorological',
  priority: 5,
  minLon: 115.0,
  minLat: 39.0,
  maxLon: 118.0,
  maxLat: 41.0,
  targetVariables: ['temperature', 'wind', 'humidity'],
  platform: '',
})

// 决策建议对话框
const decisionDialogVisible = ref(false)
const decisionResult = ref<ObservationDecision | null>(null)

const decisionForm = ref({
  minLon: 115.0,
  minLat: 39.0,
  maxLon: 118.0,
  maxLat: 41.0,
  targetVariables: ['temperature', 'wind'],
})

async function loadTasks() {
  loading.value = true
  try {
    tasks.value = await observationApi.listTasks()
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

async function submitCreate() {
  try {
    await observationApi.createTask({
      type: createForm.value.type,
      priority: createForm.value.priority,
      region: {
        minLon: createForm.value.minLon,
        minLat: createForm.value.minLat,
        maxLon: createForm.value.maxLon,
        maxLat: createForm.value.maxLat,
      },
      targetVariables: createForm.value.targetVariables,
      platform: createForm.value.platform || undefined,
    })
    ElMessage.success('观测任务已创建')
    createDialogVisible.value = false
    loadTasks()
  } catch {
    // 错误已在拦截器中处理
  }
}

async function getDecision() {
  try {
    decisionResult.value = await observationApi.getDecision({
      region: {
        minLon: decisionForm.value.minLon,
        minLat: decisionForm.value.minLat,
        maxLon: decisionForm.value.maxLon,
        maxLat: decisionForm.value.maxLat,
      },
      targetVariables: decisionForm.value.targetVariables,
    })
    decisionDialogVisible.value = true
  } catch {
    // 错误已在拦截器中处理
  }
}

function getPriorityTag(priority: number): 'success' | 'warning' | 'danger' | 'info' {
  if (priority >= 8) return 'danger'
  if (priority >= 5) return 'warning'
  if (priority >= 3) return 'info'
  return 'success'
}

onMounted(() => {
  loadTasks()
})
</script>

<template>
  <div class="observation-page">
    <div class="page-header">
      <h2>观测决策</h2>
      <div class="header-actions">
        <el-button @click="getDecision">
          <el-icon><MagicStick /></el-icon>
          获取决策建议
        </el-button>
        <el-button type="primary" @click="createDialogVisible = true">
          <el-icon><Plus /></el-icon>
          创建观测任务
        </el-button>
      </div>
    </div>

    <el-card class="table-card">
      <template #header>
        <span>观测任务列表 ({{ tasks.length }})</span>
      </template>
      <el-table v-loading="loading" :data="tasks" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="type" label="类型" width="120" />
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag :type="getPriorityTag(row.priority)" size="small">
              P{{ row.priority }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <StatusBadge :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column label="目标变量" min-width="150">
          <template #default="{ row }">
            <el-tag
              v-for="v in row.targetVariables"
              :key="v"
              size="small"
              effect="plain"
              style="margin-right: 4px"
            >
              {{ v }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="platform" label="平台" width="120">
          <template #default="{ row }">
            {{ row.platform || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column prop="completedAt" label="完成时间" width="180">
          <template #default="{ row }">
            {{ row.completedAt ? formatDateTime(row.completedAt) : '-' }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建任务对话框 -->
    <el-dialog v-model="createDialogVisible" title="创建观测任务" width="600px">
      <el-form label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="类型">
              <el-select v-model="createForm.type" style="width: 100%">
                <el-option label="气象观测" value="meteorological" />
                <el-option label="环境监测" value="environmental" />
                <el-option label="目标侦察" value="reconnaissance" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级">
              <el-input-number v-model="createForm.priority" :min="1" :max="10" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <h4 style="color: var(--color-text-secondary); margin-bottom: 12px;">观测区域</h4>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="最小经度">
              <el-input-number v-model="createForm.minLon" :precision="4" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最小纬度">
              <el-input-number v-model="createForm.minLat" :precision="4" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="最大经度">
              <el-input-number v-model="createForm.maxLon" :precision="4" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大纬度">
              <el-input-number v-model="createForm.maxLat" :precision="4" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="目标变量">
          <el-select v-model="createForm.targetVariables" multiple style="width: 100%">
            <el-option label="温度" value="temperature" />
            <el-option label="风场" value="wind" />
            <el-option label="湿度" value="humidity" />
            <el-option label="气压" value="pressure" />
            <el-option label="能见度" value="visibility" />
          </el-select>
        </el-form-item>
        <el-form-item label="平台">
          <el-input v-model="createForm.platform" placeholder="观测平台（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreate">创建任务</el-button>
      </template>
    </el-dialog>

    <!-- 决策建议对话框 -->
    <el-dialog v-model="decisionDialogVisible" title="观测决策建议" width="600px">
      <div v-if="decisionResult">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="决策">{{ decisionResult.decision }}</el-descriptions-item>
          <el-descriptions-item label="覆盖率">
            {{ (decisionResult.coverageScore * 100).toFixed(1) }}%
          </el-descriptions-item>
          <el-descriptions-item label="建议时间" :span="2">
            {{ decisionResult.suggestedTime }}
          </el-descriptions-item>
          <el-descriptions-item label="建议平台" :span="2">
            <el-tag
              v-for="p in decisionResult.suggestedPlatforms"
              :key="p"
              size="small"
              effect="plain"
              style="margin-right: 4px"
            >
              {{ p }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="决策依据" :span="2">
            {{ decisionResult.reason }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.observation-page {
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

.header-actions {
  display: flex;
  gap: 8px;
}

.table-card {
  border-radius: 8px;
}
</style>
