<template>
  <div class="tasks">
    <div class="page-title">任务管理</div>

    <a-row :gutter="[16, 16]">
      <a-col :span="24">
        <a-card>
          <a-row :gutter="[16, 16]" align="middle">
            <a-col :flex="1">
              <a-space>
                <a-button type="primary" @click="showAddTaskModal">
                  <template #icon><PlusOutlined /></template>
                  添加任务
                </a-button>
                <a-button @click="importTasks">
                  <template #icon><UploadOutlined /></template>
                  导入任务
                </a-button>
                <a-button @click="exportTasks">
                  <template #icon><DownloadOutlined /></template>
                  导出任务
                </a-button>
              </a-space>
            </a-col>
            <a-col :flex="300px">
              <a-input-search v-model:value="searchText" placeholder="搜索任务" allow-clear />
            </a-col>
          </a-row>
        </a-card>
      </a-col>

      <a-col :span="24">
        <a-card>
          <a-table
            :columns="columns"
            :data-source="filteredTasks"
            row-key="id"
            :loading="taskStore.loading"
            :pagination="{ pageSize: 10, showSizeChanger: true, showTotal: showTotal }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="getStatusColor(record.status)">{{ record.status }}</a-tag>
              </template>
              <template v-else-if="column.key === 'action'">
                <a-space>
                  <a-button size="small" @click="editTask(record)">编辑</a-button>
                  <a-button size="small" danger @click="deleteTask(record.id)">删除</a-button>
                  <a-button size="small" type="link" @click="assignTask(record)">分配无人机</a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>

    <!-- 添加/编辑任务模态框 -->
    <a-modal
      :title="isEditing ? '编辑任务' : '添加任务'"
      v-model:open="taskModalVisible"
      @ok="isEditing ? handleEditTask : handleAddTask"
      ok-text="保存"
      cancel-text="取消"
    >
      <a-form :model="taskForm" layout="vertical">
        <a-form-item label="任务名称" :rules="[{ required: true, message: '请输入任务名称' }]">
          <a-input v-model:value="taskForm.name" placeholder="请输入任务名称" />
        </a-form-item>
        <a-form-item label="任务类型">
          <a-select v-model:value="taskForm.type">
            <a-select-option value="delivery">配送任务</a-select-option>
            <a-select-option value="inspection">巡检任务</a-select-option>
            <a-select-option value="survey">测绘任务</a-select-option>
            <a-select-option value="rescue">救援任务</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="位置（经纬度）">
          <a-input v-model:value="taskForm.location" placeholder="如：39.9042, 116.4074" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="优先级">
              <a-select v-model:value="taskForm.priority">
                <a-select-option value="high">高</a-select-option>
                <a-select-option value="medium">中</a-select-option>
                <a-select-option value="low">低</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="状态">
              <a-select v-model:value="taskForm.status">
                <a-select-option value="待分配">待分配</a-select-option>
                <a-select-option value="已分配">已分配</a-select-option>
                <a-select-option value="执行中">执行中</a-select-option>
                <a-select-option value="已完成">已完成</a-select-option>
                <a-select-option value="已取消">已取消</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="描述">
          <a-textarea v-model:value="taskForm.description" :rows="3" placeholder="请输入任务描述" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 分配无人机模态框 -->
    <a-modal
      title="分配无人机"
      v-model:open="assignModalVisible"
      @ok="handleAssignTask"
      ok-text="确认分配"
      cancel-text="取消"
    >
      <a-form layout="vertical">
        <a-form-item label="选择无人机">
          <a-select v-model:value="assignForm.droneId" placeholder="请选择无人机">
            <a-select-option
              v-for="drone in droneStore.list"
              :key="drone.id"
              :value="drone.id"
            >
              {{ drone.name }}（{{ drone.status }}）
            </a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, UploadOutlined, DownloadOutlined } from '@ant-design/icons-vue'
import { useTaskStore } from '../../stores/tasks'
import { useDroneStore } from '../../stores/drones'

const taskStore = useTaskStore()
const droneStore = useDroneStore()

const searchText = ref('')
const taskModalVisible = ref(false)
const assignModalVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)

const taskForm = reactive({
  name: '',
  type: 'delivery',
  location: '',
  priority: 'medium',
  status: '待分配',
  description: ''
})

const assignForm = reactive({
  droneId: null
})

const columns = [
  { title: '任务名称', dataIndex: 'name', key: 'name', width: '20%' },
  { title: '类型', dataIndex: 'type', key: 'type', width: '12%' },
  { title: '位置', dataIndex: 'location', key: 'location', width: '20%' },
  { title: '优先级', dataIndex: 'priority', key: 'priority', width: '10%' },
  { title: '状态', key: 'status', width: '12%' },
  { title: '描述', dataIndex: 'description', key: 'description' },
  { title: '操作', key: 'action', fixed: 'right', width: '200px' }
]

const filteredTasks = computed(() => {
  if (!searchText.value) return taskStore.list
  const q = searchText.value.toLowerCase()
  return taskStore.list.filter(
    (t) =>
      (t.name && t.name.toLowerCase().includes(q)) ||
      (t.type && t.type.toLowerCase().includes(q)) ||
      (t.description && t.description.toLowerCase().includes(q))
  )
})

function getStatusColor(status) {
  const map = {
    待分配: 'blue',
    已分配: 'orange',
    执行中: 'purple',
    已完成: 'green',
    已取消: 'red'
  }
  return map[status] || 'default'
}

function showTotal(total) {
  return `共 ${total} 条`
}

function resetForm() {
  Object.assign(taskForm, {
    name: '',
    type: 'delivery',
    location: '',
    priority: 'medium',
    status: '待分配',
    description: ''
  })
  editingId.value = null
}

function showAddTaskModal() {
  resetForm()
  isEditing.value = false
  taskModalVisible.value = true
}

function editTask(record) {
  isEditing.value = true
  editingId.value = record.id
  Object.assign(taskForm, {
    name: record.name || '',
    type: record.type || 'delivery',
    location: record.location || '',
    priority: record.priority || 'medium',
    status: record.status || '待分配',
    description: record.description || ''
  })
  taskModalVisible.value = true
}

function handleAddTask() {
  if (!taskForm.name) {
    message.warning('请输入任务名称')
    return
  }
  taskStore.addTask({ ...taskForm })
  message.success('任务添加成功')
  taskModalVisible.value = false
}

function handleEditTask() {
  if (editingId.value !== null) {
    taskStore.updateTask(editingId.value, { ...taskForm })
    message.success('任务已更新')
    taskModalVisible.value = false
  }
}

function deleteTask(id) {
  Modal.confirm({
    title: '确认删除',
    content: '您确定要删除此任务吗？此操作不可撤销。',
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: () => {
      taskStore.removeTask(id)
      message.success('任务已删除')
    }
  })
}

function assignTask(record) {
  assignForm.droneId = null
  assignModalVisible.value = true
  editingId.value = record.id
}

function handleAssignTask() {
  if (!assignForm.droneId) {
    message.warning('请选择无人机')
    return
  }
  if (editingId.value !== null) {
    taskStore.updateTask(editingId.value, { status: '已分配' })
  }
  message.success('已分配无人机')
  assignModalVisible.value = false
}

function importTasks() {
  message.info('导入任务功能开发中')
}

function exportTasks() {
  message.info('导出任务功能开发中')
}

onMounted(async () => {
  await Promise.all([taskStore.fetchAll(), droneStore.fetchAll()])
})
</script>

<style scoped>
.tasks {
  padding: 0;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
  color: rgba(0, 0, 0, 0.88);
}
</style>
