<template>
  <div class="weather-station-view">
    <div class="page-header">
      <h2 class="page-title">气象站点管理</h2>
      <div class="header-actions">
        <el-button size="small" @click="handleRefresh">
          <span class="btn-icon">🔄</span> 刷新
        </el-button>
        <el-button type="primary" size="small" @click="handleAddStation">
          <span class="btn-icon">➕</span> 新增站点
        </el-button>
      </div>
    </div>

    <el-row :gutter="16" class="main-row">
      <!-- 左栏：站点列表 -->
      <el-col :span="16">
        <el-card shadow="hover" class="panel">
          <template #header>
            <div class="panel-head">
              <span class="panel-title">站点列表</span>
              <el-tag size="small" type="info">{{ stations.length }} 个站点</el-tag>
            </div>
          </template>
          <el-table :data="stations" stripe size="small" height="480" row-key="id">
            <el-table-column type="index" label="#" width="50" align="center" />
            <el-table-column prop="name" label="站点名称" width="140" />
            <el-table-column prop="code" label="站点编码" width="100" />
            <el-table-column prop="lat" label="纬度" width="80" align="center" />
            <el-table-column prop="lng" label="经度" width="80" align="center" />
            <el-table-column prop="altitude" label="海拔(m)" width="80" align="center" />
            <el-table-column prop="type" label="类型" width="100" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="stationTypeTag(row.type)">{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="row.status === '在线' ? 'success' : 'danger'" effect="dark">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" align="center">
              <template #default="{ row, $index }">
                <el-button size="small" type="primary" link @click="handleEdit(row)">编辑</el-button>
                <el-button size="small" type="danger" link @click="handleDelete($index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 右栏：站点详情/编辑 -->
      <el-col :span="8">
        <el-card shadow="hover" class="panel">
          <template #header>
            <span class="panel-title">{{ isEditing ? '编辑站点' : '新增站点' }}</span>
          </template>
          <el-form :model="form" label-width="80px" size="small">
            <el-form-item label="站点名称">
              <el-input v-model="form.name" placeholder="请输入站点名称" />
            </el-form-item>
            <el-form-item label="站点编码">
              <el-input v-model="form.code" placeholder="如 BJ-001" />
            </el-form-item>
            <el-form-item label="纬度">
              <el-input-number v-model="form.lat" :min="-90" :max="90" :precision="6" style="width: 100%" />
            </el-form-item>
            <el-form-item label="经度">
              <el-input-number v-model="form.lng" :min="-180" :max="180" :precision="6" style="width: 100%" />
            </el-form-item>
            <el-form-item label="海拔(m)">
              <el-input-number v-model="form.altitude" :min="-500" :max="9000" style="width: 100%" />
            </el-form-item>
            <el-form-item label="站点类型">
              <el-select v-model="form.type" style="width: 100%">
                <el-option value="自动站" label="自动站" />
                <el-option value="人工站" label="人工站" />
                <el-option value="气象雷达" label="气象雷达" />
                <el-option value="探空站" label="探空站" />
              </el-select>
            </el-form-item>
            <el-form-item label="状态">
              <el-radio-group v-model="form.status">
                <el-radio-button value="在线">在线</el-radio-button>
                <el-radio-button value="离线">离线</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSave" style="width: 100%">
                {{ isEditing ? '保存修改' : '确认添加' }}
              </el-button>
              <el-button v-if="isEditing" @click="handleCancel" style="width: 100%; margin-top: 8px">
                取消
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="hover" class="panel mt-12">
          <template #header>
            <span class="panel-title">数据统计</span>
          </template>
          <div class="stat-grid">
            <div class="stat-cell">
              <div class="stat-val">{{ stations.length }}</div>
              <div class="stat-label">站点总数</div>
            </div>
            <div class="stat-cell">
              <div class="stat-val">{{ onlineCount }}</div>
              <div class="stat-label">在线站点</div>
            </div>
            <div class="stat-cell">
              <div class="stat-val">{{ stationTypes.length }}</div>
              <div class="stat-label">站点类型</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'

const stations = ref([
  { id: 1, name: '北京首都机场', code: 'BJ-001', lat: 39.9362, lng: 116.6058, altitude: 35, type: '自动站', status: '在线' },
  { id: 2, name: '天津滨海机场', code: 'TJ-001', lat: 39.1244, lng: 117.3462, altitude: 3, type: '自动站', status: '在线' },
  { id: 3, name: '济南遥墙机场', code: 'JN-001', lat: 36.8572, lng: 117.2158, altitude: 23, type: '人工站', status: '在线' },
  { id: 4, name: '上海虹桥机场', code: 'SH-001', lat: 31.1972, lng: 121.3206, altitude: 4, type: '气象雷达', status: '在线' },
  { id: 5, name: '青岛流亭机场', code: 'QD-001', lat: 36.2661, lng: 120.3828, altitude: 10, type: '自动站', status: '离线' },
  { id: 6, name: '石家庄正定', code: 'SJZ-001', lat: 38.2806, lng: 114.6978, altitude: 71, type: '探空站', status: '在线' }
])

const form = reactive({
  id: null,
  name: '',
  code: '',
  lat: 39.9,
  lng: 116.4,
  altitude: 100,
  type: '自动站',
  status: '在线'
})

const isEditing = computed(() => form.id !== null)

const onlineCount = computed(() => stations.value.filter(s => s.status === '在线').length)
const stationTypes = computed(() => [...new Set(stations.value.map(s => s.type))])

function stationTypeTag(type) {
  const map = { '自动站': '', '人工站': 'info', '气象雷达': 'warning', '探空站': 'success' }
  return map[type] || 'info'
}

function handleRefresh() {
  ElMessage.success('站点数据已刷新')
}

function handleAddStation() {
  form.id = null
  form.name = ''
  form.code = ''
  form.lat = 39.9
  form.lng = 116.4
  form.altitude = 100
  form.type = '自动站'
  form.status = '在线'
}

function handleEdit(row) {
  Object.assign(form, row)
}

function handleDelete(idx) {
  stations.value.splice(idx, 1)
  ElMessage.success('站点已删除')
}

function handleSave() {
  if (!form.name || !form.code) {
    ElMessage.warning('请填写站点名称和编码')
    return
  }
  if (isEditing.value) {
    const idx = stations.value.findIndex(s => s.id === form.id)
    if (idx !== -1) stations.value[idx] = { ...form }
    ElMessage.success('站点已更新')
  } else {
    stations.value.push({ ...form, id: Date.now() })
    ElMessage.success('站点已添加')
  }
  handleAddStation()
}

function handleCancel() {
  handleAddStation()
}
</script>

<style scoped>
.weather-station-view {
  padding: 16px;
  background: #f5f7fa;
  min-height: 100%;
  font-size: 13px;
  color: #303133;
}
.page-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.header-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}
.btn-icon {
  margin-right: 4px;
}
.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}
.main-row {
  align-items: stretch;
}
.panel {
  border-radius: 8px;
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.panel-title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}
.mt-12 {
  margin-top: 12px;
}
.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.stat-cell {
  background: #f5f7fa;
  border-radius: 6px;
  padding: 16px 8px;
  text-align: center;
}
.stat-val {
  font-size: 22px;
  font-weight: 700;
  color: #409eff;
}
.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
