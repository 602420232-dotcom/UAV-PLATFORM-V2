<template>
  <el-card class="stat-card" shadow="hover" :body-style="{ padding: '16px' }">
    <div class="stat-row">
      <div class="stat-label">{{ label }}</div>
      <el-tag :type="tagType" effect="light">{{ tagText }}</el-tag>
    </div>
    <div class="stat-value" :style="{ color: valueColor }">{{ formattedValue }}</div>
    <div class="stat-desc">{{ description }}</div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({
  label: { type: String, default: '指标' },
  value: { type: [Number, String], default: 0 },
  unit: { type: String, default: '' },
  tagText: { type: String, default: '实时' },
  tagType: { type: String, default: 'success' },
  description: { type: String, default: '' },
  valueColor: { type: String, default: '#1f2937' }
})
const formattedValue = computed(() => `${props.value}${props.unit}`)
</script>

<style scoped>
.stat-card { border-radius: 12px; }
.stat-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.stat-label { font-size: 14px; color: var(--color-text-muted); }
.stat-value { font-size: 28px; font-weight: 600; margin: 8px 0; }
.stat-desc { font-size: 12px; color: var(--color-text-muted); }
</style>
