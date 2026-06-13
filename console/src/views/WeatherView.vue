<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { weatherApi } from '@/api/weather'
import type { WeatherGrid } from '@/api/weather'

const loading = ref(false)
const weatherData = ref<WeatherGrid | null>(null)

const queryForm = ref({
  lon: 116.4,
  lat: 39.9,
  altitude: 100,
  source: '',
  forecastTime: '',
})

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

function formatSpeed(speed: number): string {
  return `${speed.toFixed(1)} m/s`
}

function formatDirection(dir: number): string {
  const directions = ['北', '东北', '东', '东南', '南', '西南', '西', '西北']
  const index = Math.round(dir / 45) % 8
  return `${dir.toFixed(0)}° (${directions[index]})`
}
</script>

<template>
  <div class="weather-page">
    <div class="page-header">
      <h2>气象数据</h2>
    </div>

    <div class="content-grid">
      <!-- 地图区域（CesiumJS 占位） -->
      <!--
        TODO: 后续集成 CesiumJS 三维地球
        - 引入 cesium npm 包
        - 在此 div 中初始化 Cesium.Viewer
        - 叠加风场粒子效果（基于 weatherData 或区域查询结果）
        - 支持点击查询、区域框选
      -->
      <el-card class="map-card">
        <template #header>
          <span>气象地图</span>
        </template>
        <div class="map-placeholder">
          <el-icon :size="48" color="#0f3460"><MapLocation /></el-icon>
          <p>CesiumJS 三维地图（待集成）</p>
          <p class="placeholder-hint">支持风场叠加、温度场可视化、多源数据切换</p>
        </div>
      </el-card>

      <!-- 查询面板 -->
      <el-card class="query-card">
        <template #header>
          <span>单点气象查询</span>
        </template>
        <el-form label-width="80px">
          <el-form-item label="经度">
            <el-input-number v-model="queryForm.lon" :precision="4" :step="0.1" :min="-180" :max="180" />
          </el-form-item>
          <el-form-item label="纬度">
            <el-input-number v-model="queryForm.lat" :precision="4" :step="0.1" :min="-90" :max="90" />
          </el-form-item>
          <el-form-item label="高度(m)">
            <el-input-number v-model="queryForm.altitude" :step="100" :min="0" :max="20000" />
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
      </el-card>

      <!-- 查询结果 -->
      <el-card v-if="weatherData" class="result-card">
        <template #header>
          <span>查询结果</span>
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
    </div>
  </div>
</template>

<style scoped>
.weather-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 360px;
  grid-template-rows: auto auto;
  gap: 16px;
}

.map-card {
  grid-column: 1;
  grid-row: 1 / 3;
  border-radius: 8px;
  min-height: 500px;
}

.map-placeholder {
  height: 460px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background-color: var(--color-bg);
  border-radius: 4px;
  border: 1px dashed var(--color-border-light);
  color: var(--color-text-muted);
}

.placeholder-hint {
  font-size: 12px;
}

.query-card,
.result-card {
  border-radius: 8px;
}
</style>
