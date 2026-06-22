<template>
  <div class="api-key-manager">
    <!-- 统计卡片 -->
    <div class="stats-row">
      <el-card class="stat-card" shadow="hover">
        <div class="stat-icon total">
          <el-icon><Key /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">总密钥数</div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-icon active">
          <el-icon><CircleCheck /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.active }}</div>
          <div class="stat-label">活跃密钥</div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-icon calls">
          <el-icon><TrendCharts /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.todayCalls }}</div>
          <div class="stat-label">今日调用</div>
        </div>
      </el-card>
      <el-card class="stat-card" shadow="hover">
        <div class="stat-icon expire">
          <el-icon><Timer /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.expiringSoon }}</div>
          <div class="stat-label">即将过期</div>
        </div>
      </el-card>
    </div>

    <!-- 操作栏 -->
    <el-card class="toolbar-card" shadow="never">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-input
            v-model="searchQuery"
            placeholder="搜索密钥名称..."
            class="search-input"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-select
            v-model="statusFilter"
            placeholder="状态筛选"
            clearable
            class="status-filter"
            @change="handleFilter"
          >
            <el-option label="全部" value="" />
            <el-option label="活跃" value="active" />
            <el-option label="已禁用" value="disabled" />
            <el-option label="已过期" value="expired" />
          </el-select>
        </div>
        <div class="toolbar-right">
          <el-button type="primary" :disabled="demoModeStore.isDemoMode" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            创建密钥
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 密钥列表 -->
    <el-card class="table-card" shadow="never">
      <el-table
        :data="pagedList"
        style="width: 100%"
        v-loading="loading"
        :header-cell-style="headerCellStyle"
      >
        <el-table-column prop="name" label="名称" min-width="140">
          <template #default="{ row }">
            <div class="name-cell">
              <span class="name-text">{{ row.name }}</span>
              <el-tag v-if="row.isDefault" size="small" type="warning" class="default-tag">默认</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="keyValue" label="密钥前缀" width="180">
          <template #default="{ row }">
            <code class="key-prefix">{{ row.keyValue }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="160">
          <template #default="{ row }">
            <span class="time-text">{{ formatDate(row.createdAt) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="expiresAt" label="过期时间" width="160">
          <template #default="{ row }">
            <span :class="['time-text', isExpiringSoon(row.expiresAt) ? 'expiring' : '']">
              {{ row.expiresAt ? formatDate(row.expiresAt) : '永不过期' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="callCount" label="调用次数" width="110">
          <template #default="{ row }">
            <span class="count-text">{{ formatNumber(row.callCount || 0) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="rateLimit" label="限流设置" width="140">
          <template #default="{ row }">
            <span class="rate-text">{{ row.rateLimit ?? '-' }} 次/分钟</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button link type="primary" size="small" :disabled="demoModeStore.isDemoMode" @click="handleEdit(row)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button
                link
                :type="row.status === 'active' ? 'warning' : 'success'"
                size="small"
                :disabled="demoModeStore.isDemoMode"
                @click="handleToggleStatus(row)"
              >
                <el-icon>
                  <CircleClose v-if="row.status === 'active'" />
                  <CircleCheck v-else />
                </el-icon>
                {{ row.status === 'active' ? '禁用' : '启用' }}
              </el-button>
              <el-button link type="primary" size="small" @click="handleCopy(row)">
                <el-icon><CopyDocument /></el-icon>
                复制
              </el-button>
              <el-popconfirm
                title="确定删除该密钥吗？此操作不可恢复。"
                confirm-button-text="删除"
                cancel-button-text="取消"
                confirm-button-type="danger"
                :disabled="demoModeStore.isDemoMode"
                @confirm="handleDelete(row)"
              >
                <template #reference>
                  <el-button link type="danger" size="small" :disabled="demoModeStore.isDemoMode">
                    <el-icon><Delete /></el-icon>
                    删除
                  </el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="filteredList.length"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="520px"
      :close-on-click-modal="false"
      class="api-key-dialog"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="api-key-form"
      >
        <el-form-item label="密钥名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入密钥名称" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="过期时间" prop="expiresAt">
          <el-date-picker
            v-model="form.expiresAt"
            type="datetime"
            placeholder="选择过期时间（留空则永不过期）"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DDTHH:mm:ss"
            class="full-width"
            clearable
          />
        </el-form-item>
        <el-form-item label="限流设置" prop="rateLimit">
          <el-input-number v-model="form.rateLimit" :min="1" :max="10000" :step="10" class="rate-input" />
          <span class="unit-text">次/分钟</span>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="可选：输入密钥用途描述"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        <el-form-item v-if="isEdit" label="状态">
          <el-switch
            v-model="form.status"
            active-value="active"
            inactive-value="disabled"
            active-text="活跃"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '保存' : '创建' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 新建成功展示密钥 -->
    <el-dialog
      v-model="showNewKeyDialog"
      title="密钥创建成功"
      width="520px"
      :show-close="false"
      :close-on-click-modal="false"
      class="api-key-dialog new-key-dialog"
    >
      <el-alert type="warning" :closable="false" class="key-warning">
        <template #title>
          <div class="warning-title">
            <el-icon><Warning /></el-icon>
            <span>请立即复制并保存您的密钥，关闭后将无法再次查看完整密钥</span>
          </div>
        </template>
      </el-alert>
      <div class="new-key-display">
        <code class="new-key-code">{{ newKeyValue }}</code>
        <el-button type="primary" class="copy-btn" @click="copyNewKey">
          <el-icon><CopyDocument /></el-icon>
          复制密钥
        </el-button>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="showNewKeyDialog = false">我已保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Key,
  CircleCheck,
  CircleClose,
  TrendCharts,
  Timer,
  Search,
  Plus,
  Edit,
  CopyDocument,
  Delete,
  Warning
} from '@element-plus/icons-vue'
import { apiKeyApi } from '@/api/apiKey'
import { useAuthStore } from '@/stores/auth'
import { useDemoModeStore } from '@/stores/demoMode'

interface ApiKeyItem {
  id: number
  tenantId: number
  keyValue: string
  secret: string
  name: string
  status: 'active' | 'disabled' | 'expired'
  rateLimit: number | null
  createdAt: string
  expiresAt: string | null
  isDefault?: boolean
  callCount?: number
  description?: string
}

const authStore = useAuthStore()
const demoModeStore = useDemoModeStore()
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)

const stats = reactive({
  total: 0,
  active: 0,
  todayCalls: 0,
  expiringSoon: 0
})

const apiKeyList = ref<ApiKeyItem[]>([])

const filteredList = computed(() => {
  let list = apiKeyList.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(item => item.name.toLowerCase().includes(q) || (item.keyValue ?? '').toLowerCase().includes(q))
  }
  if (statusFilter.value) {
    list = list.filter(item => item.status === statusFilter.value)
  }
  return list
})

const pagedList = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredList.value.slice(start, start + pageSize.value)
})

function updateStats() {
  const now = new Date()
  const sevenDaysLater = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000)
  stats.total = apiKeyList.value.length
  stats.active = apiKeyList.value.filter(i => i.status === 'active').length
  stats.todayCalls = 0
  stats.expiringSoon = apiKeyList.value.filter(i => {
    if (!i.expiresAt || i.status !== 'active') return false
    const exp = new Date(i.expiresAt)
    return exp > now && exp <= sevenDaysLater
  }).length
}

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

function formatNumber(n: number): string {
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}

function getStatusType(status: string): string {
  const map: Record<string, string> = {
    active: 'success',
    disabled: 'info',
    expired: 'danger'
  }
  return map[status] || 'info'
}

function getStatusLabel(status: string): string {
  const map: Record<string, string> = {
    active: '活跃',
    disabled: '已禁用',
    expired: '已过期'
  }
  return map[status] || status
}

function isExpiringSoon(dateStr: string | null): boolean {
  if (!dateStr) return false
  const now = new Date()
  const exp = new Date(dateStr)
  const sevenDays = 7 * 24 * 60 * 60 * 1000
  return exp > now && (exp.getTime() - now.getTime()) <= sevenDays
}

const headerCellStyle = () => ({
  background: '#16162a',
  color: '#a0a0c0',
  fontWeight: 600,
  borderBottom: '1px solid #2a2a4a'
})

function handleSearch() {
  currentPage.value = 1
}

function handleFilter() {
  currentPage.value = 1
}

function handleSizeChange(val: number) {
  pageSize.value = val
  currentPage.value = 1
}

function handleCurrentChange(val: number) {
  currentPage.value = val
}

// 创建/编辑
const dialogVisible = ref(false)
const isEdit = ref(false)
const dialogTitle = computed(() => (isEdit.value ? '编辑API密钥' : '创建API密钥'))
const formRef = ref()
const submitting = ref(false)

const form = reactive({
  id: undefined as number | undefined,
  name: '',
  expiresAt: '' as string | null,
  rateLimit: 100,
  description: '',
  status: 'active' as 'active' | 'disabled'
})

const rules = {
  name: [{ required: true, message: '请输入密钥名称', trigger: 'blur' }],
  rateLimit: [{ required: true, message: '请设置限流', trigger: 'change' }]
}

function resetForm() {
  form.id = undefined
  form.name = ''
  form.expiresAt = ''
  form.rateLimit = 100
  form.description = ''
  form.status = 'active'
}

function handleCreate() {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

function handleEdit(row: ApiKeyItem) {
  isEdit.value = true
  form.id = row.id
  form.name = row.name
  form.expiresAt = row.expiresAt || ''
  form.rateLimit = row.rateLimit ?? 100
  form.description = row.description || ''
  form.status = row.status === 'expired' ? 'disabled' : row.status
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const tenantId = authStore.currentTenantId
    if (!tenantId) {
      ElMessage.error('未获取到当前租户信息')
      return
    }
    if (isEdit.value) {
      // 编辑时仅更新本地状态（后端无对应 update 接口，按需求保留编辑对话框）
      const idx = apiKeyList.value.findIndex(i => i.id === form.id)
      if (idx !== -1 && form.id !== undefined) {
        const existing = apiKeyList.value[idx]!
        apiKeyList.value[idx] = {
          ...existing,
          name: form.name,
          expiresAt: form.expiresAt || null,
          status: form.status,
          rateLimit: form.rateLimit,
          description: form.description
        }
      }
      ElMessage.success('密钥已更新')
      dialogVisible.value = false
    } else {
      const res = await apiKeyApi.generate({
        tenantId,
        name: form.name,
        rateLimit: form.rateLimit,
        expiresInDays: form.expiresAt ? Math.ceil((new Date(form.expiresAt).getTime() - Date.now()) / (1000 * 60 * 60 * 24)) : undefined
      })
      apiKeyList.value.unshift({
        id: res.id,
        tenantId: res.tenantId,
        keyValue: res.keyValue,
        secret: res.secret,
        name: res.name,
        status: mapStatus(res.status),
        rateLimit: res.rateLimit,
        createdAt: res.createdAt,
        expiresAt: res.expiresAt,
        description: form.description
      })
      newKeyValue.value = res.keyValue
      showNewKeyDialog.value = true
      ElMessage.success('密钥创建成功')
      dialogVisible.value = false
    }
    updateStats()
  } catch (err: any) {
    ElMessage.error(err?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

// 新建密钥展示
const showNewKeyDialog = ref(false)
const newKeyValue = ref('')

function copyNewKey() {
  navigator.clipboard.writeText(newKeyValue.value).then(() => {
    ElMessage.success('密钥已复制到剪贴板')
  })
}

// 操作
async function handleToggleStatus(row: ApiKeyItem) {
  const newStatus = row.status === 'active' ? 'disabled' : 'active'
  const actionText = newStatus === 'active' ? '启用' : '禁用'
  try {
    await ElMessageBox.confirm(`确定要${actionText}密钥 "${row.name}" 吗？`, '确认操作', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    if (newStatus === 'active') {
      await apiKeyApi.enable(row.id)
    } else {
      await apiKeyApi.disable(row.id)
    }
    row.status = newStatus
    updateStats()
    ElMessage.success(`密钥已${actionText}`)
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error(err?.message || '操作失败')
    }
  }
}

function handleCopy(row: ApiKeyItem) {
  const text = row.keyValue || ''
  navigator.clipboard.writeText(text).then(() => {
    ElMessage.success('密钥已复制到剪贴板')
  })
}

async function handleDelete(row: ApiKeyItem) {
  try {
    await apiKeyApi.remove(row.id)
    apiKeyList.value = apiKeyList.value.filter(i => i.id !== row.id)
    updateStats()
    ElMessage.success('密钥已删除')
  } catch (err: any) {
    ElMessage.error(err?.message || '删除失败')
  }
}

async function loadData() {
  if (demoModeStore.isDemoMode) {
    apiKeyList.value = [
      { id: 1, tenantId: 1, keyValue: 'uav_ak_prod_a1b2c3d4e5f6', secret: '****', name: '生产环境主密钥', status: 'active', rateLimit: 100, createdAt: '2025-02-01T08:00:00Z', expiresAt: null, isDefault: true, callCount: 15234, description: '用于生产环境API调用' },
      { id: 2, tenantId: 1, keyValue: 'uav_ak_test_x9y8z7w6v5u4', secret: '****', name: '测试环境密钥', status: 'active', rateLimit: 50, createdAt: '2025-03-15T10:00:00Z', expiresAt: '2026-03-15T10:00:00Z', callCount: 8765, description: '用于测试环境' },
      { id: 3, tenantId: 1, keyValue: 'uav_ak_data_m1n2o3p4q5r6', secret: '****', name: '数据分析专用', status: 'active', rateLimit: 200, createdAt: '2025-05-20T14:00:00Z', expiresAt: null, callCount: 3200, description: '仅供数据导出和分析' },
      { id: 4, tenantId: 1, keyValue: 'uav_ak_old_k1l2m3n4o5p6', secret: '****', name: '已禁用密钥', status: 'disabled', rateLimit: 0, createdAt: '2024-06-01T09:00:00Z', expiresAt: '2025-06-01T09:00:00Z', callCount: 500, description: '' },
      { id: 5, tenantId: 1, keyValue: 'uav_ak_temp_a7b8c9d0e1f2', secret: '****', name: '临时访问密钥', status: 'active', rateLimit: 30, createdAt: '2025-07-01T16:00:00Z', expiresAt: '2025-08-01T16:00:00Z', callCount: 120, description: '临时授权，即将过期' },
    ] as ApiKeyItem[]
    updateStats()
    return
  }
  const tenantId = authStore.currentTenantId
  if (!tenantId) {
    ElMessage.error('未获取到当前租户信息')
    loading.value = false
    return
  }
  loading.value = true
  try {
    const data = await apiKeyApi.listByTenant(tenantId)
    apiKeyList.value = data.map(item => ({
      id: item.id,
      tenantId: item.tenantId,
      keyValue: item.keyValue,
      secret: item.secret,
      name: item.name,
      status: mapStatus(item.status),
      rateLimit: item.rateLimit,
      createdAt: item.createdAt,
      expiresAt: item.expiresAt,
      description: ''
    }))
    updateStats()
  } catch (err: any) {
    ElMessage.error(err?.message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

function mapStatus(status: number): 'active' | 'disabled' | 'expired' {
  const map: Record<number, 'active' | 'disabled' | 'expired'> = {
    0: 'active',
    1: 'disabled',
    2: 'expired'
  }
  return map[status] ?? 'active'
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
.api-key-manager {
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
  color: #e0e0e0;
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

.stat-icon.total {
  background: rgba(64, 158, 255, 0.15);
  color: #409eff;
}

.stat-icon.active {
  background: rgba(103, 194, 58, 0.15);
  color: #67c23a;
}

.stat-icon.calls {
  background: rgba(230, 162, 60, 0.15);
  color: #e6a23c;
}

.stat-icon.expire {
  background: rgba(245, 108, 108, 0.15);
  color: #f56c6c;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
  color: #ffffff;
}

.stat-label {
  font-size: 13px;
  color: #8888aa;
  margin-top: 4px;
}

/* 工具栏 */
.toolbar-card {
  background: #1f1f35;
  border: 1px solid #2a2a4a;
  border-radius: 12px;
  margin-bottom: 20px;
}

.toolbar-card :deep(.el-card__body) {
  padding: 16px 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
  width: 260px;
}

.status-filter {
  width: 140px;
}

/* 表格卡片 */
.table-card {
  background: #1f1f35;
  border: 1px solid #2a2a4a;
  border-radius: 12px;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.table-card :deep(.el-table) {
  background: transparent;
  --el-table-row-hover-bg-color: #252545;
}

.table-card :deep(.el-table__body-wrapper) {
  background: transparent;
}

.table-card :deep(.el-table tr) {
  background: transparent;
}

.table-card :deep(.el-table td) {
  background: transparent;
  border-bottom: 1px solid #2a2a4a;
  color: #c0c0d0;
}

.table-card :deep(.el-table th) {
  background: #16162a;
  border-bottom: 1px solid #2a2a4a;
}

.table-card :deep(.el-table--enable-row-hover .el-table__body tr:hover > td) {
  background: #252545;
}

.table-card :deep(.el-table__empty-block) {
  background: transparent;
}

/* 单元格样式 */
.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.name-text {
  font-weight: 500;
  color: #e0e0e0;
}

.default-tag {
  margin-left: 4px;
}

.key-prefix {
  background: #16162a;
  padding: 4px 10px;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #a0c0ff;
  border: 1px solid #2a2a4a;
}

.time-text {
  color: #a0a0c0;
  font-size: 13px;
}

.time-text.expiring {
  color: #f56c6c;
  font-weight: 500;
}

.count-text {
  font-weight: 600;
  color: #e0e0e0;
}

.rate-text {
  color: #a0a0c0;
  font-size: 13px;
}

.action-btns {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

/* 分页 */
.pagination-wrapper {
  padding: 16px 20px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #2a2a4a;
}

/* 对话框 */
.api-key-dialog :deep(.el-dialog) {
  background: #1f1f35;
  border: 1px solid #2a2a4a;
  border-radius: 12px;
}

.api-key-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid #2a2a4a;
  padding: 20px 24px;
  margin-right: 0;
}

.api-key-dialog :deep(.el-dialog__title) {
  color: #e0e0e0;
  font-weight: 600;
}

.api-key-dialog :deep(.el-dialog__body) {
  padding: 24px;
}

.api-key-dialog :deep(.el-dialog__footer) {
  border-top: 1px solid #2a2a4a;
  padding: 16px 24px;
}

.api-key-form :deep(.el-form-item__label) {
  color: #a0a0c0;
}

.api-key-form :deep(.el-input__wrapper),
.api-key-form :deep(.el-textarea__inner),
.api-key-form :deep(.el-input-number__decrease),
.api-key-form :deep(.el-input-number__increase) {
  background: #16162a;
  border-color: #2a2a4a;
  color: #e0e0e0;
}

.api-key-form :deep(.el-input__inner),
.api-key-form :deep(.el-textarea__inner) {
  color: #e0e0e0;
}

.full-width {
  width: 100%;
}

.rate-input {
  width: 160px;
}

.unit-text {
  margin-left: 8px;
  color: #8888aa;
  font-size: 13px;
}

/* 新建密钥展示 */
.new-key-dialog .key-warning {
  margin-bottom: 20px;
  background: rgba(230, 162, 60, 0.1);
  border: 1px solid rgba(230, 162, 60, 0.3);
}

.warning-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.new-key-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #16162a;
  border-radius: 8px;
  border: 1px solid #2a2a4a;
}

.new-key-code {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: #67c23a;
  word-break: break-all;
  line-height: 1.6;
  text-align: center;
}

.copy-btn {
  min-width: 120px;
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

  .search-input,
  .status-filter {
    width: 100%;
  }

  .toolbar-right {
    width: 100%;
  }

  .toolbar-right .el-button {
    width: 100%;
  }
}
</style>
