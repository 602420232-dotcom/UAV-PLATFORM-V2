<template>
  <div class="weather">
    <div class="page-title">气象数据</div>

    <a-row :gutter="[16, 16]">
      <!-- 查询条件 -->
      <a-col :span="24">
        <a-card>
          <a-space wrap>
            <a-date-picker
              v-model:value="selectedDate"
              show-time
              placeholder="选择时间"
              style="width: 220px"
            />
            <a-select v-model:value="heightLevel" placeholder="高度层" style="width: 140px">
              <a-select-option value="ground">地面</a-select-option>
              <a-select-option value="100m">100m</a-select-option>
              <a-select-option value="500m">500m</a-select-option>
              <a-select-option value="1000m">1000m</a-select-option>
            </a-select>
            <a-select v-model:value="weatherElement" placeholder="气象要素" style="width: 160px">
              <a-select-option value="wind">风速/风向</a-select-option>
              <a-select-option value="temp">温度</a-select-option>
              <a-select-option value="humidity">湿度</a-select-option>
              <a-select-option value="pressure">气压</a-select-option>
            </a-select>
            <a-button type="primary" :loading="weatherStore.loading" @click="handleQuery">
              <template #icon><SearchOutlined /></template>
              查询
            </a-button>
            <a-button @click="handleRefresh">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </a-space>
        </a-card>
      </a-col>

      <!-- 当前气象概览 -->
      <a-col :xs="24" :sm="12" :md="6">
        <a-card>
          <a-statistic
            title="当前风速"
            :value="weatherStore.current?.windSpeed ?? 5.2"
            suffix="m/s"
          >
            <template #prefix><WindOutlined style="color: #13c2c2" /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :md="6">
        <a-card>
          <a-statistic
            title="当前温度"
            :value="weatherStore.current?.temperature ?? 25"
            suffix="°C"
          >
            <template #prefix><SunOutlined style="color: #faad14" /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :md="6">
        <a-card>
          <a-statistic
            title="湿度"
            :value="weatherStore.current?.humidity ?? 65"
            suffix="%"
          >
            <template #prefix><CloudOutlined style="color: #1677ff" /></template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :md="6">
        <a-card>
          <a-statistic
            title="风向"
            :value="weatherStore.current?.windDirection ?? 135"
            suffix="°"
          >
            <template #prefix><EnvironmentOutlined style="color: #722ed1" /></template>
          </a-statistic>
        </a-card>
      </a-col>

      <!-- 趋势图 -->
      <a-col :span="24">
        <a-card title="24小时气象趋势">
          <div ref="chartRef" class="chart-container"></div>
        </a-card>
      </a-col>

      <!-- 风场热力图 -->
      <a-col :span="24">
        <a-card title="区域风场热力图">
          <div ref="heatmapRef" class="heatmap-container">
            <a-empty v-if="!weatherStore.windField || weatherStore.windField.length === 0" description="暂无风场数据" />
            <a-row v-else :gutter="[8, 8]">
              <a-col
                v-for="(point, idx) in weatherStore.windField.slice(0, 12)"
                :key="idx"
                :xs="12"
                :sm="8"
                :md="6"
                :lg="4"
              >
                <a-card size="small" :bordered="true">
                  <a-descriptions :column="1" size="small">
                    <a-descriptions-item label="位置">{{ point.lat?.toFixed(2) }}, {{ point.lng?.toFixed(2) }}</a-descriptions-item>
                    <a-descriptions-item label="风速">{{ point.speed }} m/s</a-descriptions-item>
                    <a-descriptions-item label="温度">{{ point.temperature }} °C</a-descriptions-item>
                    <a-descriptions-item label="湿度">{{ point.humidity }} %</a-descriptions-item>
                  </a-descriptions>
                </a-card>
              </a-col>
            </a-row>
          </div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import * as echarts from 'echarts'
import {
  SearchOutlined,
  ReloadOutlined,
  WindOutlined,
  SunOutlined,
  CloudOutlined,
  EnvironmentOutlined
} from '@ant-design/icons-vue'
import { useWeatherStore } from '../../stores/weather'

const weatherStore = useWeatherStore()

const selectedDate = ref(null)
const heightLevel = ref('ground')
const weatherElement = ref('wind')

const chartRef = ref(null)
const heatmapRef = ref(null)
let chartInstance = null

function initChart() {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value)
  const hours = Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`)
  const windData = Array.from({ length: 24 }, () => (Math.random() * 6 + 2).toFixed(1))
  const tempData = Array.from({ length: 24 }, () => (Math.random() * 10 + 20).toFixed(1))
  const humidityData = Array.from({ length: 24 }, () => (Math.random() * 30 + 50).toFixed(0))

  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['风速 (m/s)', '温度 (°C)', '湿度 (%)'] },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: hours },
    yAxis: { type: 'value' },
    series: [
      {
        name: '风速 (m/s)',
        type: 'line',
        smooth: true,
        data: windData,
        itemStyle: { color: '#13c2c2' }
      },
      {
        name: '温度 (°C)',
        type: 'line',
        smooth: true,
        data: tempData,
        itemStyle: { color: '#faad14' }
      },
      {
        name: '湿度 (%)',
        type: 'line',
        smooth: true,
        data: humidityData,
        itemStyle: { color: '#1677ff' }
      }
    ]
  })
}

function handleResize() {
  chartInstance && chartInstance.resize()
}

async function handleQuery() {
  await weatherStore.fetchCurrent()
  message.success('查询完成')
}

async function handleRefresh() {
  await weatherStore.fetchCurrent()
  message.success('已刷新')
}

onMounted(async () => {
  await weatherStore.fetchCurrent()
  nextTick(() => {
    initChart()
    window.addEventListener('resize', handleResize)
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
.weather {
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
  height: 360px;
}

.heatmap-container {
  min-height: 120px;
}
</style>
