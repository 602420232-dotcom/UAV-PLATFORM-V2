import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  ErrorHandler,
  errorHandler,
  handleNetworkError,
  retry,
  safeExecute,
  createErrorBoundary,
  Logger,
  createLogger
} from '@/utils/errorHandler'

describe('ErrorHandler', () => {
  let handler

  beforeEach(() => {
    handler = new ErrorHandler()
  })

  it('应正确记录错误信息', () => {
    const error = new Error('测试错误')
    const result = handler.handleError(error, 'testContext', { extra: 'info' })

    expect(result).toHaveProperty('timestamp')
    expect(result).toHaveProperty('context', 'testContext')
    expect(result).toHaveProperty('extra', { extra: 'info' })
    expect(result.error.message).toBe('测试错误')
    expect(result.error.name).toBe('Error')
    expect(result.error.stack).toBeDefined()
  })

  it('处理上下文默认为 unknown', () => {
    const error = new Error('test')
    const result = handler.handleError(error)
    expect(result.context).toBe('unknown')
  })

  it('extra 参数默认为空对象', () => {
    const error = new Error('test')
    const result = handler.handleError(error, 'ctx')
    expect(result.extra).toEqual({})
  })

  it('应注册并触发错误监听器', () => {
    const listener = vi.fn()
    handler.onError(listener)

    const error = new Error('监听器测试')
    handler.handleError(error, 'test')

    expect(listener).toHaveBeenCalledTimes(1)
    expect(listener).toHaveBeenCalledWith(
      expect.objectContaining({
        context: 'test',
        error: expect.objectContaining({ message: '监听器测试' })
      })
    )
  })

  it('应移除错误监听器', () => {
    const listener = vi.fn()
    handler.onError(listener)
    handler.offError(listener)

    const error = new Error('移除测试')
    handler.handleError(error)

    expect(listener).not.toHaveBeenCalled()
  })

  it('getErrors 应返回所有错误记录', () => {
    const error1 = new Error('错误1')
    const error2 = new Error('错误2')
    handler.handleError(error1, 'ctx1')
    handler.handleError(error2, 'ctx2')

    const errors = handler.getErrors()
    expect(errors).toHaveLength(2)
    expect(errors[0].context).toBe('ctx1')
    expect(errors[1].context).toBe('ctx2')
  })

  it('clearErrors 应清空错误列表', () => {
    handler.handleError(new Error('test'), 'ctx')
    handler.clearErrors()
    expect(handler.getErrors()).toHaveLength(0)
  })

  it('单个监听器抛出异常不应影响其他监听器', () => {
    const badListener = vi.fn().mockImplementation(() => { throw new Error('bad') })
    const goodListener = vi.fn()
    handler.onError(badListener)
    handler.onError(goodListener)

    handler.handleError(new Error('test'))

    expect(badListener).toHaveBeenCalled()
    expect(goodListener).toHaveBeenCalled()
  })
})

describe('handleNetworkError', () => {
  it('应处理带响应状态的错误', () => {
    const error = {
      response: {
        status: 404,
        data: { message: '资源未找到' }
      }
    }
    const result = handleNetworkError(error)
    expect(result.success).toBe(false)
    expect(result.message).toBe('资源未找到')
    expect(result.code).toBe('HTTP_404')
  })

  it('响应无 data.message 时应使用默认消息', () => {
    const error = {
      response: {
        status: 500,
        data: {}
      }
    }
    const result = handleNetworkError(error)
    expect(result.message).toBe('服务器错误 (500)')
    expect(result.code).toBe('HTTP_500')
  })

  it('应处理无响应的错误（请求已发送）', () => {
    const error = {
      request: {}
    }
    const result = handleNetworkError(error)
    expect(result.message).toBe('服务器无响应，请检查网络连接')
    expect(result.code).toBe('NO_RESPONSE')
  })

  it('应处理请求配置错误', () => {
    const error = {
      message: '网络异常'
    }
    const result = handleNetworkError(error)
    expect(result.message).toBe('网络异常')
    expect(result.code).toBe('REQUEST_ERROR')
  })

  it('无 message 时应使用默认提示', () => {
    const error = {}
    const result = handleNetworkError(error)
    expect(result.message).toBe('请求配置错误')
    expect(result.code).toBe('REQUEST_ERROR')
  })

  it('返回结果应包含原始错误对象', () => {
    const error = { response: { status: 403, data: {} } }
    const result = handleNetworkError(error)
    expect(result.error).toBe(error)
  })

  it('返回结果的 success 固定为 false', () => {
    const error = { response: { status: 200, data: {} } }
    const result = handleNetworkError(error)
    expect(result.success).toBe(false)
  })
})

describe('retry', () => {
  it('第一次尝试即成功应直接返回结果', async () => {
    const func = vi.fn().mockResolvedValue('success')
    const result = await retry(func)
    expect(result).toBe('success')
    expect(func).toHaveBeenCalledTimes(1)
  })

  it('失败后重试应最终成功', async () => {
    const func = vi.fn()
      .mockRejectedValueOnce(new Error('第一次失败'))
      .mockRejectedValueOnce(new Error('第二次失败'))
      .mockResolvedValueOnce('终于成功')

    const result = await retry(func, 3, 10)
    expect(result).toBe('终于成功')
    expect(func).toHaveBeenCalledTimes(3)
  })

  it('所有尝试均失败应抛出错误', async () => {
    const error = new Error('总是失败')
    const func = vi.fn().mockRejectedValue(error)

    await expect(retry(func, 2, 10)).rejects.toThrow('总是失败')
    expect(func).toHaveBeenCalledTimes(2)
  })

  it('默认参数为重试3次延迟1000ms', async () => {
    const func = vi.fn().mockRejectedValue(new Error('fail'))
    await expect(retry(func)).rejects.toThrow('fail')
    expect(func).toHaveBeenCalledTimes(3)
  })
})

describe('safeExecute', () => {
  it('函数执行成功应返回结果', () => {
    const result = safeExecute(() => 42)
    expect(result).toBe(42)
  })

  it('函数执行失败应返回默认值', () => {
    const result = safeExecute(() => { throw new Error('失败') }, '默认值')
    expect(result).toBe('默认值')
  })

  it('默认值默认为 null', () => {
    const result = safeExecute(() => { throw new Error('失败') })
    expect(result).toBeNull()
  })
})

describe('createErrorBoundary', () => {
  it('应返回包含 data 和 errorCaptured 的对象', () => {
    const boundary = createErrorBoundary()
    expect(boundary).toHaveProperty('data')
    expect(boundary).toHaveProperty('errorCaptured')
    expect(boundary).toHaveProperty('render')

    const data = boundary.data()
    expect(data).toHaveProperty('hasError', false)
    expect(data).toHaveProperty('error', null)
  })

  it('errorCaptured 应更新状态并返回 false', () => {
    const boundary = createErrorBoundary()
    const error = new Error('组件错误')
    const instance = { $options: { name: 'TestComponent' } }
    const info = 'render'
    const ctx = { data: boundary.data, hasError: false, error: null, $options: instance.$options }
    const result = boundary.errorCaptured.call(ctx, error, instance, info)
    expect(result).toBe(false)
    expect(ctx.hasError).toBe(true)
    expect(ctx.error).toBe(error)
  })

  it('应支持自定义 onError 回调', () => {
    const onError = vi.fn()
    const boundary = createErrorBoundary({ onError })
    const error = new Error('test')
    const instance = { $options: { name: 'TestComp' } }
    const ctx = { data: boundary.data, hasError: false, error: null, $options: instance.$options }
    boundary.errorCaptured.call(ctx, error, instance, 'hook')
    expect(onError).toHaveBeenCalledWith(error, instance, 'hook')
  })
})

describe('Logger', () => {
  let logger

  beforeEach(() => {
    logger = new Logger('TestLogger')
  })

  it('应使用正确的名称创建', () => {
    expect(logger.name).toBe('TestLogger')
  })

  it('info 应记录消息', () => {
    const spy = vi.spyOn(console, 'info').mockImplementation(() => {})
    logger.info('信息消息', { key: 'value' })
    expect(spy).toHaveBeenCalledWith('[TestLogger] 信息消息', { key: 'value' })
    spy.mockRestore()
  })

  it('warn 应记录警告', () => {
    const spy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    logger.warn('警告消息')
    expect(spy).toHaveBeenCalledWith('[TestLogger] 警告消息', {})
    spy.mockRestore()
  })

  it('error 应记录错误并调用 errorHandler', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const error = new Error('记录器错误')
    logger.error('错误消息', error, { extra: 'data' })
    expect(spy).toHaveBeenCalledWith('[TestLogger] 错误消息', error, { extra: 'data' })
    spy.mockRestore()
  })

  it('error 无 error 参数时不应抛出', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    logger.error('仅消息')
    expect(spy).toHaveBeenCalledWith('[TestLogger] 仅消息', null, {})
    spy.mockRestore()
  })

  it('debug 在非开发环境不应记录', () => {
    const originalNodeEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'production'
    const spy = vi.spyOn(console, 'debug').mockImplementation(() => {})
    logger.debug('调试消息')
    expect(spy).not.toHaveBeenCalled()
    process.env.NODE_ENV = originalNodeEnv
    spy.mockRestore()
  })
})

describe('createLogger', () => {
  it('应创建 Logger 实例', () => {
    const logger = createLogger('CustomLogger')
    expect(logger).toBeInstanceOf(Logger)
    expect(logger.name).toBe('CustomLogger')
  })
})
