import { ref, onMounted, onUnmounted, type Ref } from 'vue'

/**
 * WebSocket 连接状态
 */
export enum WebSocketStatus {
  CONNECTING = 'CONNECTING',
  OPEN = 'OPEN',
  CLOSING = 'CLOSING',
  CLOSED = 'CLOSED',
  RECONNECTING = 'RECONNECTING',
}

/**
 * WebSocket 消息结构
 */
export interface WebSocketMessage<T = unknown> {
  type: string
  message: string
  data: T
}

/**
 * WebSocket 配置选项
 */
export interface WebSocketOptions {
  /** WebSocket 端点 URL */
  url: string
  /** 自动重连最大次数，默认 10 */
  maxReconnectAttempts?: number
  /** 重连间隔（毫秒），默认 3000 */
  reconnectInterval?: number
  /** 心跳间隔（毫秒），默认 30000 */
  heartbeatInterval?: number
  /** 心跳超时时间（毫秒），默认 60000 */
  heartbeatTimeout?: number
  /** 消息队列最大长度，默认 1000 */
  maxQueueSize?: number
  /** 连接建立后的回调 */
  onOpen?: (event: Event) => void
  /** 连接关闭后的回调 */
  onClose?: (event: CloseEvent) => void
  /** 收到消息后的回调 */
  onMessage?: (message: WebSocketMessage) => void
  /** 发生错误后的回调 */
  onError?: (event: Event) => void
  /** 重连时的回调 */
  onReconnect?: (attempt: number) => void
}

/**
 * Vue 3 Composition API WebSocket 客户端 Composable
 *
 * 特性：
 * - 自动重连机制（指数退避）
 * - 心跳检测（ping/pong）
 * - 消息队列缓冲（离线时缓存消息）
 * - 订阅/取消订阅区域
 * - 类型安全的消息处理
 *
 * 使用示例：
 * ```ts
 * const { status, connect, disconnect, subscribe, unsubscribe, send, messages } = useWebSocket({
 *   url: 'ws://localhost:8082/ws/weather',
 *   onMessage: (msg) => console.log(msg),
 * })
 * ```
 */
export function useWebSocket(options: WebSocketOptions) {
  const {
    url,
    maxReconnectAttempts = 10,
    reconnectInterval = 3000,
    heartbeatInterval = 30000,
    heartbeatTimeout = 60000,
    maxQueueSize = 1000,
    onOpen,
    onClose,
    onMessage,
    onError,
    onReconnect,
  } = options

  /** WebSocket 实例 */
  let ws: WebSocket | null = null

  /** 连接状态 */
  const status: Ref<WebSocketStatus> = ref(WebSocketStatus.CLOSED)

  /** 收到的消息列表 */
  const messages: Ref<WebSocketMessage[]> = ref([])

  /** 已订阅的区域集合 */
  const subscribedRegions: Ref<Set<string>> = ref(new Set())

  /** 重连计数 */
  let reconnectAttempts = 0

  /** 重连定时器 */
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  /** 心跳定时器 */
  let heartbeatTimer: ReturnType<typeof setInterval> | null = null

  /** 心跳超时定时器 */
  let heartbeatTimeoutTimer: ReturnType<typeof setTimeout> | null = null

  /** 消息队列（离线时缓存） */
  const messageQueue: string[] = []

  /** 是否手动关闭（用于区分异常断开和主动断开） */
  let manualClose = false

  /**
   * 建立 WebSocket 连接
   */
  const connect = (): void => {
    if (ws?.readyState === WebSocket.OPEN || ws?.readyState === WebSocket.CONNECTING) {
      console.warn('[WebSocket] 连接已存在或正在建立中')
      return
    }

    manualClose = false
    status.value = WebSocketStatus.CONNECTING

    try {
      ws = new WebSocket(url)

      ws.onopen = (event: Event) => {
        status.value = WebSocketStatus.OPEN
        reconnectAttempts = 0
        console.info('[WebSocket] 连接已建立')

        // 恢复之前的区域订阅
        subscribedRegions.value.forEach((region) => {
          sendCommand('subscribe', region)
        })

        // 启动心跳
        startHeartbeat()

        // 发送队列中缓存的消息
        flushMessageQueue()

        onOpen?.(event)
      }

      ws.onmessage = (event: MessageEvent) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)

          // 处理心跳响应
          if (message.type === 'heartbeat') {
            clearHeartbeatTimeout()
            return
          }

          // 存储消息
          messages.value.push(message)
          // 限制消息列表长度
          if (messages.value.length > maxQueueSize) {
            messages.value = messages.value.slice(-maxQueueSize)
          }

          onMessage?.(message)
        } catch (e) {
          console.error('[WebSocket] 消息解析失败:', event.data, e)
        }
      }

      ws.onclose = (event: CloseEvent) => {
        status.value = WebSocketStatus.CLOSED
        stopHeartbeat()
        console.info(`[WebSocket] 连接已关闭: code=${event.code}, reason=${event.reason}`)

        // 非手动关闭时触发自动重连
        if (!manualClose) {
          scheduleReconnect()
        }

        onClose?.(event)
      }

      ws.onerror = (event: Event) => {
        console.error('[WebSocket] 连接错误:', event)
        onError?.(event)
      }
    } catch (e) {
      console.error('[WebSocket] 创建连接失败:', e)
      status.value = WebSocketStatus.CLOSED
      scheduleReconnect()
    }
  }

  /**
   * 主动断开 WebSocket 连接
   */
  const disconnect = (): void => {
    manualClose = true
    stopHeartbeat()
    clearReconnectTimer()

    if (ws) {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close(1000, 'Client disconnect')
      }
      ws = null
    }

    status.value = WebSocketStatus.CLOSED
    console.info('[WebSocket] 已主动断开连接')
  }

  /**
   * 发送消息
   */
  const send = (data: string | object): boolean => {
    const payload = typeof data === 'string' ? data : JSON.stringify(data)

    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(payload)
      return true
    }

    // 连接未建立时缓存到队列
    if (messageQueue.length < maxQueueSize) {
      messageQueue.push(payload)
      console.warn('[WebSocket] 连接未就绪，消息已加入队列:', payload)
    } else {
      console.error('[WebSocket] 消息队列已满，消息丢弃:', payload)
    }
    return false
  }

  /**
   * 发送命令（subscribe / unsubscribe / heartbeat / query）
   */
  const sendCommand = (action: string, region?: string): void => {
    send({ action, region })
  }

  /**
   * 订阅指定区域的气象数据
   */
  const subscribe = (region: string): void => {
    if (!region || region.trim() === '') {
      console.warn('[WebSocket] 区域标识不能为空')
      return
    }

    subscribedRegions.value.add(region)
    sendCommand('subscribe', region)
    console.info(`[WebSocket] 已订阅区域: ${region}`)
  }

  /**
   * 取消订阅指定区域
   */
  const unsubscribe = (region?: string): void => {
    if (region) {
      subscribedRegions.value.delete(region)
      sendCommand('unsubscribe', region)
      console.info(`[WebSocket] 已取消订阅区域: ${region}`)
    } else {
      // 取消所有订阅
      subscribedRegions.value.clear()
      sendCommand('unsubscribe')
      console.info('[WebSocket] 已取消所有订阅')
    }
  }

  /**
   * 查询指定区域的实时数据
   */
  const query = (region: string): void => {
    sendCommand('query', region)
  }

  /**
   * 安排自动重连（指数退避）
   */
  const scheduleReconnect = (): void => {
    if (reconnectAttempts >= maxReconnectAttempts) {
      console.error(`[WebSocket] 达到最大重连次数 (${maxReconnectAttempts})，停止重连`)
      status.value = WebSocketStatus.CLOSED
      return
    }

    reconnectAttempts++
    status.value = WebSocketStatus.RECONNECTING

    // 指数退避：间隔时间随重连次数增加
    const delay = Math.min(reconnectInterval * Math.pow(1.5, reconnectAttempts - 1), 30000)

    console.info(`[WebSocket] 计划第 ${reconnectAttempts} 次重连，间隔 ${delay}ms`)
    onReconnect?.(reconnectAttempts)

    reconnectTimer = setTimeout(() => {
      connect()
    }, delay)
  }

  /**
   * 清除重连定时器
   */
  const clearReconnectTimer = (): void => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  /**
   * 启动心跳检测
   */
  const startHeartbeat = (): void => {
    stopHeartbeat()

    heartbeatTimer = setInterval(() => {
      if (ws?.readyState === WebSocket.OPEN) {
        sendCommand('heartbeat')

        // 设置心跳超时检测
        heartbeatTimeoutTimer = setTimeout(() => {
          console.warn('[WebSocket] 心跳超时，连接可能已断开')
          ws?.close(1001, 'Heartbeat timeout')
        }, heartbeatTimeout)
      }
    }, heartbeatInterval)
  }

  /**
   * 停止心跳检测
   */
  const stopHeartbeat = (): void => {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
    clearHeartbeatTimeout()
  }

  /**
   * 清除心跳超时定时器
   */
  const clearHeartbeatTimeout = (): void => {
    if (heartbeatTimeoutTimer) {
      clearTimeout(heartbeatTimeoutTimer)
      heartbeatTimeoutTimer = null
    }
  }

  /**
   * 发送队列中缓存的消息
   */
  const flushMessageQueue = (): void => {
    while (messageQueue.length > 0 && ws?.readyState === WebSocket.OPEN) {
      const payload = messageQueue.shift()
      if (payload) {
        ws.send(payload)
      }
    }
  }

  /**
   * 清空消息列表
   */
  const clearMessages = (): void => {
    messages.value = []
  }

  /**
   * 获取连接是否活跃
   */
  const isConnected = (): boolean => {
    return ws?.readyState === WebSocket.OPEN
  }

  // 组件挂载时自动连接（可选，根据业务需求决定是否自动连接）
  onMounted(() => {
    // 默认不自动连接，由调用方决定
  })

  // 组件卸载时清理资源
  onUnmounted(() => {
    disconnect()
  })

  return {
    /** 当前连接状态 */
    status,
    /** 收到的消息列表 */
    messages,
    /** 已订阅的区域 */
    subscribedRegions,
    /** 建立连接 */
    connect,
    /** 断开连接 */
    disconnect,
    /** 发送消息 */
    send,
    /** 订阅区域 */
    subscribe,
    /** 取消订阅 */
    unsubscribe,
    /** 查询区域数据 */
    query,
    /** 清空消息 */
    clearMessages,
    /** 是否已连接 */
    isConnected,
  }
}

export default useWebSocket
