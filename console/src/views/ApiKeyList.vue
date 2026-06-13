<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { apiKeyApi } from '@/api/apiKey'
import type { ApiKey } from '@/api/apiKey'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatDateTime, maskApiKey } from '@/utils/format'

const loading = ref(false)
const apiKeys = ref<ApiKey[]>([])

// 创建 API Key 对话框
const createDialogVisible = ref(false)
const createFormRef = ref()
const createForm = reactive({
  tenantId: 0,
  name: '',
  rateLimit: undefined as number | undefined,
  expiresInDays: undefined as number | undefined,
})
const createRules = {
  tenantId: [{ required: true, message: '请输入租户 ID', trigger: 'blur' }],
  name: [{ required: true, message: '请输入 Key 名称', trigger: 'blur' }],
}

// 新创建的 Key（用于展示完整 key/secret）
const newKey = ref<ApiKey | null>(null)
const showKeyDialogVisible = ref(false)

async function loadApiKeys() {
  loading.value = true
  try {
    // 如果有租户上下文，按租户加载；否则展示所有
    // 此处默认加载租户 ID=1 的 keys（实际应根据 authStore.currentTenantId）
    const tenantId = createForm.tenantId || 1
    apiKeys.value = await apiKeyApi.listByTenant(tenantId)
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

function handleCreate() {
  createForm.tenantId = 1 // 默认租户，实际应从 authStore 获取
  createForm.name = ''
  createForm.rateLimit = undefined
  createForm.expiresInDays = undefined
  createDialogVisible.value = true
}

async function submitCreate() {
  const valid = await createFormRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    const data = await apiKeyApi.generate(createForm)
    newKey.value = data
    createDialogVisible.value = false
    showKeyDialogVisible.value = true
    loadApiKeys()
  } catch {
    // 错误已在拦截器中处理
  }
}

async function handleToggleStatus(row: ApiKey) {
  const action = row.status === 1 ? 'disable' : 'enable'
  const actionText = row.status === 1 ? '禁用' : '启用'

  try {
    await ElMessageBox.confirm(`确定要${actionText}此 API Key 吗？`, '确认操作', { type: 'warning' })
    if (action === 'disable') {
      await apiKeyApi.disable(row.id)
    } else {
      await apiKeyApi.enable(row.id)
    }
    ElMessage.success(`${actionText}成功`)
    loadApiKeys()
  } catch {
    // 用户取消
  }
}

async function handleDelete(row: ApiKey) {
  try {
    await ElMessageBox.confirm(
      `确定要删除 API Key "${row.name}" 吗？删除后所有使用此 Key 的请求将失效。`,
      '确认删除',
      { type: 'error' }
    )
    await apiKeyApi.remove(row.id)
    ElMessage.success('删除成功')
    loadApiKeys()
  } catch {
    // 用户取消
  }
}

async function copyToClipboard(text: string, label: string) {
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success(`${label}已复制到剪贴板`)
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

onMounted(() => {
  loadApiKeys()
})
</script>

<template>
  <div class="api-key-list-page">
    <div class="page-header">
      <h2>API Key 管理</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        创建 API Key
      </el-button>
    </div>

    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="apiKeys"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="keyValue" label="API Key" min-width="200">
          <template #default="{ row }">
            <code class="key-value">{{ maskApiKey(row.keyValue) }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <StatusBadge :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column prop="rateLimit" label="速率限制" width="100">
          <template #default="{ row }">
            {{ row.rateLimit ? `${row.rateLimit}/min` : '无限制' }}
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column prop="expiresAt" label="过期时间" width="180">
          <template #default="{ row }">
            {{ row.expiresAt ? formatDateTime(row.expiresAt) : '永不过期' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              :type="row.status === 1 ? 'warning' : 'success'"
              link
              size="small"
              @click="handleToggleStatus(row)"
            >
              {{ row.status === 1 ? '禁用' : '启用' }}
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建 API Key 对话框 -->
    <el-dialog v-model="createDialogVisible" title="创建 API Key" width="500px">
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="100px"
      >
        <el-form-item label="租户 ID" prop="tenantId">
          <el-input-number v-model="createForm.tenantId" :min="1" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入 Key 名称，如：生产环境" />
        </el-form-item>
        <el-form-item label="速率限制">
          <el-input-number
            v-model="createForm.rateLimit"
            :min="0"
            :step="10"
            placeholder="0 表示无限制"
          />
          <span class="form-tip">次/分钟（0 表示无限制）</span>
        </el-form-item>
        <el-form-item label="有效期">
          <el-input-number
            v-model="createForm.expiresInDays"
            :min="0"
            :step="30"
            placeholder="0 表示永不过期"
          />
          <span class="form-tip">天（0 表示永不过期）</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 新 Key 展示对话框 -->
    <el-dialog v-model="showKeyDialogVisible" title="API Key 创建成功" width="550px">
      <el-alert
        title="请立即保存以下信息，Secret 仅显示一次！"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      />
      <div v-if="newKey" class="key-display">
        <div class="key-item">
          <label>API Key:</label>
          <div class="key-value-row">
            <code>{{ newKey.keyValue }}</code>
            <el-button size="small" @click="copyToClipboard(newKey.keyValue, 'API Key')">
              复制
            </el-button>
          </div>
        </div>
        <div class="key-item">
          <label>Secret:</label>
          <div class="key-value-row">
            <code>{{ newKey.secret }}</code>
            <el-button size="small" @click="copyToClipboard(newKey.secret, 'Secret')">
              复制
            </el-button>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="showKeyDialogVisible = false">我已保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.api-key-list-page {
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

.key-value {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: var(--color-accent-light);
  background-color: var(--color-bg);
  padding: 2px 6px;
  border-radius: 3px;
}

.form-tip {
  margin-left: 8px;
  color: var(--color-text-muted);
  font-size: 12px;
}

.key-display {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.key-item label {
  display: block;
  margin-bottom: 6px;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.key-value-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.key-value-row code {
  flex: 1;
  padding: 8px 12px;
  background-color: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: var(--color-text-primary);
  word-break: break-all;
}
</style>
