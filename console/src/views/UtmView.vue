<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { utmApi } from '@/api/utm'
import type { Airspace, FlightPlan, ConflictAlert } from '@/api/utm'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatDateTime } from '@/utils/format'
import UtmEnvironmentConfig from '@/components/settings/UtmEnvironmentConfig.vue'
import { useDemoModeStore } from '@/stores/demoMode'

const loading = ref(false)
const airspaces = ref<Airspace[]>([])
const flightPlans = ref<FlightPlan[]>([])
const conflictAlerts = ref<ConflictAlert[]>([])
const demoModeStore = useDemoModeStore()

// 创建空域对话框
const createAirspaceDialogVisible = ref(false)
const airspaceForm = ref({
  name: '',
  type: 'restricted',
  minAltitude: 0,
  maxAltitude: 500,
})

// 检查空域限制
const checkForm = ref({
  lon: 116.4,
  lat: 39.9,
  altitude: 100,
})
const checkResult = ref<boolean | null>(null)

async function loadData() {
  if (demoModeStore.isDemoMode) {
    airspaces.value = [
      { id: 1, name: '禁飞区-A01', type: 'restricted', status: 'ACTIVE', minAltitude: 0, maxAltitude: 500, geometry: null, restrictions: ['禁止所有飞行'], createdAt: '2025-06-18T08:00:00Z' },
      { id: 2, name: '限制区-B02', type: 'controlled', status: 'ACTIVE', minAltitude: 200, maxAltitude: 1000, geometry: null, restrictions: ['需审批'], createdAt: '2025-06-18T09:00:00Z' },
      { id: 3, name: '临时空域-C03', type: 'temporary', status: 'PENDING', minAltitude: 100, maxAltitude: 300, geometry: null, restrictions: ['限时飞行'], createdAt: '2025-06-18T10:00:00Z' },
    ]
    flightPlans.value = [
      { id: 1, uavId: 'UAV-001', status: 'APPROVED', waypoints: [{ lon: 116.3, lat: 39.9, altitude: 100, speed: 15, timestamp: '2025-06-18T10:00:00Z' }, { lon: 116.5, lat: 40.0, altitude: 120, speed: 15, timestamp: '2025-06-18T10:10:00Z' }], submittedAt: '2025-06-18T09:00:00Z', approvedAt: '2025-06-18T09:30:00Z' },
      { id: 2, uavId: 'UAV-002', status: 'SUBMITTED', waypoints: [{ lon: 116.8, lat: 39.7, altitude: 80, speed: 12, timestamp: '2025-06-18T11:00:00Z' }, { lon: 117.0, lat: 39.9, altitude: 100, speed: 12, timestamp: '2025-06-18T11:15:00Z' }], submittedAt: '2025-06-18T10:00:00Z', approvedAt: null },
      { id: 3, uavId: 'UAV-003', status: 'EXECUTING', waypoints: [{ lon: 115.5, lat: 39.5, altitude: 150, speed: 18, timestamp: '2025-06-18T08:00:00Z' }, { lon: 115.8, lat: 39.8, altitude: 150, speed: 18, timestamp: '2025-06-18T08:20:00Z' }, { lon: 116.0, lat: 40.0, altitude: 120, speed: 18, timestamp: '2025-06-18T08:40:00Z' }], submittedAt: '2025-06-18T07:30:00Z', approvedAt: '2025-06-18T07:45:00Z' },
      { id: 4, uavId: 'UAV-004', status: 'COMPLETED', waypoints: [{ lon: 116.2, lat: 40.1, altitude: 90, speed: 10, timestamp: '2025-06-18T06:00:00Z' }, { lon: 116.4, lat: 40.3, altitude: 90, speed: 10, timestamp: '2025-06-18T06:30:00Z' }], submittedAt: '2025-06-18T05:30:00Z', approvedAt: '2025-06-18T05:45:00Z' },
      { id: 5, uavId: 'UAV-005', status: 'REJECTED', waypoints: [{ lon: 117.0, lat: 39.6, altitude: 200, speed: 20, timestamp: '2025-06-18T12:00:00Z' }], submittedAt: '2025-06-18T11:00:00Z', approvedAt: null },
    ]
    conflictAlerts.value = [
      { id: 1, type: 'proximity', severity: 'HIGH', status: 'ACTIVE', uavId1: 'UAV-001', uavId2: 'UAV-003', location: { lon: 116.4, lat: 39.8, altitude: 120 }, timeToConflict: 45, createdAt: '2025-06-18T10:05:00Z' },
      { id: 2, type: 'altitude_conflict', severity: 'MEDIUM', status: 'RESOLVED', uavId1: 'UAV-002', uavId2: 'UAV-004', location: { lon: 116.6, lat: 39.9, altitude: 100 }, timeToConflict: 120, createdAt: '2025-06-18T09:30:00Z' },
    ]
    return
  }
  loading.value = true
  try {
    const [airspaceData, planData, alertData] = await Promise.allSettled([
      utmApi.listAirspaces(),
      utmApi.listFlightPlans(),
      utmApi.listConflictAlerts(),
    ])

    if (airspaceData.status === 'fulfilled') airspaces.value = airspaceData.value
    if (planData.status === 'fulfilled') flightPlans.value = planData.value
    if (alertData.status === 'fulfilled') conflictAlerts.value = alertData.value
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

async function createAirspace() {
  try {
    await utmApi.createAirspace(airspaceForm.value)
    ElMessage.success('空域创建成功')
    createAirspaceDialogVisible.value = false
    loadData()
  } catch {
    // 错误已在拦截器中处理
  }
}

async function checkRestriction() {
  try {
    checkResult.value = await utmApi.checkRestriction(
      checkForm.value.lon,
      checkForm.value.lat,
      checkForm.value.altitude
    )
  } catch {
    // 错误已在拦截器中处理
  }
}

function getSeverityType(severity: string): 'success' | 'warning' | 'danger' | 'info' {
  switch (severity) {
    case 'HIGH': return 'danger'
    case 'MEDIUM': return 'warning'
    case 'LOW': return 'info'
    default: return 'info'
  }
}

onMounted(async () => {
  await demoModeStore.fetchStatus()
  loadData()
})

watch(() => demoModeStore.isDemoMode, () => {
  loadData()
})
</script>

<template>
  <div class="utm-page">
    <div class="page-header">
      <h2>UTM 空域管理</h2>
      <el-button type="primary" :disabled="demoModeStore.isDemoMode" @click="createAirspaceDialogVisible = true">
        <el-icon><Plus /></el-icon>
        创建空域
      </el-button>
    </div>

    <!-- UTM 双环境配置 -->
    <UtmEnvironmentConfig />

    <!-- 快速检查 -->
    <el-card class="check-card">
      <template #header>
        <span>空域限制检查</span>
      </template>
      <div class="check-form">
        <el-input-number v-model="checkForm.lon" :precision="4" :step="0.1" placeholder="经度" />
        <el-input-number v-model="checkForm.lat" :precision="4" :step="0.1" placeholder="纬度" />
        <el-input-number v-model="checkForm.altitude" :step="50" placeholder="高度(m)" />
        <el-button type="primary" @click="checkRestriction">检查</el-button>
        <div v-if="checkResult !== null" class="check-result">
          <el-tag :type="checkResult ? 'success' : 'danger'" effect="dark" style="border: none">
            {{ checkResult ? '无限制' : '受限空域' }}
          </el-tag>
        </div>
      </div>
    </el-card>

    <div class="content-grid">
      <!-- 空域列表 -->
      <el-card class="table-card">
        <template #header>
          <span>空域列表 ({{ airspaces.length }})</span>
        </template>
        <el-table :data="airspaces" stripe style="width: 100%">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="name" label="名称" min-width="120" />
          <el-table-column prop="type" label="类型" width="100" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <StatusBadge :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column label="高度范围" width="140">
            <template #default="{ row }">
              {{ row.minAltitude }}m ~ {{ row.maxAltitude }}m
            </template>
          </el-table-column>
          <el-table-column prop="createdAt" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.createdAt) }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 冲突告警 -->
      <el-card class="table-card">
        <template #header>
          <div class="flex-between">
            <span>冲突告警 ({{ conflictAlerts.length }})</span>
          </div>
        </template>
        <el-table :data="conflictAlerts" stripe style="width: 100%">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="type" label="类型" width="80" />
          <el-table-column prop="severity" label="严重程度" width="100">
            <template #default="{ row }">
              <el-tag :type="getSeverityType(row.severity)" size="small" effect="dark" style="border: none">
                {{ row.severity }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80">
            <template #default="{ row }">
              <StatusBadge :status="row.status" />
            </template>
          </el-table-column>
          <el-table-column label="无人机" width="120">
            <template #default="{ row }">
              {{ row.uavId1 }} / {{ row.uavId2 }}
            </template>
          </el-table-column>
          <el-table-column prop="timeToConflict" label="冲突时间(s)" width="120" />
        </el-table>
      </el-card>
    </div>

    <!-- 飞行计划 -->
    <el-card class="table-card mt-16">
      <template #header>
        <span>飞行计划 ({{ flightPlans.length }})</span>
      </template>
      <el-table :data="flightPlans" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="uavId" label="无人机 ID" min-width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <StatusBadge :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column label="航点数" width="100">
          <template #default="{ row }">
            {{ row.waypoints?.length ?? 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="submittedAt" label="提交时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.submittedAt) }}
          </template>
        </el-table-column>
        <el-table-column prop="approvedAt" label="批准时间" width="180">
          <template #default="{ row }">
            {{ row.approvedAt ? formatDateTime(row.approvedAt) : '-' }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建空域对话框 -->
    <el-dialog v-model="createAirspaceDialogVisible" title="创建空域" width="500px">
      <el-form label-width="100px">
        <el-form-item label="名称">
          <el-input v-model="airspaceForm.name" placeholder="空域名称" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="airspaceForm.type" style="width: 100%">
            <el-option label="禁飞区" value="restricted" />
            <el-option label="限制区" value="controlled" />
            <el-option label="临时空域" value="temporary" />
          </el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="最低高度">
              <el-input-number v-model="airspaceForm.minAltitude" :step="50" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最高高度">
              <el-input-number v-model="airspaceForm.maxAltitude" :step="50" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="createAirspaceDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="createAirspace">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.utm-page {
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

.check-card {
  border-radius: 8px;
}

.check-form {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.check-result {
  display: flex;
  align-items: center;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.table-card {
  border-radius: 8px;
}
</style>
