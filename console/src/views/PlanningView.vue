<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { planningApi } from '@/api/planning'
import type { PlanningTask, PathResult } from '@/api/planning'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatDateTime } from '@/utils/format'

const loading = ref(false)
const tasks = ref<PlanningTask[]>([])
const selectedTask = ref<PlanningTask | null>(null)
const pathResult = ref<PathResult | null>(null)

const createDialogVisible = ref(false)
const createForm = ref({
  startLon: 116.3,
  startLat: 39.9,
  startAlt: 100,
  endLon: 117.0,
  endLat: 40.0,
  endAlt: 100,
  algorithm: 'A*',
})

async function loadTasks() {
  loading.value = true
  try {
    tasks.value = await planningApi.listTasks()
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

async function submitPathPlanning() {
  try {
    await planningApi.planPath({
      startPoint: {
        lon: createForm.value.startLon,
        lat: createForm.value.startLat,
        altitude: createForm.value.startAlt,
      },
      endPoint: {
        lon: createForm.value.endLon,
        lat: createForm.value.endLat,
        altitude: createForm.value.endAlt,
      },
      algorithm: createForm.value.algorithm || undefined,
    })
    ElMessage.success('路径规划任务已提交')
    createDialogVisible.value = false
    loadTasks()
  } catch {
    // 错误已在拦截器中处理
  }
}

async function handleViewResult(row: PlanningTask) {
  selectedTask.value = row
  try {
    pathResult.value = await planningApi.getPathResult(row.id)
  } catch {
    pathResult.value = null
  }
}

async function handleCancel(row: PlanningTask) {
  try {
    await planningApi.cancelTask(row.id)
    ElMessage.success('任务已取消')
    loadTasks()
  } catch {
    // 错误已在拦截器中处理
  }
}

onMounted(() => {
  loadTasks()
})
</script>

<template>
  <div class="planning-page">
    <div class="page-header">
      <h2>路径规划</h2>
      <el-button type="primary" @click="createDialogVisible = true">
        <el-icon><Plus /></el-icon>
        新建路径规划
      </el-button>
    </div>

    <div class="content-grid">
      <!-- 地图区域（CesiumJS 占位） -->
      <!--
        TODO: 后续集成 CesiumJS 三维地图
        - 引入 cesium npm 包
        - 在此 div 中初始化 Cesium.Viewer
        - 叠加航迹线、起终点标记、航点显示
        - 支持交互式设置起终点
      -->
      <el-card class="map-card">
        <template #header>
          <span>航迹地图</span>
        </template>
        <div class="map-placeholder">
          <el-icon :size="48" color="#0f3460"><MapLocation /></el-icon>
          <p>CesiumJS 三维地图（待集成）</p>
          <p class="placeholder-hint">支持航迹显示、起终点标记、实时位置追踪</p>
        </div>
      </el-card>

      <!-- 任务列表 -->
      <el-card class="task-card">
        <template #header>
          <span>规划任务 ({{ tasks.length }})</span>
        </template>
        <el-table :data="tasks" stripe style="width: 100%" max-height="400">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="type" label="类型" width="80" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <StatusBadge :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column prop="createdAt" label="创建时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.createdAt) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 'COMPLETED'"
                type="primary"
                link
                size="small"
                @click="handleViewResult(row)"
              >
                结果
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
    </div>

    <!-- 路径结果详情 -->
    <el-card v-if="pathResult" class="result-card mt-16">
      <template #header>
        <span>路径规划结果 - 任务 #{{ selectedTask?.id }}</span>
      </template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="总距离">
          {{ pathResult.totalDistance.toFixed(2) }} km
        </el-descriptions-item>
        <el-descriptions-item label="预计时间">
          {{ pathResult.estimatedTime.toFixed(0) }} min
        </el-descriptions-item>
        <el-descriptions-item label="航点数">
          {{ pathResult.waypoints.length }}
        </el-descriptions-item>
      </el-descriptions>
      <el-table :data="pathResult.waypoints" stripe style="width: 100%; margin-top: 16px" max-height="300">
        <el-table-column prop="lon" label="经度" width="120" />
        <el-table-column prop="lat" label="纬度" width="120" />
        <el-table-column prop="altitude" label="高度(m)" width="100" />
        <el-table-column prop="speed" label="速度(m/s)" width="100" />
        <el-table-column prop="timestamp" label="时间" />
      </el-table>
    </el-card>

    <!-- 创建路径规划对话框 -->
    <el-dialog v-model="createDialogVisible" title="新建路径规划" width="600px">
      <el-form label-width="100px">
        <h4 style="color: var(--color-text-secondary); margin-bottom: 12px;">起点</h4>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="经度">
              <el-input-number v-model="createForm.startLon" :precision="4" :step="0.1" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="纬度">
              <el-input-number v-model="createForm.startLat" :precision="4" :step="0.1" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="高度">
              <el-input-number v-model="createForm.startAlt" :step="50" />
            </el-form-item>
          </el-col>
        </el-row>

        <h4 style="color: var(--color-text-secondary); margin-bottom: 12px;">终点</h4>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="经度">
              <el-input-number v-model="createForm.endLon" :precision="4" :step="0.1" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="纬度">
              <el-input-number v-model="createForm.endLat" :precision="4" :step="0.1" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="高度">
              <el-input-number v-model="createForm.endAlt" :step="50" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="算法">
          <el-select v-model="createForm.algorithm" style="width: 100%">
            <el-option label="A* 算法" value="A*" />
            <el-option label="Dijkstra" value="Dijkstra" />
            <el-option label="RRT" value="RRT" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPathPlanning">提交规划</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.planning-page {
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

.content-grid {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 16px;
}

.map-card {
  border-radius: 8px;
  min-height: 400px;
}

.map-placeholder {
  height: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background-color: var(--color-bg);
  border-radius: 4px;
  border: 1px dashed var(--color-border-light);
  color: var(--color-text-muted);
}

.placeholder-hint {
  font-size: 12px;
}

.task-card,
.result-card {
  border-radius: 8px;
}
</style>
