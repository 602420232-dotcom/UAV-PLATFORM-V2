<template>
  <a-card title="无人机管理" class="drones-card">
    <a-row :gutter="[16, 16]">
      <!-- 无人机操作 -->
      <a-col :span="24">
        <a-card>
          <a-row :gutter="[16, 16]">
            <a-col :span="8">
              <a-button type="primary" @click="showAddDroneModal">
                <template #icon>
                  <PlusOutlined />
                </template>
                添加无人机
              </a-button>
            </a-col>
            <a-col :span="8">
              <a-button @click="triggerImport">
                <template #icon>
                  <UploadOutlined />
                </template>
                导入无人机
              </a-button>
            </a-col>
            <a-col :span="8">
              <a-button @click="exportDrones">
                <template #icon>
                  <DownloadOutlined />
                </template>
                导出无人机
              </a-button>
            </a-col>
          </a-row>
        </a-card>
      </a-col>
      
      <!-- 无人机状态概览 -->
      <a-col :span="24">
        <a-card title="无人机状态概览">
          <a-row :gutter="[16, 16]">
            <a-col :span="6">
              <a-statistic title="总数量" :value="drones.length" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="在线" :value="onlineCount" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="执行任务" :value="taskingCount" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="待命" :value="idleCount" />
            </a-col>
          </a-row>
        </a-card>
      </a-col>
      
      <!-- 无人机列表 -->
      <a-col :span="24">
        <a-card>
          <template #extra>
            <a-input-search v-model:value="searchQuery" placeholder="搜索无人机" style="width: 200px" />
          </template>
          <a-table :columns="columns" :data-source="filteredDrones" row-key="id">
            <template #status="{ record }">
              <a-tag :color="getStatusColor(record.status)">{{ record.status }}</a-tag>
            </template>
            <template #action="{ record }">
              <a-button size="small" @click="editDrone(record)">编辑</a-button>
              <a-button size="small" danger @click="deleteDrone(record.id)">删除</a-button>
              <a-button size="small" @click="viewDetails(record)">详情</a-button>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>
    
    <!-- 添加/编辑无人机模态框 -->
    <a-modal :title="isEditing ? '编辑无人机' : '添加无人机'" v-model:open="addDroneModalVisible" @ok="handleModalOk">
      <a-form :model="newDrone" layout="vertical">
        <a-form-item label="无人机编号">
          <a-input v-model:value="newDrone.id" :disabled="isEditing" />
        </a-form-item>
        <a-form-item label="无人机名称">
          <a-input v-model:value="newDrone.name" />
        </a-form-item>
        <a-form-item label="类型">
          <a-select v-model:value="newDrone.type">
            <a-select-option value="multirotor">多旋翼</a-select-option>
            <a-select-option value="fixed-wing">固定翼</a-select-option>
            <a-select-option value="hybrid">混合动力</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="最大载重">
          <a-input-number v-model:value="newDrone.maxPayload" :min="0" />
        </a-form-item>
        <a-form-item label="最大续航时间">
          <a-input-number v-model:value="newDrone.maxEndurance" :min="0" />
        </a-form-item>
        <a-form-item label="最大速度">
          <a-input-number v-model:value="newDrone.maxSpeed" :min="0" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="newDrone.description" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 无人机详情模态框 -->
    <a-modal title="无人机详情" v-model:open="detailsModalVisible" :footer="null">
      <template v-if="selectedDrone">
        <a-descriptions bordered :column="1">
          <a-descriptions-item label="无人机编号">{{ selectedDrone.id }}</a-descriptions-item>
          <a-descriptions-item label="无人机名称">{{ selectedDrone.name }}</a-descriptions-item>
          <a-descriptions-item label="类型">
            {{ { multirotor: '多旋翼', 'fixed-wing': '固定翼', hybrid: '混合动力' }[selectedDrone.type] || selectedDrone.type }}
          </a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag :color="getStatusColor(selectedDrone.status)">{{ selectedDrone.status }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="位置坐标">{{ selectedDrone.location }}</a-descriptions-item>
          <a-descriptions-item label="电量">
            <a-progress :percent="selectedDrone.battery" size="small" :status="selectedDrone.battery <= 20 ? 'exception' : 'active'" />
          </a-descriptions-item>
          <a-descriptions-item label="最大载重(kg)">{{ selectedDrone.maxPayload }}</a-descriptions-item>
          <a-descriptions-item label="最大续航(min)">{{ selectedDrone.maxEndurance }}</a-descriptions-item>
          <a-descriptions-item label="最大速度(km/h)">{{ selectedDrone.maxSpeed }}</a-descriptions-item>
          <a-descriptions-item label="描述">{{ selectedDrone.description }}</a-descriptions-item>
        </a-descriptions>
      </template>
    </a-modal>

    <!-- 隐藏的文件输入 -->
    <input type="file" ref="fileInputRef" accept=".csv" style="display: none" @change="handleFileImport" />
  </a-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { PlusOutlined, UploadOutlined, DownloadOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

// 响应式数据
const addDroneModalVisible = ref(false)
const isEditing = ref(false)
const detailsModalVisible = ref(false)
const selectedDrone = ref(null)
const searchQuery = ref('')
const fileInputRef = ref(null)

const newDrone = ref({
  id: '',
  name: '',
  type: 'multirotor',
  maxPayload: 5,
  maxEndurance: 60,
  maxSpeed: 50,
  description: ''
})

// 模拟无人机数据
const drones = ref([
  {
    id: 'UAV-001',
    name: '无人机1',
    type: 'multirotor',
    maxPayload: 5,
    maxEndurance: 60,
    maxSpeed: 50,
    status: '在线',
    location: '39.9042, 116.4074',
    battery: 85,
    description: '配送无人机'
  },
  {
    id: 'UAV-002',
    name: '无人机2',
    type: 'multirotor',
    maxPayload: 10,
    maxEndurance: 45,
    maxSpeed: 40,
    status: '执行任务',
    location: '39.9142, 116.4174',
    battery: 60,
    description: '巡检无人机'
  },
  {
    id: 'UAV-003',
    name: '无人机3',
    type: 'fixed-wing',
    maxPayload: 20,
    maxEndurance: 120,
    maxSpeed: 80,
    status: '待命',
    location: '39.9042, 116.4074',
    battery: 90,
    description: '测绘无人机'
  }
])

// 计算属性
const onlineCount = computed(() => {
  return drones.value.filter(drone => drone.status === '在线').length
})

const taskingCount = computed(() => {
  return drones.value.filter(drone => drone.status === '执行任务').length
})

const idleCount = computed(() => {
  return drones.value.filter(drone => drone.status === '待命').length
})

// 搜索过滤
const filteredDrones = computed(() => {
  if (!searchQuery.value) {
    return drones.value
  }
  const q = searchQuery.value.toLowerCase()
  return drones.value.filter(drone => drone.name.toLowerCase().includes(q))
})

// 表格列配置
const columns = [
  {
    title: '无人机编号',
    dataIndex: 'id',
    key: 'id'
  },
  {
    title: '无人机名称',
    dataIndex: 'name',
    key: 'name'
  },
  {
    title: '类型',
    dataIndex: 'type',
    key: 'type'
  },
  {
    title: '最大载重(kg)',
    dataIndex: 'maxPayload',
    key: 'maxPayload'
  },
  {
    title: '最大续航(min)',
    dataIndex: 'maxEndurance',
    key: 'maxEndurance'
  },
  {
    title: '最大速度(km/h)',
    dataIndex: 'maxSpeed',
    key: 'maxSpeed'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    slots: { customRender: 'status' }
  },
  {
    title: '电量(%)',
    dataIndex: 'battery',
    key: 'battery'
  },
  {
    title: '操作',
    key: 'action',
    slots: { customRender: 'action' }
  }
]

// ID 生成
const generateId = () => {
  const maxNum = drones.value.reduce((max, drone) => {
    const match = drone.id.match(/UAV-(\d+)/)
    const num = match ? parseInt(match[1], 10) : 0
    return Math.max(max, num)
  }, 0)
  return `UAV-${String(maxNum + 1).padStart(3, '0')}`
}

// 重置表单
const resetNewDrone = () => {
  newDrone.value = {
    id: '',
    name: '',
    type: 'multirotor',
    maxPayload: 5,
    maxEndurance: 60,
    maxSpeed: 50,
    description: ''
  }
}

// 方法
const showAddDroneModal = () => {
  isEditing.value = false
  resetNewDrone()
  addDroneModalVisible.value = true
}

const handleAddDrone = () => {
  drones.value.push({
    id: newDrone.value.id || generateId(),
    name: newDrone.value.name,
    type: newDrone.value.type,
    maxPayload: newDrone.value.maxPayload,
    maxEndurance: newDrone.value.maxEndurance,
    maxSpeed: newDrone.value.maxSpeed,
    status: '待命',
    location: '39.9042, 116.4074',
    battery: 100,
    description: newDrone.value.description
  })
  resetNewDrone()
  addDroneModalVisible.value = false
}

const handleEditDrone = () => {
  const index = drones.value.findIndex(drone => drone.id === newDrone.value.id)
  if (index !== -1) {
    drones.value[index] = {
      ...drones.value[index],
      name: newDrone.value.name,
      type: newDrone.value.type,
      maxPayload: newDrone.value.maxPayload,
      maxEndurance: newDrone.value.maxEndurance,
      maxSpeed: newDrone.value.maxSpeed,
      description: newDrone.value.description
    }
  }
  resetNewDrone()
  isEditing.value = false
  addDroneModalVisible.value = false
}

const handleModalOk = () => {
  if (isEditing.value) {
    handleEditDrone()
  } else {
    handleAddDrone()
  }
}

const getStatusColor = (status) => {
  const colorMap = {
    '在线': 'green',
    '执行任务': 'blue',
    '待命': 'orange',
    '维护中': 'purple',
    '故障': 'red'
  }
  return colorMap[status] || 'default'
}

const editDrone = (record) => {
  isEditing.value = true
  newDrone.value = {
    id: record.id,
    name: record.name,
    type: record.type,
    maxPayload: record.maxPayload,
    maxEndurance: record.maxEndurance,
    maxSpeed: record.maxSpeed,
    description: record.description
  }
  addDroneModalVisible.value = true
}

const deleteDrone = (id) => {
  drones.value = drones.value.filter(drone => drone.id !== id)
}

const viewDetails = (record) => {
  selectedDrone.value = { ...record }
  detailsModalVisible.value = true
}

const triggerImport = () => {
  fileInputRef.value?.click()
}

const handleFileImport = (event) => {
  const file = event.target.files[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (e) => {
    const text = e.target?.result
    if (typeof text !== 'string') return

    const lines = text.split('\n').filter(line => line.trim() !== '')
    let importedCount = 0

    for (let i = 0; i < lines.length; i++) {
      const parts = lines[i].split(',').map(s => s.trim())
      // 跳过标题行
      if (i === 0 && parts[0] === 'name') continue

      const [name, type, maxPayload, maxEndurance, maxSpeed, description] = parts
      if (!name) continue

      drones.value.push({
        id: generateId(),
        name,
        type: type || 'multirotor',
        maxPayload: parseFloat(maxPayload) || 5,
        maxEndurance: parseFloat(maxEndurance) || 60,
        maxSpeed: parseFloat(maxSpeed) || 50,
        status: '待命',
        location: '39.9042, 116.4074',
        battery: 100,
        description: description || ''
      })
      importedCount++
    }

    message.success(`成功导入 ${importedCount} 架无人机`)
    // 重置 file input 以允许重复选择同一文件
    event.target.value = ''
  }
  reader.readAsText(file)
}

const exportDrones = () => {
  const header = 'name,type,status,location,battery,maxPayload,maxEndurance,maxSpeed,description'
  const rows = drones.value.map(drone => {
    return [
      drone.name,
      drone.type,
      drone.status,
      drone.location,
      drone.battery,
      drone.maxPayload,
      drone.maxEndurance,
      drone.maxSpeed,
      drone.description
    ].join(',')
  })
  const csv = [header, ...rows].join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'drones_export.csv'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.drones-card {
  margin-bottom: 24px;
}
</style>
