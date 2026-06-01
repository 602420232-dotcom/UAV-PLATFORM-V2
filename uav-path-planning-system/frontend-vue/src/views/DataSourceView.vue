<template>
  <div class="data-source-view">
    <a-card title="数据源管理" class="card">
      <a-tabs v-model:activeKey="activeTab">
        <a-tab-pane key="list" tab="数据源列表">
          <a-button type="primary" @click="showAddModal" style="margin-bottom: 16px">
            <PlusOutlined /> 添加数据源
          </a-button>
          
          <a-table :columns="columns" :data-source="dataSources" :loading="loading">
            <template #action="{ record }">
              <a-button @click="editDataSource(record)" size="small" style="margin-right: 8px">
                编辑
              </a-button>
              <a-button @click="deleteDataSource(record.id)" size="small" danger>
                删除
              </a-button>
            </template>
          </a-table>
        </a-tab-pane>
        <a-tab-pane key="test" tab="数据源测试">
          <a-form :form="testForm" layout="vertical">
            <a-form-item label="数据源类型">
              <a-select v-model:value="testForm.type" placeholder="选择数据源类型">
                <a-select-option value="satellite">卫星数据</a-select-option>
                <a-select-option value="radar">雷达数据</a-select-option>
                <a-select-option value="ground_station">地面站数据</a-select-option>
                <a-select-option value="buoy">浮标数据</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item label="数据文件">
              <a-upload
                v-model:fileList="fileList"
                :multiple="false"
                :before-upload="beforeUpload"
                :show-upload-list="true"
              >
                <a-button>
                  <UploadOutlined /> 选择文件
                </a-button>
              </a-upload>
            </a-form-item>
            
            <a-form-item>
              <a-button type="primary" @click="testDataSource" :loading="testing">
                测试数据源
              </a-button>
            </a-form-item>
          </a-form>
          
          <div v-if="testResult" class="test-result">
            <a-alert
              :type="testResult.success ? 'success' : 'error'"
              :message="testResult.message"
              show-icon
            />
            <div v-if="testResult.data" class="test-data">
              <a-collapse>
                <a-collapse-panel title="测试数据" key="1">
                  <pre>{{ JSON.stringify(testResult.data, null, 2) }}</pre>
                </a-collapse-panel>
              </a-collapse>
            </div>
          </div>
        </a-tab-pane>
      </a-tabs>
    </a-card>
    
    <!-- 添加/编辑数据源模态框 -->
    <a-modal
      v-model:visible="modalVisible"
      :title="modalTitle"
      @ok="handleOk"
      @cancel="handleCancel"
    >
      <a-form :form="dataSourceForm" layout="vertical">
        <a-form-item label="数据源名称">
          <a-input v-model:value="dataSourceForm.name" placeholder="输入数据源名称" />
        </a-form-item>
        
        <a-form-item label="数据源类型">
          <a-select v-model:value="dataSourceForm.type" placeholder="选择数据源类型">
            <a-select-option value="satellite">卫星数据</a-select-option>
            <a-select-option value="radar">雷达数据</a-select-option>
            <a-select-option value="ground_station">地面站数据</a-select-option>
            <a-select-option value="buoy">浮标数据</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item label="数据格式">
          <a-select v-model:value="dataSourceForm.format" placeholder="选择数据格式">
            <a-select-option value="csv">CSV</a-select-option>
            <a-select-option value="json">JSON</a-select-option>
            <a-select-option value="netcdf">NetCDF</a-select-option>
            <a-select-option value="hdf5">HDF5</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item label="数据源配置">
          <a-textarea v-model:value="dataSourceForm.config" placeholder="输入数据源配置（JSON格式）" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { PlusOutlined, UploadOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

// 数据源列表
const dataSources = ref([
  {
    id: 1,
    name: 'GOES-16卫星数据',
    type: 'satellite',
    format: 'netcdf',
    status: 'active',
    createdAt: '2024-01-01T00:00:00Z'
  },
  {
    id: 2,
    name: '多普勒雷达数据',
    type: 'radar',
    format: 'hdf5',
    status: 'active',
    createdAt: '2024-01-02T00:00:00Z'
  },
  {
    id: 3,
    name: '气象地面站数据',
    type: 'ground_station',
    format: 'csv',
    status: 'active',
    createdAt: '2024-01-03T00:00:00Z'
  },
  {
    id: 4,
    name: '海洋浮标数据',
    type: 'buoy',
    format: 'json',
    status: 'active',
    createdAt: '2024-01-04T00:00:00Z'
  }
])

// 加载状态
const loading = ref(false)
const testing = ref(false)

// 标签页
const activeTab = ref('list')

// 模态框
const modalVisible = ref(false)
const modalTitle = ref('添加数据源')
const editingDataSource = ref(null)

// 表单
const dataSourceForm = reactive({
  name: '',
  type: '',
  format: '',
  config: '{}'
})

const testForm = reactive({
  type: 'satellite'
})

// 文件上传
const fileList = ref([])

// 测试结果
const testResult = ref(null)

// 表格列
const columns = [
  {
    title: 'ID',
    dataIndex: 'id',
    key: 'id'
  },
  {
    title: '名称',
    dataIndex: 'name',
    key: 'name'
  },
  {
    title: '类型',
    dataIndex: 'type',
    key: 'type',
    customRender: (text) => {
      const typeMap = {
        'satellite': '卫星数据',
        'radar': '雷达数据',
        'ground_station': '地面站数据',
        'buoy': '浮标数据'
      }
      return typeMap[text] || text
    }
  },
  {
    title: '格式',
    dataIndex: 'format',
    key: 'format'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    customRender: (text) => {
      return text === 'active' ? 
        <a-tag color="green">活跃</a-tag> : 
        <a-tag color="red">禁用</a-tag>
    }
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    key: 'createdAt'
  },
  {
    title: '操作',
    key: 'action',
    slots: { customRender: 'action' }
  }
]

// 显示添加模态框
const showAddModal = () => {
  modalTitle.value = '添加数据源'
  editingDataSource.value = null
  Object.assign(dataSourceForm, {
    name: '',
    type: '',
    format: '',
    config: '{}'
  })
  modalVisible.value = true
}

// 编辑数据源
const editDataSource = (record) => {
  modalTitle.value = '编辑数据源'
  editingDataSource.value = record
  Object.assign(dataSourceForm, {
    name: record.name,
    type: record.type,
    format: record.format,
    config: '{}'
  })
  modalVisible.value = true
}

// 删除数据源
const deleteDataSource = (id) => {
  // TODO: 实现删除逻辑
  message.success('数据源删除成功')
}

// 处理确定
const handleOk = () => {
  // TODO: 实现保存逻辑
  modalVisible.value = false
  message.success('数据源保存成功')
}

// 处理取消
const handleCancel = () => {
  modalVisible.value = false
}

// 文件上传前
const beforeUpload = (file) => {
  // 限制文件类型
  const allowedTypes = ['.csv', '.json', '.nc', '.h5']
  const fileExt = file.name.substring(file.name.lastIndexOf('.'))
  if (!allowedTypes.includes(fileExt)) {
    message.error('只支持CSV、JSON、NetCDF和HDF5格式的文件')
    return false
  }
  return true
}

// 测试数据源
const testDataSource = () => {
  testing.value = true
  // 模拟测试
  setTimeout(() => {
    testing.value = false
    testResult.value = {
      success: true,
      message: '数据源测试成功',
      data: {
        type: testForm.type,
        file: fileList.value.length > 0 ? fileList.value[0].name : '无文件',
        observations: 1000,
        processingTime: '2.5s'
      }
    }
  }, 1500)
}
</script>

<style scoped>
.data-source-view {
  padding: 20px;
}

.card {
  margin-bottom: 20px;
}

.test-result {
  margin-top: 20px;
}

.test-data {
  margin-top: 16px;
}

pre {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
}
</style>
