<template>
  <a-card title="气象数据" class="weather-card">
    <a-row :gutter="[16, 16]">
      <!-- 左侧气象数据面板 -->
      <a-col :span="8">
        <a-card title="气象参数">
          <a-form :model="formState" layout="vertical">
            <a-form-item label="时间">
              <a-date-picker v-model:value="selectedTime" show-time style="width: 100%" />
            </a-form-item>
            <a-form-item label="高度">
              <a-select v-model:value="selectedHeight" style="width: 100%">
                <a-option value="10">10m</a-option>
                <a-option value="50">50m</a-option>
                <a-option value="100">100m</a-option>
                <a-option value="200">200m</a-option>
                <a-option value="500">500m</a-option>
                <a-option value="1000">1000m</a-option>
              </a-select>
            </a-form-item>
            <a-form-item label="气象要素">
              <a-checkbox-group v-model:value="selectedElements">
                <a-checkbox value="wind">风速风向</a-checkbox>
                <a-checkbox value="temperature">温度</a-checkbox>
                <a-checkbox value="humidity">湿度</a-checkbox>
                <a-checkbox value="turbulence">湍流</a-checkbox>
                <a-checkbox value="visibility">能见度</a-checkbox>
                <a-checkbox value="risk">风险等级</a-checkbox>
              </a-checkbox-group>
            </a-form-item>
            <a-form-item>
              <a-button type="primary" block @click="loadWeatherData">
                <template #icon>
                  <CloudOutlined />
                </template>
                加载气象数据
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>
        
        <!-- 气象数据详情 -->
        <a-card title="数据详情" style="margin-top: 16px">
          <div v-if="weatherData" class="weather-details">
            <a-descriptions bordered>
              <a-descriptions-item label="风速">
                {{ weatherData.windSpeed }} m/s
              </a-descriptions-item>
              <a-descriptions-item label="风向">
                {{ weatherData.windDirection }}°
              </a-descriptions-item>
              <a-descriptions-item label="温度">
                {{ weatherData.temperature }} °C
              </a-descriptions-item>
              <a-descriptions-item label="湿度">
                {{ weatherData.humidity }}%
              </a-descriptions-item>
              <a-descriptions-item label="湍流强度">
                {{ weatherData.turbulence }}
              </a-descriptions-item>
              <a-descriptions-item label="能见度">
                {{ weatherData.visibility }} km
              </a-descriptions-item>
              <a-descriptions-item label="风险等级" :span="2">
                <a-tag :color="getRiskColor(weatherData.risk)">{{ weatherData.risk }}</a-tag>
              </a-descriptions-item>
            </a-descriptions>
          </div>
          <div v-else class="no-data">
            <Empty description="请选择参数并加载数据" />
          </div>
        </a-card>
      </a-col>
      
      <!-- 右侧气象可视化 -->
      <a-col :span="16">
        <a-card title="气象热力图">
          <div id="weather-map" class="weather-map-container"></div>
        </a-card>
        
        <!-- 气象趋势图 -->
        <a-card title="气象趋势" style="margin-top: 16px">
          <div ref="chartRef" class="chart-container"></div>
        </a-card>
      </a-col>
    </a-row>
  </a-card>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { CloudOutlined } from '@ant-design/icons-vue'
import { Empty } from 'ant-design-vue'
import L from 'leaflet'
import * as echarts from 'echarts'

// 响应式数据
const formState = ref({})
const selectedTime = ref(new Date())
const selectedHeight = ref('100')
const selectedElements = ref(['wind', 'temperature', 'risk'])
const weatherData = ref(null)
const chartRef = ref(null)
let weatherMap = null
let chart = null

// 方法
const loadWeatherData = async () => {
  // 模拟API调用
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  // 模拟数据
  weatherData.value = {
    windSpeed: 5.2,
    windDirection: 135,
    temperature: 25.5,
    humidity: 65,
    turbulence: '低',
    visibility: 10,
    risk: '低'
  }
  
  // 更新地图和图表
  updateWeatherMap()
  updateChart()
}

const getRiskColor = (risk) => {
  const colorMap = {
    '低': 'green',
    '中': 'orange',
    '高': 'red'
  }
  return colorMap[risk] || 'default'
}

const initWeatherMap = () => {
  weatherMap = L.map('weather-map').setView([39.9042, 116.4074], 12)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(weatherMap)
  
  // 模拟气象热力图数据
  updateWeatherMap()
}

const updateWeatherMap = () => {
  if (!weatherMap) return
  
  // 这里可以添加真实的热力图数据
  // 模拟风场数据
  const windData = [
    { lat: 39.9, lng: 116.4, value: 4 },
    { lat: 39.91, lng: 116.41, value: 5 },
    { lat: 39.92, lng: 116.42, value: 6 },
    { lat: 39.93, lng: 116.43, value: 4 },
    { lat: 39.94, lng: 116.44, value: 3 }
  ]
  
  // 清除现有图层
  weatherMap.eachLayer(layer => {
    if (layer instanceof L.Circle) {
      weatherMap.removeLayer(layer)
    }
  })
  
  // 添加风场标记
  windData.forEach(data => {
    L.circle([data.lat, data.lng], {
      color: getWindColor(data.value),
      fillColor: getWindColor(data.value),
      fillOpacity: 0.5,
      radius: data.value * 100
    }).addTo(weatherMap).bindPopup(`风速: ${data.value} m/s`)
  })
}

const getWindColor = (speed) => {
  if (speed < 3) return '#52c41a'
  if (speed < 6) return '#faad14'
  return '#f5222d'
}

const initChart = () => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    updateChart()
  }
}

const updateChart = () => {
  if (!chart) return
  
  const option = {
    title: {
      text: '风速变化趋势'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['风速']
    },
    xAxis: {
      type: 'category',
      data: ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00']
    },
    yAxis: {
      type: 'value',
      name: '风速 (m/s)'
    },
    series: [{
      name: '风速',
      type: 'line',
      data: [3.2, 4.5, 5.1, 6.2, 5.8, 4.9, 4.2, 3.8],
      smooth: true,
      lineStyle: {
        color: '#1890ff'
      }
    }]
  }
  
  chart.setOption(option)
}

// 生命周期
onMounted(() => {
  initWeatherMap()
  initChart()
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    if (chart) {
      chart.resize()
    }
  })
})

onUnmounted(() => {
  if (weatherMap) {
    weatherMap.remove()
  }
  if (chart) {
    chart.dispose()
  }
})
</script>

<style scoped>
.weather-card {
  margin-bottom: 24px;
}

.weather-details {
  padding: 16px 0;
}

.no-data {
  padding: 40px 0;
  text-align: center;
}

.weather-map-container {
  height: 400px;
  width: 100%;
}

.chart-container {
  height: 300px;
  width: 100%;
}
</style>