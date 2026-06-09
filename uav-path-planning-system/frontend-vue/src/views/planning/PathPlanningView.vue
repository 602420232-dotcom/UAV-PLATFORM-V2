<template>
  <div class="path-planning-view">
    <!-- 顶部 -->
    <el-alert
      title="演示模式 · 以下数据为本地模拟结果，仅用于前端 UI 演示"
      type="warning"
      :closable="false"
      show-icon
      class="demo-alert"
    />

    <div class="page-header">
      <h2 class="page-title">路径规划</h2>
      <el-tag type="warning" size="default" effect="dark">演示模式</el-tag>
      <div class="header-actions">
        <el-button size="small" @click="importDialogVisible = true">
          <span class="btn-icon">📥</span> 导入Excel
        </el-button>
        <el-button type="primary" size="small" @click="handleExportKML">
          <span class="btn-icon">📤</span> 导出KML
        </el-button>
      </div>
    </div>

    <!-- 主体 -->
    <el-row :gutter="16" class="main-row">
      <!-- ============== 左栏：航点与参数 ============== -->
      <el-col :span="6" class="col col-left">
        <el-card shadow="hover" class="panel">
          <template #header>
            <div class="panel-head">
              <span class="panel-title">航点列表</span>
              <el-tag size="small" type="info">{{ waypoints.length }} 个航点</el-tag>
            </div>
          </template>

          <el-table
            :data="waypoints"
            size="small"
            height="260"
            class="waypoint-table"
            row-key="id"
            @row-drop="handleRowDrop"
            :row-draggable="true"
            stripe
          >
            <el-table-column type="index" label="#" width="40" align="center" />
            <el-table-column label="名称" width="96">
              <template #default="{ row }">
                <el-input v-model="row.name" size="small" :border="false" />
              </template>
            </el-table-column>
            <el-table-column prop="lat" label="纬度" width="70" align="center">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.lat"
                  :min="-90"
                  :max="90"
                  :step="0.01"
                  size="small"
                  :controls="false"
                />
              </template>
            </el-table-column>
            <el-table-column prop="lng" label="经度" width="74" align="center">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.lng"
                  :min="-180"
                  :max="180"
                  :step="0.01"
                  size="small"
                  :controls="false"
                />
              </template>
            </el-table-column>
            <el-table-column prop="altitude" label="高度(m)" width="78" align="center">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.altitude"
                  :min="0"
                  :max="5000"
                  :step="10"
                  size="small"
                  :controls="false"
                />
              </template>
            </el-table-column>
            <el-table-column prop="danger" label="危险" width="78" align="center">
              <template #default="{ row }">
                <el-slider
                  v-model="row.danger"
                  :min="0"
                  :max="3"
                  :step="1"
                  size="small"
                  :show-tooltip="false"
                  :style="{ padding: '0 4px' }"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="44" align="center">
              <template #default="{ $index }">
                <el-button
                  size="small"
                  type="danger"
                  link
                  @click="removeWaypoint($index)"
                >删</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="add-waypoint-row">
            <el-input
              v-model="newWaypointName"
              size="small"
              placeholder="新增航点名称"
              class="new-wp-input"
              @keyup.enter="addWaypoint"
            />
            <el-button
              size="small"
              type="primary"
              @click="addWaypoint"
            >+ 添加航点</el-button>
          </div>
        </el-card>

        <el-card shadow="hover" class="panel mt-12">
          <template #header>
            <span class="panel-title">权重参数</span>
          </template>
          <div class="slider-row">
            <div class="slider-head">
              <span class="slider-label">气象权重</span>
              <span class="slider-value">{{ weights.weather }}</span>
            </div>
            <el-slider v-model="weights.weather" :min="0" :max="100" :step="1" />
          </div>
          <div class="slider-row">
            <div class="slider-head">
              <span class="slider-label">避障权重</span>
              <span class="slider-value">{{ weights.obstacle }}</span>
            </div>
            <el-slider v-model="weights.obstacle" :min="0" :max="100" :step="1" />
          </div>
          <div class="slider-row">
            <div class="slider-head">
              <span class="slider-label">能耗权重</span>
              <span class="slider-value">{{ weights.energy }}</span>
            </div>
            <el-slider v-model="weights.energy" :min="0" :max="100" :step="1" />
          </div>
        </el-card>

        <el-card shadow="hover" class="panel mt-12">
          <template #header>
            <span class="panel-title">飞行约束</span>
          </template>
          <div class="slider-row">
            <div class="slider-head">
              <span class="slider-label">最大高度 (m)</span>
              <span class="slider-value">{{ constraints.maxAltitude }}</span>
            </div>
            <el-slider v-model="constraints.maxAltitude" :min="50" :max="3000" :step="50" />
          </div>
          <div class="slider-row">
            <div class="slider-head">
              <span class="slider-label">最小间距 (km)</span>
              <span class="slider-value">{{ constraints.minGap }}</span>
            </div>
            <el-slider v-model="constraints.minGap" :min="0" :max="50" :step="1" />
          </div>
          <div class="constraint-row">
            <span>允许穿越禁飞区</span>
            <el-switch v-model="constraints.allowNoFly" />
          </div>
        </el-card>

        <el-card shadow="hover" class="panel mt-12">
          <template #header>
            <span class="panel-title">算法选择</span>
            <el-tag size="small" type="info" effect="plain" class="algo-tag-tip">支持多选</el-tag>
          </template>
          <el-checkbox-group v-model="selectedAlgorithms" class="algo-checks">
            <el-checkbox-button value="de_rrt_star" label="DE-RRT*" />
            <el-checkbox-button value="dwa" label="DWA" />
            <el-checkbox-button value="vrptw" label="VRPTW" />
          </el-checkbox-group>
        </el-card>
      </el-col>

      <!-- ============== 中栏：Leaflet 地图 ============== -->
      <el-col :span="12" class="col col-center">
        <el-card shadow="hover" class="panel map-panel">
          <template #header>
            <div class="panel-head">
              <span class="panel-title">地图可视化</span>
              <span class="map-tip">
                点击空白处添加航点 · 右键删除最近航点 · 拖拽 marker 实时更新
              </span>
            </div>
          </template>
          <div id="pp-map" ref="mapRef" class="map-canvas" />

          <div class="path-info-bar">
            <div class="info-cell">
              <div class="info-label">总距离</div>
              <div class="info-value">{{ currentPlan.distance.toFixed(2) }} km</div>
            </div>
            <div class="info-cell">
              <div class="info-label">预计飞行时间</div>
              <div class="info-value">{{ formatMinutes(currentPlan.duration) }}</div>
            </div>
            <div class="info-cell">
              <div class="info-label">预计能耗</div>
              <div class="info-value">{{ currentPlan.energy.toFixed(2) }} kWh</div>
            </div>
            <div class="info-cell">
              <div class="info-label">风险评分</div>
              <div class="info-value">
                <el-tag
                  :type="riskTagType(currentPlan.risk)"
                  size="default"
                  effect="dark"
                >{{ currentPlan.risk.toFixed(1) }} · {{ riskLabel(currentPlan.risk) }}</el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- ============== 右栏：多算法方案对比 ============== -->
      <el-col :span="6" class="col col-right">
        <el-card shadow="hover" class="panel">
          <template #header>
            <div class="panel-head">
              <span class="panel-title">方案对比</span>
              <el-tag size="small" type="success" effect="dark" v-if="bestAlgorithm">
                最佳: {{ algorithmLabel(bestAlgorithm) }}
              </el-tag>
            </div>
          </template>

          <div
            v-for="algo in allAlgorithms"
            :key="algo"
            class="algo-card"
            :class="{
              active: activeAlgorithm === algo,
              disabled: !selectedAlgorithms.includes(algo),
              best: bestAlgorithm === algo
            }"
            @click="selectAlgorithm(algo)"
          >
            <div class="algo-card-head">
              <div class="algo-card-title">
                <span class="algo-dot" :style="{ background: algorithmColor(algo) }" />
                <span>{{ algorithmLabel(algo) }}</span>
                <el-tag
                  v-if="bestAlgorithm === algo"
                  size="small"
                  type="success"
                  effect="dark"
                  class="best-tag"
                >最佳</el-tag>
              </div>
              <el-tag
                v-if="activeAlgorithm === algo"
                size="small"
                type="primary"
                effect="dark"
              >当前</el-tag>
            </div>

            <div class="algo-card-metrics">
              <div class="metric-cell">
                <span class="metric-label">距离</span>
                <span class="metric-val">{{ algorithmPlans[algo].distance.toFixed(1) }} km</span>
              </div>
              <div class="metric-cell">
                <span class="metric-label">时间</span>
                <span class="metric-val">{{ formatMinutes(algorithmPlans[algo].duration) }}</span>
              </div>
              <div class="metric-cell">
                <span class="metric-label">能耗</span>
                <span class="metric-val">{{ algorithmPlans[algo].energy.toFixed(2) }} kWh</span>
              </div>
              <div class="metric-cell">
                <span class="metric-label">风险</span>
                <el-tag
                  size="small"
                  :type="riskTagType(algorithmPlans[algo].risk)"
                >{{ algorithmPlans[algo].risk.toFixed(1) }}</el-tag>
              </div>
            </div>

            <div class="algo-card-status">
              <el-tag size="small" :type="algorithmStatus[algo].type" effect="plain">
                <span
                  class="status-dot"
                  :class="algorithmStatus[algo].dotClass"
                />
                {{ algorithmStatus[algo].text }}
              </el-tag>
            </div>
          </div>
        </el-card>

        <el-card shadow="hover" class="panel mt-12">
          <template #header>
            <div class="panel-head">
              <span class="panel-title">多目标权重雷达图</span>
            </div>
          </template>
          <div ref="radarChartRef" class="radar-chart" />
        </el-card>

        <el-card shadow="hover" class="panel mt-12">
          <template #header>
            <div class="panel-head">
              <span class="panel-title">多机协同队形</span>
              <el-switch v-model="formation.enabled" size="small" />
            </div>
          </template>
          <template v-if="formation.enabled">
            <div class="formation-row">
              <span class="formation-label">队形类型</span>
              <el-select v-model="formation.type" size="small" style="width: 120px">
                <el-option
                  v-for="ft in formationTypes"
                  :key="ft.value"
                  :label="ft.label"
                  :value="ft.value"
                />
              </el-select>
            </div>
            <div class="formation-row">
              <span class="formation-label">无人机数量</span>
              <el-input-number
                v-model="formation.uavCount"
                :min="2"
                :max="10"
                :step="1"
                size="small"
                controls-position="right"
              />
            </div>
            <div class="formation-row">
              <span class="formation-label">间距 (米)</span>
              <el-input-number
                v-model="formation.spacing"
                :min="20"
                :max="200"
                :step="10"
                size="small"
                controls-position="right"
              />
            </div>
            <div class="formation-preview">
              <div class="formation-diagram" :class="`formation-${formation.type}`">
                <div
                  v-for="i in formation.uavCount"
                  :key="i"
                  class="uav-dot"
                  :style="{ background: i === 1 ? '#67c23a' : '#409eff' }"
                >
                  <span v-if="i === 1" class="uav-label">长机</span>
                </div>
              </div>
            </div>
          </template>
          <div v-else class="formation-disabled">
            <span>关闭多机协同模式</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 导入Excel对话框 -->
    <el-dialog v-model="importDialogVisible" title="批量导入航点" width="600px" destroy-on-close>
      <ExcelBatchImporter
        ref="importRef"
        :required-fields="['name', 'lat', 'lng']"
        :optional-fields="['altitude', 'danger']"
        @success="handleImportSuccess"
      />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { createThrottledStream, throttled } from '@/utils/performance.js'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useNotificationStore } from '../../stores/notification'
import ExcelBatchImporter from '@/components/shared/ExcelBatchImporter.vue'
import { exportToKML } from '@/utils/kml.js'
import * as echarts from 'echarts'

const notificationStore = useNotificationStore()
const importDialogVisible = ref(false)
const importRef = ref(null)
const radarChartRef = ref(null)
const formationDialogVisible = ref(false)
let planningSucceededOnce = false
let planningFailedOnce = false

function notifyPlanningResult() {
  const risk = currentPlan.value && currentPlan.value.risk
  const distance = currentPlan.value && currentPlan.value.distance
  if (waypoints.value.length < 2) {
    if (!planningFailedOnce) {
      planningFailedOnce = true
      notificationStore.pushWithDesktop({
        type: 'danger',
        title: '路径规划失败',
        message: `航点数量不足（${waypoints.value.length} 个），请至少设置 2 个航点`,
        source: 'planning'
      })
    }
    return
  }
  planningFailedOnce = false
  if (!planningSucceededOnce) {
    planningSucceededOnce = true
    const algo = activeAlgorithm.value
    notificationStore.pushWithDesktop({
      type: 'success',
      title: '路径规划完成',
      message: `算法 ${algo} 已完成规划，总距离约 ${(distance || 0).toFixed(1)} km，风险 ${(risk || 0).toFixed(1)}`,
      source: 'planning'
    })
  }
}

// ===== Mock 数据 =====
const allAlgorithms = ['de_rrt_star', 'dwa', 'vrptw']
const selectedAlgorithms = ref(['de_rrt_star', 'dwa', 'vrptw'])
const activeAlgorithm = ref('de_rrt_star')

let waypointIdSeq = 0
const makeWaypoint = (name, lat, lng, altitude = 120, danger = 0) => ({
  id: ++waypointIdSeq,
  name,
  lat,
  lng,
  altitude,
  danger
})

const waypoints = ref([
  makeWaypoint('北京首都机场', 39.9000, 116.4000, 100, 1),
  makeWaypoint('天津中转点', 39.1200, 117.2000, 150, 0),
  makeWaypoint('济南上空', 36.6500, 117.0000, 120, 2),
  makeWaypoint('上海虹桥', 31.2000, 121.5000, 100, 1)
])

const newWaypointName = ref('')

const weights = reactive({
  weather: 40,
  obstacle: 60,
  energy: 50
})

const constraints = reactive({
  maxAltitude: 1000,
  minGap: 5,
  allowNoFly: false
})

// 多机队形配置
const formationTypes = [
  { value: 'line', label: '线性队列' },
  { value: 'v-shape', label: 'V字形' },
  { value: 'diamond', label: '菱形' },
  { value: 'circle', label: '圆形' }
]
const formation = reactive({
  enabled: false,
  type: 'line',
  uavCount: 3,
  spacing: 50 // 米
})

// ===== Leaflet =====
let mapInstance = null
const markerLayer = ref(null)
const pathLayer = ref(null)

function createMarkerIcon(type) {
  const color =
    type === 'start' ? '#67c23a' :
    type === 'end' ? '#f56c6c' : '#409eff'
  return L.divIcon({
    className: 'pp-marker-icon',
    html: `
      <div class="pp-marker" style="background:${color};">
        ${type === 'start' ? 'S' : type === 'end' ? 'E' : ''}
      </div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 14]
  })
}

function initMap() {
  if (!document.getElementById('pp-map')) return
  mapInstance = L.map('pp-map', {
    zoomControl: true,
    attributionControl: true
  }).setView([35.5, 118.0], 5)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 18
  }).addTo(mapInstance)

  markerLayer.value = L.layerGroup().addTo(mapInstance)
  pathLayer.value = L.layerGroup().addTo(mapInstance)

  mapInstance.on('click', (e) => {
    const { lat, lng } = e.latlng
    addWaypointAt(lat, lng)
  })

  mapInstance.on('contextmenu', (e) => {
    if (waypoints.value.length <= 2) return
    const { lat, lng } = e.latlng
    let nearestIdx = -1
    let nearestDist = Infinity
    waypoints.value.forEach((w, idx) => {
      const d = haversineKm(lat, lng, w.lat, w.lng)
      if (d < nearestDist) {
        nearestDist = d
        nearestIdx = idx
      }
    })
    if (nearestIdx !== -1 && nearestDist < 50) {
      waypoints.value.splice(nearestIdx, 1)
    }
  })

  renderMarkers()
  renderPaths()
}

function renderMarkers() {
  if (!markerLayer.value || !mapInstance) return
  markerLayer.value.clearLayers()

  waypoints.value.forEach((wp, idx) => {
    const type = idx === 0 ? 'start' : idx === waypoints.value.length - 1 ? 'end' : 'mid'
    const marker = L.marker([wp.lat, wp.lng], {
      draggable: true,
      icon: createMarkerIcon(type)
    })
    marker.bindTooltip(`${wp.name}<br/>${wp.lat.toFixed(3)}, ${wp.lng.toFixed(3)}`, {
      direction: 'top',
      offset: [0, -14]
    })
    marker.on('dragend', () => {
      const pos = marker.getLatLng()
      wp.lat = Number(pos.lat.toFixed(4))
      wp.lng = Number(pos.lng.toFixed(4))
    })
    marker.addTo(markerLayer.value)
  })
}

function renderPaths() {
  if (!pathLayer.value || !mapInstance) return
  pathLayer.value.clearLayers()

  if (waypoints.value.length < 2) return

  const enabled = selectedAlgorithms.value
  if (enabled.length === 0) return

  enabled.forEach((algo) => {
    const path = buildPathFor(algo)
    const color = algorithmColor(algo)
    const isActive = activeAlgorithm.value === algo
    const line = L.polyline(path, {
      color,
      weight: isActive ? 5 : 2.5,
      opacity: isActive ? 0.95 : 0.45,
      lineCap: 'round',
      lineJoin: 'round',
      dashArray: isActive ? null : '6 6',
      smoothFactor: 0.8
    })
    line.addTo(pathLayer.value)
  })
}

// 生成不同算法的模拟路径（中间点微扰动，形成不同形状）
function buildPathFor(algo) {
  const base = waypoints.value.map((w) => [w.lat, w.lng])
  const result = []
  for (let i = 0; i < base.length; i++) {
    result.push(base[i])
    if (i < base.length - 1) {
      result.push(midpointPerturb(base[i], base[i + 1], algo, i))
    }
  }
  return result
}

function midpointPerturb(a, b, algo, seed) {
  const midLat = (a[0] + b[0]) / 2
  const midLng = (a[1] + b[1]) / 2
  const dLat = b[0] - a[0]
  const dLng = b[1] - a[1]
  // 垂直方向偏移
  const perpLat = -dLng
  const perpLng = dLat
  let factor = 0
  if (algo === 'de_rrt_star') factor = 0.02 + (seed % 2) * 0.01
  else if (algo === 'dwa') factor = 0.08 + ((seed + 1) % 3) * 0.03
  else if (algo === 'vrptw') factor = -0.05 - (seed % 2) * 0.02
  return [midLat + perpLat * factor, midLng + perpLng * factor]
}

// ===== 路径指标计算 =====
function haversineKm(lat1, lng1, lat2, lng2) {
  const R = 6371
  const toRad = (d) => (d * Math.PI) / 180
  const dLat = toRad(lat2 - lat1)
  const dLng = toRad(lng2 - lng1)
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(a))
}

function totalDistanceKm(points) {
  let d = 0
  for (let i = 1; i < points.length; i++) {
    d += haversineKm(points[i - 1][0], points[i - 1][1], points[i][0], points[i][1])
  }
  return d
}

// 基于算法 + 权重 + 航点危险等级，估算各算法方案指标
function computePlan(algo, baseDistance) {
  const { weather, obstacle, energy } = weights
  const totalWeight = weather + obstacle + energy || 1

  // 距离系数
  let distanceFactor = 1
  let speedFactor = 1
  let energyFactor = 1

  if (algo === 'de_rrt_star') {
    distanceFactor = 1.0 + (weather / totalWeight) * 0.05
    speedFactor = 1.0
    energyFactor = 1.0
  } else if (algo === 'dwa') {
    distanceFactor = 1.0 + (obstacle / totalWeight) * 0.18
    speedFactor = 0.85 + (obstacle / totalWeight) * 0.1
    energyFactor = 1.1
  } else if (algo === 'vrptw') {
    distanceFactor = 1.0 + (energy / totalWeight) * 0.08
    speedFactor = 0.95
    energyFactor = 0.82
  }

  const distance = baseDistance * distanceFactor
  const cruiseSpeedKmh = 65 * speedFactor
  const durationMinutes = (distance / cruiseSpeedKmh) * 60
  const kwhPerKm = 0.12 * energyFactor
  const energyValue = distance * kwhPerKm

  // 风险：基于权重、航点危险等级、距离
  const avgDanger =
    waypoints.value.reduce((s, w) => s + w.danger, 0) /
    (waypoints.value.length || 1)
  const riskBase =
    (weather * 0.35 + obstacle * 0.4 + energy * 0.25) / totalWeight * 100
  let algoRisk = 0
  if (algo === 'de_rrt_star') algoRisk = -2
  else if (algo === 'dwa') algoRisk = -10
  else if (algo === 'vrptw') algoRisk = 3
  const risk = Math.max(0, Math.min(100, riskBase + avgDanger * 8 + algoRisk + distance * 0.05))

  return { distance, duration: durationMinutes, energy: energyValue, risk }
}

const baseDistance = computed(() => {
  if (waypoints.value.length < 2) return 0
  const pts = waypoints.value.map((w) => [w.lat, w.lng])
  return totalDistanceKm(pts)
})

const algorithmPlans = computed(() => {
  const res = {}
  allAlgorithms.forEach((algo) => {
    res[algo] = computePlan(algo, baseDistance.value || 1000)
  })
  return res
})

const currentPlan = computed(() => algorithmPlans.value[activeAlgorithm.value])

const bestAlgorithm = computed(() => {
  const enabled = selectedAlgorithms.value
  if (enabled.length === 0) return null
  let best = enabled[0]
  let bestRisk = algorithmPlans.value[best].risk
  enabled.forEach((algo) => {
    if (algorithmPlans.value[algo].risk < bestRisk) {
      best = algo
      bestRisk = algorithmPlans.value[algo].risk
    }
  })
  return best
})

const algorithmStatus = computed(() => {
  const res = {}
  allAlgorithms.forEach((algo) => {
    if (!selectedAlgorithms.value.includes(algo)) {
      res[algo] = { type: 'info', text: '未启用', dotClass: 'dot-off' }
    } else if (algo === bestAlgorithm.value) {
      res[algo] = { type: 'success', text: '已计算 · 最佳', dotClass: 'dot-ok' }
    } else {
      res[algo] = { type: 'primary', text: '已计算', dotClass: 'dot-ok' }
    }
  })
  return res
})

const weightRiskScore = computed(() => ({
  weather: weights.weather * 0.9 + (weights.weather > 60 ? 10 : 0),
  obstacle: weights.obstacle * 0.85 + (weights.obstacle > 60 ? 10 : 0),
  energy: weights.energy * 0.9
}))

// 权重雷达图配置
const radarOption = computed(() => ({
  radar: {
    indicator: [
      { name: '气象权重', max: 100 },
      { name: '避障权重', max: 100 },
      { name: '能耗权重', max: 100 }
    ],
    radius: '60%',
    center: ['50%', '55%'],
    axisName: { color: '#606266', fontSize: 11 }
  },
  series: [{
    type: 'radar',
    data: [{
      value: [weights.weather, weights.obstacle, weights.energy],
      name: '权重分配',
      areaStyle: { color: 'rgba(64, 158, 255, 0.25)' },
      lineStyle: { color: '#409eff', width: 2 },
      itemStyle: { color: '#409eff' }
    }]
  }]
}))

// ===== 算法工具 =====
function algorithmLabel(algo) {
  return (
    {
      de_rrt_star: 'DE-RRT*',
      dwa: 'DWA',
      vrptw: 'VRPTW'
    }[algo] || algo
  )
}

function algorithmColor(algo) {
  return (
    {
      de_rrt_star: '#67c23a',
      dwa: '#f56c6c',
      vrptw: '#409eff'
    }[algo] || '#909399'
  )
}

function riskTagType(risk) {
  if (risk < 30) return 'success'
  if (risk < 55) return 'warning'
  if (risk < 75) return 'warning'
  return 'danger'
}

function riskLabel(risk) {
  if (risk < 30) return '低'
  if (risk < 55) return '中低'
  if (risk < 75) return '中高'
  return '高'
}

function formatMinutes(m) {
  if (!m || m < 0) return '—'
  const hours = Math.floor(m / 60)
  const mins = Math.floor(m % 60)
  if (hours > 0) return `${hours}h ${mins}m`
  return `${mins} min`
}

// ===== 操作方法 =====
function addWaypoint() {
  const last = waypoints.value[waypoints.value.length - 1]
  const lat = last ? last.lat + (Math.random() - 0.5) * 0.4 : 35.0
  const lng = last ? last.lng + (Math.random() - 0.5) * 0.4 : 117.0
  const name = newWaypointName.value.trim() || `航点 ${waypoints.value.length + 1}`
  waypoints.value.push(makeWaypoint(name, Number(lat.toFixed(4)), Number(lng.toFixed(4)), 120, 0))
  newWaypointName.value = ''
}

function addWaypointAt(lat, lng) {
  const name = `航点 ${waypoints.value.length + 1}`
  waypoints.value.push(makeWaypoint(name, Number(lat.toFixed(4)), Number(lng.toFixed(4)), 120, 0))
}

function removeWaypoint(idx) {
  if (waypoints.value.length <= 2) return
  waypoints.value.splice(idx, 1)
}

function handleRowDrop() {
  // 触发重绘
  nextTick(() => {
    renderMarkers()
    renderPaths()
  })
}

function selectAlgorithm(algo) {
  if (!selectedAlgorithms.value.includes(algo)) return
  activeAlgorithm.value = algo
}

// ===== 响应式重计算 =====
function recompute() {
  if (!selectedAlgorithms.value.includes(activeAlgorithm.value)) {
    if (selectedAlgorithms.value.length > 0) {
      activeAlgorithm.value = selectedAlgorithms.value[0]
    }
  }
  nextTick(() => {
    renderMarkers()
    renderPaths()
    if (mapInstance) {
      const bounds = waypoints.value.map((w) => [w.lat, w.lng])
      if (bounds.length >= 2) {
        try {
          mapInstance.fitBounds(bounds, { padding: [40, 40] })
        } catch (_) {
          // ignore
        }
      }
    }
  })
  notifyPlanningResult()
}

const recomputeThrottled = throttled(recompute, 120)

// ===== 导入导出 =====
function handleImportSuccess(importedWaypoints) {
  waypoints.value = importedWaypoints.map((wp, idx) =>
    makeWaypoint(wp.name || `航点 ${idx + 1}`, wp.lat, wp.lng, wp.altitude || 120, wp.danger || 0)
  )
  importDialogVisible.value = false
  notificationStore.pushWithDesktop({
    type: 'success',
    title: '导入成功',
    message: `已导入 ${waypoints.value.length} 个航点`,
    source: 'planning'
  })
  nextTick(() => recompute())
}

function handleExportKML() {
  if (waypoints.value.length < 2) {
    notificationStore.pushWithDesktop({
      type: 'warning',
      title: '导出失败',
      message: '航点数量不足，至少需要 2 个航点',
      source: 'planning'
    })
    return
  }
  exportToKML(waypoints.value, 'uav-mission', { activeAlgorithm: activeAlgorithm.value })
  notificationStore.pushWithDesktop({
    type: 'success',
    title: '导出成功',
    message: 'KML 文件已触发下载',
    source: 'planning'
  })
}

watch(
  [waypoints, weights, constraints, selectedAlgorithms, activeAlgorithm],
  recomputeThrottled,
  { deep: true }
)

// ===== 生命周期 =====
let radarChart = null

onMounted(() => {
  nextTick(() => {
    initMap()
    if (mapInstance) {
      setTimeout(() => mapInstance.invalidateSize(), 200)
    }
    // 初始化雷达图
    if (radarChartRef.value) {
      radarChart = echarts.init(radarChartRef.value)
      radarChart.setOption(radarOption.value)
    }
  })
})

onBeforeUnmount(() => {
  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
  }
  if (radarChart) {
    radarChart.dispose()
    radarChart = null
  }
})

// 监听权重变化更新雷达图
watch(
  () => [weights.weather, weights.obstacle, weights.energy],
  () => {
    if (radarChart) {
      radarChart.setOption(radarOption.value, true)
    }
  }
)
</script>

<style scoped>
.path-planning-view {
  padding: 16px;
  background: #f5f7fa;
  min-height: 100%;
  font-size: 13px;
  color: #303133;
}

.demo-alert {
  margin-bottom: 12px;
  border-radius: 6px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.header-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}
.btn-icon {
  margin-right: 4px;
}
.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  letter-spacing: 1px;
}

.main-row {
  align-items: stretch;
}

.col {
  display: flex;
  flex-direction: column;
}
.col-left .panel,
.col-right .panel {
  margin-bottom: 12px;
}

.panel {
  border-radius: 8px;
  transition: box-shadow 0.2s;
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.panel-title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}
.mt-12 {
  margin-top: 12px;
}

/* 表格 */
.waypoint-table :deep(.el-table__row) {
  cursor: move;
}
.waypoint-table :deep(.el-input-number .el-input__inner) {
  text-align: center;
  padding: 0 4px;
}
.add-waypoint-row {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}
.add-waypoint-row .new-wp-input {
  flex: 1;
}

/* 权重 / 约束 */
.slider-row {
  margin-bottom: 12px;
}
.slider-row:last-child {
  margin-bottom: 0;
}
.slider-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
  font-size: 12px;
  color: #606266;
}
.slider-head .slider-label {
  font-weight: 500;
}
.slider-head .slider-value {
  color: #303133;
  font-weight: 600;
}

.constraint-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #606266;
  padding-top: 2px;
}

/* 算法 */
.algo-checks {
  display: flex;
  width: 100%;
}
.algo-checks :deep(.el-checkbox-button) {
  flex: 1;
}
.algo-checks :deep(.el-checkbox-button .el-checkbox__inner) {
  width: 100%;
  text-align: center;
}
.algo-tag-tip {
  margin-left: 8px;
}

/* 地图 */
.map-panel {
  display: flex;
  flex-direction: column;
}
.map-canvas {
  height: 520px;
  border-radius: 6px;
  overflow: hidden;
  background: #0f2a44;
  border: 1px solid #dcdfe6;
}
.map-tip {
  font-size: 12px;
  color: #909399;
  font-weight: 400;
}

.path-info-bar {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-top: 12px;
}
.info-cell {
  background: #f4f6f9;
  border-radius: 6px;
  padding: 10px 12px;
  border-left: 3px solid #409eff;
}
.info-label {
  font-size: 12px;
  color: #909399;
}
.info-value {
  margin-top: 4px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

/* 算法卡片 */
.algo-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}
.algo-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 10px rgba(64, 158, 255, 0.15);
  transform: translateY(-1px);
}
.algo-card.active {
  border-color: #409eff;
  background: linear-gradient(135deg, #ecf5ff 0%, #ffffff 100%);
  box-shadow: 0 2px 14px rgba(64, 158, 255, 0.22);
}
.algo-card.best {
  border-color: #67c23a;
}
.algo-card.best.active {
  background: linear-gradient(135deg, #f0f9eb 0%, #ffffff 100%);
}
.algo-card.disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.algo-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.algo-card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #303133;
}
.algo-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}
.best-tag {
  margin-left: 4px;
}

.algo-card-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  margin-bottom: 10px;
}
.metric-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: #f4f6f9;
  border-radius: 4px;
  padding: 6px 4px;
  text-align: center;
}
.metric-label {
  font-size: 11px;
  color: #909399;
}
.metric-val {
  font-size: 12px;
  font-weight: 600;
  color: #303133;
}

.algo-card-status {
  display: flex;
  justify-content: flex-end;
}
.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 4px;
  vertical-align: middle;
}
.dot-ok {
  background: #67c23a;
}
.dot-off {
  background: #c0c4cc;
}
.dot-working {
  background: #409eff;
  animation: pulse 1.2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* 评分行 */
.score-row {
  display: grid;
  grid-template-columns: 70px 1fr 40px;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
}
.score-label {
  font-size: 12px;
  color: #606266;
}
.score-val {
  font-size: 12px;
  color: #303133;
  text-align: right;
  font-weight: 500;
}

/* 雷达图 */
.radar-chart {
  height: 200px;
  width: 100%;
}

/* 多机队形 */
.formation-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.formation-label {
  font-size: 12px;
  color: #606266;
}
.formation-preview {
  margin-top: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  display: flex;
  justify-content: center;
}
.formation-diagram {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  align-items: center;
  max-width: 180px;
}
.uav-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  border: 2px solid #fff;
  box-shadow: 0 2px 6px rgba(0,0,0,0.3);
  position: relative;
}
.uav-label {
  font-size: 8px;
  position: absolute;
  top: -16px;
  white-space: nowrap;
}
.formation-disabled {
  text-align: center;
  color: #909399;
  font-size: 12px;
  padding: 20px 0;
}
.formation-line {
  flex-direction: row;
}
.formation-v-shape {
  flex-direction: row;
  flex-wrap: nowrap;
}
.formation-diamond {
  flex-direction: row;
  flex-wrap: wrap;
  justify-content: center;
}
.formation-circle {
  flex-direction: row;
  flex-wrap: wrap;
  justify-content: center;
}

/* 自定义 marker icon 容器无默认样式干扰 */
:deep(.pp-marker-icon) {
  background: transparent !important;
  border: none !important;
}
:deep(.pp-marker) {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  border: 2px solid #fff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
  cursor: grab;
}
:deep(.pp-marker:active) {
  cursor: grabbing;
}

@media (max-width: 768px) {
  .main-row,
  .el-row,
  .el-row--flex {
    flex-direction: column !important;
  }
  .el-col {
    max-width: 100% !important;
    flex: 0 0 100% !important;
  }
  :deep(.el-card) {
    padding: 10px !important;
  }
  :deep(.pp-marker) {
    width: 24px;
    height: 24px;
  }
  .panel {
    padding: 10px !important;
  }
  .col,
  .col-left,
  .col-right {
    padding: 0 !important;
    margin-bottom: 12px;
  }
  :deep(.el-table-wrapper) {
    overflow-x: auto;
  }
  :deep(.pp-map-container),
  .pp-map-container {
    height: 280px !important;
  }
  :deep(.pp-chart-wrapper),
  .pp-chart-wrapper {
    height: 280px !important;
  }
}
</style>
