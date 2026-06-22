<template>
  <div class="wrf-terrain-analysis">
    <div class="section-header">
      <h2 class="section-title">WRF 地形分析可视化</h2>
      <el-tag type="info" effect="plain" size="small">需要远程WRF服务器支持</el-tag>
    </div>

    <!-- 预览模式提示 -->
    <el-alert
      v-if="previewMode"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 16px"
    >
      <template #title>
        当前为预览模式，使用示例数据展示。连接WRF服务器后可获取实时分析结果。
      </template>
    </el-alert>

    <!-- 顶部统计卡片 -->
    <el-row :gutter="16" class="stat-cards">
      <el-col :span="6" v-for="card in statCards" :key="card.label">
        <div class="stat-card">
          <div class="stat-card__label">{{ card.label }}</div>
          <div class="stat-card__value" :style="{ color: card.color }">{{ card.value }}</div>
          <div class="stat-card__desc">{{ card.desc }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 地形分类热力图 -->
    <el-card shadow="never" class="chart-card">
      <template #header>
        <div class="card-header">
          <span>地形分类热力图 — 四川盆地 (27-35°N, 102-110°E)</span>
          <el-radio-group v-model="terrainLayer" size="small">
            <el-radio-button value="elevation">高程</el-radio-button>
            <el-radio-button value="slope">坡度</el-radio-button>
            <el-radio-button value="roughness">粗糙度</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div ref="heatmapRef" class="chart-container" style="height: 420px"></div>
    </el-card>

    <!-- 山谷风环流分析 -->
    <el-card shadow="never" class="chart-card">
      <template #header>
        <div class="card-header">
          <span>山谷风环流分析</span>
          <div class="card-header__controls">
            <el-time-select
              v-model="windTime"
              :start="'00:00'"
              :step="'01:00'"
              :end="'23:00'"
              placeholder="选择时间"
              size="small"
              style="width: 120px; margin-right: 12px"
            />
            <div class="wind-threshold">
              <span class="threshold-label">风速阈值:</span>
              <el-slider
                v-model="windThreshold"
                :min="0"
                :max="20"
                :step="0.5"
                :format-tooltip="(v: number) => v + ' m/s'"
                style="width: 160px"
              />
            </div>
          </div>
        </div>
      </template>
      <div ref="windChartRef" class="chart-container" style="height: 400px"></div>
    </el-card>

    <!-- 地形通道效应表格 -->
    <el-card shadow="never" class="chart-card">
      <template #header>
        <span>地形通道效应</span>
      </template>
      <el-table :data="terrainPassages" stripe style="width: 100%">
        <el-table-column prop="name" label="通道名称" width="160" />
        <el-table-column prop="location" label="地理位置" width="200" />
        <el-table-column prop="direction" label="主导风向" width="120" />
        <el-table-column prop="width" label="通道宽度(km)" width="130">
          <template #default="{ row }">{{ row.width }}</template>
        </el-table-column>
        <el-table-column prop="elevation" label="缺口高程(m)" width="130">
          <template #default="{ row }">{{ row.elevation }}</template>
        </el-table-column>
        <el-table-column prop="effect" label="通道效应">
          <template #default="{ row }">
            <el-progress
              :percentage="row.effect"
              :color="getEffectColor(row.effect)"
              :stroke-width="14"
              :text-inside="true"
            />
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip />
      </el-table>
    </el-card>

    <!-- PBL方案对比 -->
    <el-card shadow="never" class="chart-card">
      <template #header>
        <span>PBL 方案对比</span>
      </template>
      <PBLSchemeSelector
        v-model:selected-pbl="selectedPblScheme"
        v-model:selected-cumulus="selectedCumulusScheme"
        v-model:selected-micro="selectedMicroScheme"
        v-model:selected-radiation="selectedRadiationScheme"
        v-model:selected-lsm="selectedLsmScheme"
      />
    </el-card>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, shallowRef } from 'vue'
import * as echarts from 'echarts/core'
import { HeatmapChart, ScatterChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  VisualMapComponent,
  ToolboxComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'
import PBLSchemeSelector from './PBLSchemeSelector.vue'

echarts.use([
  HeatmapChart,
  ScatterChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  VisualMapComponent,
  ToolboxComponent,
  LegendComponent,
  CanvasRenderer,
])

// ---- 预览模式 ----
const previewMode = ref(true)

// ---- 统计卡片 ----
const statCards = ref([
  { label: '盆地高程范围', value: '300 ~ 700m', desc: '最低点: 重庆 200m / 最高点: 成都平原 750m', color: 'var(--color-primary)' },
  { label: '平均坡度', value: '8.5°', desc: '盆地西部陡峭，东部平缓', color: 'var(--color-success)' },
  { label: '地形粗糙度', value: '0.85m', desc: '混合农田与丘陵地形', color: 'var(--color-warning)' },
  { label: '山脊/山谷比例', value: '1 : 2.3', desc: '山谷面积占比约70%', color: 'var(--color-danger)' },
])

// ---- 地形热力图 ----
const terrainLayer = ref('elevation')
const heatmapRef = ref<HTMLDivElement>()
const heatmapChart = shallowRef<echarts.ECharts>()

function generateTerrainData(): number[][] {
  const data: number[][] = []
  for (let lat = 27; lat <= 35; lat += 0.5) {
    for (let lon = 102; lon <= 110; lon += 0.5) {
      let value = 0
      if (terrainLayer.value === 'elevation') {
        // 模拟四川盆地高程：中心低四周高
        const centerLat = 30.5, centerLon = 106
        const dist = Math.sqrt((lat - centerLat) ** 2 + (lon - centerLon) ** 2)
        value = 400 + dist * 350 + Math.random() * 100
        if (lat > 33) value += 800 // 秦岭
        if (lon < 104 && lat > 31) value += 600 // 龙门山
      } else if (terrainLayer.value === 'slope') {
        value = 2 + Math.random() * 15
        if (lat > 33 || lon < 104) value += 10
      } else {
        value = 0.3 + Math.random() * 1.2
      }
      data.push([lon, lat, Math.round(value * 10) / 10])
    }
  }
  return data
}

function initHeatmap() {
  if (!heatmapRef.value) return
  heatmapChart.value = echarts.init(heatmapRef.value)
  updateHeatmap()
}

function updateHeatmap() {
  if (!heatmapChart.value) return
  const data = generateTerrainData()
  const layerNames: Record<string, string> = {
    elevation: '高程 (m)',
    slope: '坡度 (°)',
    roughness: '粗糙度 (m)',
  }
  const option: EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      position: 'top',
      backgroundColor: 'rgba(15, 15, 30, 0.9)',
      borderColor: 'var(--color-border)',
      textStyle: { color: '#e0e0e0' },
      formatter: (params: any) => {
        const p = params.data
        return `${p[0]}°E, ${p[1]}°N<br/>${layerNames[terrainLayer.value]}: ${p[2]}`
      },
    },
    grid: { left: 60, right: 40, top: 20, bottom: 60 },
    xAxis: {
      type: 'value',
      min: 102, max: 110,
      name: '经度 (°E)',
      nameTextStyle: { color: '#a0a0b0' },
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0' },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    yAxis: {
      type: 'value',
      min: 27, max: 35,
      name: '纬度 (°N)',
      nameTextStyle: { color: '#a0a0b0' },
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0' },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    visualMap: {
      min: terrainLayer.value === 'elevation' ? 200 : terrainLayer.value === 'slope' ? 0 : 0,
      max: terrainLayer.value === 'elevation' ? 2000 : terrainLayer.value === 'slope' ? 30 : 2,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      inRange: {
        color: terrainLayer.value === 'elevation'
          ? ['#0d4a2e', '#1a7a4c', '#4caf50', '#ffeb3b', '#ff9800', '#f44336']
          : ['#1a237e', '#1565c0', '#00acc1', '#26a69a', '#9ccc65', '#ffee58'],
      },
      textStyle: { color: '#a0a0b0' },
    },
    series: [{
      type: 'heatmap',
      data: data,
      label: { show: false },
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' },
      },
    }],
  }
  heatmapChart.value.setOption(option, true)
}

watch(terrainLayer, updateHeatmap)

// ---- 山谷风环流分析 ----
const windTime = ref('14:00')
const windThreshold = ref(3)
const windChartRef = ref<HTMLDivElement>()
const windChart = shallowRef<echarts.ECharts>()

function generateWindData() {
  const scatterData: number[][] = []
  const vectorData: number[][] = []
  const hour = parseInt(windTime.value.split(':')[0] ?? '0')
  const isDaytime = hour >= 6 && hour <= 18

  for (let lat = 28; lat <= 33; lat += 0.8) {
    for (let lon = 103; lon <= 109; lon += 0.8) {
      const centerLat = 30.5, centerLon = 106
      const dx = lon - centerLon
      const dy = lat - centerLat
      const dist = Math.sqrt(dx * dx + dy * dy)

      // 山谷风：白天吹向山顶(向外)，夜间吹向谷底(向内)
      const baseSpeed = 2 + Math.random() * 6
      const direction = isDaytime ? 1 : -1
      const u = (dx / (dist || 1)) * baseSpeed * direction + (Math.random() - 0.5) * 2
      const v = (dy / (dist || 1)) * baseSpeed * direction + (Math.random() - 0.5) * 2
      const speed = Math.sqrt(u * u + v * v)

      if (speed >= windThreshold.value) {
        scatterData.push([lon, lat, speed])
        vectorData.push([lon, lat, u * 0.15, v * 0.15])
      }
    }
  }
  return { scatterData, vectorData }
}

function initWindChart() {
  if (!windChartRef.value) return
  windChart.value = echarts.init(windChartRef.value)
  updateWindChart()
}

function updateWindChart() {
  if (!windChart.value) return
  const { scatterData, vectorData } = generateWindData()
  const option: EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: 'rgba(15, 15, 30, 0.9)',
      borderColor: 'var(--color-border)',
      textStyle: { color: '#e0e0e0' },
      formatter: (params: any) => {
        if (params.seriesType === 'scatter') {
          return `${params.data[0]}°E, ${params.data[1]}°N<br/>风速: ${params.data[2].toFixed(1)} m/s`
        }
        return ''
      },
    },
    grid: { left: 60, right: 40, top: 20, bottom: 40 },
    xAxis: {
      type: 'value', min: 103, max: 109,
      name: '经度 (°E)',
      nameTextStyle: { color: '#a0a0b0' },
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0' },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    yAxis: {
      type: 'value', min: 28, max: 33,
      name: '纬度 (°N)',
      nameTextStyle: { color: '#a0a0b0' },
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0' },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    visualMap: {
      min: 0, max: 10,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      inRange: { color: ['#1a237e', '#1565c0', '#00bcd4', '#4caf50', '#ffeb3b', '#ff5722'] },
      textStyle: { color: '#a0a0b0' },
      text: ['高风速', '低风速'],
    },
    series: [
      {
        type: 'scatter',
        data: scatterData,
        symbolSize: (val: number[]) => Math.max(4, (val[2] ?? 0) * 2.5),
        itemStyle: { opacity: 0.7 },
      },
      {
        type: 'scatter',
        data: vectorData,
        symbol: 'arrow',
        symbolSize: 8,
        itemStyle: { color: '#e0e0e0', opacity: 0.5 },
        silent: true,
      },
    ],
  }
  windChart.value.setOption(option, true)
}

watch([windTime, windThreshold], updateWindChart)

// ---- 地形通道效应 ----
const terrainPassages = ref([
  {
    name: '秦岭缺口',
    location: '34°N, 106-108°E',
    direction: 'NE-SW',
    width: 85,
    elevation: 1500,
    effect: 92,
    description: '冷空气南下的主要通道，冬季强偏北风通过此处进入四川盆地',
  },
  {
    name: '大巴山缺口',
    location: '32°N, 108-109°E',
    direction: 'NW-SE',
    width: 60,
    elevation: 1200,
    effect: 78,
    description: '东南暖湿气流进入盆地的次要通道，影响盆地东部降水分布',
  },
  {
    name: '长江三峡',
    location: '30.5°N, 110°E',
    direction: 'W-E',
    width: 200,
    elevation: 150,
    effect: 95,
    description: '盆地最重要的水汽通道，东西向贯穿，对盆地湿度调节起关键作用',
  },
  {
    name: '龙门山通道',
    location: '31°N, 103-104°E',
    direction: 'N-S',
    width: 45,
    elevation: 2000,
    effect: 65,
    description: '盆地西部地形陡变带，山谷风效应显著，局地环流复杂',
  },
  {
    name: '峨眉山-瓦屋山',
    location: '29.5°N, 103°E',
    direction: 'NW-SE',
    width: 35,
    elevation: 1800,
    effect: 55,
    description: '盆地西南部地形屏障，影响攀西地区暖湿气流输送',
  },
])

function getEffectColor(effect: number): string {
  if (effect >= 90) return 'var(--color-danger)'
  if (effect >= 70) return 'var(--color-warning)'
  return 'var(--color-success)'
}

// ---- PBL方案 ----
const selectedPblScheme = ref('YSU')
const selectedCumulusScheme = ref('Kain-Fritsch')
const selectedMicroScheme = ref('Thompson')
const selectedRadiationScheme = ref('RRTMG')
const selectedLsmScheme = ref('Noah')

// ---- 生命周期 ----
function handleResize() {
  heatmapChart.value?.resize()
  windChart.value?.resize()
}

onMounted(() => {
  initHeatmap()
  initWindChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  heatmapChart.value?.dispose()
  windChart.value?.dispose()
})
</script>

<style scoped>
.wrf-terrain-analysis {
  padding: 20px;
  background: var(--color-bg-primary, #0d0d1a);
  min-height: 100vh;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary, #e0e0e0);
  margin: 0;
}

.stat-cards {
  margin-bottom: 20px;
}

.stat-card {
  background: var(--color-bg-card, #1a1a2e);
  border: 1px solid var(--color-border, #2a2a40);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.stat-card__label {
  font-size: 13px;
  color: var(--color-text-secondary, #a0a0b0);
  margin-bottom: 8px;
}

.stat-card__value {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 6px;
}

.stat-card__desc {
  font-size: 12px;
  color: var(--color-text-muted, #6a6a80);
}

.chart-card {
  margin-bottom: 20px;
  background: var(--color-bg-card, #1a1a2e);
  border-color: var(--color-border, #2a2a40);
}

.chart-card :deep(.el-card__header) {
  border-bottom-color: var(--color-border, #2a2a40);
  color: var(--color-text-primary, #e0e0e0);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header__controls {
  display: flex;
  align-items: center;
}

.wind-threshold {
  display: flex;
  align-items: center;
}

.threshold-label {
  font-size: 13px;
  color: var(--color-text-secondary, #a0a0b0);
  margin-right: 8px;
  white-space: nowrap;
}

.chart-container {
  width: 100%;
}

</style>
