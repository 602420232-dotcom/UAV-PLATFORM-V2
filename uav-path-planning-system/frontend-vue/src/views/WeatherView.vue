<template>
  <a-card title="气象服务">
    <a-row :gutter="[16, 16]">
      <a-col :xs="24" :sm="12" :md="6" v-for="item in weatherCards" :key="item.title">
        <a-card size="small">
          <a-statistic :title="item.title" :value="item.value" :suffix="item.unit">
            <template #prefix><component :is="item.icon" :style="{ color: item.color }" /></template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>
    <a-divider />
    <a-spin :spinning="loading">
      <a-alert v-if="error" :message="error" type="warning" show-icon style="margin-bottom:16px" />
      <a-empty v-if="!loading && !error && windData.length === 0" description="暂无气象数据" />
      <a-row v-else :gutter="[16, 16]">
        <a-col :span="24">
          <a-table :columns="windCols" :data-source="windData" row-key="lat" :pagination="false" size="small" />
        </a-col>
      </a-row>
    </a-spin>
  </a-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { CloudOutlined, FireOutlined, CompassOutlined, DashboardOutlined } from '@ant-design/icons-vue'
import { getWeatherCurrent } from '../api/weather'

const loading = ref(false)
const error = ref('')
const weatherCards = ref([])
const windData = ref([])

const windCols = [
  { title: '纬度', dataIndex: 'lat', key: 'lat' },
  { title: '经度', dataIndex: 'lng', key: 'lng' },
  { title: '风速(m/s)', dataIndex: 'speed', key: 'speed' },
  { title: '风向(°N)', dataIndex: 'direction', key: 'direction' },
  { title: '温度(°C)', dataIndex: 'temperature', key: 'temperature' },
  { title: '湿度(%)', dataIndex: 'humidity', key: 'humidity' },
]

const loadWeather = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await getWeatherCurrent(39.9, 116.4)
    const d = res.data || res
    if (d) {
      weatherCards.value = [
        { title: '风速', value: d.windSpeed ?? '-', unit: 'm/s', icon: DashboardOutlined, color: '#1677ff' },
        { title: '风向', value: d.windDirection ?? '-', unit: '°N', icon: CompassOutlined, color: '#52c41a' },
        { title: '温度', value: d.temperature ?? '-', unit: '°C', icon: FireOutlined, color: '#ff4d4f' },
        { title: '湿度', value: d.humidity ?? '-', unit: '%', icon: CloudOutlined, color: '#722ed1' },
      ]
      if (d.windField) {
        windData.value = Array.isArray(d.windField) ? d.windField : []
      }
    }
  } catch (e) {
    // 后端未连接或需要认证时，静默处理
    if (e.message !== 'BACKEND_UNAVAILABLE' && e.message !== 'AUTH_REQUIRED') {
      error.value = '气象服务未连接，请确认后端已启动'
    }
  } finally {
    loading.value = false
  }
}

onMounted(loadWeather)
</script>
