<template>
  <div class="weather-card" :class="status">
    <div class="weather-card-title">{{ title }}</div>
    <div class="weather-card-value">
      <span class="value">{{ value }}</span>
      <span class="unit">{{ unit }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title: string
  value: number | string
  unit?: string
  status?: 'normal' | 'warning' | 'danger'
}

withDefaults(defineProps<Props>(), {
  unit: '',
  status: 'normal'
})
</script>

<style scoped>
.weather-card {
  padding: 16px;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  text-align: center;
}
.weather-card.warning {
  border-left: 4px solid #faad14;
}
.weather-card.danger {
  border-left: 4px solid #ff4d4f;
}
.weather-card-title {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}
.weather-card-value .value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}
.weather-card-value .unit {
  font-size: 14px;
  color: #999;
  margin-left: 4px;
}
</style>
