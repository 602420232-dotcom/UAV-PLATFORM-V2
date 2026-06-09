<template>
  <div class="weather">
    <el-alert
      type="warning"
      show-icon
      :closable="false"
      title="演示模式提示"
      description="当前页面展示的所有气象数据（温度/风场/气压/多模型误差等）均为前端模拟数据，真实环境下请在 API 配置模块中对接气象服务。"
      class="demo-alert"
    />

    <el-tabs v-model="activeTab" class="weather-tabs" @tab-change="handleTabChangeThrottled">
      <!-- Tab 1: 气象概览 -->
      <el-tab-pane :label="t('weather.overview')" name="overview">
        <div class="tab-container">
          <div class="left-panel">
            <el-card shadow="hover" class="control-card">
              <template #header>
                <span class="panel-title">📌 {{ t('weather.region') }}</span>
              </template>
              <el-form label-position="top">
                <el-form-item :label="t('weather.region')">
                  <el-radio-group v-model="overviewRegion" size="default">
                    <el-radio-button label="华东" />
                    <el-radio-button label="华北" />
                    <el-radio-button label="华南" />
                  </el-radio-group>
                  <div class="location-btn-wrapper">
                    <el-button
                      type="primary"
                      size="small"
                      :loading="isLocating"
                      @click="fetchCurrentLocation"
                    >
                      <el-icon><MapPin /></el-icon>
                      {{ t('weather.locateMe') }}
                    </el-button>
                    <div v-if="currentLocation" class="location-info">
                      <span class="location-label">{{ t('weather.currentLocation') }}:</span>
                      <span class="location-value">{{ currentLocation.address?.formatted || (currentLocation.position ? `${currentLocation.position.latitude.toFixed(4)}, ${currentLocation.position.longitude.toFixed(4)}` : '未知位置') }}</span>
                    </div>
                    <div v-if="locationError" class="location-error">
                      <el-alert type="error" :message="locationError" show-icon :closable="false" />
                    </div>
                  </div>
                </el-form-item>
                <el-form-item :label="t('weather.forecastHour')">
                  <el-slider v-model="overviewHour" :min="0" :max="24" :step="6" :marks="{0: '0h', 6: '6h', 12: '12h', 18: '18h', 24: '24h'}" show-stops />
                </el-form-item>
                <el-form-item :label="t('weather.altitude')">
                  <el-select v-model="overviewAltitude" style="width: 100%">
                    <el-option :value="10" :label="t('weather.altitude10m')" />
                    <el-option :value="100" :label="t('weather.altitude100m')" />
                    <el-option :value="500" :label="t('weather.altitude500m')" />
                  </el-select>
                </el-form-item>
              </el-form>
            </el-card>
            <el-card shadow="hover" class="info-card">
              <template #header>
                <span class="panel-title">🪧 {{ t('common.info') }}</span>
              </template>
              <div class="info-text">
                {{ t('weather.infoText', { region: overviewRegion, hour: overviewHour }) }}
              </div>
            </el-card>
          </div>

          <div class="right-panel">
            <el-row :gutter="16" class="metric-row">
              <el-col :span="6" v-for="(m, idx) in overviewMetrics" :key="idx">
                <el-card shadow="hover" class="metric-card" :class="'metric-' + m.key">
                  <div class="metric-header">
                    <span class="metric-icon">{{ m.icon }}</span>
                    <span class="metric-label">{{ t(`weather.${m.key}`) || m.label }}</span>
                  </div>
                  <div class="metric-body">
                    <span class="metric-value">{{ m.value }}</span>
                    <span class="metric-unit">{{ m.unit }}</span>
                    <span class="metric-trend" :class="m.trendClass">{{ m.trend }}</span>
                  </div>
                </el-card>
              </el-col>
            </el-row>

            <el-card shadow="hover" class="chart-card">
              <template #header>
                <div class="card-header">
                  <span>📈 过去 24 小时 温度 / 风速变化</span>
                </div>
              </template>
              <div ref="overviewChartRef" class="echarts-box"></div>
            </el-card>
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab 2: 风场矢量图 -->
      <el-tab-pane :label="t('weather.windField')" name="wind">
        <div class="tab-container">
          <div class="left-panel">
            <el-card shadow="hover" class="control-card">
              <template #header>
                <span class="panel-title">🎛️ {{ t('weather.windField') }}</span>
              </template>
              <el-form label-position="top">
                <el-form-item :label="t('weather.region')">
                  <el-radio-group v-model="windRegion" @change="redrawWindThrottled">
                    <el-radio-button label="华东" />
                    <el-radio-button label="华北" />
                    <el-radio-button label="华南" />
                  </el-radio-group>
                </el-form-item>
                <el-form-item :label="t('weather.timeStep')">
                  <el-radio-group v-model="windStep" @change="redrawWindThrottled">
                    <el-radio-button :label="0">0h</el-radio-button>
                    <el-radio-button :label="6">6h</el-radio-button>
                    <el-radio-button :label="12">12h</el-radio-button>
                    <el-radio-button :label="24">24h</el-radio-button>
                  </el-radio-group>
                </el-form-item>
                <el-form-item :label="t('weather.arrowDensity')">
                  <el-slider v-model="windDensity" :min="1" :max="4" :step="1" show-stops :marks="{1:t('weather.sparse'),2:t('weather.normal'),3:t('weather.dense'),4:t('weather.veryDense')}" @change="redrawWindThrottled" />
                </el-form-item>
              </el-form>
            </el-card>
          </div>
          <div class="right-panel">
            <div class="map-wrapper">
              <div ref="windMapRef" class="leaflet-map"></div>
              <el-card shadow="always" class="map-legend">
                <div class="legend-title">🚩 {{ t('weather.windSpeedLevel') }} (m/s)</div>
                <div class="legend-item"><span class="legend-dot" style="background:#9ca3af"></span> 0 - 2  {{ t('weather.lightBreeze') }}</div>
                <div class="legend-item"><span class="legend-dot" style="background:#409EFF"></span> 3 - 5  {{ t('weather.gentleWind') }}</div>
                <div class="legend-item"><span class="legend-dot" style="background:#E6A23C"></span> 6 - 8  {{ t('weather.moderateWind') }}</div>
                <div class="legend-item"><span class="legend-dot" style="background:#F56C6C"></span> 9+    {{ t('weather.strongWind') }}</div>
                <el-divider style="margin: 6px 0" />
                <div class="legend-tip">{{ t('weather.windArrowTip') }}</div>
              </el-card>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab 3: 气象热力图 -->
      <el-tab-pane :label="t('weather.heatMap')" name="heat">
        <div class="tab-container">
          <div class="left-panel">
            <el-card shadow="hover" class="control-card">
              <template #header>
                <span class="panel-title">🔥 {{ t('weather.heatParams') }}</span>
              </template>
              <el-form label-position="top">
                <el-form-item :label="t('weather.variable')">
                  <el-radio-group v-model="heatVar" @change="redrawHeatThrottled">
                    <el-radio-button label="temperature">{{ t('weather.temperature') }}</el-radio-button>
                    <el-radio-button label="pressure">{{ t('weather.pressure') }}</el-radio-button>
                    <el-radio-button label="precipitation">{{ t('weather.precipitation') }}</el-radio-button>
                    <el-radio-button label="turbulence">{{ t('weather.turbulence') }}</el-radio-button>
                  </el-radio-group>
                </el-form-item>
                <el-form-item :label="t('weather.layerOpacity')">
                  <el-slider v-model="heatOpacity" :min="0.3" :max="1.0" :step="0.05" @input="redrawHeatThrottled" />
                </el-form-item>
                <el-form-item :label="t('weather.hotspotRadius')">
                  <el-slider v-model="heatRadius" :min="10" :max="60" :step="5" @input="redrawHeatThrottled" />
                </el-form-item>
                <el-form-item :label="t('weather.blurRadius')">
                  <el-slider v-model="heatBlur" :min="10" :max="80" :step="5" @input="redrawHeatThrottled" />
                </el-form-item>
              </el-form>
            </el-card>
          </div>
          <div class="right-panel">
            <div class="map-wrapper">
              <div ref="heatMapRef" class="leaflet-map"></div>
              <el-card shadow="always" class="map-legend">
                <div class="legend-title">🎨 {{ t('weather.variableIntensity') }}</div>
                <div class="legend-item"><span class="legend-dot" style="background:#00f"></span> {{ t('weather.low') }}</div>
                <div class="legend-item"><span class="legend-dot" style="background:#0ff"></span> {{ t('weather.lower') }}</div>
                <div class="legend-item"><span class="legend-dot" style="background:#ff0"></span> {{ t('weather.medium') }}</div>
                <div class="legend-item"><span class="legend-dot" style="background:#f80"></span> {{ t('weather.higher') }}</div>
                <div class="legend-item"><span class="legend-dot" style="background:#f00"></span> {{ t('weather.high') }}</div>
                <el-divider style="margin: 6px 0" />
                <div class="legend-tip">{{ t('weather.currentVariable') }}: <b>{{ heatVarLabel }}</b></div>
              </el-card>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab 4: 贝叶斯方差场 -->
      <el-tab-pane :label="t('weather.variance')" name="variance">
        <div class="tab-container">
          <div class="left-panel">
            <el-card shadow="hover" class="control-card">
              <template #header>
                <span class="panel-title">📊 {{ t('weather.uncertaintyParams') }}</span>
              </template>
              <el-form label-position="top">
                <el-form-item :label="t('weather.variable')">
                  <el-radio-group v-model="varianceVar" @change="redrawVarianceThrottled">
                    <el-radio-button label="temp">{{ t('weather.tempVariance') }}</el-radio-button>
                    <el-radio-button label="wind">{{ t('weather.windVariance') }}</el-radio-button>
                  </el-radio-group>
                </el-form-item>
                <el-form-item :label="t('weather.timeStep')">
                  <el-radio-group v-model="varianceStep" @change="redrawVarianceThrottled">
                    <el-radio-button :label="0">0h</el-radio-button>
                    <el-radio-button :label="6">6h</el-radio-button>
                    <el-radio-button :label="12">12h</el-radio-button>
                    <el-radio-button :label="24">24h</el-radio-button>
                  </el-radio-group>
                </el-form-item>
              </el-form>
            </el-card>
          </div>
          <div class="right-panel">
            <el-alert
              :title="t('weather.forecastConfidence', { confidence: varianceConfidence })"
              type="info"
              show-icon
              :closable="false"
              class="variance-top-alert"
            />
            <div class="map-wrapper">
              <div ref="varianceMapRef" class="leaflet-map"></div>
              <el-card shadow="always" class="map-legend">
                <div class="legend-title">🎨 {{ t('weather.varianceLevel') }}</div>
                <div class="legend-item"><span class="legend-dot" style="background:#67C23A"></span> {{ t('weather.low') }}</div>
                <div class="legend-item"><span class="legend-dot" style="background:#E6A23C"></span> {{ t('weather.medium') }}</div>
                <div class="legend-item"><span class="legend-dot" style="background:#F56C6C"></span> {{ t('weather.high') }}</div>
                <div class="legend-item"><span class="legend-dot" style="background:#9254DE"></span> {{ t('weather.veryHigh') }}</div>
              </el-card>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab 5: 多模型误差对比 -->
      <el-tab-pane :label="t('weather.comparison')" name="compare">
        <div class="tab-container">
          <div class="left-panel">
            <el-card shadow="hover" class="control-card">
              <template #header>
                <span class="panel-title">⚖️ {{ t('weather.observationVariable') }}</span>
              </template>
              <el-form label-position="top">
                <el-form-item :label="t('weather.selectVariable')">
                  <el-radio-group v-model="compareVar" @change="redrawCompareThrottled">
                    <el-radio-button label="temperature">{{ t('weather.temperature') }}</el-radio-button>
                    <el-radio-button label="wind">{{ t('weather.windSpeed') }}</el-radio-button>
                    <el-radio-button label="pressure">{{ t('weather.pressure') }}</el-radio-button>
                  </el-radio-group>
                </el-form-item>
                <el-form-item :label="t('weather.evaluationRegion')">
                  <el-select v-model="compareRegion" style="width:100%" @change="redrawCompareThrottled">
                    <el-option label="华东" value="华东" />
                    <el-option label="华北" value="华北" />
                    <el-option label="华南" value="华南" />
                  </el-select>
                </el-form-item>
              </el-form>
            </el-card>
          </div>
          <div class="right-panel">
            <el-card shadow="hover" class="chart-card">
              <template #header>
                <div class="card-header">
                  <span>📉 {{ t('weather.modelComparison', { varLabel: compareVarLabel, region: compareRegion }) }}</span>
                </div>
              </template>
              <div ref="compareChartRef" class="echarts-box tall"></div>
            </el-card>

            <el-row :gutter="12" class="compare-stats">
              <el-col :span="6" v-for="(s, i) in compareStats" :key="i">
                <el-card shadow="hover" class="stat-card" :class="{ 'best-card': s.isBest }">
                  <div class="stat-title">
                    <span class="stat-dot" :style="{ background: s.color }"></span>
                    {{ s.name }}
                    <el-tag v-if="s.isBest" type="success" size="small" style="margin-left:6px">最佳</el-tag>
                  </div>
                  <div class="stat-row"><span>平均 RMSE</span><b>{{ s.rmse }}</b></div>
                  <div class="stat-row"><span>平均偏差</span><b>{{ s.bias }}</b></div>
                  <div class="stat-row"><span>样本数</span><b>{{ s.n }}</b></div>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { createThrottledStream, throttled } from '@/utils/performance.js'
import * as echarts from 'echarts'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.heat'
import idb, { STORE_TILES } from '../../utils/indexedDB'
import { useNotificationStore } from '../../stores/notification'
import { getCurrentLocation } from '../../utils/geolocation'

const { t } = useI18n()
const notificationStore = useNotificationStore()
let weatherAlertSent = { wind: false, rain: false }

const currentLocation = ref(null)
const locationError = ref(null)
const isLocating = ref(false)

const TILE_TTL = 30 * 24 * 60 * 60 * 1000 // 30 天

// ========== Tile 缓存工具 ==========
let tileCacheReady = false
let tileCachePromise = null

function initTileCache() {
  if (tileCachePromise) return tileCachePromise
  tileCachePromise = idb.initDB()
    .then(() => {
      tileCacheReady = true
      if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.DEV) {
        console.info('[WeatherView] IndexedDB 瓦片缓存已启用')
      }
    })
    .catch((err) => {
      tileCacheReady = false
      console.warn('[WeatherView] IndexedDB 不可用，瓦片缓存已降级', err && err.message)
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
  } catch (_) {
    return null
  }
}

async function putTileBlob(tileUrl, blob, contentType) {
  if (!tileCacheReady) return
  try {
    const value = {
      blob,
      contentType: contentType || blob.type || 'image/png',
      expireAt: Date.now() + TILE_TTL,
      fetchedAt: Date.now()
    }
    await idb.put(STORE_TILES, tileUrl, value)
  } catch (_) {}
}

// 自定义 TileLayer：命中 IndexedDB 后用 createObjectURL 作为 src
const CachedTileLayer = L.TileLayer.extend({
  createTile(coords, done) {
    const tile = L.DomUtil.create('img', 'leaflet-tile')
    tile.decoding = 'async'
    tile.alt = ''
    tile.setAttribute('role', 'presentation')
    const url = this.getTileUrl(coords)

    // 先尝试 IndexedDB
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
          // 网络成功后写回 IndexedDB（通过再次 fetch 拿 Blob）
          try {
            fetch(url, { mode: 'cors' })
              .then((resp) => {
                if (resp && resp.ok && resp.blob) return resp.blob()
                return null
              })
              .then((blob) => {
                if (blob) putTileBlob(url, blob, 'image/png')
              })
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

// ========== 通用状态 ==========
const activeTab = ref('overview')

// ========== Tab1: 气象概览 ==========
const overviewRegion = ref('华东')
const overviewHour = ref(6)
const overviewAltitude = ref(100)
const overviewChartRef = ref(null)
let overviewChartInstance = null

const overviewMetrics = computed(() => {
  const seed = hashSeed(overviewRegion.value + '|' + overviewHour.value)
  const temp = (22 + pseudoRand(seed) * 12).toFixed(1)
  const wind = (2 + pseudoRand(seed + 1) * 8).toFixed(1)
  const windDir = ['北', '东北', '东', '东南', '南', '西南', '西', '西北'][Math.floor(pseudoRand(seed + 2) * 8)]
  const pressure = Math.round(998 + pseudoRand(seed + 3) * 25)
  const humidity = Math.round(40 + pseudoRand(seed + 4) * 50)
  return [
    { key: 'temp', label: '温度', value: temp, unit: '°C', icon: '🌡️', trend: '+1.2°', trendClass: 'trend-up' },
    { key: 'wind', label: '风速风向', value: wind, unit: 'm/s ' + windDir, icon: '🌬️', trend: '-0.3 m/s', trendClass: 'trend-down' },
    { key: 'pressure', label: '气压', value: pressure, unit: 'hPa', icon: '🎈', trend: '+2 hPa', trendClass: 'trend-up' },
    { key: 'humidity', label: '湿度', value: humidity, unit: '%', icon: '💧', trend: '-3%', trendClass: 'trend-down' }
  ]
})

function checkWeatherAlerts() {
  const wind = +overviewMetrics.value[1].value
  if (wind > 15 && !weatherAlertSent.wind) {
    weatherAlertSent.wind = true
    notificationStore.pushWithDesktop({
      type: 'warning',
      title: '气象预警 · 风速过高',
      message: `当前区域风速 ${wind} m/s，可能影响飞行安全`,
      source: 'weather'
    })
  } else if (wind <= 12) {
    weatherAlertSent.wind = false
  }
  // 模拟强降雨：当 humidity > 85 且 region 为华东
  const humidity = +overviewMetrics.value[3].value
  if (humidity > 85 && !weatherAlertSent.rain) {
    weatherAlertSent.rain = true
    notificationStore.pushWithDesktop({
      type: 'warning',
      title: '气象预警 · 强降雨',
      message: `当前区域湿度 ${humidity}%，存在强降雨风险`,
      source: 'weather'
    })
  } else if (humidity <= 80) {
    weatherAlertSent.rain = false
  }
}

function initOverviewChart() {
  if (!overviewChartRef.value) return
  if (overviewChartInstance) overviewChartInstance.dispose()
  overviewChartInstance = echarts.init(overviewChartRef.value)
  const hours = Array.from({ length: 24 }, (_, i) => i + ':00')
  const temp = hours.map((_, i) => +(18 + 8 * Math.sin(i / 3) + pseudoRand(i + 11)).toFixed(1))
  const wind = hours.map((_, i) => +(3 + 2 * Math.cos(i / 4) + pseudoRand(i + 31)).toFixed(1))
  overviewChartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['温度 (°C)', '风速 (m/s)'] },
    grid: { left: 50, right: 50, top: 40, bottom: 40 },
    xAxis: { type: 'category', data: hours, boundaryGap: false },
    yAxis: [
      { type: 'value', name: '温度°C', position: 'left' },
      { type: 'value', name: '风速m/s', position: 'right' }
    ],
    series: [
      {
        name: '温度 (°C)', type: 'line', smooth: true, data: temp,
        itemStyle: { color: '#F56C6C' },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(245,108,108,0.45)' },
          { offset: 1, color: 'rgba(245,108,108,0.02)' }
        ]) }
      },
      {
        name: '风速 (m/s)', type: 'line', smooth: true, yAxisIndex: 1, data: wind,
        itemStyle: { color: '#409EFF' },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(64,158,255,0.4)' },
          { offset: 1, color: 'rgba(64,158,255,0.02)' }
        ]) }
      }
    ]
  })
}

// ========== Tab2: 风场矢量图 ==========
const windMapRef = ref(null)
const windRegion = ref('华东')
const windStep = ref(0)
const windDensity = ref(2)
let windMapInstance = null
let windCanvasLayer = null
let windResizeHandler = null

function regionBounds(region) {
  if (region === '华东') return [[23, 114], [32, 123]]
  if (region === '华北') return [[34, 110], [42, 120]]
  return [[18, 108], [26, 118]]
}

function genWindGrid(region, step) {
  const [[latMin, lngMin], [latMax, lngMax]] = regionBounds(region)
  const cols = 40, rows = 30
  const grid = []
  const seed = hashSeed(region + step)
  for (let r = 0; r < rows; r++) {
    const row = []
    for (let c = 0; c < cols; c++) {
      const lat = latMax - (latMax - latMin) * (r / (rows - 1))
      const lng = lngMin + (lngMax - lngMin) * (c / (cols - 1))
      const u = -3 + pseudoRand(seed + r * cols + c) * 8
      const v = -3 + pseudoRand(seed + r * cols + c + 999) * 8
      row.push({ lat, lng, u, v })
    }
    grid.push(row)
  }
  return grid
}

function initWindMap() {
  if (!windMapRef.value) return
  destroyMap(windMapInstance)
  windMapInstance = L.map(windMapRef.value, { zoomControl: true })
  new CachedTileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 18
  }).addTo(windMapInstance)
  const bounds = regionBounds(windRegion.value)
  windMapInstance.fitBounds(bounds)

  // custom canvas layer
  windCanvasLayer = L.canvas({ padding: 0.5 })
  windCanvasLayer.onAdd = function (map) {
    this._map = map
    const canvas = L.DomUtil.create('canvas', 'leaflet-heat-layer')
    const size = map.getSize()
    canvas.width = size.x
    canvas.height = size.y
    canvas.style.position = 'absolute'
    canvas.style.left = 0
    canvas.style.top = 0
    canvas.style.pointerEvents = 'none'
    this._canvas = canvas
    map.getPanes().overlayPane.appendChild(canvas)
    return canvas
  }
  windCanvasLayer.drawWind = drawWindArrows
  windCanvasLayer.addTo(windMapInstance)
  windResizeHandler = () => redrawWind()
  windMapInstance.on('moveend zoomend resize', windResizeHandler)
  redrawWind()
}

function drawWindArrows() {
  if (!windMapInstance || !windCanvasLayer || !windCanvasLayer._canvas) return
  const canvas = windCanvasLayer._canvas
  const ctx = canvas.getContext('2d')
  const size = windMapInstance.getSize()
  canvas.width = size.x
  canvas.height = size.y
  ctx.clearRect(0, 0, size.x, size.y)

  const grid = genWindGrid(windRegion.value, windStep.value)
  const stepCell = Math.max(1, 5 - windDensity.value)
  for (let r = 0; r < grid.length; r += stepCell) {
    for (let c = 0; c < grid[r].length; c += stepCell) {
      const p = grid[r][c]
      const px = windMapInstance.latLngToContainerPoint([p.lat, p.lng])
      const speed = Math.sqrt(p.u * p.u + p.v * p.v)
      let color = '#9ca3af'
      if (speed >= 3 && speed < 6) color = '#409EFF'
      else if (speed >= 6 && speed < 9) color = '#E6A23C'
      else if (speed >= 9) color = '#F56C6C'
      const len = Math.min(28, 6 + speed * 2)
      const ang = Math.atan2(p.v, p.u)
      const ex = px.x + Math.cos(ang) * len
      const ey = px.y + Math.sin(ang) * len
      ctx.strokeStyle = color
      ctx.lineWidth = 1.5
      ctx.beginPath()
      ctx.moveTo(px.x, px.y)
      ctx.lineTo(ex, ey)
      ctx.stroke()
      // arrow head
      const ah = 5
      ctx.beginPath()
      ctx.moveTo(ex, ey)
      ctx.lineTo(ex - ah * Math.cos(ang - 0.4), ey - ah * Math.sin(ang - 0.4))
      ctx.lineTo(ex - ah * Math.cos(ang + 0.4), ey - ah * Math.sin(ang + 0.4))
      ctx.closePath()
      ctx.fillStyle = color
      ctx.fill()
    }
  }
}

function redrawWind() {
  if (windMapInstance && windCanvasLayer && windCanvasLayer.drawWind) {
    windCanvasLayer.drawWind()
  }
}
const redrawWindThrottled = throttled(redrawWind, 150)

// ========== Tab3: 气象热力图 ==========
const heatMapRef = ref(null)
const heatVar = ref('temperature')
const heatOpacity = ref(0.7)
const heatRadius = ref(30)
const heatBlur = ref(20)
let heatMapInstance = null
let heatLayerInstance = null

const heatVarLabel = computed(() => {
  const map = { temperature: '温度', pressure: '气压', precipitation: '降水', turbulence: '湍流强度' }
  return map[heatVar.value]
})

function genHeatPoints(variable) {
  const seed = hashSeed(variable)
  const pts = []
  const centerLat = variable === 'precipitation' ? 28 : 30
  const centerLng = variable === 'precipitation' ? 116 : 118
  for (let i = 0; i < 260; i++) {
    const lat = centerLat + (pseudoRand(seed + i) - 0.5) * 16
    const lng = centerLng + (pseudoRand(seed + i + 500) - 0.5) * 18
    const intensity = pseudoRand(seed + i + 1000)
    pts.push([lat, lng, intensity])
  }
  return pts
}

function initHeatMap() {
  if (!heatMapRef.value) return
  destroyMap(heatMapInstance)
  heatMapInstance = L.map(heatMapRef.value)
  new CachedTileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 18
  }).addTo(heatMapInstance)
  heatMapInstance.fitBounds([[20, 105], [40, 125]])
  redrawHeat()
}

function redrawHeat() {
  if (!heatMapInstance) return
  if (heatLayerInstance) {
    heatMapInstance.removeLayer(heatLayerInstance)
    heatLayerInstance = null
  }
  const pts = genHeatPoints(heatVar.value)
  heatLayerInstance = L.heatLayer(pts, {
    radius: heatRadius.value,
    blur: heatBlur.value,
    maxZoom: 10,
    max: 1.0,
    opacity: heatOpacity.value,
    gradient: { 0.0: '#00f', 0.25: '#0ff', 0.5: '#ff0', 0.75: '#f80', 1.0: '#f00' }
  }).addTo(heatMapInstance)
}
const redrawHeatThrottled = throttled(redrawHeat, 150)

// ========== Tab4: 贝叶斯方差场 ==========
const varianceMapRef = ref(null)
const varianceVar = ref('temp')
const varianceStep = ref(0)
let varianceMapInstance = null
let varianceLayerInstance = null

const varianceConfidence = computed(() => {
  const seed = hashSeed(varianceVar.value + '|' + varianceStep.value)
  return Math.round(65 + pseudoRand(seed) * 30)
})

function genVariancePoints(variable, step) {
  const seed = hashSeed(variable + step)
  const pts = []
  for (let i = 0; i < 220; i++) {
    const lat = 25 + (pseudoRand(seed + i) - 0.5) * 16
    const lng = 110 + (pseudoRand(seed + i + 99) - 0.5) * 16
    const intensity = 0.2 + pseudoRand(seed + i + 200) * 0.8
    pts.push([lat, lng, intensity])
  }
  return pts
}

function initVarianceMap() {
  if (!varianceMapRef.value) return
  destroyMap(varianceMapInstance)
  varianceMapInstance = L.map(varianceMapRef.value)
  new CachedTileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
    maxZoom: 18
  }).addTo(varianceMapInstance)
  varianceMapInstance.fitBounds([[20, 105], [40, 125]])
  redrawVariance()
}

function redrawVariance() {
  if (!varianceMapInstance) return
  if (varianceLayerInstance) {
    varianceMapInstance.removeLayer(varianceLayerInstance)
    varianceLayerInstance = null
  }
  const pts = genVariancePoints(varianceVar.value, varianceStep.value)
  varianceLayerInstance = L.heatLayer(pts, {
    radius: 28,
    blur: 25,
    maxZoom: 10,
    max: 1.0,
    opacity: 0.75,
    gradient: { 0.0: '#67C23A', 0.4: '#E6A23C', 0.7: '#F56C6C', 1.0: '#9254DE' }
  }).addTo(varianceMapInstance)
}
const redrawVarianceThrottled = throttled(redrawVariance, 150)

// ========== Tab5: 多模型误差对比 ==========
const compareChartRef = ref(null)
const compareVar = ref('temperature')
const compareRegion = ref('华东')
let compareChartInstance = null

const compareVarLabel = computed(() => ({ temperature: '温度', wind: '风速', pressure: '气压' }[compareVar.value]))

const compareStats = computed(() => {
  const seed = hashSeed(compareVar.value + compareRegion.value)
  const base = compareVar.value === 'pressure' ? 2.5 : compareVar.value === 'wind' ? 0.8 : 0.6
  const models = [
    { name: 'WRF', color: '#409EFF' },
    { name: '风乌', color: '#67C23A' },
    { name: '天资', color: '#E6A23C' },
    { name: '风雷', color: '#F56C6C' }
  ]
  const stats = models.map((m, i) => {
    const rmse = +(base + pseudoRand(seed + i) * 1.2).toFixed(2)
    const bias = +((pseudoRand(seed + i + 55) - 0.5) * base * 1.5).toFixed(2)
    return { ...m, rmse, bias, n: 720, isBest: false }
  })
  const minRmse = Math.min(...stats.map(s => s.rmse))
  stats.forEach(s => (s.isBest = Math.abs(s.rmse - minRmse) < 1e-6))
  return stats
})

function redrawCompare() {
  if (!compareChartRef.value) return
  if (!compareChartInstance) {
    compareChartInstance = echarts.init(compareChartRef.value)
  }
  const seed = hashSeed(compareVar.value + compareRegion.value)
  const xAxis = ['0h', '3h', '6h', '9h', '12h', '15h', '18h', '21h', '24h']
  const series = compareStats.value.map(m => {
    const data = xAxis.map((_, i) => +(m.rmse + (pseudoRand(seed + hashSeed(m.name) + i) - 0.5) * 0.8).toFixed(3))
    return {
      name: m.name,
      type: 'line',
      smooth: true,
      data,
      symbol: 'circle',
      symbolSize: 6,
      itemStyle: { color: m.color },
      lineStyle: { width: 2.2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: m.color + 'aa' },
          { offset: 1, color: m.color + '10' }
        ])
      }
    }
  })
  compareChartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: compareStats.value.map(m => m.name), top: 6 },
    grid: { left: 55, right: 30, top: 50, bottom: 45 },
    xAxis: { type: 'category', data: xAxis, boundaryGap: false },
    yAxis: { type: 'value', name: 'RMSE', scale: true },
    series
  }, true)
}
const redrawCompareThrottled = throttled(redrawCompare, 150)

// ========== 位置服务 ==========
async function fetchCurrentLocation() {
  isLocating.value = true
  locationError.value = null
  
  const result = await getCurrentLocation()
  
  if (result.success) {
    currentLocation.value = result
    if (result.region && result.region.key !== 'unknown') {
      overviewRegion.value = result.region.name
      windRegion.value = result.region.name
      compareRegion.value = result.region.name
    }
    
    // 检查地址是否有效
    const locationText = result.address?.formatted 
      ? result.address.formatted
      : result.position 
        ? `${result.position.latitude.toFixed(4)}, ${result.position.longitude.toFixed(4)}`
        : '未知位置'
    
    notificationStore.push({
      type: 'success',
      title: t('weather.currentLocation'),
      message: locationText,
      source: 'weather'
    })
  } else {
    locationError.value = result.error || '定位失败'
    console.warn('[WeatherView] Failed to get location:', result.error)
  }
  
  isLocating.value = false
}

// ========== 工具函数 ==========
function destroyMap(instance) {
  if (instance) {
    try { instance.off('moveend zoomend resize') } catch (e) {}
    instance.remove()
  }
}

function hashSeed(str) {
  let h = 2166136261
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return h >>> 0
}

function pseudoRand(seed) {
  const x = Math.sin(seed * 12.9898 + 78.233) * 43758.5453
  return x - Math.floor(x)
}

// ========== Tab 切换处理 ==========
function handleTabChange(name) {
  nextTick(() => {
    if (name === 'overview') {
      initOverviewChart()
      checkWeatherAlerts()
    }
    if (name === 'wind') initWindMap()
    if (name === 'heat') initHeatMap()
    if (name === 'variance') initVarianceMap()
    if (name === 'compare') redrawCompare()
  })
}
const handleTabChangeThrottled = throttled(handleTabChange, 150)

const initOverviewChartThrottled = throttled(initOverviewChart, 150)

// ========== 生命周期 ==========
onMounted(() => {
  initTileCache()
  nextTick(() => {
    initOverviewChart()
    checkWeatherAlerts()
  })
  window.addEventListener('resize', () => {
    if (overviewChartInstance) overviewChartInstance.resize()
    if (compareChartInstance) compareChartInstance.resize()
    if (windMapInstance) windMapInstance.invalidateSize()
    if (heatMapInstance) heatMapInstance.invalidateSize()
    if (varianceMapInstance) varianceMapInstance.invalidateSize()
  })
})

onUnmounted(() => {
  if (overviewChartInstance) overviewChartInstance.dispose()
  if (compareChartInstance) compareChartInstance.dispose()
  if (windMapInstance && windResizeHandler) {
    try { windMapInstance.off('moveend zoomend resize', windResizeHandler) } catch (e) {}
  }
  destroyMap(windMapInstance)
  destroyMap(heatMapInstance)
  destroyMap(varianceMapInstance)
})

watch([overviewRegion, overviewHour, overviewAltitude], () => {
  nextTick(() => {
    initOverviewChartThrottled()
    checkWeatherAlerts()
  })
})
</script>

<style scoped>
.weather {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100%;
}

.demo-alert {
  margin-bottom: 16px;
}

.weather-tabs :deep(.el-tabs__header) {
  margin-bottom: 16px;
  background: #fff;
  border-radius: 8px;
  padding: 0 16px;
}

.tab-container {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.left-panel {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.right-panel {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.control-card,
.info-card,
.chart-card {
  border-radius: 10px;
}

.panel-title {
  font-weight: 600;
  color: #1f2937;
}

.info-text {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.7;
}

/* Metric cards */
.metric-row {
  margin-bottom: 0;
}

.metric-card {
  border-radius: 10px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08) !important;
}

.metric-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
}

.metric-icon {
  font-size: 16px;
}

.metric-body {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 4px;
}

.metric-value {
  font-size: 26px;
  font-weight: 700;
  color: #1f2937;
}

.metric-unit {
  font-size: 13px;
  color: #6b7280;
}

.metric-trend {
  font-size: 12px;
  margin-left: auto;
  padding: 2px 8px;
  border-radius: 10px;
}

.trend-up {
  color: #f56c6c;
  background: #fef0f0;
}

.trend-down {
  color: #67c23a;
  background: #f0f9eb;
}

/* echarts box */
.echarts-box {
  width: 100%;
  height: 280px;
}

.echarts-box.tall {
  height: 360px;
}

/* leaflet map */
.map-wrapper {
  position: relative;
  background: #fff;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.leaflet-map {
  width: 100%;
  height: 520px;
  border-radius: 10px;
}

.map-legend {
  position: absolute;
  top: 14px;
  right: 14px;
  width: 190px;
  padding: 10px 14px !important;
  border-radius: 10px !important;
  z-index: 500;
  font-size: 12px;
}

.legend-title {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #4b5563;
  margin-bottom: 4px;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  display: inline-block;
}

.legend-tip {
  color: #6b7280;
  font-size: 12px;
  line-height: 1.5;
}

/* variance top alert */
.variance-top-alert {
  margin-bottom: 0;
}

/* compare stats */
.compare-stats {
  margin-top: 0;
}

.stat-card {
  border-radius: 10px;
}

.stat-card.best-card {
  border: 1px solid #67c23a;
  background: linear-gradient(180deg, #f0f9eb 0%, #ffffff 40%);
}

.stat-title {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
}

.stat-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 6px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #6b7280;
  padding: 3px 0;
}

.stat-row b {
  color: #1f2937;
}

.card-header {
  font-weight: 600;
  color: #1f2937;
}

.location-btn-wrapper {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.location-info {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 8px 12px;
  background: #f0f9eb;
  border-radius: 6px;
  font-size: 13px;
}

.location-label {
  color: #67c23a;
  font-weight: 500;
  flex-shrink: 0;
}

.location-value {
  color: #303133;
  word-break: break-all;
}

.location-error {
  margin-top: 4px;
}

@media (max-width: 1100px) {
  .tab-container {
    flex-direction: column;
  }
  .left-panel {
    width: 100%;
  }
  .leaflet-map {
    height: 420px;
  }
}

@media (max-width: 768px) {
  .tab-container,
  .el-row,
  .el-row--flex {
    flex-direction: column !important;
  }
  .el-col {
    max-width: 100% !important;
    flex: 0 0 100% !important;
  }
  .weather-tabs :deep(.el-tabs__item) {
    padding: 0 8px;
    font-size: 12px;
  }
  :deep(.el-card) {
    padding: 10px !important;
  }
  .stat-card,
  .info-card,
  .control-card {
    padding: 10px !important;
  }
  .leaflet-map {
    height: 280px;
  }
  :deep(.table-wrapper),
  :deep(.el-table-wrapper) {
    overflow-x: auto;
  }
}
</style>
