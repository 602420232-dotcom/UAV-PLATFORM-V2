import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { ROLES } from './auth'
import { isNightTime as computeIsNightTime, nextTransitionSeconds } from '../composables/useSunTime'

const APP_STORAGE_KEY = 'uav_app_config'
const THEME_STORAGE_KEY = 'uav_theme_v1'
const THEME_MODE_STORAGE_KEY = 'uav_theme_mode_v1'

const DARK_THEMES = ['dark', 'brand', 'highContrast']
const LIGHT_THEMES = ['light']

// 不同角色的默认首页
const DEFAULT_HOME_BY_ROLE = {
  [ROLES.USER]: 'dashboard',
  [ROLES.PRODUCTION]: 'dashboard',
  [ROLES.FLIGHT]: 'dashboard',
  [ROLES.TESTER]: 'dashboard',
  [ROLES.DEPLOYMENT]: 'monitoring',
  [ROLES.ADMIN]: 'dashboard'
}

function applyDataThemeToDocument(val) {
  if (typeof document === 'undefined') return
  document.documentElement.setAttribute('data-theme', val)
  const isDarkMode = DARK_THEMES.includes(val)
  document.documentElement.style.setProperty('--color-blue-filter', isDarkMode ? '0.85' : '1')
}

export const useAppStore = defineStore('app', () => {
  const collapsed = ref(true)
  const sidebarManual = ref(false)
  const theme = ref('light')
  const themeMode = ref('auto') // 'light' | 'dark' | 'brand' | 'highContrast' | 'auto'
  const language = ref('zh')
  const defaultRoute = ref('')
  const envMode = ref('demo')
  const isNight = ref(false)
  let autoThemeTimer = null

  const effectiveTheme = computed(() => {
    if (themeMode.value === 'auto') {
      return isNight.value ? 'dark' : 'light'
    }
    return themeMode.value
  })

  const isDark = computed(() => DARK_THEMES.includes(effectiveTheme.value))

  function applyCurrentTheme() {
    theme.value = effectiveTheme.value
    applyDataThemeToDocument(theme.value)
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(THEME_STORAGE_KEY, theme.value)
    }
  }

  function scheduleAutoThemeCheck() {
    if (autoThemeTimer) {
      clearTimeout(autoThemeTimer)
      autoThemeTimer = null
    }
    if (typeof window === 'undefined') return
    const seconds = Math.min(nextTransitionSeconds(), 3600)
    autoThemeTimer = setTimeout(() => {
      isNight.value = computeIsNightTime()
      if (themeMode.value === 'auto') {
        applyCurrentTheme()
      }
      scheduleAutoThemeCheck()
    }, seconds * 1000)
  }

  function init() {
    try {
      const raw = localStorage.getItem(APP_STORAGE_KEY)
      if (raw) {
        const saved = JSON.parse(raw)
        if (saved.collapsed !== undefined) collapsed.value = saved.collapsed
        if (saved.sidebarManual !== undefined) sidebarManual.value = saved.sidebarManual
        if (saved.theme) theme.value = saved.theme
        if (saved.language) language.value = saved.language
        if (saved.defaultRoute !== undefined) defaultRoute.value = saved.defaultRoute
        if (saved.envMode) envMode.value = saved.envMode
      }
    } catch (e) {
      console.warn('Failed to parse app config from localStorage', e)
    }
    // theme / themeMode 独立 key 优先
    try {
      const themeRaw = localStorage.getItem(THEME_STORAGE_KEY)
      if (themeRaw) theme.value = themeRaw
    } catch (_) {}
    try {
      const modeRaw = localStorage.getItem(THEME_MODE_STORAGE_KEY)
      if (modeRaw) themeMode.value = modeRaw
    } catch (_) {}

    isNight.value = computeIsNightTime()
    // 对于 auto 模式，用日夜判断覆盖 theme
    if (themeMode.value === 'auto') {
      theme.value = isNight.value ? 'dark' : 'light'
    }
    applyDataThemeToDocument(theme.value)

    // 读取独立的 envMode key（与 SystemMonitor 共享持久化）
    try {
      const envRaw = localStorage.getItem('uav_app_env_mode_v1')
      if (envRaw) envMode.value = envRaw
    } catch (e) {}

    // 启动自动主题调度
    scheduleAutoThemeCheck()
  }

  function persist() {
    try {
      localStorage.setItem(
        APP_STORAGE_KEY,
        JSON.stringify({
          collapsed: collapsed.value,
          theme: theme.value,
          themeMode: themeMode.value,
          language: language.value,
          defaultRoute: defaultRoute.value,
          envMode: envMode.value
        })
      )
    } catch (e) {}
    try {
      localStorage.setItem(THEME_MODE_STORAGE_KEY, String(themeMode.value))
    } catch (e) {}
  }

  function setEnvMode(val) {
    envMode.value = val
    persist()
    try {
      localStorage.setItem('uav_app_env_mode_v1', String(val))
    } catch (e) {}
  }

  function toggleSidebar() {
    collapsed.value = !collapsed.value
    persist()
  }

  function setCollapsed(val) {
    collapsed.value = val
    persist()
  }

  function toggleTheme() {
    // 当处于 auto 模式时，先切到 light；否则按固定顺序
    if (themeMode.value === 'auto') {
      themeMode.value = 'light'
    } else {
      const order = ['light', 'dark', 'brand', 'highContrast', 'auto']
      const idx = order.indexOf(themeMode.value)
      themeMode.value = order[(idx + 1) % order.length]
    }
    isNight.value = computeIsNightTime()
    applyCurrentTheme()
    persist()
  }

  function setTheme(val) {
    const valid = ['light', 'dark', 'brand', 'highContrast', 'auto']
    themeMode.value = valid.includes(val) ? val : 'light'
    isNight.value = computeIsNightTime()
    applyCurrentTheme()
    persist()
  }

  function setThemeMode(val) {
    const valid = ['light', 'dark', 'brand', 'highContrast', 'auto']
    themeMode.value = valid.includes(val) ? val : 'auto'
    isNight.value = computeIsNightTime()
    applyCurrentTheme()
    persist()
  }

  function refreshNightStatus() {
    isNight.value = computeIsNightTime()
    if (themeMode.value === 'auto') applyCurrentTheme()
  }

  function setLanguage(val) {
    language.value = val
    persist()
  }

  function setDefaultRoute(routeKey) {
    defaultRoute.value = routeKey
    persist()
  }

  function getDefaultRoute(role) {
    if (defaultRoute.value) return defaultRoute.value
    return DEFAULT_HOME_BY_ROLE[role] || 'dashboard'
  }

  init()

  // 主题模式变化时自动持久化 + 应用
  watch(themeMode, () => {
    isNight.value = computeIsNightTime()
    applyCurrentTheme()
    persist()
  })

  return {
    collapsed,
    theme,
    themeMode,
    effectiveTheme,
    language,
    defaultRoute,
    envMode,
    isDark,
    isNight,
    toggleSidebar,
    setCollapsed,
    toggleTheme,
    setTheme,
    setThemeMode,
    setLanguage,
    setDefaultRoute,
    setEnvMode,
    getDefaultRoute,
    refreshNightStatus,
    init
  }
})

