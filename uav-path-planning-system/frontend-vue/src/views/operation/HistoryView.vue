<template>
  <div class="history">
    <div class="page-title">历史记录</div>

    <a-row :gutter="[16, 16]">
      <a-col :span="24">
        <a-card>
          <a-row :gutter="[16, 16]" align="middle">
            <a-col :flex="1">
              <a-space>
                <a-range-picker
                  v-model:value="dateRange"
                  show-time
                  style="width: 360px"
                  placeholder="选择时间范围"
                />
                <a-select v-model:value="statusFilter" allow-clear placeholder="状态筛选" style="width: 140px">
                  <a-select-option value="成功">成功</a-select-option>
                  <a-select-option value="失败">失败</a-select-option>
                  <a-select-option value="进行中">进行中</a-select-option>
                </a-select>
                <a-input-search v-model:value="searchText" allow-clear placeholder="搜索任务名称" style="width: 200px" />
              </a-space>
            </a-col>
            <a-col>
              <a-button @click="exportHistory">
                <template #icon><DownloadOutlined /></template>
                导出
              </a-button>
            </a-col>
          </a-row>
        </a-card>
      </a-col>

      <a-col :span="24">
        <a-card>
          <a-table
            :columns="columns"
            :data-source="filteredHistory"
            row-key="id"
            :loading="taskStore.loading"
            :pagination="{ pageSize: 10 }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="getStatusColor(record.status)">{{ record.status }}</a-tag>
              </template>
              <template v-else-if="column.key === 'action'">
                <a-button type="link" size="small" @click="showDetail(record)">详情</a-button>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>

    <!-- 详情模态框 -->
    <a-drawer title="历史详情" v-model:open="detailVisible" width="520">
      <template v-if="currentRecord">
        <a-descriptions :column="1" bordered size="small">
          <a-descriptions-item label="任务名称">{{ currentRecord.name }}</a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag :color="getStatusColor(currentRecord.status)">{{ currentRecord.status }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="开始时间">{{ currentRecord.startTime }}</a-descriptions-item>
          <a-descriptions-item label="结束时间">{{ currentRecord.endTime }}</a-descriptions-item>
          <a-descriptions-item label="耗时">{{ currentRecord.duration || '-' }}</a-descriptions-item>
          <a-descriptions-item label="无人机数量">{{ currentRecord.droneCount || 0 }}</a-descriptions-item>
          <a-descriptions-item label="任务数量">{{ currentRecord.taskCount || 0 }}</a-descriptions-item>
          <a-descriptions-item label="总距离 (m)">{{ currentRecord.totalDistance || 0 }}</a-descriptions-item>
          <a-descriptions-item label="总时间 (min)">{{ currentRecord.totalTime || 0 }}</a-descriptions-item>
          <a-descriptions-item label="气象">
            <template v-if="currentRecord.weatherData">
              风速：{{ currentRecord.weatherData.windSpeed }} m/s
              <br />
              温度：{{ currentRecord.weatherData.temperature }} °C
              <br />
              湿度：{{ currentRecord.weatherData.humidity }} %
            </template>
            <template v-else>-</template>
          </a-descriptions-item>
          <a-descriptions-item label="路径详情">
            <template v-if="currentRecord.routes && currentRecord.routes.length">
              <div v-for="(route, idx) in currentRecord.routes" :key="idx" class="route-item">
                <div><b>无人机 {{ route.droneId }}</b></div>
                <div>路径：{{ (route.path || []).join(' → ') }}</div>
                <div>距离：{{ route.distance }} m / 时间：{{ route.time }} 分钟</div>
              </div>
            </template>
            <template v-else>-</template>
          </a-descriptions-item>
        </a-descriptions>
      </template>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { DownloadOutlined } from '@ant-design/icons-vue'
import { useTaskStore } from '../../stores/tasks'

const taskStore = useTaskStore()

const dateRange = ref(null)
const statusFilter = ref(null)
const searchText = ref('')
const detailVisible = ref(false)
const currentRecord = ref(null)

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: '8%' },
  { title: '任务名称', dataIndex: 'name', key: 'name' },
  { title: '开始时间', dataIndex: 'startTime', key: 'startTime', width: '16%' },
  { title: '结束时间', dataIndex: 'endTime', key: 'endTime', width: '16%' },
  { title: '耗时', dataIndex: 'duration', key: 'duration', width: '10%' },
  { title: '状态', key: 'status', width: '10%' },
  { title: '操作', key: 'action', width: '80px' }
]

const filteredHistory = computed(() => {
  let list = taskStore.history
  if (searchText.value) {
    const q = searchText.value.toLowerCase()
    list = list.filter((r) => (r.name || '').toLowerCase().includes(q))
  }
  if (statusFilter.value) {
    list = list.filter((r) => r.status === statusFilter.value)
  }
  return list
})

function getStatusColor(status) {
  const map = {
    成功: 'green',
    失败: 'red',
    进行中: 'blue'
  }
  return map[status] || 'default'
}

function showDetail(record) {
  currentRecord.value = record
  detailVisible.value = true
}

function exportHistory() {
  message.info('导出功能开发中')
}

onMounted(() => {
  taskStore.fetchHistory()
})
</script>

<style scoped>
.history {
  padding: 0;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
  color: rgba(0, 0, 0, 0.88);
}

.route-item {
  padding: 8px 0;
  border-bottom: 1px dashed rgba(0, 0, 0, 0.12);
  font-size: 13px;
}

.route-item:last-child {
  border-bottom: none;
}
</style>
