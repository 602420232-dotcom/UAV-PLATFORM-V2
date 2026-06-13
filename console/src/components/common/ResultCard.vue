<script setup lang="ts">
defineProps<{
  title: string
  value: string | number
  icon?: string
  color?: string
  subtitle?: string
}>()
</script>

<template>
  <el-card class="result-card" shadow="hover">
    <div class="card-content">
      <div class="card-info">
        <div class="card-title">{{ title }}</div>
        <div class="card-value" :style="{ color: color || 'var(--color-accent)' }">
          {{ value }}
        </div>
        <div v-if="subtitle" class="card-subtitle">{{ subtitle }}</div>
      </div>
      <div v-if="icon" class="card-icon" :style="{ backgroundColor: (color || 'var(--color-accent)') + '20' }">
        <el-icon :size="28" :color="color || 'var(--color-accent)'">
          <component :is="icon" />
        </el-icon>
      </div>
    </div>
  </el-card>
</template>

<style scoped>
.result-card {
  border-radius: 8px;
}

.result-card :deep(.el-card__body) {
  padding: 20px;
}

.card-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-info {
  flex: 1;
}

.card-title {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-bottom: 8px;
}

.card-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.card-subtitle {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 4px;
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
