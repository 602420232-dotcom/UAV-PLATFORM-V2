/**
 * 表单验证器工具
 * 提供统一的表单验证规则和验证函数
 */

/**
 * 坐标格式验证
 * 支持格式: "纬度, 经度" 或 "纬度,经度"
 */
export const validateCoordinates = (rule, value) => {
  if (!value) {
    return Promise.reject('请输入坐标');
  }
  
  const pattern = /^(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)$/;
  if (!pattern.test(value)) {
    return Promise.reject('坐标格式错误，应为: 纬度, 经度');
  }
  
  const parts = value.split(',').map(p => p.trim());
  const lat = parseFloat(parts[0]);
  const lng = parseFloat(parts[1]);
  
  if (isNaN(lat) || isNaN(lng)) {
    return Promise.reject('坐标必须是有效的数字');
  }
  
  if (lat < -90 || lat > 90) {
    return Promise.reject('纬度范围: -90 到 90');
  }
  
  if (lng < -180 || lng > 180) {
    return Promise.reject('经度范围: -180 到 180');
  }
  
  return Promise.resolve();
};

/**
 * 任务名称验证
 */
export const validateTaskName = (rule, value) => {
  if (!value || !value.trim()) {
    return Promise.reject('请输入任务名称');
  }
  
  if (value.length > 50) {
    return Promise.reject('任务名称不能超过50个字符');
  }
  
  if (value.length < 2) {
    return Promise.reject('任务名称至少2个字符');
  }
  
  return Promise.resolve();
};

/**
 * 无人机ID验证
 */
export const validateDroneId = (rule, value) => {
  if (!value) {
    return Promise.reject('请选择无人机');
  }
  
  const pattern = /^UAV-\d{3}$/;
  if (!pattern.test(value)) {
    return Promise.reject('无人机ID格式错误，应为: UAV-XXX');
  }
  
  return Promise.resolve();
};

/**
 * 高度验证
 */
export const validateAltitude = (rule, value) => {
  if (value === undefined || value === null || value === '') {
    return Promise.reject('请输入高度');
  }
  
  const alt = parseFloat(value);
  if (isNaN(alt)) {
    return Promise.reject('高度必须是有效的数字');
  }
  
  if (alt < 0) {
    return Promise.reject('高度不能为负数');
  }
  
  if (alt > 10000) {
    return Promise.reject('高度不能超过10000米');
  }
  
  return Promise.resolve();
};

/**
 * 速度验证
 */
export const validateSpeed = (rule, value) => {
  if (value === undefined || value === null || value === '') {
    return Promise.reject('请输入速度');
  }
  
  const speed = parseFloat(value);
  if (isNaN(speed)) {
    return Promise.reject('速度必须是有效的数字');
  }
  
  if (speed < 0) {
    return Promise.reject('速度不能为负数');
  }
  
  if (speed > 500) {
    return Promise.reject('速度不能超过500 m/s');
  }
  
  return Promise.resolve();
};

/**
 * 风险阈值验证
 */
export const validateRiskThreshold = (rule, value) => {
  if (value === undefined || value === null) {
    return Promise.reject('请设置风险阈值');
  }
  
  const threshold = parseFloat(value);
  if (isNaN(threshold)) {
    return Promise.reject('风险阈值必须是有效的数字');
  }
  
  if (threshold < 0 || threshold > 10) {
    return Promise.reject('风险阈值范围: 0 到 10');
  }
  
  return Promise.resolve();
};

/**
 * 必填字段验证
 */
export const validateRequired = (fieldName) => {
  return (rule, value) => {
    if (value === undefined || value === null || value === '') {
      return Promise.reject(`请输入${fieldName}`);
    }
    return Promise.resolve();
  };
};

/**
 * 数字范围验证
 */
export const validateNumberRange = (min, max, fieldName = '数值') => {
  return (rule, value) => {
    if (value === undefined || value === null || value === '') {
      return Promise.reject(`请输入${fieldName}`);
    }
    
    const num = parseFloat(value);
    if (isNaN(num)) {
      return Promise.reject(`${fieldName}必须是有效的数字`);
    }
    
    if (num < min || num > max) {
      return Promise.reject(`${fieldName}范围: ${min} 到 ${max}`);
    }
    
    return Promise.resolve();
  };
};

/**
 * 预定义的验证规则
 */
export const validators = {
  // 坐标验证
  coordinates: [
    { required: true, validator: validateCoordinates, trigger: 'blur' }
  ],
  
  // 任务名称验证
  taskName: [
    { required: true, validator: validateTaskName, trigger: 'blur' }
  ],
  
  // 无人机ID验证
  droneId: [
    { required: true, validator: validateDroneId, trigger: 'blur' }
  ],
  
  // 高度验证
  altitude: [
    { required: true, validator: validateAltitude, trigger: 'blur' }
  ],
  
  // 速度验证
  speed: [
    { required: true, validator: validateSpeed, trigger: 'blur' }
  ],
  
  // 风险阈值验证
  riskThreshold: [
    { required: true, validator: validateRiskThreshold, trigger: 'change' }
  ],
  
  // 必填验证
  required: (fieldName) => [
    { required: true, validator: validateRequired(fieldName), trigger: 'blur' }
  ],
  
  // 数字范围验证
  numberRange: (min, max, fieldName) => [
    { required: true, validator: validateNumberRange(min, max, fieldName), trigger: 'blur' }
  ]
};

/**
 * 创建自定义验证规则
 * @param {Function} validateFn - 验证函数
 * @param {string} trigger - 触发方式
 * @returns {Array} 验证规则数组
 */
export const createRule = (validateFn, trigger = 'blur') => {
  return [
    { required: true, validator: validateFn, trigger }
  ];
};

/**
 * 批量验证表单
 * @param {Object} formRef - 表单引用
 * @returns {Promise<boolean>} 验证结果
 */
export const validateForm = async (formRef) => {
  try {
    await formRef.value?.validate();
    return true;
  } catch (error) {
    console.error('表单验证失败:', error);
    return false;
  }
};

/**
 * 重置表单
 * @param {Object} formRef - 表单引用
 * @param {Object} formData - 表单数据
 * @param {Object} defaultValues - 默认值
 */
export const resetForm = (formRef, formData, defaultValues = {}) => {
  formRef.value?.resetFields();
  Object.keys(formData).forEach(key => {
    formData[key] = defaultValues[key] ?? '';
  });
};

export default validators;
