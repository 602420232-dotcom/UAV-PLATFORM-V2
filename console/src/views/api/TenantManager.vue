<template>
  <div class="tenant-manager">
    <!-- 统计卡片 -->
    <div class="stats-row">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-icon" style="background: rgba(64,158,255,0.15); color: #409eff;">
          <el-icon><User /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">总租户数</div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-icon" style="background: rgba(103,194,58,0.15); color: #67c23a;">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.active }}</div>
          <div class="stat-label">活跃租户</div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-icon" style="background: rgba(230,162,60,0.15); color: #e6a23c;">
          <el-icon><DataAnalysis /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.totalQuota }}</div>
          <div class="stat-label">总配额 (GB)</div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-icon" style="background: rgba(245,108,108,0.15); color: #f56c6c;">
          <el-icon><TrendCharts /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.avgUsage }}%</div>
          <div class="stat-label">平均使用率</div>
        </div>
      </el-card>
    </div>

    <!-- 操作栏 -->
    <el-card class="table-card" shadow="never">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-input
            v-model="searchQuery"
            placeholder="搜索租户名称"
            clearable
            class="search-input"
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-select v-model="statusFilter" placeholder="状态筛选" clearable @change="handleSearch">
            <el-option label="全部" value="" />
            <el-option label="活跃" value="active" />
            <el-option label="暂停" value="suspended" />
          </el-select>
        </div>
        <el-button type="primary" :disabled="demoModeStore.isDemoMode" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          创建租户
        </el-button>
      </div>

      <!-- 租户表格 -->
      <el-table
        :data="pagedTenants"
        style="width: 100%"
        v-loading="loading"
        :header-cell-style="headerStyle"
      >
        <el-table-column prop="name" label="租户名称" min-width="140">
          <template #default="{ row }">
            <div class="tenant-name">
              <el-avatar :size="32" :style="{ background: row.avatarColor }">
                {{ row.name.charAt(0) }}
              </el-avatar>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="schemaName" label="Schema" min-width="120" />
        <el-table-column label="配额使用" min-width="200">
          <template #default="{ row }">
            <div class="usage-cell">
              <div class="usage-text">
                <span>{{ row.used }} GB / {{ row.quota }} GB</span>
                <span :class="['usage-percent', getUsageClass(row)]">{{ getUsagePercent(row) }}%</span>
              </div>
              <el-progress
                :percentage="getUsagePercent(row)"
                :color="getProgressColor(row)"
                :stroke-width="8"
                :show-text="false"
              />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="160">
          <template #default="{ row }">
            <span>{{ formatDate(row.createdAt) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewDetail(row)">
              <el-icon><View /></el-icon>
            </el-button>
            <el-button link type="primary" size="small" :disabled="demoModeStore.isDemoMode" @click="openEditDialog(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button
              link
              :type="row.status === 'active' ? 'warning' : 'success'"
              size="small"
              :disabled="demoModeStore.isDemoMode"
              @click="toggleStatus(row)"
            >
              <el-icon>
                <VideoPause v-if="row.status === 'active'" />
                <VideoPlay v-else />
              </el-icon>
            </el-button>
            <el-popconfirm
              title="确定删除该租户吗？"
              confirm-button-text="确定"
              cancel-button-text="取消"
              :disabled="demoModeStore.isDemoMode"
              @confirm="deleteTenant(row)"
            >
              <template #reference>
                <el-button link type="danger" size="small" :disabled="demoModeStore.isDemoMode">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          background
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑租户' : '创建租户'"
      width="500px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="tenant-form"
      >
        <el-form-item label="租户名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入租户名称" />
        </el-form-item>
        <el-form-item label="Schema" prop="schemaName">
          <el-input v-model="form.schemaName" placeholder="请输入数据库 schema 名称" />
        </el-form-item>
        <el-form-item label="配额 (GB)" prop="quota">
          <el-input-number v-model="form.quota" :min="1" :max="100000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio label="active">活跃</el-radio>
            <el-radio label="suspended">暂停</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer
      v-model="detailVisible"
      title="租户详情"
      size="400px"
      destroy-on-close
    >
      <div v-if="currentTenant" class="detail-content">
        <div class="detail-header">
          <el-avatar :size="64" :style="{ background: currentTenant.avatarColor }">
            {{ currentTenant.name.charAt(0) }}
          </el-avatar>
          <h3>{{ currentTenant.name }}</h3>
          <el-tag :type="getStatusType(currentTenant.status)" size="small">
            {{ getStatusLabel(currentTenant.status) }}
          </el-tag>
        </div>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="Schema">{{ currentTenant.schemaName }}</el-descriptions-item>
          <el-descriptions-item label="配额">{{ currentTenant.quota }} GB</el-descriptions-item>
          <el-descriptions-item label="已用量">{{ currentTenant.used }} GB</el-descriptions-item>
          <el-descriptions-item label="使用率">
            <el-progress :percentage="getUsagePercent(currentTenant)" :color="getProgressColor(currentTenant)" />
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(currentTenant.createdAt) }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ formatDate(currentTenant.updatedAt) }}</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, watch } from 'vue'
import {
  User, CircleCheck, DataAnalysis, TrendCharts,
  Search, Plus, View, Edit, Delete, VideoPause, VideoPlay
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { tenantApi } from '@/api/tenant'
import { useDemoModeStore } from '@/stores/demoMode'

const demoModeStore = useDemoModeStore()

interface TenantView {
  id: number
  name: string
  schemaName: string
  status: 'active' | 'suspended' | 'deleted'
  quotaConfig: string | null
  createdAt: string
  updatedAt: string
  avatarColor?: string
  quota: number
  used: number
}

const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const dialogVisible = ref(false)
const isEdit = ref(false)
const detailVisible = ref(false)
const currentTenant = ref<TenantView | null>(null)
const formRef = ref<FormInstance>()
const submitting = ref(false)

const form = reactive({
  id: undefined as number | undefined,
  name: '',
  schemaName: '',
  quota: 100,
  status: 'active' as 'active' | 'suspended'
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入租户名称', trigger: 'blur' }],
  schemaName: [{ required: true, message: '请输入 Schema 名称', trigger: 'blur' }],
  quota: [{ required: true, message: '请输入配额', trigger: 'blur' }]
}

const avatarColors = ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399', '#8e44ad', '#16a085', '#d35400']

const tenants = ref<TenantView[]>([])

// 统计
const stats = computed(() => {
  const total = tenants.value.length
  const active = tenants.value.filter(t => t.status === 'active').length
  const totalQuota = tenants.value.reduce((sum, t) => sum + t.quota, 0)
  const avgUsage = total > 0
    ? Math.round(tenants.value.reduce((sum, t) => sum + (t.used / t.quota * 100), 0) / total)
    : 0
  return { total, active, totalQuota, avgUsage }
})

// 筛选
const filteredTenants = computed(() => {
  let result = tenants.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(t => t.name.toLowerCase().includes(q))
  }
  if (statusFilter.value) {
    result = result.filter(t => t.status === statusFilter.value)
  }
  return result
})

const pagedTenants = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredTenants.value.slice(start, start + pageSize.value)
})

const handleSearch = () => {
  currentPage.value = 1
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
  loadData()
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  loadData()
}

const getUsagePercent = (row: TenantView) => {
  return Math.round((row.used / row.quota) * 100)
}

const getUsageClass = (row: TenantView) => {
  const p = getUsagePercent(row)
  if (p >= 90) return 'usage-high'
  if (p >= 70) return 'usage-medium'
  return 'usage-low'
}

const getProgressColor = (row: TenantView) => {
  const p = getUsagePercent(row)
  if (p >= 90) return '#f56c6c'
  if (p >= 70) return '#e6a23c'
  return '#67c23a'
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = { active: 'success', suspended: 'warning', deleted: 'info' }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = { active: '活跃', suspended: '暂停', deleted: '已删除' }
  return map[status] || status
}

const headerStyle = () => ({
  background: '#252545',
  color: '#b0b0d0',
  fontWeight: 600
})

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const openCreateDialog = () => {
  isEdit.value = false
  form.id = undefined
  form.name = ''
  form.schemaName = ''
  form.quota = 100
  form.status = 'active'
  dialogVisible.value = true
}

const openEditDialog = (row: TenantView) => {
  isEdit.value = true
  form.id = row.id
  form.name = row.name
  form.schemaName = row.schemaName
  form.quota = row.quota
  form.status = row.status as 'active' | 'suspended'
  dialogVisible.value = true
}

const submitForm = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    if (isEdit.value) {
      await tenantApi.update(form.id!, {
        name: form.name,
        quotaConfig: JSON.stringify({ quota: form.quota })
      })
      const idx = tenants.value.findIndex(t => t.id === form.id)
      if (idx !== -1) {
        const existing = tenants.value[idx]!
        tenants.value[idx] = {
          ...existing,
          name: form.name,
          schemaName: form.schemaName,
          quota: form.quota,
          status: form.status
        }
      }
      ElMessage.success('租户更新成功')
    } else {
      const res = await tenantApi.create({
        name: form.name,
        schemaName: form.schemaName,
        quotaConfig: JSON.stringify({ quota: form.quota })
      })
      const newTenant: TenantView = {
        id: res.id,
        name: res.name,
        schemaName: res.schemaName,
        status: mapStatus(res.status),
        quotaConfig: res.quotaConfig,
        createdAt: res.createdAt,
        updatedAt: res.updatedAt,
        quota: form.quota,
        used: 0,
        avatarColor: avatarColors[Math.floor(Math.random() * avatarColors.length)] || '#409eff'
      }
      tenants.value.unshift(newTenant)
      total.value += 1
      ElMessage.success('租户创建成功')
    }
    dialogVisible.value = false
  } catch (err: any) {
    ElMessage.error(err?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

const viewDetail = (row: TenantView) => {
  currentTenant.value = row
  detailVisible.value = true
}

const toggleStatus = async (row: TenantView) => {
  const newStatus = row.status === 'active' ? 'suspended' : 'active'
  try {
    if (newStatus === 'active') {
      await tenantApi.enable(row.id)
    } else {
      await tenantApi.disable(row.id)
    }
    row.status = newStatus
    ElMessage.success(`租户已${newStatus === 'active' ? '恢复' : '暂停'}`)
  } catch (err: any) {
    ElMessage.error(err?.message || '操作失败')
  }
}

const deleteTenant = async (row: TenantView) => {
  try {
    await tenantApi.remove(row.id)
    tenants.value = tenants.value.filter(t => t.id !== row.id)
    total.value -= 1
    ElMessage.success('租户删除成功')
  } catch (err: any) {
    ElMessage.error(err?.message || '删除失败')
  }
}

async function loadData() {
  loading.value = true
  try {
    if (demoModeStore.isDemoMode) {
      tenants.value = [
        { id: 1, name: '默认租户', schemaName: 'tenant_default', status: 'active', quotaConfig: '{"quota": 100}', createdAt: '2025-01-01T00:00:00Z', updatedAt: '2025-06-01T00:00:00Z', avatarColor: '#409eff', quota: 100, used: 45 },
        { id: 2, name: '气象服务中心', schemaName: 'tenant_weather', status: 'active', quotaConfig: '{"quota": 200}', createdAt: '2025-02-15T08:00:00Z', updatedAt: '2025-05-20T10:00:00Z', avatarColor: '#67c23a', quota: 200, used: 130 },
        { id: 3, name: '科研院所', schemaName: 'tenant_research', status: 'active', quotaConfig: '{"quota": 150}', createdAt: '2025-03-10T09:00:00Z', updatedAt: '2025-06-10T14:00:00Z', avatarColor: '#e6a23c', quota: 150, used: 60 },
        { id: 4, name: '应急救援队', schemaName: 'tenant_emergency', status: 'suspended', quotaConfig: '{"quota": 80}', createdAt: '2025-04-20T11:30:00Z', updatedAt: '2025-05-15T16:00:00Z', avatarColor: '#f56c6c', quota: 80, used: 75 },
      ] as TenantView[]
      total.value = tenants.value.length
      return
    }
    const res = await tenantApi.list(currentPage.value, pageSize.value)
    tenants.value = (res.records || []).map((item, idx) => ({
      id: item.id,
      name: item.name,
      schemaName: item.schemaName,
      status: mapStatus(item.status),
      quotaConfig: item.quotaConfig,
      createdAt: item.createdAt,
      updatedAt: item.updatedAt,
      avatarColor: avatarColors[idx % avatarColors.length],
      quota: parseQuota(item.quotaConfig),
      used: 0
    }))
    total.value = res.total || 0
  } catch (err: any) {
    ElMessage.error(err?.message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

function mapStatus(status: number): 'active' | 'suspended' | 'deleted' {
  const map: Record<number, 'active' | 'suspended' | 'deleted'> = {
    0: 'active',
    1: 'suspended',
    2: 'deleted'
  }
  return map[status] ?? 'active'
}

function parseQuota(config: string | null): number {
  if (!config) return 100
  try {
    const parsed = JSON.parse(config)
    return parsed.quota || 100
  } catch {
    return 100
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

<style scoped>
.tenant-manager {
  padding: 24px;
  background: #1a1a2e;
  min-height: 100vh;
  color: #e0e0e0;
}

/* 统计卡片 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  background: #1f1f35;
  border: 1px solid #2a2a4a;
  border-radius: 12px;
}

.stat-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #e0e0e0;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #8888aa;
  margin-top: 4px;
}

/* 表格卡片 */
.table-card {
  background: #1f1f35;
  border: 1px solid #2a2a4a;
  border-radius: 12px;
}

.table-card :deep(.el-card__body) {
  padding: 20px;
}

/* 工具栏 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-left {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.search-input {
  width: 240px;
}

/* 表格样式 */
:deep(.el-table) {
  background: transparent;
  --el-table-header-bg-color: #252545;
  --el-table-row-hover-bg-color: #2a2a50;
  --el-table-border-color: #2a2a4a;
  --el-table-text-color: #e0e0e0;
}

:deep(.el-table th.el-table__cell) {
  background: #252545 !important;
}

:deep(.el-table td.el-table__cell) {
  background: #1f1f35;
  border-bottom-color: #2a2a4a;
}

:deep(.el-table tr:hover td.el-table__cell) {
  background: #2a2a50 !important;
}

/* 租户名称 */
.tenant-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tenant-name span {
  font-weight: 500;
  color: #e0e0e0;
}

/* 用量进度 */
.usage-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.usage-text {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #a0a0c0;
}

.usage-percent {
  font-weight: 600;
}

.usage-low { color: #67c23a; }
.usage-medium { color: #e6a23c; }
.usage-high { color: #f56c6c; }

/* 分页 */
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #2a2a4a;
}

/* 表单 */
.tenant-form :deep(.el-form-item__label) {
  color: #c0c0e0;
}

/* 详情抽屉 */
.detail-content {
  padding: 16px 0;
}

.detail-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #2a2a4a;
}

.detail-header h3 {
  margin: 0;
  color: #e0e0e0;
  font-size: 20px;
}

:deep(.el-descriptions__body) {
  background: #1f1f35;
}

:deep(.el-descriptions__label) {
  background: #252545 !important;
  color: #a0a0c0;
}

:deep(.el-descriptions__content) {
  background: #1f1f35 !important;
  color: #e0e0e0;
}

/* 响应式 */
@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: 1fr;
  }

  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar-left {
    flex-direction: column;
    width: 100%;
  }

  .search-input {
    width: 100%;
  }

  :deep(.el-table) {
    font-size: 12px;
  }
}
</style>
