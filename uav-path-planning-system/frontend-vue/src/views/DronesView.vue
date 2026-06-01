<template>
  <a-card title="无人机管理" class="drones-card">
    <a-row :gutter="[16, 16]">
      <a-col :span="24">
        <a-spin :spinning="store.loading.drones">
          <a-row :gutter="[16, 16]">
            <a-col :xs="24" :sm="12" :lg="8" v-for="drone in store.drones" :key="drone.id">
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
import { onMounted } from 'vue'
import { useDataStore } from '../stores/dataStore'

const store = useDataStore()

onMounted(() => {
  store.fetchDrones()
})
</script>

<style scoped>
.drones-card { margin-bottom: 24px; }
</style>
