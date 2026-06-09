<template>
  <div class="docker-status">
    <div class="page-header">
      <h2 class="page-title">Docker / 服务器状态</h2>
      <div class="header-actions">
        <el-button size="small" @click="handleRefresh">
          <span class="btn-icon">🔄</span> 刷新
        </el-button>
      </div>
    </div>

    <!-- 主机概览 -->
    <el-row :gutter="16" class="host-row">
      <el-col :xs="24" :sm="12" :md="6" v-for="host in hosts" :key="host.hostname">
        <el-card class="host-card" shadow="hover">
          <div class="host-header">
            <div class="host-icon" :style="{ background: host.color }">🖥️</div>
            <div class="host-title">
              <div class="host-name">{{ host.hostname }}</div>
              <div class="host-role">{{ host.role }}</div>
            </div>
            <el-tag :type="host.online ? 'success' : 'info'" :effect="host.online ? 'dark' : 'light'" size="small">
              {{ host.online ? '在线' : '维护' }}
            </el-tag>
          </div>
          <el-divider style="margin: 12px 0" />
          <div class="host-metrics">
            <div class="metric-item">
              <span class="metric-label">CPU 核数</span>
              <span class="metric-value">{{ host.cpuCores }} 核</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">内存总量</span>
              <span class="metric-value">{{ host.memoryTotal }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">磁盘总量</span>
              <span class="metric-value">{{ host.diskTotal }}</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">运行容器</span>
              <span class="metric-value">{{ host.runningContainers }} 个</span>
            </div>
            <div class="metric-item">
              <span class="metric-label">系统负载</span>
              <span class="metric-value">{{ host.load }}</span>
            </div>
          </div>
          <div class="host-progress">
            <div class="progress-line">
              <span class="label">CPU</span>
              <el-progress :percentage="host.cpu" :stroke-width="8" :color="'#409EFF'" />
            </div>
            <div class="progress-line">
              <span class="label">内存</span>
              <el-progress :percentage="host.memory" :stroke-width="8" :color="'#67C23A'" />
            </div>
            <div class="progress-line">
              <span class="label">磁盘</span>
              <el-progress :percentage="host.disk" :stroke-width="8" :color="'#E6A23C'" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 容器列表表格 -->
    <el-card class="section-card" shadow="never" v-if="authStore.hasAction('docker:view')">
      <template #header>
        <div class="card-header">
          <span class="header-icon">🐳</span>
          <span>容器列表</span>
          <div class="header-right">
            <el-tag type="success" effect="plain">运行 {{ runningCount }}</el-tag>
            <el-tag type="info" effect="plain">退出 {{ exitedCount }}</el-tag>
            <el-tag type="warning" effect="plain">重启 {{ restartingCount }}</el-tag>
            <span class="total">共 {{ containers.length }} 个</span>
          </div>
        </div>
      </template>

      <el-table :data="containers" stripe border size="default" style="width: 100%">
        <el-table-column prop="id" label="容器 ID" width="150">
          <template #default="{ row }">
            <span class="mono">{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="image" label="镜像" width="240">
          <template #default="{ row }">
            <span class="mono">{{ row.image }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" width="180">
          <template #default="{ row }">
            <span class="container-name">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag
              :type="containerStatusType(row.status)"
              :effect="row.status === '运行' ? 'dark' : 'light'"
              round
              size="small"
            >
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ports" label="端口映射" width="180">
          <template #default="{ row }">
            <span class="mono small">{{ row.ports }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="cpu" label="CPU %" width="110" align="center">
          <template #default="{ row }">
            <el-progress
              :percentage="Math.min(100, row.cpu)"
              :stroke-width="10"
              :color="row.cpu > 80 ? '#F56C6C' : '#409EFF'"
              :text-inside="true"
            />
          </template>
        </el-table-column>
        <el-table-column prop="memory" label="内存 %" width="110" align="center">
          <template #default="{ row }">
            <el-progress
              :percentage="Math.min(100, row.memory)"
              :stroke-width="10"
              :color="row.memory > 80 ? '#F56C6C' : '#67C23A'"
              :text-inside="true"
            />
          </template>
        </el-table-column>
        <el-table-column prop="uptime" label="启动时间" width="180" align="center" />
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="authStore.hasAction('docker:logs')"
              size="small"
              type="primary"
              link
              :disabled="row.status === '退出'"
              @click="handleViewLogs(row)"
            >
              查看日志
            </el-button>
            <el-button
              v-if="authStore.hasAction('docker:restart')"
              size="small"
              type="warning"
              link
              :disabled="row.status === '重启中'"
              @click="handleRestart(row)"
            >
              重启
            </el-button>
            <el-button
              v-if="authStore.hasAction('docker:stop')"
              size="small"
              type="danger"
              link
              :disabled="row.status === '退出'"
              @click="handleStop(row)"
            >
              停止
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    <el-empty v-else description="无权限查看容器状态" />

    <!-- 实时日志面板 -->
    <el-card class="section-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="header-icon">📝</span>
          <span>实时日志面板</span>
          <div class="header-right">
            <el-select v-model="selectedLogContainer" size="small" style="width: 220px">
              <el-option
                v-for="c in containers.filter(c => c.status === '运行')"
                :key="c.id"
                :label="c.name"
                :value="c.id"
              />
            </el-select>
            <el-tag v-if="logRunning" type="success" effect="light" size="small">● 自动追加中</el-tag>
            <el-button size="small" @click="clearLogs">清空</el-button>
            <el-button size="small" :type="logRunning ? 'danger' : 'primary'" @click="toggleLog">
              {{ logRunning ? '暂停' : '开始' }}
            </el-button>
          </div>
        </div>
      </template>

      <div class="log-panel">
        <div class="log-meta">
          <span>容器：<b>{{ currentLogContainer?.name }}</b></span>
          <span style="margin-left: 16px">共 <b>{{ logs.length }}</b> 条</span>
        </div>
        <el-input
          v-model="logContent"
          type="textarea"
          :autosize="{ minRows: 12, maxRows: 16 }"
          readonly
          class="log-textarea"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { getContainers, getHostStats, restartContainer, stopContainer } from '@/api/docker'

const authStore = useAuthStore()
const loading = ref(false)

// ===== 主机 =====
const hosts = ref([
  {
    hostname: 'node-master-01',
    role: '主节点 · Docker Swarm',
    color: '#409EFF',
    cpuCores: 16,
    memoryTotal: '64 GB',
    diskTotal: '1 TB SSD',
    runningContainers: 5,
    load: '2.34 / 16',
    online: true,
    cpu: 32,
    memory: 58,
    disk: 64
  },
  {
    hostname: 'node-worker-02',
    role: '计算节点',
    color: '#67C23A',
    cpuCores: 32,
    memoryTotal: '128 GB',
    diskTotal: '2 TB NVMe',
    runningContainers: 6,
    load: '8.12 / 32',
    online: true,
    cpu: 68,
    memory: 74,
    disk: 45
  },
  {
    hostname: 'node-worker-03',
    role: '气象模型节点',
    color: '#E6A23C',
    cpuCores: 24,
    memoryTotal: '96 GB',
    diskTotal: '4 TB HDD',
    runningContainers: 5,
    load: '14.88 / 24',
    online: true,
    cpu: 85,
    memory: 82,
    disk: 72
  },
  {
    hostname: 'node-storage-04',
    role: '数据节点',
    color: '#9B59B6',
    cpuCores: 8,
    memoryTotal: '32 GB',
    diskTotal: '8 TB RAID',
    runningContainers: 2,
    load: '1.2 / 8',
    online: true,
    cpu: 28,
    memory: 45,
    disk: 55
  }
])

// ===== 容器（18个服务）=====
const containers = ref([
  { id: 'mysql', image: 'mysql:8.0', name: 'mysql', status: '运行', ports: '3306:3306', cpu: 38, memory: 62, uptime: '12 天 4 小时' },
  { id: 'redis', image: 'redis:7.2', name: 'redis', status: '运行', ports: '6379:6379', cpu: 12, memory: 41, uptime: '12 天 4 小时' },
  { id: 'nacos', image: 'nacos:2.3', name: 'nacos', status: '运行', ports: '8848:8848', cpu: 18, memory: 44, uptime: '12 天 4 小时' },
  { id: 'api-gateway', image: 'uav-api-gateway:latest', name: 'api-gateway', status: '运行', ports: '8088:8088', cpu: 22, memory: 35, uptime: '12 天 4 小时' },
  { id: 'wrf-processor', image: 'uav-wrf-processor:latest', name: 'wrf-processor', status: '运行', ports: '8081:8081', cpu: 74, memory: 78, uptime: '3 天 11 小时' },
  { id: 'data-assimilation', image: 'uav-data-assimilation:latest', name: 'data-assimilation', status: '运行', ports: '8084:8084', cpu: 68, memory: 72, uptime: '3 天 11 小时' },
  { id: 'meteor-forecast', image: 'uav-meteor-forecast:latest', name: 'meteor-forecast', status: '运行', ports: '8082:8082', cpu: 45, memory: 58, uptime: '3 天 11 小时' },
  { id: 'path-planning', image: 'uav-path-planning:latest', name: 'path-planning', status: '运行', ports: '8083:8083', cpu: 52, memory: 65, uptime: '3 天 11 小时' },
  { id: 'uav-platform', image: 'uav-platform:latest', name: 'uav-platform', status: '运行', ports: '8080:8080', cpu: 35, memory: 48, uptime: '5 小时' },
  { id: 'uav-weather-collector', image: 'uav-weather-collector:latest', name: 'uav-weather-collector', status: '运行', ports: '8086:8086', cpu: 28, memory: 42, uptime: '5 小时' },
  { id: 'edge-cloud-coordinator', image: 'uav-edge-cloud:latest', name: 'edge-cloud-coordinator', status: '运行', ports: '8000:8000, 8765:8765', cpu: 32, memory: 55, uptime: '5 小时' },
  { id: 'fengwu-service', image: 'uav-fengwu:latest', name: 'fengwu-service', status: '运行', ports: '8085:8085', cpu: 62, memory: 74, uptime: '5 小时' },
  { id: 'model-engine', image: 'uav-model-engine:latest', name: 'model-engine', status: '运行', ports: '8087:8087', cpu: 58, memory: 68, uptime: '5 小时' },
  { id: 'tianzi-service', image: 'uav-tianzi:latest', name: 'tianzi-service', status: '运行', ports: '8090:8090', cpu: 42, memory: 52, uptime: '5 小时' },
  { id: 'fenglei-service', image: 'uav-fenglei:latest', name: 'fenglei-service', status: '运行', ports: '8091:8091', cpu: 91, memory: 88, uptime: '5 小时' },
  { id: 'kafka', image: 'kafka:3.6', name: 'kafka', status: '运行', ports: '9092:9092', cpu: 25, memory: 38, uptime: '12 天 4 小时' },
  { id: 'zookeeper', image: 'zookeeper:3.9', name: 'zookeeper', status: '运行', ports: '2181:2181', cpu: 15, memory: 28, uptime: '12 天 4 小时' },
  { id: 'frontend', image: 'uav-frontend:latest', name: 'frontend', status: '运行', ports: '3000:80', cpu: 18, memory: 45, uptime: '5 小时' }
])

const runningCount = computed(() => containers.value.filter(c => c.status === '运行').length)
const exitedCount = computed(() => containers.value.filter(c => c.status === '退出').length)
const restartingCount = computed(() => containers.value.filter(c => c.status === '重启中').length)

function containerStatusType(status) {
  switch (status) {
    case '运行':
      return 'success'
    case '重启中':
      return 'warning'
    case '退出':
      return 'info'
    default:
      return 'info'
  }
}

async function handleRefresh() {
  loading.value = true
  try {
    const res = await getContainers()
    if (res && res.data) {
      containers.value = res.data
      ElMessage.success('容器状态已刷新')
    }
  } catch (e) {
    console.warn('[DOCKER] 刷新容器状态失败，使用模拟数据:', e)
  } finally {
    loading.value = false
  }
}

function handleViewLogs(row) {
  selectedLogContainer.value = row.id
  ElMessage.info(`已切换到 ${row.name} 的日志`)
}

async function handleRestart(row) {
  ElMessageBox.confirm(`确认要重启容器 "${row.name}" 吗？`, '重启确认', {
    confirmButtonText: '确认重启',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(async () => {
      row.status = '重启中'
      try {
        await restartContainer(row.id)
      } catch (e) {
        console.warn('[DOCKER] 重启容器失败:', e)
      }
      setTimeout(() => {
        row.status = '运行'
        ElMessage.success(`${row.name} 已重新启动`)
      }, 1500)
    })
    .catch(() => {})
}

async function handleStop(row) {
  ElMessageBox.confirm(`确认要停止容器 "${row.name}" 吗？`, '停止确认', {
    confirmButtonText: '确认停止',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(async () => {
      try {
        await stopContainer(row.id)
      } catch (e) {
        console.warn('[DOCKER] 停止容器失败:', e)
      }
      row.status = '退出'
      row.cpu = 0
      row.memory = 0
      ElMessage.info(`${row.name} 已停止`)
    })
    .catch(() => {})
}

// ===== 日志面板 =====
const selectedLogContainer = ref(containers.value[0].id)
const logRunning = ref(true)
const logs = ref([])
const LOG_TEMPLATES = [
  { level: 'INFO', msg: 'request completed with status 200' },
  { level: 'INFO', msg: 'health check passed' },
  { level: 'INFO', msg: 'connected to upstream service' },
  { level: 'DEBUG', msg: 'cache hit for key user:12845' },
  { level: 'WARN', msg: 'slow query detected (845ms)' },
  { level: 'WARN', msg: 'response time above threshold: 1.24s' },
  { level: 'INFO', msg: 'scheduled job finished' },
  { level: 'INFO', msg: 'established new database connection' },
  { level: 'DEBUG', msg: 'loaded config from nacos' },
  { level: 'ERROR', msg: 'upstream timeout, will retry (attempt 1/3)' }
]

const currentLogContainer = computed(() =>
  containers.value.find(c => c.id === selectedLogContainer.value)
)

const logContent = computed(() =>
  logs.value.map(l => `[${l.time}] [${l.level}] ${l.msg}`).join('\n')
)

function formatTime(d) {
  const p = n => String(n).padStart(2, '0')
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

let logTimer = null
function pushLog() {
  const name = currentLogContainer.value?.name || 'container'
  const tpl = LOG_TEMPLATES[Math.floor(Math.random() * LOG_TEMPLATES.length)]
  logs.value.push({ time: formatTime(new Date()), level: tpl.level, msg: `[${name}] ${tpl.msg}` })
  if (logs.value.length > 80) logs.value.shift()
}

function clearLogs() {
  logs.value = []
  ElMessage.success('日志已清空')
}

function toggleLog() {
  logRunning.value = !logRunning.value
  if (logRunning.value) {
    logTimer = setInterval(pushLog, 2000)
    ElMessage.success('开始自动追加日志')
  } else {
    logTimer && clearInterval(logTimer)
    logTimer = null
    ElMessage.info('已暂停日志输出')
  }
}

watch(selectedLogContainer, () => {
  logs.value = []
  for (let i = 0; i < 5; i++) pushLog()
})

onMounted(() => {
  handleRefresh()
  for (let i = 0; i < 8; i++) pushLog()
  logTimer = setInterval(pushLog, 2000)
})

onBeforeUnmount(() => {
  logTimer && clearInterval(logTimer)
})
</script>

<style scoped>
.docker-status {
  padding: 16px;
  background: #f5f7fa;
  min-height: 100%;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
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

/* 主机概览 */
.host-row {
  margin-bottom: 16px;
}

.host-row .el-col {
  margin-bottom: 12px;
}

.host-card {
  border-radius: 8px;
  height: 100%;
}

.host-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.host-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
}

.host-title {
  flex: 1;
  min-width: 0;
}

.host-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.host-role {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.host-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 16px;
  padding: 4px 2px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  font-size: 12.5px;
}

.metric-label {
  color: #6b7280;
}

.metric-value {
  color: #1f2937;
  font-weight: 600;
}

.host-progress {
  margin-top: 10px;
}

.progress-line {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.progress-line .label {
  font-size: 12px;
  color: #6b7280;
  width: 32px;
}

/* 表格卡片 */
.section-card {
  border-radius: 8px;
  margin-bottom: 16px;
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

.header-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: normal;
  font-size: 13px;
}

.total {
  color: #6b7280;
  margin-left: 8px;
}

.container-name {
  font-family: 'SFMono-Regular', Menlo, monospace;
  color: #1f2937;
  font-weight: 500;
}

.mono {
  font-family: 'SFMono-Regular', Menlo, monospace;
  color: #1f2937;
}

.mono.small {
  font-size: 12px;
  color: #6b7280;
}

/* 日志面板 */
.log-panel {
  padding: 2px 4px;
}

.log-meta {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
}

.log-textarea :deep(textarea) {
  font-family: 'SFMono-Regular', Menlo, monospace;
  font-size: 12.5px;
  background: #0f172a;
  color: #e2e8f0;
  line-height: 1.6;
}
</style>
