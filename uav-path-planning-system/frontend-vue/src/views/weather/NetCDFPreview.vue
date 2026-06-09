<template>
  <div class="netcdf-preview">
    <el-card shadow="never" class="header-card">
      <div class="header-inner">
        <span class="page-title">NetCDF 剖面预览（后端解析）</span>
        <el-alert
          v-if="!payload"
          title="当前处于演示模式：左侧上传文件后自动渲染图表；也可点击下方『加载演示数据』直接预览"
          type="info"
          show-icon
          :closable="false"
          class="demo-alert"
        />
        <el-alert
          v-else
          :title="'已加载文件：' + payload.fileName + '（' + formatBytes(payload.fileSize) + '）'"
          type="success"
          show-icon
          :closable="false"
          class="demo-alert"
        />
      </div>
    </el-card>

    <el-row :gutter="16" class="main-row">
      <el-col :span="10" class="left-col">
        <NetCDFChunkUploader
          @success="onUploadSuccess"
          @progress="onUploadProgress"
          @error="onUploadError"
        />
      </el-col>

      <el-col :span="14" class="right-col">
        <el-card shadow="hover" class="preview-card" v-if="!payload && !loading">
          <div class="empty-wrap">
            <el-empty description="请在左侧上传 NetCDF 文件">
              <el-button type="primary" @click="loadDemoData">加载演示数据</el-button>
            </el-empty>
          </div>
        </el-card>

        <el-card shadow="hover" class="preview-card" v-else-if="loading">
          <el-skeleton :rows="6" animated />
          <el-skeleton style="margin-top: 16px" :rows="4" animated />
        </el-card>

        <el-card shadow="hover" class="preview-card" v-else>
          <el-tabs v-model="activeTab" class="preview-tabs">
            <el-tab-pane label="2D 水平剖面" name="2d">
              <div class="tab-toolbar">
                <span class="tool-label">高度层：{{ payload.levelNames[levelIndex] }}</span>
                <el-slider
                  v-model="levelIndex"
                  :min="0"
                  :max="(payload.dims?.level || 1) - 1"
                  :marks="levelMarks"
                  show-stops
                  class="level-slider"
                />
              </div>
              <div ref="heatmapRef" class="chart-box"></div>
            </el-tab-pane>

            <el-tab-pane label="3D 垂直剖面" name="3d">
              <div class="tab-toolbar">
                <span class="tool-label">沿经度方向的温度垂直剖面（高度 vs 经度，颜色 = 温度 °C）</span>
              </div>
              <div ref="surfaceRef" class="chart-box"></div>
            </el-tab-pane>

            <el-tab-pane label="原始信息" name="raw">
              <div class="raw-info">
                <el-descriptions :column="2" border title="文件与维度">
                  <el-descriptions-item label="文件名"><code>{{ payload.fileName }}</code></el-descriptions-item>
                  <el-descriptions-item label="大小">{{ formatBytes(payload.fileSize) }}</el-descriptions-item>
                  <el-descriptions-item label="时间步">{{ payload.dims.time }}</el-descriptions-item>
                  <el-descriptions-item label="高度层">{{ payload.dims.level }}</el-descriptions-item>
                  <el-descriptions-item label="纬度">{{ payload.dims.lat }}</el-descriptions-item>
                  <el-descriptions-item label="经度">{{ payload.dims.lon }}</el-descriptions-item>
                </el-descriptions>

                <el-descriptions :column="3" border title="变量列表" style="margin-top: 16px">
                  <el-descriptions-item v-for="v in payload.vars" :key="v" :label="v">
                    <el-tag size="small" type="primary">{{ v }}</el-tag>
                  </el-descriptions-item>
                </el-descriptions>

                <el-descriptions :column="2" border title="网格坐标（范围）" style="margin-top: 16px">
                  <el-descriptions-item label="纬度">
                    {{ payload.grid.lat[0] }} ~ {{ payload.grid.lat[payload.grid.lat.length - 1] }}
                  </el-descriptions-item>
                  <el-descriptions-item label="经度">
                    {{ payload.grid.lon[0] }} ~ {{ payload.grid.lon[payload.grid.lon.length - 1] }}
                  </el-descriptions-item>
                  <el-descriptions-item label="高度层" :span="2">
                    <el-tag v-for="(n, i) in payload.levelNames" :key="n" size="small" effect="plain" style="margin-right: 6px">{{ n }}</el-tag>
                  </el-descriptions-item>
                </el-descriptions>

                <pre class="json-preview">{{ snippet }}</pre>
              </div>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import NetCDFChunkUploader from '../components/shared/NetCDFChunkUploader.vue'

const payload = ref(null)
const loading = ref(false)
const activeTab = ref('2d')
const levelIndex = ref(0)

const heatmapRef = ref(null)
const surfaceRef = ref(null)

let heatmapChart = null
let surfaceChart = null

const levelMarks = computed(() => {
  if (!payload.value) return {}
  const marks = {}
  const names = payload.value.levelNames || []
  names.forEach((n, i) => {
    if (i === 0 || i === names.length - 1 || i % 2 === 0) {
      marks[i] = n
    }
  })
  return marks
})

const snippet = computed(() => {
  if (!payload.value) return ''
  const sample = {
    temperature: {
      shape: [payload.value.dims.level, payload.value.dims.lat, payload.value.dims.lon],
      sample_0_0: payload.value.temperature[0][0].slice(0, 5)
    }
  }
  return JSON.stringify(sample, null, 2)
})

function formatBytes(b) {
  if (!b) return '0 B'
  if (b < 1024) return b + ' B'
  if (b < 1024 * 1024) return (b / 1024).toFixed(2) + ' KB'
  if (b < 1024 * 1024 * 1024) return (b / 1024 / 1024).toFixed(2) + ' MB'
  return (b / 1024 / 1024 / 1024).toFixed(2) + ' GB'
}

function onUploadSuccess(p) {
  loading.value = true
  setTimeout(() => {
    payload.value = p
    levelIndex.value = 0
    loading.value = false
    nextTick(() => renderAll())
  }, 300)
}

function onUploadProgress() {}
function onUploadError(msg) {}

function loadDemoData() {
  loading.value = true
  setTimeout(() => {
    const latN = 30
    const lonN = 40
    const levelN = 10
    const lats = []
    const lons = []
    const levels = []
    const levelNames = []
    for (let i = 0; i < latN; i++) lats.push(+(20 + 25 * i / (latN - 1)).toFixed(3))
    for (let j = 0; j < lonN; j++) lons.push(+(110 + 20 * j / (lonN - 1)).toFixed(3))
    const bases = [1000, 950, 900, 850, 800, 700, 600, 500, 400, 300]
    for (let k = 0; k < levelN; k++) {
      levels.push(bases[k])
      levelNames.push(bases[k] + 'hPa')
    }
    const temperature = []
    const u = []
    const v = []
    for (let k = 0; k < levelN; k++) {
      const t2d = []
      const u2d = []
      const v2d = []
      for (let i = 0; i < latN; i++) {
        const trow = []
        const urow = []
        const vrow = []
        for (let j = 0; j < lonN; j++) {
          const baseK = 290 - k * 4 - (latN - i) * 0.15 + Math.sin(j * 0.3) * 3
          trow.push(+(baseK + (Math.random() - 0.5) * 2).toFixed(2))
          urow.push(+(Math.sin(i * 0.2 + k) * 8).toFixed(2))
          vrow.push(+(Math.cos(j * 0.15 + k) * 6).toFixed(2))
        }
        t2d.push(trow)
        u2d.push(urow)
        v2d.push(vrow)
      }
      temperature.push(t2d)
      u.push(u2d)
      v.push(v2d)
    }
    payload.value = {
      fileName: 'wrfout_d01_2024-01-01_00-00-00.nc',
      fileSize: 42345678,
      dims: { time: 24, level: levelN, lat: latN, lon: lonN },
      vars: ['T2', 'U', 'V', 'P', 'RH'],
      levelNames,
      grid: { lat: lats, lon: lons, levels },
      temperature,
      u,
      v
    }
    levelIndex.value = 0
    loading.value = false
    nextTick(() => renderAll())
  }, 400)
}

function renderHeatmap() {
  if (!heatmapRef.value || !payload.value) return
  if (!heatmapChart) heatmapChart = echarts.init(heatmapRef.value)
  else heatmapChart.clear()

  const lats = payload.value.grid.lat
  const lons = payload.value.grid.lon
  const data = []
  let vmin = Infinity
  let vmax = -Infinity
  const latN = lats.length
  const lonN = lons.length
  for (let i = 0; i < latN; i++) {
    for (let j = 0; j < lonN; j++) {
      const k = payload.value.temperature[levelIndex.value][i][j] - 273.15
      if (k < vmin) vmin = k
      if (k > vmax) vmax = k
      data.push([lons[j], lats[i], +k.toFixed(2)])
    }
  }

  heatmapChart.setOption({
    title: {
      text: '温度水平剖面（°C） · ' + payload.value.levelNames[levelIndex.value],
      left: 'center',
      textStyle: { fontSize: 14, fontWeight: 600 }
    },
    tooltip: {
      formatter: p => `经度: ${p.value[0]}<br/>纬度: ${p.value[1]}<br/>温度: ${p.value[2].toFixed(2)} °C`
    },
    grid: { left: 60, right: 60, top: 50, bottom: 60 },
    xAxis: {
      type: 'category',
      data: lons.map(v => v.toFixed(1)),
      name: '经度',
      nameLocation: 'middle',
      nameGap: 30,
      splitArea: { show: true }
    },
    yAxis: {
      type: 'category',
      data: lats.map(v => v.toFixed(1)),
      name: '纬度',
      nameLocation: 'middle',
      nameGap: 40,
      splitArea: { show: true }
    },
    visualMap: {
      min: +vmin.toFixed(1),
      max: +vmax.toFixed(1),
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 10,
      inRange: { color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026'] },
      textStyle: { fontSize: 12 }
    },
    series: [{
      name: '温度',
      type: 'heatmap',
      data: data.map(d => [lons.indexOf(d[0]), lats.indexOf(d[1]), d[2]]),
      emphasis: { itemStyle: { borderColor: '#333', borderWidth: 1 } },
      progressive: 1000,
      animation: false
    }]
  })
}

function renderSurface() {
  if (!surfaceRef.value || !payload.value) return
  if (!surfaceChart) surfaceChart = echarts.init(surfaceRef.value)
  else surfaceChart.clear()

  const lons = payload.value.grid.lon
  const levels = payload.value.grid.levels
  const latMid = Math.floor(payload.value.grid.lat.length / 2)
  const data = []
  for (let k = 0; k < levels.length; k++) {
    for (let j = 0; j < lons.length; j++) {
      const tC = payload.value.temperature[k][latMid][j] - 273.15
      data.push([lons[j], levels[k], +tC.toFixed(2)])
    }
  }

  surfaceChart.setOption({
    title: {
      text: '温度垂直剖面（沿中间纬度）',
      left: 'center',
      textStyle: { fontSize: 14, fontWeight: 600 }
    },
    tooltip: {
      formatter: p => `经度: ${p.value[0]}<br/>气压: ${p.value[1]} hPa<br/>温度: ${p.value[2].toFixed(2)} °C`
    },
    grid3D: {
      viewControl: { autoRotate: false, distance: 180 },
      boxWidth: 160,
      boxDepth: 80,
      boxHeight: 100,
      light: { main: { intensity: 1.2, shadow: true }, ambient: { intensity: 0.3 } }
    },
    xAxis3D: { type: 'value', name: '经度', min: lons[0], max: lons[lons.length - 1] },
    yAxis3D: { type: 'value', name: 'hPa', min: levels[levels.length - 1], max: levels[0], inverse: true },
    zAxis3D: { type: 'value', name: '温度 °C' },
    visualMap: {
      show: true,
      dimension: 2,
      min: -40,
      max: 30,
      calculable: true,
      inRange: { color: ['#313695', '#74add1', '#e0f3f8', '#fee090', '#fdae61', '#d73027'] }
    },
    series: [{
      type: 'surface',
      wireframe: { show: false },
      shading: 'color',
      data
    }]
  })
}

function renderAll() {
  if (activeTab.value === '2d') renderHeatmap()
  if (activeTab.value === '3d') renderSurface()
}

watch(activeTab, (t) => {
  nextTick(() => {
    if (t === '2d') renderHeatmap()
    if (t === '3d') renderSurface()
  })
})

watch(levelIndex, () => {
  if (activeTab.value === '2d') renderHeatmap()
})

let resizeHandler = null
onMounted(() => {
  resizeHandler = () => {
    heatmapChart && heatmapChart.resize()
    surfaceChart && surfaceChart.resize()
  }
  window.addEventListener('resize', resizeHandler)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeHandler)
  heatmapChart && heatmapChart.dispose()
  surfaceChart && surfaceChart.dispose()
})
</script>

<style scoped>
.netcdf-preview {
  padding: 16px;
  background: #f5f7fa;
  min-height: 100vh;
}
.header-card {
  margin-bottom: 16px;
  border-radius: 10px;
}
.header-inner {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}
.demo-alert {
  width: 100%;
}
.main-row {
  display: flex;
}
.left-col, .right-col {
  min-width: 0;
}
.preview-card {
  border-radius: 10px;
  background: #fff;
}
.empty-wrap {
  min-height: 360px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.preview-tabs :deep(.el-tabs__item) {
  font-size: 14px;
}
.tab-toolbar {
  padding: 12px 4px 8px;
  display: flex;
  align-items: center;
  gap: 16px;
}
.tool-label {
  font-size: 13px;
  color: #606266;
}
.level-slider {
  flex: 1;
}
.chart-box {
  width: 100%;
  height: 480px;
}
.raw-info {
  padding: 8px 0;
}
.raw-info code {
  font-family: monospace;
  background: #f4f4f5;
  padding: 2px 6px;
  border-radius: 4px;
}
.json-preview {
  margin-top: 16px;
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 6px;
  font-family: monospace;
  font-size: 12px;
  max-height: 320px;
  overflow: auto;
}
</style>
