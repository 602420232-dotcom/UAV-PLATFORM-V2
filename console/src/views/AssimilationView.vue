<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { assimilationApi } from '@/api/assimilation'
import type { AssimilationTask, AssimilationResult } from '@/api/assimilation'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatDateTime } from '@/utils/format'

const loading = ref(false)
const tasks = ref<AssimilationTask[]>([])
const selectedResult = ref<AssimilationResult | null>(null)
const resultDialogVisible = ref(false)

// 创建任务对话框
const createDialogVisible = ref(false)
const createForm = ref({
  type: '3DVAR',
  algorithm: 'WRF-3DVAR',
  startTime: '',
  endTime: '',
  minLon: 115.0,
  minLat: 39.0,
  maxLon: 118.0,
  maxLat: 41.0,
})

async function loadTasks() {
  loading.value = true
  try {
    const data = await assimilationApi.listTasks({ page: 1, size: 50 })
    // 适配可能的不同返回结构
    if (Array.isArray(data)) {
      tasks.value = data as AssimilationTask[]
    } else if (data && typeof data === 'object') {
      const obj = data as { records?: AssimilationTask[] }
      tasks.value = obj.records ?? []
    }
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

async function submitTask() {
  try {
    await assimilationApi.submitTask({
      type: createForm.value.type,
      algorithm: createForm.value.algorithm,
      startTime: createForm.value.startTime,
      endTime: createForm.value.endTime,
      region: {
        minLon: createForm.value.minLon,
        minLat: createForm.value.minLat,
        maxLon: createForm.value.maxLon,
        maxLat: createForm.value.maxLat,
      },
    })
    ElMessage.success('同化任务已提交')
    createDialogVisible.value = false
    loadTasks()
  } catch {
    // 错误已在拦截器中处理
  }
}

async function handleViewResult(row: AssimilationTask) {
  try {
    selectedResult.value = await assimilationApi.getTaskResult(row.id)
    resultDialogVisible.value = true
  } catch {
    ElMessage.error('获取结果失败')
  }
}

async function handleCancel(row: AssimilationTask) {
  try {
    await ElMessageBox.confirm(`确定要取消任务 #${row.id} 吗？`, '确认取消', { type: 'warning' })
    await assimilationApi.cancelTask(row.id)
    ElMessage.success('任务已取消')
    loadTasks()
  } catch {
    // 用户取消
  }
}

onMounted(() => {
  loadTasks()
})
</script>

<template>
  <div class="assimilation-page">
    <div class="page-header">
      <h2>数据同化</h2>
      <el-button type="primary" @click="createDialogVisible = true">
        <el-icon><Plus /></el-icon>
        提交同化任务
      </el-button>
    </div>

    <el-card class="table-card">
      <el-table v-loading="loading" :data="tasks" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="type" label="类型" width="100" />
        <el-table-column prop="algorithm" label="算法" min-width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <StatusBadge :status="row.status" />
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
        <el-table-column prop="errorMessage" label="错误信息" min-width="200">
          <template #default="{ row }">
            <span v-if="row.errorMessage" class="error-text">{{ row.errorMessage }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'COMPLETED'"
              type="primary"
              link
              size="small"
              @click="handleViewResult(row)"
            >
              查看结果
            </el-button>
            <el-button
              v-if="row.status === 'RUNNING' || row.status === 'PENDING'"
              type="warning"
              link
              size="small"
              @click="handleCancel(row)"
            >
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 结果对话框 -->
    <el-dialog v-model="resultDialogVisible" title="同化结果" width="600px">
      <div v-if="selectedResult">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="分析时间">{{ selectedResult.analysisTime }}</el-descriptions-item>
          <el-descriptions-item label="变量">
            {{ selectedResult.variables?.join(', ') || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="分辨率">
            {{ selectedResult.gridInfo?.resolution }}
          </el-descriptions-item>
          <el-descriptions-item label="层数">
            {{ selectedResult.gridInfo?.levels }}
          </el-descriptions-item>
          <el-descriptions-item label="区域范围" :span="2">
            {{ selectedResult.gridInfo?.minLon }}, {{ selectedResult.gridInfo?.minLat }} ~
            {{ selectedResult.gridInfo?.maxLon }}, {{ selectedResult.gridInfo?.maxLat }}
          </el-descriptions-item>
        </el-descriptions>
        <div v-if="selectedResult.dataUrl" class="mt-16">
          <el-link type="primary" :href="selectedResult.dataUrl" target="_blank">
            下载数据文件
          </el-link>
        </div>
      </div>
    </el-dialog>

    <!-- 创建任务对话框 -->
    <el-dialog v-model="createDialogVisible" title="提交同化任务" width="600px">
      <el-form label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="同化类型">
              <el-select v-model="createForm.type" style="width: 100%">
                <el-option label="3DVAR" value="3DVAR" />
                <el-option label="4DVAR" value="4DVAR" />
                <el-option label="EnKF" value="EnKF" />
                <el-option label="Hybrid" value="Hybrid" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="算法">
              <el-select v-model="createForm.algorithm" style="width: 100%">
                <el-option label="WRF-3DVAR" value="WRF-3DVAR" />
                <el-option label="WRF-4DVAR" value="WRF-4DVAR" />
                <el-option label="GFS-EnKF" value="GFS-EnKF" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="开始时间">
              <el-input v-model="createForm.startTime" placeholder="ISO 时间格式" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束时间">
              <el-input v-model="createForm.endTime" placeholder="ISO 时间格式" />
            </el-form-item>
          </el-col>
        </el-row>
        <h4 style="color: var(--color-text-secondary); margin-bottom: 12px;">区域范围</h4>
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
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitTask">提交任务</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.assimilation-page {
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

.table-card {
  border-radius: 8px;
}

.error-text {
  color: var(--color-danger);
  font-size: 12px;
}
</style>
