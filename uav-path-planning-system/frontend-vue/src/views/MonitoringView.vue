<template>
  <a-card title="系统监控" class="monitoring-card">
    <a-row :gutter="[16, 16]">
      <!-- 系统概览 -->
      <a-col :span="24">
        <a-card title="系统概览">
          <a-row :gutter="[16, 16]">
            <a-col :span="4">
              <a-statistic title="服务状态" :value="systemStatus.services" suffix="/5">
                <template #prefix>
                  <span :class="systemStatus.services === 5 ? 'status-green' : 'status-yellow'">
                    <CheckCircleOutlined />
                  </span>
                </template>
              </a-statistic>
            </a-col>
            <a-col :span="4">
              <a-statistic title="CPU使用率" :value="systemStatus.cpu" suffix="%">
                <template #prefix>
                  <span :class="systemStatus.cpu < 70 ? 'status-green' : 'status-yellow'">
                    <CpuOutlined />
                  </span>
                </template>
              </a-statistic>
            </a-col>
            <a-col :span="4">
              <a-statistic title="内存使用率" :value="systemStatus.memory" suffix="%">
                <template #prefix>
                  <span :class="systemStatus.memory < 70 ? 'status-green' : 'status-yellow'">
                    <DatabaseOutlined />
                  </span>
                </template>
              </a-statistic>
            </a-col>
            <a-col :span="4">
              <a-statistic title="磁盘使用率" :value="systemStatus.disk" suffix="%">
                <template #prefix>
                  <span :class="systemStatus.disk < 70 ? 'status-green' : 'status-yellow'">
                    <HddOutlined />
                  </span>
                </template>
              </a-statistic>
            </a-col>
            <a-col :span="4">
              <a-statistic title="活跃任务" :value="systemStatus.activeTasks">
                <template #prefix>
                  <span class="status-blue">
                    <OrderedListOutlined />
                  </span>
                </template>
              </a-statistic>
            </a-col>
            <a-col :span="4">
              <a-statistic title="系统健康" :value="systemStatus.healthScore" suffix="%">
                <template #prefix>
                  <span :class="systemStatus.healthScore > 80 ? 'status-green' : 'status-yellow'">
                    <HeartOutlined />
                  </span>
                </template>
              </a-statistic>
            </a-col>
          </a-row>
        </a-card>
      </a-col>
      
      <!-- 服务状态 -->
      <a-col :span="12">
        <a-card title="服务状态">
          <a-list :data-source="serviceStatus" :render-item="renderServiceItem" />
        </a-card>
      </a-col>
      
      <!-- 算法性能 -->
      <a-col :span="12">
        <a-card title="算法性能">
          <a-list :data-source="algorithmPerformance" :render-item="renderAlgorithmItem" />
        </a-card>
      </a-col>
      
      <!-- 系统负载 -->
      <a-col :span="24">
        <a-card title="系统负载">
          <div ref="loadChart" class="chart-container"></div>
        </a-card>
      </a-col>
      
      <!-- 服务响应时间 -->
      <a-col :span="24">
        <a-card title="服务响应时间">
          <div ref="responseTimeChart" class="chart-container"></div>
        </a-card>
      </a-col>
      
      <!-- 任务执行统计 -->
      <a-col :span="12">
        <a-card title="任务执行统计">
          <div ref="taskStatsChart" class="chart-container"></div>
        </a-card>
      </a-col>
      
      <!-- 系统告警 -->
      <a-col :span="12">
        <a-card title="系统告警" :extra="<a href='#'>查看全部</a>">
          <a-list :data-source="alerts" :render-item="renderAlertItem" />
        </a-card>
      </a-col>
      
      <!-- 最近任务 -->
      <a-col :span="24">
        <a-card title="最近任务">
          <a-table :columns="taskColumns" :data-source="recentTasks" />
        </a-card>
      </a-col>
    </a-row>
  </a-card>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { CheckCircleOutlined, CpuOutlined, DatabaseOutlined, HddOutlined, RocketOutlined, CloudOutlined, OrderedListOutlined, ClockCircleOutlined, HeartOutlined, AlertOutlined, LineChartOutlined, BarChartOutlined, PieChartOutlined } from '@ant-design/icons-vue'
import * as echarts from 'echarts'

// 响应式数据
const systemStatus = ref({
  services: 5,
  cpu: 45,
  memory: 60,
  disk: 55,
  activeTasks: 12,
  healthScore: 92
})

const serviceStatus = ref([
  { name: 'WRF处理服务', status: '运行中', response: '0.2s', lastUpdated: '2分钟前' },
  { name: '贝叶斯同化服务', status: '运行中', response: '0.5s', lastUpdated: '1分钟前' },
  { name: '气象预测服务', status: '运行中', response: '0.3s', lastUpdated: '3分钟前' },
  { name: '路径规划服务', status: '运行中', response: '0.4s', lastUpdated: '1分钟前' },
  { name: '主平台服务', status: '运行中', response: '0.1s', lastUpdated: '30秒前' }
])

const algorithmPerformance = ref([
  { name: '3D-VAR', averageTime: '2.5s', successRate: '98%' },
  { name: 'EnKF', averageTime: '4.2s', successRate: '95%' },
  { name: '混合算法', averageTime: '3.1s', successRate: '99%' },
  { name: 'VRPTW', averageTime: '1.8s', successRate: '97%' },
  { name: 'A*', averageTime: '0.5s', successRate: '99%' },
  { name: 'DWA', averageTime: '0.1s', successRate: '100%' }
])

const recentTasks = ref([
  { id: 1, name: '路径规划任务1', status: '成功', startTime: '2024-01-01 10:00:00', endTime: '2024-01-01 10:02:30', duration: '2分30秒' },
  { id: 2, name: '气象预测任务', status: '成功', startTime: '2024-01-01 09:45:00', endTime: '2024-01-01 09:46:15', duration: '1分15秒' },
  { id: 3, name: '路径规划任务2', status: '成功', startTime: '2024-01-01 09:30:00', endTime: '2024-01-01 09:33:45', duration: '3分45秒' },
  { id: 4, name: '贝叶斯同化任务', status: '成功', startTime: '2024-01-01 09:15:00', endTime: '2024-01-01 09:18:30', duration: '3分30秒' }
])

const alerts = ref([
  { id: 1, level: 'warning', message: 'WRF处理服务响应时间过长', time: '10分钟前' },
  { id: 2, level: 'info', message: '系统负载正常', time: '30分钟前' },
  { id: 3, level: 'error', message: '数据库连接数接近上限', time: '1小时前' },
  { id: 4, level: 'warning', message: '内存使用率超过60%', time: '2小时前' }
])

const taskColumns = [
  { title: '任务ID', dataIndex: 'id', key: 'id' },
  { title: '任务名称', dataIndex: 'name', key: 'name' },
  { title: '状态', dataIndex: 'status', key: 'status' },
  { title: '开始时间', dataIndex: 'startTime', key: 'startTime' },
  { title: '结束时间', dataIndex: 'endTime', key: 'endTime' },
  { title: '耗时', dataIndex: 'duration', key: 'duration' }
]

let loadChart = null
let responseTimeChart = null
let taskStatsChart = null

// 方法
const renderServiceItem = (service) => {
  const statusColor = service.status === '运行中' ? 'green' : 'red'
  return (
    <a-list-item>
      <a-list-item-meta title={service.name} description={`响应时间: ${service.response} | 最后更新: ${service.lastUpdated}`} />
      <a-tag :color={statusColor}>{service.status}</a-tag>
    </a-list-item>
  )
}

const renderAlgorithmItem = (algorithm) => {
  return (
    <a-list-item>
      <a-list-item-meta title={algorithm.name} description={`平均时间: ${algorithm.averageTime}`} />
      <a-tag color="blue">{algorithm.successRate}</a-tag>
    </a-list-item>
  )
}

const renderAlertItem = (alert) => {
  const levelColor = {
    'info': 'blue',
    'warning': 'orange',
    'error': 'red'
  }
  return (
    <a-list-item>
      <a-list-item-meta title={alert.message} description={alert.time} />
      <a-tag :color={levelColor[alert.level]}>{alert.level}</a-tag>
    </a-list-item>
  )
}

const initLoadChart = () => {
  const loadChartElement = document.querySelector('.chart-container')
  if (loadChartElement && !loadChart) {
    loadChart = echarts.init(loadChartElement)
  }
  
  if (loadChart) {
    const option = {
      title: {
        text: '系统负载趋势',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          label: {
            backgroundColor: '#6a7985'
          }
        }
      },
      legend: {
        data: ['CPU', '内存', '磁盘'],
        bottom: 0
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true
      },
      xAxis: [
        {
          type: 'category',
          boundaryGap: false,
          data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
        }
      ],
      yAxis: [
        {
          type: 'value',
          name: '使用率(%)',
          max: 100
        }
      ],
      series: [
        {
          name: 'CPU',
          type: 'line',
          stack: 'Total',
          areaStyle: {},
          emphasis: {
            focus: 'series'
          },
          data: [30, 40, 55, 45, 60, 45]
        },
        {
          name: '内存',
          type: 'line',
          stack: 'Total',
          areaStyle: {},
          emphasis: {
            focus: 'series'
          },
          data: [45, 50, 65, 60, 70, 60]
        },
        {
          name: '磁盘',
          type: 'line',
          stack: 'Total',
          areaStyle: {},
          emphasis: {
            focus: 'series'
          },
          data: [40, 45, 55, 50, 60, 55]
        }
      ]
    }
    
    loadChart.setOption(option)
  }
}

const initResponseTimeChart = () => {
  const responseTimeChartElement = document.querySelectorAll('.chart-container')[1]
  if (responseTimeChartElement && !responseTimeChart) {
    responseTimeChart = echarts.init(responseTimeChartElement)
  }
  
  if (responseTimeChart) {
    const option = {
      title: {
        text: '服务响应时间',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          label: {
            backgroundColor: '#6a7985'
          }
        }
      },
      legend: {
        data: ['WRF处理服务', '贝叶斯同化服务', '气象预测服务', '路径规划服务', '主平台服务'],
        bottom: 0
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true
      },
      xAxis: [
        {
          type: 'category',
          boundaryGap: false,
          data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']
        }
      ],
      yAxis: [
        {
          type: 'value',
          name: '响应时间(ms)'
        }
      ],
      series: [
        {
          name: 'WRF处理服务',
          type: 'line',
          data: [200, 250, 300, 220, 280, 230]
        },
        {
          name: '贝叶斯同化服务',
          type: 'line',
          data: [500, 600, 700, 550, 650, 580]
        },
        {
          name: '气象预测服务',
          type: 'line',
          data: [300, 350, 400, 320, 380, 340]
        },
        {
          name: '路径规划服务',
          type: 'line',
          data: [400, 450, 500, 420, 480, 430]
        },
        {
          name: '主平台服务',
          type: 'line',
          data: [100, 150, 200, 120, 180, 140]
        }
      ]
    }
    
    responseTimeChart.setOption(option)
  }
}

const initTaskStatsChart = () => {
  const taskStatsChartElement = document.querySelectorAll('.chart-container')[2]
  if (taskStatsChartElement && !taskStatsChart) {
    taskStatsChart = echarts.init(taskStatsChartElement)
  }
  
  if (taskStatsChart) {
    const option = {
      title: {
        text: '任务执行统计',
        left: 'center'
      },
      tooltip: {
        trigger: 'item'
      },
      legend: {
        orient: 'vertical',
        left: 'left'
      },
      series: [
        {
          name: '任务类型',
          type: 'pie',
          radius: '60%',
          data: [
            { value: 35, name: '路径规划' },
            { value: 25, name: '气象预测' },
            { value: 20, name: '贝叶斯同化' },
            { value: 15, name: 'WRF处理' },
            { value: 5, name: '其他' }
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }
    
    taskStatsChart.setOption(option)
  }
}

// 生命周期
let updateInterval = null
const handleResize = () => {
  if (loadChart) loadChart.resize()
  if (responseTimeChart) responseTimeChart.resize()
  if (taskStatsChart) taskStatsChart.resize()
}
onMounted(() => {
  initLoadChart()
  initResponseTimeChart()
  initTaskStatsChart()
  
  updateInterval = setInterval(() => {
    systemStatus.value.cpu = Math.floor(Math.random() * 30) + 30
    systemStatus.value.memory = Math.floor(Math.random() * 20) + 50
    systemStatus.value.disk = Math.floor(Math.random() * 10) + 50
    systemStatus.value.activeTasks = Math.floor(Math.random() * 10) + 8
    systemStatus.value.healthScore = Math.floor(Math.random() * 10) + 85
  }, 5000)
  
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (updateInterval) clearInterval(updateInterval)
  window.removeEventListener('resize', handleResize)
  if (loadChart) loadChart.dispose()
  if (responseTimeChart) responseTimeChart.dispose()
  if (taskStatsChart) taskStatsChart.dispose()
})

onUnmounted(() => {
  if (loadChart) {
    loadChart.dispose()
  }
  if (responseTimeChart) {
    responseTimeChart.dispose()
  }
  if (taskStatsChart) {
    taskStatsChart.dispose()
  }
})
</script>

<style scoped>
.monitoring-card {
  margin-bottom: 24px;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.status-green {
  color: #52c41a;
}

.status-yellow {
  color: #faad14;
}

.status-red {
  color: #f5222d;
}
</style>