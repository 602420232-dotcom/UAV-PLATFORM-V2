<template>
  <div class="order-view">
    <el-alert
      title="演示模式 - 订单不会实际派发到无人机系统"
      type="warning"
      :closable="false"
      show-icon
      class="demo-alert"
    />

    <!-- 顶部：数据范围 -->
    <el-card class="order-header" shadow="never">
      <div class="header-row">
        <div class="scope-info">
          <span class="scope-label">数据范围：</span>
          <DataScopeBadge :scope="activeScope" :team="authStore.team" />
        </div>
        <el-select
          v-model="dataScopeFilter"
          placeholder="数据范围（跟随账号）"
          clearable
          size="default"
          style="width: 220px"
        >
          <el-option label="跟随账号" value="" />
          <el-option label="仅个人" value="personal" />
          <el-option label="仅团队" value="team" />
          <el-option label="全部数据" value="all" />
        </el-select>
      </div>
    </el-card>

    <div class="layout">
      <el-card shadow="never" class="map-card">
        <template #header>
          <div class="card-header">
            <span class="header-icon">🗺️</span>
            <span>选择起点 / 终点</span>
          </div>
        </template>

        <div class="pick-form">
          <div class="point-block">
            <span class="point-icon start">起点</span>
            <el-input
              v-model="startPoint.name"
              placeholder="起点名称（如：总部仓库）"
              class="point-name"
            />
            <div class="coord-row">
              <el-input-number
                v-model="startPoint.lng"
                :min="-180"
                :max="180"
                :step="0.01"
                :controls="false"
                placeholder="经度"
                class="coord-input"
              />
              <el-input-number
                v-model="startPoint.lat"
                :min="-90"
                :max="90"
                :step="0.01"
                :controls="false"
                placeholder="纬度"
                class="coord-input"
              />
              <el-button plain type="primary" @click="locate('start')">定位</el-button>
            </div>
          </div>

          <div class="point-divider">
            <span>→</span>
          </div>

          <div class="point-block">
            <span class="point-icon end">终点</span>
            <el-input
              v-model="endPoint.name"
              placeholder="终点名称"
              class="point-name"
            />
            <div class="coord-row">
              <el-input-number
                v-model="endPoint.lng"
                :min="-180"
                :max="180"
                :step="0.01"
                :controls="false"
                placeholder="经度"
                class="coord-input"
              />
              <el-input-number
                v-model="endPoint.lat"
                :min="-90"
                :max="90"
                :step="0.01"
                :controls="false"
                placeholder="纬度"
                class="coord-input"
              />
              <el-button plain type="primary" @click="locate('end')">定位</el-button>
            </div>
          </div>
        </div>

        <div class="map-area">
          <div class="map-grid"></div>
          <div class="map-marker" :style="startPosStyle">
            <div class="marker-dot start"></div>
            <div class="marker-label">{{ startPoint.name || '起点' }}</div>
          </div>
          <div class="map-marker" :style="endPosStyle">
            <div class="marker-dot end"></div>
            <div class="marker-label">{{ endPoint.name || '终点' }}</div>
          </div>
          <svg class="route-line" viewBox="0 0 100 100" preserveAspectRatio="none">
            <line
              x1="20" y1="30" x2="80" y2="70"
              stroke="#409EFF"
              stroke-width="0.8"
              stroke-dasharray="2 1"
            />
          </svg>
          <div class="map-legend">
            <span>📌 起点：{{ startPoint.name || '未命名' }}</span>
            <span>🎯 终点：{{ endPoint.name || '未命名' }}</span>
            <span>📏 距离：约 {{ distance }} km</span>
          </div>
        </div>
      </el-card>

      <div class="param-panel">
        <el-card shadow="never" class="panel-card">
          <template #header>
            <div class="card-header">
              <span class="header-icon">📦</span>
              <span>基础配置</span>
            </div>
          </template>

          <el-form :model="orderForm" label-position="top">
            <el-form-item label="起点名称">
              <el-input v-model="startPoint.name" placeholder="请输入起点名称" />
            </el-form-item>

            <el-form-item label="终点名称">
              <el-input v-model="endPoint.name" placeholder="请输入终点名称" />
            </el-form-item>

            <el-form-item label="货物重量 (kg)">
              <el-input-number
                v-model="orderForm.weight"
                :min="0.1"
                :max="50"
                :step="0.1"
                style="width: 100%"
              />
            </el-form-item>

            <el-form-item label="优先级">
              <el-select v-model="orderForm.priority" style="width: 100%">
                <el-option label="普通" value="normal" />
                <el-option label="加急" value="urgent" />
                <el-option label="特快" value="express" />
                <el-option label="优先保障" value="guaranteed" />
              </el-select>
            </el-form-item>

            <el-form-item label="送达时间">
              <el-date-picker
                v-model="orderForm.deliveryTime"
                type="datetime"
                placeholder="选择送达日期时间"
                style="width: 100%"
                value-format="YYYY-MM-DD HH:mm:ss"
              />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card v-if="hasAdvanced" shadow="never" class="panel-card advanced-card">
          <template #header>
            <div class="card-header">
              <span class="header-icon">⚙️</span>
              <span>高级配置</span>
              <el-tag size="small" type="info" effect="light" class="advanced-tag">飞控专用</el-tag>
            </div>
          </template>

          <el-form label-position="top">
            <el-form-item label="飞行高度 (米)">
              <el-input-number
                v-model="advancedConfig.flightAltitude"
                :min="50"
                :max="500"
                :step="10"
                style="width: 100%"
              />
            </el-form-item>

            <el-form-item label="航路 RNP (Required Navigation Performance)">
              <el-input-number
                v-model="advancedConfig.rnp"
                :min="0.1"
                :max="9.9"
                :step="0.1"
                :precision="1"
                style="width: 100%"
              />
            </el-form-item>

            <el-divider content-position="left">载荷参数</el-divider>

            <el-form-item label="电池电量 (%)">
              <el-input-number
                v-model="advancedConfig.payload.battery"
                :min="0"
                :max="100"
                :step="5"
                style="width: 100%"
              />
            </el-form-item>

            <el-form-item label="形状">
              <el-select v-model="advancedConfig.payload.shape" style="width: 100%">
                <el-option label="长方体" value="rectangular" />
                <el-option label="圆柱体" value="cylindrical" />
                <el-option label="球形" value="spherical" />
                <el-option label="不规则" value="irregular" />
              </el-select>
            </el-form-item>

            <el-form-item label="尺寸 (长 × 宽 × 高 cm)">
              <div class="size-row">
                <el-input-number v-model="advancedConfig.payload.length" :min="1" :step="1" placeholder="长" />
                <span class="size-sep">×</span>
                <el-input-number v-model="advancedConfig.payload.width" :min="1" :step="1" placeholder="宽" />
                <span class="size-sep">×</span>
                <el-input-number v-model="advancedConfig.payload.height" :min="1" :step="1" placeholder="高" />
              </div>
            </el-form-item>

            <el-form-item label="形状描述">
              <el-input
                v-model="advancedConfig.payload.description"
                type="textarea"
                :rows="2"
                placeholder="描述载荷外观与特殊要求"
              />
            </el-form-item>

            <el-divider content-position="left">飞行策略</el-divider>

            <el-form-item label="禁飞区避让策略">
              <el-select v-model="advancedConfig.noFlyStrategy" style="width: 100%">
                <el-option label="严格 (strict)" value="strict" />
                <el-option label="中等 (moderate)" value="moderate" />
                <el-option label="宽松 (relax)" value="relax" />
              </el-select>
            </el-form-item>

            <el-form-item label="气象敏感度">
              <el-switch
                v-model="advancedConfig.weatherSensitive"
                active-text="开启"
                inactive-text="关闭"
              />
            </el-form-item>
          </el-form>
        </el-card>

        <el-button type="primary" class="submit-btn" size="large" @click="submitOrder">
          提交订单
        </el-button>

        <div class="footer-tip">
          <el-icon><InfoFilled /></el-icon>
          <span>您的订单不会实际派发，仅为演示</span>
        </div>
      </div>
    </div>

    <!-- 历史订单列表 (基于数据范围过滤) -->
    <el-card shadow="never" class="history-card">
      <template #header>
        <div class="card-header">
          <span class="header-icon">📋</span>
          <span>历史订单 ({{ visibleOrders.length }} 条 · 可见范围)</span>
        </div>
      </template>
      <el-table :data="visibleOrders" stripe border size="small" style="width: 100%">
        <el-table-column prop="id" label="订单编号" width="130" />
        <el-table-column prop="from" label="起点" min-width="140" show-overflow-tooltip />
        <el-table-column prop="to" label="终点" min-width="140" show-overflow-tooltip />
        <el-table-column prop="weight" label="重量(kg)" width="90" align="right" />
        <el-table-column label="负责人" width="160">
          <template #default="{ row }">
            <div class="owner-cell">
              <span>{{ row.owner }}</span>
              <el-tag size="small" type="info" effect="plain">{{ teamDisplay(row.team) }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="statusTag(row.status)" effect="light">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="180" />
      </el-table>
      <el-empty
        v-if="visibleOrders.length === 0"
        description="当前数据范围下暂无订单，可尝试切换数据范围。"
        :image-size="80"
      />
    </el-card>
  </div>
</template>

<script setup>
import { reactive, computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import { useAuthStore, TEAM_LABELS } from '../../stores/auth'
import { logAction, AUDIT_ACTIONS } from '../../utils/audit'
import { useNotificationStore } from '../../stores/notification'
import DataScopeBadge from '../../components/shared/DataScopeBadge.vue'

const authStore = useAuthStore()
const notificationStore = useNotificationStore()
const hasAdvanced = computed(() => authStore.hasAction('orders:advanced'))

// 数据范围
const dataScopeFilter = ref('')
const activeScope = computed(() => dataScopeFilter.value || authStore.dataScope || 'personal')

const startPoint = reactive({
  name: '总部仓库',
  lng: 116.4074,
  lat: 39.9042
})

const endPoint = reactive({
  name: '中关村配送点',
  lng: 116.3162,
  lat: 39.9847
})

const orderForm = reactive({
  weight: 2.5,
  priority: 'normal',
  deliveryTime: ''
})

const advancedConfig = reactive({
  flightAltitude: 120,
  rnp: 1.0,
  payload: {
    battery: 85,
    shape: 'rectangular',
    length: 30,
    width: 20,
    height: 15,
    description: ''
  },
  noFlyStrategy: 'moderate',
  weatherSensitive: true
})

const startPosStyle = computed(() => ({ left: '20%', top: '30%' }))
const endPosStyle = computed(() => ({ left: '80%', top: '70%' }))

const distance = computed(() => {
  const dx = endPoint.lng - startPoint.lng
  const dy = endPoint.lat - startPoint.lat
  return (Math.sqrt(dx * dx + dy * dy) * 111).toFixed(1)
})

function teamDisplay(team) {
  return TEAM_LABELS[team] || team || '-'
}

function statusTag(status) {
  return {
    '待调度': 'warning',
    '执行中': 'primary',
    '已完成': 'success',
    '已取消': 'info'
  }[status] || 'info'
}

function locate(type) {
  const name = type === 'start' ? startPoint.name : endPoint.name
  ElMessage.success(`已定位${type === 'start' ? '起点' : '终点'}：${name || '未命名'}`)
}

// 历史订单 mock (带 owner / team 字段)
const ownerLabel = computed(() => authStore.username || authStore.displayName || '当前用户')
const ownerTeam = computed(() => authStore.team || 'team-a')
const historyOrders = ref([
  { id: 'O-2026-0001', from: '总部仓库', to: '中关村配送点', weight: 2.5, owner: ownerLabel.value, ownerId: 'user01', team: 'team-a', status: '执行中', createdAt: '2026-06-09 08:15' },
  { id: 'O-2026-0002', from: '海淀仓A', to: '西二旗医院', weight: 8.5, owner: '张工', ownerId: 'user01', team: 'team-a', status: '已完成', createdAt: '2026-06-09 07:30' },
  { id: 'O-2026-0003', from: '通州生鲜仓', to: '朝阳国贸', weight: 12.0, owner: '李工', ownerId: 'flight01', team: 'team-b', status: '待调度', createdAt: '2026-06-09 09:02' },
  { id: 'O-2026-0004', from: '亦庄变电站', to: '次渠变电站', weight: 2.0, owner: '赵工', ownerId: 'test01', team: 'team-c', status: '已完成', createdAt: '2026-06-08 14:20' },
  { id: 'O-2026-0005', from: '丰台医药仓', to: '丰台医院', weight: 3.5, owner: '陈工', ownerId: 'deploy01', team: 'team-c', status: '待调度', createdAt: '2026-06-09 10:10' },
  { id: 'O-2026-0006', from: '海淀应急中心', to: '门头沟山区', weight: 15.0, owner: '王工', ownerId: 'prod01', team: 'team-a', status: '已完成', createdAt: '2026-06-08 16:45' }
])

function _canSeeOrder(ownerId, team) {
  const scope = activeScope.value
  if (scope === 'all') return true
  if (scope === 'personal') {
    const uid = authStore.userId
    return ownerId && uid && String(ownerId) === String(uid)
  }
  if (scope === 'team') {
    return team && authStore.team && team === authStore.team
  }
  return true
}

const visibleOrders = computed(() => historyOrders.value.filter(o => _canSeeOrder(o.ownerId, o.team)))

async function submitOrder() {
  if (!startPoint.name || !endPoint.name) {
    ElMessage.warning('请填写起点和终点名称')
    return
  }
  if (!orderForm.deliveryTime) {
    ElMessage.warning('请选择送达时间')
    return
  }

  const confirmed = await authStore.requireSensitiveConfirmation('提交运输订单')
  if (!confirmed) return

  const payload = {
    startPoint: { ...startPoint },
    endPoint: { ...endPoint },
    weight: orderForm.weight,
    priority: orderForm.priority,
    deliveryTime: orderForm.deliveryTime
  }

  if (hasAdvanced.value) {
    payload.advanced = { ...advancedConfig, payload: { ...advancedConfig.payload } }
  }

  console.log('[演示模式] 订单提交:', payload)
  logAction({
    action: AUDIT_ACTIONS.SUBMIT_ORDER,
    target: 'orders/submit',
    detail: `${startPoint.name || startPoint.lng + ',' + startPoint.lat} → ${endPoint.name || endPoint.lng + ',' + endPoint.lat}`,
    level: 'info'
  })
  ElMessage.success('订单已提交（演示模式，不会实际派发）')
  // 加入历史订单
  historyOrders.value.unshift({
    id: 'O-2026-' + String(historyOrders.value.length + 1).padStart(4, '0'),
    from: startPoint.name,
    to: endPoint.name,
    weight: orderForm.weight,
    owner: ownerLabel.value,
    ownerId: authStore.userId || authStore.username || 'anonymous',
    team: ownerTeam.value,
    status: '待调度',
    createdAt: new Date().toLocaleString('zh-CN', { hour12: false }).replace(/\//g, '-')
  })
  notificationStore.pushWithDesktop({
    type: 'success',
    title: '订单已提交',
    message: `运输订单：${startPoint.name || startPoint.lng + ',' + startPoint.lat} → ${endPoint.name || endPoint.lng + ',' + endPoint.lat}`,
    source: 'task'
  })
}
</script>

<style scoped>
.order-view {
  padding: 20px;
}

.demo-alert {
  margin-bottom: 16px;
}

.order-header {
  margin-bottom: 16px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.header-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.scope-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.scope-label {
  font-size: 13px;
  color: #606266;
}

.layout {
  display: grid;
  grid-template-columns: 7fr 3fr;
  gap: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #1f2937;
}

.header-icon {
  font-size: 16px;
}

.map-card,
.panel-card {
  border-radius: 10px;
}

.pick-form {
  padding: 4px 0 16px;
}

.point-block {
  padding: 12px;
  border: 1px solid #f0f2f5;
  border-radius: 8px;
  background: #fafbfc;
}

.point-icon {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  padding: 3px 10px;
  border-radius: 12px;
  margin-bottom: 10px;
}

.point-icon.start {
  background: #409EFF;
}

.point-icon.end {
  background: #67C23A;
}

.point-name {
  margin-bottom: 10px;
}

.coord-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.coord-input {
  flex: 1;
}

.point-divider {
  text-align: center;
  padding: 8px 0;
  color: #c0c4cc;
  font-size: 18px;
}

.map-area {
  position: relative;
  height: 320px;
  background: linear-gradient(135deg, #e6f4ff 0%, #f0f9ff 50%, #e6fff0 100%);
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid #e6f0fa;
}

.map-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(64, 158, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(64, 158, 255, 0.08) 1px, transparent 1px);
  background-size: 30px 30px, 30px 30px;
}

.map-marker {
  position: absolute;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 2;
}

.marker-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 3px solid #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.marker-dot.start {
  background: #409EFF;
}

.marker-dot.end {
  background: #67C23A;
}

.marker-label {
  font-size: 11px;
  color: #374151;
  background: #fff;
  padding: 2px 6px;
  border-radius: 4px;
  margin-top: 4px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  white-space: nowrap;
}

.route-line {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.map-legend {
  position: absolute;
  left: 12px;
  bottom: 10px;
  background: rgba(255, 255, 255, 0.9);
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
  color: #6b7280;
  display: flex;
  flex-direction: column;
  gap: 2px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.param-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.advanced-card {
  background: #f5f7fa;
}

.advanced-tag {
  margin-left: auto;
}

.size-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.size-row :deep(.el-input-number) {
  flex: 1;
  width: auto !important;
  min-width: 0;
}

.size-sep {
  color: #909399;
  font-weight: 500;
}

.submit-btn {
  width: 100%;
}

.footer-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 12px;
  color: #909399;
  padding: 4px 0;
}

.history-card {
  margin-top: 16px;
  border-radius: 10px;
}

.owner-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

@media (max-width: 1100px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .map-area {
    height: 260px;
  }
}
</style>
