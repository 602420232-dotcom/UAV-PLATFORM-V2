<template>
  <el-card shadow="hover" class="role-matrix">
    <div class="title">角色 × 页面权限矩阵</div>
    <el-table :data="tableData" border stripe size="small" style="width:100%">
      <el-table-column prop="route" label="页面" width="160" fixed />
      <el-table-column v-for="role in roles" :key="role" :label="roleLabel(role)" align="center">
        <template #default="{ row }">
          <el-icon v-if="row[role]" color="#67C23A"><Check /></el-icon>
          <el-icon v-else color="#F56C6C"><Close /></el-icon>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup>
import { Check, Close } from '@element-plus/icons-vue'
const props = defineProps({
  roles: { type: Array, default: () => ['user','production','flight','tester','deployment','admin'] },
  matrix: {
    type: Object,
    default: () => ({
      dashboard: ['user','production','flight','tester','deployment','admin'],
      weather: ['user','production','flight','tester','deployment','admin'],
      orders: ['user','production','admin'],
      cockpit: ['production','flight','admin'],
      'path-planning': ['flight','tester','admin'],
      monitoring: ['tester','deployment','admin'],
      database: ['admin']
    })
  }
})
const roleLabel = (r) => ({user:'普通用户',production:'生产',flight:'飞控',tester:'测试',deployment:'部署',admin:'管理员'}[r] || r)
const tableData = Object.keys(props.matrix).map(route => {
  const row = { route }
  props.roles.forEach(r => { row[r] = (props.matrix[route] || []).includes(r) })
  return row
})
</script>

<style scoped>
.title { font-size: 16px; font-weight: 600; margin-bottom: 12px; }
</style>
