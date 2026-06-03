import { describe, it, expect, vi } from 'vitest'
import {
  destroyChart,
  destroyMap
} from '@/utils/visualization'

describe('destroyChart', () => {
  it('传入 null 不应抛出异常', () => {
    expect(() => destroyChart(null)).not.toThrow()
  })

  it('传入 undefined 不应抛出异常', () => {
    expect(() => destroyChart(undefined)).not.toThrow()
  })

  it('应调用 chart 的 dispose 方法', () => {
    const dispose = vi.fn()
    const chart = { dispose }
    destroyChart(chart)
    expect(dispose).toHaveBeenCalledTimes(1)
  })

  it('chart 对象有 dispose 但不返回任何值', () => {
    const dispose = vi.fn(() => undefined)
    const chart = { dispose }
    destroyChart(chart)
    expect(dispose).toHaveBeenCalled()
  })
})

describe('destroyMap', () => {
  it('传入 null 不应抛出异常', () => {
    expect(() => destroyMap(null)).not.toThrow()
  })

  it('传入 undefined 不应抛出异常', () => {
    expect(() => destroyMap(undefined)).not.toThrow()
  })

  it('应调用 map 的 remove 方法', () => {
    const remove = vi.fn()
    const map = { remove }
    destroyMap(map)
    expect(remove).toHaveBeenCalledTimes(1)
  })

  it('map 对象有 remove 但不返回任何值', () => {
    const remove = vi.fn(() => undefined)
    const map = { remove }
    destroyMap(map)
    expect(remove).toHaveBeenCalled()
  })
})
