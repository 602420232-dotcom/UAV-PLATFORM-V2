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
    <a-spin :spinning="store.loading.weather">
      <a-alert v-if="store.error.weather" :message="store.error.weather" type="warning" show-icon style="margin-bottom:16px" />
      <a-empty v-if="!store.loading.weather && !store.error.weather && store.windData.length === 0" description="暂无气象数据" />
      <a-row v-else :gutter="[16, 16]">
        <a-col :span="24">
          <a-table :columns="windCols" :data-source="store.windData" row-key="lat" :pagination="false" size="small" />
        </a-col>
      </a-row>
    </a-spin>
    
    <a-divider>方差场分析</a-divider>
    
    <a-row :gutter="[16, 16]">
      <a-col :span="24">
        <a-card title="方差场参数" size="small">
          <a-descriptions :column="2" size="small">
            <a-descriptions-item label="背景误差尺度">{{ varianceParams.background_error_scale?.toFixed(4) || '-' }}</a-descriptions-item>
            <a-descriptions-item label="观测误差尺度">{{ varianceParams.observation_error_scale?.toFixed(4) || '-' }}</a-descriptions-item>
            <a-descriptions-item label="相关长度尺度">{{ varianceParams.correlation_length_scale?.toFixed(4) || '-' }}</a-descriptions-item>
            <a-descriptions-item label="正则化参数">{{ varianceParams.regularization?.toFixed(6) || '-' }}</a-descriptions-item>
          </a-descriptions>
          <a-space style="margin-top: 16px">
            <a-button @click="loadVarianceParams" :loading="varianceLoading">刷新参数</a-button>
            <a-button @click="computeVarianceField" :loading="varianceLoading" type="primary">计算方差场</a-button>
          </a-space>
        </a-card>
      </a-col>
    </a-row>
    
    <a-row :gutter="[16, 16]" style="margin-top: 16px">
      <a-col :xs="24" :md="12">
        <a-card title="方差场可视化" size="small">
          <div ref="varianceChartRef" style="height: 300px"></div>
          <a-empty v-if="!varianceData.length" description="暂无方差场数据" />
        </a-card>
      </a-col>
      <a-col :xs="24" :md="12">
        <a-card title="优化历史" size="small">
          <a-table 
            :columns="optimizationCols" 
            :data-source="optimizationHistory" 
            :pagination="false"
            size="small"
            :scroll="{ y: 250 }"
          />
        </a-card>
      </a-col>
    </a-row>
    
    <a-row :gutter="[16, 16]" style="margin-top: 16px">
      <a-col :span="24">
        <a-card title="方差场配置" size="small">
          <a-form layout="inline" :model="varianceConfig">
            <a-form-item label="使用自适应">
              <a-switch v-model:checked="varianceConfig.use_adaptive" />
            </a-form-item>
            <a-form-item label="使用交叉验证">
              <a-switch v-model:checked="varianceConfig.use_cv" />
            </a-form-item>
            <a-form-item label="交叉验证折数">
              <a-input-number v-model:value="varianceConfig.n_folds" :min="2" :max="10" :disabled="!varianceConfig.use_cv" />
            </a-form-item>
            <a-form-item label="优化方法">
              <a-select v-model:value="varianceConfig.method" style="width: 120px">
                <a-select-option value="L-BFGS-B">L-BFGS-B</a-select-option>
                <a-select-option value="SLSQP">SLSQP</a-select-option>
                <a-select-option value="Powell">Powell</a-select-option>
              </a-select-option>
            </a-form-item>
            <a-form-item>
              <a-button @click="applyVarianceConfig" type="primary">应用配置</a-button>
            </a-form-item>
          </a-form>
        </a-card>
      </a-col>
    </a-row>
  </a-card>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { CloudOutlined, FireOutlined, CompassOutlined, DashboardOutlined } from '@ant-design/icons-vue'
import { getVarianceParams, setVarianceParams, computeVariance } from '../api/variance'
import { useDataStore } from '../stores/dataStore'
import { demoData } from '../utils/demoData'
import * as echarts from 'echarts'

const store = useDataStore()

const varianceLoading = ref(false)
const varianceParams = ref({})
const varianceData = ref([])
const optimizationHistory = ref([])
const varianceChartRef = ref(null)
let varianceChart = null

const varianceConfig = ref({
  use_adaptive: false,
  use_cv: false,
  n_folds: 5,
  method: 'L-BFGS-B'
})

const weatherCards = computed(() => {
  const d = store.weatherData
  return [
    { title: '风速', value: d?.windSpeed ?? '-', unit: 'm/s', icon: DashboardOutlined, color: '#1677ff' },
    { title: '风向', value: d?.windDirection ?? '-', unit: '°N', icon: CompassOutlined, color: '#52c41a' },
    { title: '温度', value: d?.temperature ?? '-', unit: '°C', icon: FireOutlined, color: '#ff4d4f' },
    { title: '湿度', value: d?.humidity ?? '-', unit: '%', icon: CloudOutlined, color: '#722ed1' },
  ]
})

const windCols = [
  { title: '纬度', dataIndex: 'lat', key: 'lat' },
  { title: '经度', dataIndex: 'lng', key: 'lng' },
  { title: '风速(m/s)', dataIndex: 'speed', key: 'speed' },
  { title: '风向(°N)', dataIndex: 'direction', key: 'direction' },
  { title: '温度(°C)', dataIndex: 'temperature', key: 'temperature' },
  { title: '湿度(%)', dataIndex: 'humidity', key: 'humidity' },
]

const optimizationCols = [
  { title: '迭代', dataIndex: 'iteration', key: 'iteration', width: 80 },
  { title: '参数', dataIndex: 'params', key: 'params', 
    customRender: ({ text }) => text ? text.map(v => v.toFixed(4)).join(', ') : '-' 
  },
  { title: '分数', dataIndex: 'score', key: 'score', 
    customRender: ({ text }) => text ? text.toFixed(6) : '-' 
  },
]

const loadVarianceParams = async () => {
  varianceLoading.value = true
  try {
    const res = await getVarianceParams()
    varianceParams.value = res.current_params || {}
  } catch (e) {
    console.error('加载方差场参数失败:', e)
  } finally {
    varianceLoading.value = false
  }
}

const applyVarianceConfig = async () => {
  varianceLoading.value = true
  try {
    await setVarianceParams(varianceConfig.value)
    await loadVarianceParams()
  } catch (e) {
    console.error('应用方差场配置失败:', e)
  } finally {
    varianceLoading.value = false
  }
}

const computeVarianceField = async () => {
  varianceLoading.value = true
  try {
    const nx = 20, ny = 20, nz = 5
    const background = Array(nx).fill(0).map(() => 
      Array(ny).fill(0).map(() => Array(nz).fill(10).map(() => Math.random() * 10))
    )
    
    const obsCount = 50
    const obsLocations = Array(obsCount).fill(0).map(() => [
      Math.floor(Math.random() * nx),
      Math.floor(Math.random() * ny),
      Math.floor(Math.random() * nz)
    ])
    
    const observations = obsLocations.map(loc => 
      background[loc[0]][loc[1]][loc[2]] + (Math.random() - 0.5) * 2
    )
    
    const res = await computeVariance({
      background,
      observations,
      obsLocations,
      ...varianceConfig.value
    })
    
    if (res.variance_field) {
      varianceData.value = res.variance_field
      optimizationHistory.value = res.optimization_history || []
      renderVarianceChart()
    }
  } catch (e) {
    console.error('计算方差场失败:', e)
  } finally {
    varianceLoading.value = false
  }
}

const renderVarianceChart = () => {
  nextTick(() => {
    if (!varianceChartRef.value || !varianceData.value.length) return
    
    if (!varianceChart) {
      varianceChart = echarts.init(varianceChartRef.value)
    }
    
    const flatData = varianceData.value.flat(Infinity)
    const gridSize = Math.sqrt(flatData.length)
    
    const option = {
      title: {
        text: '方差场分布',
        left: 'center'
      },
      tooltip: {
        formatter: (params) => `方差: ${params.value.toFixed(6)}`
      },
      visualMap: {
        min: Math.min(...flatData),
        max: Math.max(...flatData),
        calculable: true,
        orient: 'vertical',
        left: 'left',
        bottom: '20%',
        inRange: {
          color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
        }
      },
      grid: {
        left: '3%',
        right: '10%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: Array.from({ length: gridSize }, (_, i) => i),
        name: 'X'
      },
      yAxis: {
        type: 'category',
        data: Array.from({ length: gridSize }, (_, i) => i),
        name: 'Y'
      },
      series: [{
        type: 'heatmap',
        data: flatData.map((value, idx) => [
          idx % gridSize,
          Math.floor(idx / gridSize),
          value
        ]),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    }
    
    varianceChart.setOption(option)
  })
}

const handleResize = () => {
  if (varianceChart) {
    varianceChart.resize()
  }
}

onMounted(async () => {
  await store.fetchWeather()
  await loadVarianceParams()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (varianceChart) {
    varianceChart.dispose()
    varianceChart = null
  }
})
</script>
