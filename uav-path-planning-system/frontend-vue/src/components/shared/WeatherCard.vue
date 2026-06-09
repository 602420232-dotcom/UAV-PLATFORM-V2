<template>
  <el-card shadow="hover" class="weather-card">
    <div class="row">
      <div>
        <div class="title">{{ city }}</div>
        <div class="time">{{ timeText }}</div>
      </div>
      <el-icon :size="32" color="var(--color-primary)"><Sunny /></el-icon>
    </div>
    <div class="big-temp">{{ temperature }}<span>°C</span></div>
    <div class="metrics">
      <div><span>风向</span><strong>{{ windDir }}</strong></div>
      <div><span>风速</span><strong>{{ windSpeed }} m/s</strong></div>
      <div><span>气压</span><strong>{{ pressure }} hPa</strong></div>
      <div><span>湿度</span><strong>{{ humidity }}%</strong></div>
    </div>
  </el-card>
</template>

<script setup>
import { Sunny } from '@element-plus/icons-vue'
defineProps({
  city: { type: String, default: '北京' },
  timeText: { type: String, default: '2026-06-09 12:00' },
  temperature: { type: Number, default: 24 },
  windDir: { type: String, default: '东南' },
  windSpeed: { type: Number, default: 4 },
  pressure: { type: Number, default: 1013 },
  humidity: { type: Number, default: 42 }
})
</script>

<style scoped>
.weather-card { border-radius: 12px; }
.row { display: flex; justify-content: space-between; align-items: center; }
.title { font-size: 18px; font-weight: 600; }
.time { font-size: 12px; color: var(--color-text-muted); margin-top: 4px; }
.big-temp { font-size: 40px; font-weight: 600; color: var(--color-primary); margin: 12px 0; }
.big-temp span { font-size: 18px; color: var(--color-text-muted); margin-left: 4px; }
.metrics { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
.metrics > div { display: flex; justify-content: space-between; font-size: 13px; padding: 6px 10px; background: rgba(0,0,0,0.03); border-radius: 6px; }
.metrics span { color: var(--color-text-muted); }
</style>
