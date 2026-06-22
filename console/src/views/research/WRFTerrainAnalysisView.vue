<template>
  <div class="wrf-terrain-analysis-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header__left">
        <el-button
          class="back-btn"
          :icon="ArrowLeft"
          text
          @click="router.back()"
        >
          返回
        </el-button>
        <h1 class="page-title">WRF 地形分析可视化</h1>
      </div>
    </div>

    <!-- 内容区域 -->
    <el-card shadow="never" class="content-card">
      <WRFTerrainAnalysis />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import WRFTerrainAnalysis from '@/components/research/WRFTerrainAnalysis.vue'

const router = useRouter()
</script>

<style scoped>
.wrf-terrain-analysis-view {
  padding: 24px;
  background: #1a1a2e;
  min-height: 100vh;
  color: #e0e0e0;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-header__left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  color: #a0a0b0;
  font-size: 14px;
  padding: 8px 12px;
}

.back-btn:hover {
  color: #e0e0e0;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #e0e0e0;
  margin: 0;
}

.content-card {
  background: #1f1f35;
  border-color: #2a2a40;
  color: #e0e0e0;
}

.content-card :deep(.el-card__body) {
  padding: 0;
}

.content-card :deep(.el-card__header) {
  border-bottom-color: #2a2a40;
  color: #e0e0e0;
}
</style>
