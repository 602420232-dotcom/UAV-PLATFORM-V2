<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, shallowRef, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { weatherApi } from '@/api/weather'
import type { WeatherGrid } from '@/api/weather'
import * as echarts from 'echarts/core'
import { ScatterChart, HeatmapChart, EffectScatterChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  VisualMapComponent,
  GeoComponent,
  GridComponent,
  LegendComponent,
  ToolboxComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'

echarts.use([
  ScatterChart,
  HeatmapChart,
  EffectScatterChart,
  TitleComponent,
  TooltipComponent,
  VisualMapComponent,
  GeoComponent,
  GridComponent,
  LegendComponent,
  ToolboxComponent,
  CanvasRenderer,
])

type VisualizationMode = 'wind' | 'temperature' | 'humidity'

const loading = ref(false)
const regionLoading = ref(false)
const weatherData = ref<WeatherGrid | null>(null)
const regionData = ref<WeatherGrid[]>([])
const activeTab = ref<'point' | 'region'>('point')
const vizMode = ref<VisualizationMode>('wind')

// 单点查询表单
const queryForm = ref({
  lon: 116.4,
  lat: 39.9,
  altitude: 100,
  source: '',
  forecastTime: '',
})

// 区域查询表单
const regionForm = ref({
  minLon: 115.0,
  minLat: 39.0,
  maxLon: 118.0,
  maxLat: 41.0,
  altitude: 100,
  source: '',
  forecastTime: '',
})

// ECharts
const chartRef = ref<HTMLDivElement>()
const chartInstance = shallowRef<echarts.ECharts>()

function initChart() {
  if (!chartRef.value) return
  chartInstance.value = echarts.init(chartRef.value)
  updateChart()
}

function handleResize() {
  chartInstance.value?.resize()
}

// 风场散点图配置
function buildWindOption(data: WeatherGrid[]): EChartsOption {
  const scatterData = data.map((d) => ({
    value: [d.lon, d.lat, d.windSpeed, d.windDirection],
    name: `(${d.lon.toFixed(2)}, ${d.lat.toFixed(2)})`,
  }))

  return {
    backgroundColor: 'transparent',
    title: {
      text: '风场散点图',
      textStyle: { color: '#e0e0e0', fontSize: 14 },
      left: 10,
      top: 5,
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0' },
      formatter: (params: any) => {
        const d = params.data.value
        const dir = getWindDirectionName(d[3])
        return `<strong>${params.data.name}</strong><br/>
          风速: ${d[2].toFixed(1)} m/s<br/>
          风向: ${d[3].toFixed(0)}° (${dir})`
      },
    },
    toolbox: {
      feature: {
        dataZoom: {},
        restore: {},
        saveAsImage: {},
      },
      iconStyle: { borderColor: '#a0a0b0' },
    },
    grid: {
      left: '3%',
      right: '12%',
      bottom: '3%',
      top: 50,
      containLabel: true,
    },
    xAxis: {
      type: 'value',
      name: '经度',
      nameTextStyle: { color: '#a0a0b0' },
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0' },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    yAxis: {
      type: 'value',
      name: '纬度',
      nameTextStyle: { color: '#a0a0b0' },
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0' },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    visualMap: {
      min: 0,
      max: 20,
      calculable: true,
      orient: 'vertical',
      right: 10,
      top: 'center',
      text: ['高 (m/s)', '低'],
      textStyle: { color: '#a0a0b0' },
      inRange: {
        color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026'],
      },
    },
    series: [
      {
        name: '风速',
        type: 'scatter',
        symbolSize: (val: number[]) => Math.max(8, (val[2] ?? 0) * 2),
        data: scatterData,
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)',
        },
        emphasis: {
          itemStyle: { shadowBlur: 20, shadowColor: 'rgba(0, 0, 0, 0.8)' },
        },
      },
    ],
  }
}

// 温度场热力图配置
function buildTemperatureOption(data: WeatherGrid[]): EChartsOption {
  // 将数据聚合为热力图格式 [lon, lat, value]
  const heatData = data.map((d) => [d.lon, d.lat, d.temperature])

  return {
    backgroundColor: 'transparent',
    title: {
      text: '温度场热力图',
      textStyle: { color: '#e0e0e0', fontSize: 14 },
      left: 10,
      top: 5,
    },
    tooltip: {
      position: 'top',
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0' },
      formatter: (params: any) => {
        return `经度: ${params.data[0].toFixed(2)}<br/>纬度: ${params.data[1].toFixed(2)}<br/>温度: ${params.data[2].toFixed(1)} °C`
      },
    },
    toolbox: {
      feature: {
        dataZoom: {},
        restore: {},
        saveAsImage: {},
      },
      iconStyle: { borderColor: '#a0a0b0' },
    },
    grid: {
      left: '3%',
      right: '12%',
      bottom: '3%',
      top: 50,
      containLabel: true,
    },
    xAxis: {
      type: 'value',
      name: '经度',
      nameTextStyle: { color: '#a0a0b0' },
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0' },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    yAxis: {
      type: 'value',
      name: '纬度',
      nameTextStyle: { color: '#a0a0b0' },
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0' },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    visualMap: {
      min: -20,
      max: 45,
      calculable: true,
      orient: 'vertical',
      right: 10,
      top: 'center',
      text: ['高温 (°C)', '低温'],
      textStyle: { color: '#a0a0b0' },
      inRange: {
        color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026'],
      },
    },
    series: [
      {
        name: '温度',
        type: 'heatmap',
        data: heatData,
        label: {
          show: false,
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      },
    ],
  }
}

// 湿度场配置
function buildHumidityOption(data: WeatherGrid[]): EChartsOption {
  const scatterData = data.map((d) => ({
    value: [d.lon, d.lat, d.humidity],
    name: `(${d.lon.toFixed(2)}, ${d.lat.toFixed(2)})`,
  }))

  return {
    backgroundColor: 'transparent',
    title: {
      text: '湿度分布图',
      textStyle: { color: '#e0e0e0', fontSize: 14 },
      left: 10,
      top: 5,
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0' },
      formatter: (params: any) => {
        const d = params.data.value
        return `<strong>${params.data.name}</strong><br/>湿度: ${d[2].toFixed(1)} %`
      },
    },
    toolbox: {
      feature: {
        dataZoom: {},
        restore: {},
        saveAsImage: {},
      },
      iconStyle: { borderColor: '#a0a0b0' },
    },
    grid: {
      left: '3%',
      right: '12%',
      bottom: '3%',
      top: 50,
      containLabel: true,
    },
    xAxis: {
      type: 'value',
      name: '经度',
      nameTextStyle: { color: '#a0a0b0' },
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0' },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    yAxis: {
      type: 'value',
      name: '纬度',
      nameTextStyle: { color: '#a0a0b0' },
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0' },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    visualMap: {
      min: 0,
      max: 100,
      calculable: true,
      orient: 'vertical',
      right: 10,
      top: 'center',
      text: ['高 (%)', '低'],
      textStyle: { color: '#a0a0b0' },
      inRange: {
        color: ['#f7fbff', '#c6dbef', '#6baed6', '#2171b5', '#08306b'],
      },
    },
    series: [
      {
        name: '湿度',
        type: 'effectScatter',
        symbolSize: (val: number[]) => Math.max(6, (val[2] ?? 0) / 5),
        data: scatterData,
        rippleEffect: { brushType: 'stroke' },
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.3)',
        },
      },
    ],
  }
}

function updateChart() {
  if (!chartInstance.value) return
  const data = regionData.value
  if (data.length === 0) {
    // 空状态
    chartInstance.value.setOption({
      backgroundColor: 'transparent',
      title: {
        text: '气象数据可视化',
        textStyle: { color: '#e0e0e0', fontSize: 14 },
        left: 'center',
        top: 'middle',
      },
    } as EChartsOption, true)
    return
  }

  let option: EChartsOption
  switch (vizMode.value) {
    case 'wind':
      option = buildWindOption(data)
      break
    case 'temperature':
      option = buildTemperatureOption(data)
      break
    case 'humidity':
      option = buildHumidityOption(data)
      break
    default:
      option = buildWindOption(data)
  }
  chartInstance.value.setOption(option, true)
}

watch(vizMode, () => {
  updateChart()
})

watch(regionData, () => {
  nextTick(() => updateChart())
}, { deep: true })

async function queryPoint() {
  loading.value = true
  try {
    weatherData.value = await weatherApi.queryPoint({
      lon: queryForm.value.lon,
      lat: queryForm.value.lat,
      altitude: queryForm.value.altitude || undefined,
      source: queryForm.value.source || undefined,
      forecastTime: queryForm.value.forecastTime || undefined,
    })
    ElMessage.success('查询成功')
  } catch {
    // 错误已在拦截器中处理
  } finally {
    loading.value = false
  }
}

async function queryRegion() {
  regionLoading.value = true
  try {
    regionData.value = await weatherApi.queryRegion({
      minLon: regionForm.value.minLon,
      minLat: regionForm.value.minLat,
      maxLon: regionForm.value.maxLon,
      maxLat: regionForm.value.maxLat,
      altitude: regionForm.value.altitude || undefined,
      source: regionForm.value.source || undefined,
      forecastTime: regionForm.value.forecastTime || undefined,
    })
    ElMessage.success(`查询成功，获取 ${regionData.value.length} 个格点数据`)
    nextTick(() => updateChart())
  } catch {
    // 错误已在拦截器中处理
  } finally {
    regionLoading.value = false
  }
}

function formatSpeed(speed: number): string {
  return `${speed.toFixed(1)} m/s`
}

function formatDirection(dir: number): string {
  const directions = ['北', '东北', '东', '东南', '南', '西南', '西', '西北']
  const index = Math.round(dir / 45) % 8
  return `${dir.toFixed(0)}° (${directions[index]})`
}

function getWindDirectionName(dir: number): string {
  const directions = ['北', '东北', '东', '东南', '南', '西南', '西', '西北']
  const index = Math.round(dir / 45) % 8
  return directions[index] ?? '北'
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance.value?.dispose()
})
</script>

<template>
  <div class="weather-page">
    <div class="page-header">
      <h2>气象数据</h2>
      <div class="viz-mode-switch">
        <el-radio-group v-model="vizMode" size="small">
          <el-radio-button value="wind">风场</el-radio-button>
          <el-radio-button value="temperature">温度</el-radio-button>
          <el-radio-button value="humidity">湿度</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div class="content-grid">
      <!-- ECharts 可视化区域 -->
      <el-card class="map-card">
        <template #header>
          <span>气象可视化</span>
        </template>
        <div ref="chartRef" class="chart-container" />
        <div v-if="regionData.length === 0" class="chart-empty">
          <el-icon :size="48" color="#0f3460"><MapLocation /></el-icon>
          <p>请使用区域查询获取气象数据后查看可视化</p>
        </div>
      </el-card>

      <!-- 查询面板 -->
      <el-card class="query-card">
        <template #header>
          <el-tabs v-model="activeTab" class="query-tabs">
            <el-tab-pane label="单点查询" name="point" />
            <el-tab-pane label="区域查询" name="region" />
          </el-tabs>
        </template>

        <!-- 单点查询表单 -->
        <el-form v-if="activeTab === 'point'" label-width="80px">
          <el-form-item label="经度">
            <el-input-number v-model="queryForm.lon" :precision="4" :step="0.1" :min="-180" :max="180" style="width: 100%" />
          </el-form-item>
          <el-form-item label="纬度">
            <el-input-number v-model="queryForm.lat" :precision="4" :step="0.1" :min="-90" :max="90" style="width: 100%" />
          </el-form-item>
          <el-form-item label="高度(m)">
            <el-input-number v-model="queryForm.altitude" :step="100" :min="0" :max="20000" style="width: 100%" />
          </el-form-item>
          <el-form-item label="数据源">
            <el-input v-model="queryForm.source" placeholder="如: GFS, ERA5（可选）" />
          </el-form-item>
          <el-form-item label="预报时间">
            <el-input v-model="queryForm.forecastTime" placeholder="ISO 时间格式（可选）" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loading" @click="queryPoint">
              查询
            </el-button>
          </el-form-item>
        </el-form>

        <!-- 区域查询表单 -->
        <el-form v-if="activeTab === 'region'" label-width="80px">
          <el-divider content-position="left">矩形范围</el-divider>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="最小经度">
                <el-input-number v-model="regionForm.minLon" :precision="2" :step="0.5" :min="-180" :max="180" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="最小纬度">
                <el-input-number v-model="regionForm.minLat" :precision="2" :step="0.5" :min="-90" :max="90" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="最大经度">
                <el-input-number v-model="regionForm.maxLon" :precision="2" :step="0.5" :min="-180" :max="180" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="最大纬度">
                <el-input-number v-model="regionForm.maxLat" :precision="2" :step="0.5" :min="-90" :max="90" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-divider content-position="left">其他参数</el-divider>
          <el-form-item label="高度(m)">
            <el-input-number v-model="regionForm.altitude" :step="100" :min="0" :max="20000" style="width: 100%" />
          </el-form-item>
          <el-form-item label="数据源">
            <el-input v-model="regionForm.source" placeholder="如: GFS, ERA5（可选）" />
          </el-form-item>
          <el-form-item label="预报时间">
            <el-input v-model="regionForm.forecastTime" placeholder="ISO 时间格式（可选）" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="regionLoading" @click="queryRegion">
              查询区域
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <!-- 单点查询结果 -->
      <el-card v-if="weatherData" class="result-card">
        <template #header>
          <span>单点查询结果</span>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="位置">
            {{ weatherData.lon.toFixed(4) }}, {{ weatherData.lat.toFixed(4) }}
          </el-descriptions-item>
          <el-descriptions-item label="高度">{{ weatherData.altitude }} m</el-descriptions-item>
          <el-descriptions-item label="风速">{{ formatSpeed(weatherData.windSpeed) }}</el-descriptions-item>
          <el-descriptions-item label="风向">{{ formatDirection(weatherData.windDirection) }}</el-descriptions-item>
          <el-descriptions-item label="温度">{{ weatherData.temperature.toFixed(1) }} °C</el-descriptions-item>
          <el-descriptions-item label="湿度">{{ weatherData.humidity.toFixed(1) }} %</el-descriptions-item>
          <el-descriptions-item label="气压">{{ weatherData.pressure.toFixed(0) }} hPa</el-descriptions-item>
          <el-descriptions-item label="能见度">{{ weatherData.visibility.toFixed(1) }} km</el-descriptions-item>
          <el-descriptions-item label="天气代码">{{ weatherData.weatherCode }}</el-descriptions-item>
          <el-descriptions-item label="数据源">{{ weatherData.source }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 区域查询统计 -->
      <el-card v-if="regionData.length > 0" class="result-card">
        <template #header>
          <span>区域数据统计 ({{ regionData.length }} 个格点)</span>
        </template>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="温度范围">
            {{ Math.min(...regionData.map(d => d.temperature)).toFixed(1) }} ~ {{ Math.max(...regionData.map(d => d.temperature)).toFixed(1) }} °C
          </el-descriptions-item>
          <el-descriptions-item label="平均温度">
            {{ (regionData.reduce((s, d) => s + d.temperature, 0) / regionData.length).toFixed(1) }} °C
          </el-descriptions-item>
          <el-descriptions-item label="最大风速">
            {{ Math.max(...regionData.map(d => d.windSpeed)).toFixed(1) }} m/s
          </el-descriptions-item>
          <el-descriptions-item label="平均风速">
            {{ (regionData.reduce((s, d) => s + d.windSpeed, 0) / regionData.length).toFixed(1) }} m/s
          </el-descriptions-item>
          <el-descriptions-item label="湿度范围">
            {{ Math.min(...regionData.map(d => d.humidity)).toFixed(1) }} ~ {{ Math.max(...regionData.map(d => d.humidity)).toFixed(1) }} %
          </el-descriptions-item>
          <el-descriptions-item label="平均气压">
            {{ (regionData.reduce((s, d) => s + d.pressure, 0) / regionData.length).toFixed(0) }} hPa
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.weather-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  grid-template-rows: auto auto;
  gap: 16px;
}

.map-card {
  grid-column: 1;
  grid-row: 1 / 3;
  border-radius: 8px;
  min-height: 500px;
}

.chart-container {
  width: 100%;
  height: 460px;
}

.chart-empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--color-text-muted);
  pointer-events: none;
}

.map-card :deep(.el-card__body) {
  position: relative;
}

.query-tabs {
  margin-bottom: -18px;
}

.query-card,
.result-card {
  border-radius: 8px;
}
</style>
