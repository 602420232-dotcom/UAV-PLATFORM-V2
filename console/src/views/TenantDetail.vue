<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { tenantApi } from '@/api/tenant'
import { apiKeyApi } from '@/api/apiKey'
import type { Tenant } from '@/api/tenant'
import type { ApiKey } from '@/api/apiKey'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatDateTime, maskApiKey } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const tenantId = Number(route.params.id)
const loading = ref(false)
const tenant = ref<Tenant | null>(null)
const apiKeys = ref<ApiKey[]>([])

// 编辑对话框
const editDialogVisible = ref(false)
const editForm = ref({
  name: '',
  quotaConfig: '',
})

async function loadTenant() {
  loading.value = true
  try {
    const [tenantData, keysData] = await Promise.all([
      tenantApi.getById(tenantId),
      apiKeyApi.listByTenant(tenantId),
    ])
    tenant.value = tenantData
    apiKeys.value = keysData
  } catch {
    ElMessage.error('加载租户信息失败')
  } finally {
    loading.value = false
  }
}

function handleEdit() {
  if (!tenant.value) return
  editForm.value = {
    name: tenant.value.name,
    quotaConfig: tenant.value.quotaConfig || '',
  }
  editDialogVisible.value = true
}

async function submitEdit() {
  try {
    await tenantApi.update(tenantId, editForm.value)
    ElMessage.success('更新成功')
    editDialogVisible.value = false
    loadTenant()
  } catch {
    // 错误已在拦截器中处理
  }
}

async function handleToggleStatus() {
  if (!tenant.value) return
  const action = tenant.value.status === 1 ? 'disable' : 'enable'
  const actionText = tenant.value.status === 1 ? '禁用' : '启用'

  try {
    await ElMessageBox.confirm(`确定要${actionText}此租户吗？`, '确认操作', { type: 'warning' })
    if (action === 'disable') {
      await tenantApi.disable(tenantId)
    } else {
      await tenantApi.enable(tenantId)
    }
    ElMessage.success(`${actionText}成功`)
    loadTenant()
  } catch {
    // 用户取消
  }
}

async function handleDelete() {
  if (!tenant.value) return
  try {
    await ElMessageBox.confirm(
      `确定要删除租户 "${tenant.value.name}" 吗？此操作不可恢复。`,
      '确认删除',
      { type: 'error' }
    )
    await tenantApi.remove(tenantId)
    ElMessage.success('删除成功')
    router.push('/tenants')
  } catch {
    // 用户取消
  }
}

function goBack() {
  router.push('/tenants')
}

onMounted(() => {
  loadTenant()
})
</script>

<template>
  <div v-loading="loading" class="tenant-detail-page">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <h2>租户详情</h2>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleEdit">
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
        <el-button
          :type="tenant?.status === 1 ? 'warning' : 'success'"
          @click="handleToggleStatus"
        >
          {{ tenant?.status === 1 ? '禁用' : '启用' }}
        </el-button>
        <el-button type="danger" @click="handleDelete">
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
      </div>
    </div>

    <!-- 租户基本信息 -->
    <el-card v-if="tenant" class="info-card">
      <template #header>
        <span>基本信息</span>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="ID">{{ tenant.id }}</el-descriptions-item>
        <el-descriptions-item label="租户名称">{{ tenant.name }}</el-descriptions-item>
        <el-descriptions-item label="Schema">{{ tenant.schemaName }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <StatusBadge :status="tenant.status" />
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDateTime(tenant.createdAt) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDateTime(tenant.updatedAt) }}</el-descriptions-item>
        <el-descriptions-item label="配额配置" :span="2">
          <pre class="quota-config">{{ tenant.quotaConfig || '无' }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- API Key 列表 -->
    <el-card class="keys-card">
      <template #header>
        <div class="flex-between">
          <span>API Keys ({{ apiKeys.length }})</span>
        </div>
      </template>
      <el-table :data="apiKeys" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="keyValue" label="API Key" min-width="180">
          <template #default="{ row }">
            <code>{{ maskApiKey(row.keyValue) }}</code>
          </template>
        </el-table-column>
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
      </el-table>
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑租户" width="500px">
      <el-form label-width="100px">
        <el-form-item label="租户名称">
          <el-input v-model="editForm.name" />
        </el-form-item>
        <el-form-item label="配额配置">
          <el-input v-model="editForm.quotaConfig" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.tenant-detail-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.header-right {
  display: flex;
  gap: 8px;
}

.info-card,
.keys-card {
  border-radius: 8px;
}

.quota-config {
  margin: 0;
  padding: 8px;
  background-color: var(--color-bg);
  border-radius: 4px;
  font-size: 12px;
  color: var(--color-text-secondary);
  max-height: 200px;
  overflow-y: auto;
}
</style>
