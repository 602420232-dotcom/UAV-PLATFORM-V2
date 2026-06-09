import { ElNotification } from 'element-plus'

let ws = null
let reconnectTimer = null
let heartbeatTimer = null
let listeners = []

const RECONNECT_INTERVAL = 5000
const HEARTBEAT_INTERVAL = 30000

class WebSocketService {
  constructor() {
    this.connected = false
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.wsUrl = ''
  }

  connect(userId) {
    if (this.connected) {
      console.log('[WebSocket] Already connected')
      return
    }

    // 演示模式：使用模拟WebSocket
    this.wsUrl = `wss://demo.forum.local/ws?userId=${userId}`
    
    try {
      // 在演示模式下，我们模拟WebSocket连接
      this.simulateConnection(userId)
    } catch (error) {
      console.error('[WebSocket] Connection failed:', error)
      this.scheduleReconnect(userId)
    }
  }

  simulateConnection(userId) {
    console.log('[WebSocket] Simulating connection for user:', userId)
    
    // 模拟连接成功
    setTimeout(() => {
      this.connected = true
      this.reconnectAttempts = 0
      console.log('[WebSocket] Connected successfully (simulated)')
      
      // 触发连接成功事件
      this.emit('connect', { userId })
      
      // 启动心跳
      this.startHeartbeat()
      
      // 模拟接收通知（每隔30秒随机接收一条通知）
      this.simulateNotifications(userId)
    }, 500)
  }

  simulateNotifications(userId) {
    // 模拟的通知消息
    const mockNotifications = [
      {
        id: `n_${Date.now()}`,
        type: 'reply',
        source: 'forum',
        message: '张三 回复了你的帖子',
        postTitle: '关于DE-RRT*算法参数调优的讨论',
        postId: '2',
        from: '张三',
        timestamp: new Date().toISOString()
      },
      {
        id: `n_${Date.now()}`,
        type: 'mention',
        source: 'forum',
        message: '李四 在评论中提到了你',
        postTitle: '飞控端GPS信号异常问题反馈',
        postId: '3',
        from: '李四',
        timestamp: new Date().toISOString()
      },
      {
        id: `n_${Date.now()}`,
        type: 'system',
        source: 'system',
        message: '系统公告：有新的版本更新',
        postTitle: 'V2.0版本发布公告',
        postId: '1',
        from: '系统',
        timestamp: new Date().toISOString()
      }
    ]

    // 每30-60秒随机发送一条通知
    const scheduleNextNotification = () => {
      const delay = 30000 + Math.random() * 30000 // 30-60秒
      setTimeout(() => {
        if (this.connected) {
          const notification = mockNotifications[Math.floor(Math.random() * mockNotifications.length)]
          const newNotification = {
            ...notification,
            id: `n_${Date.now()}`,
            timestamp: new Date().toISOString()
          }
          this.handleMessage(newNotification)
          scheduleNextNotification()
        }
      }, delay)
    }

    scheduleNextNotification()
  }

  handleMessage(data) {
    console.log('[WebSocket] Received message:', data)
    
    // 解析消息类型
    const messageType = data.type || 'unknown'
    
    // 触发消息事件
    this.emit('message', data)
    
    // 根据消息类型显示通知
    this.showNotification(data)
  }

  showNotification(data) {
    // 检查免打扰模式
    try {
      const doNotDisturb = localStorage.getItem('notification_doNotDisturb')
      if (doNotDisturb === 'true') {
        return // 免打扰模式下不显示弹窗
      }
    } catch (e) {
      // localStorage 不可用，继续显示通知
    }
    
    // 静默消息不弹窗
    if (data.silent) {
      return
    }
    
    const typeMap = {
      reply: { type: 'info', icon: '💬' },
      mention: { type: 'warning', icon: '@' },
      system: { type: 'success', icon: '📢' }
    }
    
    const config = typeMap[data.type] || { type: 'info', icon: '📬' }
    
    ElNotification({
      title: `${config.icon} ${data.type === 'reply' ? '新回复' : data.type === 'mention' ? '@提及' : '系统通知'}`,
      message: data.message || data.content,
      duration: 5000,
      type: config.type,
      position: 'top-right',
      onClick: () => {
        // 点击通知跳转到帖子
        if (data.postId) {
          window.location.hash = `/forum?post=${data.postId}`
        }
      }
    })
  }

  send(data) {
    if (!this.connected) {
      console.warn('[WebSocket] Not connected, message not sent')
      return false
    }

    try {
      // 演示模式：模拟发送
      console.log('[WebSocket] Sending message:', data)
      
      // 模拟服务器响应
      if (data.type === 'comment') {
        setTimeout(() => {
          this.emit('message', {
            type: 'confirmation',
            original: data,
            success: true,
            timestamp: new Date().toISOString()
          })
        }, 100)
      }
      
      return true
    } catch (error) {
      console.error('[WebSocket] Send failed:', error)
      return false
    }
  }

  startHeartbeat() {
    this.stopHeartbeat()
    
    heartbeatTimer = setInterval(() => {
      if (this.connected) {
        this.send({ type: 'ping', timestamp: Date.now() })
      }
    }, HEARTBEAT_INTERVAL)
  }

  stopHeartbeat() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  scheduleReconnect(userId) {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnect attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = RECONNECT_INTERVAL * Math.pow(2, this.reconnectAttempts - 1)
    
    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)
    
    reconnectTimer = setTimeout(() => {
      this.connect(userId)
    }, delay)
  }

  disconnect() {
    this.connected = false
    this.stopHeartbeat()
    
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    
    if (ws) {
      ws.close()
      ws = null
    }
    
    console.log('[WebSocket] Disconnected')
    this.emit('disconnect', {})
  }

  on(event, callback) {
    if (!listeners[event]) {
      listeners[event] = []
    }
    listeners[event].push(callback)
  }

  off(event, callback) {
    if (!listeners[event]) return
    listeners[event] = listeners[event].filter(cb => cb !== callback)
  }

  emit(event, data) {
    if (!listeners[event]) return
    listeners[event].forEach(callback => callback(data))
  }

  isConnected() {
    return this.connected
  }

  // 手动触发一条通知（用于测试）
  triggerNotification(notification) {
    this.handleMessage(notification)
  }
}

// 单例模式
const wsService = new WebSocketService()

export default wsService
export { WebSocketService }