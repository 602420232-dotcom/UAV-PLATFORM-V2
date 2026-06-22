<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { tenantApi } from '@/api/tenant'
import type { Tenant } from '@/api/tenant'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatDateTime } from '@/utils/format'
import { useDemoModeStore } from '@/stores/demoMode'

const router = useRouter()
const demoModeStore = useDemoModeStore()

const loading = ref(false)
const tenants = ref<Tenant[]>([])
const total = ref(0)

const queryParams = reactive({
  current: 1,
  size: 10,
})

// 创建租户对话框
const createDialogVisible = ref(false)
const createFormRef = ref()
const createForm = reactive({
  name: '',
  schemaName: '',
  quotaConfig: '',
})
const createRules = {
  name: [{ required: true, message: '请输入租户名称', trigger: 'blur' }],
  schemaName: [{ required: true, message: '请输入 Schema 名称', trigger: 'blur' }],
}

async function loadTenants() {
  loading.value = true
  try {
    if (demoModeStore.isDemoMode) {
      tenants.value = [
        { id: 1, name: '默认租户', schemaName: 'tenant_default', status: 1, quotaConfig: '{"quota": 100}', createdAt: '2025-01-01T00:00:00Z', updatedAt: '2025-06-01T00:00:00Z' } as Tenant,
        { id: 2, name: '气象服务中心', schemaName: 'tenant_weather', status: 1, quotaConfig: '{"quota": 200}', createdAt: '2025-02-15T08:00:00Z', updatedAt: '2025-05-20T10:00:00Z' } as Tenant,
        { id: 3, name: '科研院所', schemaName: 'tenant_research', status: 1, quotaConfig: '{"quota": 150}', createdAt: '2025-03-10T09:00:00Z', updatedAt: '2025-06-10T14:00:00Z' } as Tenant,
        { id: 4, name: '应急救援队', schemaName: 'tenant_emergency', status: 0, quotaConfig: '{"quota": 80}', createdAt: '2025-04-20T11:30:00Z', updatedAt: '2025-05-15T16:00:00Z' } as Tenant,
      ] as Tenant[]
      total.value = tenants.value.length
      return
    }
    const data = await tenantApi.list(queryParams.current, queryParams.size)
    tenants.value = data.records
    total.value = data.total
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

function handlePageChange(page: number) {
  queryParams.current = page
  loadTenants()
}

function handleSizeChange(size: number) {
  queryParams.size = size
  queryParams.current = 1
  loadTenants()
}

function handleCreate() {
  createDialogVisible.value = true
}

async function submitCreate() {
  const valid = await createFormRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    await tenantApi.create(createForm)
    ElMessage.success('租户创建成功')
    createDialogVisible.value = false
    createFormRef.value?.resetFields()
    loadTenants()
  } catch {
    // 错误已在拦截器中处理
  }
}

function handleDetail(row: Tenant) {
  router.push(`/tenants/${row.id}`)
}

async function handleToggleStatus(row: Tenant) {
  const action = row.status === 1 ? 'disable' : 'enable'
  const actionText = row.status === 1 ? '禁用' : '启用'

  try {
    await ElMessageBox.confirm(`确定要${actionText}租户 "${row.name}" 吗？`, '确认操作', {
      type: 'warning',
    })
    if (action === 'disable') {
      await tenantApi.disable(row.id)
    } else {
      await tenantApi.enable(row.id)
    }
    ElMessage.success(`${actionText}成功`)
    loadTenants()
  } catch {
    // 用户取消或请求失败
  }
}

async function handleDelete(row: Tenant) {
  try {
    await ElMessageBox.confirm(
      `确定要删除租户 "${row.name}" 吗？此操作不可恢复。`,
      '确认删除',
      { type: 'error' }
    )
    await tenantApi.remove(row.id)
    ElMessage.success('删除成功')
    loadTenants()
  } catch {
    // 用户取消或请求失败
  }
}

onMounted(async () => {
  await demoModeStore.fetchStatus()
  loadTenants()
})

watch(() => demoModeStore.isDemoMode, () => {
  loadTenants()
})
</script>

<template>
  <div class="tenant-list-page">
    <div class="page-header">
      <h2>租户管理</h2>
      <el-button type="primary" :disabled="demoModeStore.isDemoMode" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        新建租户
      </el-button>
    </div>

    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="tenants"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="租户名称" min-width="150" />
        <el-table-column prop="schemaName" label="Schema" min-width="120" />
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
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleDetail(row)">
              详情
            </el-button>
            <el-button
              :type="row.status === 1 ? 'warning' : 'success'"
              link
              size="small"
              :disabled="demoModeStore.isDemoMode"
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 1 ? '禁用' : '启用' }}
            </el-button>
            <el-button type="danger" link size="small" :disabled="demoModeStore.isDemoMode" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="queryParams.current"
          v-model:page-size="queryParams.size"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>

    <!-- 创建租户对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建租户"
      width="500px"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="100px"
      >
        <el-form-item label="租户名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入租户名称" />
        </el-form-item>
        <el-form-item label="Schema" prop="schemaName">
          <el-input v-model="createForm.schemaName" placeholder="请输入数据库 Schema 名称" />
        </el-form-item>
        <el-form-item label="配额配置" prop="quotaConfig">
          <el-input
            v-model="createForm.quotaConfig"
            type="textarea"
            :rows="3"
            placeholder="JSON 格式配额配置（可选）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreate">确认创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.tenant-list-page {
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

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
