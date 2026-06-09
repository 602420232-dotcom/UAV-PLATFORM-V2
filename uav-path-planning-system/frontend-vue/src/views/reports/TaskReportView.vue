<template>
  <div class="task-report">
    <!-- 顶部栏 -->
    <div class="top-bar">
      <div class="title-block">
        <h2 class="page-title">任务报告中心</h2>
        <el-tag type="warning" effect="dark" class="demo-tag">演示模式</el-tag>
        <DataScopeBadge :scope="activeScope" :team="authStore.team" class="scope-badge" />
      </div>
      <div class="actions">
        <el-select v-model="dataScopeFilter" placeholder="数据范围" size="default" style="width: 180px" clearable>
          <el-option label="跟随账号" value="" />
          <el-option label="仅个人" value="personal" />
          <el-option label="仅团队" value="team" />
          <el-option label="全部数据" value="all" />
        </el-select>
        <el-select v-model="reportType" size="default" style="width: 160px">
          <el-option label="任务清单" value="task-list" />
          <el-option label="气象评估" value="weather" />
          <el-option label="路径规划摘要" value="path-summary" />
        </el-select>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="起始日期"
          end-placeholder="结束日期"
          size="default"
          value-format="YYYY-MM-DD"
          style="width: 280px"
        />
        <el-button type="primary" :icon="RefreshRight" @click="generateReport">
          生成
        </el-button>
        <el-dropdown trigger="click" @command="handleExport">
          <el-button :icon="Download">
            导出 <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="csv">📄 CSV 明细表</el-dropdown-item>
              <el-dropdown-item command="pdf">🖨️ PDF（打印对话框）</el-dropdown-item>
              <el-dropdown-item command="xlsx">📊 XLSX / Excel</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 主体：左筛选 + 右预览 -->
    <el-row :gutter="16" class="main-row">
      <!-- 左栏：筛选 -->
      <el-col :xs="24" :md="5">
        <el-card shadow="never" class="filter-card">
          <template #header>
            <div class="card-header"><span>🎛️ 筛选条件 · {{ dataScopeSummary }}</span></div>
          </template>
          <el-form label-width="90px" size="default">
            <el-form-item label="报告类型">
              <el-select v-model="reportType" style="width: 100%">
                <el-option label="任务清单" value="task-list" />
                <el-option label="气象评估" value="weather" />
                <el-option label="路径规划摘要" value="path-summary" />
              </el-select>
            </el-form-item>
            <el-form-item label="数据范围">
              <el-select v-model="dataScopeFilter" placeholder="跟随账号" clearable style="width: 100%">
                <el-option label="跟随账号" value="" />
                <el-option label="仅个人" value="personal" />
                <el-option label="仅团队" value="team" />
                <el-option label="全部数据" value="all" />
              </el-select>
            </el-form-item>
            <el-form-item label="时间范围">
              <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="起始"
                end-placeholder="结束"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="任务状态">
              <el-select
                v-model="statusFilter"
                multiple
                collapse-tags
                collapse-tags-tooltip
                placeholder="全部"
                style="width: 100%"
              >
                <el-option label="进行中" value="running" />
                <el-option label="已完成" value="done" />
                <el-option label="失败" value="failed" />
                <el-option label="已取消" value="canceled" />
                <el-option label="排队中" value="pending" />
              </el-select>
            </el-form-item>
            <el-form-item label="角色">
              <el-select v-model="roleFilter" placeholder="全部" clearable style="width: 100%">
                <el-option label="生产人员" value="production" />
                <el-option label="飞控人员" value="flight" />
                <el-option label="测试人员" value="tester" />
                <el-option label="管理员" value="admin" />
              </el-select>
            </el-form-item>
            <el-form-item label="包含图表">
              <el-switch v-model="includeCharts" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :icon="RefreshRight" @click="generateReport" style="width: 100%">
                重新生成
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右栏：预览 -->
      <el-col :xs="24" :md="19">
        <div class="print-area">
          <div class="print-header no-print-keep">
            <h3 class="report-title">
              无人机任务报告 - {{ reportTypeText }}
            </h3>
            <div class="report-meta">
              <span>生成时间：{{ generatedAt }}</span>
              <span>时间范围：{{ dateRangeText }}</span>
              <span>共 {{ filteredTasks.length }} 条记录</span>
            </div>
          </div>

          <!-- 摘要卡片 -->
          <el-row :gutter="12" class="summary-row">
            <el-col :xs="12" :sm="8">
              <div class="summary-card total">
                <div class="summary-label">任务总数</div>
                <div class="summary-value">{{ summary.total }}</div>
              </div>
            </el-col>
            <el-col :xs="12" :sm="8">
              <div class="summary-card done">
                <div class="summary-label">完成数</div>
                <div class="summary-value">{{ summary.done }}</div>
              </div>
            </el-col>
            <el-col :xs="12" :sm="8">
              <div class="summary-card failed">
                <div class="summary-label">失败数</div>
                <div class="summary-value">{{ summary.failed }}</div>
              </div>
            </el-col>
            <el-col :xs="12" :sm="8">
              <div class="summary-card running">
                <div class="summary-label">进行中</div>
                <div class="summary-value">{{ summary.running }}</div>
              </div>
            </el-col>
            <el-col :xs="12" :sm="8">
              <div class="summary-card avg-time">
                <div class="summary-label">平均飞行 (min)</div>
                <div class="summary-value">{{ summary.avgFlight }}</div>
              </div>
            </el-col>
            <el-col :xs="12" :sm="8">
              <div class="summary-card mileage">
                <div class="summary-label">总里程 (km)</div>
                <div class="summary-value">{{ summary.totalMileage }}</div>
              </div>
            </el-col>
          </el-row>

          <!-- 图表 -->
          <el-card v-if="includeCharts" shadow="never" class="chart-card">
            <template #header>📈 按日期任务完成量 & 成功率</template>
            <div ref="chartRef" class="report-chart"></div>
          </el-card>

          <!-- 明细表 -->
          <el-card shadow="never" class="table-card">
            <template #header>
              <div class="card-header">
                <span>🧾 任务明细 (前 {{ Math.min(filteredTasks.length, 50) }} 行)</span>
                <el-tag type="info" effect="plain" size="small">共 {{ filteredTasks.length }} 条</el-tag>
              </div>
            </template>
            <el-table :data="pagedTasks" stripe border size="small" style="width: 100%">
              <el-table-column label="任务编号" prop="code" width="160" fixed />
              <el-table-column label="类型" prop="type" width="120" />
              <el-table-column label="状态" width="100" align="center">
                <template #default="{ row }">
                  <el-tag :type="statusTag(row.status)" size="small" effect="light">
                    {{ statusText(row.status) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="起点" prop="from" min-width="140" show-overflow-tooltip />
              <el-table-column label="终点" prop="to" min-width="140" show-overflow-tooltip />
              <el-table-column label="里程 (km)" prop="mileage" width="110" align="right" />
              <el-table-column label="飞行时间 (min)" prop="flightMin" width="130" align="right" />
              <el-table-column label="提交时间" prop="createdAt" width="180" />
              <el-table-column label="负责人" width="160">
        <template #default="{ row }">
          <div class="owner-cell">
            <span>{{ row.owner }}</span>
            <el-tag size="small" type="info" effect="plain">{{ teamDisplay(row.team) }}</el-tag>
          </div>
        </template>
      </el-table-column>
    </el-table>
            <el-pagination
              v-if="filteredTasks.length > pageSize"
              v-model:current-page="page"
              :page-size="pageSize"
              :total="filteredTasks.length"
              layout="total, prev, pager, next"
              background
              style="justify-content: flex-end; padding-top: 12px"
            />
          </el-card>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { RefreshRight, Download, ArrowDown } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useAuthStore, TEAM_LABELS } from '../../stores/auth'
import DataScopeBadge from '../../components/shared/DataScopeBadge.vue'

const authStore = useAuthStore()

// 顶部选项
const reportType = ref('task-list')
const dateRange = ref([
  new Date(Date.now() - 6 * 24 * 3600 * 1000).toISOString().slice(0, 10),
  new Date().toISOString().slice(0, 10)
])
const statusFilter = ref(['running', 'done', 'failed', 'pending', 'canceled'])
const roleFilter = ref('')
const includeCharts = ref(true)
const page = ref(1)
const pageSize = 20

// 数据范围
const dataScopeFilter = ref('')
const activeScope = computed(() => dataScopeFilter.value || authStore.dataScope || 'personal')

function teamDisplay(team) {
  return TEAM_LABELS[team] || team || '-'
}

const dataScopeSummary = computed(() => {
  const scope = activeScope.value
  if (scope === 'all') return '全部数据汇总'
  if (scope === 'team') return `团队 ${teamDisplay(authStore.team)} 汇总`
  return '个人任务汇总'
})

const reportTypeText = computed(() => ({
  'task-list': '任务清单',
  'weather': '气象评估',
  'path-summary': '路径规划摘要'
}[reportType.value] || '任务清单'))

const dateRangeText = computed(() => {
  if (!dateRange.value || dateRange.value.length !== 2) return '未选择'
  return `${dateRange.value[0]} ~ ${dateRange.value[1]}`
})

const generatedAt = ref(new Date().toLocaleString('zh-CN', { hour12: false }))

// ===== Mock 数据生成 =====
const TYPES = ['短途运输', '中程配送', '长途货运', '应急物资', '医疗配送', '农业植保']
const STATUS_POOL = ['running', 'done', 'done', 'done', 'failed', 'pending', 'canceled']
const OWNER_RECORDS = [
  { owner: '张工程师', ownerId: 'user01', team: 'team-a' },
  { owner: '李飞控', ownerId: 'flight01', team: 'team-b' },
  { owner: '王操作', ownerId: 'prod01', team: 'team-a' },
  { owner: '赵生产', ownerId: 'test01', team: 'team-c' },
  { owner: '孙调度', ownerId: 'deploy01', team: 'team-c' },
  { owner: '周主管', ownerId: 'admin01', team: 'team-a' }
]
const CITY_PAIRS = [
  ['北京-中关村仓', '天津-滨海分中心'],
  ['上海-虹桥仓', '苏州-工业园分中心'],
  ['深圳-前海仓', '广州-白云分中心'],
  ['成都-天府仓', '重庆-两江分中心'],
  ['杭州-萧山仓', '宁波-北仑分中心'],
  ['武汉-光谷仓', '长沙-岳麓分中心'],
  ['西安-高新仓', '郑州-航空港分中心'],
  ['南京-江宁仓', '合肥-经开分中心'],
  ['青岛-黄岛仓', '济南-历城分中心'],
  ['厦门-湖里仓', '福州-马尾分中心']
]

function buildMockTasks(n = 35) {
  const list = []
  const now = Date.now()
  for (let i = 0; i < n; i++) {
    const ts = now - Math.floor(Math.random() * 7 * 24 * 3600 * 1000)
    const pair = CITY_PAIRS[i % CITY_PAIRS.length]
    const mileage = +(3 + Math.random() * 80).toFixed(2)
    const flight = +(mileage * (0.8 + Math.random() * 0.6)).toFixed(1)
    const status = STATUS_POOL[Math.floor(Math.random() * STATUS_POOL.length)]
    const ownerRecord = OWNER_RECORDS[i % OWNER_RECORDS.length]
    list.push({
      code: 'TASK-' + (10000 + i),
      type: TYPES[i % TYPES.length],
      status,
      from: pair[0],
      to: pair[1],
      mileage,
      flightMin: flight,
      createdAt: new Date(ts).toLocaleString('zh-CN', { hour12: false }),
      _ts: ts,
      owner: ownerRecord.owner,
      ownerId: ownerRecord.ownerId,
      team: ownerRecord.team
    })
  }
  return list.sort((a, b) => b._ts - a._ts)
}

const allTasks = ref(buildMockTasks(35))

// 数据范围过滤
function _canSee(ownerId, team) {
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

// 过滤后的结果（基于日期 + 状态 + 角色 + 数据范围）
const filteredTasks = computed(() => {
  const [start, end] = dateRange.value || [null, null]
  return allTasks.value.filter(t => {
    if (!_canSee(t.ownerId, t.team)) return false
    if (start || end) {
      const day = new Date(t._ts).toISOString().slice(0, 10)
      if (start && day < start) return false
      if (end && day > end) return false
    }
    if (statusFilter.value && statusFilter.value.length > 0) {
      if (!statusFilter.value.includes(t.status)) return false
    }
    return true
  })
})

const pagedTasks = computed(() => {
  const start = (page.value - 1) * pageSize
  return filteredTasks.value.slice(start, start + pageSize)
})

const summary = computed(() => {
  const list = filteredTasks.value
  const total = list.length
  const done = list.filter(t => t.status === 'done').length
  const failed = list.filter(t => t.status === 'failed').length
  const running = list.filter(t => t.status === 'running').length
  const avg = total > 0 ? (list.reduce((s, t) => s + t.flightMin, 0) / total).toFixed(1) : '0.0'
  const totalMileage = list.reduce((s, t) => s + t.mileage, 0).toFixed(1)
  return { total, done, failed, running, avgFlight: avg, totalMileage }
})

// 图表
const chartRef = ref(null)
let chartInstance = null

function renderChart() {
  if (!chartRef.value) return
  if (!chartInstance) chartInstance = echarts.init(chartRef.value)
  const list = filteredTasks.value
  const byDay = {}
  list.forEach(t => {
    const d = new Date(t._ts).toISOString().slice(5, 10)
    if (!byDay[d]) byDay[d] = { total: 0, done: 0, failed: 0 }
    byDay[d].total++
    if (t.status === 'done') byDay[d].done++
    if (t.status === 'failed') byDay[d].failed++
  })
  const days = Object.keys(byDay).sort()
  const totals = days.map(d => byDay[d].total)
  const rates = days.map(d => {
    const b = byDay[d]
    const v = b.total > 0 ? +((b.done / b.total) * 100).toFixed(1) : 0
    return v
  })

  chartInstance.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['任务数', '成功率 %'] },
    grid: { left: 40, right: 50, top: 40, bottom: 30 },
    xAxis: { type: 'category', data: days, axisLabel: { color: '#606266' } },
    yAxis: [
      { type: 'value', name: '任务数', axisLabel: { color: '#606266' }, splitLine: { lineStyle: { color: '#f0f2f5' } } },
      { type: 'value', name: '成功率 %', min: 0, max: 100, axisLabel: { color: '#606266', formatter: '{value}%' }, splitLine: { show: false } }
    ],
    series: [
      { name: '任务数', type: 'bar', data: totals, itemStyle: { color: '#409EFF' }, barMaxWidth: 24 },
      { name: '成功率 %', type: 'line', yAxisIndex: 1, smooth: true, data: rates, itemStyle: { color: '#67C23A' }, lineStyle: { width: 2 } }
    ]
  })
}

function statusTag(s) {
  return {
    running: 'primary',
    done: 'success',
    failed: 'danger',
    pending: 'warning',
    canceled: 'info'
  }[s] || 'info'
}
function statusText(s) {
  return { running: '进行中', done: '已完成', failed: '失败', pending: '排队中', canceled: '已取消' }[s] || s
}

function generateReport() {
  generatedAt.value = new Date().toLocaleString('zh-CN', { hour12: false })
  page.value = 1
  nextTick(() => {
    if (includeCharts.value) renderChart()
  })
  ElMessage.success('报告已生成')
}

// ===== 导出 =====
function buildCsvText(rows) {
  const header = ['任务编号', '类型', '状态', '起点', '终点', '里程(km)', '飞行时间(min)', '提交时间', '负责人']
  const map = (t) => [
    t.code, t.type, statusText(t.status), t.from, t.to,
    String(t.mileage), String(t.flightMin), t.createdAt, t.owner
  ]
  const lines = [header, ...rows.map(map)]
  return lines.map(row =>
    row.map(cell => {
      const s = String(cell ?? '')
      if (/[",\n]/.test(s)) return '"' + s.replace(/"/g, '""') + '"'
      return s
    }).join(',')
  ).join('\n')
}

function downloadText(text, filename, mime, withBom = false) {
  const bom = withBom ? '\uFEFF' : ''
  const blob = new Blob([bom + text], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function handleExport(cmd) {
  const rows = filteredTasks.value
  if (rows.length === 0) {
    ElMessage.warning('当前筛选结果为空，无需导出')
    return
  }
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
  if (cmd === 'csv') {
    const text = buildCsvText(rows)
    downloadText(text, `tasks_report_${ts}.csv`, 'text/csv;charset=utf-8', true)
    ElMessage.success('CSV 已导出')
  } else if (cmd === 'xlsx') {
    const text = buildCsvText(rows)
    downloadText(text, `tasks_report_${ts}.xlsx`, 'application/vnd.ms-excel', true)
    ElMessage.success('XLSX 已导出（CSV 兼容格式，Excel 可直接打开）')
  } else if (cmd === 'pdf') {
    // 触发浏览器打印，用户选择"另存为 PDF"
    nextTick(() => {
      window.print()
    })
  }
}

function onResize() {
  if (chartInstance) chartInstance.resize()
}

onMounted(async () => {
  await nextTick()
  if (includeCharts.value) renderChart()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  if (chartInstance) { chartInstance.dispose(); chartInstance = null }
})

watch(includeCharts, v => {
  if (v) nextTick(() => renderChart())
})
</script>

<style scoped>
.task-report {
  padding: 16px 20px 24px;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.title-block {
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

.actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.main-row {
  margin-bottom: 16px;
}

.filter-card {
  border-radius: 10px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: #1f2937;
}

.print-area {
  background: transparent;
}

.print-header {
  background: #fff;
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 12px;
  border: 1px solid #ebeef5;
}

.report-title {
  margin: 0 0 6px 0;
  font-size: 18px;
  color: #1f2937;
  font-weight: 700;
}

.report-meta {
  font-size: 13px;
  color: #606266;
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
}

.summary-row {
  margin-bottom: 12px;
}

.summary-card {
  border-radius: 10px;
  padding: 16px 18px;
  color: #fff;
  background: linear-gradient(135deg, #409EFF, #1d7ed8);
  margin-bottom: 12px;
}

.summary-card.done { background: linear-gradient(135deg, #67C23A, #3f9b1f); }
.summary-card.failed { background: linear-gradient(135deg, #F56C6C, #c94141); }
.summary-card.running { background: linear-gradient(135deg, #E6A23C, #b9801f); }
.summary-card.avg-time { background: linear-gradient(135deg, #8e7cc3, #6c5ab0); }
.summary-card.mileage { background: linear-gradient(135deg, #36B5C5, #1f8f9d); }

.summary-label {
  font-size: 13px;
  opacity: 0.9;
}

.summary-value {
  font-size: 28px;
  font-weight: 700;
  margin-top: 4px;
}

.chart-card, .table-card {
  border-radius: 10px;
  margin-bottom: 12px;
}

.report-chart {
  height: 320px;
}

/* ===== 打印样式：隐藏顶部栏与左栏，只保留右栏报告内容 ===== */
@media print {
  :deep(.top-bar),
  :deep(.filter-card),
  :deep(.el-dropdown),
  :deep(.print-area .no-print-keep .el-pagination),
  :deep(.el-pagination) {
    display: none !important;
  }

  :deep(.print-area) {
    width: 100% !important;
    max-width: 100% !important;
  }

  :deep(.summary-card) {
    break-inside: avoid;
  }

  :deep(.report-chart) {
    break-inside: avoid;
  }

  :deep(.el-table) {
    font-size: 12px;
  }
}

@media (max-width: 768px) {
  .el-row,
  .el-row--flex {
    flex-direction: column !important;
  }
  .el-col {
    max-width: 100% !important;
    flex: 0 0 100% !important;
  }
  :deep(.el-card) {
    padding: 10px !important;
  }
  :deep(.el-table-wrapper) {
    overflow-x: auto;
  }
  :deep(.report-chart),
  .report-chart,
  .chart-wrapper {
    height: 280px !important;
  }
  .page-header,
  .report-header {
    padding: 10px !important;
  }
  .stat-card,
  .summary-card {
    padding: 10px !important;
  }
}
</style>
