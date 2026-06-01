<template>
  <a-card title="历史记录" class="history-card">
    <!-- 搜索和筛选 -->
    <div class="search-filter">
      <a-row :gutter="[16, 16]">
        <a-col :span="8">
          <a-input v-model:value="searchKeyword" placeholder="搜索任务名称" prefix="🔍" />
        </a-col>
        <a-col :span="6">
          <a-select v-model:value="statusFilter" placeholder="状态筛选">
            <a-select-option value="">全部</a-select-option>
            <a-select-option value="成功">成功</a-select-option>
            <a-select-option value="失败">失败</a-select-option>
            <a-select-option value="进行中">进行中</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-date-picker v-model:value="dateRange" range-picker placeholder="选择时间范围" style="width: 100%" />
        </a-col>
        <a-col :span="4">
          <a-button type="primary" block @click="store.fetchHistory">
            <template #icon>
              <SearchOutlined />
            </template>
            搜索
          </a-button>
        </a-col>
      </a-row>
    </div>

    <!-- 历史记录表格 -->
    <div class="history-table" style="margin-top: 16px">
      <a-table :columns="columns" :data-source="store.historyData" :loading="store.loading.history" @change="handleTableChange">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColors[record.status]">{{ record.status }}</a-tag>
          </template>
          <template v-else-if="column.key === 'actions'">
            <a-button size="small" @click="viewDetails(record)">
              <template #icon>
                <EyeOutlined />
              </template>
              查看详情
            </a-button>
            <a-button size="small" style="margin-left: 8px" @click="exportResult(record)">
              <template #icon>
                <DownloadOutlined />
              </template>
              导出
            </a-button>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 详情模态框 -->
    <a-modal v-model:open="detailModalVisible" title="任务详情" width="800px">
      <div v-if="selectedRecord" class="detail-content">
        <a-descriptions bordered column="2">
          <a-descriptions-item label="任务ID">{{ selectedRecord.id }}</a-descriptions-item>
          <a-descriptions-item label="任务名称">{{ selectedRecord.name }}</a-descriptions-item>
          <a-descriptions-item label="开始时间">{{ selectedRecord.startTime }}</a-descriptions-item>
          <a-descriptions-item label="结束时间">{{ selectedRecord.endTime }}</a-descriptions-item>
          <a-descriptions-item label="状态"><a-tag :color="statusColors[selectedRecord.status]">{{ selectedRecord.status }}</a-tag></a-descriptions-item>
          <a-descriptions-item label="耗时">{{ selectedRecord.duration }}</a-descriptions-item>
          <a-descriptions-item label="无人机数量" :span="2">{{ selectedRecord.droneCount }}</a-descriptions-item>
          <a-descriptions-item label="任务点数量" :span="2">{{ selectedRecord.taskCount }}</a-descriptions-item>
          <a-descriptions-item label="总距离" :span="2">{{ selectedRecord.totalDistance }} m</a-descriptions-item>
          <a-descriptions-item label="总时间" :span="2">{{ selectedRecord.totalTime }} min</a-descriptions-item>
        </a-descriptions>

        <!-- 路径详情 -->
        <div style="margin-top: 24px">
          <h4>路径详情</h4>
          <a-collapse v-model:activeKey="activePathKey">
            <a-collapse-panel v-for="(route, index) in selectedRecord.routes" :key="index" :title="`无人机 ${route.droneId}`">
              <div class="route-detail">
                <p>路径: {{ route.path.join(' → ') }}</p>
                <p>距离: {{ route.distance }} m</p>
                <p>时间: {{ route.time }} min</p>
                <p>风险等级: <a-tag :color="riskColors[route.risk]">{{ route.risk }}</a-tag></p>
              </div>
            </a-collapse-panel>
          </a-collapse>
        </div>

        <!-- 气象数据 -->
        <div style="margin-top: 24px">
          <h4>气象数据</h4>
          <a-descriptions bordered column="2">
            <a-descriptions-item label="风速">{{ selectedRecord.weatherData.windSpeed }} m/s</a-descriptions-item>
            <a-descriptions-item label="风向">{{ selectedRecord.weatherData.windDirection }}°</a-descriptions-item>
            <a-descriptions-item label="温度">{{ selectedRecord.weatherData.temperature }} °C</a-descriptions-item>
            <a-descriptions-item label="湿度">{{ selectedRecord.weatherData.humidity }}%</a-descriptions-item>
            <a-descriptions-item label="湍流强度">{{ selectedRecord.weatherData.turbulence }}</a-descriptions-item>
            <a-descriptions-item label="能见度">{{ selectedRecord.weatherData.visibility }} km</a-descriptions-item>
          </a-descriptions>
        </div>
      </div>
      <template #footer>
        <a-button @click="detailModalVisible = false">关闭</a-button>
      </template>
    </a-modal>
  </a-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { SearchOutlined, EyeOutlined, DownloadOutlined } from '@ant-design/icons-vue'
import { useDataStore } from '../stores/dataStore'
import { statusColors, riskColors } from '../utils/demoData'

const store = useDataStore()

// 响应式数据
const searchKeyword = ref('')
const statusFilter = ref('')
const dateRange = ref(null)
const detailModalVisible = ref(false)
const selectedRecord = ref(null)
const activePathKey = ref(['0'])

// 表格列配置
const columns = [
  {
    title: '任务ID',
    dataIndex: 'id',
    key: 'id'
  },
  {
    title: '任务名称',
    dataIndex: 'name',
    key: 'name'
  },
  {
    title: '开始时间',
    dataIndex: 'startTime',
    key: 'startTime'
  },
  {
    title: '结束时间',
    dataIndex: 'endTime',
    key: 'endTime'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status'
  },
  {
    title: '耗时',
    dataIndex: 'duration',
    key: 'duration'
  },
  {
    title: '操作',
    key: 'actions',
    width: 150
  }
]

const handleTableChange = (_pagination, _filters, _sorter) => {
  // 分页、排序等处理（当接入真实API后实现）
}

const viewDetails = (record) => {
  selectedRecord.value = record
  detailModalVisible.value = true
}

const exportResult = (record) => {
  message.info(`正在导出任务: ${record?.name || record?.id}`)
}

// 生命周期
onMounted(() => {
  store.fetchHistory()
})
</script>

<style scoped>
.history-card {
  margin-bottom: 24px;
}

.search-filter {
  margin-bottom: 16px;
}

.detail-content {
  max-height: 600px;
  overflow-y: auto;
}

.route-detail {
  padding: 16px;
  background: #f5f5f5;
  border-radius: 4px;
}

.route-detail p {
  margin: 8px 0;
}
</style>