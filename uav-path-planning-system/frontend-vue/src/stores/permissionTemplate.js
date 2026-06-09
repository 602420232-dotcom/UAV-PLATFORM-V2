import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { PERMISSION_MATRIX, ACTION_PERMISSIONS, ROLES, ROLE_LABELS } from './auth'

const TPL_KEY = 'uav_permission_templates_v1'
const GRANTS_KEY = 'uav_temporary_grants_v1'

const ALL_ROUTE_KEYS = [
  // 通用页面
  'dashboard', 'weather', 'orders', 'cockpit', 'tasks', 'settings',
  'theme-customizer', 'docs',

  // 飞控相关
  'path-planning', 'model-evaluation', 'parameter-tuning',
  'sensitivity-analysis', 'experiment-compare', 'airworthiness',

  // 测试/部署相关
  'weather-station', 'weather-source', 'monitoring', 'database',
  'docker', 'docker-build', 'api-config',

  // 协作相关
  'utm-integration', 'task-report', 'forum',

  // 管理相关
  'permission-templates', 'user-stats', 'permission-debug',

  // 数据同化
  'assimilation'
]

const ROUTE_LABELS = {
  // 通用页面
  dashboard: '首页 / 项目简介',
  weather: '气象数据',
  orders: '下单 / 选择运输地点',
  cockpit: '智能驾驶舱',
  tasks: '运输任务管理',
  settings: '设置',
  'theme-customizer': '主题定制',
  docs: '使用文档',

  // 飞控相关
  'path-planning': '路径规划',
  'model-evaluation': '模型评估',
  'parameter-tuning': '算法参数调优',
  'sensitivity-analysis': '参数敏感性分析',
  'experiment-compare': '实验对比工具',
  airworthiness: '适航性评估',

  // 测试/部署相关
  'weather-station': '气象站点管理',
  'weather-source': '气象数据源',
  monitoring: '系统监控面板',
  database: '数据库管理',
  docker: 'Docker / 服务器状态',
  'docker-build': 'Docker 构建',
  'api-config': '气象模型 API 配置',

  // 协作相关
  'utm-integration': '低空 UTM 对接',
  'task-report': '任务报告中心',
  forum: '团队论坛',

  // 管理相关
  'permission-templates': '权限模板管理',
  'user-stats': '用户统计',
  'permission-debug': '权限调试工具',

  // 数据同化
  assimilation: '数据同化'
}

const ACTION_DEFS = [
  // 通用权限
  { key: 'common:export', label: '通用导出操作', roles: ['admin'] },
  { key: 'common:delete', label: '通用删除操作', roles: ['admin'] },
  { key: 'common:edit', label: '通用编辑操作', roles: ['admin'] },

  // 气象数据
  { key: 'weather:view', label: '查看气象数据', roles: ['user', 'production', 'flight', 'tester', 'deployment', 'admin'] },
  { key: 'weather:download', label: '下载气象数据', roles: ['flight', 'tester', 'admin'] },
  { key: 'weather:advanced', label: '高级气象功能', roles: ['flight', 'tester', 'admin'] },

  // 下单
  { key: 'orders:view', label: '查看订单', roles: ['user', 'production', 'admin'] },
  { key: 'orders:create', label: '创建订单', roles: ['user', 'production', 'admin'] },
  { key: 'orders:advanced', label: '高级下单操作', roles: ['flight', 'admin'] },
  { key: 'orders:cancel', label: '取消订单', roles: ['user', 'production', 'admin'] },

  // 智能驾驶舱
  { key: 'cockpit:view', label: '查看驾驶舱', roles: ['production', 'flight', 'admin'] },
  { key: 'cockpit:control', label: '控制驾驶舱', roles: ['flight', 'admin'] },
  { key: 'cockpit:emergency', label: '紧急控制', roles: ['flight', 'admin'] },

  // 任务管理
  { key: 'tasks:view', label: '查看任务', roles: ['production', 'flight', 'admin'] },
  { key: 'tasks:create', label: '创建任务', roles: ['production', 'admin'] },
  { key: 'tasks:edit', label: '编辑任务', roles: ['production', 'flight', 'admin'] },
  { key: 'tasks:delete', label: '删除任务', roles: ['admin'] },
  { key: 'tasks:assign', label: '分配任务', roles: ['production', 'admin'] },

  // 路径规划
  { key: 'planning:view', label: '查看路径规划', roles: ['flight', 'tester', 'admin'] },
  { key: 'planning:execute', label: '执行路径规划', roles: ['flight', 'tester', 'admin'] },
  { key: 'planning:save', label: '保存路径规划', roles: ['flight', 'tester', 'admin'] },

  // 模型评估
  { key: 'evaluation:view', label: '查看模型评估', roles: ['flight', 'tester', 'admin'] },
  { key: 'evaluation:run', label: '运行模型评估', roles: ['flight', 'tester', 'admin'] },
  { key: 'evaluation:compare', label: '对比模型评估', roles: ['flight', 'tester', 'admin'] },

  // 算法参数调优
  { key: 'tuning:view', label: '查看参数调优', roles: ['flight', 'tester', 'admin'] },
  { key: 'tuning:adjust', label: '调整参数', roles: ['flight', 'tester', 'admin'] },
  { key: 'tuning:save', label: '保存参数配置', roles: ['admin'] },

  // 数据同化
  { key: 'assimilation:view', label: '查看数据同化', roles: ['tester', 'deployment', 'admin'] },
  { key: 'assimilation:execute', label: '执行数据同化', roles: ['tester', 'deployment', 'admin'] },
  { key: 'assimilation:config', label: '配置数据同化', roles: ['deployment', 'admin'] },
  { key: 'assimilation:download', label: '下载同化结果', roles: ['tester', 'deployment', 'admin'] },
  { key: 'assimilation:delete', label: '删除同化数据', roles: ['deployment', 'admin'] },

  // 数据库
  { key: 'database:view', label: '查看数据库', roles: ['deployment', 'admin'] },
  { key: 'database:backup', label: '备份数据库', roles: ['deployment', 'admin'] },
  { key: 'database:restore', label: '恢复数据库', roles: ['deployment', 'admin'] },
  { key: 'database:config', label: '配置数据库', roles: ['deployment', 'admin'] },
  { key: 'database:cleanup', label: '清理数据库', roles: ['deployment', 'admin'] },
  { key: 'database:edit', label: '编辑数据库', roles: ['admin'] },
  { key: 'database:execute', label: '执行 SQL', roles: ['admin'] },

  // Docker
  { key: 'docker:view', label: '查看 Docker 状态', roles: ['deployment', 'admin'] },
  { key: 'docker:restart', label: '重启 Docker 容器', roles: ['deployment', 'admin'] },
  { key: 'docker:build', label: '构建 Docker 镜像', roles: ['deployment', 'admin'] },
  { key: 'docker:logs', label: '查看 Docker 日志', roles: ['deployment', 'admin'] },
  { key: 'docker:cleanup', label: '清理 Docker 资源', roles: ['deployment', 'admin'] },
  { key: 'docker:stop', label: '停止 Docker 容器', roles: ['admin'] },

  // 系统监控
  { key: 'monitoring:view', label: '查看系统监控', roles: ['deployment', 'admin'] },
  { key: 'monitoring:restart', label: '重启监控服务', roles: ['admin'] },
  { key: 'monitoring:stop', label: '停止监控服务', roles: ['admin'] },
  { key: 'monitoring:config', label: '配置监控系统', roles: ['admin'] },

  // 任务报告
  { key: 'report:view', label: '查看任务报告', roles: ['production', 'flight', 'deployment', 'admin'] },
  { key: 'report:create', label: '创建任务报告', roles: ['production', 'flight', 'admin'] },
  { key: 'report:export', label: '导出任务报告', roles: ['admin'] },
  { key: 'report:delete', label: '删除任务报告', roles: ['admin'] },

  // 气象站点
  { key: 'weather-station:view', label: '查看气象站点', roles: ['tester', 'deployment', 'admin'] },
  { key: 'weather-station:add', label: '添加气象站点', roles: ['admin'] },
  { key: 'weather-station:edit', label: '编辑气象站点', roles: ['admin'] },
  { key: 'weather-station:delete', label: '删除气象站点', roles: ['admin'] },
  { key: 'weather-station:toggle', label: '开关气象站点', roles: ['admin'] },

  // 气象数据源
  { key: 'weather-source:view', label: '查看气象数据源', roles: ['tester', 'deployment', 'admin'] },
  { key: 'weather-source:add', label: '添加气象数据源', roles: ['admin'] },
  { key: 'weather-source:edit', label: '编辑气象数据源', roles: ['admin'] },
  { key: 'weather-source:delete', label: '删除气象数据源', roles: ['admin'] },
  { key: 'weather-source:toggle', label: '开关气象数据源', roles: ['admin'] },
  { key: 'weather-source:config', label: '配置气象数据源', roles: ['admin'] },

  // 适航性评估
  { key: 'airworthiness:view', label: '查看适航性', roles: ['flight', 'tester', 'admin'] },
  { key: 'airworthiness:evaluate', label: '执行适航评估', roles: ['flight', 'tester', 'admin'] },
  { key: 'airworthiness:approve', label: '批准适航性', roles: ['admin'] },

  // 敏感性分析
  { key: 'sensitivity:view', label: '查看敏感性分析', roles: ['flight', 'tester', 'admin'] },
  { key: 'sensitivity:run', label: '运行敏感性分析', roles: ['flight', 'tester', 'admin'] },
  { key: 'sensitivity:export', label: '导出敏感性分析', roles: ['admin'] },

  // 实验对比
  { key: 'experiment:view', label: '查看实验对比', roles: ['flight', 'tester', 'admin'] },
  { key: 'experiment:run', label: '运行实验对比', roles: ['flight', 'tester', 'admin'] },
  { key: 'experiment:compare', label: '对比实验结果', roles: ['flight', 'tester', 'admin'] },

  // 团队论坛
  { key: 'forum:view', label: '查看论坛', roles: ['user', 'production', 'flight', 'tester', 'deployment', 'admin'] },
  { key: 'forum:post', label: '发帖', roles: ['production', 'flight', 'tester', 'deployment', 'admin'] },
  { key: 'forum:comment', label: '评论', roles: ['user', 'production', 'flight', 'tester', 'deployment', 'admin'] },
  { key: 'forum:delete', label: '删除帖子/评论', roles: ['admin'] },
  { key: 'forum:pin', label: '置顶帖子', roles: ['admin'] },
  { key: 'forum:admin', label: '论坛管理', roles: ['admin'] },

  // 用户统计
  { key: 'user-stats:view', label: '查看用户统计', roles: ['admin'] },
  { key: 'user-stats:export', label: '导出用户统计', roles: ['admin'] },

  // UTM 对接
  { key: 'utm:view', label: '查看 UTM 对接', roles: ['production', 'flight', 'admin'] },
  { key: 'utm:request', label: '发起 UTM 请求', roles: ['flight', 'admin'] },
  { key: 'utm:approve', label: '批准 UTM 请求', roles: ['admin'] },

  // API 配置
  { key: 'api-config:view', label: '查看 API 配置', roles: ['deployment', 'admin'] },
  { key: 'api-config:edit', label: '编辑 API 配置', roles: ['admin'] }
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
