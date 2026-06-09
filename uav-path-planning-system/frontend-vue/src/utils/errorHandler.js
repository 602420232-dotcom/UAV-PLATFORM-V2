let ElMessageRef = null

export function setElMessage(elMessage) {
  ElMessageRef = elMessage
}

function showMessage(type, text) {
  try {
    if (ElMessageRef && typeof ElMessageRef[type] === 'function') {
      ElMessageRef[type]({ message: text, duration: 4000, showClose: true })
    } else {
      const fn = type === 'error' ? console.error : type === 'warning' ? console.warn : console.log
      fn('[提示]', text)
    }
  } catch (e) {
    console.error('[errorHandler] 提示展示失败:', e, text)
  }
}

const HTTP_MESSAGES = {
  400: '请求参数不正确，请检查输入后重试',
  401: '登录已过期，请重新登录',
  403: '抱歉，您没有权限执行此操作',
  404: '请求的资源不存在或接口未找到',
  405: '请求方法不被允许',
  408: '请求超时，请稍后再试',
  415: '请求格式不正确，请联系管理员',
  422: '请求数据校验失败，请检查输入',
  429: '请求过于频繁，请稍后再试',
  500: '服务器内部错误，请稍后再试或联系管理员',
  502: '网关错误，服务暂时不可用',
  503: '服务暂时不可用，请稍后再试',
  504: '网关超时，请稍后再试'
}

function classifyError(err) {
  if (!err || typeof err !== 'object') return 'UNKNOWN'

  if (
    err.code === 'ECONNABORTED' ||
    (typeof err.message === 'string' && /timeout/i.test(err.message))
  ) {
    return 'TIMEOUT'
  }

  if (err.message === 'Network Error' || err.code === 'NETWORK_ERROR') {
    return 'NETWORK_ERROR'
  }

  if (!err.response) return 'NETWORK_ERROR'

  const status = err.response.status
  if (status === 401) return 'UNAUTHORIZED'
  if (status === 403) return 'FORBIDDEN'
  if (status === 404) return 'NOT_FOUND'
  if (status === 429) return 'TOO_MANY_REQUESTS'
  if (status >= 400 && status < 500) return 'CLIENT_ERROR'
  if (status >= 500 && status < 600) return 'SERVER_ERROR'
  return 'UNKNOWN'
}

export function handleApiError(err, customMessage = null) {
  const kind = classifyError(err)
  const status = err && err.response ? err.response.status : null
  const url = err && err.config ? err.config.url : ''
  const method = err && err.config ? err.config.method : ''

  let userMessage = customMessage
  let logLevel = 'error'
  let shouldRetry = false
  let shouldLogout = false

  switch (kind) {
    case 'UNAUTHORIZED':
      userMessage = userMessage || HTTP_MESSAGES[401]
      shouldLogout = true
      break
    case 'FORBIDDEN':
      userMessage = userMessage || HTTP_MESSAGES[403]
      logLevel = 'warning'
      break
    case 'NOT_FOUND':
      userMessage = userMessage || HTTP_MESSAGES[404]
      logLevel = 'warning'
      break
    case 'CLIENT_ERROR':
      userMessage = userMessage || (status ? HTTP_MESSAGES[status] : null) || '请求失败，请稍后再试'
      logLevel = 'warning'
      break
    case 'TOO_MANY_REQUESTS':
      userMessage = userMessage || HTTP_MESSAGES[429]
      logLevel = 'warning'
      break
    case 'SERVER_ERROR':
      userMessage = userMessage || (status ? HTTP_MESSAGES[status] : null) || '服务器错误，请稍后再试'
      shouldRetry = true
      break
    case 'TIMEOUT':
      userMessage = userMessage || '请求超时，请检查网络连接后重试'
      shouldRetry = true
      break
    case 'NETWORK_ERROR':
      userMessage = userMessage || '网络连接异常，请检查网络后重试'
      shouldRetry = true
      break
    default:
      userMessage = userMessage || (err && err.message) || '请求失败，请稍后再试'
  }

  console[logLevel](
    `[API Error] kind=${kind} status=${status || '-'} method=${method || '-'} url=${url || '-'}`,
    (err && err.message) || '',
    err
  )

  if (kind !== 'UNAUTHORIZED') {
    showMessage(logLevel === 'warning' ? 'warning' : 'error', userMessage)
  }

  return {
    kind, status, userMessage, shouldRetry, shouldLogout, url, method
  }
}

export function handleGenericError(err, { context = 'runtime' } = {}) {
  if (!err) return null
  const message = (err && err.message) ? err.message : String(err)
  console.error(`[Runtime Error] context=${context} message=${message}`, err)
  return { message, context }
}

export class ErrorHandler {
  constructor() {
    this.errors = []
    this.listeners = []
  }

  handleError(error, context = 'unknown', extra = {}) {
    const errorRecord = {
      timestamp: new Date().toISOString(),
      context,
      extra: typeof extra === 'object' ? extra : {},
      error: error instanceof Error ? error : new Error(String(error))
    }
    this.errors.push(errorRecord)
    this.notifyListeners(errorRecord)
    console.error(`[ErrorHandler] ${context}:`, error)
    return errorRecord
  }

  onError(listener) {
    if (typeof listener === 'function' && !this.listeners.includes(listener)) {
      this.listeners.push(listener)
    }
  }

  offError(listener) {
    const index = this.listeners.indexOf(listener)
    if (index > -1) {
      this.listeners.splice(index, 1)
    }
  }

  subscribe(listener) {
    this.onError(listener)
  }

  unsubscribe(listener) {
    this.offError(listener)
  }

  notifyListeners(errorRecord) {
    this.listeners.forEach(listener => {
      try {
        listener(errorRecord)
      } catch (e) {
        console.error('[ErrorHandler] Listener error:', e)
      }
    })
  }

  getErrors() {
    return [...this.errors]
  }

  clearErrors() {
    this.errors = []
  }
}

export const errorHandler = new ErrorHandler()

export function handleNetworkError(error) {
  const status = error.response?.status
  const data = error.response?.data

  let message = '请求配置错误'
  let code = 'REQUEST_ERROR'

  if (error.response) {
    code = `HTTP_${status}`
    if (data?.message) {
      message = data.message
    } else {
      message = `服务器错误 (${status})`
    }
  } else if (error.message) {
    message = error.message
    if (error.code) code = error.code
  } else if (error.request) {
    message = '服务器无响应，请检查网络连接'
    code = 'NO_RESPONSE'
  }

  return {
    success: false,
    message,
    code,
    error
  }
}

export async function retry(func, maxRetries = 3, delayMs = 1000) {
  let lastError
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await func()
    } catch (error) {
      lastError = error
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delayMs))
      }
    }
  }
  throw lastError
}

export function safeExecute(func, defaultValue = null) {
  try {
    return func()
  } catch {
    return defaultValue
  }
}

export function createErrorBoundary({ onError } = {}) {
  function data() {
    return { hasError: false, error: null }
  }

  function errorCaptured(err, instance, info) {
    if (this && typeof this === 'object') {
      this.hasError = true
      this.error = err
    }
    if (onError) {
      onError(err, instance, info)
    }
    console.error('[ErrorBoundary] Captured:', err)
    return false
  }

  function render() {}

  return {
    data,
    errorCaptured,
    render
  }
}

export class Logger {
  constructor(name) {
    this.name = name
  }

  info(message, extra = {}) {
    console.info(`[${this.name}] ${message}`, extra)
  }

  warn(message, extra = {}) {
    console.warn(`[${this.name}] ${message}`, extra)
  }

  error(message, error = null, extra = {}) {
    console.error(`[${this.name}] ${message}`, error, extra)
  }

  debug(message, extra = {}) {
    if (process.env.NODE_ENV === 'development') {
      console.debug(`[${this.name}] ${message}`, extra)
    }
  }
}

export function createLogger(name) {
  return new Logger(name)
}

export { classifyError }