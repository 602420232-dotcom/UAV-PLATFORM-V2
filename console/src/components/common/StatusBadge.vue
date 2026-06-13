<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  status: string | number
  statusMap?: Record<string | number, { label: string; type: string }>
}>(), {
  statusMap: () => ({
    0: { label: '正常', type: 'success' },
    1: { label: '启用', type: 'success' },
    2: { label: '禁用', type: 'danger' },
    UP: { label: '正常', type: 'success' },
    DOWN: { label: '宕机', type: 'danger' },
    DEGRADED: { label: '降级', type: 'warning' },
    PENDING: { label: '等待中', type: 'info' },
    RUNNING: { label: '运行中', type: 'primary' },
    COMPLETED: { label: '已完成', type: 'success' },
    FAILED: { label: '失败', type: 'danger' },
    CANCELLED: { label: '已取消', type: 'info' },
  }),
})

const config = computed(() => {
  return props.statusMap[props.status] ?? { label: String(props.status), type: 'info' }
})
</script>

<template>
  <el-tag :type="config.type as 'success' | 'warning' | 'danger' | 'info' | 'primary'" size="small" effect="plain">
    {{ config.label }}
  </el-tag>
</template>
