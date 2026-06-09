<template>
  <el-tag
    v-if="scope === 'personal'"
    type="info"
    size="small"
    effect="light"
    class="data-scope-badge"
  >
    个人 · {{ teamLabel }}
  </el-tag>
  <el-tag
    v-else-if="scope === 'team'"
    type="primary"
    size="small"
    effect="light"
    class="data-scope-badge"
  >
    团队 · {{ teamLabel }}
  </el-tag>
  <el-tag
    v-else
    type="danger"
    size="small"
    effect="dark"
    class="data-scope-badge"
  >
    全部数据
  </el-tag>
</template>

<script setup>
import { computed } from 'vue'
import { TEAM_LABELS } from '../../stores/auth'

const props = defineProps({
  scope: {
    type: String,
    default: 'personal'
  },
  team: {
    type: String,
    default: ''
  }
})

const teamLabel = computed(() => {
  if (!props.team) return '-'
  return TEAM_LABELS[props.team] || props.team
})
</script>

<style scoped>
.data-scope-badge {
  font-size: 12px;
}
</style>
