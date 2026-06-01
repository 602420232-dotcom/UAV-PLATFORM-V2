<template>
  <a-card title="任务管理" class="tasks-card">
    <a-row :gutter="[16, 16]">
      <!-- 任务操作 -->
      <a-col :span="24">
        <a-card>
          <a-row :gutter="[16, 16]">
            <a-col :span="8">
              <a-button type="primary" @click="showAddTaskModal">
                <template #icon>
                  <PlusOutlined />
                </template>
                添加任务
              </a-button>
            </a-col>
            <a-col :span="8">
              <a-button @click="importTasks">
                <template #icon>
                  <UploadOutlined />
                </template>
                导入任务
              </a-button>
            </a-col>
            <a-col :span="8">
              <a-button @click="exportTasks">
                <template #icon>
                  <DownloadOutlined />
                </template>
                导出任务
              </a-button>
            </a-col>
          </a-row>
        </a-card>
      </a-col>
      
      <!-- 任务列表 -->
      <a-col :span="24">
        <a-card>
          <template #extra>
            <a-input-search placeholder="搜索任务" style="width: 200px" />
          </template>
          <a-table :columns="columns" :data-source="tasks" row-key="id">
            <template #status="{ record }">
              <a-tag :color="getStatusColor(record.status)">{{ record.status }}</a-tag>
            </template>
            <template #action="{ record }">
              <a-button size="small" @click="editTask(record)">编辑</a-button>
              <a-button size="small" danger @click="deleteTask(record.id)">删除</a-button>
              <a-button size="small" @click="assignTask(record.id)">分配</a-button>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>
    
    <!-- 添加任务模态框 -->
    <a-modal title="添加任务" v-model:open="addTaskModalVisible" @ok="handleAddTask">
      <a-form :model="newTask" layout="vertical">
        <a-form-item label="任务名称">
          <a-input v-model:value="newTask.name" />
        </a-form-item>
        <a-form-item label="任务类型">
          <a-select v-model:value="newTask.type">
            <a-option value="delivery">配送</a-option>
            <a-option value="inspection">巡检</a-option>
            <a-option value="rescue">救援</a-option>
            <a-option value="survey">测绘</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="任务点">
          <a-input v-model:value="newTask.location" placeholder="经纬度，格式：lat,lng" />
        </a-form-item>
        <a-form-item label="开始时间">
          <a-date-picker v-model:value="newTask.startTime" show-time style="width: 100%" />
        </a-form-item>
        <a-form-item label="结束时间">
          <a-date-picker v-model:value="newTask.endTime" show-time style="width: 100%" />
        </a-form-item>
        <a-form-item label="优先级">
          <a-select v-model:value="newTask.priority">
            <a-option value="low">低</a-option>
            <a-option value="medium">中</a-option>
            <a-option value="high">高</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="newTask.description" />
        </a-form-item>
      </a-form>
    </a-modal>
  </a-card>
</template>

<script setup>
import { ref } from 'vue'
import { PlusOutlined, UploadOutlined, DownloadOutlined } from '@ant-design/icons-vue'

// 响应式数据
const addTaskModalVisible = ref(false)
const newTask = ref({
  name: '',
  type: 'delivery',
  location: '',
  startTime: new Date(),
  endTime: new Date(),
  priority: 'medium',
  description: ''
})

// 模拟任务数据
const tasks = ref([
  {
    id: 1,
    name: '配送任务1',
    type: 'delivery',
    location: '39.9042, 116.4074',
    startTime: '2024-01-01 09:00',
    endTime: '2024-01-01 10:00',
    priority: 'high',
    status: '待分配',
    description: '紧急配送任务'
  },
  {
    id: 2,
    name: '巡检任务1',
    type: 'inspection',
    location: '39.9142, 116.4174',
    startTime: '2024-01-01 10:00',
    endTime: '2024-01-01 11:00',
    priority: 'medium',
    status: '已分配',
    description: '电力线路巡检'
  },
  {
    id: 3,
    name: '测绘任务1',
    type: 'survey',
    location: '39.9242, 116.4274',
    startTime: '2024-01-01 11:00',
    endTime: '2024-01-01 12:00',
    priority: 'low',
    status: '已完成',
    description: '区域测绘'
  }
])

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
    title: '任务类型',
    dataIndex: 'type',
    key: 'type'
  },
  {
    title: '任务点',
    dataIndex: 'location',
    key: 'location'
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
    title: '优先级',
    dataIndex: 'priority',
    key: 'priority'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    slots: { customRender: 'status' }
  },
  {
    title: '操作',
    key: 'action',
    slots: { customRender: 'action' }
  }
]

// 方法
const showAddTaskModal = () => {
  addTaskModalVisible.value = true
}

const handleAddTask = () => {
  // 添加新任务
  const newId = tasks.value.length + 1
  tasks.value.push({
    id: newId,
    name: newTask.value.name,
    type: newTask.value.type,
    location: newTask.value.location,
    startTime: newTask.value.startTime.toLocaleString(),
    endTime: newTask.value.endTime.toLocaleString(),
    priority: newTask.value.priority,
    status: '待分配',
    description: newTask.value.description
  })
  
  // 重置表单
  newTask.value = {
    name: '',
    type: 'delivery',
    location: '',
    startTime: new Date(),
    endTime: new Date(),
    priority: 'medium',
    description: ''
  }
  
  // 关闭模态框
  addTaskModalVisible.value = false
}

const getStatusColor = (status) => {
  const colorMap = {
    '待分配': 'blue',
    '已分配': 'orange',
    '执行中': 'purple',
    '已完成': 'green',
    '已取消': 'red'
  }
  return colorMap[status] || 'default'
}

const editTask = (record) => {
  console.log('编辑任务:', record)
  // 这里可以打开编辑模态框
}

const deleteTask = (id) => {
  tasks.value = tasks.value.filter(task => task.id !== id)
}

const assignTask = (id) => {
  console.log('分配任务:', id)
  // 这里可以打开分配模态框
}

const importTasks = () => {
  console.log('导入任务')
  // 这里可以实现文件上传
}

const exportTasks = () => {
  console.log('导出任务')
  // 这里可以实现文件下载
}
</script>

<style scoped>
.tasks-card {
  margin-bottom: 24px;
}
</style>