<template>
  <div class="cockpit">
    <div class="cockpit-header">
      <div class="cockpit-title">
        <span class="cockpit-icon">✈</span>
        <h2>无人机路径规划 · 智能驾驶舱</h2>
      </div>
      <div class="cockpit-time">{{ currentTime }}</div>
    </div>

    <a-row :gutter="[16, 16]">
      <!-- 左上：气象态势 -->
      <a-col :xs="24" :lg="12">
        <a-card title="气象态势" class="cockpit-card">
          <a-row :gutter="[12, 12]">
            <a-col :span="12">
              <div class="metric-box">
                <div class="metric-label">风速</div>
                <div class="metric-value">{{ weatherStore.current?.windSpeed ?? 5.2 }} <span class="metric-unit">m/s</span></div>
              </div>
            </a-col>
            <a-col :span="12">
              <div class="metric-box">
                <div class="metric-label">温度</div>
                <div class="metric-value">{{ weatherStore.current?.temperature ?? 25 }} <span class="metric-unit">°C</span></div>
              </div>
            </a-col>
            <a-col :span="12">
              <div class="metric-box">
                <div class="metric-label">湿度</div>
                <div class="metric-value">{{ weatherStore.current?.humidity ?? 65 }} <span class="metric-unit">%</span></div>
              </div>
            </a-col>
            <a-col :span="12">
              <div class="metric-box">
                <div class="metric-label">风向</div>
                <div class="metric-value">{{ weatherStore.current?.windDirection ?? 135 }} <span class="metric-unit">°</span></div>
              </div>
            </a-col>
          </a-row>
        </a-card>
      </a-col>

      <!-- 右上：飞行态势 -->
      <a-col :xs="24" :lg="12">
        <a-card title="飞行态势" class="cockpit-card">
          <a-row :gutter="[12, 12]">
            <a-col :span="12">
              <a-progress
                type="circle"
                :percent="droneFlying"
                :format="(p) => `${p}%`"
              />
              <div class="circle-label">飞行中</div>
            </a-col>
            <a-col :span="12">
              <a-progress
                type="circle"
                :percent="droneIdle"
                status="active"
                :format="(p) => `${p}%`"
              />
              <div class="circle-label">待命</div>
            </a-col>
          </a-row>
        </a-card>
      </a-col>

      <!-- 中间左：任务态势 -->
      <a-col :xs="24" :lg="8">
        <a-card title="任务态势" class="cockpit-card">
          <a-statistic title="今日任务总数" :value="taskCount" style="margin-bottom: 16px" />
          <div class="ring-row">
            <div v-for="item in taskRings" :key="item.label" class="ring-item">
              <a-progress type="dashboard" :percent="item.value" :stroke-color="item.color" />
              <div class="ring-label">{{ item.label }}</div>
            </div>
          </div>
        </a-card>
      </a-col>

      <!-- 中间中：地理信息 -->
      <a-col :xs="24" :lg="8">
        <a-card title="地理信息态势" class="cockpit-card">
          <div class="geo-box">
            <a-descriptions :column="1" size="small">
              <a-descriptions-item label="覆盖区域">{{ geo.region }}</a-descriptions-item>
              <a-descriptions-item label="禁飞区数量">{{ geo.noFlyZones }}</a-descriptions-item>
              <a-descriptions-item label="活跃航点">{{ geo.activeWaypoints }}</a-descriptions-item>
              <a-descriptions-item label="实时追踪无人机">{{ geo.drones }}</a-descriptions-item>
            </a-descriptions>
          </div>
        </a-card>
      </a-col>

      <!-- 中间右：风险预警 -->
      <a-col :xs="24" :lg="8">
        <a-card title="风险预警" class="cockpit-card">
          <a-row :gutter="[8, 8]">
            <a-col :span="12">
              <div class="risk-box high">
                <div class="risk-label">高风险</div>
                <div class="risk-value">{{ risks.high }}</div>
              </div>
            </a-col>
            <a-col :span="12">
              <div class="risk-box medium">
                <div class="risk-label">中风险</div>
                <div class="risk-value">{{ risks.medium }}</div>
              </div>
            </a-col>
            <a-col :span="12">
              <div class="risk-box low">
                <div class="risk-label">低风险</div>
                <div class="risk-value">{{ risks.low }}</div>
              </div>
            </a-col>
            <a-col :span="12">
              <div class="risk-box safe">
                <div class="risk-label">安全</div>
                <div class="risk-value">{{ risks.safe }}</div>
              </div>
            </a-col>
          </a-row>
        </a-card>
      </a-col>

      <!-- 底部：趋势图表 -->
      <a-col :span="24">
        <a-card title="实时任务/气象综合趋势" class="cockpit-card">
          <div ref="trendChartRef" class="trend-chart"></div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useWeatherStore } from '../../stores/weather'
import { useTaskStore } from '../../stores/tasks'
import { useDroneStore } from '../../stores/drones'

const weatherStore = useWeatherStore()
const taskStore = useTaskStore()
const droneStore = useDroneStore()

const currentTime = ref(new Date().toLocaleString('zh-CN', { hour12: false }))
let timeTimer = null
let trendChart = null
const trendChartRef = ref(null)

const droneFlying = computed(() => {
  const total = droneStore.list.length || 5
  const flying = droneStore.list.filter((d) => d.status === '执行任务').length || 2
  return Math.round((flying / total) * 100)
})

const droneIdle = computed(() => {
  const total = droneStore.list.length || 5
  const idle = droneStore.list.filter((d) => d.status === '待命' || d.status === '在线').length || 3
  return Math.round((idle / total) * 100)
})

const taskCount = computed(() => taskStore.list.length || 12)
const taskRings = computed(() => [
  { label: '已完成', value: 60, color: '#52c41a' },
  { label: '执行中', value: 25, color: '#1677ff' },
  { label: '待分配', value: 15, color: '#faad14' }
])

const geo = {
  region: '北京及周边区域',
  noFlyZones: 8,
  activeWaypoints: 24,
  drones: 5
}

const risks = {
  high: 1,
  medium: 3,
  low: 7,
  safe: 15
}

function initTrendChart() {
  if (!trendChartRef.value) return
  trendChart = echarts.init(trendChartRef.value)
  const times = Array.from({ length: 20 }, (_, i) => `${String(i * 3).padStart(2, '0')}:00`)
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['任务完成数', '平均风速', '平均温度'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: times },
    yAxis: { type: 'value' },
    series: [
      {
        name: '任务完成数',
        type: 'bar',
        data: Array.from({ length: 20 }, () => Math.floor(Math.random() * 10)),
        itemStyle: { color: '#1677ff' }
      },
      {
        name: '平均风速',
        type: 'line',
        smooth: true,
        yAxisIndex: 0,
        data: Array.from({ length: 20 }, () => (Math.random() * 6 + 2).toFixed(1)),
        itemStyle: { color: '#13c2c2' }
      },
      {
        name: '平均温度',
        type: 'line',
        smooth: true,
        data: Array.from({ length: 20 }, () => (Math.random() * 10 + 20).toFixed(1)),
        itemStyle: { color: '#faad14' }
      }
    ]
  })
}

function handleResize() {
  trendChart && trendChart.resize()
}

onMounted(async () => {
  await Promise.all([weatherStore.fetchCurrent(), taskStore.fetchAll(), droneStore.fetchAll()])
  timeTimer = setInterval(() => {
    currentTime.value = new Date().toLocaleString('zh-CN', { hour12: false })
  }, 1000)
  nextTick(() => {
    initTrendChart()
    window.addEventListener('resize', handleResize)
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  timeTimer && clearInterval(timeTimer)
  if (trendChart) {
    trendChart.dispose()
    trendChart = null
  }
})
</script>

<style scoped>
.cockpit {
  padding: 16px 24px 24px;
  background: linear-gradient(135deg, #001529 0%, #003a8c 50%, #001529 100%);
  min-height: 100vh;
}

.cockpit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 16px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 8px;
  color: #fff;
}

.cockpit-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cockpit-icon {
  font-size: 28px;
  color: #40a9ff;
}

.cockpit-title h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #fff;
}

.cockpit-time {
  font-size: 14px;
  font-family: 'Courier New', monospace;
  color: #91d5ff;
}

.cockpit-card :deep(.ant-card-head-title),
.cockpit-card :deep(.ant-card) {
  background: rgba(255, 255, 255, 0.98);
}

.metric-box {
  padding: 12px;
  text-align: center;
  background: linear-gradient(135deg, #e6f7ff, #bae7ff);
  border-radius: 8px;
}

.metric-label {
  font-size: 13px;
  color: rgba(0, 0, 0, 0.55);
  margin-bottom: 4px;
}

.metric-value {
  font-size: 24px;
  font-weight: 600;
  color: #1677ff;
}

.metric-unit {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin-left: 2px;
}

.circle-label {
  text-align: center;
  margin-top: 8px;
  font-size: 13px;
  color: rgba(0, 0, 0, 0.65);
}

.ring-row {
  display: flex;
  justify-content: space-around;
  margin-top: 12px;
}

.ring-item {
  text-align: center;
}

.ring-label {
  margin-top: 6px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.55);
}

.geo-box {
  padding: 8px 0;
}

.risk-box {
  padding: 12px;
  text-align: center;
  border-radius: 8px;
  color: #fff;
}

.risk-box.high {
  background: linear-gradient(135deg, #ff7875, #ff4d4f);
}

.risk-box.medium {
  background: linear-gradient(135deg, #ffc069, #fa8c16);
}

.risk-box.low {
  background: linear-gradient(135deg, #ffd666, #faad14);
}

.risk-box.safe {
  background: linear-gradient(135deg, #95de64, #52c41a);
}

.risk-label {
  font-size: 12px;
  opacity: 0.9;
}

.risk-value {
  font-size: 24px;
  font-weight: 700;
  margin-top: 4px;
}

.trend-chart {
  width: 100%;
  height: 280px;
}
</style>
