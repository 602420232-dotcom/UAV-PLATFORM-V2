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
            <a-option value="">全部</a-option>
            <a-option value="成功">成功</a-option>
            <a-option value="失败">失败</a-option>
            <a-option value="进行中">进行中</a-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-date-picker v-model:value="dateRange" range-picker placeholder="选择时间范围" style="width: 100%" />
        </a-col>
        <a-col :span="4">
          <a-button type="primary" block @click="searchHistory">
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
      <a-table :columns="columns" :data-source="historyData" :loading="loading" @change="handleTableChange">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">{{ record.status }}</a-tag>
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
          <a-descriptions-item label="状态"><a-tag :color="getStatusColor(selectedRecord.status)">{{ selectedRecord.status }}</a-tag></a-descriptions-item>
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
                <p>风险等级: <a-tag :color="getRiskColor(route.risk)">{{ route.risk }}</a-tag></p>
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
import { SearchOutlined, EyeOutlined, DownloadOutlined } from '@ant-design/icons-vue'

// 响应式数据
const searchKeyword = ref('')
const statusFilter = ref('')
const dateRange = ref(null)
const loading = ref(false)
const historyData = ref([])
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

// 方法
const getStatusColor = (status) => {
  const colorMap = {
    '成功': 'green',
    '失败': 'red',
    '进行中': 'blue'
  }
  return colorMap[status] || 'default'
}

const getRiskColor = (risk) => {
  const colorMap = {
    '低': 'green',
    '中': 'orange',
    '高': 'red'
  }
  return colorMap[risk] || 'default'
}

const searchHistory = async () => {
  loading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 模拟数据
    historyData.value = generateMockData()
  } catch (error) {
    console.error('搜索失败:', error)
  } finally {
    loading.value = false
  }
}

const handleTableChange = (pagination, filters, sorter) => {
  console.log('表格变化:', pagination, filters, sorter)
  // 这里可以处理分页、排序等
}

const viewDetails = (record) => {
  selectedRecord.value = record
  detailModalVisible.value = true
}

const exportResult = (record) => {
  console.log('导出结果:', record)
  // 这里可以实现导出功能
  alert('导出功能已触发')
}

const generateMockData = () => {
  return [
    {
      id: 1,
      name: '路径规划任务1',
      startTime: '2024-01-01 10:00:00',
      endTime: '2024-01-01 10:02:30',
      status: '成功',
      duration: '2分30秒',
      droneCount: 2,
      taskCount: 3,
      totalDistance: 1500,
      totalTime: 25,
      routes: [
        {
          droneId: 1,
          path: ['基地', '任务点1', '任务点3', '基地'],
          distance: 800,
          time: 12,
          risk: '低'
        },
        {
          droneId: 2,
          path: ['基地', '任务点2', '基地'],
          distance: 700,
          time: 13,
          risk: '低'
        }
      ],
      weatherData: {
        windSpeed: 5.2,
        windDirection: 135,
        temperature: 25.5,
        humidity: 65,
        turbulence: '低',
        visibility: 10
      }
    },
    {
      id: 2,
      name: '气象预测任务',
      startTime: '2024-01-01 09:45:00',
      endTime: '2024-01-01 09:46:15',
      status: '成功',
      duration: '1分15秒',
      droneCount: 0,
      taskCount: 0,
      totalDistance: 0,
      totalTime: 0,
      routes: [],
      weatherData: {
        windSpeed: 4.8,
        windDirection: 120,
        temperature: 24.8,
        humidity: 60,
        turbulence: '低',
        visibility: 12
      }
    },
    {
      id: 3,
      name: '路径规划任务2',
      startTime: '2024-01-01 09:30:00',
      endTime: '2024-01-01 09:33:45',
      status: '成功',
      duration: '3分45秒',
      droneCount: 3,
      taskCount: 5,
      totalDistance: 2500,
      totalTime: 40,
      routes: [
        {
          droneId: 1,
          path: ['基地', '任务点1', '任务点3', '基地'],
          distance: 900,
          time: 15,
          risk: '低'
        },
        {
          droneId: 2,
          path: ['基地', '任务点2', '任务点5', '基地'],
          distance: 800,
          time: 14,
          risk: '中'
        },
        {
          droneId: 3,
          path: ['基地', '任务点4', '基地'],
          distance: 800,
          time: 11,
          risk: '低'
        }
      ],
      weatherData: {
        windSpeed: 6.5,
        windDirection: 90,
        temperature: 26.2,
        humidity: 55,
        turbulence: '中',
        visibility: 8
      }
    },
    {
      id: 4,
      name: '贝叶斯同化任务',
      startTime: '2024-01-01 09:15:00',
      endTime: '2024-01-01 09:18:30',
      status: '成功',
      duration: '3分30秒',
      droneCount: 0,
      taskCount: 0,
      totalDistance: 0,
      totalTime: 0,
      routes: [],
      weatherData: {
        windSpeed: 5.0,
        windDirection: 135,
        temperature: 25.0,
        humidity: 62,
        turbulence: '低',
        visibility: 10
      }
    }
  ]
}

// 生命周期
onMounted(() => {
  searchHistory()
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