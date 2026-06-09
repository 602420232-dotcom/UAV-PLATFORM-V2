<template>
  <div class="permission-template-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">
          <el-icon><Key /></el-icon>权限管理
        </h2>
        <el-tag size="small" effect="dark" type="warning">管理员专属</el-tag>
      </div>
      <div class="header-actions">
        <el-button type="primary" size="small" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>新建模板
        </el-button>
        <el-button size="small" @click="openImportDialog">
          <el-icon><Upload /></el-icon>导入
        </el-button>
        <el-button size="small" @click="exportTemplates">
          <el-icon><Download /></el-icon>导出
        </el-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧：模板列表 -->
      <div class="template-list-panel">
        <div class="panel-header">
          <span class="panel-title">权限模板</span>
          <el-input
            v-model="templateSearch"
            placeholder="搜索模板..."
            size="small"
            clearable
            style="width: 140px"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
        </div>

        <!-- 角色筛选标签 -->
        <div class="role-filter-tags">
          <el-tag
            v-for="opt in tplStore.roleOptions"
            :key="opt.value"
            :type="roleFilter === opt.value ? 'primary' : 'info'"
            size="small"
            class="role-tag"
            @click="toggleRoleFilter(opt.value)"
          >
            {{ opt.label }}
          </el-tag>
          <el-tag
            v-if="roleFilter"
            type="info"
            size="small"
            class="clear-tag"
            @click="roleFilter = ''"
          >
            <el-icon><Close /></el-icon>清除
          </el-tag>
        </div>

        <!-- 模板卡片列表 -->
        <div class="template-cards">
          <div
            v-for="tpl in filteredTemplates"
            :key="tpl.id"
            class="template-card"
            :class="{ 'is-active': currentId === tpl.id }"
            @click="onSelectTemplate(tpl)"
          >
            <div class="card-header">
              <span class="card-name">{{ tpl.name }}</span>
              <el-tag v-if="tpl.isSystem" size="small" type="info" effect="plain">系统</el-tag>
            </div>
            <div class="card-meta">
              <span class="meta-item">
                <el-icon><User /></el-icon>
                {{ roleLabel(tpl.role) }}
              </span>
              <span class="meta-item">
                <el-icon><Guide /></el-icon>
                {{ tpl.routes?.length || 0 }} 路由
              </span>
              <span class="meta-item">
                <el-icon><Operation /></el-icon>
                {{ tpl.actions?.length || 0 }} 动作
              </span>
            </div>
            <div class="card-actions" @click.stop>
              <el-button link type="primary" size="small" @click="onDuplicate(tpl)">复制</el-button>
              <el-button link type="success" size="small" @click="onApplyToUser(tpl)">应用</el-button>
              <el-popconfirm
                v-if="!tpl.isSystem"
                title="确认删除该模板？"
                @confirm="onDelete(tpl)"
              >
                <template #reference>
                  <el-button link type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </div>

          <el-empty
            v-if="filteredTemplates.length === 0"
            description="暂无模板"
            :image-size="80"
          />
        </div>
      </div>

      <!-- 右侧：编辑/授权区 -->
      <div class="edit-panel">
        <el-tabs v-model="activeTab" class="main-tabs">
          <!-- 模板编辑 -->
          <el-tab-pane label="模板编辑" name="edit">
            <template #label>
              <el-icon><Edit /></el-icon> 模板编辑
            </template>

            <div v-if="!currentId" class="empty-state">
              <el-empty description="请在左侧选择一个模板进行编辑">
                <el-button type="primary" @click="openCreateDialog">
                  <el-icon><Plus /></el-icon>新建模板
                </el-button>
              </el-empty>
            </div>

            <div v-else class="edit-content">
              <!-- 基本信息 -->
              <el-card shadow="never" class="info-card">
                <template #header>
                  <div class="card-header-row">
                    <span class="card-title">基本信息</span>
                    <el-tag v-if="isDirty" type="warning" size="small">已修改</el-tag>
                  </div>
                </template>
                <el-form :model="draft" size="small" label-width="80px">
                  <el-form-item label="模板名称">
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
                </el-form>
              </el-card>

              <!-- 路由权限 -->
              <el-card shadow="never" class="permission-card">
                <template #header>
                  <div class="card-header-row">
                    <span class="card-title">路由权限</span>
                    <div class="header-right">
                      <el-checkbox
                        :model-value="allRoutesChecked"
                        :indeterminate="partialRoutesChecked"
                        @change="onToggleAllRoutes"
                      >全选</el-checkbox>
                      <span class="count-badge">{{ draft.routes.length }}/{{ allRouteKeys.length }}</span>
                    </div>
                  </div>
                </template>
                <div class="permission-groups">
                  <el-checkbox-group v-model="draft.routes" class="permission-list">
                    <el-checkbox
                      v-for="r in tplStore.availableRoutes"
                      :key="r.key"
                      :value="r.key"
                      class="permission-item"
                    >
                      <span class="perm-label">{{ r.label }}</span>
                      <span class="perm-key">{{ r.key }}</span>
                    </el-checkbox>
                  </el-checkbox-group>
                </div>
              </el-card>

              <!-- 动作权限 -->
              <el-card shadow="never" class="permission-card">
                <template #header>
                  <div class="card-header-row">
                    <span class="card-title">动作权限</span>
                    <div class="header-right">
                      <el-checkbox
                        :model-value="allActionsChecked"
                        :indeterminate="partialActionsChecked"
                        @change="onToggleAllActions"
                      >全选</el-checkbox>
                      <span class="count-badge">{{ draft.actions.length }}/{{ allActionKeys.length }}</span>
                    </div>
                  </div>
                </template>
                <div class="permission-groups">
                  <el-checkbox-group v-model="draft.actions" class="permission-list">
                    <el-checkbox
                      v-for="a in tplStore.availableActions"
                      :key="a.key"
                      :value="a.key"
                      class="permission-item"
                    >
                      <span class="perm-label">{{ a.label }}</span>
                      <span class="perm-key">{{ a.key }}</span>
                    </el-checkbox>
                  </el-checkbox-group>
                </div>
              </el-card>

              <!-- 操作按钮 -->
              <div class="action-buttons">
                <el-button @click="onReset">重置</el-button>
                <el-button type="primary" :disabled="!isDirty" @click="onSave">
                  <el-icon><Check /></el-icon>保存
                </el-button>
              </div>
            </div>
          </el-tab-pane>

          <!-- 临时授权 -->
          <el-tab-pane label="临时授权" name="grant">
            <template #label>
              <el-icon><Timer /></el-icon> 临时授权
              <el-badge v-if="activeGrantCount > 0" :value="activeGrantCount" class="grant-badge" />
            </template>

            <div class="grant-content">
              <div class="grant-header">
                <el-button type="primary" @click="openGrantDialog">
                  <el-icon><Plus /></el-icon>新增授权
                </el-button>
                <el-select v-model="grantFilter" placeholder="状态筛选" clearable size="small" style="width: 120px">
                  <el-option label="生效中" value="active" />
                  <el-option label="已失效" value="inactive" />
                </el-select>
              </div>

              <el-table :data="filteredGrants" size="small" class="grant-table">
                <el-table-column label="用户" prop="username" min-width="100" />
                <el-table-column label="角色" width="80" align="center">
                  <template #default="{ row }">{{ roleLabel(row.role) }}</template>
                </el-table-column>
                <el-table-column label="有效期" width="160" align="center">
                  <template #default="{ row }">
                    <span :class="{ 'text-muted': !row.active }">{{ formatTime(row.expireAt) }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="80" align="center">
                  <template #default="{ row }">
                    <el-tag size="small" :type="row.active ? 'success' : 'info'" effect="plain">
                      {{ row.active ? '生效中' : '已失效' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="80" align="center" fixed="right">
                  <template #default="{ row }">
                    <el-button link type="danger" size="small" :disabled="!row.active" @click="onRevoke(row)">
                      撤销
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <!-- 新建模板对话框 -->
    <el-dialog v-model="createVisible" title="新建权限模板" width="500px">
      <el-form :model="createForm" label-width="100px" size="default">
        <el-form-item label="模板名称">
          <el-input v-model="createForm.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="2" placeholder="可选" />
        </el-form-item>
        <el-form-item label="所属角色">
          <el-select v-model="createForm.role" style="width: 100%">
            <el-option
              v-for="opt in tplStore.roleOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="onCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 应用到用户对话框 -->
    <el-dialog v-model="applyVisible" title="应用模板到用户" width="480px">
      <el-form :model="applyForm" label-width="100px" size="default">
        <el-form-item label="选择模板">
          <el-tag type="primary">{{ applyForm.templateName }}</el-tag>
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="applyForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="有效期">
          <el-input-number v-model="applyForm.expireHours" :min="1" :max="720" />
          <span class="form-tip">小时</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="applyVisible = false">取消</el-button>
        <el-button type="primary" @click="onConfirmApply">应用</el-button>
      </template>
    </el-dialog>

    <!-- 新增临时授权对话框 -->
    <el-dialog v-model="grantDialogVisible" title="新增临时授权" width="600px">
      <el-form :model="grantForm" label-width="100px" size="default">
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
        <el-form-item label="有效期">
          <el-input-number v-model="grantForm.expireHours" :min="1" :max="720" style="width: 100%" />
        </el-form-item>
        <el-form-item label="路由权限">
          <el-checkbox v-model="grantAllRoutes" @change="onGrantAllRoutesChange">授予全部路由</el-checkbox>
          <div v-if="!grantAllRoutes" class="route-list">
            <el-checkbox-group v-model="grantForm.routes">
              <el-checkbox
                v-for="r in tplStore.availableRoutes"
                :key="r.key"
                :value="r.key"
              >{{ r.label }}</el-checkbox>
            </el-checkbox-group>
          </div>
        </el-form-item>
        <el-form-item label="动作权限">
          <el-checkbox v-model="grantAllActions" @change="onGrantAllActionsChange">授予全部动作</el-checkbox>
          <div v-if="!grantAllActions" class="route-list">
            <el-checkbox-group v-model="grantForm.actions">
              <el-checkbox
                v-for="a in tplStore.availableActions"
                :key="a.key"
                :value="a.key"
              >{{ a.label || a.key }}</el-checkbox>
            </el-checkbox-group>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="grantDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="onConfirmGrant">确认授权</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Key, Search, Close, User, Edit, Timer, Download, Upload,
  Check, Operation, Guide, Timer as TimerIcon
} from '@element-plus/icons-vue'
import { usePermissionTemplateStore } from '../../stores/permissionTemplate'
import { ROLE_LABELS, useAuthStore } from '../../stores/auth'

const tplStore = usePermissionTemplateStore()
const authStore = useAuthStore()

// 状态
const activeTab = ref('edit')
const currentId = ref('')
const templateSearch = ref('')
const roleFilter = ref('')
const grantFilter = ref('')

// 模板草稿
const draft = reactive({
  name: '',
  description: '',
  role: 'user',
  routes: [],
  actions: []
})
const originalSnapshot = ref(null)

// 创建对话框
const createVisible = ref(false)
const createForm = reactive({ name: '', description: '', role: 'user' })

// 应用到用户对话框
const applyVisible = ref(false)
const applyForm = reactive({ templateId: '', templateName: '', username: '', expireHours: 24 })

// 临时授权对话框
const grantDialogVisible = ref(false)
const grantForm = reactive({
  username: '',
  role: 'user',
  expireHours: 24,
  routes: [],
  actions: []
})
const grantAllRoutes = ref(false)
const grantAllActions = ref(false)

// 计算属性
const filteredTemplates = computed(() => {
  let list = tplStore.templates
  if (roleFilter.value) {
    list = list.filter((t) => t.role === roleFilter.value)
  }
  if (templateSearch.value) {
    const kw = templateSearch.value.toLowerCase()
    list = list.filter((t) => t.name.toLowerCase().includes(kw))
  }
  return list
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
  if (!originalSnapshot.value) return false
  const o = originalSnapshot.value
  return (
    o.name !== draft.name ||
    o.description !== draft.description ||
    o.role !== draft.role ||
    JSON.stringify([...o.routes].sort()) !== JSON.stringify([...draft.routes].sort()) ||
    JSON.stringify([...o.actions].sort()) !== JSON.stringify([...draft.actions].sort())
  )
})

const activeGrantCount = computed(() =>
  tplStore.temporaryGrants.filter((g) => g.active).length
)

const filteredGrants = computed(() => {
  let list = tplStore.temporaryGrants
  if (grantFilter.value === 'active') {
    list = list.filter((g) => g.active)
  } else if (grantFilter.value === 'inactive') {
    list = list.filter((g) => !g.active)
  }
  return list
})

// 方法
function roleLabel(role) {
  return ROLE_LABELS[role] || role
}

function formatTime(ts) {
  if (!ts) return '-'
  const d = new Date(ts)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function toggleRoleFilter(role) {
  roleFilter.value = roleFilter.value === role ? '' : role
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
  activeTab.value = 'edit'
}

function onToggleAllRoutes(checked) {
  draft.routes = checked ? [...allRouteKeys.value] : []
}

function onToggleAllActions(checked) {
  draft.actions = checked ? [...allActionKeys.value] : []
}

function onReset() {
  if (originalSnapshot.value) {
    onSelectTemplate(currentTemplate.value)
  }
}

function openCreateDialog() {
  createForm.name = ''
  createForm.description = ''
  createForm.role = 'user'
  createVisible.value = true
}

function onCreate() {
  if (!createForm.name) {
    ElMessage.warning('请输入模板名称')
    return
  }
  const tpl = tplStore.addTemplate(createForm.name, createForm.description, createForm.role, [], [])
  currentId.value = tpl.id
  onSelectTemplate(tpl)
  createVisible.value = false
  ElMessage.success('创建成功')
  activeTab.value = 'edit'
}

function onDuplicate(row) {
  const copy = tplStore.duplicateTemplate(row.id)
  if (copy) {
    currentId.value = copy.id
    onSelectTemplate(copy)
    ElMessage.success('复制成功')
    activeTab.value = 'edit'
  }
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

function onApplyToUser(tpl) {
  applyForm.templateId = tpl.id
  applyForm.templateName = tpl.name
  applyForm.username = ''
  applyForm.expireHours = 24
  applyVisible.value = true
}

async function onConfirmApply() {
  if (!applyForm.username) {
    ElMessage.warning('请输入用户名')
    return
  }
  const confirmed = await authStore.requireSensitiveConfirmation('应用模板到用户')
  if (!confirmed) return

  tplStore.grantTemporary({
    username: applyForm.username,
    role: currentTemplate.value?.role || 'user',
    routes: [...draft.routes],
    actions: [...draft.actions],
    expireHours: applyForm.expireHours
  })

  applyVisible.value = false
  ElMessage.success(`已为 ${applyForm.username} 创建临时授权`)
  activeTab.value = 'grant'
}

function openGrantDialog() {
  grantForm.username = ''
  grantForm.role = 'user'
  grantForm.expireHours = 24
  grantForm.routes = []
  grantForm.actions = []
  grantAllRoutes.value = false
  grantAllActions.value = false
  grantDialogVisible.value = true
}

function onGrantAllRoutesChange(val) {
  grantForm.routes = val ? [...allRouteKeys.value] : []
}

function onGrantAllActionsChange(val) {
  grantForm.actions = val ? [...allActionKeys.value] : []
}

function onConfirmGrant() {
  if (!grantForm.username) {
    ElMessage.warning('请填写用户名')
    return
  }
  if (grantForm.routes.length === 0 && !grantAllRoutes.value) {
    ElMessage.warning('请至少选择一项路由权限')
    return
  }
  tplStore.grantTemporary({
    username: grantForm.username,
    role: grantForm.role,
    routes: grantAllRoutes.value ? [...allRouteKeys.value] : [...grantForm.routes],
    actions: grantAllActions.value ? [...allActionKeys.value] : [...grantForm.actions],
    expireHours: grantForm.expireHours
  })
  ElMessage.success('已创建临时授权')
  grantDialogVisible.value = false
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

function exportTemplates() {
  const data = JSON.stringify(tplStore.templates, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `permission_templates_${Date.now()}.json`
  link.click()
  ElMessage.success('导出成功')
}

function openImportDialog() {
  ElMessage.info('请在弹出窗口中选择 JSON 文件导入')
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = (e) => {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (evt) => {
      try {
        const data = JSON.parse(evt.target.result)
        if (Array.isArray(data)) {
          data.forEach((tpl) => {
            if (tpl.name && tpl.role) {
              tplStore.addTemplate(tpl.name, tpl.description || '', tpl.role, tpl.routes || [], tpl.actions || [])
            }
          })
          ElMessage.success(`成功导入 ${data.length} 个模板`)
        } else {
          ElMessage.error('文件格式错误')
        }
      } catch (err) {
        ElMessage.error('解析文件失败')
      }
    }
    reader.readAsText(file)
  }
  input.click()
}

// 生命周期
onMounted(() => {
  tplStore.init()
  tplStore.syncFromAuthStore()
  if (tplStore.templates.length) {
    onSelectTemplate(tplStore.templates[0])
  }
})

// 监听模板变化
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
  background: var(--color-bg-page, #f5f7fa);
  min-height: 100%;
  font-size: 13px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

/* 主内容区 */
.main-content {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 16px;
  height: calc(100vh - 140px);
}

/* 左侧模板列表 */
.template-list-panel {
  background: var(--color-bg-card, #fff);
  border-radius: 8px;
  padding: 12px;
  overflow-y: auto;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.panel-title {
  font-weight: 600;
  font-size: 14px;
}

.role-filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.role-tag {
  cursor: pointer;
}

.clear-tag {
  cursor: pointer;
}

.template-cards {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.template-card {
  padding: 12px;
  border: 1px solid var(--color-border, #e4e7ed);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.template-card:hover {
  border-color: var(--el-color-primary);
  background: var(--color-bg-hover, #f5f7fa);
}

.template-card.is-active {
  border-color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.card-name {
  font-weight: 600;
  font-size: 14px;
}

.card-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--color-text-muted, #909399);
  margin-bottom: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.card-actions {
  display: flex;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--color-border-light, #f0f0f0);
}

/* 右侧编辑区 */
.edit-panel {
  background: var(--color-bg-card, #fff);
  border-radius: 8px;
  overflow: hidden;
}

.main-tabs {
  height: 100%;
}

.main-tabs :deep(.el-tabs__header) {
  margin: 0;
  padding: 0 16px;
  background: var(--color-bg-page, #f5f7fa);
}

.main-tabs :deep(.el-tabs__content) {
  padding: 16px;
  height: calc(100% - 40px);
  overflow-y: auto;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
}

.edit-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-weight: 600;
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.count-badge {
  background: var(--el-color-info-light-9);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  color: var(--color-text-muted, #909399);
}

/* 权限卡片 */
.permission-card :deep(.el-card__header) {
  padding: 12px 16px;
}

.permission-groups {
  max-height: 300px;
  overflow-y: auto;
}

.permission-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
}

.permission-item {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 180px;
}

.perm-label {
  font-weight: 500;
}

.perm-key {
  font-size: 11px;
  color: var(--color-text-muted, #909399);
  background: var(--color-bg-hover, #f5f7fa);
  padding: 1px 4px;
  border-radius: 3px;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border-light, #f0f0f0);
}

/* 临时授权 */
.grant-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.grant-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.grant-table {
  width: 100%;
}

.grant-badge {
  margin-left: 4px;
}

.text-muted {
  color: var(--color-text-muted, #909399);
}

.form-tip {
  margin-left: 8px;
  color: var(--color-text-muted, #909399);
}

.route-list {
  margin-top: 8px;
  padding: 8px;
  background: var(--color-bg-hover, #f5f7fa);
  border-radius: 4px;
  max-height: 150px;
  overflow-y: auto;
}

/* 响应式 */
@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 280px 1fr;
  }
}

@media (max-width: 992px) {
  .main-content {
    grid-template-columns: 1fr;
    height: auto;
  }

  .template-list-panel {
    max-height: 400px;
  }
}
</style>
