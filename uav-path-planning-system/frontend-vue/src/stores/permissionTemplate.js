import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { PERMISSION_MATRIX, ACTION_PERMISSIONS, ROLES, ROLE_LABELS } from './auth'

const TPL_KEY = 'uav_permission_templates_v1'
const GRANTS_KEY = 'uav_temporary_grants_v1'

const ALL_ROUTE_KEYS = [
  'dashboard', 'weather', 'orders', 'cockpit', 'tasks',
  'path-planning', 'assimilation', 'monitoring', 'database',
  'docker', 'api-config', 'settings', 'docs'
]

const ROUTE_LABELS = {
  dashboard: '首页 / 项目简介',
  weather: '气象数据',
  orders: '下单 / 选择运输地点',
  cockpit: '智能驾驶舱',
  tasks: '运输任务管理',
  'path-planning': '路径规划',
  assimilation: '数据同化',
  monitoring: '系统监控面板',
  database: '数据库管理',
  docker: 'Docker / 服务器状态',
  'api-config': '气象模型 API 配置',
  settings: '设置',
  docs: '使用文档'
}

const ACTION_DEFS = [
  { key: 'orders:advanced', label: '订单高级操作（orders:advanced）', roles: ['flight', 'admin'] },
  { key: 'api-config:edit', label: 'API 配置编辑（api-config:edit）', roles: ['admin'] },
  { key: 'api-config:view', label: 'API 配置查看（api-config:view）', roles: ['deployment', 'admin'] },
  { key: 'database:view', label: '数据库查看（database:view）', roles: ['admin'] },
  { key: 'database:edit', label: '数据库编辑（database:edit）', roles: ['admin'] },
  { key: 'planning:execute', label: '路径规划执行（planning:execute）', roles: ['flight', 'tester', 'admin'] }
]

function genId(prefix = 'tpl') {
  return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`
}

function actionsForRole(role) {
  const keys = []
  Object.entries(ACTION_PERMISSIONS).forEach(([key, allowed]) => {
    if (Array.isArray(allowed) && allowed.includes(role)) keys.push(key)
  })
  return keys
}

function makeDefaultSystemTemplates() {
  const now = Date.now()
  return Object.values(ROLES).map((role) => ({
    id: `system_${role}`,
    name: `${ROLE_LABELS[role] || role} - 系统模板`,
    description: `系统内置模板，基于 ${ROLE_LABELS[role] || role} 默认权限生成`,
    role,
    routes: Array.from(new Set([...(PERMISSION_MATRIX[role] || []), ...ALL_ROUTE_KEYS.filter(k => PERMISSION_MATRIX[role]?.includes(k))])),
    actions: actionsForRole(role),
    createdAt: now,
    isSystem: true
  }))
}

export const usePermissionTemplateStore = defineStore('permissionTemplate', () => {
  const templates = ref([])
  const temporaryGrants = ref([])

  const roleOptions = computed(() =>
    Object.values(ROLES).map((r) => ({ value: r, label: ROLE_LABELS[r] || r }))
  )

  const availableRoutes = computed(() =>
    ALL_ROUTE_KEYS.map((k) => ({ key: k, label: ROUTE_LABELS[k] || k }))
  )

  const availableActions = computed(() =>
    ACTION_DEFS.map((a) => ({ key: a.key, label: a.label, roles: [...a.roles] }))
  )

  function persist() {
    try {
      localStorage.setItem(TPL_KEY, JSON.stringify(templates.value))
      localStorage.setItem(GRANTS_KEY, JSON.stringify(temporaryGrants.value))
    } catch (e) {
      console.warn('Failed to persist permission template store', e)
    }
  }

  function loadTemplatesFromStorage() {
    try {
      const rawTpl = localStorage.getItem(TPL_KEY)
      const rawGrant = localStorage.getItem(GRANTS_KEY)
      if (rawTpl) {
        const parsed = JSON.parse(rawTpl)
        templates.value = Array.isArray(parsed) ? parsed : []
      }
      if (rawGrant) {
        const parsed = JSON.parse(rawGrant)
        temporaryGrants.value = Array.isArray(parsed) ? parsed : []
      }
    } catch (e) {
      console.warn('Failed to parse permission templates from storage', e)
      templates.value = []
      temporaryGrants.value = []
    }
  }

  function init() {
    loadTemplatesFromStorage()
    if (!templates.value || templates.value.length === 0) {
      templates.value = makeDefaultSystemTemplates()
      persist()
    }
    refreshGrantsActive()
  }

  function syncFromAuthStore() {
    if (!templates.value || templates.value.length === 0) {
      templates.value = makeDefaultSystemTemplates()
    } else {
      templates.value.forEach((tpl) => {
        if (tpl.isSystem && PERMISSION_MATRIX[tpl.role]) {
          tpl.routes = [...(PERMISSION_MATRIX[tpl.role] || [])]
          tpl.actions = actionsForRole(tpl.role)
        }
      })
    }
    refreshGrantsActive()
    persist()
  }

  function refreshGrantsActive() {
    const now = Date.now()
    temporaryGrants.value.forEach((g) => {
      if (g.expireAt && g.expireAt <= now) g.active = false
    })
  }

  function addTemplate(name, description, role, routes, actions, isSystem = false) {
    const tpl = {
      id: genId('tpl'),
      name: name || '未命名模板',
      description: description || '',
      role: role || ROLES.USER,
      routes: Array.isArray(routes) ? routes : [],
      actions: Array.isArray(actions) ? actions : [],
      createdAt: Date.now(),
      isSystem: !!isSystem
    }
    templates.value.push(tpl)
    persist()
    return tpl
  }

  function updateTemplate(id, patch) {
    if (!patch) return
    const tpl = templates.value.find((t) => t.id === id)
    if (!tpl) return
    Object.assign(tpl, patch)
    persist()
  }

  function deleteTemplate(id) {
    const idx = templates.value.findIndex((t) => t.id === id)
    if (idx < 0) return
    if (templates.value[idx].isSystem) return
    templates.value.splice(idx, 1)
    persist()
  }

  function duplicateTemplate(id) {
    const src = templates.value.find((t) => t.id === id)
    if (!src) return null
    const copy = {
      id: genId('tpl'),
      name: `${src.name} - 副本`,
      description: src.description,
      role: src.role,
      routes: [...(src.routes || [])],
      actions: [...(src.actions || [])],
      createdAt: Date.now(),
      isSystem: false
    }
    templates.value.push(copy)
    persist()
    return copy
  }

  function createUserFromTemplate(templateId, username, password, extraRoutes = [], extraActions = []) {
    const tpl = templates.value.find((t) => t.id === templateId)
    if (!tpl) throw new Error('模板不存在')
    const role = tpl.role
    const routes = Array.from(new Set([...(tpl.routes || []), ...extraRoutes]))
    const actions = Array.from(new Set([...(tpl.actions || []), ...extraActions]))
    const user = {
      id: Date.now(),
      username: username || `tpl_${role}_user`,
      displayName: `${ROLE_LABELS[role] || role} - ${username || '模板用户'}`,
      role,
      routes,
      actions,
      demo: true,
      templateId,
      loginTime: new Date().toISOString()
    }
    try {
      localStorage.setItem(TPL_KEY + '_user_' + user.username, JSON.stringify({ user, password: password || '' }))
    } catch (e) {
      console.warn('Failed to persist template user', e)
    }
    return user
  }

  function grantTemporary({ username, role, routes, actions, expireHours = 24 }) {
    const expireAt = Date.now() + Math.max(1, Number(expireHours) || 24) * 60 * 60 * 1000
    const grant = {
      id: genId('grant'),
      username: username || '',
      role: role || ROLES.USER,
      routes: Array.isArray(routes) ? routes : [],
      actions: Array.isArray(actions) ? actions : [],
      expireAt,
      createdAt: Date.now(),
      active: true
    }
    temporaryGrants.value.push(grant)
    persist()
    return grant
  }

  function revokeTemporary(id) {
    const g = temporaryGrants.value.find((x) => x.id === id)
    if (g) g.active = false
    persist()
  }

  function getActiveGrantsFor(username) {
    refreshGrantsActive()
    return temporaryGrants.value.filter((g) => g.username === username && g.active)
  }

  return {
    // state
    templates,
    temporaryGrants,
    // computed
    roleOptions,
    availableRoutes,
    availableActions,
    // methods
    init,
    syncFromAuthStore,
    addTemplate,
    updateTemplate,
    deleteTemplate,
    duplicateTemplate,
    createUserFromTemplate,
    grantTemporary,
    revokeTemporary,
    getActiveGrantsFor,
    refreshGrantsActive
  }
})
