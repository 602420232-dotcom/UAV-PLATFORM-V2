<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { roleApi, permissionApi } from '@/api/user'
import type { Role, Permission } from '@/api/user'
import { useDemoModeStore } from '@/stores/demoMode'

const demoModeStore = useDemoModeStore()

const loading = ref(false)
const roles = ref<Role[]>([])
const allPermissions = ref<Permission[]>([])

// 权限分组定义
const permissionGroups = [
  {
    name: '租户管理',
    key: 'tenant',
    permissions: ['tenant:create', 'tenant:read', 'tenant:update', 'tenant:delete'],
  },
  {
    name: '飞行计划',
    key: 'flight',
    permissions: ['flight:create', 'flight:read', 'flight:update', 'flight:delete', 'flight:approve'],
  },
  {
    name: '气象服务',
    key: 'weather',
    permissions: ['weather:read', 'weather:export'],
  },
  {
    name: '算法管理',
    key: 'algorithm',
    permissions: ['algorithm:read', 'algorithm:create', 'algorithm:update', 'algorithm:delete', 'algorithm:execute'],
  },
  {
    name: '用户管理',
    key: 'user',
    permissions: ['user:create', 'user:read', 'user:update', 'user:delete'],
  },
  {
    name: '系统设置',
    key: 'system',
    permissions: ['system:config', 'system:monitor'],
  },
]

// 权限名称映射
const permissionNameMap: Record<string, string> = {
  'tenant:create': '创建租户',
  'tenant:read': '查看租户',
  'tenant:update': '编辑租户',
  'tenant:delete': '删除租户',
  'flight:create': '创建飞行计划',
  'flight:read': '查看飞行计划',
  'flight:update': '编辑飞行计划',
  'flight:delete': '删除飞行计划',
  'flight:approve': '审批飞行计划',
  'weather:read': '查看气象数据',
  'weather:export': '导出气象数据',
  'algorithm:read': '查看算法',
  'algorithm:create': '创建算法',
  'algorithm:update': '编辑算法',
  'algorithm:delete': '删除算法',
  'algorithm:execute': '执行算法',
  'user:create': '创建用户',
  'user:read': '查看用户',
  'user:update': '编辑用户',
  'user:delete': '删除用户',
  'system:config': '系统配置',
  'system:monitor': '系统监控',
}

// 创建角色对话框
const createDialogVisible = ref(false)
const createFormRef = ref()
const createForm = reactive({
  code: '',
  name: '',
  description: '',
  permissions: [] as string[],
})
const createRules = {
  code: [{ required: true, message: '请输入角色编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
}

// 编辑角色权限对话框
const editDialogVisible = ref(false)
const editFormRef = ref()
const editForm = reactive({
  id: 0,
  code: '',
  name: '',
  description: '',
  permissions: [] as string[],
})
const editRules = {
  name: [{ required: true, message: '请输入角色名称', trigger: 'blur' }],
}

// 全选/取消全选（编辑对话框）
const isAllChecked = computed(() => {
  const allCodes = permissionGroups.flatMap((g) => g.permissions)
  return allCodes.length > 0 && allCodes.every((code) => editForm.permissions.includes(code))
})

const isIndeterminate = computed(() => {
  const allCodes = permissionGroups.flatMap((g) => g.permissions)
  const checkedCount = allCodes.filter((code) => editForm.permissions.includes(code)).length
  return checkedCount > 0 && checkedCount < allCodes.length
})

function handleCheckAll(val: boolean) {
  const allCodes = permissionGroups.flatMap((g) => g.permissions)
  editForm.permissions = val ? [...allCodes] : []
}

function handleGroupCheckAll(group: typeof permissionGroups[0], val: boolean) {
  if (val) {
    const newPerms = [...new Set([...editForm.permissions, ...group.permissions])]
    editForm.permissions = newPerms
  } else {
    editForm.permissions = editForm.permissions.filter((p) => !group.permissions.includes(p))
  }
}

function isGroupAllChecked(group: typeof permissionGroups[0]): boolean {
  return group.permissions.every((code) => editForm.permissions.includes(code))
}

function isGroupIndeterminate(group: typeof permissionGroups[0]): boolean {
  const checkedCount = group.permissions.filter((code) => editForm.permissions.includes(code)).length
  return checkedCount > 0 && checkedCount < group.permissions.length
}

async function loadRoles() {
  loading.value = true
  try {
    if (demoModeStore.isDemoMode) {
      roles.value = [
        { id: 1, code: 'SUPER_ADMIN', name: '超级管理员', description: '拥有系统全部权限', permissions: ['tenant:create', 'tenant:read', 'tenant:update', 'tenant:delete', 'flight:create', 'flight:read', 'flight:update', 'flight:delete', 'flight:approve', 'weather:read', 'weather:export', 'algorithm:read', 'algorithm:create', 'algorithm:update', 'algorithm:delete', 'algorithm:execute', 'user:create', 'user:read', 'user:update', 'user:delete', 'system:config', 'system:monitor'], userCount: 2 },
        { id: 2, code: 'TENANT_ADMIN', name: '租户管理员', description: '管理租户内的用户和资源', permissions: ['flight:create', 'flight:read', 'flight:update', 'weather:read', 'weather:export', 'user:create', 'user:read', 'user:update'], userCount: 5 },
        { id: 3, code: 'OPERATOR', name: '操作员', description: '执行日常飞行和观测任务', permissions: ['flight:create', 'flight:read', 'flight:update', 'weather:read', 'algorithm:execute'], userCount: 12 },
        { id: 4, code: 'OBSERVER', name: '观察员', description: '只读查看各类数据', permissions: ['flight:read', 'weather:read', 'algorithm:read'], userCount: 8 },
      ] as Role[]
      return
    }
    roles.value = await roleApi.list()
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

async function loadPermissions() {
  try {
    allPermissions.value = await permissionApi.list()
  } catch {
    // 错误已在拦截器中处理
  }
}

function handleCreate() {
  createForm.code = ''
  createForm.name = ''
  createForm.description = ''
  createForm.permissions = []
  createDialogVisible.value = true
}

async function submitCreate() {
  const valid = await createFormRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    await roleApi.create({
      code: createForm.code,
      name: createForm.name,
      description: createForm.description || undefined,
      permissions: createForm.permissions,
    })
    ElMessage.success('角色创建成功')
    createDialogVisible.value = false
    createFormRef.value?.resetFields()
    loadRoles()
  } catch {
    // 错误已在拦截器中处理
  }
}

function handleEdit(row: Role) {
  editForm.id = row.id
  editForm.code = row.code
  editForm.name = row.name
  editForm.description = row.description || ''
  editForm.permissions = [...row.permissions]
  editDialogVisible.value = true
}

async function submitEdit() {
  const valid = await editFormRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    await roleApi.update(editForm.id, {
      name: editForm.name,
      description: editForm.description || undefined,
      permissions: editForm.permissions,
    })
    ElMessage.success('角色更新成功')
    editDialogVisible.value = false
    loadRoles()
  } catch {
    // 错误已在拦截器中处理
  }
}

async function handleDelete(row: Role) {
  try {
    await ElMessageBox.confirm(
      `确定要删除角色「${row.name}」吗？删除后关联用户的角色将被清除。`,
      '确认删除',
      { type: 'error' }
    )
    await roleApi.remove(row.id)
    ElMessage.success('删除成功')
    loadRoles()
  } catch {
    // 用户取消或请求失败
  }
}

onMounted(async () => {
  await demoModeStore.fetchStatus()
  loadRoles()
  loadPermissions()
})

watch(() => demoModeStore.isDemoMode, () => {
  loadRoles()
})
</script>

<template>
  <div class="role-list-page">
    <div class="page-header">
      <h2>角色管理</h2>
      <el-button type="primary" :disabled="demoModeStore.isDemoMode" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        新建角色
      </el-button>
    </div>

    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="roles"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="code" label="角色编码" min-width="140" />
        <el-table-column prop="name" label="角色名称" min-width="120" />
        <el-table-column prop="description" label="描述" min-width="180">
          <template #default="{ row }">
            {{ row.description || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="permissions" label="权限数量" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="primary">{{ row.permissions.length }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="userCount" label="用户数量" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.userCount ?? 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" :disabled="demoModeStore.isDemoMode" @click="handleEdit(row)">
              编辑权限
            </el-button>
            <el-button type="danger" link size="small" :disabled="demoModeStore.isDemoMode" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建角色对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建角色"
      width="600px"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="100px"
      >
        <el-form-item label="角色编码" prop="code">
          <el-input v-model="createForm.code" placeholder="如：OPERATOR（大写字母+下划线）" />
        </el-form-item>
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="createForm.name" placeholder="如：操作员" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="2"
            placeholder="角色描述（可选）"
          />
        </el-form-item>
        <el-form-item label="权限">
          <div class="permission-select-area">
            <el-checkbox-group v-model="createForm.permissions">
              <div v-for="group in permissionGroups" :key="group.key" class="permission-group">
                <div class="group-header">{{ group.name }}</div>
                <div class="group-permissions">
                  <el-checkbox
                    v-for="perm in group.permissions"
                    :key="perm"
                    :value="perm"
                    :label="perm"
                  >
                    {{ permissionNameMap[perm] || perm }}
                  </el-checkbox>
                </div>
              </div>
            </el-checkbox-group>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 编辑角色权限对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑角色权限"
      width="600px"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="100px"
      >
        <el-form-item label="角色编码">
          <el-input :model-value="editForm.code" disabled />
        </el-form-item>
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="2"
            placeholder="角色描述（可选）"
          />
        </el-form-item>
        <el-form-item label="权限">
          <div class="permission-select-area">
            <div class="select-all-row">
              <el-checkbox
                :model-value="isAllChecked"
                :indeterminate="isIndeterminate"
                @change="handleCheckAll"
              >
                全选
              </el-checkbox>
            </div>
            <el-checkbox-group v-model="editForm.permissions">
              <div v-for="group in permissionGroups" :key="group.key" class="permission-group">
                <div class="group-header">
                  <el-checkbox
                    :model-value="isGroupAllChecked(group)"
                    :indeterminate="isGroupIndeterminate(group)"
                    @change="(val: boolean) => handleGroupCheckAll(group, val)"
                  >
                    {{ group.name }}
                  </el-checkbox>
                </div>
                <div class="group-permissions">
                  <el-checkbox
                    v-for="perm in group.permissions"
                    :key="perm"
                    :value="perm"
                    :label="perm"
                  >
                    {{ permissionNameMap[perm] || perm }}
                  </el-checkbox>
                </div>
              </div>
            </el-checkbox-group>
          </div>
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
.role-list-page {
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

.permission-select-area {
  width: 100%;
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 12px;
}

.select-all-row {
  padding-bottom: 8px;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--color-border);
}

.permission-group {
  margin-bottom: 12px;
}

.permission-group:last-child {
  margin-bottom: 0;
}

.group-header {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.group-permissions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding-left: 16px;
}
</style>
