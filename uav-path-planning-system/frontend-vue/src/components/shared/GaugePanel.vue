<template>
  <el-card class="gauge-panel" shadow="hover">
    <div class="gauge-label">{{ label }}</div>
    <el-progress type="dashboard" :percentage="innerPercent" :color="colorSet" :width="180" />
    <div class="gauge-meta">
      <div><span class="k">当前</span><span class="v">{{ value }}{{ unit }}</span></div>
      <div><span class="k">阈值</span><span class="v">{{ threshold }}{{ unit }}</span></div>
      <div><span class="k">均值</span><span class="v">{{ avg }}{{ unit }}</span></div>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
  label: { type: String, default: 'CPU 使用率' },
  value: { type: Number, default: 0 },
  max: { type: Number, default: 100 },
  threshold: { type: Number, default: 80 },
  avg: { type: Number, default: 40 },
  unit: { type: String, default: '%' }
})
const innerPercent = computed(() => Math.min(100, Math.round((props.value / props.max) * 100)))
const colorSet = computed(() => {
  if (props.value < 60) return [{ color: '#67C23A', percentage: 100 }]
  if (props.value < props.threshold) return [{ color: '#E6A23C', percentage: 100 }]
  return [{ color: '#F56C6C', percentage: 100 }]
})
</script>

<style scoped>
.gauge-panel { border-radius: 12px; text-align: center; }
.gauge-label { font-size: 14px; color: var(--color-text-muted); margin-bottom: 8px; }
.gauge-meta { display: flex; justify-content: space-around; margin-top: 8px; font-size: 13px; }
.gauge-meta .k { color: var(--color-text-muted); margin-right: 4px; }
.gauge-meta .v { font-weight: 600; }
</style>
