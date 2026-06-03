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
              <a-button size="small" @click="assignTask(record)">分配</a-button>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>
    
    <!-- 添加/编辑任务模态框 -->
    <a-modal :title="isEditing ? '编辑任务' : '添加任务'" v-model:open="addTaskModalVisible" @ok="isEditing ? handleEditTask : handleAddTask">
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
            <a-select-option value="low">低</a-select-option>
            <a-select-option value="medium">中</a-select-option>
            <a-select-option value="high">高</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model:value="newTask.description" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 分配任务模态框 -->
    <a-modal title="分配任务" v-model:open="assignModalVisible" @ok="confirmAssign" @cancel="assignModalVisible = false">
      <a-form layout="vertical">
        <a-form-item label="任务名称">
          <a-input :value="selectedTaskForAssign?.name" disabled />
        </a-form-item>
        <a-form-item label="选择无人机">
          <a-select v-model:value="assignDroneId" placeholder="请选择无人机">
            <a-select-option value="1">无人机1</a-select-option>
            <a-select-option value="2">无人机2</a-select-option>
            <a-select-option value="3">无人机3</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </a-card>
</template>

<script setup>
import { ref } from 'vue'
import { PlusOutlined, UploadOutlined, DownloadOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

// 响应式数据
const addTaskModalVisible = ref(false)
const isEditing = ref(false)
const editingTaskId = ref(null)
const assignModalVisible = ref(false)
const selectedTaskForAssign = ref(null)
const assignDroneId = ref(undefined)

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

// 工具函数
const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const resetNewTask = () => {
  newTask.value = {
    name: '',
    type: 'delivery',
    location: '',
    startTime: new Date(),
    endTime: new Date(),
    priority: 'medium',
    description: ''
  }
}

// 方法
const showAddTaskModal = () => {
  isEditing.value = false
  editingTaskId.value = null
  resetNewTask()
  addTaskModalVisible.value = true
}

const handleAddTask = () => {
  const newId = tasks.value.length > 0 ? Math.max(...tasks.value.map(t => t.id)) + 1 : 1
  tasks.value.push({
    id: newId,
    name: newTask.value.name,
    type: newTask.value.type,
    location: newTask.value.location,
    startTime: formatDate(newTask.value.startTime),
    endTime: formatDate(newTask.value.endTime),
    priority: newTask.value.priority,
    status: '待分配',
    description: newTask.value.description
  })
  resetNewTask()
  addTaskModalVisible.value = false
  message.success('任务添加成功')
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
  isEditing.value = true
  editingTaskId.value = record.id
  newTask.value = {
    name: record.name,
    type: record.type,
    location: record.location,
    startTime: record.startTime ? new Date(record.startTime) : new Date(),
    endTime: record.endTime ? new Date(record.endTime) : new Date(),
    priority: record.priority,
    description: record.description
  }
  addTaskModalVisible.value = true
}

const handleEditTask = () => {
  const index = tasks.value.findIndex(t => t.id === editingTaskId.value)
  if (index !== -1) {
    tasks.value[index] = {
      ...tasks.value[index],
      name: newTask.value.name,
      type: newTask.value.type,
      location: newTask.value.location,
      startTime: formatDate(newTask.value.startTime),
      endTime: formatDate(newTask.value.endTime),
      priority: newTask.value.priority,
      description: newTask.value.description
    }
  }
  resetNewTask()
  addTaskModalVisible.value = false
  message.success('任务编辑成功')
}

const deleteTask = (id) => {
  tasks.value = tasks.value.filter(task => task.id !== id)
  message.success('任务删除成功')
}

const assignTask = (record) => {
  selectedTaskForAssign.value = record
  assignDroneId.value = undefined
  assignModalVisible.value = true
}

const confirmAssign = () => {
  if (!assignDroneId.value) {
    message.warning('请选择无人机')
    return
  }
  const task = tasks.value.find(t => t.id === selectedTaskForAssign.value.id)
  if (task) {
    task.status = '已分配'
  }
  assignModalVisible.value = false
  message.success('任务分配成功')
}

const importTasks = () => {
  // 导入任务
}

const exportTasks = () => {
  if (tasks.value.length === 0) {
    message.warning('没有可导出的任务')
    return
  }
  const headers = ['任务ID', '任务名称', '任务类型', '任务点', '开始时间', '结束时间', '优先级', '状态', '描述']
  let csv = headers.join(',') + '\n'
  tasks.value.forEach(task => {
    const row = [task.id, task.name, task.type, task.location, task.startTime, task.endTime, task.priority, task.status, task.description]
    csv += row.join(',') + '\n'
  })
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'tasks_export.csv'
  a.click()
  URL.revokeObjectURL(url)
  message.success('任务导出成功')
}
</script>

<style scoped>
.tasks-card {
  margin-bottom: 24px;
}
</style>
