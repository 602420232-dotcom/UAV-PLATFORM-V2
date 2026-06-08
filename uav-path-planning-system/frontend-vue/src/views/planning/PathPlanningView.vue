<template>
  <div class="planning">
    <div class="page-title">路径规划</div>

    <a-row :gutter="[16, 16]">
      <!-- 左侧配置面板 -->
      <a-col :xs="24" :lg="8">
        <a-card title="规划配置">
          <a-form :model="formState" layout="vertical">
            <!-- 任务点 -->
            <a-form-item label="任务点">
              <a-row :gutter="[8, 8]">
                <a-col :span="12">
                  <a-button type="primary" block @click="addTaskPoint">
                    <template #icon><PlusOutlined /></template>
                    添加
                  </a-button>
                </a-col>
                <a-col :span="12">
                  <a-button block @click="planningStore.clearTaskPoints">
                    <template #icon><DeleteOutlined /></template>
                    清空
                  </a-button>
                </a-col>
              </a-row>
              <a-list
                :data-source="planningStore.taskPoints"
                size="small"
                class="task-point-list"
              >
                <template #renderItem="{ item, index }">
                  <a-list-item>
                    <a-list-item-meta
                      :title="`任务点 ${index + 1}: ${item.name}`"
                      :description="`坐标: ${item.lat?.toFixed(4)}, ${item.lng?.toFixed(4)}`"
                    />
                    <template #actions>
                      <a-button
                        type="text"
                        danger
                        size="small"
                        @click="planningStore.taskPoints.splice(index, 1)"
                      >
                        <template #icon><DeleteOutlined /></template>
                      </a-button>
                    </template>
                  </a-list-item>
                </template>
              </a-list>
            </a-form-item>

            <!-- 无人机 -->
            <a-form-item label="选择无人机">
              <a-select v-model:value="formState.selectedDrone" placeholder="请选择">
                <a-select-option
                  v-for="drone in droneStore.list"
                  :key="drone.id"
                  :value="drone.id"
                >
                  {{ drone.name }} ({{ drone.status }})
                </a-select-option>
              </a-select>
            </a-form-item>

            <!-- 风险阈值 -->
            <a-form-item :label="`风险阈值：${formState.riskThreshold.toFixed(1)}`">
              <a-slider
                v-model:value="formState.riskThreshold"
                :min="0"
                :max="10"
                :step="0.1"
              />
            </a-form-item>

            <a-form-item label="禁飞区">
              <a-space direction="vertical" style="width: 100%">
                <div v-for="zone in planningStore.noFlyZones" :key="zone.id" class="nfz-item">
                  <span>{{ zone.name }} ({{ zone.type }})</span>
                  <a-button
                    type="text"
                    danger
                    size="small"
                    @click="planningStore.removeNoFlyZone(zone.id)"
                  >
                    <template #icon><CloseOutlined /></template>
                  </a-button>
                </div>
                <a-button size="small" @click="addNoFlyZone">
                  <template #icon><PlusOutlined /></template>
                  添加禁飞区
                </a-button>
              </a-space>
            </a-form-item>

            <a-form-item>
              <a-button
                type="primary"
                block
                :loading="planningStore.loading"
                @click="handleExecute"
              >
                <template #icon><PlayCircleOutlined /></template>
                执行路径规划
              </a-button>
            </a-form-item>

            <a-form-item>
              <a-space>
                <a-button @click="handleSavePlan">保存方案</a-button>
                <a-button @click="handleExport">导出</a-button>
                <a-button @click="handlePrint">打印</a-button>
              </a-space>
            </a-form-item>
          </a-form>
        </a-card>

        <!-- 实时状态 -->
        <a-card title="实时状态" style="margin-top: 16px">
          <a-descriptions :column="1" size="small" bordered>
            <a-descriptions-item label="风速">
              {{ planningStore.realtime.windSpeed }} m/s
            </a-descriptions-item>
            <a-descriptions-item label="温度">
              {{ planningStore.realtime.temperature }} °C
            </a-descriptions-item>
            <a-descriptions-item label="湿度">
              {{ planningStore.realtime.humidity }} %
            </a-descriptions-item>
            <a-descriptions-item label="预警数">
              <a-badge :count="planningStore.realtime.alertCount" />
            </a-descriptions-item>
            <a-descriptions-item label="风险等级">
              <a-tag :color="planningStore.realtime.riskLevel === '低' ? 'green' : 'orange'">
                {{ planningStore.realtime.riskLevel }}
              </a-tag>
            </a-descriptions-item>
          </a-descriptions>
        </a-card>
      </a-col>

      <!-- 右侧结果区 -->
      <a-col :xs="24" :lg="16">
        <a-card title="路径可视化" class="map-card">
          <div class="map-container">
            <div ref="leafletRef" class="leaflet-map"></div>
            <div v-if="!planningStore.result" class="map-placeholder">
              <a-empty description="请配置任务点后执行路径规划" />
            </div>
          </div>
        </a-card>

        <a-card title="规划结果" style="margin-top: 16px" v-if="planningStore.result">
          <a-descriptions :column="4" bordered size="small">
            <a-descriptions-item label="总任务点">{{ planningStore.result.taskCount || planningStore.taskPoints.length }}</a-descriptions-item>
            <a-descriptions-item label="使用无人机">{{ planningStore.result.droneCount || 1 }}</a-descriptions-item>
            <a-descriptions-item label="总距离">{{ planningStore.result.totalDistance || 0 }} m</a-descriptions-item>
            <a-descriptions-item label="预计时间">{{ planningStore.result.totalTime || 0 }} 分钟</a-descriptions-item>
          </a-descriptions>
          <a-table
            :columns="routeColumns"
            :data-source="planningStore.result.routes"
            size="small"
            :pagination="false"
            style="margin-top: 12px"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'risk'">
                <a-tag :color="record.riskLevel === '低' ? 'green' : record.riskLevel === '中' ? 'orange' : 'red'">
                  {{ record.riskLevel || record.risk || '低' }}
                </a-tag>
              </template>
              <template v-else-if="column.key === 'path'">
                <span class="path-text">{{ (record.path || []).join(' → ') }}</span>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>

    <!-- 添加任务点模态框 -->
    <a-modal title="添加任务点" v-model:open="pointModalVisible" @ok="confirmAddPoint" ok-text="添加">
      <a-form :model="pointForm" layout="vertical">
        <a-form-item label="名称">
          <a-input v-model:value="pointForm.name" placeholder="如：配送点A" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="纬度">
              <a-input-number v-model:value="pointForm.lat" :min="-90" :max="90" :step="0.0001" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="经度">
              <a-input-number v-model:value="pointForm.lng" :min="-180" :max="180" :step="0.0001" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>

    <!-- 禁飞区模态框 -->
    <a-modal title="添加禁飞区" v-model:open="nfzModalVisible" @ok="confirmAddNoFly" ok-text="添加">
      <a-form :model="nfzForm" layout="vertical">
        <a-form-item label="名称">
          <a-input v-model:value="nfzForm.name" placeholder="如：机场禁飞区" />
        </a-form-item>
        <a-form-item label="类型">
          <a-select v-model:value="nfzForm.type">
            <a-select-option value="circle">圆形区域</a-select-option>
            <a-select-option value="polygon">多边形区域</a-select-option>
          </a-select>
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="中心纬度">
              <a-input-number v-model:value="nfzForm.lat" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="中心经度">
              <a-input-number v-model:value="nfzForm.lng" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="半径 (m)">
          <a-input-number v-model:value="nfzForm.radius" :min="1" style="width: 100%" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  DeleteOutlined,
  CloseOutlined,
  PlayCircleOutlined
} from '@ant-design/icons-vue'
import { usePlanningStore } from '../../stores/planning'
import { useDroneStore } from '../../stores/drones'

const planningStore = usePlanningStore()
const droneStore = useDroneStore()

const formState = reactive({
  selectedDrone: null,
  riskThreshold: 3.0
})

const pointModalVisible = ref(false)
const nfzModalVisible = ref(false)
const pointForm = reactive({ name: '', lat: 39.9042, lng: 116.4074 })
const nfzForm = reactive({ name: '新禁飞区', type: 'circle', lat: 39.9142, lng: 116.4174, radius: 200 })

const leafletRef = ref(null)
let leafletMap = null

const routeColumns = [
  { title: '无人机 ID', dataIndex: 'droneId', key: 'droneId', width: '15%' },
  { title: '飞行路径', key: 'path' },
  { title: '距离 (m)', dataIndex: 'distance', key: 'distance', width: '12%' },
  { title: '时间 (分钟)', dataIndex: 'time', key: 'time', width: '12%' },
  { title: '风险', key: 'risk', width: '10%' }
]

function addTaskPoint() {
  pointForm.name = `任务点${planningStore.taskPoints.length + 1}`
  pointModalVisible.value = true
}

function confirmAddPoint() {
  if (!pointForm.lat || !pointForm.lng) {
    message.warning('请输入经纬度')
    return
  }
  planningStore.addTaskPoint({ ...pointForm })
  pointModalVisible.value = false
  message.success('任务点已添加')
}

function addNoFlyZone() {
  nfzModalVisible.value = true
}

function confirmAddNoFly() {
  planningStore.addNoFlyZone({
    id: Date.now(),
    name: nfzForm.name,
    type: nfzForm.type,
    center: [nfzForm.lat, nfzForm.lng],
    radius: nfzForm.radius
  })
  nfzModalVisible.value = false
  message.success('禁飞区已添加')
}

async function handleExecute() {
  if (planningStore.taskPoints.length < 1) {
    message.warning('请至少添加一个任务点')
    return
  }
  await planningStore.execute({ droneId: formState.selectedDrone, riskThreshold: formState.riskThreshold })
  message.success('规划完成')
}

function handleSavePlan() {
  if (!planningStore.result) {
    message.warning('请先执行路径规划')
    return
  }
  planningStore.savePlan(`方案 ${planningStore.savedPlans.length + 1}`)
  message.success('方案已保存')
}

function handleExport() {
  message.info('导出功能开发中')
}

function handlePrint() {
  message.info('打印功能开发中')
}

function initLeaflet() {
  if (!leafletRef.value || !window.L) return
  leafletMap = window.L.map(leafletRef.value).setView([39.9042, 116.4074], 12)
  window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap',
    maxZoom: 18
  }).addTo(leafletMap)
  // 标记任务点
  planningStore.taskPoints.forEach((p, i) => {
    if (p.lat && p.lng) {
      window.L.marker([p.lat, p.lng]).addTo(leafletMap).bindPopup(`任务点 ${i + 1}: ${p.name}`)
    }
  })
}

onMounted(async () => {
  await droneStore.fetchAll()
  nextTick(() => {
    if (!window.L) {
      // 如果 Leaflet 没通过 CDN 加载，使用占位图
      const el = leafletRef.value
      if (el) {
        el.style.background =
          'radial-gradient(circle, #e6f7ff 0%, #bae7ff 100%)'
        el.innerHTML =
          '<div style="text-align:center;padding:120px 0;color:#1677ff;font-size:16px;">地图区域（Leaflet 通过 public/index.html 加载）</div>'
      }
    } else {
      initLeaflet()
    }
  })
})

onBeforeUnmount(() => {
  if (leafletMap) {
    leafletMap.remove()
    leafletMap = null
  }
})
</script>

<style scoped>
.planning {
  padding: 0;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
  color: rgba(0, 0, 0, 0.88);
}

.task-point-list {
  margin-top: 8px;
  max-height: 240px;
  overflow-y: auto;
}

.nfz-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  background: rgba(255, 77, 79, 0.06);
  border-radius: 4px;
  font-size: 13px;
}

.map-container {
  position: relative;
  width: 100%;
  height: 480px;
  overflow: hidden;
  border-radius: 4px;
}

.leaflet-map {
  width: 100%;
  height: 100%;
  background: #f0f5ff;
}

.map-placeholder {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.path-text {
  font-size: 13px;
  color: rgba(0, 0, 0, 0.75);
}
</style>
