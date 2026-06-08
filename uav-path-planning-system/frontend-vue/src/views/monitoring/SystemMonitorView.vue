<template>
  <div class="monitor">
    <div class="page-title">系统监控</div>

    <a-row :gutter="[16, 16]">
      <a-col :xs="24" :sm="12" :md="6">
        <a-card>
          <a-statistic title="CPU 使用率" :value="systemStore.status.cpu" suffix="%">
            <template #prefix><DashboardOutlined style="color: #1677ff" /></template>
          </a-statistic>
          <a-progress :percent="systemStore.status.cpu" status="active" />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :md="6">
        <a-card>
          <a-statistic title="内存使用率" :value="systemStore.status.memory" suffix="%">
            <template #prefix><DatabaseOutlined style="color: #52c41a" /></template>
          </a-statistic>
          <a-progress
            :percent="systemStore.status.memory"
            :status="systemStore.status.memory > 80 ? 'exception' : 'active'"
          />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :md="6">
        <a-card>
          <a-statistic title="磁盘使用率" :value="systemStore.status.disk" suffix="%">
            <template #prefix><HardDriveOutlined style="color: #faad14" /></template>
          </a-statistic>
          <a-progress :percent="systemStore.status.disk" status="normal" />
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :md="6">
        <a-card>
          <a-statistic title="活动任务" :value="systemStore.status.activeTasks" suffix="个">
            <template #prefix><ClusterOutlined style="color: #722ed1" /></template>
          </a-statistic>
        </a-card>
      </a-col>

      <a-col :span="24">
        <a-card title="服务状态">
          <a-table :columns="serviceColumns" :data-source="systemStore.services" :pagination="false" size="small">
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-badge
                  status="success"
                  :text="record.status"
                />
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>

      <a-col :xs="24" :lg="12">
        <a-card title="CPU / 内存趋势 (近 30 分钟)">
          <div ref="trendChartRef" class="chart-container"></div>
        </a-card>
      </a-col>
      <a-col :xs="24" :lg="12">
        <a-card title="磁盘 I/O">
          <div ref="diskChartRef" class="chart-container"></div>
        </a-card>
      </a-col>

      <a-col :span="24">
        <a-card title="告警列表">
          <a-list :data-source="systemStore.alerts">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta>
                  <template #title>
                    <a-space>
                      <a-tag :color="item.level === 'error' ? 'red' : item.level === 'warning' ? 'orange' : 'blue'">
                        {{ item.level.toUpperCase() }}
                      </a-tag>
                      <span>{{ item.message }}</span>
                    </a-space>
                  </template>
                  <template #description>{{ item.time }}</template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import {
  DashboardOutlined,
  DatabaseOutlined,
  HardDriveOutlined,
  ClusterOutlined
} from '@ant-design/icons-vue'
import { useSystemStore } from '../../stores/system'

const systemStore = useSystemStore()
const trendChartRef = ref(null)
const diskChartRef = ref(null)
let trendChart = null
let diskChart = null
let refreshTimer = null

const serviceColumns = [
  { title: '服务名称', dataIndex: 'name', key: 'name' },
  { title: '状态', key: 'status' },
  { title: '响应时间', dataIndex: 'response', key: 'response' },
  { title: '最后更新', dataIndex: 'lastUpdated', key: 'lastUpdated' }
]

function initCharts() {
  if (trendChartRef.value) {
    trendChart = echarts.init(trendChartRef.value)
    const data = Array.from({ length: 30 }, (_, i) => i * 2 + Math.random() * 10)
    const mem = Array.from({ length: 30 }, (_, i) => i * 1.5 + Math.random() * 8)
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['CPU (%)', '内存 (%)'] },
      xAxis: { type: 'category', data: Array.from({ length: 30 }, (_, i) => `${i}m`) },
      yAxis: { type: 'value', max: 100 },
      series: [
        { name: 'CPU (%)', type: 'line', smooth: true, data, itemStyle: { color: '#1677ff' } },
        { name: '内存 (%)', type: 'line', smooth: true, data: mem, itemStyle: { color: '#52c41a' } }
      ]
    })
  }
  if (diskChartRef.value) {
    diskChart = echarts.init(diskChartRef.value)
    diskChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['读取 (MB/s)', '写入 (MB/s)'] },
      xAxis: { type: 'category', data: Array.from({ length: 30 }, (_, i) => `${i}m`) },
      yAxis: { type: 'value' },
      series: [
        {
          name: '读取 (MB/s)',
          type: 'bar',
          data: Array.from({ length: 30 }, () => (Math.random() * 50).toFixed(1)),
          itemStyle: { color: '#13c2c2' }
        },
        {
          name: '写入 (MB/s)',
          type: 'bar',
          data: Array.from({ length: 30 }, () => (Math.random() * 30).toFixed(1)),
          itemStyle: { color: '#faad14' }
        }
      ]
    })
  }
}

function handleResize() {
  trendChart && trendChart.resize()
  diskChart && diskChart.resize()
}

function startAutoRefresh() {
  refreshTimer = setInterval(() => {
    systemStore.refreshMock()
  }, 5000)
}

onMounted(async () => {
  await systemStore.refreshStatus()
  nextTick(() => {
    initCharts()
    window.addEventListener('resize', handleResize)
    startAutoRefresh()
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  refreshTimer && clearInterval(refreshTimer)
  trendChart && trendChart.dispose()
  diskChart && diskChart.dispose()
})
</script>

<style scoped>
.monitor {
  padding: 0;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
  color: rgba(0, 0, 0, 0.88);
}

.chart-container {
  width: 100%;
  height: 300px;
}
</style>
