import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { logAction, AUDIT_ACTIONS } from '../utils/audit'

const STORAGE_KEY = 'uav_auth_user'
const TOKEN_KEY = 'uav_auth_token_v1'
const DEMO_MODE_KEY = 'uav_demo_mode'
const DEMO_SHOWN_KEY = 'uav_demo_shown'

// ===== 权限矩阵来源（P1 动态权限支持，P0 先预留逻辑）=====
// Nacos 不可达时回退到本地默认矩阵 PERMISSION_MATRIX
const NACOS_PERMISSION_KEY = 'uav_nacos_permission_matrix'
const NACOS_FETCHED_KEY = 'uav_nacos_fetched'

// ===== 团队定义 =====
export const TEAMS = ['team-a', 'team-b', 'team-c']

export const TEAM_LABELS = {
  'team-a': '团队 A',
  'team-b': '团队 B',
  'team-c': '团队 C'
}

// ===== 数据范围定义 =====
export const DATA_SCOPES = ['personal', 'team', 'all']

export const DATA_SCOPE_LABELS = {
  personal: '个人',
  team: '团队',
  all: '全部'
}

export const DEFAULT_DATA_SCOPE_BY_ROLE = {
  user: 'personal',
  admin: 'all',
  production: 'team',
  flight: 'team',
  tester: 'team',
  deployment: 'team'
}

// 演示账号 → 团队映射
export const DEMO_USER_TEAM_MAP = {
  user01: 'team-a',
  flight01: 'team-b',
  prod01: 'team-a',
  test01: 'team-c',
  deploy01: 'team-c',
  admin01: 'team-a'
}

// ===== 角色定义 =====
export const ROLES = {
  USER: 'user',
  PRODUCTION: 'production',
  FLIGHT: 'flight',
  TESTER: 'tester',
  DEPLOYMENT: 'deployment',
  ADMIN: 'admin'
}

export const ROLE_LABELS = {
  [ROLES.USER]: '普通用户',
  [ROLES.PRODUCTION]: '生产人员',
  [ROLES.FLIGHT]: '飞控人员',
  [ROLES.TESTER]: '测试人员',
  [ROLES.DEPLOYMENT]: '部署人员',
  [ROLES.ADMIN]: '管理员'
}

export const ROLE_LABELS_EN = {
  [ROLES.USER]: 'Normal User',
  [ROLES.PRODUCTION]: 'Production Staff',
  [ROLES.FLIGHT]: 'Flight Control',
  [ROLES.TESTER]: 'Tester',
  [ROLES.DEPLOYMENT]: 'Deployment Engineer',
  [ROLES.ADMIN]: 'Administrator'
}

// ===== 权限矩阵（角色 → 可访问的路由 key 列表）=====
// 注意：dashboard、weather、settings、docs 为所有角色共有
// 其他页面按矩阵控制
export const PERMISSION_MATRIX = {
  [ROLES.USER]: [
    'dashboard', 'weather', 'orders', 'forum', 'settings', 'docs', 'theme-customizer'
  ],
  [ROLES.PRODUCTION]: [
    'dashboard', 'weather', 'orders', 'cockpit', 'tasks',
    'forum', 'utm-integration', 'task-report', 'settings', 'docs', 'theme-customizer'
  ],
  [ROLES.FLIGHT]: [
    'dashboard', 'weather', 'cockpit', 'tasks', 'path-planning',
    'airworthiness', 'model-evaluation', 'parameter-tuning', 'sensitivity-analysis',
    'experiment-compare', 'assimilation',
    'forum', 'utm-integration', 'task-report', 'settings', 'docs', 'theme-customizer'
  ],
  [ROLES.TESTER]: [
    'dashboard', 'weather', 'weather-station', 'weather-source', 'path-planning', 'airworthiness',
    'model-evaluation', 'parameter-tuning', 'sensitivity-analysis', 'experiment-compare',
    'assimilation', 'monitoring',
    'forum', 'settings', 'docs', 'theme-customizer'
  ],
  [ROLES.DEPLOYMENT]: [
    'dashboard', 'weather', 'weather-station', 'weather-source', 'monitoring', 'docker', 'docker-build',
    'api-config',
    'forum', 'settings', 'docs', 'theme-customizer'
  ],
  [ROLES.ADMIN]: [
    'dashboard', 'weather', 'weather-station', 'weather-source', 'orders', 'cockpit', 'tasks',
    'path-planning', 'airworthiness', 'model-evaluation', 'parameter-tuning', 'sensitivity-analysis',
    'experiment-compare', 'assimilation', 'monitoring', 'database',
    'docker', 'docker-build', 'api-config', 'permission-templates', 'utm-integration', 'task-report',
    'forum', 'user-stats',
    'settings', 'docs', 'theme-customizer', 'permission-debug'
  ]
}

// ===== 按钮级权限（页面内的操作权限）=====
export const ACTION_PERMISSIONS = {
  // ===== 通用权限 =====
  'common:export': [ROLES.ADMIN],
  'common:delete': [ROLES.ADMIN],
  'common:edit': [ROLES.ADMIN],

  // ===== 气象数据页面 =====
  'weather:view': [ROLES.USER, ROLES.PRODUCTION, ROLES.FLIGHT, ROLES.TESTER, ROLES.DEPLOYMENT, ROLES.ADMIN],
  'weather:download': [ROLES.FLIGHT, ROLES.TESTER, ROLES.ADMIN],
  'weather:advanced': [ROLES.FLIGHT, ROLES.TESTER, ROLES.ADMIN],

  // ===== 下单页面 =====
  'orders:view': [ROLES.USER, ROLES.PRODUCTION, ROLES.ADMIN],
  'orders:create': [ROLES.USER, ROLES.PRODUCTION, ROLES.ADMIN],
  'orders:advanced': [ROLES.FLIGHT, ROLES.ADMIN],
  'orders:cancel': [ROLES.USER, ROLES.PRODUCTION, ROLES.ADMIN],

  // ===== 智能驾驶舱 =====
  'cockpit:view': [ROLES.PRODUCTION, ROLES.FLIGHT, ROLES.ADMIN],
  'cockpit:control': [ROLES.FLIGHT, ROLES.ADMIN],
  'cockpit:emergency': [ROLES.FLIGHT, ROLES.ADMIN],

  // ===== 任务管理 =====
  'tasks:view': [ROLES.PRODUCTION, ROLES.FLIGHT, ROLES.ADMIN],
  'tasks:create': [ROLES.PRODUCTION, ROLES.ADMIN],
  'tasks:edit': [ROLES.PRODUCTION, ROLES.FLIGHT, ROLES.ADMIN],
  'tasks:delete': [ROLES.ADMIN],
  'tasks:assign': [ROLES.PRODUCTION, ROLES.ADMIN],

  // ===== API 配置页面 =====
  'api-config:view': [ROLES.DEPLOYMENT, ROLES.ADMIN],
  'api-config:edit': [ROLES.ADMIN],

  // ===== 下单页面高级配置 =====
  'orders:advanced': [ROLES.FLIGHT, ROLES.ADMIN],

  // ===== 路径规划执行 =====
  'planning:view': [ROLES.FLIGHT, ROLES.TESTER, ROLES.ADMIN],
  'planning:execute': [ROLES.FLIGHT, ROLES.TESTER, ROLES.ADMIN],
  'planning:save': [ROLES.FLIGHT, ROLES.TESTER, ROLES.ADMIN],

  // ===== 模型评估 =====
  'evaluation:view': [ROLES.FLIGHT, ROLES.TESTER, ROLES.ADMIN],
  'evaluation:run': [ROLES.FLIGHT, ROLES.TESTER, ROLES.ADMIN],
  'evaluation:compare': [ROLES.FLIGHT, ROLES.TESTER, ROLES.ADMIN],

  // ===== 算法参数调优 =====
  'tuning:view': [ROLES.FLIGHT, ROLES.TESTER, ROLES.ADMIN],
  'tuning:adjust': [ROLES.FLIGHT, ROLES.TESTER, ROLES.ADMIN],
  'tuning:save': [ROLES.ADMIN],

  // ===== 数据同化页面 =====
  'assimilation:view': [ROLES.TESTER, ROLES.DEPLOYMENT, ROLES.ADMIN],
  'assimilation:execute': [ROLES.TESTER, ROLES.DEPLOYMENT, ROLES.ADMIN],
  'assimilation:config': [ROLES.DEPLOYMENT, ROLES.ADMIN],
  'assimilation:download': [ROLES.TESTER, ROLES.DEPLOYMENT, ROLES.ADMIN],
  'assimilation:delete': [ROLES.DEPLOYMENT, ROLES.ADMIN],

  // ===== 数据库管理页面 =====
  'database:view': [ROLES.DEPLOYMENT, ROLES.ADMIN],
  'database:backup': [ROLES.DEPLOYMENT, ROLES.ADMIN],
  'database:restore': [ROLES.DEPLOYMENT, ROLES.ADMIN],
  'database:config': [ROLES.DEPLOYMENT, ROLES.ADMIN],
  'database:cleanup': [ROLES.DEPLOYMENT, ROLES.ADMIN],
  'database:edit': [ROLES.ADMIN],
  'database:execute': [ROLES.ADMIN],

  // ===== Docker 构建/状态页面 =====
  'docker:view': [ROLES.DEPLOYMENT, ROLES.ADMIN],
  'docker:restart': [ROLES.DEPLOYMENT, ROLES.ADMIN],
  'docker:build': [ROLES.DEPLOYMENT, ROLES.ADMIN],
  'docker:logs': [ROLES.DEPLOYMENT, ROLES.ADMIN],
  'docker:cleanup': [ROLES.DEPLOYMENT, ROLES.ADMIN],
  'docker:stop': [ROLES.ADMIN],

  // ===== 系统监控页面 =====
  'monitoring:view': [ROLES.DEPLOYMENT, ROLES.ADMIN],
  'monitoring:restart': [ROLES.ADMIN],
  'monitoring:stop': [ROLES.ADMIN],
  'monitoring:config': [ROLES.ADMIN],

  // ===== 任务报告页面 =====
  'report:view': [ROLES.PRODUCTION, ROLES.FLIGHT, ROLES.DEPLOYMENT, ROLES.ADMIN],
  'report:create': [ROLES.PRODUCTION, ROLES.FLIGHT, ROLES.ADMIN],
  'report:export': [ROLES.ADMIN],
  'report:delete': [ROLES.ADMIN],

  // ===== 气象站点管理 =====
  'weather-station:view': [ROLES.TESTER, ROLES.DEPLOYMENT, ROLES.ADMIN],
  'weather-station:add': [ROLES.ADMIN],
  'weather-station:edit': [ROLES.ADMIN],
  'weather-station:delete': [ROLES.ADMIN],
  'weather-station:toggle': [ROLES.ADMIN],

  // ===== 气象数据源页面 =====
  'weather-source:view': [ROLES.TESTER, ROLES.DEPLOYMENT, ROLES.ADMIN],
  'weather-source:add': [ROLES.ADMIN],
  'weather-source:edit': [ROLES.ADMIN],
  'weather-source:delete': [ROLES.ADMIN],
  'weather-source:toggle': [ROLES.ADMIN],
  'weather-source:config': [ROLES.ADMIN],

  // ===== 适航性评估 =====
  'airworthiness:view': [ROLES.FLIGHT, ROLES.TESTER, ROLES.ADMIN],
  'airworthiness:evaluate': [ROLES.FLIGHT, ROLES.TESTER, ROLES.ADMIN],
  'airworthiness:approve': [ROLES.ADMIN],

  // ===== 参数敏感性分析 =====
  'sensitivity:view': [ROLES.FLIGHT, ROLES.TESTER, ROLES.ADMIN],
  'sensitivity:run': [ROLES.FLIGHT, ROLES.TESTER, ROLES.ADMIN],
  'sensitivity:export': [ROLES.ADMIN],

  // ===== 实验对比工具 =====
  'experiment:view': [ROLES.FLIGHT, ROLES.TESTER, ROLES.ADMIN],
  'experiment:run': [ROLES.FLIGHT, ROLES.TESTER, ROLES.ADMIN],
  'experiment:compare': [ROLES.FLIGHT, ROLES.TESTER, ROLES.ADMIN],

  // ===== 团队论坛 =====
  'forum:view': [ROLES.USER, ROLES.PRODUCTION, ROLES.FLIGHT, ROLES.TESTER, ROLES.DEPLOYMENT, ROLES.ADMIN],
  'forum:post': [ROLES.PRODUCTION, ROLES.FLIGHT, ROLES.TESTER, ROLES.DEPLOYMENT, ROLES.ADMIN],
  'forum:comment': [ROLES.USER, ROLES.PRODUCTION, ROLES.FLIGHT, ROLES.TESTER, ROLES.DEPLOYMENT, ROLES.ADMIN],
  'forum:delete': [ROLES.ADMIN],
  'forum:pin': [ROLES.ADMIN],
  'forum:admin': [ROLES.ADMIN],

  // ===== 用户统计 =====
  'user-stats:view': [ROLES.ADMIN],
  'user-stats:export': [ROLES.ADMIN],

  // ===== UTM 对接 =====
  'utm:view': [ROLES.PRODUCTION, ROLES.FLIGHT, ROLES.ADMIN],
  'utm:request': [ROLES.FLIGHT, ROLES.ADMIN],
  'utm:approve': [ROLES.ADMIN]
}

// ===== 默认账号 =====
export const DEFAULT_ACCOUNTS = [
  { username: 'user01', password: 'User@123456', role: ROLES.USER, displayName: '普通用户测试账号' },
  { username: 'prod01', password: 'Prod@123456', role: ROLES.PRODUCTION, displayName: '生产人员测试账号' },
  { username: 'flight01', password: 'Flight@123456', role: ROLES.FLIGHT, displayName: '飞控人员测试账号' },
  { username: 'test01', password: 'Test@123456', role: ROLES.TESTER, displayName: '测试人员测试账号' },
  { username: 'deploy01', password: 'Deploy@123456', role: ROLES.DEPLOYMENT, displayName: '部署人员测试账号' },
  { username: 'admin01', password: 'Admin@123456', role: ROLES.ADMIN, displayName: '系统管理员' }
]

// 用于演示模式登录匹配的 map
const DEMO_USER_MAP = DEFAULT_ACCOUNTS.reduce((acc, a) => {
  acc[a.username] = a
  return acc
}, {})

// ===== Pinia Store =====
export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(null)
  const tokenPayload = ref(null)
  const tokenExpiresAt = ref(0)
  const loading = ref(false)
  const error = ref(null)
  const demoMode = ref(true)
  const demoShownOnce = ref(false) // 是否已显示过首次进入的 Toast
  const refreshIntervalId = ref(null) // token刷新定时器ID

  // === 计算属性 ===
  const isLoggedIn = computed(() => !!user.value)
  const role = computed(() => user.value?.role || null)
  const roleLabel = computed(() => ROLE_LABELS[role.value] || '')
  const roleLabelEn = computed(() => ROLE_LABELS_EN[role.value] || '')
  const displayName = computed(() => user.value?.displayName || user.value?.username || '')
  const username = computed(() => user.value?.username || '')
  const userId = computed(() => user.value?.id || user.value?.username || null)
  const team = computed(() => user.value?.team || '')
  const teamLabel = computed(() => TEAM_LABELS[team.value] || team.value || '')
  const dataScope = computed(() => user.value?.dataScope || (DEFAULT_DATA_SCOPE_BY_ROLE[role.value] || 'personal'))
  const dataScopeLabel = computed(() => DATA_SCOPE_LABELS[dataScope.value] || '')

  // 当前角色可访问的路由 key 列表
  const accessibleRoutes = computed(() => {
    if (!role.value) return []
    return PERMISSION_MATRIX[role.value] || []
  })

  // token剩余有效时间（秒）
  const tokenRemainingSeconds = computed(() => {
    if (!tokenExpiresAt.value) return 0
    const remaining = Math.max(0, Math.floor((tokenExpiresAt.value - Date.now()) / 1000))
    return remaining
  })

  // === 方法 ===
  function hasRouteAccess(routeKey) {
    return accessibleRoutes.value.includes(routeKey)
  }

  function hasAction(actionKey) {
    if (!role.value) return false
    const allowed = ACTION_PERMISSIONS[actionKey]
    if (!allowed) return false
    return allowed.includes(role.value)
  }

  function canSee(owner, itemTeam) {
    if (dataScope.value === 'all') return true
    if (dataScope.value === 'personal') return owner && userId.value && String(owner) === String(userId.value)
    if (dataScope.value === 'team') return itemTeam && team.value && itemTeam === team.value
    return true
  }

  function getVisibleOwnerIds() {
    if (dataScope.value === 'all') return null
    if (dataScope.value === 'personal') return userId.value ? [userId.value] : []
    if (dataScope.value === 'team') return [team.value]
    return null
  }

  function updateTeam(newTeam) {
    if (!TEAMS.includes(newTeam)) return false
    if (!user.value) return false
    const oldTeam = user.value.team || ''
    user.value.team = newTeam
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(user.value))
    } catch (e) {}
    try {
      logAction({
        action: AUDIT_ACTIONS.CHANGE_TEAM,
        target: newTeam,
        detail: `${oldTeam || '-'} → ${newTeam}`,
        level: 'info'
      })
    } catch (e) {
      console.warn('[AUTH] 审计记录失败', e)
    }
    return true
  }

  function updateDataScope(newScope) {
    if (!DATA_SCOPES.includes(newScope)) return false
    if (!user.value) return false
    const oldScope = user.value.dataScope || ''
    user.value.dataScope = newScope
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(user.value))
    } catch (e) {}
    try {
      logAction({
        action: AUDIT_ACTIONS.CHANGE_DATA_SCOPE,
        target: newScope,
        detail: `${oldScope || '-'} → ${newScope}`,
        level: 'info'
      })
    } catch (e) {
      console.warn('[AUTH] 审计记录失败', e)
    }
    return true
  }

  function setUser(userData) {
    user.value = userData
    if (userData) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(userData))
      } catch (e) {
        console.warn('Failed to persist user to localStorage', e)
      }
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  }

  function initFromStorage() {
    if (user.value) return
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        user.value = JSON.parse(raw)
      }
      const demoModeRaw = localStorage.getItem(DEMO_MODE_KEY)
      if (demoModeRaw !== null) {
        demoMode.value = demoModeRaw === 'true'
      }
      const shownRaw = localStorage.getItem(DEMO_SHOWN_KEY)
      if (shownRaw !== null) {
        demoShownOnce.value = shownRaw === 'true'
      }
      const tokenRaw = localStorage.getItem(TOKEN_KEY)
      if (tokenRaw) {
        try {
          const parsed = JSON.parse(tokenRaw)
          token.value = parsed.token || null
          tokenPayload.value = parsed.payload || null
          tokenExpiresAt.value = parsed.expiresAt || 0
        } catch (e) {}
      }
    } catch (e) {
      console.warn('Failed to parse user from localStorage', e)
      localStorage.removeItem(STORAGE_KEY)
    }

    // Nacos 权限预留：若 localStorage 中存在 Nacos 拉取结果，直接合并（不覆盖角色列表，仅合并页面/按钮权限）
    try {
      const nacosMatrixRaw = localStorage.getItem(NACOS_PERMISSION_KEY)
      if (nacosMatrixRaw) {
        const nacosMatrix = JSON.parse(nacosMatrixRaw)
        if (nacosMatrix && typeof nacosMatrix === 'object') {
          // 合并到 PERMISSION_MATRIX：Nacos 优先（生产环境由运维配置）
          Object.keys(nacosMatrix).forEach((role) => {
            if (PERMISSION_MATRIX[role]) {
              const merged = new Set([...PERMISSION_MATRIX[role], ...(nacosMatrix[role] || [])])
              PERMISSION_MATRIX[role] = Array.from(merged)
            }
          })
        }
      }
    } catch (e) {
      console.warn('Failed to merge Nacos permission matrix', e)
    }

    // 初始化时启动 token 刷新定时器
    if (token.value && !isTokenExpired()) {
      startTokenRefreshTimer()
    }
  }

  function setDemoMode(isDemo) {
    demoMode.value = isDemo
    try {
      localStorage.setItem(DEMO_MODE_KEY, String(isDemo))
    } catch (e) {
      console.warn('Failed to persist demo mode', e)
    }
  }

  function decodeBase64Url(str) {
    try {
      const base64 = String(str).replace(/-/g, '+').replace(/_/g, '/')
      const decoded = typeof atob === 'function'
        ? atob(base64)
        : Buffer.from(base64, 'base64').toString('utf-8')
      return JSON.parse(decoded)
    } catch (e) {
      return null
    }
  }

  function setToken(tokenStr) {
    if (!tokenStr) {
      token.value = null
      tokenPayload.value = null
      tokenExpiresAt.value = 0
      try { localStorage.removeItem(TOKEN_KEY) } catch (e) {}
      stopTokenRefreshTimer()
      return null
    }

    let payload = null
    let expiresAt = 0

    if (demoMode.value) {
      expiresAt = Date.now() + 3600 * 1000
      payload = {
        sub: user.value?.username || 'demo',
        role: user.value?.role || ROLES.USER,
        demo: true,
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(expiresAt / 1000)
      }
    } else {
      try {
        const parts = String(tokenStr).split('.')
        if (parts.length >= 2) {
          payload = decodeBase64Url(parts[1])
        }
      } catch (e) {
        console.warn('[AUTH] JWT 解析失败:', e)
      }
      if (payload && payload.exp) {
        expiresAt = payload.exp * 1000
      } else {
        expiresAt = Date.now() + 3600 * 1000
      }
    }

    token.value = tokenStr
    tokenPayload.value = payload
    tokenExpiresAt.value = expiresAt
    try {
      localStorage.setItem(TOKEN_KEY, JSON.stringify({
        token: tokenStr,
        payload,
        expiresAt
      }))
    } catch (e) {
      console.warn('[AUTH] token 持久化失败:', e)
    }

    // 启动 token 刷新定时器
    startTokenRefreshTimer()

    return payload
  }

  function isTokenExpired(thresholdSec = 60) {
    if (!tokenExpiresAt.value) return true
    const now = Date.now()
    return now + (thresholdSec * 1000) > tokenExpiresAt.value
  }

  /**
   * 启动 token 自动刷新定时器
   * 在 token 过期前 5 分钟自动刷新
   */
  function startTokenRefreshTimer() {
    // 先停止已有定时器
    stopTokenRefreshTimer()

    const refreshBeforeSec = 300 // 过期前 5 分钟刷新
    let nextRefreshMs = Math.max(0, tokenExpiresAt.value - Date.now() - refreshBeforeSec * 1000)

    // 如果剩余时间不足，立即刷新
    if (nextRefreshMs < 1000) {
      refreshToken().catch(e => console.error('[AUTH] 立即刷新失败:', e))
      nextRefreshMs = 300000 // 5分钟后再次检查
    }

    console.info(`[AUTH] Token 刷新定时器已启动，下次刷新时间: ${new Date(Date.now() + nextRefreshMs).toLocaleString()}`)

    refreshIntervalId.value = setTimeout(async () => {
      try {
        await refreshToken()
      } catch (e) {
        console.error('[AUTH] 定时刷新失败:', e)
        // 刷新失败后 30 秒重试
        if (isLoggedIn.value) {
          refreshIntervalId.value = setTimeout(() => {
            startTokenRefreshTimer()
          }, 30000)
        }
      }
    }, nextRefreshMs)
  }

  /**
   * 停止 token 刷新定时器
   */
  function stopTokenRefreshTimer() {
    if (refreshIntervalId.value) {
      clearTimeout(refreshIntervalId.value)
      refreshIntervalId.value = null
    }
  }

  async function refreshToken() {
    try {
      if (demoMode.value) {
        const newExpiresAt = Date.now() + 3600 * 1000
        tokenExpiresAt.value = newExpiresAt
        if (tokenPayload.value) {
          tokenPayload.value = { ...tokenPayload.value, exp: Math.floor(newExpiresAt / 1000) }
        }
        try {
          const stored = JSON.parse(localStorage.getItem(TOKEN_KEY) || '{}')
          stored.expiresAt = newExpiresAt
          if (stored.payload) stored.payload.exp = Math.floor(newExpiresAt / 1000)
          localStorage.setItem(TOKEN_KEY, JSON.stringify(stored))
        } catch (e) {}

        // 重新启动定时器
        startTokenRefreshTimer()
        return { ok: true, mode: 'demo', expiresAt: newExpiresAt }
      }

      try {
        const { default: api } = await import('../api')
        const res = await api.post('/auth/refresh')
        if (res && res.token) {
          setToken(res.token)
          return { ok: true, mode: 'prod' }
        }
        throw new Error('刷新接口未返回 token')
      } catch (e) {
        console.warn('[AUTH] 生产环境 token 刷新接口未接入，降级为演示续期:', e)
        const newExpiresAt = Date.now() + 3600 * 1000
        tokenExpiresAt.value = newExpiresAt

        // 重新启动定时器
        startTokenRefreshTimer()
        return { ok: true, mode: 'fallback', expiresAt: newExpiresAt }
      }
    } catch (e) {
      console.error('[AUTH] token 刷新失败:', e)
      throw e
    }
  }

  async function requireSensitiveConfirmation(actionLabel) {
    try {
      const label = actionLabel || '该操作'
      const passwordPrompt = demoMode.value
        ? '（演示模式：输入任意字符即可通过）'
        : '（请输入登录密码）'
      const message = `即将执行敏感操作：${label}\n\n请确认已了解操作后果${passwordPrompt}`

      await ElMessageBox.prompt(
        message,
        '敏感操作二次确认',
        {
          confirmButtonText: '确认执行',
          cancelButtonText: '取消',
          confirmButtonClass: 'el-button--danger',
          inputType: 'password',
          inputPlaceholder: '请输入密码以确认',
          showCancelButton: true,
          distinguishCancelAndClose: true,
          beforeClose: (action, instance, done) => {
            if (action !== 'confirm') { done(); return }
            const val = String(instance.inputValue || '').trim()
            if (!val) {
              ElMessage.warning('请输入密码以确认操作')
              return
            }
            if (!demoMode.value && user.value?.password && val !== user.value.password) {
              ElMessage.error('密码错误，操作已取消')
              return
            }
            done()
          }
        }
      )
      return true
    } catch (e) {
      if (e !== 'cancel' && e !== 'close' && !(e && typeof e === 'object' && e.action === 'cancel')) {
        console.warn('[AUTH] requireSensitiveConfirmation error:', e)
      }
      return false
    }
  }

  function markDemoShown() {
    demoShownOnce.value = true
    try {
      localStorage.setItem(DEMO_SHOWN_KEY, 'true')
    } catch (e) {}
  }

  async function login(username, password, selectedRole) {
    loading.value = true
    error.value = null

    try {
      const matched = DEMO_USER_MAP[username]
      if (matched && matched.password === password) {
        const userData = {
          id: DEFAULT_ACCOUNTS.findIndex(a => a.username === username) + 1,
          username: matched.username,
          role: matched.role,
          displayName: matched.displayName,
          demo: true,
          team: DEMO_USER_TEAM_MAP[username] || 'team-a',
          dataScope: DEFAULT_DATA_SCOPE_BY_ROLE[matched.role] || 'personal',
          loginTime: new Date().toISOString()
        }
        setUser(userData)
        setDemoMode(true)
        setToken(`demo.${btoa(username)}.${Date.now()}`)
        return userData
      }

      if (selectedRole && ROLES[selectedRole.toUpperCase()]) {
        const resolvedRole = ROLES[selectedRole.toUpperCase()]
        const userData = {
          id: 100,
          username,
          role: resolvedRole,
          displayName: `${ROLE_LABELS[resolvedRole]} - ${username}`,
          demo: true,
          team: DEMO_USER_TEAM_MAP[username] || 'team-a',
          dataScope: DEFAULT_DATA_SCOPE_BY_ROLE[resolvedRole] || 'personal',
          loginTime: new Date().toISOString()
        }
        setUser(userData)
        setDemoMode(true)
        setToken(`demo.${btoa(username)}.${Date.now()}`)
        return userData
      }

      throw new Error('用户名或密码错误')
    } catch (err) {
      error.value = err?.message || '登录失败，请检查用户名和密码'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function register(username, password, selectedRole) {
    loading.value = true
    error.value = null
    try {
      if (!selectedRole || !ROLES[selectedRole.toUpperCase()]) {
        throw new Error('请选择用户类型')
      }
      if (!username || username.length < 3) {
        throw new Error('用户名至少3个字符')
      }
      if (!password || password.length < 6) {
        throw new Error('密码至少6个字符')
      }
      const resolvedRole = ROLES[selectedRole.toUpperCase()]
      const userData = {
        id: Date.now(),
        username,
        role: resolvedRole,
        displayName: `${ROLE_LABELS[resolvedRole]} - ${username}`,
        demo: true,
        team: DEMO_USER_TEAM_MAP[username] || 'team-a',
        dataScope: DEFAULT_DATA_SCOPE_BY_ROLE[resolvedRole] || 'personal',
        loginTime: new Date().toISOString()
      }
      setUser(userData)
      setDemoMode(true)
      return userData
    } catch (err) {
      error.value = err?.message || '注册失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function resetPassword(username, selectedRole, newPassword) {
    loading.value = true
    error.value = null
    try {
      if (!selectedRole || !ROLES[selectedRole.toUpperCase()]) {
        throw new Error('请选择用户类型')
      }
      if (!username) throw new Error('请输入用户名')
      if (!newPassword || newPassword.length < 6) {
        throw new Error('新密码至少6个字符')
      }
      // 演示模式：重置密码成功即返回（不实际修改任何持久数据）
      return { success: true, message: '密码已重置成功，请使用新密码登录' }
    } catch (err) {
      error.value = err?.message || '重置密码失败'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 从 Nacos 拉取权限矩阵（P1 生产模式正式启用，P0 预留接口）
   * 失败时自动回退到本地 PERMISSION_MATRIX
   */
  async function fetchPermissionFromNacos() {
    // TODO: 接入真实 Nacos API（P1 实现）
    // const res = await fetch('/nacos/v1/cs/configs?dataId=uav-permission-matrix&group=DEFAULT_GROUP')
    // const json = await res.json()
    // localStorage.setItem(NACOS_PERMISSION_KEY, JSON.stringify(json.content))
    localStorage.setItem(NACOS_FETCHED_KEY, 'true')
    return { ok: true, note: 'P1 启用：当前为占位实现，后续接入真实 Nacos 接口' }
  }

  async function logout() {
    stopTokenRefreshTimer()
    setUser(null)
    token.value = null
    tokenPayload.value = null
    tokenExpiresAt.value = 0
    try { localStorage.removeItem(TOKEN_KEY) } catch (e) {}
  }

  return {
    // state
    user,
    token,
    tokenPayload,
    tokenExpiresAt,
    loading,
    error,
    demoMode,
    demoShownOnce,
    // computed
    isLoggedIn,
    role,
    roleLabel,
    roleLabelEn,
    displayName,
    username,
    userId,
    team,
    teamLabel,
    dataScope,
    dataScopeLabel,
    accessibleRoutes,
    tokenRemainingSeconds,
    // methods
    hasRouteAccess,
    hasAction,
    canSee,
    getVisibleOwnerIds,
    updateTeam,
    updateDataScope,
    setUser,
    setToken,
    isTokenExpired,
    refreshToken,
    startTokenRefreshTimer,
    stopTokenRefreshTimer,
    requireSensitiveConfirmation,
    initFromStorage,
    setDemoMode,
    markDemoShown,
    login,
    register,
    resetPassword,
    fetchPermissionFromNacos,
    logout
  }
})


