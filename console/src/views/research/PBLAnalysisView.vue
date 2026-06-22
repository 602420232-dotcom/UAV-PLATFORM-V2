<template>
  <div class="pbl-analysis-view">
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
        <h1 class="page-title">边界层方案分析与对比</h1>
      </div>
    </div>

    <!-- 内容区域 -->
    <el-card shadow="never" class="content-card">
      <PBLSchemeSelector
        v-model:selected-pbl="selectedPblScheme"
        v-model:selected-cumulus="selectedCumulusScheme"
        v-model:selected-micro="selectedMicroScheme"
        v-model:selected-radiation="selectedRadiationScheme"
        v-model:selected-lsm="selectedLsmScheme"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import PBLSchemeSelector from '@/components/research/PBLSchemeSelector.vue'

const router = useRouter()

// 方案选择状态
const selectedPblScheme = ref('YSU')
const selectedCumulusScheme = ref('Kain-Fritsch')
const selectedMicroScheme = ref('Thompson')
const selectedRadiationScheme = ref('RRTMG')
const selectedLsmScheme = ref('Noah')
</script>

<style scoped>
.pbl-analysis-view {
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
  padding: 20px;
}

.content-card :deep(.el-card__header) {
  border-bottom-color: #2a2a40;
  color: #e0e0e0;
}
</style>
