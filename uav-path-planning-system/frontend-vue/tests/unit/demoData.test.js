import { describe, it, expect } from 'vitest'
import {
  demoData,
  statusColors,
  riskColors,
  normalizeApiResponse
} from '@/utils/demoData'

describe('normalizeApiResponse', () => {
  it('应返回 null 当传入 null', () => {
    expect(normalizeApiResponse(null)).toBeNull()
  })

  it('应返回 undefined 当传入 undefined', () => {
    expect(normalizeApiResponse(undefined)).toBeUndefined()
  })

  it('应直接返回数组', () => {
    const arr = [1, 2, 3]
    expect(normalizeApiResponse(arr)).toBe(arr)
  })

  it('应返回对象中的 data 字段内容', () => {
    const data = { id: 1 }
    expect(normalizeApiResponse({ data })).toBe(data)
  })

  it('应返回对象中的 content 字段内容', () => {
    const content = { id: 2 }
    expect(normalizeApiResponse({ content })).toBe(content)
  })

  it('应优先返回 data 字段（data 和 content 同时存在）', () => {
    const data = { id: 1 }
    const content = { id: 2 }
    expect(normalizeApiResponse({ data, content })).toBe(data)
  })

  it('应递归处理嵌套的 data 字段', () => {
    const inner = [1, 2, 3]
    const response = { data: { data: inner } }
    expect(normalizeApiResponse(response)).toBe(inner)
  })

  it('应递归处理嵌套的 content 字段', () => {
    const inner = [4, 5, 6]
    const response = { data: { content: inner } }
    expect(normalizeApiResponse(response)).toBe(inner)
  })

  it('应返回普通对象本身（无 data/content 字段）', () => {
    const obj = { a: 1, b: 2 }
    expect(normalizeApiResponse(obj)).toBe(obj)
  })
})

describe('statusColors', () => {
  it('应包含所有预期的状态映射', () => {
    expect(statusColors).toEqual({
      '待分配': 'blue',
      '已分配': 'orange',
      '执行中': 'purple',
      '已完成': 'green',
      '已取消': 'red',
      '成功': 'green',
      '失败': 'red',
      '进行中': 'blue'
    })
  })

  it('应返回正确的颜色值', () => {
    expect(statusColors['待分配']).toBe('blue')
    expect(statusColors['已完成']).toBe('green')
    expect(statusColors['已取消']).toBe('red')
    expect(statusColors['进行中']).toBe('blue')
  })

  it('对不存在的状态应返回 undefined', () => {
    expect(statusColors['未知状态']).toBeUndefined()
  })
})

describe('riskColors', () => {
  it('应包含所有预期的风险等级映射', () => {
    expect(riskColors).toEqual({
      '低': 'green',
      '中': 'orange',
      '高': 'red'
    })
  })

  it('应返回正确的颜色值', () => {
    expect(riskColors['低']).toBe('green')
    expect(riskColors['中']).toBe('orange')
    expect(riskColors['高']).toBe('red')
  })

  it('对不存在的风险等级应返回 undefined', () => {
    expect(riskColors['极高']).toBeUndefined()
  })
})

describe('demoData 结构', () => {
  it('应包含所有必需的顶级字段', () => {
    expect(demoData).toHaveProperty('drones')
    expect(demoData).toHaveProperty('tasks')
    expect(demoData).toHaveProperty('history')
    expect(demoData).toHaveProperty('weather')
    expect(demoData).toHaveProperty('pathPlanning')
  })

  it('drones 应包含3架无人机，每架有必需的字段', () => {
    expect(demoData.drones).toHaveLength(3)
    demoData.drones.forEach(drone => {
      expect(drone).toHaveProperty('id')
      expect(drone).toHaveProperty('name')
      expect(drone).toHaveProperty('type')
      expect(drone).toHaveProperty('status')
      expect(drone).toHaveProperty('battery')
      expect(drone).toHaveProperty('location')
    })
  })

  it('tasks 应包含3个任务，每项有必需的字段', () => {
    expect(demoData.tasks).toHaveLength(3)
    demoData.tasks.forEach(task => {
      expect(task).toHaveProperty('id')
      expect(task).toHaveProperty('name')
      expect(task).toHaveProperty('type')
      expect(task).toHaveProperty('location')
      expect(task).toHaveProperty('priority')
      expect(task).toHaveProperty('status')
      expect(task).toHaveProperty('description')
    })
  })

  it('history 应包含3条记录，每条有必需的字段', () => {
    expect(demoData.history).toHaveLength(3)
    demoData.history.forEach(record => {
      expect(record).toHaveProperty('id')
      expect(record).toHaveProperty('name')
      expect(record).toHaveProperty('startTime')
      expect(record).toHaveProperty('endTime')
      expect(record).toHaveProperty('status')
      expect(record).toHaveProperty('duration')
      expect(record).toHaveProperty('weatherData')
    })
  })

  it('weather 应包含必需的字段', () => {
    expect(demoData.weather).toHaveProperty('windSpeed')
    expect(demoData.weather).toHaveProperty('windDirection')
    expect(demoData.weather).toHaveProperty('temperature')
    expect(demoData.weather).toHaveProperty('humidity')
    expect(demoData.weather).toHaveProperty('windField')
    expect(Array.isArray(demoData.weather.windField)).toBe(true)
  })

  it('pathPlanning 应包含必需的子字段', () => {
    expect(demoData.pathPlanning).toHaveProperty('defaultTaskPoints')
    expect(demoData.pathPlanning).toHaveProperty('defaultSavedPlans')
    expect(demoData.pathPlanning).toHaveProperty('mockResult')
    expect(demoData.pathPlanning).toHaveProperty('defaultRealtimeData')
  })
})
