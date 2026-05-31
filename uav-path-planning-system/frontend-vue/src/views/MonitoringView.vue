<template>
  <a-card title="系统监控中心">
    <a-row :gutter="[16, 16]">
      <a-col :xs="24" :sm="12" :md="6" v-for="stat in stats" :key="stat.title">
        <a-card>
          <a-statistic :title="stat.title" :value="stat.value" :suffix="stat.suffix">
            <template #prefix>
              <component :is="stat.icon" :style="{ color: stat.color }" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <a-divider />

    <a-spin :spinning="loading">
      <a-row :gutter="[16, 16]">
        <a-col :span="24">
          <a-card title="服务健康状态" size="small">
            <a-table :columns="svcCols" :data-source="serviceStatus" row-key="name" :pagination="false" size="small" />
          </a-card>
        </a-col>
        <a-col :xs="24" :lg="12">
          <a-card title="告警列表" size="small">
            <a-timeline>
              <a-timeline-item v-for="alert in alerts" :key="alert.id" :color="alert.level === 'critical' ? 'red' : 'orange'">
                {{ alert.message }}
              </a-timeline-item>
            </a-timeline>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>
  </a-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  DashboardOutlined, CloudOutlined, DeploymentUnitOutlined,
  CheckCircleOutlined, AlertOutlined,
} from '@ant-design/icons-vue'
import { getSystemStatus, getServiceHealth, getAlerts } from '../api/system'

const loading = ref(false)
const stats = ref([])
const serviceStatus = ref([])
const alerts = ref([])

const svcCols = [
  { title: '服务名称', dataIndex: 'name', key: 'name' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '端口', dataIndex: 'port', key: 'port' },
  { title: '响应时间', dataIndex: 'responseTime', key: 'responseTime' },
]

const loadMonitoring = async () => {
  loading.value = true
  try {
    const [statusRes, healthRes, alertsRes] = await Promise.allSettled([
      getSystemStatus(),
      getServiceHealth(),
      getAlerts(),
    ])
    if (statusRes.status === 'fulfilled') {
      const d = statusRes.value || {}
      stats.value = [
        { title: '活跃服务', value: (d.data || d).activeServices || 5, suffix: '个', icon: DashboardOutlined, color: '#1677ff' },
        { title: '活跃任务', value: (d.data || d).activeTasks || 0, suffix: '个', icon: DeploymentUnitOutlined, color: '#52c41a' },
        { title: '健康评分', value: (d.data || d).healthScore || 92, suffix: '分', icon: CheckCircleOutlined, color: '#722ed1' },
        { title: '告警', value: alerts.value.length || 0, suffix: '条', icon: AlertOutlined, color: '#ff4d4f' },
      ]
    }
    if (alertsRes.status === 'fulfilled') {
      alerts.value = Array.isArray(alertsRes.value) ? alertsRes.value : (alertsRes.value?.data || [])
    }
    if (healthRes.status === 'fulfilled') {
      const h = healthRes.value || {}
      const components = h.components || (h.data && h.data.components) || {}
      serviceStatus.value = Object.entries(components).map(([name, info]) => ({
        name,
        status: info.status === 'UP' ? '运行中' : '异常',
        port: '-',
        responseTime: '-',
      }))
      if (serviceStatus.value.length === 0) {
        serviceStatus.value = [
          { name: 'API Gateway', status: '运行中', port: '8088', responseTime: '23ms' },
          { name: 'UAV Platform', status: '运行中', port: '8080', responseTime: '45ms' },
        ]
      }
    }
  } catch {
    loadDemo()
  } finally {
    loading.value = false
  }
}

const loadDemo = () => {
  stats.value = [
    { title: '活跃服务', value: 5, suffix: '个', icon: DashboardOutlined, color: '#1677ff' },
    { title: '活跃任务', value: 12, suffix: '个', icon: DeploymentUnitOutlined, color: '#52c41a' },
    { title: '健康评分', value: 92, suffix: '分', icon: CheckCircleOutlined, color: '#722ed1' },
    { title: '告警', value: 4, suffix: '条', icon: AlertOutlined, color: '#ff4d4f' },
  ]
  serviceStatus.value = [
    { name: 'API Gateway', status: '运行中', port: '8088', responseTime: '23ms' },
    { name: 'UAV Platform', status: '运行中', port: '8080', responseTime: '45ms' },
  ]
  alerts.value = [
    { id: 1, level: 'critical', message: 'CPU使用率超过90%' },
    { id: 2, level: 'warning', message: '内存使用率达到85%' },
    { id: 3, level: 'warning', message: '磁盘空间不足' },
  ]
}

onMounted(loadMonitoring)
setInterval(loadMonitoring, 60000)
</script>
