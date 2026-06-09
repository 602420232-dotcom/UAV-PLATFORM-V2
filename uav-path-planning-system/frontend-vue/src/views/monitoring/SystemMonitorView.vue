<template>
  <div class="system-monitor">
    <!-- 顶部栏 -->
    <div class="top-bar">
      <div class="left-group">
        <h2 class="page-title">系统监控大盘</h2>
        <el-tag type="warning" effect="dark" class="demo-tag">演示模式</el-tag>
      </div>
      <div class="right-group">
        <el-select
          v-model="envMode"
          size="default"
          style="width: 130px"
          @change="onEnvChange"
        >
          <el-option label="演示" value="demo" />
          <el-option label="开发" value="dev" />
          <el-option label="测试" value="test" />
          <el-option label="生产" value="prod" />
        </el-select>

        <el-select
          v-model="timeRange"
          size="default"
          style="width: 130px"
          @change="refreshAll"
        >
          <el-option label="近 5 分钟" value="5m" />
          <el-option label="近 1 小时" value="1h" />
          <el-option label="近 24 小时" value="24h" />
        </el-select>

        <el-switch
          v-model="autoRefresh"
          active-text="自动刷新"
          inactive-text="手动"
        />
        <el-select
          v-if="autoRefresh"
          v-model="refreshInterval"
          size="small"
          style="width: 90px; margin-left: 4px"
        >
          <el-option label="5s" :value="5000" />
          <el-option label="10s" :value="10000" />
          <el-option label="30s" :value="30000" />
        </el-select>

        <el-button type="primary" :icon="Refresh" @click="refreshAll">
          刷新
        </el-button>
      </div>
    </div>

    <!-- 上半部分：Gauge 卡片行 + 实时事件流（右侧边栏） -->
    <el-row :gutter="16" class="main-row">
      <el-col :xs="24" :lg="17">
        <el-row :gutter="16">
          <el-col :xs="12" :sm="8" v-for="g in gauges" :key="g.key">
            <el-card shadow="hover" class="gauge-card">
              <div class="gauge-title">{{ g.label }}</div>
              <div ref="el => gaugeRefs[g.key] = el" class="gauge-chart"></div>
              <div ref="el => sparkRefs[g.key] = el" class="sparkline-chart"></div>
            </el-card>
          </el-col>
        </el-row>
      </el-col>

      <!-- 右侧边栏：实时事件流 -->
      <el-col :xs="24" :lg="7">
        <el-card shadow="hover" class="events-card">
          <template #header>
            <div class="events-header">
              <span>📡 实时事件流</span>
              <el-tag size="small" type="info">最近 {{ events.length }} 条</el-tag>
            </div>
          </template>
          <div class="events-list" ref="eventsListRef">
            <div
              v-for="(ev, idx) in events"
              :key="ev.id || idx"
              class="event-item"
              :class="'event-' + ev.level"
            >
              <div class="event-meta">
                <el-tag :type="ev.levelTag" size="small" effect="dark">
                  {{ ev.levelText }}
                </el-tag>
                <span class="event-time">{{ ev.time }}</span>
              </div>
              <div class="event-source">[{{ ev.source }}]</div>
              <div class="event-content">{{ ev.content }}</div>
            </div>
            <div v-if="events.length === 0" class="events-empty">
              暂无事件
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 微服务列表表格 -->
    <el-card shadow="never" class="services-card">
      <template #header>
        <div class="card-header-row">
          <div class="card-title">🖥️ 微服务健康状态</div>
          <div class="card-filters">
            <el-input
              v-model="serviceKeyword"
              placeholder="搜索服务名称…"
              clearable
              style="width: 220px"
              :prefix-icon="Search"
            />
            <el-select
              v-model="statusFilter"
              placeholder="状态筛选"
              clearable
              style="width: 140px"
            >
              <el-option label="健康" value="healthy" />
              <el-option label="警告" value="warning" />
              <el-option label="严重" value="critical" />
              <el-option label="离线" value="offline" />
              <el-option label="重启中" value="restarting" />
            </el-select>
            <el-tag type="success" effect="plain" class="summary-tag">
              健康 {{ stats.healthy }}
            </el-tag>
            <el-tag type="warning" effect="plain" class="summary-tag">
              警告 {{ stats.warning }}
            </el-tag>
            <el-tag type="danger" effect="plain" class="summary-tag">
              严重 {{ stats.critical }}
            </el-tag>
            <el-tag type="info" effect="plain" class="summary-tag">
              离线 {{ stats.offline }}
            </el-tag>
          </div>
        </div>
      </template>

      <el-table :data="filteredServices" stripe border size="default" style="width: 100%">
        <el-table-column label="服务名称" prop="name" min-width="200" fixed>
          <template #default="{ row }">
            <span class="svc-name">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" effect="dark" size="small">
              {{ statusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="版本" prop="version" width="110" align="center" />
        <el-table-column label="实例数" prop="instances" width="90" align="center" />
        <el-table-column label="QPS" prop="qps" width="110" align="center" />
        <el-table-column label="平均延迟 (ms)" prop="latency" width="130" align="center" />
        <el-table-column label="错误率 (%)" width="120" align="center">
          <template #default="{ row }">
            <span
              :style="{
                color: row.errorRate >= 5 ? '#F56C6C' : row.errorRate >= 1 ? '#E6A23C' : '#67C23A',
                fontWeight: 600
              }"
            >
              {{ row.errorRate.toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column label="最后心跳" prop="lastHeartbeat" width="170" align="center" />
        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              link
              :loading="row.status === 'restarting'"
              :disabled="row.status === 'restarting'"
              @click="restartService(row)"
            >
              重启
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 性能曲线区 -->
    <el-row :gutter="16" class="perf-row">
      <el-col :xs="24" :md="8">
        <el-card shadow="hover" class="perf-card">
          <template #header>📈 请求数（QPS）趋势</template>
          <div ref="chartQpsRef" class="perf-chart"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="hover" class="perf-card">
          <template #header>⏱️ 平均延迟 (ms) 趋势</template>
          <div ref="chartLatencyRef" class="perf-chart"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="hover" class="perf-card">
          <template #header>⚠️ 错误率 (%) 趋势</template>
          <div ref="chartErrRef" class="perf-chart"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useAuthStore } from '../../stores/auth'
import { useAppStore } from '../../stores/app'
import { getSystemStatus, getServiceHealth } from '../../api/system'

const authStore = useAuthStore()
const appStore = useAppStore()

// 顶部栏状态
const envMode = ref(appStore.envMode || 'demo')
const timeRange = ref('5m')
const autoRefresh = ref(true)
const refreshInterval = ref(5000)

// 仪表与 sparkline 引用
const gaugeRefs = reactive({})
const sparkRefs = reactive({})
const gaugeInstances = reactive({})
const sparkInstances = reactive({})

// 图表引用
const chartQpsRef = ref(null)
const chartLatencyRef = ref(null)
const chartErrRef = ref(null)
const eventsListRef = ref(null)
let chartQps = null
let chartLatency = null
let chartErr = null

// 搜索与筛选
const serviceKeyword = ref('')
const statusFilter = ref('')

// ===== Gauge 定义 + 历史 =====
const POINTS = 60
function buildGauges() {
  return [
    { key: 'cpu', label: 'CPU 使用率', value: 42, unit: '%', max: 100, color: '#409EFF' },
    { key: 'mem', label: '内存使用率', value: 58, unit: '%', max: 100, color: '#67C23A' },
    { key: 'disk', label: '磁盘使用率', value: 35, unit: '%', max: 100, color: '#E6A23C' },
    { key: 'netIn', label: '网络入流量', value: 6.2, unit: 'MB/s', max: 20, color: '#36B5C5' },
    { key: 'netOut', label: '网络出流量', value: 4.5, unit: 'MB/s', max: 20, color: '#9B59B6' },
    { key: 'conn', label: '活跃连接', value: 1280, unit: '', max: 5000, color: '#F56C6C' }
  ]
}
const gauges = ref(buildGauges())
const gaugeHistory = reactive({
  cpu: Array.from({ length: POINTS }, () => 40 + Math.random() * 10),
  mem: Array.from({ length: POINTS }, () => 55 + Math.random() * 8),
  disk: Array.from({ length: POINTS }, () => 33 + Math.random() * 4),
  netIn: Array.from({ length: POINTS }, () => 5 + Math.random() * 3),
  netOut: Array.from({ length: POINTS }, () => 3 + Math.random() * 3),
  conn: Array.from({ length: POINTS }, () => 1200 + Math.random() * 200)
})

// ===== 微服务列表 =====
const services = ref([
  { name: 'API Gateway',       status: 'healthy',    version: 'v3.3.0', instances: 3, qps: 1520, latency: 18,  errorRate: 0.15, lastHeartbeat: '刚刚' },
  { name: 'TianZi Service',    status: 'healthy',    version: 'v1.2.0', instances: 2, qps: 420,  latency: 22,  errorRate: 0.30, lastHeartbeat: '2s 前' },
  { name: 'FengLei Service',   status: 'warning',    version: 'v1.1.3', instances: 2, qps: 310,  latency: 140, errorRate: 2.10, lastHeartbeat: '3s 前' },
  { name: 'FengWu Model',      status: 'healthy',    version: 'v2.0.1', instances: 2, qps: 180,  latency: 85,  errorRate: 0.50, lastHeartbeat: '1s 前' },
  { name: 'Model Engine',      status: 'healthy',    version: 'v2.1.0', instances: 2, qps: 260,  latency: 62,  errorRate: 0.40, lastHeartbeat: '1s 前' },
  { name: 'WRF Processor',     status: 'critical',   version: 'v1.8.0', instances: 1, qps: 12,   latency: 820, errorRate: 8.50, lastHeartbeat: '6s 前' },
  { name: 'Edge Cloud Coordinator', status: 'warning', version: 'v2.1.0', instances: 3, qps: 680, latency: 35, errorRate: 1.80, lastHeartbeat: '4s 前' },
  { name: 'Database',          status: 'offline',    version: 'MySQL 8.0', instances: 0, qps: 0, latency: 0,  errorRate: 100, lastHeartbeat: '3m 前' }
])

function statusTag(s) {
  switch (s) {
    case 'healthy': return 'success'
    case 'warning': return 'warning'
    case 'critical': return 'danger'
    case 'offline': return 'info'
    case 'restarting': return 'primary'
    default: return 'info'
  }
}
function statusText(s) {
  switch (s) {
    case 'healthy': return '健康'
    case 'warning': return '警告'
    case 'critical': return '严重'
    case 'offline': return '离线'
    case 'restarting': return '重启中'
    default: return s
  }
}

const filteredServices = computed(() => {
  const kw = serviceKeyword.value.trim().toLowerCase()
  return services.value.filter(s => {
    if (kw && !s.name.toLowerCase().includes(kw)) return false
    if (statusFilter.value && s.status !== statusFilter.value) return false
    return true
  })
})

const stats = computed(() => {
  const out = { healthy: 0, warning: 0, critical: 0, offline: 0, restarting: 0 }
  services.value.forEach(s => {
    if (out[s.status] !== undefined) out[s.status]++
  })
  return out
})

function restartService(row) {
  ElMessageBox.confirm(`确认要重启服务 "${row.name}" 吗？`, '重启确认', {
    confirmButtonText: '确认重启',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(() => {
      const prevStatus = row.status
      row.status = 'restarting'
      row.lastHeartbeat = '重启中…'
      pushEvent('info', row.name, `收到重启指令，正在重启服务…`)
      setTimeout(() => {
        row.status = (prevStatus === 'offline' || prevStatus === 'critical') ? 'warning' : 'healthy'
        row.lastHeartbeat = '刚刚'
        row.instances = Math.max(1, row.instances)
        row.qps = Math.max(10, Math.round(row.qps * 0.9 + Math.random() * 100))
        row.latency = Math.max(5, Math.round(row.latency * 0.9 + Math.random() * 20))
        row.errorRate = Math.max(0.05, row.errorRate * 0.6)
        pushEvent('info', row.name, `服务已成功重启并恢复健康`)
        ElMessage.success(`${row.name} 已成功重启`)
      }, 1500)
    })
    .catch(() => {})
}

// ===== 事件流 =====
let eventIdSeq = 1
const events = ref([])
function pushEvent(level, source, content) {
  const now = new Date()
  const time = now.toLocaleTimeString('zh-CN', { hour12: false })
  const map = {
    info: { levelTag: 'info', levelText: 'INFO' },
    warn: { levelTag: 'warning', levelText: 'WARN' },
    error: { levelTag: 'danger', levelText: 'ERROR' }
  }
  const m = map[level] || map.info
  events.value.unshift({
    id: eventIdSeq++,
    level,
    levelText: m.levelText,
    levelTag: m.levelTag,
    source,
    content,
    time
  })
  if (events.value.length > 30) events.value.length = 30
}

const sampleEvents = [
  { level: 'info',  source: 'API Gateway', content: '配置热更新成功（版本 v3.3.0-2）' },
  { level: 'info',  source: 'Model Engine', content: '模型权重预热完成，推理缓存 100% 命中' },
  { level: 'warn',  source: 'FengLei Service', content: 'CPU 高峰，当前使用率 82%，建议扩容' },
  { level: 'error', source: 'WRF Processor', content: '数值预报任务超时（> 60s），已熔断降级' },
  { level: 'warn',  source: 'Database', content: '数据库连接池告警：活跃连接接近上限 85/100' },
  { level: 'error', source: 'Database', content: '主从同步延迟超过 30s，写操作被限流' },
  { level: 'info',  source: 'TianZi Service', content: '新增 1 个实例，当前 3 个实例健康' },
  { level: 'warn',  source: 'Edge Cloud Coordinator', content: '边缘节点 edge-node-07 延迟 > 200ms' },
  { level: 'info',  source: 'FengWu Model', content: '批次推理任务完成，平均延迟 65ms' },
  { level: 'error', source: 'WRF Processor', content: '气象源数据 GFS 拉取失败，重试中（2/3）' }
]
function tickEvents() {
  const count = 1 + Math.floor(Math.random() * 2)
  for (let i = 0; i < count; i++) {
    const ev = sampleEvents[Math.floor(Math.random() * sampleEvents.length)]
    pushEvent(ev.level, ev.source, ev.content)
  }
}

// ===== 刷新逻辑 =====
const isDemoMode = computed(() => envMode.value === 'demo')

function tickMetrics() {
  gauges.value.forEach(g => {
    let delta
    if (g.unit === '%') {
      delta = (Math.random() - 0.5) * 8
      g.value = Math.max(3, Math.min(98, +(g.value + delta).toFixed(0)))
    } else if (g.unit === 'MB/s') {
      delta = (Math.random() - 0.5) * 2
      g.value = Math.max(0.1, +(g.value + delta).toFixed(1))
    } else {
      delta = (Math.random() - 0.5) * 150
      g.value = Math.max(10, Math.round(g.value + delta))
    }
    gaugeHistory[g.key].push(g.value)
    if (gaugeHistory[g.key].length > POINTS) gaugeHistory[g.key].shift()
  })

  // 微服务抖动
  services.value.forEach(s => {
    if (s.status === 'restarting' || s.status === 'offline') return
    s.qps = Math.max(5, Math.round(s.qps * (0.92 + Math.random() * 0.18)))
    s.latency = Math.max(5, Math.round(s.latency * (0.9 + Math.random() * 0.25)))
    const errDelta = (Math.random() - 0.5) * 0.6
    s.errorRate = Math.max(0.01, +(s.errorRate + errDelta).toFixed(2))
    const hb = Math.floor(Math.random() * 8) + 1
    s.lastHeartbeat = hb <= 1 ? '刚刚' : `${hb}s 前`
  })
}

async function fetchSystemStatus() {
  if (isDemoMode.value) return
  try {
    const res = await getSystemStatus()
    if (res && res.data) {
      const data = res.data
      if (data.metrics) {
        gauges.value.forEach(g => {
          if (data.metrics[g.key] !== undefined) {
            g.value = +data.metrics[g.key].toFixed(g.unit === '%' ? 0 : 1)
            gaugeHistory[g.key].push(g.value)
            if (gaugeHistory[g.key].length > POINTS) gaugeHistory[g.key].shift()
          }
        })
      }
      if (data.services) {
        services.value = data.services.map(s => ({
          name: s.name,
          status: s.status || 'healthy',
          version: s.version || 'unknown',
          instances: s.instances || 1,
          qps: s.qps || 0,
          latency: s.latency || 0,
          errorRate: s.errorRate || 0,
          lastHeartbeat: s.lastHeartbeat || '刚刚'
        }))
      }
    }
  } catch (e) {
    console.warn('[SYSTEM] 获取系统状态失败，使用模拟数据:', e)
  }
}

async function refreshAll() {
  if (isDemoMode.value) {
    tickMetrics()
  } else {
    await fetchSystemStatus()
  }
  pushEvent('info', 'SystemMonitor', `手动刷新 - 环境：${envText(envMode.value)} · 时间范围：${timeRange.value}`)
  renderAll()
  ElMessage.success('监控数据已刷新')
}

function envText(e) {
  return ({ demo: '演示', dev: '开发', test: '测试', prod: '生产' })[e] || e
}

function onEnvChange(val) {
  appStore.setEnvMode(val)
  pushEvent('info', 'SystemMonitor', `环境已切换为 ${envText(val)}`)
  renderAll()
}

// ===== ECharts 渲染 =====
function renderGauge(g) {
  const dom = gaugeRefs[g.key]
  if (!dom) return
  if (!gaugeInstances[g.key]) {
    gaugeInstances[g.key] = echarts.init(dom)
  }
  const chart = gaugeInstances[g.key]
  chart.setOption({
    series: [
      {
        type: 'gauge',
        startAngle: 210,
        endAngle: -30,
        min: 0,
        max: g.max,
        radius: '95%',
        center: ['50%', '60%'],
        progress: { show: true, width: 10, itemStyle: { color: g.color } },
        axisLine: { lineStyle: { width: 10, color: [[1, '#f0f2f5']] } },
        axisTick: { show: false },
        splitLine: { length: 8, lineStyle: { color: '#dcdfe6', width: 1 } },
        axisLabel: { distance: 12, color: '#909399', fontSize: 10 },
        pointer: { show: false },
        anchor: { show: false },
        title: { show: false },
        detail: {
          valueAnimation: true,
          fontSize: 22,
          fontWeight: 700,
          color: g.color,
          offsetCenter: [0, '5%'],
          formatter: v => `${v}${g.unit}`
        },
        data: [{ value: g.value }]
      }
    ]
  })
}

function renderSpark(g) {
  const dom = sparkRefs[g.key]
  if (!dom) return
  if (!sparkInstances[g.key]) {
    sparkInstances[g.key] = echarts.init(dom)
  }
  const chart = sparkInstances[g.key]
  const data = gaugeHistory[g.key] || []
  chart.setOption({
    grid: { left: 2, right: 2, top: 4, bottom: 2 },
    xAxis: { type: 'category', show: false, data: data.map((_, i) => i) },
    yAxis: { type: 'value', show: false },
    tooltip: { trigger: 'axis' },
    series: [{
      type: 'line',
      smooth: true,
      symbol: 'none',
      data,
      lineStyle: { color: g.color, width: 2 },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: g.color + '66' },
            { offset: 1, color: g.color + '00' }
          ]
        }
      }
    }]
  })
}

// 性能曲线数据
const perfTimeLabels = Array.from({ length: POINTS }, (_, i) => `${POINTS - i}s`)
const perfQps = ref(Array.from({ length: POINTS }, () => 800 + Math.random() * 800))
const perfLatency = ref(Array.from({ length: POINTS }, () => 30 + Math.random() * 40))
const perfErr = ref(Array.from({ length: POINTS }, () => 0.3 + Math.random() * 0.8))

function renderPerfChart(ref, data, color, unit) {
  if (!ref) return null
  let chart = echarts.getInstanceByDom(ref) || echarts.init(ref)
  chart.setOption({
    grid: { left: 40, right: 16, top: 16, bottom: 30 },
    xAxis: {
      type: 'category',
      data: perfTimeLabels,
      axisLabel: { color: '#909399', fontSize: 10, interval: Math.floor(POINTS / 6) },
      axisLine: { lineStyle: { color: '#dcdfe6' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#909399', fontSize: 10, formatter: `{value} ${unit}` },
      splitLine: { lineStyle: { color: '#f0f2f5' } }
    },
    tooltip: { trigger: 'axis' },
    series: [{
      type: 'line',
      smooth: true,
      data,
      symbol: 'circle',
      symbolSize: 4,
      lineStyle: { color, width: 2 },
      itemStyle: { color },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: color + '55' },
            { offset: 1, color: color + '00' }
          ]
        }
      }
    }]
  })
  return chart
}

function renderAll() {
  gauges.value.forEach(g => {
    renderGauge(g)
    renderSpark(g)
  })
  if (chartQpsRef.value) chartQps = renderPerfChart(chartQpsRef.value, perfQps.value, '#409EFF', 'req/s')
  if (chartLatencyRef.value) chartLatency = renderPerfChart(chartLatencyRef.value, perfLatency.value, '#67C23A', 'ms')
  if (chartErrRef.value) chartErr = renderPerfChart(chartErrRef.value, perfErr.value, '#F56C6C', '%')
}

// ===== 定时器 =====
let autoTimer = null
let eventTimer = null
let perfTimer = null
async function autoRefreshData() {
  if (!autoRefresh.value) return
  if (isDemoMode.value) {
    tickMetrics()
  } else {
    await fetchSystemStatus()
  }
  renderAll()
}
function startTimers() {
  stopTimers()
  autoTimer = setInterval(autoRefreshData, refreshInterval.value)

  eventTimer = setInterval(() => {
    if (!autoRefresh.value) return
    tickEvents()
  }, 5000)

  perfTimer = setInterval(() => {
    if (!autoRefresh.value) return
    // 滚动性能曲线
    perfQps.value.shift()
    perfQps.value.push(Math.max(100, Math.round(perfQps.value[perfQps.value.length - 1] * (0.9 + Math.random() * 0.2))))
    perfLatency.value.shift()
    perfLatency.value.push(Math.max(5, +(perfLatency.value[perfLatency.value.length - 1] * (0.9 + Math.random() * 0.25)).toFixed(1)))
    perfErr.value.shift()
    perfErr.value.push(Math.max(0.01, +(perfErr.value[perfErr.value.length - 1] + (Math.random() - 0.5) * 0.4).toFixed(2)))
    renderAll()
  }, refreshInterval.value)
}

function stopTimers() {
  if (autoTimer) clearInterval(autoTimer)
  if (eventTimer) clearInterval(eventTimer)
  if (perfTimer) clearInterval(perfTimer)
  autoTimer = eventTimer = perfTimer = null
}

watch(refreshInterval, () => { startTimers() })
watch(autoRefresh, () => { startTimers() })

function onResize() {
  Object.values(gaugeInstances).forEach(c => c && c.resize())
  Object.values(sparkInstances).forEach(c => c && c.resize())
  chartQps && chartQps.resize()
  chartLatency && chartLatency.resize()
  chartErr && chartErr.resize()
}

onMounted(async () => {
  // 初始事件
  pushEvent('info', 'SystemMonitor', `监控大盘已启动，环境：${envText(envMode.value)}`)
  pushEvent('info', 'SystemMonitor', `当前角色：${authStore.roleLabel}（权限验证通过）`)
  await nextTick()
  renderAll()
  startTimers()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  stopTimers()
  window.removeEventListener('resize', onResize)
  Object.values(gaugeInstances).forEach(c => c && c.dispose())
  Object.values(sparkInstances).forEach(c => c && c.dispose())
  chartQps && chartQps.dispose()
  chartLatency && chartLatency.dispose()
  chartErr && chartErr.dispose()
})
</script>

<style scoped>
.system-monitor {
  padding: 16px 20px 24px;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.left-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  padding-left: 10px;
  border-left: 4px solid #409EFF;
}

.demo-tag {
  font-weight: 500;
}

.right-group {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.main-row {
  margin-bottom: 16px;
}

.gauge-card {
  margin-bottom: 16px;
  border-radius: 10px;
}

.gauge-title {
  font-size: 13px;
  color: #606266;
  font-weight: 600;
  text-align: center;
  margin-bottom: 4px;
}

.gauge-chart {
  height: 140px;
}

.sparkline-chart {
  height: 60px;
  margin-top: 4px;
}

.events-card {
  border-radius: 10px;
  height: 100%;
}

.events-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #1f2937;
}

.events-list {
  max-height: 520px;
  overflow-y: auto;
  padding-right: 4px;
}

.event-item {
  padding: 8px 10px;
  margin-bottom: 8px;
  border-left: 3px solid #909399;
  background: #fafafa;
  border-radius: 4px;
  font-size: 12.5px;
  line-height: 1.5;
}

.event-item.event-info { border-left-color: #409EFF; background: #ecf5ff; }
.event-item.event-warn { border-left-color: #E6A23C; background: #fdf6ec; }
.event-item.event-error { border-left-color: #F56C6C; background: #fef0f0; }

.event-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 3px;
}

.event-time {
  font-size: 11.5px;
  color: #909399;
}

.event-source {
  color: #409EFF;
  font-weight: 600;
  display: inline;
  margin-right: 4px;
}

.event-content {
  color: #606266;
  display: inline;
}

.events-empty {
  padding: 30px 0;
  text-align: center;
  color: #c0c4cc;
  font-size: 13px;
}

.services-card {
  border-radius: 10px;
  margin-bottom: 16px;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.card-filters {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.summary-tag {
  font-weight: 500;
}

.svc-name {
  font-weight: 600;
  color: #1f2937;
}

.perf-row {
  margin-bottom: 16px;
}

.perf-card {
  border-radius: 10px;
  height: 100%;
}

.perf-chart {
  height: 240px;
}
</style>
