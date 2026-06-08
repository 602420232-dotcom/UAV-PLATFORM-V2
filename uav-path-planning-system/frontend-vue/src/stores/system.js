import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as systemApi from '../api/system'

export const useSystemStore = defineStore('system', () => {
  const status = ref({
    services: 5,
    cpu: 45,
    memory: 60,
    disk: 55,
    activeTasks: 12,
    healthScore: 92
  })

  const services = ref([
    { name: 'WRF处理服务', status: '运行中', response: '0.2s', lastUpdated: '2分钟前' },
    { name: '贝叶斯同化服务', status: '运行中', response: '0.5s', lastUpdated: '1分钟前' },
    { name: '气象预测服务', status: '运行中', response: '0.3s', lastUpdated: '3分钟前' },
    { name: '路径规划服务', status: '运行中', response: '0.4s', lastUpdated: '1分钟前' },
    { name: '主平台服务', status: '运行中', response: '0.1s', lastUpdated: '30秒前' }
  ])

  const alerts = ref([
    { id: 1, level: 'warning', message: 'WRF处理服务响应时间过长', time: '10分钟前' },
    { id: 2, level: 'info', message: '系统负载正常', time: '30分钟前' },
    { id: 3, level: 'error', message: '数据库连接数接近上限', time: '1小时前' },
    { id: 4, level: 'warning', message: '内存使用率超过60%', time: '2小时前' }
  ])

  const loading = ref(false)
  const error = ref(null)

  async function refreshStatus() {
    loading.value = true
    try {
      const res = await systemApi.getSystemStatus()
      const data = res?.data || res
      if (data && typeof data === 'object') {
        status.value = { ...status.value, ...data }
      }
    } catch (e) {
      error.value = e?.message || '获取系统状态失败'
    } finally {
      loading.value = false
    }
  }

  function refreshMock() {
    status.value = {
      services: 5,
      cpu: Math.floor(Math.random() * 30) + 30,
      memory: Math.floor(Math.random() * 20) + 50,
      disk: Math.floor(Math.random() * 10) + 50,
      activeTasks: Math.floor(Math.random() * 10) + 8,
      healthScore: Math.floor(Math.random() * 10) + 85
    }
  }

  return {
    status,
    services,
    alerts,
    loading,
    error,
    refreshStatus,
    refreshMock
  }
})
