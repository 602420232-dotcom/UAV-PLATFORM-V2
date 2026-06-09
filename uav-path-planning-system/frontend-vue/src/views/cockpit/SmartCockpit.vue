<template>
  <div class="cockpit">
    <el-alert
      title="演示模式 - 数据为模拟数据"
      type="warning"
      show-icon
      :closable="false"
      class="demo-alert"
    />

    <!-- 顶部状态条 -->
    <div class="status-bar">
      <div class="status-left">
        <span class="cockpit-icon">✈</span>
        <h2>智能驾驶舱 · 3D 低空态势</h2>
      </div>
      <div class="status-right">
        <el-card class="status-card" shadow="hover">
          <div class="stat-label">数据范围</div>
          <div class="stat-value">
            <DataScopeBadge :scope="activeScope" :team="authStore.team" />
          </div>
          <div class="stat-hint" style="margin-top: 4px;">
            <el-select v-model="dataScopeFilter" placeholder="切换" size="small" clearable style="width: 100%">
              <el-option label="跟随账号" value="" />
              <el-option label="仅个人" value="personal" />
              <el-option label="仅团队" value="team" />
              <el-option label="全部数据" value="all" />
            </el-select>
          </div>
        </el-card>
        <el-card class="status-card weather-stat-card" shadow="hover">
          <div class="stat-label">实时气象</div>
          <div class="stat-value weather-value">
            <span>{{ weatherTop.temperature }}°C</span>
            <span class="stat-value-divider">|</span>
            <span>{{ weatherTop.windSpeed }} m/s</span>
            <span class="stat-value-divider">|</span>
            <span>{{ weatherTop.windDirection }}°</span>
          </div>
          <div class="stat-hint">数据来源：天资 / 风雷服务</div>
        </el-card>

        <el-card class="status-card task-stat-card" shadow="hover">
          <div class="stat-label">任务执行状态</div>
          <div class="task-progress-wrap">
            <el-progress
              :percentage="67"
              :stroke-width="8"
              color="#40E0FF"
              class="task-progress"
              :format="(p) => '86 / 128  已完成  ' + p + '%'"
            />
          </div>
          <div class="task-mini-grid">
            <div class="task-mini-item">
              <span class="task-mini-label">进行中</span>
              <span class="task-mini-value primary">{{ taskStat.inProgress }}</span>
            </div>
            <div class="task-mini-item">
              <span class="task-mini-label">异常</span>
              <span class="task-mini-value danger">{{ taskStat.exception }}</span>
            </div>
            <div class="task-mini-item">
              <span class="task-mini-label">已完成</span>
              <span class="task-mini-value success">{{ taskStat.done }}</span>
            </div>
            <div class="task-mini-item">
              <span class="task-mini-label">总任务</span>
              <span class="task-mini-value">{{ taskStat.total }}</span>
            </div>
          </div>
        </el-card>

        <el-card class="status-card plan-stat-card" shadow="hover">
          <div class="stat-label">路径规划耗时</div>
          <div class="plan-values">
            <div class="plan-value-item">
              <span class="plan-value-label">最新</span>
              <span class="plan-value-num">{{ planCost.latest }}<small>s</small></span>
            </div>
            <div class="plan-value-item">
              <span class="plan-value-label">平均</span>
              <span class="plan-value-num">{{ planCost.avg }}<small>s</small></span>
            </div>
          </div>
          <div class="stat-hint">近 50 次规划平均</div>
        </el-card>
      </div>
    </div>

    <!-- 主体布局: 左 78% 3D 地图, 右 22% 面板 -->
    <el-row :gutter="16" class="main-row" style="flex-wrap: nowrap;">
      <el-col :xs="24" :lg="18" class="main-left-col" style="flex: 0 0 78%; max-width: 78%;">
        <el-card class="cockpit-card dark-card map-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>3D 低空飞行地图 · 北京</span>
              <div class="map-toolbar">
                <el-tag size="small" type="success" effect="dark" class="mode-tag">
                  {{ useCesium ? 'Cesium 3D' : 'Leaflet 2D' }}
                </el-tag>
                <el-button size="small" @click="resetView">复位视角</el-button>
                <el-button size="small" @click="toggleFollow">
                  {{ followSelected ? '取消跟随' : '跟随选中' }}
                </el-button>
              </div>
            </div>
          </template>
          <div ref="mapContainerRef" class="map-container"></div>
          <div v-if="!useCesium" class="map-degrade-hint">
            ⚠ Cesium 资源未就绪，当前显示 Leaflet 2D 降级视图
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="6" class="main-right-col" style="flex: 0 0 22%; max-width: 22%;">
        <el-card class="cockpit-card dark-card side-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>无人机列表</span>
              <el-tag size="small" type="info">{{ visibleDrones.length }} / {{ drones.length }}</el-tag>
            </div>
          </template>
          <el-table
            :data="visibleDrones"
            size="mini"
            :row-class-name="tableRowClassName"
            class="drone-table"
            :highlight-current-row="true"
            @row-click="onDroneRowClick"
            stripe
            height="220"
          >
            <el-table-column prop="id" label="编号" width="64" />
            <el-table-column prop="model" label="型号" width="80" />
            <el-table-column label="团队" width="72">
              <template #default="scope">
                <el-tag size="small" effect="plain">{{ teamDisplay(scope.row.team) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="battery" label="电量" width="72">
              <template #default="scope">
                <el-progress :percentage="scope.row.battery" :stroke-width="6" :color="getBatteryColor(scope.row.battery)" :show-text="false" />
              </template>
            </el-table-column>
            <el-table-column label="状态" width="64">
              <template #default="scope">
                <el-tag :type="getDroneStatusTag(scope.row.status).type" size="small" effect="dark">
                  {{ scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="task" label="任务" min-width="90" show-overflow-tooltip />
            <el-table-column prop="altitude" label="高度(m)" width="72" align="right" />
            <el-table-column prop="speed" label="速度(km/h)" width="80" align="right" />
          </el-table>
        </el-card>

        <el-card class="cockpit-card dark-card side-card detail-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>选中详情 · {{ selectedDrone ? selectedDrone.id : '-' }}</span>
            </div>
          </template>
          <div v-if="selectedDrone" class="detail-body">
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">所属团队</span>
                <el-tag size="small" effect="plain">{{ teamDisplay(selectedDrone.team) }}</el-tag>
              </div>
              <div class="detail-item">
                <span class="detail-label">负责人</span>
                <span class="detail-value mono">{{ selectedDrone.ownerId }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">经度</span>
                <span class="detail-value mono">{{ selectedDrone.lng.toFixed(5) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">纬度</span>
                <span class="detail-value mono">{{ selectedDrone.lat.toFixed(5) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">航向角</span>
                <span class="detail-value mono">{{ selectedDrone.heading }}°</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">水平速度</span>
                <span class="detail-value mono">{{ selectedDrone.speed }} km/h</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">垂直速度</span>
                <span class="detail-value mono">{{ selectedDrone.vSpeed }} m/s</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">高度</span>
                <span class="detail-value mono highlight">{{ selectedDrone.altitude }} m</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">电池温度</span>
                <span class="detail-value mono">{{ selectedDrone.batteryTemp }} °C</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">信号强度</span>
                <span class="detail-value mono">{{ selectedDrone.signal }} dBm</span>
              </div>
              <div class="detail-item wide">
                <span class="detail-label">预计抵达</span>
                <span class="detail-value mono highlight">{{ selectedDrone.eta }}</span>
              </div>
            </div>
          </div>
          <div v-else class="detail-empty">
            点击地图或左侧列表选择无人机
          </div>
        </el-card>

        <el-card class="cockpit-card dark-card side-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>禁飞区列表</span>
              <el-tag size="small" type="danger" effect="dark">{{ noFlyZones.length }}</el-tag>
            </div>
          </template>
          <div class="nofly-list">
            <div
              v-for="(zone, idx) in noFlyZones" :key="'nfz-' + idx"
              class="nofly-item"
              @click="flyToNoFlyZone(zone)"
            >
              <span class="nofly-name">{{ zone.name }}</span>
              <span class="nofly-type">{{ zone.type }}</span>
            </div>
          </div>
        </el-card>

        <el-card class="cockpit-card dark-card side-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>回放控制</span>
              <el-tag size="small" :type="playing ? 'success' : 'info'" effect="dark">
                {{ playing ? '播放中' : '已暂停' }}
              </el-tag>
            </div>
          </template>
          <div class="replay-box">
            <div class="replay-row">
              <span class="replay-label">当前帧</span>
              <span class="replay-value">{{ currentFrame }} / {{ totalFrames }}</span>
            </div>
            <div class="replay-row">
              <span class="replay-label">当前时间</span>
              <span class="replay-value mono">{{ formatReplayTime(currentFrame) }}</span>
            </div>
            <div class="replay-row">
              <span class="replay-label">倍速</span>
              <el-radio-group v-model="playSpeed" size="small">
                <el-radio-button :value="0.5">0.5x</el-radio-button>
                <el-radio-button :value="1">1x</el-radio-button>
                <el-radio-button :value="2">2x</el-radio-button>
                <el-radio-button :value="4">4x</el-radio-button>
              </el-radio-group>
            </div>
            <div class="replay-row">
              <el-button size="small" @click="togglePlay">
                {{ playing ? '⏸ 暂停' : '▶ 播放' }}
              </el-button>
              <el-button size="small" @click="resetReplay">↺ 重置</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 底部时间轴 scrubber -->
    <el-card class="cockpit-card dark-card timeline-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>轨迹回放时间轴</span>
          <span class="timeline-hint">
            总时长 <span class="mono">{{ formatReplayTime(0) }}</span> -
            <span class="mono">{{ formatReplayTime(totalFrames) }}</span>
          </span>
        </div>
      </template>
      <div class="timeline-body">
        <el-slider
          v-model="currentFrame"
          :min="0"
          :max="totalFrames"
          :step="1"
          show-stops
          :marks="sliderMarks"
          :tooltip-format="(v) => '帧 ' + v + ' · ' + formatReplayTime(v)"
          class="replay-slider"
        />
        <div class="timeline-bar">
          <div class="timeline-track" :style="{ width: (currentFrame / totalFrames * 100) + '%' }"></div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { createThrottledStream, batchRaf } from '@/utils/performance.js'
import L from 'leaflet'
import idb, { STORE_TILES } from '../../utils/indexedDB'
import { useNotificationStore } from '../../stores/notification'
import { useAuthStore, TEAM_LABELS } from '../../stores/auth'
import DataScopeBadge from '../../components/shared/DataScopeBadge.vue'

const authStore = useAuthStore()
const notificationStore = useNotificationStore()
const droneAlertSent = new Set()

// 数据范围过滤
const dataScopeFilter = ref('')
const activeScope = computed(() => dataScopeFilter.value || authStore.dataScope || 'team')

function teamDisplay(team) {
  return TEAM_LABELS[team] || team || '-'
}

function _canSeeDrone(ownerId, team) {
  const scope = activeScope.value
  if (scope === 'all') return true
  if (scope === 'personal') {
    const uid = authStore.userId
    return ownerId && uid && String(ownerId) === String(uid)
  }
  if (scope === 'team') {
    return team && authStore.team && team === authStore.team
  }
  return true
}

const TILE_TTL = 30 * 24 * 60 * 60 * 1000

let tileCacheReady = false
let tileCachePromise = null

function initTileCache() {
  if (tileCachePromise) return tileCachePromise
  tileCachePromise = idb.initDB()
    .then(() => {
      tileCacheReady = true
      if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.DEV) {
        console.info('[SmartCockpit] IndexedDB 瓦片缓存已启用')
      }
    })
    .catch((err) => {
      tileCacheReady = false
      console.warn('[SmartCockpit] IndexedDB 不可用，瓦片缓存已降级', err && err.message)
    })
  return tileCachePromise
}

async function getTileBlob(tileUrl) {
  if (!tileCacheReady) return null
  try {
    const rec = await idb.get(STORE_TILES, tileUrl)
    if (rec && rec.blob && (rec.expireAt === Infinity || rec.expireAt > Date.now())) {
      return rec.blob
    }
    return null
  } catch (_) { return null }
}

async function putTileBlob(tileUrl, blob, contentType) {
  if (!tileCacheReady) return
  try {
    await idb.put(STORE_TILES, tileUrl, {
      blob,
      contentType: contentType || blob.type || 'image/png',
      expireAt: Date.now() + TILE_TTL,
      fetchedAt: Date.now()
    })
  } catch (_) {}
}

const CachedTileLayer = L.TileLayer.extend({
  createTile(coords, done) {
    const tile = L.DomUtil.create('img', 'leaflet-tile')
    tile.decoding = 'async'
    tile.alt = ''
    tile.setAttribute('role', 'presentation')
    const url = this.getTileUrl(coords)
    getTileBlob(url).then((blob) => {
      if (blob) {
        const objUrl = URL.createObjectURL(blob)
        tile.onload = () => {
          try { URL.revokeObjectURL(objUrl) } catch (_) {}
          done(null, tile)
        }
        tile.onerror = () => {
          try { URL.revokeObjectURL(objUrl) } catch (_) {}
          done(new Error('blob-tile-failed'), tile)
        }
        tile.src = objUrl
      } else {
        tile.onload = () => {
          try {
            fetch(url, { mode: 'cors' })
              .then((resp) => (resp && resp.ok && resp.blob ? resp.blob() : null))
              .then((blob) => { if (blob) putTileBlob(url, blob, 'image/png') })
              .catch(() => {})
          } catch (_) {}
          done(null, tile)
        }
        tile.onerror = () => done(new Error('tile-failed'), tile)
        tile.src = url
      }
    })
    return tile
  }
})

const FRAME_COUNT = 200
const totalFrames = FRAME_COUNT
const currentFrame = ref(0)
const playSpeed = ref(1)
const playing = ref(false)
const followSelected = ref(false)

const sliderMarks = {
  0: '起点',
  50: '1/4',
  100: '1/2',
  150: '3/4',
  200: '终点'
}

const weatherTop = reactive({
  temperature: 23,
  windSpeed: 8.5,
  windDirection: 145
})

const taskStat = reactive({
  total: 128,
  inProgress: 42,
  done: 86,
  exception: 2
})

const planCost = reactive({ latest: 2.3, avg: 3.1 })

const CENTER_BJ = { lng: 116.404, lat: 39.915 }

function genPath(seed, radius, altBase) {
  const pts = []
  for (let i = 0; i <= FRAME_COUNT; i++) {
    const t = i / FRAME_COUNT
    const angle = seed + t * Math.PI * 2
    const r = radius * (0.6 + 0.4 * Math.sin(t * Math.PI * 3 + seed))
    const lng = CENTER_BJ.lng + Math.cos(angle) * r + t * 0.01 * Math.cos(seed)
    const lat = CENTER_BJ.lat + Math.sin(angle) * r * 0.8 + t * 0.008 * Math.sin(seed)
    const alt = altBase + 30 * Math.sin(t * Math.PI * 4 + seed)
    pts.push({ lng, lat, alt })
  }
  return pts
}

const droneTemplates = [
  { id: 'UAV-01', model: 'Matrice 300', seed: 0.2, radius: 0.02, altBase: 120, speedBase: 58, task: '运输 #T-2026', status: '飞行中', ownerId: 'user01', team: 'team-a' },
  { id: 'UAV-02', model: 'Mavic 3E', seed: 1.4, radius: 0.015, altBase: 95, speedBase: 45, task: '巡检 #T-2031', status: '飞行中', ownerId: 'flight01', team: 'team-b' },
  { id: 'UAV-03', model: 'Matrice 300', seed: 2.6, radius: 0.018, altBase: 150, speedBase: 62, task: '救援 #T-2045', status: '飞行中', ownerId: 'prod01', team: 'team-a' },
  { id: 'UAV-04', model: 'Mavic 3E', seed: 3.8, radius: 0.022, altBase: 80, speedBase: 48, task: '巡检 #T-2052', status: '飞行中', ownerId: 'test01', team: 'team-c' },
  { id: 'UAV-05', model: 'Inspire 3', seed: 5.0, radius: 0.012, altBase: 200, speedBase: 70, task: '侦察 #T-2060', status: '暂停', ownerId: 'deploy01', team: 'team-c' },
  { id: 'UAV-06', model: 'Matrice 300', seed: 0.8, radius: 0.025, altBase: 110, speedBase: 52, task: '运输 #T-2078', status: '异常', ownerId: 'admin01', team: 'team-a' }
]

const drones = ref(
  droneTemplates.map((d, idx) => {
    const path = genPath(d.seed, d.radius, d.altBase)
    const p0 = path[0]
    return {
      id: d.id,
      model: d.model,
      battery: 85 - idx * 8,
      status: d.status,
      task: d.task,
      altitude: Math.round(p0.alt),
      speed: d.speedBase,
      vSpeed: 0,
      heading: 0,
      signal: -65 - idx * 3,
      batteryTemp: 38 + idx,
      eta: '14:58',
      lng: p0.lng,
      lat: p0.lat,
      ownerId: d.ownerId,
      team: d.team,
      path
    }
  })
)

const visibleDrones = computed(() => drones.value.filter(d => _canSeeDrone(d.ownerId, d.team)))

const selectedDrone = ref(drones.value[0])

const noFlyZones = ref([
  { name: '首都机场', type: '民航机场', center: { lng: 116.58, lat: 40.08 }, radius: 0.025, height: 500 },
  { name: '大兴机场跑道', type: '机场跑道', center: { lng: 116.38, lat: 39.51 }, radius: 0.02, height: 400 },
  { name: '西郊军事基地', type: '军事基地', center: { lng: 116.27, lat: 39.95 }, radius: 0.012, height: 600 },
  { name: '朝阳区雷暴区', type: '危险天气', center: { lng: 116.48, lat: 39.93 }, radius: 0.015, height: 300 }
])

function getBatteryColor(percent) {
  if (percent > 60) return '#67C23A'
  if (percent > 30) return '#E6A23C'
  return '#F56C6C'
}

function getDroneStatusTag(status) {
  const map = {
    '飞行中': { type: 'success' },
    '暂停': { type: 'warning' },
    '异常': { type: 'danger' },
    '待命': { type: 'info' },
    '维护': { type: 'warning' },
    '离线': { type: 'danger' }
  }
  return map[status] || { type: 'info' }
}

function getDroneStatusColor(status) {
  const map = {
    '飞行中': Cesium ? Cesium.Color.LIME : '#67C23A',
    '暂停': Cesium ? Cesium.Color.YELLOW : '#E6A23C',
    '异常': Cesium ? Cesium.Color.RED : '#F56C6C',
    '待命': Cesium ? Cesium.Color.CYAN : '#40E0FF'
  }
  return map[status] || (Cesium ? Cesium.Color.CYAN : '#40E0FF')
}

function tableRowClassName({ rowIndex }) {
  return rowIndex % 2 === 0 ? 'row-even' : 'row-odd'
}

function formatReplayTime(frame) {
  const totalSec = frame * 10
  const hh = String(Math.floor(totalSec / 3600)).padStart(2, '0')
  const mm = String(Math.floor((totalSec % 3600) / 60)).padStart(2, '0')
  const ss = String(totalSec % 60).padStart(2, '0')
  return `${hh}:${mm}:${ss}`
}

// ============ Cesium / Leaflet ============
const mapContainerRef = ref(null)
const useCesium = ref(false)
let viewer = null
let leafletMap = null
let leafletDroneMarkers = []
let leafletPathLayers = []
let leafletNoFlyLayers = []
let cesiumDroneEntities = []
let cesiumNoFlyEntities = []

function centerTo(viewerOrMap, lng, lat, altOrZoom, use3D) {
  if (use3D && viewerOrMap && viewerOrMap.camera) {
    viewerOrMap.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(lng, lat, altOrZoom || 1500),
      duration: 1.2
    })
  } else if (!use3D && viewerOrMap && viewerOrMap.setView) {
    viewerOrMap.setView([lat, lng], altOrZoom || 12, { animate: true, duration: 1 })
  }
}

function flyToNoFlyZone(zone) {
  if (useCesium.value && viewer) {
    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(zone.center.lng, zone.center.lat, zone.height + 800),
      duration: 1.5
    })
  } else if (leafletMap) {
    leafletMap.setView([zone.center.lat, zone.center.lng], 13, { animate: true, duration: 1 })
  }
}

function resetView() {
  if (useCesium.value && viewer) {
    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(CENTER_BJ.lng, CENTER_BJ.lat, 3000),
      orientation: {
        heading: 0.0,
        pitch: Cesium.Math.toRadians(-45),
        roll: 0.0
      },
      duration: 1.5
    })
  } else if (leafletMap) {
    leafletMap.setView([CENTER_BJ.lat, CENTER_BJ.lng], 12, { animate: true, duration: 1 })
  }
}

function onDroneRowClick(row) {
  selectedDrone.value = row
  const p = row.path[currentFrame.value] || row.path[row.path.length - 1]
  if (useCesium.value && viewer) {
    viewer.camera.flyTo({
      destination: Cesium.Cartesian3.fromDegrees(p.lng, p.lat, row.altitude + 400),
      orientation: {
        heading: Cesium.Math.toRadians(row.heading || 0),
        pitch: Cesium.Math.toRadians(-30),
        roll: 0.0
      },
      duration: 1.2
    })
  } else if (leafletMap) {
    leafletMap.setView([p.lat, p.lng], 14, { animate: true, duration: 1 })
  }
}

// ============ Leaflet 降级 ============
function initLeaflet() {
  if (typeof L === 'undefined') {
    console.warn('[SmartCockpit] Leaflet 未加载')
    return
  }
  leafletMap = L.map(mapContainerRef.value, {
    zoomControl: true,
    attributionControl: false
  }).setView([CENTER_BJ.lat, CENTER_BJ.lng], 12)

  new CachedTileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    subdomains: 'abc',
    maxZoom: 19
  }).addTo(leafletMap)

  for (const zone of noFlyZones.value) {
    const circle = L.circle([zone.center.lat, zone.center.lng], {
      radius: zone.radius * 111000,
      color: '#F56C6C',
      weight: 2,
      fillColor: '#F56C6C',
      fillOpacity: 0.25,
      dashArray: '6, 4'
    }).bindTooltip(zone.name).addTo(leafletMap)
    leafletNoFlyLayers.push(circle)
  }

  for (const d of visibleDrones.value) {
    const latlngs = d.path.map((p) => [p.lat, p.lng])
    const pathLine = L.polyline(latlngs, { color: '#40E0FF', weight: 2, opacity: 0.6 }).addTo(leafletMap)
    leafletPathLayers.push(pathLine)

    const color = getDroneStatusColor(d.status)
    const icon = L.divIcon({
      className: 'leaflet-drone-icon',
      html: `<div style="width:14px;height:14px;border-radius:50%;background:${color};border:2px solid #fff;box-shadow:0 0 8px ${color};"></div>`,
      iconSize: [14, 14],
      iconAnchor: [7, 7]
    })
    const marker = L.marker([d.path[0].lat, d.path[0].lng], { icon }).bindTooltip(d.id).addTo(leafletMap)
    marker.on('click', () => {
      selectedDrone.value = d
    })
    leafletDroneMarkers.push(marker)
  }

  nextTick(() => leafletMap && leafletMap.invalidateSize())
}

// ============ Cesium 初始化 ============
function initCesium() {
  if (typeof Cesium === 'undefined') {
    useCesium.value = false
    initLeaflet()
    return
  }
  useCesium.value = true

  Cesium.Ion.defaultAccessToken = ''

  try {
    const imagery = new Cesium.UrlTemplateImageryProvider({
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      subdomains: ['a', 'b', 'c'],
      maximumLevel: 19
    })

    // ========== IndexedDB 瓦片缓存：拦截 requestImage ==========
    const originalRequestImage = imagery.requestImage.bind(imagery)
    imagery.requestImage = function (x, y, level, request) {
      const url = `https://a.tile.openstreetmap.org/${level}/${x}/${y}.png`
      // 先查 IndexedDB
      return getTileBlob(url).then((blob) => {
        if (blob) {
          return new Promise((resolve, reject) => {
            const objUrl = URL.createObjectURL(blob)
            const img = new Image()
            img.onload = () => {
              try { URL.revokeObjectURL(objUrl) } catch (_) {}
              resolve(img)
            }
            img.onerror = () => {
              try { URL.revokeObjectURL(objUrl) } catch (_) {}
              // 降级：走原实现
              originalRequestImage(x, y, level, request).then(resolve).catch(reject)
            }
            img.src = objUrl
          })
        }
        // 未命中 → 走原实现，成功后把 Blob 写入 IndexedDB
        return originalRequestImage(x, y, level, request).then((img) => {
          try {
            fetch(url, { mode: 'cors' })
              .then((resp) => (resp && resp.ok && resp.blob ? resp.blob() : null))
              .then((b) => { if (b) putTileBlob(url, b, 'image/png') })
              .catch(() => {})
          } catch (_) {}
          return img
        })
      })
    }

    viewer = new Cesium.Viewer(mapContainerRef.value, {
      animation: false,
      timeline: false,
      baseLayerPicker: false,
      geocoder: false,
      homeButton: true,
      sceneModePicker: true,
      navigationHelpButton: false,
      infoBox: false,
      selectionIndicator: false,
      fullscreenButton: true,
      imageryProvider: imagery
    })
  } catch (e) {
    console.warn('[SmartCockpit] Cesium 初始化失败，降级为 Leaflet', e)
    useCesium.value = false
    initLeaflet()
    return
  }

  viewer.scene.globe.enableLighting = false
  viewer.scene.skyAtmosphere.show = true
  viewer.scene.backgroundColor = Cesium.Color.fromCssColorString('#0a1929')

  // 初始相机
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(CENTER_BJ.lng, CENTER_BJ.lat, 3000),
    orientation: {
      heading: 0.0,
      pitch: Cesium.Math.toRadians(-45),
      roll: 0.0
    },
    duration: 1.5
  })

  // 随机建筑物 (Cube)
  const buildingCount = 80
  for (let i = 0; i < buildingCount; i++) {
    const lng = CENTER_BJ.lng + (Math.random() - 0.5) * 0.08
    const lat = CENTER_BJ.lat + (Math.random() - 0.5) * 0.06
    const h = 40 + Math.random() * 120
    viewer.entities.add({
      position: Cesium.Cartesian3.fromDegrees(lng, lat, h / 2),
      box: {
        dimensions: new Cesium.Cartesian3(40 + Math.random() * 40, 40 + Math.random() * 40, h),
        material: Cesium.Color.fromCssColorString('#2a4868').withAlpha(0.6),
        outline: true,
        outlineColor: Cesium.Color.fromCssColorString('#40E0FF').withAlpha(0.5)
      }
    })
  }

  // 禁飞区
  for (const zone of noFlyZones.value) {
    const points = []
    const segments = 32
    for (let i = 0; i < segments; i++) {
      const a = (i / segments) * Math.PI * 2
      points.push(zone.center.lng + Math.cos(a) * zone.radius)
      points.push(zone.center.lat + Math.sin(a) * zone.radius)
    }
    const entity = viewer.entities.add({
      name: zone.name,
      polygon: {
        hierarchy: Cesium.Cartesian3.fromDegreesArray(points),
        material: Cesium.Color.RED.withAlpha(0.35),
        extrudedHeight: zone.height,
        outline: true,
        outlineColor: Cesium.Color.RED
      },
      position: Cesium.Cartesian3.fromDegrees(zone.center.lng, zone.center.lat, zone.height),
      label: {
        text: zone.name,
        font: '12px sans-serif',
        fillColor: Cesium.Color.WHITE,
        outlineColor: Cesium.Color.RED,
        outlineWidth: 2,
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
        pixelOffset: new Cesium.Cartesian2(0, -10),
        showBackground: true,
        backgroundColor: Cesium.Color.fromCssColorString('#0a1929').withAlpha(0.7)
      }
    })
    cesiumNoFlyEntities.push(entity)
  }

  // 无人机实体 + 轨迹
  for (const d of drones.value) {
    const positions = d.path.map((p) => Cesium.Cartesian3.fromDegrees(p.lng, p.lat, p.alt))
    const color = getDroneStatusColor(d.status)

    // 尾迹 polyline
    const trailEntity = viewer.entities.add({
      polyline: {
        positions: positions,
        width: 2,
        material: new Cesium.PolylineGlowMaterialProperty({
          glowPower: 0.2,
          color: color instanceof Cesium.Color ? color : Cesium.Color.fromCssColorString(color)
        }),
        clampToGround: false
      }
    })
    cesiumDroneEntities.push(trailEntity)

    // 动态点 / 标签
    const property = new Cesium.SampledPositionProperty()
    const start = Cesium.JulianDate.now()
    d.path.forEach((p, i) => {
      const t = Cesium.JulianDate.addSeconds(start, i * 10, new Cesium.JulianDate())
      property.addSample(t, Cesium.Cartesian3.fromDegrees(p.lng, p.lat, p.alt))
    })
    property.setInterpolationOptions({
      interpolationDegree: 2,
      interpolationAlgorithm: Cesium.LagrangePolynomialApproximation
    })

    const pointEntity = viewer.entities.add({
      id: d.id,
      name: d.id,
      position: positions[0],
      point: {
        pixelSize: 12,
        color: color instanceof Cesium.Color ? color : Cesium.Color.fromCssColorString(color),
        outlineColor: Cesium.Color.WHITE,
        outlineWidth: 2,
        disableDepthTestDistance: Number.POSITIVE_INFINITY
      },
      label: {
        text: d.id,
        font: '12px sans-serif',
        fillColor: Cesium.Color.WHITE,
        outlineColor: Cesium.Color.BLACK,
        outlineWidth: 2,
        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
        pixelOffset: new Cesium.Cartesian2(0, -18),
        showBackground: true,
        backgroundColor: Cesium.Color.fromCssColorString('#0a1929').withAlpha(0.8),
        disableDepthTestDistance: Number.POSITIVE_INFINITY
      },
      _droneRef: d,
      _positionProperty: property,
      _startTime: start
    })
    cesiumDroneEntities.push(pointEntity)
  }

  // 点击交互
  const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas)
  handler.setInputAction((click) => {
    const picked = viewer.scene.pick(click.position)
    if (Cesium.defined(picked) && picked.id && picked.id._droneRef) {
      selectedDrone.value = picked.id._droneRef
      const d = picked.id._droneRef
      const p = d.path[currentFrame.value] || d.path[0]
      if (followSelected.value) {
        viewer.camera.flyTo({
          destination: Cesium.Cartesian3.fromDegrees(p.lng, p.lat, d.altitude + 400),
          duration: 1.0
        })
      }
    }
  }, Cesium.ScreenSpaceEventType.LEFT_CLICK)
  viewer._clickHandler = handler
}

// ============ 实时推送 (模拟 WebSocket) ============
let pushTimer = null
let playTimer = null
let resizeObserver = null

const updateStateRaf = batchRaf((frame) => {
  applyFrame(frame)
})

const cockpitStream = createThrottledStream(100, (snapshot) => {
  const latest = snapshot[snapshot.length - 1]
  if (!latest) return
  if (latest.frame != null && currentFrame.value !== latest.frame) {
    currentFrame.value = latest.frame
  }
  updateStateRaf(currentFrame.value)
})

function advanceFrame() {
  currentFrame.value = (currentFrame.value + 1) % (FRAME_COUNT + 1)
}

function applyFrame(frame) {
  const idx = Math.min(Math.max(frame, 0), FRAME_COUNT)

  drones.value.forEach((d, di) => {
    const p = d.path[idx]
    d.lng = p.lng
    d.lat = p.lat
    d.altitude = Math.round(p.alt)

    const prev = d.path[Math.max(0, idx - 1)]
    const dx = p.lng - prev.lng
    const dy = p.lat - prev.lat
    d.heading = Math.round((Math.atan2(dx, dy) * 180 / Math.PI + 360) % 360)
    d.vSpeed = +(p.alt - prev.alt).toFixed(2)
    d.battery = Math.max(0, d.battery - 0.02)

    // 状态告警（节流：同一飞机同一类型只报一次）
    if (d.battery < 20 && !droneAlertSent.has(d.id + ':battery')) {
      droneAlertSent.add(d.id + ':battery')
      notificationStore.pushWithDesktop({
        type: 'warning',
        title: '无人机电量告警',
        message: `${d.id}（${d.model}）电量已低于 20%，建议尽快返航`,
        source: 'uav'
      })
    }
    if (d.signal < -85 && !droneAlertSent.has(d.id + ':signal')) {
      droneAlertSent.add(d.id + ':signal')
      notificationStore.pushWithDesktop({
        type: 'danger',
        title: '无人机信号丢失',
        message: `${d.id} 信号强度 ${d.signal} dBm，疑似通讯中断`,
        source: 'uav'
      })
    }
    if (d.status === '异常' && !droneAlertSent.has(d.id + ':status')) {
      droneAlertSent.add(d.id + ':status')
      notificationStore.pushWithDesktop({
        type: 'danger',
        title: '无人机状态异常',
        message: `${d.id}（任务：${d.task}）状态为异常`,
        source: 'uav'
      })
    }

    // 禁飞区入侵判断
    for (const zone of noFlyZones.value) {
      const dLat = d.lat - zone.center.lat
      const dLng = d.lng - zone.center.lng
      const distance = Math.sqrt(dLat * dLat + dLng * dLng)
      if (distance < zone.radius && !droneAlertSent.has(d.id + ':zone:' + zone.name)) {
        droneAlertSent.add(d.id + ':zone:' + zone.name)
        notificationStore.pushWithDesktop({
          type: 'danger',
          title: '禁飞区入侵告警',
          message: `${d.id} 已进入 "${zone.name}"，请立即介入`,
          source: 'uav'
        })
      }
    }
  })

  if (useCesium.value && viewer) {
    let i = 0
    for (const entity of cesiumDroneEntities) {
      if (entity._droneRef) {
        const d = entity._droneRef
        const pos = Cesium.Cartesian3.fromDegrees(d.lng, d.lat, d.altitude)
        entity.position = pos
        i++
      }
    }
    if (followSelected.value && selectedDrone.value) {
      const d = selectedDrone.value
      viewer.camera.lookAt(
        Cesium.Cartesian3.fromDegrees(d.lng, d.lat, d.altitude),
        new Cesium.HeadingPitchRange(
          Cesium.Math.toRadians(d.heading || 0),
          Cesium.Math.toRadians(-35),
          600
        )
      )
    }
  } else if (leafletMap) {
    drones.value.forEach((d, di) => {
      if (leafletDroneMarkers[di]) {
        leafletDroneMarkers[di].setLatLng([d.lat, d.lng])
      }
    })
  }
}

function startPush() {
  stopPush()
  pushTimer = setInterval(() => {
    if (!playing.value) {
      advanceFrame()
    }
    cockpitStream.push({ ts: Date.now(), frame: currentFrame.value })
  }, 100)
}

function stopPush() {
  if (pushTimer) clearInterval(pushTimer)
  pushTimer = null
  cockpitStream.flushNow()
}

function togglePlay() {
  playing.value = !playing.value
  if (playing.value) {
    if (playTimer) clearInterval(playTimer)
    playTimer = setInterval(() => {
      advanceFrame()
      applyFrame(currentFrame.value)
    }, Math.round(100 / playSpeed.value))
  } else {
    if (playTimer) clearInterval(playTimer)
    playTimer = null
  }
}

watch(playSpeed, () => {
  if (playing.value) {
    if (playTimer) clearInterval(playTimer)
    playTimer = setInterval(() => {
      advanceFrame()
      applyFrame(currentFrame.value)
    }, Math.round(100 / playSpeed.value))
  }
})

watch(currentFrame, (v) => {
  applyFrame(v)
})

function resetReplay() {
  playing.value = false
  currentFrame.value = 0
  applyFrame(0)
}

function toggleFollow() {
  followSelected.value = !followSelected.value
}

// ============ 生命周期 ============
onMounted(async () => {
  initTileCache()
  await nextTick()
  initCesium()
  applyFrame(0)
  startPush()

  if (mapContainerRef.value && typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => {
      if (viewer) viewer.resize()
      if (leafletMap) leafletMap.invalidateSize()
    })
    resizeObserver.observe(mapContainerRef.value)
  }
})

onUnmounted(() => {
  stopPush()
  cockpitStream.cancel()
  if (playTimer) clearInterval(playTimer)
  playTimer = null
  if (viewer && viewer._clickHandler) {
    try { viewer._clickHandler.destroy() } catch (e) {}
  }
  if (viewer) {
    try { viewer.entities.removeAll() } catch (e) {}
    try { viewer.destroy() } catch (e) {}
  }
  viewer = null
  cesiumDroneEntities = []
  cesiumNoFlyEntities = []
  if (leafletMap) {
    try { leafletMap.remove() } catch (e) {}
  }
  leafletMap = null
  leafletDroneMarkers = []
  leafletPathLayers = []
  leafletNoFlyLayers = []
  if (resizeObserver) {
    try { resizeObserver.disconnect() } catch (e) {}
  }
})
</script>

<style scoped>
.cockpit {
  padding: 16px 20px 20px;
  background: linear-gradient(135deg, #0a1929 0%, #051220 50%, #0a1929 100%);
  min-height: 100vh;
  color: #E6F1FF;
}

.demo-alert {
  margin-bottom: 16px;
}

/* 顶部状态条 */
.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  margin-bottom: 12px;
  background: rgba(64, 158, 255, 0.08);
  border: 1px solid rgba(64, 158, 255, 0.2);
  border-radius: 10px;
  gap: 20px;
}

.status-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.status-left h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #E6F1FF;
  letter-spacing: 1px;
  white-space: nowrap;
}

.cockpit-icon {
  font-size: 24px;
  color: #40E0FF;
  text-shadow: 0 0 12px rgba(64, 224, 255, 0.6);
}

.status-right {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  flex: 1;
  max-width: 100%;
}

.status-card {
  border-radius: 10px;
  border: 1px solid rgba(64, 158, 255, 0.18) !important;
  background: rgba(10, 25, 41, 0.7) !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
  transition: transform 0.2s, box-shadow 0.2s;
}

.status-card:hover {
  box-shadow: 0 4px 14px rgba(64, 224, 255, 0.2);
}

.status-card :deep(.el-card__body) {
  padding: 10px 14px;
}

.stat-label {
  font-size: 12px;
  color: #8FA4C4;
  margin-bottom: 6px;
  font-weight: 500;
}

.stat-value {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 18px;
  font-weight: 600;
  color: #E6F1FF;
  font-family: 'Courier New', monospace;
  flex-wrap: wrap;
}

.stat-value-divider {
  color: #4A6B8C;
  font-weight: 400;
  font-size: 14px;
}

.weather-value span {
  color: #40E0FF;
  text-shadow: 0 0 6px rgba(64, 224, 255, 0.4);
}

.stat-hint {
  margin-top: 6px;
  font-size: 11px;
  color: #6B7C95;
}

.task-stat-card .task-progress-wrap { margin: 2px 0 8px; }

.task-progress :deep(.el-progress__text) {
  color: #B7C9E0;
  font-size: 12px;
  font-family: 'Courier New', monospace;
}

.task-mini-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4px;
  margin-top: 2px;
}

.task-mini-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 4px 2px;
  background: rgba(64, 158, 255, 0.05);
  border-radius: 4px;
}

.task-mini-label {
  font-size: 11px;
  color: #8FA4C4;
  margin-bottom: 2px;
}

.task-mini-value {
  font-size: 15px;
  font-weight: 600;
  color: #E6F1FF;
  font-family: 'Courier New', monospace;
}

.task-mini-value.primary {
  color: #40E0FF;
  text-shadow: 0 0 6px rgba(64, 224, 255, 0.4);
}

.task-mini-value.success { color: #67C23A; }
.task-mini-value.danger { color: #F56C6C; }

.plan-values {
  display: flex;
  justify-content: space-around;
  margin: 6px 0;
}

.plan-value-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.plan-value-label {
  font-size: 12px;
  color: #8FA4C4;
  margin-bottom: 2px;
}

.plan-value-num {
  font-size: 22px;
  font-weight: 700;
  color: #40E0FF;
  font-family: 'Courier New', monospace;
  text-shadow: 0 0 6px rgba(64, 224, 255, 0.4);
}

.plan-value-num small {
  font-size: 12px;
  color: #8FA4C4;
  margin-left: 2px;
  font-weight: 400;
}

/* 主体行 */
.main-row {
  margin-bottom: 16px;
  display: flex;
  align-items: stretch;
}

.dark-card {
  background: rgba(10, 25, 41) !important;
  border: 1px solid rgba(64, 158, 255, 0.2) !important;
  border-radius: 10px;
  transition: box-shadow 0.2s;
}

.dark-card:hover {
  box-shadow: 0 4px 18px rgba(64, 224, 255, 0.15);
}

.dark-card :deep(.el-card__header) {
  background: rgba(64, 158, 255, 0.06);
  border-bottom: 1px solid rgba(64, 158, 255, 0.2);
  padding: 10px 14px;
}

.dark-card :deep(.el-card__body) {
  padding: 12px 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #E6F1FF;
  font-size: 14px;
}

.cockpit-card {
  height: 100%;
}

/* 地图 */
.map-card :deep(.el-card__body) { padding: 0; position: relative; }

.map-container {
  position: relative;
  width: 100%;
  height: 640px;
  background: radial-gradient(circle at center, #0d2540 0%, #051220 100%);
}

.map-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mode-tag { font-family: 'Courier New', monospace; }

.map-degrade-hint {
  position: absolute;
  bottom: 10px;
  left: 10px;
  padding: 6px 12px;
  background: rgba(245, 108, 108, 0.15);
  border: 1px solid rgba(245, 108, 108, 0.5);
  color: #F5C2C2;
  font-size: 12px;
  border-radius: 6px;
  z-index: 1000;
}

/* 右侧面板 */
.main-right-col { display: flex; flex-direction: column; gap: 12px; }

.side-card { margin-bottom: 0; }

.detail-card {
  :deep(.el-card__body) {
    padding-bottom: 14px;
  }
}

.detail-body { padding: 2px 0; }

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  padding: 6px 8px;
  background: rgba(64, 158, 255, 0.05);
  border-radius: 6px;
}

.detail-item.wide { grid-column: 1 / -1; }

.detail-label {
  font-size: 11px;
  color: #8FA4C4;
  margin-bottom: 2px;
}

.detail-value {
  font-size: 14px;
  font-weight: 600;
  color: #E6F1FF;
}

.detail-value.highlight {
  color: #40E0FF;
  text-shadow: 0 0 4px rgba(64, 224, 255, 0.4);
}

.mono { font-family: 'Courier New', monospace; }

.detail-empty {
  text-align: center;
  color: #6B7C95;
  padding: 24px 0;
  font-size: 12px;
}

/* 禁飞区列表 */
.nofly-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 150px;
  overflow-y: auto;
}

.nofly-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  background: rgba(245, 108, 108, 0.08);
  border: 1px solid rgba(245, 108, 108, 0.25);
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
}

.nofly-item:hover {
  background: rgba(245, 108, 108, 0.2);
  transform: translateX(2px);
}

.nofly-name {
  font-size: 13px;
  color: #E6F1FF;
  font-weight: 500;
}

.nofly-type {
  font-size: 11px;
  color: #F56C6C;
  padding: 2px 6px;
  background: rgba(245, 108, 108, 0.15);
  border-radius: 4px;
}

/* 回放控制 */
.replay-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.replay-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #B7C9E0;
}

.replay-label {
  color: #8FA4C4;
  flex-shrink: 0;
}

.replay-value {
  color: #40E0FF;
  font-family: 'Courier New', monospace;
  font-weight: 600;
}

/* 底部时间轴 */
.timeline-card { margin-bottom: 0; }

.timeline-body {
  padding: 4px 10px 6px;
}

.timeline-hint {
  font-size: 12px;
  color: #8FA4C4;
  font-weight: normal;
}

.replay-slider :deep(.el-slider__runway) {
  background-color: rgba(64, 158, 255, 0.2);
}

.replay-slider :deep(.el-slider__bar) {
  background: linear-gradient(90deg, #40E0FF, #79EBFF);
  box-shadow: 0 0 6px rgba(64, 224, 255, 0.5);
}

.replay-slider :deep(.el-slider__button) {
  border-color: #40E0FF;
  box-shadow: 0 0 8px rgba(64, 224, 255, 0.6);
}

.replay-slider :deep(.el-slider__marks-text) {
  color: #8FA4C4;
  font-size: 11px;
}

.timeline-bar {
  margin-top: 8px;
  height: 6px;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.timeline-track {
  height: 100%;
  background: linear-gradient(90deg, #40E0FF, #79EBFF);
  box-shadow: 0 0 8px rgba(64, 224, 255, 0.5);
  border-radius: 4px;
  transition: width 0.1s linear;
}

/* 无人机表格 */
.drone-table :deep(.el-table) {
  background: transparent;
  color: #B7C9E0;
  font-size: 12px;
}

.drone-table :deep(.el-table tr) {
  background: transparent;
}

.drone-table :deep(.el-table td),
.drone-table :deep(.el-table th.el-table__cell) {
  background: transparent;
  border-bottom: 1px solid rgba(64, 158, 255, 0.08);
  padding: 8px 4px;
}

.drone-table :deep(.el-table th.el-table__cell) {
  background: rgba(64, 158, 255, 0.05);
  color: #8FA4C4;
  font-weight: 500;
  font-size: 11px;
}

.drone-table :deep(.el-table .row-odd td) {
  background: rgba(64, 158, 255, 0.03);
}

.drone-table :deep(.el-table__body tr:hover > td) {
  background: rgba(64, 158, 255, 0.08) !important;
}

.drone-table :deep(.el-table__body tr.current-row > td) {
  background: rgba(64, 224, 255, 0.12) !important;
}

@media (max-width: 1280px) {
  .main-row { flex-wrap: wrap !important; }
  .main-left-col,
  .main-right-col {
    flex: 0 0 100% !important;
    max-width: 100% !important;
  }
  .map-container { height: 480px; }
  .status-right { grid-template-columns: 1fr; }
}

@media (max-width: 768px) {
  .status-bar { flex-direction: column; align-items: stretch; gap: 12px; }
  .map-container { height: 280px; }
  .detail-grid { grid-template-columns: 1fr; }
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
  :deep(.el-table-wrapper) {
    overflow-x: auto;
  }
  :deep(.cockpit-chart),
  .cockpit-chart,
  .chart-container {
    height: 280px !important;
  }
}
</style>

<style>
.cockpit .leaflet-container {
  background: #0a1929;
  width: 100%;
  height: 100%;
  font-family: inherit;
}

.cockpit .cesium-viewer-bottom { display: none !important; }
</style>
