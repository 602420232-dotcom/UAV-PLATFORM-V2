<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { userApi, roleApi } from '@/api/user'
import type { User, Role } from '@/api/user'
import { formatDateTime } from '@/utils/format'
import { useDemoModeStore } from '@/stores/demoMode'

const demoModeStore = useDemoModeStore()

const loading = ref(false)
const users = ref<User[]>([])
const total = ref(0)
const roles = ref<Role[]>([])

// 搜索参数
const queryParams = reactive({
  current: 1,
  size: 10,
  keyword: '',
  role: '',
  status: undefined as number | undefined,
})

// 角色标签颜色映射
const roleTagTypeMap: Record<string, string> = {
  SUPER_ADMIN: 'danger',
  TENANT_ADMIN: 'warning',
  OPERATOR: 'primary',
  OBSERVER: 'info',
  ALGORITHM_ADMIN: 'success',
}

// 角色名称映射
const roleNameMap: Record<string, string> = {
  SUPER_ADMIN: '超级管理员',
  TENANT_ADMIN: '租户管理员',
  OPERATOR: '操作员',
  OBSERVER: '观察员',
  ALGORITHM_ADMIN: '算法管理员',
}

function getRoleName(code: string): string {
  return roleNameMap[code] || code
}

function getRoleTagType(code: string): string {
  return roleTagTypeMap[code] || 'info'
}

// 创建/编辑用户对话框
const userDialogVisible = ref(false)
const userDialogMode = ref<'create' | 'edit'>('create')
const userFormRef = ref()
const userForm = reactive({
  id: 0,
  username: '',
  realName: '',
  email: '',
  phone: '',
  password: '',
  role: '',
  tenantId: undefined as number | undefined,
})
const userRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  realName: [{ required: true, message: '请输入真实姓名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

// 重置密码对话框
const resetPwdDialogVisible = ref(false)
const resetPwdFormRef = ref()
const resetPwdForm = reactive({
  userId: 0,
  username: '',
  newPassword: '',
  confirmPassword: '',
})
const resetPwdRules = {
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_rule: unknown, value: string, callback: (err?: Error) => void) => {
        if (value !== resetPwdForm.newPassword) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// 分配角色对话框
const assignRoleDialogVisible = ref(false)
const assignRoleForm = reactive({
  userId: 0,
  username: '',
  roleCode: '',
})

async function loadUsers() {
  loading.value = true
  try {
    if (demoModeStore.isDemoMode) {
      users.value = [
        { id: 1, username: 'admin', realName: '系统管理员', email: 'admin@uav-platform.com', phone: '13800000001', role: 'SUPER_ADMIN', tenantId: 1, tenantName: '默认租户', status: 1, createdAt: '2025-01-15T08:00:00Z' } as User,
        { id: 2, username: 'zhangwei', realName: '张伟', email: 'zhangwei@example.com', phone: '13800000002', role: 'TENANT_ADMIN', tenantId: 1, tenantName: '默认租户', status: 1, createdAt: '2025-02-20T10:30:00Z' } as User,
        { id: 3, username: 'lina', realName: '李娜', email: 'lina@example.com', phone: '13800000003', role: 'OPERATOR', tenantId: 2, tenantName: '气象服务中心', status: 1, createdAt: '2025-03-10T14:00:00Z' } as User,
        { id: 4, username: 'wangfang', realName: '王芳', email: 'wangfang@example.com', phone: '13800000004', role: 'OPERATOR', tenantId: 1, tenantName: '默认租户', status: 1, createdAt: '2025-04-05T09:15:00Z' } as User,
        { id: 5, username: 'liuyang', realName: '刘洋', email: 'liuyang@example.com', phone: '13800000005', role: 'OBSERVER', tenantId: 3, tenantName: '科研院所', status: 1, createdAt: '2025-05-12T16:45:00Z' } as User,
        { id: 6, username: 'chenming', realName: '陈明', email: 'chenming@example.com', phone: '13800000006', role: 'OPERATOR', tenantId: 2, tenantName: '气象服务中心', status: 0, createdAt: '2025-06-01T11:00:00Z' } as User,
        { id: 7, username: 'zhaolei', realName: '赵磊', email: 'zhaolei@example.com', phone: '13800000007', role: 'ALGORITHM_ADMIN', tenantId: 1, tenantName: '默认租户', status: 1, createdAt: '2025-06-15T08:30:00Z' } as User,
        { id: 8, username: 'sunli', realName: '孙丽', email: 'sunli@example.com', phone: '13800000008', role: 'OBSERVER', tenantId: 1, tenantName: '默认租户', status: 1, createdAt: '2025-07-20T13:20:00Z' } as User,
      ]
      total.value = users.value.length
      return
    }
    const data = await userApi.list(queryParams)
    users.value = data.records
    total.value = data.total
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

async function loadRoles() {
  try {
    roles.value = await roleApi.list()
  } catch {
    // 错误已在拦截器中处理
  }
}

function handleSearch() {
  queryParams.current = 1
  loadUsers()
}

function handleReset() {
  queryParams.keyword = ''
  queryParams.role = ''
  queryParams.status = undefined
  queryParams.current = 1
  loadUsers()
}

function handlePageChange(page: number) {
  queryParams.current = page
  loadUsers()
}

function handleSizeChange(size: number) {
  queryParams.size = size
  queryParams.current = 1
  loadUsers()
}

function handleCreate() {
  userDialogMode.value = 'create'
  userForm.id = 0
  userForm.username = ''
  userForm.realName = ''
  userForm.email = ''
  userForm.phone = ''
  userForm.password = ''
  userForm.role = ''
  userForm.tenantId = undefined
  userDialogVisible.value = true
}

function handleEdit(row: User) {
  userDialogMode.value = 'edit'
  userForm.id = row.id
  userForm.username = row.username
  userForm.realName = row.realName || ''
  userForm.email = row.email || ''
  userForm.phone = row.phone || ''
  userForm.password = ''
  userForm.role = row.role
  userForm.tenantId = row.tenantId
  userDialogVisible.value = true
}

async function submitUser() {
  const valid = await userFormRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    if (userDialogMode.value === 'create') {
      await userApi.create({
        username: userForm.username,
        realName: userForm.realName,
        email: userForm.email || undefined,
        phone: userForm.phone || undefined,
        password: userForm.password,
        role: userForm.role,
        tenantId: userForm.tenantId,
      })
      ElMessage.success('用户创建成功')
    } else {
      const updateData: Partial<User> = {
        realName: userForm.realName,
        email: userForm.email || undefined,
        phone: userForm.phone || undefined,
        role: userForm.role,
        tenantId: userForm.tenantId,
      }
      await userApi.update(userForm.id, updateData)
      ElMessage.success('用户更新成功')
    }
    userDialogVisible.value = false
    userFormRef.value?.resetFields()
    loadUsers()
  } catch {
    // 错误已在拦截器中处理
  }
}

async function handleToggleStatus(row: User) {
  const newStatus = row.status === 1 ? 0 : 1
  const actionText = newStatus === 1 ? '启用' : '禁用'

  try {
    await ElMessageBox.confirm(`确定要${actionText}用户 "${row.realName || row.username}" 吗？`, '确认操作', {
      type: 'warning',
    })
    await userApi.update(row.id, { status: newStatus })
    ElMessage.success(`${actionText}成功`)
    loadUsers()
  } catch {
    // 用户取消或请求失败
  }
}

function handleResetPassword(row: User) {
  resetPwdForm.userId = row.id
  resetPwdForm.username = row.realName || row.username
  resetPwdForm.newPassword = ''
  resetPwdForm.confirmPassword = ''
  resetPwdDialogVisible.value = true
}

async function submitResetPassword() {
  const valid = await resetPwdFormRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    await userApi.resetPassword(resetPwdForm.userId, {
      newPassword: resetPwdForm.newPassword,
    })
    ElMessage.success('密码重置成功')
    resetPwdDialogVisible.value = false
    resetPwdFormRef.value?.resetFields()
  } catch {
    // 错误已在拦截器中处理
  }
}

function handleAssignRole(row: User) {
  assignRoleForm.userId = row.id
  assignRoleForm.username = row.realName || row.username
  assignRoleForm.roleCode = row.role
  assignRoleDialogVisible.value = true
}

async function submitAssignRole() {
  if (!assignRoleForm.roleCode) {
    ElMessage.warning('请选择角色')
    return
  }

  try {
    await userApi.assignRole(assignRoleForm.userId, {
      roleCode: assignRoleForm.roleCode,
    })
    ElMessage.success('角色分配成功')
    assignRoleDialogVisible.value = false
    loadUsers()
  } catch {
    // 错误已在拦截器中处理
  }
}

async function handleDelete(row: User) {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${row.realName || row.username}" 吗？此操作不可恢复。`,
      '确认删除',
      { type: 'error' }
    )
    await userApi.remove(row.id)
    ElMessage.success('删除成功')
    loadUsers()
  } catch {
    // 用户取消或请求失败
  }
}

onMounted(async () => {
  await demoModeStore.fetchStatus()
  loadUsers()
  loadRoles()
})

watch(() => demoModeStore.isDemoMode, () => {
  loadUsers()
})
</script>

<template>
  <div class="user-list-page">
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary" :disabled="demoModeStore.isDemoMode" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        新建用户
      </el-button>
    </div>

    <el-card class="table-card">
      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="queryParams.keyword"
          placeholder="搜索用户名 / 姓名 / 邮箱 / 手机号"
          clearable
          style="width: 280px"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        />
        <el-select
          v-model="queryParams.role"
          placeholder="角色筛选"
          clearable
          style="width: 160px"
          @change="handleSearch"
        >
          <el-option
            v-for="role in roles"
            :key="role.code"
            :label="role.name"
            :value="role.code"
          />
        </el-select>
        <el-select
          v-model="queryParams.status"
          placeholder="状态筛选"
          clearable
          style="width: 120px"
          @change="handleSearch"
        >
          <el-option label="启用" :value="1" />
          <el-option label="禁用" :value="0" />
        </el-select>
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
        <el-button @click="handleReset">
          重置
        </el-button>
      </div>

      <!-- 数据表格 -->
      <el-table
        v-loading="loading"
        :data="users"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="realName" label="真实姓名" min-width="100" />
        <el-table-column prop="role" label="角色" width="130">
          <template #default="{ row }">
            <el-tag :type="getRoleTagType(row.role)" size="small">
              {{ getRoleName(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="tenantName" label="租户" min-width="120">
          <template #default="{ row }">
            {{ row.tenantName || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-switch
              :model-value="row.status === 1"
              inline-prompt
              active-text="启用"
              inactive-text="禁用"
              @change="handleToggleStatus(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.createdAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" :disabled="demoModeStore.isDemoMode" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-button type="warning" link size="small" :disabled="demoModeStore.isDemoMode" @click="handleResetPassword(row)">
              重置密码
            </el-button>
            <el-button type="success" link size="small" :disabled="demoModeStore.isDemoMode" @click="handleAssignRole(row)">
              分配角色
            </el-button>
            <el-button type="danger" link size="small" :disabled="demoModeStore.isDemoMode" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
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

    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="userDialogVisible"
      :title="userDialogMode === 'create' ? '新建用户' : '编辑用户'"
      width="550px"
    >
      <el-form
        ref="userFormRef"
        :model="userForm"
        :rules="userRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="userForm.username"
            placeholder="请输入用户名"
            :disabled="userDialogMode === 'edit'"
          />
        </el-form-item>
        <el-form-item label="真实姓名" prop="realName">
          <el-input v-model="userForm.realName" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="userForm.email" placeholder="请输入邮箱（可选）" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="userForm.phone" placeholder="请输入手机号（可选）" />
        </el-form-item>
        <el-form-item v-if="userDialogMode === 'create'" label="密码" prop="password">
          <el-input
            v-model="userForm.password"
            type="password"
            show-password
            placeholder="请输入密码"
          />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" placeholder="请选择角色" style="width: 100%">
            <el-option
              v-for="role in roles"
              :key="role.code"
              :label="role.name"
              :value="role.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="租户 ID">
          <el-input-number
            v-model="userForm.tenantId"
            :min="1"
            placeholder="可选"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitUser">
          {{ userDialogMode === 'create' ? '创建' : '保存' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog
      v-model="resetPwdDialogVisible"
      title="重置密码"
      width="450px"
    >
      <el-alert
        :title="`正在为用户「${resetPwdForm.username}」重置密码`"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      />
      <el-form
        ref="resetPwdFormRef"
        :model="resetPwdForm"
        :rules="resetPwdRules"
        label-width="100px"
      >
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="resetPwdForm.newPassword"
            type="password"
            show-password
            placeholder="请输入新密码（至少 6 位）"
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="resetPwdForm.confirmPassword"
            type="password"
            show-password
            placeholder="请再次输入新密码"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPwdDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitResetPassword">确认重置</el-button>
      </template>
    </el-dialog>

    <!-- 分配角色对话框 -->
    <el-dialog
      v-model="assignRoleDialogVisible"
      title="分配角色"
      width="450px"
    >
      <el-alert
        :title="`正在为用户「${assignRoleForm.username}」分配角色`"
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      />
      <el-form label-width="80px">
        <el-form-item label="角色">
          <el-select v-model="assignRoleForm.roleCode" placeholder="请选择角色" style="width: 100%">
            <el-option
              v-for="role in roles"
              :key="role.code"
              :label="role.name"
              :value="role.code"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignRoleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitAssignRole">确认分配</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.user-list-page {
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

.search-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
