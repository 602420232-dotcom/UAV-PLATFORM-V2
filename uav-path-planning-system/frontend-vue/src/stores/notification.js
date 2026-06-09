import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

const STORAGE_KEY = 'uav_notifications_v1'
const MAX_NOTIFICATIONS = 200

const VALID_TYPES = ['info', 'success', 'warning', 'danger']
const VALID_SOURCES = ['task', 'weather', 'uav', 'planning', 'apiConfig', 'utm', 'system']

function genId() {
  return 'n_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8)
}

function normalizeType(type) {
  return VALID_TYPES.includes(type) ? type : 'info'
}

function normalizeSource(source) {
  return VALID_SOURCES.includes(source) ? source : 'system'
}

const DEFAULT_PREFS = {
  task: true,
  weather: true,
  uav: true,
  planning: true,
  apiConfig: true,
  utm: true,
  system: true,
  desktop: false
}

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch (_) {
    return null
  }
}

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref([])
  const subscriptionPrefs = ref({ ...DEFAULT_PREFS })

  const unreadCount = computed(() => {
    return notifications.value.reduce((sum, n) => sum + (n.read ? 0 : 1), 0)
  })

  function init() {
    const data = loadFromStorage()
    if (data) {
      if (Array.isArray(data.notifications)) {
        notifications.value = data.notifications.slice(0, MAX_NOTIFICATIONS)
      }
      if (data.subscriptionPrefs && typeof data.subscriptionPrefs === 'object') {
        subscriptionPrefs.value = { ...DEFAULT_PREFS, ...data.subscriptionPrefs }
      }
    }
  }

  function persist() {
    try {
      const payload = {
        notifications: notifications.value.slice(0, MAX_NOTIFICATIONS),
        subscriptionPrefs: { ...subscriptionPrefs.value }
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
    } catch (_) {}
  }

  function isSourceEnabled(source) {
    return subscriptionPrefs.value[source] !== false
  }

  function addNotification({ type, title, message, source }) {
    const normalizedSource = normalizeSource(source)
    if (!isSourceEnabled(normalizedSource)) return null
    const item = {
      id: genId(),
      type: normalizeType(type),
      title: title || '通知',
      message: message || '',
      source: normalizedSource,
      read: false,
      createdAt: new Date().toISOString()
    }
    notifications.value.unshift(item)
    if (notifications.value.length > MAX_NOTIFICATIONS) {
      notifications.value = notifications.value.slice(0, MAX_NOTIFICATIONS)
    }
    persist()
    return item
  }

  function markAllRead() {
    if (notifications.value.length === 0) return
    let changed = false
    notifications.value.forEach((n) => {
      if (!n.read) {
        n.read = true
        changed = true
      }
    })
    if (changed) persist()
  }

  function markAsRead(id) {
    const item = notifications.value.find((n) => n.id === id)
    if (item && !item.read) {
      item.read = true
      persist()
    }
  }

  function removeNotification(id) {
    const before = notifications.value.length
    notifications.value = notifications.value.filter((n) => n.id !== id)
    if (notifications.value.length !== before) persist()
  }

  function clearAll() {
    if (notifications.value.length > 0) {
      notifications.value = []
      persist()
    }
  }

  function filterBySource(source) {
    if (!source || source === 'all') return notifications.value
    return notifications.value.filter((n) => n.source === source)
  }

  function updateSubscriptionPrefs(prefs) {
    subscriptionPrefs.value = { ...subscriptionPrefs.value, ...prefs }
    persist()
  }

  function requestDesktopPermission() {
    if (typeof window === 'undefined' || typeof Notification === 'undefined') {
      return Promise.resolve('unsupported')
    }
    if (Notification.permission === 'granted') return Promise.resolve('granted')
    if (Notification.permission === 'denied') return Promise.resolve('denied')
    try {
      return Notification.requestPermission()
    } catch (_) {
      return Promise.resolve('unsupported')
    }
  }

  function sendDesktop(notification) {
    if (!notification) return
    if (typeof window === 'undefined' || typeof Notification === 'undefined') return
    if (Notification.permission !== 'granted') return
    try {
      const body = notification.message || ''
      const title = notification.title || '系统通知'
      const icon = '/favicon.svg'
      new Notification(title, { body, icon })
    } catch (_) {}
  }

  function pushWithDesktop({ type, title, message, source }) {
    const item = addNotification({ type, title, message, source })
    if (!item) return null
    if (subscriptionPrefs.value.desktop) {
      sendDesktop(item)
    }
    return item
  }

  // 演示模式健康检查定时器：每 2 分钟随机推送一条
  let healthTimer = null
  function startHealthCheck(intervalMs = 120000) {
    stopHealthCheck()
    if (typeof window === 'undefined') return
    const sampleMessages = [
      { title: '系统健康检查', message: '当前系统运行正常，无异常告警。', type: 'success' },
      { title: '气象数据同步', message: '已拉取最新气象数据（演示模式）。', type: 'info' },
      { title: '任务调度', message: '调度器已处理 5 条任务队列。', type: 'info' },
      { title: '路径规划引擎', message: '规划引擎空闲，等待新任务。', type: 'info' },
      { title: '无人机状态', message: '全部无人机通讯正常。', type: 'success' },
      { title: '存储状态', message: '本地缓存占用约 2MB。', type: 'info' }
    ]
    healthTimer = window.setInterval(() => {
      const sample = sampleMessages[Math.floor(Math.random() * sampleMessages.length)]
      pushWithDesktop({
        type: sample.type,
        title: sample.title,
        message: sample.message,
        source: 'system'
      })
    }, intervalMs)
  }

  function stopHealthCheck() {
    if (healthTimer !== null) {
      try {
        window.clearInterval(healthTimer)
      } catch (_) {}
      healthTimer = null
    }
  }

  // 偏好变化时持久化
  watch(subscriptionPrefs, () => persist(), { deep: true })

  // 初始化
  init()

  return {
    notifications,
    unreadCount,
    subscriptionPrefs,
    addNotification,
    markAllRead,
    markAsRead,
    removeNotification,
    clearAll,
    filterBySource,
    updateSubscriptionPrefs,
    requestDesktopPermission,
    sendDesktop,
    pushWithDesktop,
    persist,
    init,
    startHealthCheck,
    stopHealthCheck
  }
})
