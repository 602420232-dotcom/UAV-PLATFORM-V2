import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import wsService from '@/utils/websocket'
import { ElNotification } from 'element-plus'

export const useNotificationStore = defineStore('notification', () => {
  // 状态
  const notifications = ref([])
  const unreadCount = ref(0)
  const isConnected = ref(false)
  const showNotificationDialog = ref(false)
  const currentNotification = ref(null)
  const doNotDisturb = ref(false) // 免打扰模式

  // 通知偏好设置
  const subscriptionPrefs = ref({
    task: true,
    weather: true,
    uav: true,
    planning: true,
    apiConfig: true,
    utm: true,
    system: true,
    desktop: true
  })

  // 初始化：从 localStorage 加载设置
  function init() {
    try {
      const saved = localStorage.getItem('notification_doNotDisturb')
      if (saved !== null) {
        doNotDisturb.value = saved === 'true'
      }
    } catch (e) {
      console.error('[NotificationStore] Failed to load settings:', e)
    }
  }

  // 保存免打扰设置
  function setDoNotDisturb(enabled) {
    doNotDisturb.value = enabled
    try {
      localStorage.setItem('notification_doNotDisturb', String(enabled))
    } catch (e) {
      console.error('[NotificationStore] Failed to save settings:', e)
    }
  }

  // 计算属性
  const unreadNotifications = computed(() => {
    return notifications.value.filter(n => !n.read)
  })

  const hasUnread = computed(() => unreadCount.value > 0)

  // 方法
  function connect(userId) {
    // 监听WebSocket事件
    wsService.on('connect', handleConnect)
    wsService.on('disconnect', handleDisconnect)
    wsService.on('message', handleMessage)
    
    // 连接WebSocket
    wsService.connect(userId)
  }

  function disconnect() {
    wsService.disconnect()
    wsService.off('connect', handleConnect)
    wsService.off('disconnect', handleDisconnect)
    wsService.off('message', handleMessage)
  }

  function handleConnect(data) {
    isConnected.value = true
    console.log('[NotificationStore] WebSocket connected')
  }

  function handleDisconnect() {
    isConnected.value = false
    console.log('[NotificationStore] WebSocket disconnected')
  }

  function handleMessage(data) {
    console.log('[NotificationStore] Received notification:', data)
    
    // 添加到通知列表
    addNotification({
      id: data.id || `n_${Date.now()}`,
      type: data.type || 'info',
      title: data.title || getNotificationTitle(data.type),
      message: data.message || data.content || '',
      postId: data.postId || null,
      postTitle: data.postTitle || '',
      from: data.from || '系统',
      source: data.source || 'system',
      read: false,
      timestamp: data.timestamp || new Date().toISOString(),
      createdAt: data.timestamp || data.createdAt || new Date().toISOString()
    })
  }

  function getNotificationTitle(type) {
    const titles = {
      reply: '新回复',
      mention: '@提及',
      system: '系统通知',
      like: '点赞',
      confirmation: '操作确认'
    }
    return titles[type] || '新通知'
  }

  function addNotification(notification) {
    // 添加到列表头部
    notifications.value.unshift(notification)
    
    // 更新未读计数
    unreadCount.value++
    
    // 显示桌面通知
    showDesktopNotification(notification)
  }

  function showDesktopNotification(notification) {
    // 免打扰模式下不弹窗
    if (doNotDisturb.value) {
      return
    }
    
    // 静默消息不弹窗
    if (notification.silent) {
      return
    }
    
    ElNotification({
      title: `${notification.title}`,
      message: notification.message,
      duration: 5000,
      type: notification.type === 'system' ? 'success' : 'info',
      position: 'top-right',
      onClick: () => {
        // 点击跳转到相关帖子
        if (notification.postId) {
          window.location.hash = `/forum?post=${notification.postId}`
        }
      }
    })
  }

  // 推送通知（带桌面通知）
  function pushWithDesktop(notification) {
    addNotification({
      id: notification.id || `n_${Date.now()}`,
      type: notification.type || 'info',
      title: notification.title || '',
      message: notification.message || '',
      source: notification.source || 'system',
      read: false,
      timestamp: new Date().toISOString()
    })
  }

  function markAsRead(notificationId) {
    const notification = notifications.value.find(n => n.id === notificationId)
    if (notification && !notification.read) {
      notification.read = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
  }

  function markAllAsRead() {
    notifications.value.forEach(n => {
      n.read = true
    })
    unreadCount.value = 0
  }

  function removeNotification(notificationId) {
    const index = notifications.value.findIndex(n => n.id === notificationId)
    if (index !== -1) {
      const notification = notifications.value[index]
      if (!notification.read) {
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
      notifications.value.splice(index, 1)
    }
  }

  function clearAll() {
    notifications.value = []
    unreadCount.value = 0
  }

  function openNotificationDialog() {
    showNotificationDialog.value = true
    // 打开对话框时标记所有为已读
    markAllAsRead()
  }

  function closeNotificationDialog() {
    showNotificationDialog.value = false
    currentNotification.value = null
  }

  // 手动触发通知（用于测试）
  function triggerTestNotification() {
    const testNotification = {
      id: `test_${Date.now()}`,
      type: 'reply',
      title: '新回复',
      message: '这是一条测试通知',
      postId: '2',
      postTitle: '关于DE-RRT*算法参数调优的讨论',
      from: '测试用户',
      read: false,
      timestamp: new Date().toISOString()
    }
    addNotification(testNotification)
  }

  // 按来源筛选通知
  function filterBySource(source) {
    if (!source || source === 'all') {
      return notifications.value
    }
    return notifications.value.filter(n => n.source === source)
  }

  return {
    // 状态
    notifications,
    unreadCount,
    isConnected,
    showNotificationDialog,
    currentNotification,
    subscriptionPrefs,
    doNotDisturb,

    // 计算属性
    unreadNotifications,
    hasUnread,
    
    // 方法
    init,
    setDoNotDisturb,
    connect,
    disconnect,
    addNotification,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAll,
    openNotificationDialog,
    closeNotificationDialog,
    triggerTestNotification,
    pushWithDesktop,
    filterBySource
  }
})