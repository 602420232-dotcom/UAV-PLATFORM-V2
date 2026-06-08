<template>
  <div class="drones">
    <div class="page-title">无人机管理</div>

    <a-row :gutter="[16, 16]">
      <a-col :span="24">
        <a-card>
          <a-space>
            <a-button type="primary" @click="showAddModal">
              <template #icon><PlusOutlined /></template>
              添加无人机
            </a-button>
            <a-button @click="handleImport">
              <template #icon><UploadOutlined /></template>
              CSV 导入
            </a-button>
            <a-button @click="handleExport">
              <template #icon><DownloadOutlined /></template>
              CSV 导出
            </a-button>
          </a-space>
        </a-card>
      </a-col>

      <a-col :span="24">
        <a-card>
          <a-table
            :columns="columns"
            :data-source="droneStore.list"
            row-key="id"
            :loading="droneStore.loading"
            :pagination="{ pageSize: 10 }"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'battery'">
                <a-progress
                  :percent="record.battery"
                  :status="record.battery < 30 ? 'exception' : record.battery < 60 ? 'normal' : 'success'"
                  :show-info="true"
                />
              </template>
              <template v-else-if="column.key === 'status'">
                <a-tag :color="getStatusColor(record.status)">{{ record.status }}</a-tag>
              </template>
              <template v-else-if="column.key === 'action'">
                <a-space>
                  <a-button size="small" @click="editDrone(record)">编辑</a-button>
                  <a-button size="small" danger @click="deleteDrone(record.id)">删除</a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>

    <!-- 添加/编辑无人机模态框 -->
    <a-modal
      :title="isEditing ? '编辑无人机' : '添加无人机'"
      v-model:open="modalVisible"
      @ok="handleSubmit"
      ok-text="保存"
      cancel-text="取消"
    >
      <a-form :model="form" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="无人机ID">
              <a-input v-model:value="form.id" placeholder="如：UAV-005" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="名称">
              <a-input v-model:value="form.name" placeholder="请输入名称" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="类型">
              <a-select v-model:value="form.type">
                <a-select-option value="multirotor">多旋翼</a-select-option>
                <a-select-option value="fixed-wing">固定翼</a-select-option>
                <a-select-option value="hybrid">混合动力</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="状态">
              <a-select v-model:value="form.status">
                <a-select-option value="在线">在线</a-select-option>
                <a-select-option value="待命">待命</a-select-option>
                <a-select-option value="执行任务">执行任务</a-select-option>
                <a-select-option value="维护中">维护中</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="电量 (%)">
              <a-input-number v-model:value="form.battery" :min="0" :max="100" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="当前位置">
              <a-input v-model:value="form.location" placeholder="如：39.90, 116.40" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="最大载重 (kg)">
              <a-input-number v-model:value="form.maxPayload" :min="0" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="续航时间 (分钟)">
              <a-input-number v-model:value="form.maxEndurance" :min="0" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="24">
            <a-form-item label="备注">
              <a-textarea v-model:value="form.description" :rows="2" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { PlusOutlined, UploadOutlined, DownloadOutlined } from '@ant-design/icons-vue'
import { useDroneStore } from '../../stores/drones'

const droneStore = useDroneStore()

const modalVisible = ref(false)
const isEditing = ref(false)
const editingId = ref(null)

const form = reactive({
  id: '',
  name: '',
  type: 'multirotor',
  status: '待命',
  battery: 100,
  location: '',
  maxPayload: 5,
  maxEndurance: 30,
  description: ''
})

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: '12%' },
  { title: '名称', dataIndex: 'name', key: 'name', width: '15%' },
  { title: '类型', dataIndex: 'type', key: 'type', width: '12%' },
  { title: '状态', key: 'status', width: '10%' },
  { title: '电量', key: 'battery', width: '15%' },
  { title: '位置', dataIndex: 'location', key: 'location' },
  { title: '操作', key: 'action', fixed: 'right', width: '150px' }
]

function getStatusColor(status) {
  const map = {
    在线: 'green',
    待命: 'blue',
    执行任务: 'orange',
    维护中: 'red'
  }
  return map[status] || 'default'
}

function resetForm() {
  Object.assign(form, {
    id: '',
    name: '',
    type: 'multirotor',
    status: '待命',
    battery: 100,
    location: '',
    maxPayload: 5,
    maxEndurance: 30,
    description: ''
  })
  editingId.value = null
}

function showAddModal() {
  resetForm()
  isEditing.value = false
  modalVisible.value = true
}

function editDrone(record) {
  isEditing.value = true
  editingId.value = record.id
  Object.assign(form, {
    id: record.id,
    name: record.name,
    type: record.type,
    status: record.status,
    battery: record.battery,
    location: record.location,
    maxPayload: record.maxPayload,
    maxEndurance: record.maxEndurance,
    description: record.description
  })
  modalVisible.value = true
}

function handleSubmit() {
  if (!form.id || !form.name) {
    message.warning('请填写无人机 ID 和名称')
    return
  }
  if (isEditing.value && editingId.value !== null) {
    droneStore.updateDrone(editingId.value, { ...form })
    message.success('已更新无人机信息')
  } else {
    droneStore.addDrone({ ...form })
    message.success('已添加无人机')
  }
  modalVisible.value = false
}

function deleteDrone(id) {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除此无人机吗？',
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: () => {
      droneStore.removeDrone(id)
      message.success('已删除')
    }
  })
}

function handleImport() {
  message.info('CSV 导入功能开发中')
}

function handleExport() {
  message.info('CSV 导出功能开发中')
}

onMounted(() => {
  droneStore.fetchAll()
})
</script>

<style scoped>
.drones {
  padding: 0;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
  color: rgba(0, 0, 0, 0.88);
}
</style>
