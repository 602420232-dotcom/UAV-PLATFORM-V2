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
              <a-button @click="importDrones">
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
            <a-input-search placeholder="搜索无人机" style="width: 200px" />
          </template>
          <a-table :columns="columns" :data-source="drones" row-key="id">
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
    
    <!-- 添加无人机模态框 -->
    <a-modal title="添加无人机" v-model:open="addDroneModalVisible" @ok="handleAddDrone">
      <a-form :model="newDrone" layout="vertical">
        <a-form-item label="无人机编号">
          <a-input v-model:value="newDrone.id" />
        </a-form-item>
        <a-form-item label="无人机名称">
          <a-input v-model:value="newDrone.name" />
        </a-form-item>
        <a-form-item label="类型">
          <a-select v-model:value="newDrone.type">
            <a-option value="multirotor">多旋翼</a-option>
            <a-option value="fixed-wing">固定翼</a-option>
            <a-option value="hybrid">混合动力</a-option>
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
  </a-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { PlusOutlined, UploadOutlined, DownloadOutlined } from '@ant-design/icons-vue'

// 响应式数据
const addDroneModalVisible = ref(false)
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

// 方法
const showAddDroneModal = () => {
  addDroneModalVisible.value = true
}

const handleAddDrone = () => {
  // 添加新无人机
  drones.value.push({
    id: newDrone.value.id,
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
  
  // 重置表单
  newDrone.value = {
    id: '',
    name: '',
    type: 'multirotor',
    maxPayload: 5,
    maxEndurance: 60,
    maxSpeed: 50,
    description: ''
  }
  
  // 关闭模态框
  addDroneModalVisible.value = false
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
  console.log('编辑无人机:', record)
  // 这里可以打开编辑模态框
}

const deleteDrone = (id) => {
  drones.value = drones.value.filter(drone => drone.id !== id)
}

const viewDetails = (record) => {
  console.log('查看详情:', record)
  // 这里可以打开详情模态框
}

const importDrones = () => {
  console.log('导入无人机')
  // 这里可以实现文件上传
}

const exportDrones = () => {
  console.log('导出无人机')
  // 这里可以实现文件下载
}
</script>

<style scoped>
.drones-card {
  margin-bottom: 24px;
}
</style>