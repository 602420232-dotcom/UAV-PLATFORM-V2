<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { riskApi } from '@/api/risk'
import type { RiskAssessment } from '@/api/risk'
import { formatDateTime } from '@/utils/format'

const loading = ref(false)
const historyRecords = ref<RiskAssessment[]>([])

// 风险评估表单
const assessDialogVisible = ref(false)
const assessForm = ref({
  lon: 116.4,
  lat: 39.9,
  altitude: 100,
  time: '',
  uavType: 'multirotor',
})

// 评估结果
const assessResult = ref<RiskAssessment | null>(null)
const resultDialogVisible = ref(false)

async function loadHistory() {
  loading.value = true
  try {
    historyRecords.value = await riskApi.getHistory({ limit: 50 })
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

async function submitAssess() {
  try {
    assessResult.value = await riskApi.assess({
      path: [
        {
          lon: assessForm.value.lon,
          lat: assessForm.value.lat,
          altitude: assessForm.value.altitude,
        },
      ],
      time: assessForm.value.time || new Date().toISOString(),
      uavType: assessForm.value.uavType,
    })
    assessDialogVisible.value = false
    resultDialogVisible.value = true
  } catch {
    // 错误已在拦截器中处理
  }
}

function getRiskLevelColor(level: string): string {
  switch (level) {
    case 'LOW': return 'var(--color-success)'
    case 'MEDIUM': return 'var(--color-warning)'
    case 'HIGH': return 'var(--color-danger)'
    default: return 'var(--color-text-muted)'
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<template>
  <div class="risk-page">
    <div class="page-header">
      <h2>风险/适航评估</h2>
      <el-button type="primary" @click="assessDialogVisible = true">
        <el-icon><Plus /></el-icon>
        发起评估
      </el-button>
    </div>

    <!-- 快速统计 -->
    <div class="stats-row">
      <el-card class="stat-card">
        <div class="stat-content">
          <span class="stat-label">低风险</span>
          <span class="stat-value" style="color: var(--color-success)">
            {{ historyRecords.filter(r => r.riskLevel === 'LOW').length }}
          </span>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <span class="stat-label">中风险</span>
          <span class="stat-value" style="color: var(--color-warning)">
            {{ historyRecords.filter(r => r.riskLevel === 'MEDIUM').length }}
          </span>
        </div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-content">
          <span class="stat-label">高风险</span>
          <span class="stat-value" style="color: var(--color-danger)">
            {{ historyRecords.filter(r => r.riskLevel === 'HIGH').length }}
          </span>
        </div>
      </el-card>
    </div>

    <!-- 历史记录 -->
    <el-card class="table-card">
      <template #header>
        <span>评估历史</span>
      </template>
      <el-table v-loading="loading" :data="historyRecords" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="type" label="类型" width="120" />
        <el-table-column prop="riskLevel" label="风险等级" width="120">
          <template #default="{ row }">
            <el-tag
              :color="getRiskLevelColor(row.riskLevel)"
              effect="dark"
              size="small"
              style="border: none"
            >
              {{ row.riskLevel }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="风险分数" width="100">
          <template #default="{ row }">
            {{ row.score?.toFixed(2) ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column label="位置" width="180">
          <template #default="{ row }">
            {{ row.lon?.toFixed(4) }}, {{ row.lat?.toFixed(4) }}
          </template>
        </el-table-column>
        <el-table-column prop="assessedAt" label="评估时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.assessedAt) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 评估对话框 -->
    <el-dialog v-model="assessDialogVisible" title="发起风险评估" width="500px">
      <el-form label-width="100px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="经度">
              <el-input-number v-model="assessForm.lon" :precision="4" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="纬度">
              <el-input-number v-model="assessForm.lat" :precision="4" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="高度(m)">
          <el-input-number v-model="assessForm.altitude" :step="50" style="width: 100%" />
        </el-form-item>
        <el-form-item label="评估时间">
          <el-input v-model="assessForm.time" placeholder="ISO 时间格式（可选）" />
        </el-form-item>
        <el-form-item label="无人机类型">
          <el-select v-model="assessForm.uavType" style="width: 100%">
            <el-option label="多旋翼" value="multirotor" />
            <el-option label="固定翼" value="fixedwing" />
            <el-option label="垂直起降" value="vtol" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assessDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAssess">发起评估</el-button>
      </template>
    </el-dialog>

    <!-- 结果对话框 -->
    <el-dialog v-model="resultDialogVisible" title="评估结果" width="600px">
      <div v-if="assessResult">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="风险等级">
            <el-tag
              :color="getRiskLevelColor(assessResult.riskLevel)"
              effect="dark"
              style="border: none"
            >
              {{ assessResult.riskLevel }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="风险分数">
            {{ assessResult.score?.toFixed(2) }}
          </el-descriptions-item>
          <el-descriptions-item label="类型" :span="2">{{ assessResult.type }}</el-descriptions-item>
        </el-descriptions>
        <div v-if="assessResult.factors?.length" class="mt-16">
          <h4 style="color: var(--color-text-secondary); margin-bottom: 8px;">风险因子</h4>
          <el-table :data="assessResult.factors" stripe size="small">
            <el-table-column prop="name" label="因子" />
            <el-table-column prop="value" label="值" width="100" />
            <el-table-column prop="weight" label="权重" width="100" />
            <el-table-column prop="level" label="等级" width="100">
              <template #default="{ row }">
                <el-tag
                  :color="getRiskLevelColor(row.level)"
                  effect="dark"
                  size="small"
                  style="border: none"
                >
                  {{ row.level }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.risk-page {
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

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-card {
  border-radius: 8px;
}

.stat-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px;
}

.stat-label {
  color: var(--color-text-secondary);
  font-size: 14px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
}

.table-card {
  border-radius: 8px;
}
</style>
