<template>
  <div class="permission-debug-view">
    <!-- 顶部栏 -->
    <div class="debug-header">
      <div class="header-left">
        <h2 class="page-title">
          <el-icon><MagicStick /></el-icon>
          <span>权限调试工具</span>
        </h2>
      </div>
      <div class="header-right">
        <el-alert
          v-if="authStore.demoMode"
          class="demo-alert"
          title="演示模式：所有权限判定均基于本地矩阵，仅供参考"
          type="info"
          :closable="false"
          show-icon
        />
        <div class="role-display">
          <span class="label">当前实际角色：</span>
          <el-tag type="primary" effect="dark">{{ authStore.roleLabel || '未登录' }}</el-tag>
        </div>
        <div class="role-display" v-if="simulatedRole">
          <span class="label">当前模拟角色：</span>
          <el-tag type="warning" effect="dark">
            {{ roleLabels[simulatedRole] || simulatedRole }}
          </el-tag>
        </div>
        <div class="simulate-control">
          <el-select
            v-model="selectedRole"
            placeholder="选择模拟角色"
            size="default"
            style="width: 160px"
          >
            <el-option
              v-for="(label, key) in roleLabels"
              :key="key"
              :label="label"
              :value="key"
            />
          </el-select>
          <el-button type="primary" @click="applySimulatedRole">应用模拟</el-button>
          <el-button v-if="simulatedRole" type="danger" plain @click="exitSimulatedRole">
            退出模拟
          </el-button>
        </div>
      </div>
    </div>

    <!-- 主体（三栏） -->
    <el-row :gutter="16" class="debug-body">
      <!-- 左栏：权限矩阵 -->
      <el-col :span="7" class="debug-col">
        <el-card shadow="never" class="debug-card">
          <template #header>
            <div class="card-header">
              <el-icon><Key /></el-icon>
              <span>权限矩阵（{{ displayRoleLabel }} × 所有路由）</span>
            </div>
          </template>

          <el-input
            v-model="routeSearch"
            placeholder="按路由键筛选"
            clearable
            class="search-input"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <el-table
            :data="filteredMatrixRows"
            size="small"
            stripe
            height="520"
            class="matrix-table"
          >
            <el-table-column prop="key" label="路由键" width="180" />
            <el-table-column label="权限" width="100" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.allowed" type="success" size="small">✅ 允许</el-tag>
                <el-tag v-else type="info" size="small" effect="plain">❌ 禁止</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="说明" min-width="140" />
          </el-table>
        </el-card>
      </el-col>

      <!-- 中栏：命中权限与动作 -->
      <el-col :span="10" class="debug-col">
        <el-card shadow="never" class="debug-card">
          <template #header>
            <div class="card-header">
              <el-icon><Check /></el-icon>
              <span>{{ displayRoleLabel }} 可访问的路由</span>
            </div>
          </template>

          <div class="hit-routes">
            <el-tag
              v-for="route in hitRoutes"
              :key="route.key"
              type="success"
              effect="light"
              class="hit-tag"
            >
              {{ route.key }}
            </el-tag>
            <el-empty
              v-if="hitRoutes.length === 0"
              description="无可用路由"
              :image-size="80"
            />
          </div>
        </el-card>

        <el-card shadow="never" class="debug-card action-card">
          <template #header>
            <div class="card-header">
              <el-icon><Lock /></el-icon>
              <span>动作权限</span>
            </div>
          </template>

          <el-table
            :data="actionRows"
            size="small"
            stripe
            height="340"
            class="action-table"
          >
            <el-table-column prop="key" label="动作 Key" width="180" />
            <el-table-column label="是否允许" width="110" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.allowed" type="success" size="small">✅ 允许</el-tag>
                <el-tag v-else type="info" size="small" effect="plain">❌ 禁止</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="desc" label="说明" min-width="150" />
          </el-table>
        </el-card>
      </el-col>

      <!-- 右栏：调试控制台 -->
      <el-col :span="7" class="debug-col">
        <el-card shadow="never" class="debug-card">
          <template #header>
            <div class="card-header">
              <el-icon><Monitor /></el-icon>
              <span>调试控制台</span>
            </div>
          </template>

          <el-input
            v-model="consoleLog"
            type="textarea"
            :rows="14"
            readonly
            placeholder="模拟角色变更记录将出现在此..."
            class="console-textarea"
          />

          <div class="console-buttons">
            <el-button size="default" @click="clearLogs">清空日志</el-button>
            <el-button type="primary" size="default" @click="exportJson">
              导出为 JSON
            </el-button>
            <el-button type="success" size="default" @click="copyMatrix">
              复制矩阵到剪贴板
            </el-button>
          </div>

          <el-divider />

          <div class="status-block">
            <div class="status-item">
              <span class="status-label">Nacos 权限矩阵：</span>
              <el-tag v-if="hasNacosMatrix" type="success" size="small">已加载 Nacos 矩阵</el-tag>
              <el-tag v-else type="info" size="small" effect="plain">使用本地矩阵</el-tag>
            </div>
            <div class="status-item">
              <span class="status-label">Token 过期时间：</span>
              <span class="status-value">{{ tokenExpiresLabel }}</span>
            </div>
            <div class="status-item">
              <span class="status-label">演示用户：</span>
              <span class="status-value">{{ demoUserLabel }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  MagicStick, Key, Search, Check, Lock, Monitor
} from '@element-plus/icons-vue'
import {
  useAuthStore,
  PERMISSION_MATRIX,
  ACTION_PERMISSIONS,
  ROLE_LABELS
} from '../../stores/auth'

const authStore = useAuthStore()

const roleLabels = ROLE_LABELS
const simulatedRole = ref('')
const selectedRole = ref('')
const routeSearch = ref('')
const consoleLog = ref('')

const displayRole = computed(() => simulatedRole.value || authStore.role || '')

const displayRoleLabel = computed(() => {
  const r = displayRole.value
  if (!r) return '未知角色'
  return roleLabels[r] || r
})

// 所有路由键与标题（取自 PERMISSION_MATRIX + 路由 meta）
const allRouteKeys = computed(() => {
  const keySet = new Set()
  Object.values(PERMISSION_MATRIX).forEach((list) => {
    list.forEach((k) => keySet.add(k))
  })
  // 显式包含 permission-debug（即使 admin 矩阵中才存在）
  keySet.add('permission-debug')
  return Array.from(keySet).sort()
})

// 为路由键提供简单的说明/标题
const routeTitleMap = {
  dashboard: '首页 / 项目简介',
  weather: '气象数据',
  orders: '下单 / 选择运输地点',
  cockpit: '智能驾驶舱',
  tasks: '运输任务管理',
  'task-report': '任务报告中心',
  'utm-integration': '低空 UTM 对接',
  'path-planning': '路径规划',
  'model-evaluation': '模型评估',
  'parameter-tuning': '算法参数调优',
  assimilation: '数据同化',
  monitoring: '系统监控面板',
  database: '数据库管理',
  docker: 'Docker / 服务器状态',
  'api-config': '气象模型 API 配置',
  'permission-templates': '权限模板管理',
  settings: '设置',
  'theme-customizer': '主题定制',
  docs: '使用文档',
  'permission-debug': '权限调试工具'
}

function hasRouteAccessForDebug(routeKey) {
  if (simulatedRole.value) {
    const list = PERMISSION_MATRIX[simulatedRole.value] || []
    return list.includes(routeKey)
  }
  return authStore.hasRouteAccess(routeKey)
}

function hasActionForDebug(actionKey) {
  const allowedRoles = ACTION_PERMISSIONS[actionKey]
  if (!allowedRoles) return false
  const r = displayRole.value
  if (!r) return false
  return allowedRoles.includes(r)
}

const matrixRows = computed(() =>
  allRouteKeys.value.map((key) => ({
    key,
    allowed: hasRouteAccessForDebug(key),
    title: routeTitleMap[key] || key
  }))
)

const filteredMatrixRows = computed(() => {
  const q = String(routeSearch.value || '').trim().toLowerCase()
  if (!q) return matrixRows.value
  return matrixRows.value.filter((r) => r.key.toLowerCase().includes(q))
})

const hitRoutes = computed(() =>
  matrixRows.value.filter((r) => r.allowed)
)

// 动作权限：按需求列出的动作 key 映射到实际 ACTION_PERMISSIONS 中的键
const ACTION_KEY_MAP = [
  { key: 'orders:advanced', displayKey: 'orders.advanced', desc: '高级下单操作（飞控/管理员）' },
  { key: 'api-config:edit', displayKey: 'api-config.edit', desc: '编辑气象模型 API 配置（仅管理员）' },
  { key: 'api-config:view', displayKey: 'api-config.view', desc: '查看气象模型 API 配置（部署/管理员）' },
  { key: 'database:edit', displayKey: 'database.edit', desc: '数据库管理操作（仅管理员）' },
  { key: 'planning:execute', displayKey: 'planning.execute', desc: '执行路径规划（飞控/测试/管理员）' },
  { key: 'monitoring:restart', displayKey: 'monitoring.restart', desc: '系统监控重启操作（运维/管理员）' },
  { key: 'report:export', displayKey: 'report.export', desc: '任务报告导出（生产/飞控/管理员）' }
]

const actionRows = computed(() =>
  ACTION_KEY_MAP.map((item) => ({
    key: item.displayKey,
    allowed: hasActionForDebug(item.key),
    desc: item.desc
  }))
)

// Nacos 状态
const hasNacosMatrix = computed(() => {
  try {
    return !!localStorage.getItem('uav_nacos_permission_matrix')
  } catch (e) {
    return false
  }
})

const tokenExpiresLabel = computed(() => {
  if (!authStore.tokenExpiresAt) return '无'
  const date = new Date(authStore.tokenExpiresAt)
  return date.toLocaleString()
})

const demoUserLabel = computed(() => {
  const u = authStore.user
  if (!u) return '未登录'
  return `${u.username}（${roleLabels[u.role] || u.role}）`
})

// ========== 操作 ==========
function timestamp() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function pushLog(text) {
  const line = `[${timestamp()}] ${text}`
  consoleLog.value = consoleLog.value
    ? `${consoleLog.value}\n${line}`
    : line
}

function applySimulatedRole() {
  if (!selectedRole.value) {
    ElMessage.warning('请先选择模拟角色')
    return
  }
  simulatedRole.value = selectedRole.value
  pushLog(`应用模拟角色：${roleLabels[simulatedRole.value]}(${simulatedRole.value})`)
  ElMessage.success(`已切换到模拟角色：${roleLabels[simulatedRole.value]}`)
}

function exitSimulatedRole() {
  const prev = simulatedRole.value
  simulatedRole.value = ''
  selectedRole.value = ''
  pushLog(`退出模拟角色，恢复为实际角色：${roleLabels[authStore.role] || authStore.role}`)
  if (prev) {
    ElMessage.info('已恢复使用实际登录角色')
  }
}

function clearLogs() {
  consoleLog.value = ''
  ElMessage.info('日志已清空')
}

function buildExportData() {
  const routes = {}
  matrixRows.value.forEach((r) => { routes[r.key] = r.allowed })
  const actions = {}
  actionRows.value.forEach((a) => { actions[a.key] = a.allowed })
  return {
    simulatedRole: simulatedRole.value || null,
    actualRole: authStore.role || null,
    displayRole: displayRole.value,
    routes,
    actions,
    generatedAt: new Date().toISOString()
  }
}

function exportJson() {
  try {
    const data = buildExportData()
    const blob = new Blob(
      [JSON.stringify(data, null, 2)],
      { type: 'application/json;charset=utf-8' }
    )
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `permission-debug-${displayRole.value || 'unknown'}-${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    pushLog('导出权限矩阵 JSON 文件成功')
    ElMessage.success('已导出 JSON 文件')
  } catch (e) {
    ElMessage.error('导出失败：' + (e?.message || e))
  }
}

async function copyMatrix() {
  try {
    const data = buildExportData()
    const text = JSON.stringify(data, null, 2)
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      const ta = document.createElement('textarea')
      ta.value = text
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
    pushLog('权限矩阵已复制到剪贴板')
    ElMessage.success('已复制到剪贴板')
  } catch (e) {
    ElMessage.error('复制失败：' + (e?.message || e))
  }
}

onMounted(() => {
  pushLog(`权限调试工具启动，当前实际角色：${roleLabels[authStore.role] || authStore.role || '未登录'}`)
})
</script>

<style scoped>
.permission-debug-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.debug-header {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 14px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #24292f;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.demo-alert {
  max-width: 420px;
}

.role-display {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #57606a;
}

.role-display .label {
  color: #57606a;
}

.simulate-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.debug-body {
  margin: 0;
}

.debug-col {
  display: flex;
  flex-direction: column;
}

.debug-card {
  height: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 14px;
  color: #24292f;
}

.search-input {
  margin-bottom: 12px;
}

.matrix-table,
.action-table {
  width: 100%;
}

.hit-routes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 60px;
}

.hit-tag {
  font-size: 12px;
}

.action-card {
  margin-top: 16px;
}

.console-textarea {
  font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
  font-size: 12px;
  background: #f6f8fa;
  resize: none;
}

.console-buttons {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.status-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.status-label {
  color: #57606a;
  min-width: 110px;
}

.status-value {
  color: #24292f;
  word-break: break-all;
}

/* 深色模式适配 */
:deep(.is-dark) .debug-header,
:deep(.is-dark) .debug-card {
  background: #161b22;
  border-color: #30363d;
}

:deep(.is-dark) .page-title,
:deep(.is-dark) .card-header,
:deep(.is-dark) .status-value {
  color: #c9d1d9;
}

:deep(.is-dark) .role-display .label,
:deep(.is-dark) .status-label,
:deep(.is-dark) .role-display {
  color: #8b949e;
}

:deep(.is-dark) .console-textarea {
  background: #0d1117;
}
</style>
