<template>
  <div class="weather-source-page">
    <div class="page-header">
      <h2>气象数据源配置</h2>
      <p class="page-desc">管理气象数据源连接、API密钥配置和WRF服务器设置</p>
    </div>
    <WeatherSourceConfig />
  </div>
</template>

<script setup lang="ts">
import WeatherSourceConfig from '@/components/settings/WeatherSourceConfig.vue'
</script>

<style scoped>
.weather-source-page {
  padding: 24px;
}
.page-header {
  margin-bottom: 20px;
}
.page-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary, #e0e0e0);
  margin: 0 0 8px 0;
}
.page-desc {
  font-size: 13px;
  color: var(--color-text-muted, #6a6a80);
  margin: 0;
}
</style>
