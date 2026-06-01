<template>
  <div class="example-view">
    <a-card title="系统功能示范" class="card">
      <a-tabs v-model:activeKey="activeTab">
        <a-tab-pane key="path-planning" tab="路径规划">
          <div class="example-section">
            <h3>路径规划示例</h3>
            <p>本示例展示如何使用系统进行无人机路径规划。</p>
            
            <a-form :form="pathPlanningForm" layout="vertical" style="margin-top: 20px">
              <a-form-item label="起点">
                <a-input-group compact>
                  <a-input v-model:value="pathPlanningForm.startLat" placeholder="纬度" style="width: 120px" />
                  <a-input v-model:value="pathPlanningForm.startLng" placeholder="经度" style="width: 120px" />
                </a-input-group>
              </a-form-item>
              
              <a-form-item label="终点">
                <a-input-group compact>
                  <a-input v-model:value="pathPlanningForm.endLat" placeholder="纬度" style="width: 120px" />
                  <a-input v-model:value="pathPlanningForm.endLng" placeholder="经度" style="width: 120px" />
                </a-input-group>
              </a-form-item>
              
              <a-form-item label="算法选择">
                <a-select v-model:value="pathPlanningForm.algorithm" placeholder="选择算法">
                  <a-select-option value="astar">A*算法</a-select-option>
                  <a-select-option value="rrt">RRT*算法</a-select-option>
                  <a-select-option value="dijkstra">Dijkstra算法</a-select-option>
                  <a-select-option value="ga">遗传算法</a-select-option>
                  <a-select-option value="pso">粒子群优化</a-select-option>
                </a-select>
              </a-form-item>
              
              <a-form-item>
                <a-button type="primary" @click="runPathPlanning" :loading="pathPlanningLoading">
                  运行路径规划
                </a-button>
              </a-form-item>
            </a-form>
            
            <div v-if="pathPlanningResult" class="result-section">
              <a-alert
                type="success"
                message="路径规划成功"
                show-icon
              />
              <div class="map-container" ref="mapContainer"></div>
              <div class="result-details">
                <p>路径长度: {{ pathPlanningResult.length }} 米</p>
                <p>预计飞行时间: {{ pathPlanningResult.duration }} 秒</p>
                <p>路径点数量: {{ pathPlanningResult.points.length }}</p>
              </div>
            </div>
          </div>
        </a-tab-pane>
        
        <a-tab-pane key="weather" tab="气象数据">
          <div class="example-section">
            <h3>气象数据示例</h3>
            <p>本示例展示如何查看和分析气象数据。</p>
            
            <a-form :form="weatherForm" layout="vertical" style="margin-top: 20px">
              <a-form-item label="数据类型">
                <a-select v-model:value="weatherForm.type" placeholder="选择数据类型">
                  <a-select-option value="temperature">温度</a-select-option>
                  <a-select-option value="humidity">湿度</a-select-option>
                  <a-select-option value="wind">风速</a-select-option>
                  <a-select-option value="pressure">气压</a-select-option>
                </a-select>
              </a-form-item>
              
              <a-form-item label="时间范围">
                <a-date-picker
                  v-model:value="weatherForm.dateRange"
                  range
                  style="width: 300px"
                />
              </a-form-item>
              
              <a-form-item>
                <a-button type="primary" @click="loadWeatherData" :loading="weatherLoading">
                  加载数据
                </a-button>
              </a-form-item>
            </a-form>
            
            <div v-if="weatherData" class="result-section">
              <a-alert
                type="success"
                message="气象数据加载成功"
                show-icon
              />
              <div class="chart-container" ref="weatherChart"></div>
            </div>
          </div>
        </a-tab-pane>
        
        <a-tab-pane key="real-data" tab="真实数据源">
          <div class="example-section">
            <h3>真实数据源示例</h3>
            <p>本示例展示如何查看真实的地面站和浮标数据。</p>
            
            <a-form :form="realDataForm" layout="vertical" style="margin-top: 20px">
              <a-form-item label="数据源类型">
                <a-select v-model:value="realDataForm.type" placeholder="选择数据源类型">
                  <a-select-option value="ground_station">地面站数据</a-select-option>
                  <a-select-option value="buoy">浮标数据</a-select-option>
                </a-select>
              </a-form-item>
              
              <a-form-item>
                <a-button type="primary" @click="loadRealData" :loading="realDataLoading">
                  加载数据
                </a-button>
              </a-form-item>
            </a-form>
            
            <div v-if="realData" class="result-section">
              <a-alert
                type="success"
                message="真实数据加载成功"
                show-icon
              />
              <a-table :columns="realDataColumns" :data-source="realData" :loading="realDataLoading">
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'temperature'">
                    {{ record.temperature ? record.temperature.toFixed(2) : '-' }} °C
                  </template>
                  <template v-else-if="column.key === 'humidity'">
                    {{ record.humidity ? record.humidity.toFixed(2) : '-' }} %
                  </template>
                  <template v-else-if="column.key === 'wind_speed'">
                    {{ record.wind_speed ? record.wind_speed.toFixed(2) : '-' }} m/s
                  </template>
  
                  <template v-else-if="column.key === 'timestamp'">
                    {{ formatTimestamp(record.timestamp) }}
                  </template>
                </template>
              </a-table>
            </div>
          </div>
        </a-tab-pane>
        
        <a-tab-pane key="monitoring" tab="系统监控">
          <div class="example-section">
            <h3>系统监控示例</h3>
            <p>本示例展示如何查看系统的运行状态和性能指标。</p>
            
            <a-form :form="monitoringForm" layout="vertical" style="margin-top: 20px">
              <a-form-item label="监控指标">
                <a-select v-model:value="monitoringForm.metric" placeholder="选择监控指标">
                  <a-select-option value="api_requests">API请求率</a-select-option>
                  <a-select-option value="api_response_time">API响应时间</a-select-option>
                  <a-select-option value="cpu_usage">CPU使用率</a-select-option>
                  <a-select-option value="memory_usage">内存使用率</a-select-option>
                </a-select>
              </a-form-item>
              
              <a-form-item label="时间范围">
                <a-select v-model:value="monitoringForm.timeRange" placeholder="选择时间范围">
                  <a-select-option value="1h">最近1小时</a-select-option>
                  <a-select-option value="6h">最近6小时</a-select-option>
                  <a-select-option value="24h">最近24小时</a-select-option>
                  <a-select-option value="7d">最近7天</a-select-option>
                </a-select>
              </a-form-item>
              
              <a-form-item>
                <a-button type="primary" @click="loadMonitoringData" :loading="monitoringLoading">
                  加载监控数据
                </a-button>
              </a-form-item>
            </a-form>
            
            <div v-if="monitoringData" class="result-section">
              <a-alert
                type="success"
                message="监控数据加载成功"
                show-icon
              />
              <div class="chart-container" ref="monitoringChart"></div>
            </div>
          </div>
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import * as L from 'leaflet'
import * as echarts from 'echarts'

// 标签页
const activeTab = ref('path-planning')

// 路径规划
const pathPlanningForm = reactive({
  startLat: '39.9042',
  startLng: '116.4074',
  endLat: '39.9142',
  endLng: '116.4174',
  algorithm: 'astar'
})
const pathPlanningLoading = ref(false)
const pathPlanningResult = ref(null)
const mapContainer = ref(null)
let map = null

// 气象数据
const weatherForm = reactive({
  type: 'temperature',
  dateRange: null
})
const weatherLoading = ref(false)
const weatherData = ref(null)
const weatherChart = ref(null)
let weatherEchart = null

// 真实数据
const realDataForm = reactive({
  type: 'ground_station'
})
const realDataLoading = ref(false)
const realData = ref(null)
const realDataColumns = [
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
    title: '纬度',
    dataIndex: 'latitude',
    key: 'latitude'
  },
  {
    title: '经度',
    dataIndex: 'longitude',
    key: 'longitude'
  },
  {
    title: '温度',
    dataIndex: 'temperature',
    key: 'temperature'
  },
  {
    title: '湿度',
    dataIndex: 'humidity',
    key: 'humidity'
  },
  {
    title: '风速',
    dataIndex: 'wind_speed',
    key: 'wind_speed'
  },
  {
    title: '时间',
    dataIndex: 'timestamp',
    key: 'timestamp'
  }
]

// 监控数据
const monitoringForm = reactive({
  metric: 'api_requests',
  timeRange: '6h'
})
const monitoringLoading = ref(false)
const monitoringData = ref(null)
const monitoringChart = ref(null)
let monitoringEchart = null

// 运行路径规划
const runPathPlanning = () => {
  pathPlanningLoading.value = true
  
  // 模拟路径规划
  setTimeout(() => {
    pathPlanningLoading.value = false
    pathPlanningResult.value = {
      length: 1500,
      duration: 120,
      points: [
        [39.9042, 116.4074],
        [39.9062, 116.4084],
        [39.9082, 116.4094],
        [39.9102, 116.4104],
        [39.9122, 116.4124],
        [39.9142, 116.4174]
      ]
    }
    
    // 初始化地图
    nextTick(() => {
      initMap()
    })
    
    message.success('路径规划成功')
  }, 1500)
}

// 初始化地图
const initMap = () => {
  if (map) {
    map.remove()
  }
  
  map = L.map(mapContainer.value).setView([39.9042, 116.4074], 13)
  
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map)
  
  // 添加起点和终点
  L.marker([parseFloat(pathPlanningForm.startLat), parseFloat(pathPlanningForm.startLng)]).addTo(map)
    .bindPopup('起点')
    .openPopup()
  
  L.marker([parseFloat(pathPlanningForm.endLat), parseFloat(pathPlanningForm.endLng)]).addTo(map)
    .bindPopup('终点')
  
  // 添加路径
  if (pathPlanningResult.value) {
    const path = L.polyline(pathPlanningResult.value.points, {
      color: 'blue',
      weight: 3,
      opacity: 0.7
    }).addTo(map)
    
    map.fitBounds(path.getBounds())
  }
}

// 加载气象数据
const loadWeatherData = () => {
  weatherLoading.value = true
  
  // 模拟气象数据
  setTimeout(() => {
    weatherLoading.value = false
    weatherData.value = {
      type: weatherForm.type,
      data: [
        { time: '00:00', value: 20 + Math.random() * 5 },
        { time: '03:00', value: 19 + Math.random() * 4 },
        { time: '06:00', value: 18 + Math.random() * 3 },
        { time: '09:00', value: 22 + Math.random() * 5 },
        { time: '12:00', value: 25 + Math.random() * 6 },
        { time: '15:00', value: 26 + Math.random() * 6 },
        { time: '18:00', value: 23 + Math.random() * 5 },
        { time: '21:00', value: 21 + Math.random() * 4 }
      ]
    }
    
    // 初始化图表
    nextTick(() => {
      initWeatherChart()
    })
    
    message.success('气象数据加载成功')
  }, 1500)
}

// 初始化气象图表
const initWeatherChart = () => {
  if (weatherEchart) {
    weatherEchart.dispose()
  }
  
  weatherEchart = echarts.init(weatherChart.value)
  
  const option = {
    title: {
      text: weatherForm.type === 'temperature' ? '温度变化' : 
             weatherForm.type === 'humidity' ? '湿度变化' : 
             weatherForm.type === 'wind' ? '风速变化' : '气压变化',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: weatherData.value.data.map(item => item.time)
    },
    yAxis: {
      type: 'value',
      name: weatherForm.type === 'temperature' ? '温度 (°C)' : 
             weatherForm.type === 'humidity' ? '湿度 (%)' : 
             weatherForm.type === 'wind' ? '风速 (m/s)' : '气压 (hPa)'
    },
    series: [{
      data: weatherData.value.data.map(item => item.value),
      type: 'line',
      smooth: true
    }]
  }
  
  weatherEchart.setOption(option)
}

// 加载真实数据
const loadRealData = () => {
  realDataLoading.value = true
  
  // 模拟真实数据
  setTimeout(() => {
    realDataLoading.value = false
    
    if (realDataForm.type === 'ground_station') {
      realData.value = [
        {
          id: 'GS001',
          name: '地面站1',
          latitude: 39.9042,
          longitude: 116.4074,
          temperature: 22.5 + Math.random() * 5,
          humidity: 65 + Math.random() * 10,
          wind_speed: 5 + Math.random() * 3,
          timestamp: Date.now()
        },
        {
          id: 'GS002',
          name: '地面站2',
          latitude: 39.9142,
          longitude: 116.4174,
          temperature: 23.5 + Math.random() * 5,
          humidity: 60 + Math.random() * 10,
          wind_speed: 4 + Math.random() * 3,
          timestamp: Date.now()
        }
      ]
    } else {
      realData.value = [
        {
          id: 'B001',
          name: '浮标1',
          latitude: 39.8042,
          longitude: 116.3074,
          temperature: 20.5 + Math.random() * 3,
          humidity: 70 + Math.random() * 10,
          wind_speed: 6 + Math.random() * 4,
          timestamp: Date.now()
        },
        {
          id: 'B002',
          name: '浮标2',
          latitude: 39.8142,
          longitude: 116.3174,
          temperature: 21.0 + Math.random() * 3,
          humidity: 68 + Math.random() * 10,
          wind_speed: 5 + Math.random() * 4,
          timestamp: Date.now()
        }
      ]
    }
    
    message.success('真实数据加载成功')
  }, 1500)
}

// 加载监控数据
const loadMonitoringData = () => {
  monitoringLoading.value = true
  
  // 模拟监控数据
  setTimeout(() => {
    monitoringLoading.value = false
    monitoringData.value = {
      metric: monitoringForm.metric,
      data: [
        { time: '00:00', value: Math.random() * 100 },
        { time: '03:00', value: Math.random() * 100 },
        { time: '06:00', value: Math.random() * 100 },
        { time: '09:00', value: Math.random() * 100 },
        { time: '12:00', value: Math.random() * 100 },
        { time: '15:00', value: Math.random() * 100 },
        { time: '18:00', value: Math.random() * 100 },
        { time: '21:00', value: Math.random() * 100 }
      ]
    }
    
    // 初始化图表
    nextTick(() => {
      initMonitoringChart()
    })
    
    message.success('监控数据加载成功')
  }, 1500)
}

// 初始化监控图表
const initMonitoringChart = () => {
  if (monitoringEchart) {
    monitoringEchart.dispose()
  }
  
  monitoringEchart = echarts.init(monitoringChart.value)
  
  const option = {
    title: {
      text: monitoringForm.metric === 'api_requests' ? 'API请求率' : 
             monitoringForm.metric === 'api_response_time' ? 'API响应时间' : 
             monitoringForm.metric === 'cpu_usage' ? 'CPU使用率' : '内存使用率',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: monitoringData.value.data.map(item => item.time)
    },
    yAxis: {
      type: 'value',
      name: monitoringForm.metric === 'api_requests' ? '请求/分钟' : 
             monitoringForm.metric === 'api_response_time' ? '响应时间 (ms)' : 
             monitoringForm.metric === 'cpu_usage' ? '使用率 (%)' : '使用率 (%)'
    },
    series: [{
      data: monitoringData.value.data.map(item => item.value),
      type: 'line',
      smooth: true
    }]
  }
  
  monitoringEchart.setOption(option)
}

// 格式化时间戳
const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleString()
}

// 响应式处理
const handleResize = () => {
  if (weatherEchart) {
    weatherEchart.resize()
  }
  if (monitoringEchart) {
    monitoringEchart.resize()
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})
</script>

<style scoped>
.example-view {
  padding: 20px;
}

.card {
  margin-bottom: 20px;
}

.example-section {
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
}

.result-section {
  margin-top: 20px;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.map-container {
  height: 400px;
  margin: 20px 0;
  border-radius: 8px;
  overflow: hidden;
}

.chart-container {
  height: 400px;
  margin: 20px 0;
  border-radius: 8px;
  overflow: hidden;
}

.result-details {
  margin-top: 16px;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 4px;
}

.result-details p {
  margin: 8px 0;
}
</style>
