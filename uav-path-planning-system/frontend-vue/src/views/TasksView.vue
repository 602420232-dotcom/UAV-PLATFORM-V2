<template>
  <a-card title="任务管理" class="tasks-card">
    <a-row :gutter="[16, 16]">
      <a-col :span="24">
        <a-card>
          <a-row :gutter="[16, 16]">
            <a-col :span="8">
              <a-button type="primary" @click="showAddTaskModal">
                <template #icon><PlusOutlined /></template>
                添加任务
              </a-button>
            </a-col>
            <a-col :span="8">
              <a-button @click="importTasks">
                <template #icon><UploadOutlined /></template>
                导入任务
              </a-button>
            </a-col>
            <a-col :span="8">
              <a-button @click="exportTasks">
                <template #icon><DownloadOutlined /></template>
                导出任务
              </a-button>
            </a-col>
          </a-row>
        </a-card>
      </a-col>

      <a-col :span="24">
        <a-card>
          <template #extra>
            <a-input-search
              v-model:value="searchText"
              placeholder="搜索任务"
              style="width: 200px"
              @search="onSearch"
            />
          </template>
          <a-spin :spinning="store.loading.tasks">
            <a-table :columns="columns" :data-source="store.tasks" row-key="id">
              <template #status="{ record }">
                <a-tag :color="statusColors[record.status]">{{ record.status }}</a-tag>
              </template>
              <template #action="{ record }">
                <a-button size="small" @click="editTask(record)">编辑</a-button>
                <a-button size="small" danger @click="deleteTask(record.id)">删除</a-button>
                <a-button size="small" @click="assignTask(record.id)">分配</a-button>
              </template>
            </a-table>
          </a-spin>
        </a-card>
      </a-col>
    </a-row>

    <a-modal title="添加任务" v-model:open="addTaskModalVisible" @ok="handleAddTask" :confirm-loading="submitting">
      <a-form :model="newTask" layout="vertical">
        <a-form-item label="任务名称">
          <a-input v-model:value="newTask.name" />
        </a-form-item>
        <a-form-item label="任务类型">
          <a-select v-model:value="newTask.type">
            <a-select-option value="delivery">配送</a-select-option>
            <a-select-option value="inspection">巡检</a-select-option>
            <a-select-option value="survey">测绘</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="任务点">
          <a-input v-model:value="newTask.location" placeholder="经度,纬度" />
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
  </a-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, UploadOutlined, DownloadOutlined } from '@ant-design/icons-vue'
import { getTasks, createTask } from '../api/tasks'
import { useDataStore } from '../stores/dataStore'
import { statusColors } from '../utils/demoData'

const store = useDataStore()

const submitting = ref(false)
const searchText = ref('')
const addTaskModalVisible = ref(false)

const newTask = ref({
  name: '',
  type: 'delivery',
  location: '',
  priority: 'medium',
  description: '',
})

const columns = [
  { title: '任务ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: '任务名称', dataIndex: 'name', key: 'name' },
  { title: '任务类型', dataIndex: 'type', key: 'type', width: 100 },
  { title: '任务点', dataIndex: 'location', key: 'location' },
  { title: '优先级', dataIndex: 'priority', key: 'priority', width: 80 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 100 },
  { title: '操作', key: 'action', width: 220 },
]

onMounted(() => {
  store.fetchTasks()
})

const showAddTaskModal = () => {
  addTaskModalVisible.value = true
}

const handleAddTask = async () => {
  if (!newTask.value.name.trim()) {
    message.error('请输入任务名称')
    return
  }
  submitting.value = true
  try {
    await createTask({
      name: newTask.value.name,
      type: newTask.value.type,
      location: newTask.value.location,
      priority: newTask.value.priority,
      description: newTask.value.description,
    })
    message.success('任务创建成功')
    addTaskModalVisible.value = false
    newTask.value = { name: '', type: 'delivery', location: '', priority: 'medium', description: '' }
    store.fetchTasks()
  } catch (e) {
    message.error('创建失败：' + e.message)
  } finally {
    submitting.value = false
  }
}

const onSearch = async () => {
  await store.fetchTasks({ keyword: searchText.value })
}

const editTask = (record) => { message.info('编辑任务: ' + record.name) }
const deleteTask = async (id) => {
  store.tasks = store.tasks.filter(t => t.id !== id)
  message.success('删除成功')
}
const assignTask = (id) => { message.info('分配任务: ' + id) }
const importTasks = () => { message.info('导入功能开发中') }
const exportTasks = () => { message.info('导出功能开发中') }
</script>

<style scoped>
.tasks-card { margin-bottom: 24px; }
</style>
