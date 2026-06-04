<template>
  <a-card title="路径规划" class="path-planning-card">
    <a-row :gutter="[16, 16]">
      <!-- 左侧配置面板 -->
      <a-col :span="8">
        <a-card title="规划配置">
          <!-- 任务点配置 -->
          <div class="config-section">
            <a-form :model="formState" layout="vertical">
              <a-form-item label="任务点">
                <a-row :gutter="[8, 8]">
                  <a-col :span="12">
                    <a-button type="primary" @click="addTaskPoint">
                      <template #icon>
                        <PlusOutlined />
                      </template>
                      添加任务点
                    </a-button>
                  </a-col>
                  <a-col :span="12">
                    <a-upload
                      name="file"
                      :show-upload-list="false"
                      :before-upload="handleExcelUpload"
                      accept=".csv,.xlsx,.xls"
                    >
                      <a-button>
                        <template #icon>
                          <UploadOutlined />
                        </template>
                        批量导入
                      </a-button>
                    </a-upload>
                  </a-col>
                </a-row>
                <a-list :data-source="taskPoints" :render-item="renderTaskItem" />
              </a-form-item>
              
              <!-- 无人机配置 -->
              <a-form-item label="无人机">
                <a-select v-model:value="selectedDrone" placeholder="选择无人机">
                  <a-select-option value="1">无人机1</a-select-option>
                  <a-select-option value="2">无人机2</a-select-option>
                  <a-select-option value="3">无人机3</a-select-option>
                </a-select>
              </a-form-item>
              
              <!-- 气象数据选择 -->
              <a-form-item label="气象数据">
                <a-select v-model:value="selectedWeather" placeholder="选择气象数据">
                  <a-option value="latest">最新数据</a-option>
                  <a-option value="custom">自定义数据</a-option>
                </a-select>
              </a-form-item>
              
              <!-- 规划参数 -->
              <a-form-item label="风险阈值">
                <a-slider v-model:value="riskThreshold" :min="0" :max="10" :step="0.1" />
                <span>{{ riskThreshold }}</span>
              </a-form-item>
              
              <!-- 执行按钮 -->
              <a-form-item>
                <a-button type="primary" block @click="executePlanning" :loading="loading">
                  <template #icon>
                    <PlayCircleOutlined />
                  </template>
                  执行路径规划
                </a-button>
              </a-form-item>
            </a-form>
          </div>
        </a-card>
        
        <!-- 禁飞区管理 -->
        <a-card title="禁飞区管理" style="margin-top: 16px">
          <a-collapse v-model:activeKey="noFlyCollapseActive" :bordered="false">
            <a-collapse-panel key="noFlyPanel" header="禁飞区列表">
              <a-button type="primary" size="small" style="margin-bottom: 8px" @click="openNoFlyModal">
                <template #icon><PlusOutlined /></template>
                添加禁飞区
              </a-button>
              <a-list :data-source="noFlyZones" :locale="{ emptyText: '暂无禁飞区' }">
                <template #renderItem="{ item }">
                  <a-list-item>
                    <a-list-item-meta
                      :title="item.name"
                      :description="item.type === 'circle' ? `圆形 · 半径 ${item.radius}m` : '多边形禁飞区'"
                    />
                    <template #actions>
                      <a-button size="small" danger @click="removeNoFlyZone(item.id)">
                        <template #icon><CloseOutlined /></template>
                      </a-button>
                    </template>
                  </a-list-item>
                </template>
              </a-list>
            </a-collapse-panel>
          </a-collapse>
        </a-card>

        <!-- 方案管理 -->
        <a-card title="方案管理" style="margin-top: 16px">
          <a-form :model="planForm" layout="vertical">
            <a-form-item label="方案名称">
              <a-input v-model:value="planForm.name" placeholder="输入方案名称" />
            </a-form-item>
            <a-form-item>
              <a-row :gutter="[8, 8]">
                <a-col :span="8">
                  <a-button @click="savePlan" :disabled="!planningResult">
                    <template #icon>
                      <SaveOutlined />
                    </template>
                    保存
                  </a-button>
                </a-col>
                <a-col :span="8">
                  <a-button @click="exportPlan" :disabled="!planningResult">
                    <template #icon>
                      <DownloadOutlined />
                    </template>
                    导出
                  </a-button>
                </a-col>
                <a-col :span="8">
                  <a-button @click="printPlan" :disabled="!planningResult">
                    <template #icon>
                      <PrinterOutlined />
                    </template>
                    打印
                  </a-button>
                </a-col>
              </a-row>
            </a-form-item>
            <a-form-item label="历史方案">
              <a-select v-model:value="selectedPlan" placeholder="选择历史方案">
                <a-option v-for="plan in savedPlans" :key="plan.id" :value="plan.id">
                  {{ plan.name }}
                </a-option>
              </a-select>
              <a-button style="margin-left: 8px" @click="loadPlan" :disabled="!selectedPlan">
                加载
              </a-button>
              <a-button style="margin-left: 8px" danger @click="deletePlan" :disabled="!selectedPlan">
                删除
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>
      </a-col>
      
      <!-- 右侧地图和结果 -->
      <a-col :span="16">
        <a-card title="地图视图">
          <div id="map" class="map-container"></div>
        </a-card>
        
        <!-- 实时数据面板 -->
        <a-card title="实时数据" style="margin-top: 16px">
          <a-row :gutter="[16, 16]">
            <a-col :span="6">
              <a-statistic title="风速" :value="realtimeData.windSpeed" suffix="m/s" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="风向" :value="realtimeData.windDirection" suffix="°" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="温度" :value="realtimeData.temperature" suffix="°C" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="湿度" :value="realtimeData.humidity" suffix="%" />
            </a-col>
          </a-row>
          <a-divider />
          <a-row :gutter="[16, 16]">
            <a-col :span="6">
              <a-statistic title="无人机状态" :value="realtimeData.droneStatus" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="任务进度" :value="realtimeData.taskProgress" suffix="%" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="风险等级" :value="realtimeData.riskLevel" />
            </a-col>
            <a-col :span="6">
              <a-statistic title="告警数量" :value="realtimeData.alertCount" />
            </a-col>
          </a-row>
        </a-card>
        
        <!-- 规划结果 -->
        <a-card title="规划结果" style="margin-top: 16px">
          <div v-if="planningResult" class="result-content">
            <a-row :gutter="[16, 16]">
              <a-col :span="6">
                <a-statistic title="无人机数量" :value="planningResult.droneCount" />
              </a-col>
              <a-col :span="6">
                <a-statistic title="任务点数量" :value="planningResult.taskCount" />
              </a-col>
              <a-col :span="6">
                <a-statistic title="总距离" :value="planningResult.totalDistance" suffix="m" />
              </a-col>
              <a-col :span="6">
                <a-statistic title="总时间" :value="planningResult.totalTime" suffix="min" />
              </a-col>
            </a-row>
            <a-divider />
            <div class="routes-list">
              <h4>路径详情</h4>
              <a-list :data-source="planningResult.routes">
                <template #renderItem="{ item, index }">
                  <a-list-item :key="index">
                    <a-list-item-meta :title="`无人机 ${item.droneId}`" :description="`无人机 ${item.droneId}`" />
                    <div>
                      <p>路径: {{ item.path.join(' → ') }}</p>
                      <p>距离: {{ item.distance }}m</p>
                      <p>时间: {{ item.time }}min</p>
                      <p v-if="item.riskLevel">风险等级: {{ item.riskLevel }}</p>
                    </div>
                  </a-list-item>
                </template>
              </a-list>
            </div>
          </div>
          <div v-else class="no-result">
            <Empty description="请点击执行路径规划" />
          </div>
        </a-card>
      </a-col>
    </a-row>
  </a-card>

  <!-- 添加禁飞区模态框 -->
  <a-modal
    v-model:visible="showNoFlyModal"
    title="添加禁飞区"
    @ok="submitNoFlyZone"
    @cancel="closeNoFlyModal"
  >
    <a-form layout="vertical">
      <a-form-item label="禁飞区名称">
        <a-input v-model:value="noFlyForm.name" placeholder="输入禁飞区名称" />
      </a-form-item>
      <a-form-item label="禁飞区类型">
        <a-select v-model:value="noFlyForm.type">
          <a-select-option value="circle">圆形</a-select-option>
          <a-select-option value="polygon">多边形</a-select-option>
        </a-select>
      </a-form-item>
      <template v-if="noFlyForm.type === 'circle'">
        <a-form-item label="中心纬度">
          <a-input-number v-model:value="noFlyForm.lat" :min="-90" :max="90" :step="0.001" style="width: 100%" />
        </a-form-item>
        <a-form-item label="中心经度">
          <a-input-number v-model:value="noFlyForm.lng" :min="-180" :max="180" :step="0.001" style="width: 100%" />
        </a-form-item>
        <a-form-item label="半径（米）">
          <a-input-number v-model:value="noFlyForm.radius" :min="10" :max="10000" :step="10" style="width: 100%" />
        </a-form-item>
      </template>
      <template v-else>
        <a-form-item label="多边形坐标点（JSON 数组）">
          <a-textarea v-model:value="noFlyForm.points" placeholder='[[39.91, 116.41], [39.92, 116.42], [39.93, 116.41]]' :rows="4" />
        </a-form-item>
      </template>
    </a-form>
  </a-modal>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, h } from 'vue'
import { 
  PlusOutlined, PlayCircleOutlined, UploadOutlined, 
  SaveOutlined, DownloadOutlined, PrinterOutlined,
  CloseOutlined
} from '@ant-design/icons-vue'
import { Empty, message } from 'ant-design-vue'
import L from 'leaflet'
import { addNoFlyZone } from '../utils/visualization'

// 响应式数据
const formState = ref({})
const taskPoints = ref([
  { id: 1, name: '任务点1', lat: 39.9042, lng: 116.4074, demand: 1, startTime: '08:00', endTime: '18:00', serviceTime: 10 },
  { id: 2, name: '任务点2', lat: 39.9142, lng: 116.4174, demand: 2, startTime: '09:00', endTime: '17:00', serviceTime: 15 },
  { id: 3, name: '任务点3', lat: 39.9242, lng: 116.4274, demand: 1, startTime: '08:30', endTime: '16:30', serviceTime: 20 }
])

// 禁飞区管理
const noFlyZones = ref([
  { id: 1, name: '禁飞区A', type: 'circle', center: [39.9142, 116.4174], radius: 200, points: [] },
  { id: 2, name: '禁飞区B', type: 'circle', center: [39.9242, 116.4274], radius: 150, points: [] }
])
const zoneLayers = ref([])
const showNoFlyModal = ref(false)
const noFlyForm = ref({ name: '', type: 'circle', lat: 39.91, lng: 116.41, radius: 200, points: '' })
const noFlyCollapseActive = ref(['noFlyPanel'])
const selectedDrone = ref('1')
const selectedWeather = ref('latest')
const riskThreshold = ref(3.0)
const loading = ref(false)
const planningResult = ref(null)
let map = null

// 实时数据
const realtimeData = ref({
  windSpeed: 5.2,
  windDirection: 135,
  temperature: 22,
  humidity: 65,
  droneStatus: '正常',
  taskProgress: 0,
  riskLevel: '低',
  alertCount: 0
})

// 方案管理
const planForm = ref({ name: '' })
const selectedPlan = ref('')
const savedPlans = ref([
  { id: 1, name: '方案1' },
  { id: 2, name: '方案2' },
  { id: 3, name: '方案3' }
])

// 方法
const addTaskPoint = () => {
  const newId = taskPoints.value.length + 1
  taskPoints.value.push({
    id: newId,
    name: `任务点${newId}`,
    lat: 39.9 + Math.random() * 0.1,
    lng: 116.4 + Math.random() * 0.1,
    demand: 1,
    startTime: '08:00',
    endTime: '18:00',
    serviceTime: 10
  })
  updateMap()
}

const renderTaskItem = (task) => {
  const timeInfo = `${task.startTime || '08:00'} - ${task.endTime || '18:00'} (服务: ${task.serviceTime || 10}min)`
  return h('a-list-item', [
    h('a-list-item-meta', {
      title: task.name,
      description: `${task.lat.toFixed(4)}, ${task.lng.toFixed(4)} | ${timeInfo}`
    }),
    h('a-button', {
      size: 'small',
      danger: true,
      onClick: () => removeTaskPoint(task.id)
    }, '删除')
  ])
}

const removeTaskPoint = (id) => {
  taskPoints.value = taskPoints.value.filter(task => task.id !== id)
  updateMap()
}

const executePlanning = async () => {
  loading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 模拟结果
    planningResult.value = {
      droneCount: 2,
      taskCount: taskPoints.value.length,
      totalDistance: 1500,
      totalTime: 25,
      routes: [
        {
          droneId: 1,
          path: ['基地', '任务点1', '任务点3', '基地'],
          distance: 800,
          time: 12,
          riskLevel: '低'
        },
        {
          droneId: 2,
          path: ['基地', '任务点2', '基地'],
          distance: 700,
          time: 13,
          riskLevel: '低'
        }
      ]
    }
    
    // 更新地图
    updateMap()
  } catch (error) {
    console.error('规划失败:', error)
    message.error('规划失败')
  } finally {
    loading.value = false
  }
}

const handleExcelUpload = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const text = e.target.result
      const lines = text.split('\n').filter(line => line.trim())
      if (lines.length < 2) {
        message.error('CSV文件为空或格式不正确')
        return
      }
      // 跳过表头行，从第2行开始解析
      const newPoints = []
      let id = 1
      for (let i = 1; i < lines.length; i++) {
        const parts = lines[i].split(',').map(s => s.trim())
        if (parts.length >= 3) {
          const name = parts[0] || `任务点${id}`
          const lat = parseFloat(parts[1])
          const lng = parseFloat(parts[2])
          const demand = parseInt(parts[3]) || 1
          const startTime = parts[4] || '08:00'
          const endTime = parts[5] || '18:00'
          const serviceTime = parseInt(parts[6]) || 10
          if (!isNaN(lat) && !isNaN(lng)) {
            newPoints.push({ id, name, lat, lng, demand, startTime, endTime, serviceTime })
            id++
          }
        }
      }
      if (newPoints.length > 0) {
        taskPoints.value = newPoints
        updateMap()
        message.success(`成功导入 ${newPoints.length} 个任务点`)
      } else {
        message.error('未解析到有效数据')
      }
    } catch (err) {
      message.error('文件解析失败')
    }
  }
  reader.readAsText(file)
  return false // 阻止自动上传
}

const savePlan = () => {
  if (!planForm.value.name) {
    message.error('请输入方案名称')
    return
  }
  const planData = {
    name: planForm.value.name,
    taskPoints: taskPoints.value,
    timestamp: new Date().toISOString()
  }
  const blob = new Blob([JSON.stringify(planData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${planForm.value.name}.json`
  a.click()
  URL.revokeObjectURL(url)

  const newPlan = {
    id: savedPlans.value.length + 1,
    name: planForm.value.name
  }
  savedPlans.value.push(newPlan)
  selectedPlan.value = newPlan.id
  message.success('方案保存成功')
}

const exportPlan = () => {
  if (taskPoints.value.length === 0) {
    message.error('没有可导出的任务点')
    return
  }
  let csv = '名称,纬度,经度,需求量,开始时间,结束时间,服务时间(min)\n'
  taskPoints.value.forEach(tp => {
    csv += `${tp.name},${tp.lat},${tp.lng},${tp.demand},${tp.startTime || ''},${tp.endTime || ''},${tp.serviceTime || ''}\n`
  })
  const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${planForm.value.name || '任务点数据'}.csv`
  a.click()
  URL.revokeObjectURL(url)
  message.success('方案导出成功')
}

const printPlan = () => {
  window.print()
}

const loadPlan = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = (e) => {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (event) => {
      try {
        const data = JSON.parse(event.target.result)
        if (data.taskPoints && Array.isArray(data.taskPoints)) {
          taskPoints.value = data.taskPoints
          updateMap()
          message.success('方案加载成功')
        } else {
          message.error('无效的方案文件')
        }
      } catch (err) {
        message.error('文件解析失败')
      }
    }
    reader.readAsText(file)
  }
  input.click()
}

const deletePlan = () => {
  savedPlans.value = savedPlans.value.filter(plan => plan.id !== selectedPlan.value)
  selectedPlan.value = ''
  message.success('方案删除成功')
}

const initMap = () => {
  map = L.map('map').setView([39.9042, 116.4074], 13)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map)
  
  // 添加基地标记
  L.marker([39.9042, 116.4074]).addTo(map).bindPopup('基地')
  
  // 添加任务点标记
  taskPoints.value.forEach(task => {
    L.marker([task.lat, task.lng]).addTo(map).bindPopup(task.name)
  })
}

const updateMap = () => {
  if (!map) return
  
  // 清除现有标记
  map.eachLayer(layer => {
    if (layer instanceof L.Marker) {
      map.removeLayer(layer)
    }
  })
  
  // 重新添加标记
  L.marker([39.9042, 116.4074]).addTo(map).bindPopup('基地')
  taskPoints.value.forEach(task => {
    L.marker([task.lat, task.lng]).addTo(map).bindPopup(task.name)
  })
  
  // 添加路径
  if (planningResult.value) {
    planningResult.value.routes.forEach((route, index) => {
      const pathCoords = route.path.map(point => {
        if (point === '基地') {
          return [39.9042, 116.4074]
        } else {
          const task = taskPoints.value.find(t => t.name === point)
          return task ? [task.lat, task.lng] : [39.9042, 116.4074]
        }
      })
      
      const colors = ['#1890ff', '#52c41a', '#faad14', '#f5222d']
      L.polyline(pathCoords, {
        color: colors[index % colors.length],
        weight: 3
      }).addTo(map)
    })
  }
}

// 模拟实时数据更新
const updateRealtimeData = () => {
  realtimeData.value = {
    windSpeed: (5 + Math.random() * 2).toFixed(1),
    windDirection: Math.floor(Math.random() * 360),
    temperature: Math.floor(20 + Math.random() * 5),
    humidity: Math.floor(60 + Math.random() * 10),
    droneStatus: '正常',
    taskProgress: Math.floor(Math.random() * 100),
    riskLevel: ['低', '中', '高'][Math.floor(Math.random() * 3)],
    alertCount: Math.floor(Math.random() * 5)
  }
}

// 禁飞区管理方法
const openNoFlyModal = () => {
  noFlyForm.value = { name: '', type: 'circle', lat: 39.91, lng: 116.41, radius: 200, points: '' }
  showNoFlyModal.value = true
}

const closeNoFlyModal = () => {
  showNoFlyModal.value = false
}

const submitNoFlyZone = () => {
  const form = noFlyForm.value
  if (!form.name) {
    message.error('请输入禁飞区名称')
    return
  }
  let newZone
  if (form.type === 'circle') {
    newZone = {
      id: Date.now(),
      name: form.name,
      type: 'circle',
      center: [form.lat, form.lng],
      radius: form.radius,
      points: []
    }
  } else {
    let points
    try {
      points = JSON.parse(form.points)
      if (!Array.isArray(points) || points.length < 3) {
        message.error('多边形至少需要3个顶点')
        return
      }
    } catch {
      message.error('坐标点格式错误，请输入有效的 JSON 数组')
      return
    }
    newZone = {
      id: Date.now(),
      name: form.name,
      type: 'polygon',
      center: [],
      radius: 0,
      points
    }
  }
  noFlyZones.value.push(newZone)
  showNoFlyModal.value = false
  updateNoFlyZones()
}

const removeNoFlyZone = (id) => {
  noFlyZones.value = noFlyZones.value.filter(z => z.id !== id)
  updateNoFlyZones()
}

const updateNoFlyZones = () => {
  if (!map) return
  // 清除旧禁飞区图层
  zoneLayers.value.forEach(layer => {
    if (map.hasLayer(layer)) {
      map.removeLayer(layer)
    }
  })
  zoneLayers.value = []
  // 添加新禁飞区图层
  noFlyZones.value.forEach(zone => {
    const layer = addNoFlyZone(map, zone)
    zoneLayers.value.push(layer)
  })
}

// 生命周期
let updateInterval = null
onMounted(() => {
  initMap()
  updateNoFlyZones()
  updateInterval = setInterval(updateRealtimeData, 5000)
})

onUnmounted(() => {
  if (updateInterval) clearInterval(updateInterval)
  if (map) {
    map.remove()
  }
})
</script>

<style scoped>
.path-planning-card {
  margin-bottom: 24px;
}

.config-section {
  margin-bottom: 24px;
}

.map-container {
  height: 500px;
  width: 100%;
}

.result-content {
  padding: 16px 0;
}

.routes-list {
  margin-top: 16px;
}

.no-result {
  padding: 40px 0;
  text-align: center;
}
</style>