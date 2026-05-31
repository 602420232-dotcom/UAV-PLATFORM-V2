<template>
  <a-card title="无人机管理" class="drones-card">
    <a-row :gutter="[16, 16]">
      <a-col :span="24">
        <a-spin :spinning="loading">
          <a-row :gutter="[16, 16]">
            <a-col :xs="24" :sm="12" :lg="8" v-for="drone in drones" :key="drone.id">
              <a-card hoverable>
                <template #title>
                  <span>
                    <a-badge :status="drone.status === '在线' ? 'success' : drone.status === '执行任务' ? 'processing' : 'default'" />
                    {{ drone.name }}
                  </span>
                </template>
                <a-descriptions :column="1" size="small">
                  <a-descriptions-item label="ID">{{ drone.id }}</a-descriptions-item>
                  <a-descriptions-item label="类型">{{ drone.type }}</a-descriptions-item>
                  <a-descriptions-item label="状态">{{ drone.status }}</a-descriptions-item>
                  <a-descriptions-item label="电量">
                    <a-progress :percent="drone.battery" :size="20" :status="drone.battery < 20 ? 'exception' : 'normal'" />
                  </a-descriptions-item>
                  <a-descriptions-item label="位置">{{ drone.location }}</a-descriptions-item>
                </a-descriptions>
              </a-card>
            </a-col>
          </a-row>
        </a-spin>
      </a-col>
    </a-row>
  </a-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { getDrones } from '../api/drones'

const drones = ref([])
const loading = ref(false)

const loadDrones = async () => {
  loading.value = true
  try {
    const res = await getDrones()
    drones.value = Array.isArray(res) ? res : (res.data || res.content || [])
  } catch (e) {
    // 后端未连接或需要认证时，使用演示数据
    if (e.message === 'BACKEND_UNAVAILABLE' || e.message === 'AUTH_REQUIRED') {
      console.log('[DronesView] 使用演示数据')
    }
    drones.value = [
      { id: 'UAV-001', name: '无人机1', type: 'multirotor', status: '在线', battery: 85, location: '39.90, 116.40' },
      { id: 'UAV-002', name: '无人机2', type: 'multirotor', status: '执行任务', battery: 60, location: '39.91, 116.41' },
      { id: 'UAV-003', name: '无人机3', type: 'fixed-wing', status: '待命', battery: 90, location: '39.92, 116.42' },
    ]
  } finally {
    loading.value = false
  }
}

onMounted(loadDrones)
</script>

<style scoped>
.drones-card { margin-bottom: 24px; }
</style>
