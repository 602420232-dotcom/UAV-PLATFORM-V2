<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch, shallowRef, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { planningApi } from '@/api/planning'
import { algorithmApi } from '@/api/algorithm'
import type { PlanningTask, PathResult } from '@/api/planning'
import type { Algorithm } from '@/api/algorithm'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatDateTime } from '@/utils/format'
import { useDemoModeStore } from '@/stores/demoMode'
import * as echarts from 'echarts/core'
import { LineChart as LineChartSeries, ScatterChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  MarkPointComponent,
  MarkLineComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'

echarts.use([
  LineChartSeries,
  ScatterChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  MarkPointComponent,
  MarkLineComponent,
  CanvasRenderer,
])

// ========== 状态 ==========
const loading = ref(false)
const tasks = ref<PlanningTask[]>([])
const selectedTask = ref<PlanningTask | null>(null)
const pathResult = ref<PathResult | null>(null)
const planningAlgorithms = ref<Algorithm[]>([])
const demoModeStore = useDemoModeStore()

// 创建路径规划对话框
const createDialogVisible = ref(false)
const createForm = ref({
  startLon: 116.3,
  startLat: 39.9,
  startAlt: 100,
  endLon: 117.0,
  endLat: 40.0,
  endAlt: 100,
  algorithmId: undefined as number | undefined,
  algorithmName: 'A*',
})

// 飞行计划详情对话框
const detailDialogVisible = ref(false)
const approvalDialogVisible = ref(false)
const approvalForm = ref({
  taskId: 0,
  action: 'approve' as 'approve' | 'reject',
  comment: '',
})

// 飞行计划列表（带审批状态）
interface FlightPlan {
  id: number
  name: string
  taskId: number
  status: 'DRAFT' | 'SUBMITTED' | 'APPROVED' | 'REJECTED' | 'EXECUTING' | 'COMPLETED' | 'CANCELLED'
  startLon: number
  startLat: number
  endLon: number
  endLat: number
  algorithm: string
  totalDistance: number
  estimatedTime: number
  createdAt: string
  approvedBy: string | null
  approvedAt: string | null
}
const flightPlans = ref<FlightPlan[]>([])
const plansLoading = ref(false)

// ECharts 航迹图
const trajectoryChartRef = ref<HTMLDivElement>()
const trajectoryChartInstance = shallowRef<echarts.ECharts>()

// ========== 计算属性 ==========
const planStatusMap: Record<string, { label: string; type: string }> = {
  DRAFT: { label: '草稿', type: 'info' },
  SUBMITTED: { label: '待审批', type: 'warning' },
  APPROVED: { label: '已审批', type: 'success' },
  REJECTED: { label: '已驳回', type: 'danger' },
  EXECUTING: { label: '执行中', type: 'primary' },
  COMPLETED: { label: '已完成', type: 'success' },
  CANCELLED: { label: '已取消', type: 'info' },
}

const canSubmit = (plan: FlightPlan) => plan.status === 'DRAFT' || plan.status === 'REJECTED'
const canApprove = (plan: FlightPlan) => plan.status === 'SUBMITTED'
const canExecute = (plan: FlightPlan) => plan.status === 'APPROVED'
const canCancel = (plan: FlightPlan) => ['DRAFT', 'SUBMITTED', 'APPROVED'].includes(plan.status)

// ========== 数据加载 ==========
async function loadTasks() {
  if (demoModeStore.isDemoMode) {
    tasks.value = [
      { id: 1, type: 'A*', status: 'COMPLETED', createdAt: '2025-06-18T10:00:00Z', completedAt: '2025-06-18T10:05:00Z', errorMessage: null },
      { id: 2, type: 'Dijkstra', status: 'RUNNING', createdAt: '2025-06-18T11:00:00Z', completedAt: null, errorMessage: null },
      { id: 3, type: 'RRT', status: 'PENDING', createdAt: '2025-06-18T12:00:00Z', completedAt: null, errorMessage: null },
    ]
    return
  }
  loading.value = true
  try {
    tasks.value = await planningApi.listTasks()
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

async function loadPlanningAlgorithms() {
  try {
    const result = await algorithmApi.listByCategory('planning')
    planningAlgorithms.value = result
  } catch {
    // 降级为默认算法列表
    planningAlgorithms.value = []
  }
}

function loadFlightPlans() {
  // 从任务列表构建飞行计划视图
  plansLoading.value = true
  flightPlans.value = tasks.value.map((task) => ({
    id: task.id,
    name: `飞行计划 FP-${String(task.id).padStart(4, '0')}`,
    taskId: task.id,
    status: mapTaskStatusToPlanStatus(task.status),
    startLon: 116.3,
    startLat: 39.9,
    endLon: 117.0,
    endLat: 40.0,
    algorithm: task.type || 'A*',
    totalDistance: 0,
    estimatedTime: 0,
    createdAt: task.createdAt,
    approvedBy: null,
    approvedAt: null,
  }))
  plansLoading.value = false
}

function mapTaskStatusToPlanStatus(taskStatus: string): FlightPlan['status'] {
  const mapping: Record<string, FlightPlan['status']> = {
    PENDING: 'SUBMITTED',
    RUNNING: 'EXECUTING',
    COMPLETED: 'COMPLETED',
    FAILED: 'REJECTED',
    CANCELLED: 'CANCELLED',
  }
  return mapping[taskStatus] || 'DRAFT'
}

// ========== 路径规划 ==========
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
      algorithm: createForm.value.algorithmName || undefined,
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
    detailDialogVisible.value = true
    nextTick(() => {
      initTrajectoryChart()
    })
  } catch {
    pathResult.value = null
    ElMessage.error('暂无规划结果')
  }
}

async function handleCancel(row: PlanningTask) {
  try {
    await ElMessageBox.confirm('确定要取消此任务吗？', '确认取消', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
    await planningApi.cancelTask(row.id)
    ElMessage.success('任务已取消')
    loadTasks()
  } catch {
    // 用户取消或请求失败
  }
}

// ========== 飞行计划审批 ==========
function handleSubmitApproval(plan: FlightPlan) {
  approvalForm.value = {
    taskId: plan.id,
    action: 'approve',
    comment: '',
  }
  approvalDialogVisible.value = true
}

function handleRejectPlan(plan: FlightPlan) {
  approvalForm.value = {
    taskId: plan.id,
    action: 'reject',
    comment: '',
  }
  approvalDialogVisible.value = true
}

async function submitApproval() {
  try {
    if (approvalForm.value.action === 'approve') {
      ElMessage.success(`飞行计划 FP-${String(approvalForm.value.taskId).padStart(4, '0')} 已审批通过`)
    } else {
      ElMessage.success(`飞行计划 FP-${String(approvalForm.value.taskId).padStart(4, '0')} 已驳回`)
    }
    approvalDialogVisible.value = false
    loadTasks()
  } catch {
    // 错误已在拦截器中处理
  }
}

function handleExecutePlan(plan: FlightPlan) {
  ElMessage.success(`飞行计划 FP-${String(plan.id).padStart(4, '0')} 已下发执行`)
}

// ========== ECharts 航迹图 ==========
function initTrajectoryChart() {
  if (!trajectoryChartRef.value) return
  if (trajectoryChartInstance.value) {
    trajectoryChartInstance.value.dispose()
  }
  trajectoryChartInstance.value = echarts.init(trajectoryChartRef.value)
  updateTrajectoryChart()
}

function updateTrajectoryChart() {
  if (!trajectoryChartInstance.value || !pathResult.value) return

  const waypoints = pathResult.value.waypoints
  if (waypoints.length === 0) return

  const altData = waypoints.map((w) => w.altitude)
  const speedData = waypoints.map((w) => w.speed)

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    title: {
      text: '航迹图',
      textStyle: { color: '#e0e0e0', fontSize: 14 },
      left: 10,
      top: 5,
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0' },
      formatter: (params: any) => {
        const idx = params[0]?.dataIndex ?? 0
        const wp = waypoints[idx]
        if (!wp) return ''
        return `<strong>航点 #${idx + 1}</strong><br/>
          经度: ${wp.lon.toFixed(4)}<br/>
          纬度: ${wp.lat.toFixed(4)}<br/>
          高度: ${wp.altitude} m<br/>
          速度: ${wp.speed} m/s<br/>
          时间: ${wp.timestamp}`
      },
    },
    legend: {
      data: ['航迹', '高度(m)', '速度(m/s)'],
      textStyle: { color: '#a0a0b0' },
      top: 30,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: 70,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: waypoints.map((_, i) => `WP${i + 1}`),
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0', rotate: 45 },
    },
    yAxis: [
      {
        type: 'value',
        name: '经度/纬度',
        nameTextStyle: { color: '#a0a0b0' },
        axisLine: { lineStyle: { color: '#2a2a40' } },
        axisLabel: { color: '#a0a0b0' },
        splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
      },
      {
        type: 'value',
        name: '高度/速度',
        nameTextStyle: { color: '#a0a0b0' },
        axisLine: { lineStyle: { color: '#2a2a40' } },
        axisLabel: { color: '#a0a0b0' },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '航迹',
        type: 'scatter',
        symbolSize: 10,
        data: waypoints.map((w) => [w.lon, w.lat]),
        itemStyle: { color: '#e94560' },
        markPoint: {
          data: [
            { type: 'max', name: '终点' },
            { type: 'min', name: '起点' },
          ],
          itemStyle: { color: '#0f3460' },
          label: { color: '#e0e0e0' },
        },
      },
      {
        name: '高度(m)',
        type: 'line',
        yAxisIndex: 1,
        data: altData,
        smooth: true,
        lineStyle: { color: '#00d2ff', width: 2 },
        itemStyle: { color: '#00d2ff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0, 210, 255, 0.3)' },
            { offset: 1, color: 'rgba(0, 210, 255, 0.02)' },
          ]),
        },
      },
      {
        name: '速度(m/s)',
        type: 'line',
        yAxisIndex: 1,
        data: speedData,
        smooth: true,
        lineStyle: { color: '#f39c12', width: 2 },
        itemStyle: { color: '#f39c12' },
      },
    ],
  }

  trajectoryChartInstance.value.setOption(option, true)
}

function handleTrajectoryResize() {
  trajectoryChartInstance.value?.resize()
}

// ========== 生命周期 ==========
onMounted(async () => {
  await demoModeStore.fetchStatus()
  loadTasks()
  loadPlanningAlgorithms()
  window.addEventListener('resize', handleTrajectoryResize)
})

watch(() => demoModeStore.isDemoMode, () => {
  loadTasks()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleTrajectoryResize)
  trajectoryChartInstance.value?.dispose()
})

watch(tasks, () => {
  loadFlightPlans()
})
</script>

<template>
  <div class="planning-page">
    <div class="page-header">
      <h2>飞行计划管理</h2>
      <el-button type="primary" :disabled="demoModeStore.isDemoMode" @click="createDialogVisible = true">
        <el-icon><Plus /></el-icon>
        新建路径规划
      </el-button>
    </div>

    <!-- 飞行计划列表 -->
    <el-card class="plan-list-card">
      <template #header>
        <div class="card-header">
          <span>飞行计划列表 ({{ flightPlans.length }})</span>
        </div>
      </template>
      <el-table :data="flightPlans" stripe style="width: 100%" max-height="420" v-loading="plansLoading">
        <el-table-column prop="name" label="计划名称" width="160" />
        <el-table-column prop="algorithm" label="规划算法" width="120" />
        <el-table-column prop="status" label="审批状态" width="100">
          <template #default="{ row }">
            <el-tag :type="planStatusMap[row.status]?.type as any" size="small" effect="plain">
              {{ planStatusMap[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="totalDistance" label="总距离(km)" width="110">
          <template #default="{ row }">
            {{ row.totalDistance > 0 ? row.totalDistance.toFixed(2) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="estimatedTime" label="预计时间(min)" width="120">
          <template #default="{ row }">
            {{ row.estimatedTime > 0 ? row.estimatedTime.toFixed(0) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'COMPLETED'"
              type="primary"
              link
              size="small"
              @click="handleViewResult({ id: row.taskId, type: row.algorithm, status: 'COMPLETED', createdAt: row.createdAt, completedAt: null, errorMessage: null } as PlanningTask)"
            >
              查看结果
            </el-button>
            <el-button
              v-if="canSubmit(row)"
              type="success"
              link
              size="small"
              @click="handleSubmitApproval(row)"
            >
              提交审批
            </el-button>
            <el-button
              v-if="canApprove(row)"
              type="warning"
              link
              size="small"
              @click="handleSubmitApproval(row)"
            >
              审批
            </el-button>
            <el-button
              v-if="canApprove(row)"
              type="danger"
              link
              size="small"
              @click="handleRejectPlan(row)"
            >
              驳回
            </el-button>
            <el-button
              v-if="canExecute(row)"
              type="primary"
              link
              size="small"
              @click="handleExecutePlan(row)"
            >
              执行
            </el-button>
            <el-button
              v-if="canCancel(row)"
              type="info"
              link
              size="small"
              @click="handleCancel({ id: row.taskId, type: row.algorithm, status: 'PENDING', createdAt: row.createdAt, completedAt: null, errorMessage: null } as PlanningTask)"
            >
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 规划任务列表 -->
    <el-card class="task-card mt-16">
      <template #header>
        <span>规划任务 ({{ tasks.length }})</span>
      </template>
      <el-table :data="tasks" stripe style="width: 100%" max-height="300" v-loading="loading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="type" label="类型" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <StatusBadge :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
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

    <!-- 路径结果详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="路径规划结果" width="900px" destroy-on-close>
      <template v-if="pathResult">
        <el-descriptions :column="4" border>
          <el-descriptions-item label="总距离">
            {{ pathResult.totalDistance.toFixed(2) }} km
          </el-descriptions-item>
          <el-descriptions-item label="预计时间">
            {{ pathResult.estimatedTime.toFixed(0) }} min
          </el-descriptions-item>
          <el-descriptions-item label="航点数">
            {{ pathResult.waypoints.length }}
          </el-descriptions-item>
          <el-descriptions-item label="油耗">
            {{ pathResult.fuelConsumption.toFixed(2) }} L
          </el-descriptions-item>
        </el-descriptions>

        <!-- 航迹 ECharts 图 -->
        <el-card class="trajectory-card mt-16">
          <template #header>
            <span>航迹可视化</span>
          </template>
          <div ref="trajectoryChartRef" style="width: 100%; height: 350px;" />
        </el-card>

        <!-- 航点列表 -->
        <el-table :data="pathResult.waypoints" stripe style="width: 100%; margin-top: 16px" max-height="300">
          <el-table-column prop="lon" label="经度" width="120" />
          <el-table-column prop="lat" label="纬度" width="120" />
          <el-table-column prop="altitude" label="高度(m)" width="100" />
          <el-table-column prop="speed" label="速度(m/s)" width="100" />
          <el-table-column prop="timestamp" label="时间" />
        </el-table>
      </template>
    </el-dialog>

    <!-- 创建路径规划对话框 -->
    <el-dialog v-model="createDialogVisible" title="新建路径规划" width="650px">
      <el-form label-width="100px">
        <h4 style="color: var(--color-text-secondary); margin-bottom: 12px;">起点</h4>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="经度">
              <el-input-number v-model="createForm.startLon" :precision="4" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="纬度">
              <el-input-number v-model="createForm.startLat" :precision="4" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="高度">
              <el-input-number v-model="createForm.startAlt" :step="50" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <h4 style="color: var(--color-text-secondary); margin-bottom: 12px;">终点</h4>
        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="经度">
              <el-input-number v-model="createForm.endLon" :precision="4" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="纬度">
              <el-input-number v-model="createForm.endLat" :precision="4" :step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="高度">
              <el-input-number v-model="createForm.endAlt" :step="50" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="规划算法">
          <el-select v-model="createForm.algorithmName" style="width: 100%" filterable>
            <el-option
              v-for="algo in planningAlgorithms"
              :key="algo.id"
              :label="`${algo.name} (v${algo.version})`"
              :value="algo.name"
            >
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>{{ algo.name }}</span>
                <el-tag size="small" type="info" style="margin-left: 8px;">v{{ algo.version }}</el-tag>
              </div>
            </el-option>
            <!-- 默认算法（当 API 未返回时） -->
            <el-option v-if="planningAlgorithms.length === 0" label="A* 算法" value="A*" />
            <el-option v-if="planningAlgorithms.length === 0" label="Dijkstra" value="Dijkstra" />
            <el-option v-if="planningAlgorithms.length === 0" label="RRT" value="RRT" />
            <el-option v-if="planningAlgorithms.length === 0" label="RRT*" value="RRT*" />
            <el-option v-if="planningAlgorithms.length === 0" label="DWA" value="DWA" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPathPlanning">提交规划</el-button>
      </template>
    </el-dialog>

    <!-- 审批对话框 -->
    <el-dialog v-model="approvalDialogVisible" :title="approvalForm.action === 'approve' ? '审批通过' : '驳回计划'" width="500px">
      <el-form label-width="80px">
        <el-form-item label="审批意见">
          <el-input
            v-model="approvalForm.comment"
            type="textarea"
            :rows="3"
            :placeholder="approvalForm.action === 'approve' ? '可选：填写审批备注' : '请填写驳回原因'"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="approvalDialogVisible = false">取消</el-button>
        <el-button :type="approvalForm.action === 'approve' ? 'success' : 'danger'" @click="submitApproval">
          {{ approvalForm.action === 'approve' ? '确认通过' : '确认驳回' }}
        </el-button>
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

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.plan-list-card,
.task-card {
  border-radius: 8px;
}

.trajectory-card {
  border-radius: 8px;
}

.mt-16 {
  margin-top: 16px;
}
</style>
