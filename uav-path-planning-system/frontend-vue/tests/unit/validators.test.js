import { describe, it, expect } from 'vitest'
import {
  validateCoordinates,
  validateTaskName,
  validateDroneId,
  validateAltitude,
  validateSpeed,
  validateRiskThreshold,
  validateRequired,
  validateNumberRange,
  validators,
  createRule,
  validateForm,
  resetForm
} from '@/utils/validators'

describe('validateCoordinates', () => {
  const rule = {}

  it('应通过有效的坐标格式', async () => {
    await expect(validateCoordinates(rule, '39.90, 116.40')).resolves.toBeUndefined()
  })

  it('应通过无空格的坐标格式', async () => {
    await expect(validateCoordinates(rule, '39.90,116.40')).resolves.toBeUndefined()
  })

  it('应通过负经度的坐标', async () => {
    await expect(validateCoordinates(rule, '39.90, -116.40')).resolves.toBeUndefined()
  })

  it('应拒绝空值', async () => {
    await expect(validateCoordinates(rule, '')).rejects.toBe('请输入坐标')
    await expect(validateCoordinates(rule, undefined)).rejects.toBe('请输入坐标')
    await expect(validateCoordinates(rule, null)).rejects.toBe('请输入坐标')
  })

  it('应拒绝格式错误的值', async () => {
    await expect(validateCoordinates(rule, '39.90 116.40')).rejects.toBe('坐标格式错误，应为: 纬度, 经度')
    await expect(validateCoordinates(rule, 'abc, def')).rejects.toBe('坐标格式错误，应为: 纬度, 经度')
    await expect(validateCoordinates(rule, '39.90')).rejects.toBe('坐标格式错误，应为: 纬度, 经度')
  })

  it('应拒绝超出范围的纬度', async () => {
    await expect(validateCoordinates(rule, '100, 116.40')).rejects.toBe('纬度范围: -90 到 90')
    await expect(validateCoordinates(rule, '-100, 116.40')).rejects.toBe('纬度范围: -90 到 90')
  })

  it('应拒绝超出范围的经度', async () => {
    await expect(validateCoordinates(rule, '39.90, 200')).rejects.toBe('经度范围: -180 到 180')
    await expect(validateCoordinates(rule, '39.90, -200')).rejects.toBe('经度范围: -180 到 180')
  })

  it('应拒绝非数字坐标', async () => {
    await expect(validateCoordinates(rule, 'abc, 116.40')).rejects.toBe('坐标格式错误，应为: 纬度, 经度')
  })
})

describe('validateTaskName', () => {
  const rule = {}

  it('应通过有效的任务名称', async () => {
    await expect(validateTaskName(rule, '配送任务1')).resolves.toBeUndefined()
  })

  it('应拒绝空值', async () => {
    await expect(validateTaskName(rule, '')).rejects.toBe('请输入任务名称')
    await expect(validateTaskName(rule, undefined)).rejects.toBe('请输入任务名称')
  })

  it('应拒绝纯空格', async () => {
    await expect(validateTaskName(rule, '   ')).rejects.toBe('请输入任务名称')
  })

  it('应拒绝少于2个字符的名称', async () => {
    await expect(validateTaskName(rule, 'a')).rejects.toBe('任务名称至少2个字符')
  })

  it('应拒绝超过50个字符的名称', async () => {
    const longName = 'a'.repeat(51)
    await expect(validateTaskName(rule, longName)).rejects.toBe('任务名称不能超过50个字符')
  })

  it('应通过恰好50个字符的名称', async () => {
    const name = 'a'.repeat(50)
    await expect(validateTaskName(rule, name)).resolves.toBeUndefined()
  })

  it('应通过恰好2个字符的名称', async () => {
    await expect(validateTaskName(rule, 'ab')).resolves.toBeUndefined()
  })
})

describe('validateDroneId', () => {
  const rule = {}

  it('应通过有效的无人机ID', async () => {
    await expect(validateDroneId(rule, 'UAV-001')).resolves.toBeUndefined()
    await expect(validateDroneId(rule, 'UAV-999')).resolves.toBeUndefined()
  })

  it('应拒绝空值', async () => {
    await expect(validateDroneId(rule, '')).rejects.toBe('请选择无人机')
    await expect(validateDroneId(rule, undefined)).rejects.toBe('请选择无人机')
    await expect(validateDroneId(rule, null)).rejects.toBe('请选择无人机')
  })

  it('应拒绝格式错误的值', async () => {
    await expect(validateDroneId(rule, 'UAV-01')).rejects.toBe('无人机ID格式错误，应为: UAV-XXX')
    await expect(validateDroneId(rule, 'UAV-0001')).rejects.toBe('无人机ID格式错误，应为: UAV-XXX')
    await expect(validateDroneId(rule, 'DRONE-001')).rejects.toBe('无人机ID格式错误，应为: UAV-XXX')
    await expect(validateDroneId(rule, 'uav-001')).rejects.toBe('无人机ID格式错误，应为: UAV-XXX')
    await expect(validateDroneId(rule, 'UAV-abc')).rejects.toBe('无人机ID格式错误，应为: UAV-XXX')
  })
})

describe('validateAltitude', () => {
  const rule = {}

  it('应通过有效的高度值', async () => {
    await expect(validateAltitude(rule, 100)).resolves.toBeUndefined()
    await expect(validateAltitude(rule, '500')).resolves.toBeUndefined()
    await expect(validateAltitude(rule, 0)).resolves.toBeUndefined()
  })

  it('应拒绝空值', async () => {
    await expect(validateAltitude(rule, undefined)).rejects.toBe('请输入高度')
    await expect(validateAltitude(rule, null)).rejects.toBe('请输入高度')
    await expect(validateAltitude(rule, '')).rejects.toBe('请输入高度')
  })

  it('应拒绝负数', async () => {
    await expect(validateAltitude(rule, -1)).rejects.toBe('高度不能为负数')
  })

  it('应拒绝超过10000的值', async () => {
    await expect(validateAltitude(rule, 10001)).rejects.toBe('高度不能超过10000米')
  })

  it('应通过边界值10000', async () => {
    await expect(validateAltitude(rule, 10000)).resolves.toBeUndefined()
  })

  it('应拒绝非数字', async () => {
    await expect(validateAltitude(rule, 'abc')).rejects.toBe('高度必须是有效的数字')
  })
})

describe('validateSpeed', () => {
  const rule = {}

  it('应通过有效的速度值', async () => {
    await expect(validateSpeed(rule, 50)).resolves.toBeUndefined()
    await expect(validateSpeed(rule, '100')).resolves.toBeUndefined()
    await expect(validateSpeed(rule, 0)).resolves.toBeUndefined()
  })

  it('应拒绝空值', async () => {
    await expect(validateSpeed(rule, undefined)).rejects.toBe('请输入速度')
    await expect(validateSpeed(rule, null)).rejects.toBe('请输入速度')
    await expect(validateSpeed(rule, '')).rejects.toBe('请输入速度')
  })

  it('应拒绝负数', async () => {
    await expect(validateSpeed(rule, -1)).rejects.toBe('速度不能为负数')
  })

  it('应拒绝超过500的值', async () => {
    await expect(validateSpeed(rule, 501)).rejects.toBe('速度不能超过500 m/s')
  })

  it('应通过边界值500', async () => {
    await expect(validateSpeed(rule, 500)).resolves.toBeUndefined()
  })

  it('应拒绝非数字', async () => {
    await expect(validateSpeed(rule, 'abc')).rejects.toBe('速度必须是有效的数字')
  })
})

describe('validateRiskThreshold', () => {
  const rule = {}

  it('应通过有效的风险阈值', async () => {
    await expect(validateRiskThreshold(rule, 5)).resolves.toBeUndefined()
    await expect(validateRiskThreshold(rule, '3')).resolves.toBeUndefined()
    await expect(validateRiskThreshold(rule, 0)).resolves.toBeUndefined()
    await expect(validateRiskThreshold(rule, 10)).resolves.toBeUndefined()
  })

  it('应拒绝空值', async () => {
    await expect(validateRiskThreshold(rule, undefined)).rejects.toBe('请设置风险阈值')
    await expect(validateRiskThreshold(rule, null)).rejects.toBe('请设置风险阈值')
  })

  it('应拒绝超出范围的值', async () => {
    await expect(validateRiskThreshold(rule, -1)).rejects.toBe('风险阈值范围: 0 到 10')
    await expect(validateRiskThreshold(rule, 11)).rejects.toBe('风险阈值范围: 0 到 10')
  })

  it('应拒绝非数字', async () => {
    await expect(validateRiskThreshold(rule, 'abc')).rejects.toBe('风险阈值必须是有效的数字')
  })
})

describe('validateRequired', () => {
  it('应生成验证函数并验证空值', async () => {
    const validator = validateRequired('测试字段')
    const rule = {}
    await expect(validator(rule, '')).rejects.toBe('请输入测试字段')
    await expect(validator(rule, undefined)).rejects.toBe('请输入测试字段')
    await expect(validator(rule, null)).rejects.toBe('请输入测试字段')
  })

  it('应通过非空值', async () => {
    const validator = validateRequired('测试字段')
    const rule = {}
    await expect(validator(rule, 'hello')).resolves.toBeUndefined()
    await expect(validator(rule, 0)).resolves.toBeUndefined()
    await expect(validator(rule, false)).resolves.toBeUndefined()
  })
})

describe('validateNumberRange', () => {
  it('应生成验证函数并验证有效值', async () => {
    const validator = validateNumberRange(0, 100, '测试值')
    const rule = {}
    await expect(validator(rule, 50)).resolves.toBeUndefined()
    await expect(validator(rule, 0)).resolves.toBeUndefined()
    await expect(validator(rule, 100)).resolves.toBeUndefined()
  })

  it('应拒绝空值', async () => {
    const validator = validateNumberRange(0, 100, '测试值')
    const rule = {}
    await expect(validator(rule, '')).rejects.toBe('请输入测试值')
    await expect(validator(rule, undefined)).rejects.toBe('请输入测试值')
    await expect(validator(rule, null)).rejects.toBe('请输入测试值')
  })

  it('应拒绝超出范围的值', async () => {
    const validator = validateNumberRange(0, 100, '测试值')
    const rule = {}
    await expect(validator(rule, -1)).rejects.toBe('测试值范围: 0 到 100')
    await expect(validator(rule, 101)).rejects.toBe('测试值范围: 0 到 100')
  })

  it('应拒绝非数字', async () => {
    const validator = validateNumberRange(0, 100, '测试值')
    const rule = {}
    await expect(validator(rule, 'abc')).rejects.toBe('测试值必须是有效的数字')
  })
})

describe('validators 对象结构', () => {
  it('应包含所有预定义的验证规则', () => {
    expect(validators).toHaveProperty('coordinates')
    expect(validators).toHaveProperty('taskName')
    expect(validators).toHaveProperty('droneId')
    expect(validators).toHaveProperty('altitude')
    expect(validators).toHaveProperty('speed')
    expect(validators).toHaveProperty('riskThreshold')
    expect(validators).toHaveProperty('required')
    expect(validators).toHaveProperty('numberRange')
  })

  it('coordinates 应包含一个验证规则', () => {
    expect(validators.coordinates).toHaveLength(1)
    expect(validators.coordinates[0]).toHaveProperty('validator', validateCoordinates)
    expect(validators.coordinates[0]).toHaveProperty('trigger', 'blur')
  })

  it('required 应返回正确的验证规则数组', () => {
    const rules = validators.required('名称')
    expect(rules).toHaveLength(1)
    expect(rules[0]).toHaveProperty('trigger', 'blur')
  })

  it('numberRange 应返回正确的验证规则数组', () => {
    const rules = validators.numberRange(0, 10, '分数')
    expect(rules).toHaveLength(1)
    expect(rules[0]).toHaveProperty('required', true)
  })
})

describe('createRule', () => {
  it('应创建包含验证函数和触发方式的规则', () => {
    const fn = () => Promise.resolve()
    const rules = createRule(fn, 'change')
    expect(rules).toHaveLength(1)
    expect(rules[0].validator).toBe(fn)
    expect(rules[0].trigger).toBe('change')
  })

  it('默认 trigger 应为 blur', () => {
    const fn = () => Promise.resolve()
    const rules = createRule(fn)
    expect(rules[0].trigger).toBe('blur')
  })
})

describe('validateForm', () => {
  it('应返回 true 当验证通过', async () => {
    const formRef = { value: { validate: () => Promise.resolve() } }
    await expect(validateForm(formRef)).resolves.toBe(true)
  })

  it('应返回 false 当验证失败', async () => {
    const formRef = { value: { validate: () => Promise.reject(new Error('验证失败')) } }
    await expect(validateForm(formRef)).resolves.toBe(false)
  })

  it('应处理空表单引用', async () => {
    const formRef = { value: null }
    await expect(validateForm(formRef)).resolves.toBe(true)
  })
})

describe('resetForm', () => {
  it('应重置表单数据', () => {
    const formRef = { value: { resetFields: () => {} } }
    const formData = { name: 'test', age: 20 }
    const defaultValues = { name: '', age: '' }
    resetForm(formRef, formData, defaultValues)
    expect(formData.name).toBe('')
    expect(formData.age).toBe('')
  })

  it('不使用默认值时应清空字段', () => {
    const formRef = { value: { resetFields: () => {} } }
    const formData = { name: 'test' }
    resetForm(formRef, formData)
    expect(formData.name).toBe('')
  })
})
