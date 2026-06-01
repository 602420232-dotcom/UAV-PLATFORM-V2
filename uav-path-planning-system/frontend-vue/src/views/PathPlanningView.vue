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
                      accept=".xlsx,.xls"
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
                  <a-option value="1">无人机1</a-option>
                  <a-option value="2">无人机2</a-option>
                  <a-option value="3">无人机3</a-option>
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
              <a-list v-for="(route, index) in planningResult.routes" :key="index">
                <a-list-item>
                  <a-list-item-meta title="无人机" description="无人机" />
                  <div>
                    <p>路径: {{ route.path.join(' → ') }}</p>
                    <p>距离: {{ route.distance }}m</p>
                    <p>时间: {{ route.time }}min</p>
                    <p v-if="route.riskLevel">风险等级: {{ route.riskLevel }}</p>
                  </div>
                </a-list-item>
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
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { 
  PlusOutlined, PlayCircleOutlined, UploadOutlined, 
  SaveOutlined, DownloadOutlined, PrinterOutlined 
} from '@ant-design/icons-vue'
import { Empty, message } from 'ant-design-vue'
import L from 'leaflet'

// 响应式数据
const formState = ref({})
const taskPoints = ref([
  { id: 1, name: '任务点1', lat: 39.9042, lng: 116.4074, demand: 1 },
  { id: 2, name: '任务点2', lat: 39.9142, lng: 116.4174, demand: 2 },
  { id: 3, name: '任务点3', lat: 39.9242, lng: 116.4274, demand: 1 }
])
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
    demand: 1
  })
  updateMap()
}

const renderTaskItem = (task) => {
  return (
    <a-list-item>
      <a-list-item-meta title={task.name} description={`${task.lat.toFixed(4)}, ${task.lng.toFixed(4)}`} />
      <a-button size="small" danger @click={() => removeTaskPoint(task.id)}>
        删除
      </a-button>
    </a-list-item>
  )
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
  // 模拟Excel导入
  message.success('Excel导入成功')
  // 模拟导入数据
  taskPoints.value = [
    { id: 1, name: '任务点1', lat: 39.9042, lng: 116.4074, demand: 1 },
    { id: 2, name: '任务点2', lat: 39.9142, lng: 116.4174, demand: 2 },
    { id: 3, name: '任务点3', lat: 39.9242, lng: 116.4274, demand: 1 },
    { id: 4, name: '任务点4', lat: 39.9342, lng: 116.4374, demand: 2 },
    { id: 5, name: '任务点5', lat: 39.9442, lng: 116.4474, demand: 1 }
  ]
  updateMap()
  return false // 阻止自动上传
}

const savePlan = () => {
  if (!planForm.value.name) {
    message.error('请输入方案名称')
    return
  }
  const newPlan = {
    id: savedPlans.value.length + 1,
    name: planForm.value.name
  }
  savedPlans.value.push(newPlan)
  selectedPlan.value = newPlan.id
  message.success('方案保存成功')
}

const exportPlan = () => {
  message.success('方案导出成功')
}

const printPlan = () => {
  message.success('方案打印成功')
}

const loadPlan = () => {
  message.success('方案加载成功')
  // 模拟加载方案
  taskPoints.value = [
    { id: 1, name: '任务点A', lat: 39.9042, lng: 116.4074, demand: 1 },
    { id: 2, name: '任务点B', lat: 39.9142, lng: 116.4174, demand: 2 },
    { id: 3, name: '任务点C', lat: 39.9242, lng: 116.4274, demand: 1 }
  ]
  updateMap()
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

// 生命周期
let updateInterval = null
onMounted(() => {
  initMap()
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