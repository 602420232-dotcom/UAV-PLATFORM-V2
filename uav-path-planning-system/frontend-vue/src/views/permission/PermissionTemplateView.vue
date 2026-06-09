<template>
  <div class="permission-template-view">
    <div class="page-header">
      <h2 class="page-title">权限模板与临时授权</h2>
      <el-tag size="default" effect="dark" type="warning">管理员专属</el-tag>
    </div>

    <el-row :gutter="16" class="main-row">
      <!-- 左列：模板列表 -->
      <el-col :span="6" class="col col-left">
        <el-card shadow="hover" class="panel">
          <template #header>
            <div class="panel-head">
              <span class="panel-title">权限模板</span>
              <el-button type="primary" size="small" @click="onCreateBlank">
                <el-icon><Plus /></el-icon>&nbsp;新建
              </el-button>
            </div>
          </template>

          <el-form :inline="true" size="small" class="filter-form">
            <el-form-item label="角色过滤">
              <el-select v-model="roleFilter" placeholder="全部" clearable style="width: 100%">
                <el-option
                  v-for="opt in tplStore.roleOptions"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>
            </el-form-item>
          </el-form>

          <el-table
            :data="filteredTemplates"
            size="small"
            height="520"
            highlight-current-row
            @current-change="onSelectTemplate"
            class="template-table"
            stripe
          >
            <el-table-column label="名称" min-width="140">
              <template #default="{ row }">
                <div class="tpl-name">
                  <span>{{ row.name }}</span>
                  <el-tag v-if="row.isSystem" size="small" type="info" effect="plain" class="tag-sys">系统</el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="角色" width="88" align="center">
              <template #default="{ row }">{{ roleLabel(row.role) }}</template>
            </el-table-column>
            <el-table-column label="路由" width="64" align="center">
              <template #default="{ row }">{{ row.routes?.length || 0 }}</template>
            </el-table-column>
            <el-table-column label="动作" width="64" align="center">
              <template #default="{ row }">{{ row.actions?.length || 0 }}</template>
            </el-table-column>
            <el-table-column label="操作" width="128" align="center" fixed="right">
              <template #default="{ row }">
                <el-button
                  link
                  type="primary"
                  size="small"
                  @click.stop="onDuplicate(row)"
                >复制</el-button>
                <el-popconfirm
                  :disabled="row.isSystem"
                  title="确认删除该模板？"
                  @confirm="onDelete(row)"
                >
                  <template #reference>
                    <el-button
                      link
                      type="danger"
                      size="small"
                      :disabled="row.isSystem"
                    >删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 中列：模板编辑区 -->
      <el-col :span="11" class="col col-middle">
        <el-card shadow="hover" class="panel">
          <template #header>
            <div class="panel-head">
              <span class="panel-title">
                {{ currentId ? '编辑模板' : '未选中模板' }}
              </span>
              <div class="panel-actions">
                <el-button size="small" :disabled="!currentId" @click="onDuplicateCurrent">复制模板</el-button>
                <el-button type="primary" size="small" :disabled="!currentId || !isDirty" @click="onSave">保存</el-button>
                <el-button type="success" size="small" :disabled="!currentId" @click="openCreateUserDialog">
                  <el-icon><UserFilled /></el-icon>&nbsp;新建用户
                </el-button>
              </div>
            </div>
          </template>

          <div v-if="!currentId" class="empty-tip">
            <el-empty description="请在左侧选择一个模板，或点击「新建」创建一个新模板" />
          </div>

          <el-form v-else size="small" label-width="90px" class="edit-form">
            <el-form-item label="名称">
              <el-input v-model="draft.name" placeholder="请输入模板名称" />
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="draft.description" type="textarea" :rows="2" placeholder="可选" />
            </el-form-item>
            <el-form-item label="所属角色">
              <el-select v-model="draft.role" style="width: 100%">
                <el-option
                  v-for="opt in tplStore.roleOptions"
                  :key="opt.value"
                  :label="opt.label"
                  :value="opt.value"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="路由权限">
              <div class="checkbox-group-wrap">
                <el-checkbox
                  :model-value="allRoutesChecked"
                  :indeterminate="partialRoutesChecked"
                  @change="onToggleAllRoutes"
                >全选</el-checkbox>
                <el-divider direction="vertical" />
                <el-checkbox-group v-model="draft.routes">
                  <el-checkbox
                    v-for="r in tplStore.availableRoutes"
                    :key="r.key"
                    :label="r.key"
                  >{{ r.label }}</el-checkbox>
                </el-checkbox-group>
              </div>
            </el-form-item>

            <el-form-item label="动作权限">
              <div class="checkbox-group-wrap">
                <el-checkbox
                  :model-value="allActionsChecked"
                  :indeterminate="partialActionsChecked"
                  @change="onToggleAllActions"
                >全选</el-checkbox>
                <el-divider direction="vertical" />
                <el-checkbox-group v-model="draft.actions">
                  <el-checkbox
                    v-for="a in tplStore.availableActions"
                    :key="a.key"
                    :label="a.key"
                  >{{ a.label }}</el-checkbox>
                </el-checkbox-group>
              </div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右列：临时授权区 -->
      <el-col :span="7" class="col col-right">
        <el-card shadow="hover" class="panel">
          <template #header>
            <div class="panel-head">
              <span class="panel-title">临时授权</span>
              <el-button type="primary" size="small" @click="openGrantDialog">
                <el-icon><Plus /></el-icon>&nbsp;新增授权
              </el-button>
            </div>
          </template>

          <el-table
            :data="tplStore.temporaryGrants"
            size="small"
            height="560"
            class="grant-table"
            stripe
          >
            <el-table-column label="用户" min-width="110">
              <template #default="{ row }">
                <span :class="{ 'strikethrough': !row.active }">{{ row.username }}</span>
              </template>
            </el-table-column>
            <el-table-column label="角色" width="80" align="center">
              <template #default="{ row }">
                <span :class="{ 'strikethrough': !row.active }">{{ roleLabel(row.role) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="过期时间" width="150" align="center">
              <template #default="{ row }">
                <span :class="{ 'strikethrough': !row.active }">{{ formatTime(row.expireAt) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="72" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.active ? 'success' : 'info'" effect="plain">
                  {{ row.active ? '生效中' : '已失效' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80" align="center" fixed="right">
              <template #default="{ row }">
                <el-button link type="danger" size="small" :disabled="!row.active" @click="onRevoke(row)">撤销</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新建用户对话框 -->
    <el-dialog v-model="createUserVisible" title="基于模板创建用户" width="480px">
      <el-form :model="createUserForm" label-width="90px" size="small">
        <el-form-item label="用户名">
          <el-input v-model="createUserForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="createUserForm.password" type="password" show-password placeholder="演示环境可任意填写" />
        </el-form-item>
        <el-form-item label="基于模板">
          <el-tag type="info" effect="plain">{{ currentTemplate?.name }}</el-tag>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createUserVisible = false">取消</el-button>
        <el-button type="primary" @click="onCreateUser">创建</el-button>
      </template>
    </el-dialog>

    <!-- 新增临时授权对话框 -->
    <el-dialog v-model="grantVisible" title="新增临时授权" width="560px">
      <el-form :model="grantForm" label-width="100px" size="small">
        <el-form-item label="用户名">
          <el-input v-model="grantForm.username" placeholder="请输入被授权用户名" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="grantForm.role" style="width: 100%">
            <el-option
              v-for="opt in tplStore.roleOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="有效期(小时)">
          <el-input-number v-model="grantForm.expireHours" :min="1" :max="24 * 30" style="width: 100%" />
        </el-form-item>
        <el-form-item label="路由">
          <el-checkbox-group v-model="grantForm.routes">
            <el-checkbox
              v-for="r in tplStore.availableRoutes"
              :key="r.key"
              :label="r.key"
            >{{ r.label }}</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="动作">
          <el-checkbox-group v-model="grantForm.actions">
            <el-checkbox
              v-for="a in tplStore.availableActions"
              :key="a.key"
              :label="a.key"
            >{{ a.key }}</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="grantVisible = false">取消</el-button>
        <el-button type="primary" @click="onConfirmGrant">确认授权</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, UserFilled } from '@element-plus/icons-vue'
import { usePermissionTemplateStore } from '../../stores/permissionTemplate'
import { ROLE_LABELS, useAuthStore } from '../../stores/auth'

const tplStore = usePermissionTemplateStore()
const authStore = useAuthStore()
const roleFilter = ref('')

const currentId = ref('')
const draft = reactive({
  name: '',
  description: '',
  role: 'user',
  routes: [],
  actions: []
})
const originalSnapshot = ref(null)

const createUserVisible = ref(false)
const createUserForm = reactive({ username: '', password: '' })

const grantVisible = ref(false)
const grantForm = reactive({
  username: '',
  role: 'user',
  expireHours: 24,
  routes: [],
  actions: []
})

onMounted(() => {
  tplStore.init()
  tplStore.syncFromAuthStore()
  if (tplStore.templates.length) {
    onSelectTemplate(tplStore.templates[0])
  }
})

const filteredTemplates = computed(() => {
  if (!roleFilter.value) return tplStore.templates
  return tplStore.templates.filter((t) => t.role === roleFilter.value)
})

const currentTemplate = computed(() =>
  tplStore.templates.find((t) => t.id === currentId.value) || null
)

const allRouteKeys = computed(() => tplStore.availableRoutes.map((r) => r.key))
const allActionKeys = computed(() => tplStore.availableActions.map((a) => a.key))

const allRoutesChecked = computed(() =>
  draft.routes.length > 0 && draft.routes.length === allRouteKeys.value.length
)
const partialRoutesChecked = computed(() =>
  draft.routes.length > 0 && draft.routes.length < allRouteKeys.value.length
)
const allActionsChecked = computed(() =>
  draft.actions.length > 0 && draft.actions.length === allActionKeys.value.length
)
const partialActionsChecked = computed(() =>
  draft.actions.length > 0 && draft.actions.length < allActionKeys.value.length
)

const isDirty = computed(() => {
  if (!originalSnapshot.value) return true
  const o = originalSnapshot.value
  return (
    o.name !== draft.name ||
    o.description !== draft.description ||
    o.role !== draft.role ||
    JSON.stringify([...o.routes].sort()) !== JSON.stringify([...draft.routes].sort()) ||
    JSON.stringify([...o.actions].sort()) !== JSON.stringify([...draft.actions].sort())
  )
})

function roleLabel(role) {
  return ROLE_LABELS[role] || role
}

function formatTime(ts) {
  if (!ts) return '-'
  const d = new Date(ts)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function onSelectTemplate(row) {
  if (!row) return
  currentId.value = row.id
  draft.name = row.name
  draft.description = row.description
  draft.role = row.role
  draft.routes = [...(row.routes || [])]
  draft.actions = [...(row.actions || [])]
  originalSnapshot.value = {
    name: row.name,
    description: row.description,
    role: row.role,
    routes: [...(row.routes || [])],
    actions: [...(row.actions || [])]
  }
}

function onToggleAllRoutes(checked) {
  draft.routes = checked ? [...allRouteKeys.value] : []
}
function onToggleAllActions(checked) {
  draft.actions = checked ? [...allActionKeys.value] : []
}

function onCreateBlank() {
  const tpl = tplStore.addTemplate('新权限模板', '', 'user', ['dashboard', 'weather'], [])
  currentId.value = tpl.id
  onSelectTemplate(tpl)
  ElMessage.success('已创建新模板，请在右侧编辑并保存')
}

function onDuplicate(row) {
  const copy = tplStore.duplicateTemplate(row.id)
  if (copy) {
    currentId.value = copy.id
    onSelectTemplate(copy)
    ElMessage.success('复制成功')
  }
}

function onDuplicateCurrent() {
  if (!currentId.value) return
  onDuplicate(currentTemplate.value)
}

function onDelete(row) {
  if (row.isSystem) {
    ElMessage.warning('系统模板不可删除')
    return
  }
  tplStore.deleteTemplate(row.id)
  if (currentId.value === row.id) {
    currentId.value = ''
    originalSnapshot.value = null
  }
  ElMessage.success('已删除')
}

function onSave() {
  if (!currentId.value) return
  tplStore.updateTemplate(currentId.value, {
    name: draft.name || '未命名模板',
    description: draft.description,
    role: draft.role,
    routes: [...draft.routes],
    actions: [...draft.actions]
  })
  originalSnapshot.value = {
    name: draft.name,
    description: draft.description,
    role: draft.role,
    routes: [...draft.routes],
    actions: [...draft.actions]
  }
  ElMessage.success('保存成功')
}

function openCreateUserDialog() {
  if (!currentId.value) return
  createUserForm.username = ''
  createUserForm.password = ''
  createUserVisible.value = true
}

async function onCreateUser() {
  if (!createUserForm.username) {
    ElMessage.warning('请填写用户名')
    return
  }
  const confirmed = await authStore.requireSensitiveConfirmation('新增用户')
  if (!confirmed) return
  try {
    const user = tplStore.createUserFromTemplate(
      currentId.value,
      createUserForm.username,
      createUserForm.password
    )
    ElMessage.success(`已基于模板创建用户：${user.username}`)
    createUserVisible.value = false
  } catch (e) {
    ElMessage.error(e?.message || '创建失败')
  }
}

function openGrantDialog() {
  grantForm.username = ''
  grantForm.role = 'user'
  grantForm.expireHours = 24
  grantForm.routes = []
  grantForm.actions = []
  grantVisible.value = true
}

function onConfirmGrant() {
  if (!grantForm.username) {
    ElMessage.warning('请填写用户名')
    return
  }
  tplStore.grantTemporary({
    username: grantForm.username,
    role: grantForm.role,
    routes: [...grantForm.routes],
    actions: [...grantForm.actions],
    expireHours: grantForm.expireHours
  })
  ElMessage.success('已创建临时授权')
  grantVisible.value = false
}

function onRevoke(row) {
  ElMessageBox.confirm(`确认撤销对「${row.username}」的临时授权？`, '提示', {
    confirmButtonText: '撤销',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(() => {
      tplStore.revokeTemporary(row.id)
      ElMessage.success('已撤销')
    })
    .catch(() => {})
}

watch(
  () => tplStore.templates,
  () => {
    const stillExists = tplStore.templates.find((t) => t.id === currentId.value)
    if (!stillExists && tplStore.templates.length) {
      onSelectTemplate(tplStore.templates[0])
    }
  },
  { deep: true }
)
</script>

<style scoped>
.permission-template-view {
  padding: 16px;
  background: #f5f7fa;
  min-height: 100%;
  font-size: 13px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.main-row {
  display: flex;
}

.col-left .panel,
.col-middle .panel,
.col-right .panel {
  margin-bottom: 12px;
}
.panel {
  border-radius: 8px;
  transition: box-shadow 0.2s;
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.panel-title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}
.panel-actions {
  display: flex;
  gap: 8px;
}

.filter-form {
  margin-bottom: 8px;
}

.tpl-name {
  display: flex;
  align-items: center;
  gap: 6px;
}
.tag-sys {
  margin-left: 4px;
}

.empty-tip {
  padding: 40px 0;
}

.edit-form .checkbox-group-wrap {
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 6px 16px;
  padding: 8px;
  background: #fafafa;
  border-radius: 6px;
  border: 1px solid #ebeef5;
  min-height: 44px;
}

.strikethrough {
  text-decoration: line-through;
  color: #909399;
}

.grant-table,
.template-table {
  width: 100%;
}
</style>
