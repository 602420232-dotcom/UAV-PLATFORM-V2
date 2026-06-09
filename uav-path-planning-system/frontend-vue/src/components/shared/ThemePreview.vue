<template>
  <el-card shadow="hover" class="theme-preview" :style="{ background: surface, color: text }">
    <div class="title">{{ title }}</div>
    <div class="swatches">
      <div class="sw" v-for="c in colors" :key="c.name" :style="{ background: c.value }">
        <span>{{ c.name }}</span>
      </div>
    </div>
    <div class="sample">
      <el-button :style="{ background: primary, borderColor: primary }" type="primary">主要按钮</el-button>
      <el-button type="success" :style="{ background: success, borderColor: success }">成功</el-button>
      <el-button type="warning" :style="{ background: warning, borderColor: warning }">警告</el-button>
      <el-button type="danger" :style="{ background: danger, borderColor: danger }">危险</el-button>
    </div>
  </el-card>
</template>

<script setup>
const props = defineProps({
  title: { type: String, default: '浅色主题' },
  surface: { type: String, default: '#ffffff' },
  text: { type: String, default: '#1f2937' },
  primary: { type: String, default: '#409EFF' },
  success: { type: String, default: '#67C23A' },
  warning: { type: String, default: '#E6A23C' },
  danger: { type: String, default: '#F56C6C' }
})
const colors = [
  { name: '主色', value: props.primary },
  { name: '成功', value: props.success },
  { name: '警告', value: props.warning },
  { name: '危险', value: props.danger }
]
</script>

<style scoped>
.theme-preview { border-radius: 12px; }
.title { font-size: 16px; font-weight: 600; margin-bottom: 12px; }
.swatches { display: flex; gap: 8px; margin-bottom: 16px; }
.sw { padding: 8px 14px; border-radius: 6px; color: #fff; font-size: 12px; }
.sample { display: flex; gap: 8px; flex-wrap: wrap; }
</style>
