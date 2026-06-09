<template>
  <div class="utm-integration-view">
    <!-- 顶部栏 -->
    <div class="top-bar">
      <div class="top-left">
        <h2 class="page-title">低空 UTM 对接</h2>
        <el-tag :type="authStore.demoMode ? 'warning' : 'success'" effect="light" class="mode-tag">
          {{ authStore.demoMode ? '演示环境' : '生产环境' }}
        </el-tag>
      </div>
      <div class="top-center">
        <el-card shadow="never" class="status-card" :class="connectionStatus.class">
          <div class="status-row">
            <el-icon :size="18" class="status-icon"><component :is="connectionStatus.icon" /></el-icon>
            <div class="status-text">
              <div class="status-label">对接状态</div>
              <div class="status-value">{{ connectionStatus.label }}</div>
            </div>
          </div>
          <div class="status-meta">
            <div>心跳：<b>{{ heartbeatCount }}</b> 次</div>
            <div>最后同步：<b>{{ formatTime(lastSyncTime) }}</b></div>
            <div>UTM 版本：<b>{{ utmVersion }}</b></div>
          </div>
        </el-card>
      </div>
      <div class="top-right">
        <el-button type="primary" :icon="Refresh" @click="manualSync">手动同步</el-button>
        <el-button :icon="Switch" @click="toggleEnv">切换环境</el-button>
        <el-button type="danger" plain :icon="Close" @click="disconnect">断开连接</el-button>
      </div>
    </div>

    <!-- 主体三栏 -->
    <div class="main-grid">
      <!-- 左栏：报备表单 -->
      <el-card shadow="never" class="col-panel col-report">
        <template #header>
          <div class="panel-head">
            <el-icon><Document /></el-icon>
            <span>飞行任务报备</span>
            <el-tag size="small" type="info">向 UTM 系统提交飞行计划</el-tag>
          </div>
        </template>

        <el-form :model="reportForm" label-position="top" size="default" class="report-form">
          <el-form-item label="任务编号">
            <el-select
              v-model="reportForm.taskId"
              filterable
              allow-create
              default-first-option
              placeholder="从已有任务中选择或手动输入"
            >
              <el-option v-for="t in mockTasks" :key="t.id" :label="t.id + ' · ' + t.name" :value="t.id" />
            </el-select>
          </el-form-item>

          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="空域类型">
                <el-select v-model="reportForm.airspaceType" placeholder="请选择">
                  <el-option label="低空 UAV" value="LOW_ALT_UAV" />
                  <el-option label="微型无人机" value="MICRO" />
                  <el-option label="小型无人机" value="SMALL" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="无人机型号">
                <el-select v-model="reportForm.uavModel" placeholder="请选择">
                  <el-option v-for="m in uavModelOptions" :key="m" :label="m" :value="m" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="起飞时间">
                <el-date-picker
                  v-model="reportForm.startTime"
                  type="datetime"
                  placeholder="选择起飞时间"
                  style="width: 100%"
                  value-format="YYYY-MM-DD HH:mm:ss"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="降落时间">
                <el-date-picker
                  v-model="reportForm.endTime"
                  type="datetime"
                  placeholder="选择降落时间"
                  style="width: 100%"
                  value-format="YYYY-MM-DD HH:mm:ss"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="最低高度 (m)">
                <el-input-number v-model="reportForm.altitudeMin" :min="0" :max="1000" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="最高高度 (m)">
                <el-input-number v-model="reportForm.altitudeMax" :min="0" :max="1000" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="起降点经度">
                <el-input-number v-model="reportForm.lng" :min="-180" :max="180" :step="0.0001" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="起降点纬度">
                <el-input-number v-model="reportForm.lat" :min="-90" :max="90" :step="0.0001" style="width: 100%" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="飞行航线（可选）">
            <el-input
              v-model="reportForm.route"
              type="textarea"
              :rows="4"
              placeholder="输入坐标点序列，格式：lng,lat;lng,lat ..."
            />
            <div class="form-actions-small">
              <el-button link type="primary" size="small" @click="importFromPlanning">从路径规划导入</el-button>
            </div>
          </el-form-item>

          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="机号">
                <el-input v-model="reportForm.uavNo" placeholder="如 UAV-0001" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="运营者名称">
                <el-input v-model="reportForm.operator" placeholder="运营者/公司名称" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="备注">
            <el-input v-model="reportForm.remark" type="textarea" :rows="2" placeholder="备注信息（可选）" />
          </el-form-item>

          <div class="form-actions">
            <el-button @click="resetReportForm">重置</el-button>
            <el-button type="primary" :loading="submitting" @click="submitReport">
              提交报备
            </el-button>
          </div>
        </el-form>
      </el-card>

      <!-- 中栏：审核列表 -->
      <el-card shadow="never" class="col-panel col-list">
        <template #header>
          <div class="panel-head">
            <el-icon><List /></el-icon>
            <span>合规审核列表</span>
            <el-badge v-if="pendingCount > 0" :value="pendingCount" class="pending-badge" />
          </div>
        </template>

        <div class="list-toolbar">
          <el-input
            v-model="searchKeyword"
            placeholder="按任务编号 / 报备编号筛选"
            clearable
            size="default"
            class="search-input"
            :prefix-icon="Search"
          />
          <el-select v-model="statusFilter" placeholder="状态筛选" size="default" clearable style="width: 140px">
            <el-option
              v-for="s in statusOptions"
              :key="s.value"
              :label="s.label"
              :value="s.value"
            />
          </el-select>
        </div>

        <el-table :data="filteredReports" size="small" height="520" stripe>
          <el-table-column prop="reportNo" label="报备编号" width="120" />
          <el-table-column prop="taskId" label="任务编号" width="110" />
          <el-table-column prop="airspaceType" label="空域类型" width="96" />
          <el-table-column label="状态" width="92">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.status)" size="small" effect="light">
                {{ statusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="submitTime" label="提交时间" min-width="160" />
          <el-table-column prop="reviewTime" label="审核时间" min-width="160">
            <template #default="{ row }">{{ row.reviewTime || '-' }}</template>
          </el-table-column>
          <el-table-column prop="reviewer" label="审核人" width="100">
            <template #default="{ row }">{{ row.reviewer || '-' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="showDetail(row)">详情</el-button>
              <el-button
                v-if="row.status === 'PENDING'"
                link
                type="warning"
                size="small"
                @click="withdrawReport(row)"
              >撤回</el-button>
              <el-button
                v-if="row.status === 'REJECTED' || row.status === 'WITHDRAWN'"
                link
                type="primary"
                size="small"
                @click="resubmitReport(row)"
              >重新提交</el-button>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty description="暂无报备记录" />
          </template>
        </el-table>
      </el-card>

      <!-- 右栏：状态监控与日志 -->
      <el-card shadow="never" class="col-panel col-monitor">
        <template #header>
          <div class="panel-head">
            <el-icon><Monitor /></el-icon>
            <span>对接状态与日志</span>
          </div>
        </template>

        <div class="monitor-summary">
          <div class="monitor-block">
            <div class="mon-label">心跳数</div>
            <div class="mon-value">{{ heartbeatCount }}</div>
          </div>
          <div class="monitor-block">
            <div class="mon-label">最后心跳</div>
            <div class="mon-value small">{{ formatTime(lastHeartbeatTime) }}</div>
          </div>
          <div class="monitor-block">
            <div class="mon-label">错误数</div>
            <div class="mon-value" :class="{ danger: errorCount > 0 }">{{ errorCount }}</div>
          </div>
        </div>

        <el-divider content-position="left">最近对接日志</el-divider>

        <div class="log-actions">
          <el-button size="small" @click="clearLogs">清理日志</el-button>
          <el-button size="small" type="primary" @click="simulatePush">模拟 UTM 推送</el-button>
          <el-button size="small" type="danger" plain @click="simulateLost">模拟心跳丢失</el-button>
        </div>

        <div class="log-container">
          <div v-for="log in recentLogs" :key="log.id" class="log-item" :class="'log-' + log.level">
            <span class="log-time">{{ formatTime(log.timestamp, true) }}</span>
            <el-tag size="small" :type="logLevelTag(log.level)" effect="plain" class="log-level-tag">
              {{ log.level.toUpperCase() }}
            </el-tag>
            <span class="log-content">{{ log.message }}</span>
          </div>
          <el-empty v-if="!recentLogs.length" description="暂无日志" :image-size="60" />
        </div>
      </el-card>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="报备详情" width="560px">
      <el-descriptions v-if="detailRow" :column="1" border size="small">
        <el-descriptions-item label="报备编号">{{ detailRow.reportNo }}</el-descriptions-item>
        <el-descriptions-item label="任务编号">{{ detailRow.taskId }}</el-descriptions-item>
        <el-descriptions-item label="空域类型">{{ detailRow.airspaceType }}</el-descriptions-item>
        <el-descriptions-item label="起飞时间">{{ detailRow.startTime }}</el-descriptions-item>
        <el-descriptions-item label="降落时间">{{ detailRow.endTime }}</el-descriptions-item>
        <el-descriptions-item label="飞行高度">{{ detailRow.altitudeMin }} - {{ detailRow.altitudeMax }} m</el-descriptions-item>
        <el-descriptions-item label="起降点">{{ detailRow.lng }}, {{ detailRow.lat }}</el-descriptions-item>
        <el-descriptions-item label="无人机型号">{{ detailRow.uavModel }}</el-descriptions-item>
        <el-descriptions-item label="机号">{{ detailRow.uavNo }}</el-descriptions-item>
        <el-descriptions-item label="运营者">{{ detailRow.operator }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTagType(detailRow.status)" size="small">{{ statusLabel(detailRow.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="航线">{{ detailRow.route || '-' }}</el-descriptions-item>
        <el-descriptions-item label="备注">{{ detailRow.remark || '-' }}</el-descriptions-item>
        <el-descriptions-item label="提交时间">{{ detailRow.submitTime }}</el-descriptions-item>
        <el-descriptions-item label="审核时间">{{ detailRow.reviewTime || '-' }}</el-descriptions-item>
        <el-descriptions-item label="审核人">{{ detailRow.reviewer || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Refresh, Switch, Close, Document, List, Monitor, Search,
  CircleCheck, CircleClose, Loading, Warning
} from '@element-plus/icons-vue'
import { useAuthStore } from '../../stores/auth'
import { logAction, AUDIT_ACTIONS } from '../../utils/audit'
import { useNotificationStore } from '../../stores/notification'

const authStore = useAuthStore()
const notificationStore = useNotificationStore()

// 对接状态
const connectionStatus = ref({ class: 'connected', icon: CircleCheck, label: '已连接' })
const heartbeatCount = ref(0)
const lastHeartbeatTime = ref(new Date())
const lastSyncTime = ref(new Date())
const errorCount = ref(0)
const utmVersion = ref('UTM v2.6.1')

// 任务选项
const mockTasks = [
  { id: 'T-2026-001', name: '北京海淀园区巡检' },
  { id: 'T-2026-002', name: '上海浦东配送' },
  { id: 'T-2026-003', name: '深圳南山航拍测绘' },
  { id: 'T-2026-004', name: '成都高新区应急勘察' }
]
const uavModelOptions = ['DJI M300 RTK', 'DJI M350 RTK', '飞鲨 FS-X8', '纵横 CW-15', '极侠 GX-10']

// 报备表单
const submitting = ref(false)
const reportForm = reactive({
  taskId: '',
  airspaceType: 'LOW_ALT_UAV',
  startTime: '',
  endTime: '',
  altitudeMin: 50,
  altitudeMax: 120,
  lng: 116.4074,
  lat: 39.9042,
  route: '',
  uavModel: 'DJI M300 RTK',
  uavNo: 'UAV-0001',
  operator: '演示运营者',
  remark: ''
})

// 报备记录
const statusOptions = [
  { value: 'PENDING', label: '待审核' },
  { value: 'APPROVED', label: '已通过' },
  { value: 'REJECTED', label: '已驳回' },
  { value: 'WITHDRAWN', label: '已取消' }
]

const initialReports = [
  {
    id: 1, reportNo: 'R-20260601-001', taskId: 'T-2026-001',
    airspaceType: 'LOW_ALT_UAV',
    startTime: '2026-06-01 08:00:00', endTime: '2026-06-01 09:00:00',
    altitudeMin: 50, altitudeMax: 120, lng: 116.4074, lat: 39.9042,
    uavModel: 'DJI M300 RTK', uavNo: 'UAV-0001', operator: '演示运营者',
    route: '116.4074,39.9042;116.4100,39.9055', remark: '园区日常巡检',
    status: 'APPROVED', submitTime: '2026-06-01 07:40:00',
    reviewTime: '2026-06-01 07:55:20', reviewer: 'UTM-系统'
  },
  {
    id: 2, reportNo: 'R-20260602-002', taskId: 'T-2026-002',
    airspaceType: 'SMALL',
    startTime: '2026-06-02 10:00:00', endTime: '2026-06-02 10:30:00',
    altitudeMin: 60, altitudeMax: 100, lng: 121.5445, lat: 31.2208,
    uavModel: 'DJI M350 RTK', uavNo: 'UAV-0002', operator: '演示运营者',
    route: '', remark: '急件配送',
    status: 'PENDING', submitTime: '2026-06-02 09:15:00',
    reviewTime: '', reviewer: ''
  },
  {
    id: 3, reportNo: 'R-20260603-003', taskId: 'T-2026-003',
    airspaceType: 'MICRO',
    startTime: '2026-06-03 14:00:00', endTime: '2026-06-03 15:30:00',
    altitudeMin: 30, altitudeMax: 80, lng: 113.9228, lat: 22.5330,
    uavModel: '飞鲨 FS-X8', uavNo: 'UAV-0003', operator: '南方测绘',
    route: '', remark: '测绘飞行',
    status: 'REJECTED', submitTime: '2026-06-03 13:30:00',
    reviewTime: '2026-06-03 13:50:10', reviewer: 'UTM-审核员A',
    remark: '与已批复航线冲突'
  },
  {
    id: 4, reportNo: 'R-20260604-004', taskId: 'T-2026-004',
    airspaceType: 'LOW_ALT_UAV',
    startTime: '2026-06-04 09:00:00', endTime: '2026-06-04 10:00:00',
    altitudeMin: 80, altitudeMax: 150, lng: 104.0665, lat: 30.5723,
    uavModel: '纵横 CW-15', uavNo: 'UAV-0004', operator: '西部应急',
    route: '', remark: '应急勘察飞行',
    status: 'PENDING', submitTime: '2026-06-04 08:20:00',
    reviewTime: '', reviewer: ''
  },
  {
    id: 5, reportNo: 'R-20260605-005', taskId: 'T-2026-001',
    airspaceType: 'LOW_ALT_UAV',
    startTime: '2026-06-05 16:00:00', endTime: '2026-06-05 17:00:00',
    altitudeMin: 50, altitudeMax: 120, lng: 116.4074, lat: 39.9042,
    uavModel: 'DJI M300 RTK', uavNo: 'UAV-0001', operator: '演示运营者',
    route: '', remark: '',
    status: 'WITHDRAWN', submitTime: '2026-06-05 15:30:00',
    reviewTime: '2026-06-05 15:45:00', reviewer: '运营者主动撤回'
  },
  {
    id: 6, reportNo: 'R-20260606-006', taskId: 'T-2026-002',
    airspaceType: 'SMALL',
    startTime: '2026-06-06 11:00:00', endTime: '2026-06-06 11:40:00',
    altitudeMin: 60, altitudeMax: 100, lng: 121.5445, lat: 31.2208,
    uavModel: 'DJI M350 RTK', uavNo: 'UAV-0002', operator: '演示运营者',
    route: '', remark: '',
    status: 'APPROVED', submitTime: '2026-06-06 10:15:00',
    reviewTime: '2026-06-06 10:30:20', reviewer: 'UTM-系统'
  }
]

const reports = ref([...initialReports])

const searchKeyword = ref('')
const statusFilter = ref('')

const filteredReports = computed(() => {
  const kw = searchKeyword.value.trim().toLowerCase()
  return reports.value.filter((r) => {
    const matchKw = !kw ||
      r.reportNo.toLowerCase().includes(kw) ||
      r.taskId.toLowerCase().includes(kw)
    const matchStatus = !statusFilter.value || r.status === statusFilter.value
    return matchKw && matchStatus
  })
})

const pendingCount = computed(() => reports.value.filter((r) => r.status === 'PENDING').length)

// 详情弹窗
const detailVisible = ref(false)
const detailRow = ref(null)

// 日志
const logs = ref([])
const recentLogs = computed(() => logs.value.slice(-20).reverse())

let heartbeatTimer = null

function addLog(level, message) {
  logs.value.push({
    id: Date.now() + Math.random(),
    level,
    message,
    timestamp: new Date()
  })
  if (logs.value.length > 200) logs.value = logs.value.slice(-200)
}

function statusLabel(s) {
  const m = {
    PENDING: '待审核', APPROVED: '已通过', REJECTED: '已驳回', WITHDRAWN: '已取消'
  }
  return m[s] || s
}

function statusTagType(s) {
  const m = {
    PENDING: 'warning', APPROVED: 'success', REJECTED: 'danger', WITHDRAWN: 'info'
  }
  return m[s] || 'info'
}

function logLevelTag(level) {
  const m = { success: 'success', error: 'danger', warning: 'warning', info: 'info' }
  return m[level] || 'info'
}

function pad(n) { return n < 10 ? '0' + n : String(n) }
function formatTime(t, withMs) {
  if (!t) return '-'
  const d = t instanceof Date ? t : new Date(t)
  if (isNaN(d.getTime())) return String(t)
  const s = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  if (withMs) return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  return s
}

function manualSync() {
  lastSyncTime.value = new Date()
  heartbeatCount.value += 3
  addLog('info', `[手动同步] 用户 ${authStore.username || 'anonymous'} 触发全量同步`)
  ElMessage.success('已触发手动同步')
}

function toggleEnv() {
  if (!authStore.demoMode) {
    ElMessage.warning('生产模式下禁止随意切换环境')
    return
  }
  ElMessageBox.confirm(
    '确认切换环境？当前为演示模式。',
    '切换环境确认',
    { confirmButtonText: '确认切换', cancelButtonText: '取消', type: 'warning' }
  )
    .then(() => {
      const isDemo = !authStore.demoMode
      authStore.setDemoMode(isDemo)
      addLog('info', `[环境切换] 切换为 ${isDemo ? '演示模式' : '生产模式'}`)
      ElMessage.success(`已切换为${isDemo ? '演示' : '生产'}模式`)
    })
    .catch(() => {})
}

function disconnect() {
  ElMessageBox.confirm(
    '确认断开与 UTM 系统的连接？',
    '断开确认',
    { confirmButtonText: '断开', cancelButtonText: '取消', type: 'warning' }
  )
    .then(() => {
      connectionStatus.value = { class: 'disconnected', icon: CircleClose, label: '未连接' }
      addLog('warning', '[连接] 已主动断开 UTM 连接')
      ElMessage.info('已断开连接')
    })
    .catch(() => {})
}

function simulatePush() {
  addLog('success', '[UTM 推送] 收到一条飞行状态更新：T-2026-001 已进入空域 A-301')
  ElMessage.success('已模拟一条 UTM 推送')
}

function simulateLost() {
  connectionStatus.value = { class: 'pending', icon: Warning, label: '对接中' }
  addLog('error', '[心跳] 检测到心跳丢失，尝试重连 ...')
  errorCount.value += 1
  setTimeout(() => {
    connectionStatus.value = { class: 'connected', icon: CircleCheck, label: '已连接' }
    addLog('success', '[心跳] 已恢复心跳')
  }, 2400)
}

function clearLogs() {
  logs.value = []
  ElMessage.success('日志已清理')
}

function resetReportForm() {
  reportForm.taskId = ''
  reportForm.airspaceType = 'LOW_ALT_UAV'
  reportForm.startTime = ''
  reportForm.endTime = ''
  reportForm.altitudeMin = 50
  reportForm.altitudeMax = 120
  reportForm.lng = 116.4074
  reportForm.lat = 39.9042
  reportForm.route = ''
  reportForm.uavModel = 'DJI M300 RTK'
  reportForm.uavNo = 'UAV-0001'
  reportForm.operator = '演示运营者'
  reportForm.remark = ''
}

function importFromPlanning() {
  reportForm.route = '116.4074,39.9042;116.4100,39.9055;116.4150,39.9070;116.4180,39.9090'
  ElMessage.success('已从路径规划模块导入示例航线')
  addLog('info', '[航线导入] 从路径规划模块导入示例航线')
}

async function submitReport() {
  if (!reportForm.taskId) {
    ElMessage.warning('请选择或填写任务编号')
    return
  }
  if (!reportForm.startTime || !reportForm.endTime) {
    ElMessage.warning('请填写起飞和降落时间')
    return
  }
  if (reportForm.altitudeMax < reportForm.altitudeMin) {
    ElMessage.warning('最高高度必须大于最低高度')
    return
  }

  const now = formatTime(new Date())
  const seq = String(reports.value.length + 1).padStart(3, '0')
  const newReport = {
    id: Date.now(),
    reportNo: `R-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${seq}`,
    taskId: reportForm.taskId,
    airspaceType: reportForm.airspaceType,
    startTime: reportForm.startTime,
    endTime: reportForm.endTime,
    altitudeMin: reportForm.altitudeMin,
    altitudeMax: reportForm.altitudeMax,
    lng: reportForm.lng,
    lat: reportForm.lat,
    route: reportForm.route,
    uavModel: reportForm.uavModel,
    uavNo: reportForm.uavNo,
    operator: reportForm.operator,
    remark: reportForm.remark,
    status: 'PENDING',
    submitTime: now,
    reviewTime: '',
    reviewer: ''
  }

  reports.value.unshift(newReport)
  addLog('info', `[报备] ${newReport.reportNo} 已提交，等待审核`)
  logAction({
    action: AUDIT_ACTIONS.SUBMIT_REPORT,
    target: newReport.reportNo,
    detail: `任务 ${newReport.taskId} 报备提交`,
    level: 'info'
  })
  ElMessage.success('报备已提交，进入待审核状态')

  submitting.value = true
  setTimeout(() => {
    submitting.value = false
    const rand = Math.random()
    const reviewNow = formatTime(new Date())
    if (rand < 0.7) {
      newReport.status = 'APPROVED'
      newReport.reviewTime = reviewNow
      newReport.reviewer = 'UTM-系统'
      addLog('success', `[报备] ${newReport.reportNo} 审核通过`)
      ElMessage.success(`${newReport.reportNo} 已自动审核通过`)
      notificationStore.pushWithDesktop({
        type: 'success',
        title: 'UTM 报备通过',
        message: `${newReport.reportNo}（任务 ${newReport.taskId}）已自动审核通过`,
        source: 'utm'
      })
    } else if (rand < 0.9) {
      newReport.status = 'REJECTED'
      newReport.reviewTime = reviewNow
      newReport.reviewer = 'UTM-审核员A'
      newReport.remark = (newReport.remark || '') + ' [驳回] 与管制空域冲突'
      addLog('warning', `[报备] ${newReport.reportNo} 被驳回`)
      ElMessage.warning(`${newReport.reportNo} 已被驳回`)
      notificationStore.pushWithDesktop({
        type: 'danger',
        title: 'UTM 报备被驳回',
        message: `${newReport.reportNo}（任务 ${newReport.taskId}）被驳回：与管制空域冲突`,
        source: 'utm'
      })
    } else {
      addLog('info', `[报备] ${newReport.reportNo} 进入人工审核队列`)
      ElMessage.info(`${newReport.reportNo} 进入人工审核，将延迟处理`)
      notificationStore.pushWithDesktop({
        type: 'warning',
        title: 'UTM 报备待人工审核',
        message: `${newReport.reportNo}（任务 ${newReport.taskId}）已进入人工审核队列`,
        source: 'utm'
      })
    }
  }, 1200)
}

function showDetail(row) {
  detailRow.value = row
  detailVisible.value = true
}

function withdrawReport(row) {
  ElMessageBox.confirm(`确认撤回报备 ${row.reportNo}？`, '撤回确认', { type: 'warning' })
    .then(() => {
      row.status = 'WITHDRAWN'
      row.reviewTime = formatTime(new Date())
      row.reviewer = '运营者主动撤回'
      addLog('warning', `[报备] ${row.reportNo} 已由运营者撤回`)
      logAction({
        action: AUDIT_ACTIONS.CANCEL_REPORT,
        target: row.reportNo,
        detail: '运营者主动撤回',
        level: 'warning'
      })
      ElMessage.success('已撤回')
    })
    .catch(() => {})
}

function resubmitReport(row) {
  const seq = String(reports.value.length + 1).padStart(3, '0')
  const newReport = {
    ...row,
    id: Date.now(),
    reportNo: `R-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}-${seq}`,
    status: 'PENDING',
    submitTime: formatTime(new Date()),
    reviewTime: '',
    reviewer: ''
  }
  reports.value.unshift(newReport)
  addLog('info', `[报备] ${newReport.reportNo} 重新提交`)
  ElMessage.success(`重新提交成功：${newReport.reportNo}`)
}

// 定时心跳
onMounted(() => {
  addLog('success', '[UTM] 系统初始化完成，已连接至 UTM 网关')
  heartbeatTimer = setInterval(() => {
    if (connectionStatus.value.class === 'connected') {
      heartbeatCount.value += 1
      lastHeartbeatTime.value = new Date()
    }
  }, 5000)
})

onBeforeUnmount(() => {
  if (heartbeatTimer) clearInterval(heartbeatTimer)
})
</script>

<style scoped>
.utm-integration-view {
  padding: 16px 20px;
  background: #f5f7fa;
  min-height: 100%;
}

.top-bar {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
  align-items: center;
  gap: 16px;
  padding: 14px 18px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  margin-bottom: 14px;
}

.top-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.mode-tag {
  margin-left: 4px;
}

.top-center {
  display: flex;
  justify-content: center;
}

.status-card {
  border: 1px solid #e4e7ed;
  border-radius: 10px;
  padding: 6px 14px;
  min-width: 480px;
}

.status-card.connected { border-color: #95d475; background: #f6ffed; }
.status-card.disconnected { border-color: #f0a0a0; background: #fff1f0; }
.status-card.pending { border-color: #e6c47a; background: #fdf6ec; }

.status-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-icon { color: #52c41a; }
.status-card.disconnected .status-icon { color: #f56c6c; }
.status-card.pending .status-icon { color: #e6a23c; }

.status-label {
  font-size: 12px;
  color: #6b7280;
}

.status-value {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.status-meta {
  display: flex;
  gap: 20px;
  margin-top: 4px;
  font-size: 12px;
  color: #4b5563;
}

.status-meta b {
  color: #1f2937;
  font-weight: 500;
}

.top-right {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.main-grid {
  display: grid;
  grid-template-columns: 40% 30% 30%;
  gap: 14px;
}

.col-panel {
  border-radius: 10px;
}

.panel-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #1f2937;
}

.panel-head .el-tag { margin-left: auto; font-weight: 400; }

.pending-badge { margin-left: 4px; }

.report-form :deep(.el-form-item) { margin-bottom: 14px; }

.form-actions-small {
  margin-top: -6px;
  margin-bottom: 8px;
  text-align: right;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 4px;
}

.list-toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.search-input {
  flex: 1;
}

.monitor-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 8px;
}

.monitor-block {
  padding: 10px;
  background: #f7f9fc;
  border-radius: 8px;
  text-align: center;
}

.mon-label {
  font-size: 12px;
  color: #6b7280;
}

.mon-value {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  margin-top: 4px;
}

.mon-value.small { font-size: 13px; font-weight: 500; color: #4b5563; }
.mon-value.danger { color: #f56c6c; }

.log-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.log-container {
  max-height: 380px;
  overflow-y: auto;
  background: #0f172a;
  border-radius: 8px;
  padding: 10px;
  font-family: Menlo, Consolas, monospace;
  font-size: 12px;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  border-bottom: 1px dashed #1e293b;
  color: #cbd5e1;
}

.log-item:last-child { border-bottom: none; }

.log-time {
  color: #94a3b8;
  flex-shrink: 0;
}

.log-level-tag { flex-shrink: 0; }

.log-content {
  flex: 1;
  word-break: break-all;
  color: #e2e8f0;
}

.log-success .log-content { color: #86efac; }
.log-error .log-content { color: #fca5a5; }
.log-warning .log-content { color: #fcd34d; }

@media (max-width: 1400px) {
  .top-bar { grid-template-columns: 1fr; gap: 10px; }
  .top-center, .top-right { justify-content: flex-start; }
  .status-card { min-width: auto; width: 100%; }
  .main-grid { grid-template-columns: 1fr; }
}
</style>
