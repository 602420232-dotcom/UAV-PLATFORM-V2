<template>
  <div class="docker-build">
    <div class="page-title">Docker 构建可视化</div>

    <el-alert
      type="warning"
      :closable="false"
      show-icon
      title="演示模式"
      description="以下构建流程与日志均为模拟数据，用于测试构建可视化的交互与视觉呈现。"
      class="demo-alert"
    />

    <!-- 卡住告警 -->
    <el-alert
      v-if="stuckWarning"
      type="error"
      :closable="true"
      show-icon
      title="构建疑似卡住"
      description="日志长时间无更新，可点击顶部「停止构建」并联系管理员。"
      class="stuck-alert"
      @close="stuckWarning = false"
    />

    <!-- 顶部栏：环境 + 镜像名/版本 + 操作按钮 -->
    <el-card class="section-card" shadow="never">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-select v-model="env" class="w-140">
            <el-option label="开发环境 (dev)" value="dev" />
            <el-option label="测试环境 (test)" value="test" />
            <el-option label="生产环境 (prod)" value="prod" />
          </el-select>

          <el-input
            v-model="imageName"
            placeholder="镜像名"
            class="w-180"
            clearable
          >
            <template #prefix>🐳</template>
          </el-input>

          <el-input
            v-model="imageVersion"
            placeholder="版本号"
            class="w-140"
            clearable
          >
            <template #prefix>v</template>
          </el-input>

          <el-tag :type="statusTagType" effect="dark" size="default" class="status-tag">
            {{ statusLabel }}
          </el-tag>
        </div>

        <div class="toolbar-right">
          <el-button v-if="authStore.hasAction('docker:build')" type="primary" :loading="status === 'building'" @click="startBuild">
            开始构建
          </el-button>
          <el-button v-if="authStore.hasAction('docker:build')" type="danger" :disabled="status !== 'building'" @click="stopBuild">
            停止构建
          </el-button>
          <el-button v-if="authStore.hasAction('docker:view')" @click="showHistory = true">
            查看历史
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 上半部分：构建进度 -->
    <el-card class="section-card" shadow="never" v-if="authStore.hasAction('docker:view')">
      <template #header>
        <div class="card-header">
          <span class="header-icon">📦</span>
          <span>构建进度</span>
          <div class="header-right">
            <span>总进度</span>
            <span class="total-percent">{{ overallPercent }}%</span>
            <span class="duration">耗时 {{ formatDuration(totalDuration) }}</span>
          </div>
        </div>
      </template>

      <el-progress
        :percentage="overallPercent"
        :status="status === 'failed' ? 'exception' : (status === 'success' ? 'success' : null)"
        :stroke-width="16"
        class="main-progress"
      />

      <el-row :gutter="12" class="stages">
        <el-col
          :xs="24"
          :sm="12"
          :md="8"
          v-for="(stage, idx) in stages"
          :key="stage.key"
        >
          <el-card
            :class="['stage-card', { active: stage.status === 'running', done: stage.status === 'done', failed: stage.status === 'failed' }]"
            shadow="hover"
          >
            <div class="stage-header">
              <div class="stage-index">{{ idx + 1 }}</div>
              <div class="stage-title">
                <div class="stage-name">{{ stage.name }}</div>
                <div class="stage-desc">{{ stage.desc }}</div>
              </div>
              <el-tag :type="stageTagType(stage.status)" effect="light" size="small">
                {{ stageStatusLabel(stage.status) }}
              </el-tag>
            </div>

            <el-progress
              :percentage="stage.percent"
              :status="stage.status === 'failed' ? 'exception' : (stage.status === 'done' ? 'success' : null)"
              :stroke-width="6"
              class="stage-progress"
            />

            <div class="stage-footer">
              <span>耗时：{{ formatDuration(stage.duration) }}</span>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 下半部分：日志流 -->
    <el-card class="section-card" shadow="never" v-if="authStore.hasAction('docker:view')">
      <template #header>
        <div class="card-header">
          <span class="header-icon">📝</span>
          <span>构建日志</span>
          <div class="header-right">
            <el-switch v-model="autoScroll" active-text="自动滚动" inactive-text="" />
            <el-button size="small" @click="clearLogs">清空</el-button>
            <el-button size="small" type="primary" @click="downloadLogs">下载日志</el-button>
          </div>
        </div>
      </template>

      <div class="log-panel" ref="logPanelRef">
        <div
          v-for="(line, idx) in logs"
          :key="idx"
          class="log-line"
          :class="'log-' + line.level.toLowerCase()"
        >
          <span class="log-time">[{{ line.time }}]</span>
          <span class="log-level">[{{ line.level }}]</span>
          <span class="log-msg">{{ line.msg }}</span>
        </div>
        <div v-if="logs.length === 0" class="log-empty">暂无日志，点击「开始构建」以运行演示流程。</div>
      </div>
    </el-card>

    <!-- 历史记录弹窗 -->
    <el-dialog v-model="showHistory" title="构建历史" width="720px">
      <el-table :data="history" stripe border>
        <el-table-column type="index" label="#" width="60" />
        <el-table-column prop="image" label="镜像名" width="180" />
        <el-table-column prop="version" label="版本" width="120" />
        <el-table-column prop="env" label="环境" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.env }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : (row.status === 'failed' ? 'danger' : 'info')" size="small">
              {{ row.status === 'success' ? '成功' : (row.status === 'failed' ? '失败' : '进行中') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="120" align="center">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        <el-table-column prop="time" label="触发时间" />
      </el-table>
      <template #footer>
        <el-button @click="showHistory = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useNotificationStore } from '../../stores/notification'
import { useAuthStore } from '@/stores/auth'

const notificationStore = useNotificationStore()
const authStore = useAuthStore()

// ===== 顶部配置 =====
const env = ref('dev')
const imageName = ref('uav-frontend')
const imageVersion = ref('v1.0.0')

// ===== 状态 =====
const status = ref('idle') // idle | building | success | failed
const stuckWarning = ref(false)

const statusLabel = computed(() => {
  switch (status.value) {
    case 'idle': return '空闲'
    case 'building': return '构建中'
    case 'success': return '构建成功'
    case 'failed': return '构建失败'
    default: return '空闲'
  }
})

const statusTagType = computed(() => {
  switch (status.value) {
    case 'idle': return 'info'
    case 'building': return 'warning'
    case 'success': return 'success'
    case 'failed': return 'danger'
    default: return 'info'
  }
})

// ===== 阶段 =====
const STAGE_DEFS = [
  { key: 'pull',    name: '拉取基础镜像', desc: '从镜像仓库拉取 node:20-alpine 基础层' },
  { key: 'install', name: '安装依赖',     desc: 'npm ci 安装生产依赖' },
  { key: 'build',   name: '构建应用',     desc: 'npm run build 打包前端资源' },
  { key: 'optimize',name: '优化产物',     desc: '压缩静态文件 / 删除未使用资源' },
  { key: 'package', name: '打包镜像',     desc: '复制 dist 到 nginx 基础层并生成镜像' },
  { key: 'push',    name: '上传镜像',     desc: '推送到私有镜像仓库 registry.example.com' }
]

const makeStages = () =>
  STAGE_DEFS.map(s => ({ ...s, status: 'pending', percent: 0, duration: 0 }))

const stages = ref(makeStages())

// ===== 时间 =====
const buildStartAt = ref(0)
const totalDuration = ref(0)
let buildTimer = null
let tickTimer = null
let stuckTimer = null

// ===== 进度计算 =====
const overallPercent = computed(() => {
  if (stages.value.length === 0) return 0
  const sum = stages.value.reduce((acc, s) => acc + s.percent, 0)
  return Math.min(100, Math.round(sum / stages.value.length))
})

function stageTagType(stageStatus) {
  switch (stageStatus) {
    case 'running': return 'warning'
    case 'done': return 'success'
    case 'failed': return 'danger'
    default: return 'info'
  }
}

function stageStatusLabel(stageStatus) {
  switch (stageStatus) {
    case 'running': return '进行中'
    case 'done': return '完成'
    case 'failed': return '失败'
    default: return '等待中'
  }
}

function formatDuration(ms) {
  if (!ms || ms < 0) return '0.0s'
  const sec = ms / 1000
  if (sec < 60) return `${sec.toFixed(1)}s`
  const m = Math.floor(sec / 60)
  const s = Math.round(sec - m * 60)
  return `${m}m ${s}s`
}

function formatTime(d) {
  const p = n => String(n).padStart(2, '0')
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

// ===== 日志 =====
const logs = ref([])
const autoScroll = ref(true)
const logPanelRef = ref(null)

function pushLog(level, msg) {
  logs.value.push({
    time: formatTime(new Date()),
    level,
    msg
  })
  if (logs.value.length > 500) logs.value.shift()
  // 触发卡住检测重置
  resetStuckTimer()
  nextTick(() => {
    if (autoScroll.value && logPanelRef.value) {
      logPanelRef.value.scrollTop = logPanelRef.value.scrollHeight
    }
  })
}

function clearLogs() {
  logs.value = []
  ElMessage.success('日志已清空')
}

function downloadLogs() {
  if (logs.value.length === 0) {
    ElMessage.warning('当前无日志可下载')
    return
  }
  const content = logs.value
    .map(l => `[${l.time}] [${l.level}] ${l.msg}`)
    .join('\n')
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${imageName.value}-${imageVersion.value}-build.log`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  ElMessage.success('日志已下载')
}

// ===== 卡住检测 =====
function resetStuckTimer() {
  if (stuckTimer) clearTimeout(stuckTimer)
  stuckTimer = setTimeout(() => {
    if (status.value === 'building') {
      stuckWarning.value = true
      notificationStore.pushWithDesktop({
        type: 'danger',
        title: '构建疑似卡住',
        message: `镜像 ${imageName.value}:${imageVersion.value} 30 秒无日志更新`,
        source: 'system'
      })
    }
  }, 30000)
}

function clearStuckTimer() {
  if (stuckTimer) {
    clearTimeout(stuckTimer)
    stuckTimer = null
  }
}

// ===== 历史 =====
const showHistory = ref(false)
const history = ref([
  { image: 'uav-frontend', version: 'v0.9.5', env: 'test', status: 'success', duration: 11200, time: '2025-06-08 14:22:10' },
  { image: 'uav-frontend', version: 'v0.9.4', env: 'dev',  status: 'failed',  duration: 7400,  time: '2025-06-07 18:05:32' },
  { image: 'uav-frontend', version: 'v0.9.3', env: 'dev',  status: 'success', duration: 10800, time: '2025-06-07 09:41:08' },
  { image: 'uav-backend',  version: 'v1.2.0', env: 'prod', status: 'success', duration: 15300, time: '2025-06-05 22:10:51' },
  { image: 'uav-frontend', version: 'v0.9.2', env: 'test', status: 'success', duration: 12000, time: '2025-06-04 16:30:11' }
])

function pushHistory(histStatus, histDuration) {
  history.value.unshift({
    image: imageName.value,
    version: imageVersion.value,
    env: env.value,
    status: histStatus,
    duration: histDuration,
    time: new Date().toLocaleString('zh-CN', { hour12: false })
  })
  if (history.value.length > 10) history.value.length = 10
}

// ===== 构建主流程 =====
function resetBuild() {
  stages.value = makeStages()
  totalDuration.value = 0
  buildStartAt.value = 0
  logs.value = []
  stuckWarning.value = false
}

function startBuild() {
  if (status.value === 'building') {
    ElMessage.warning('当前已有构建在进行')
    return
  }

  ElMessageBox.confirm(
    `将在「${env.value}」环境构建 ${imageName.value}:${imageVersion.value}，是否继续？`,
    '构建确认',
    { confirmButtonText: '开始构建', cancelButtonText: '取消', type: 'warning' }
  )
    .then(() => runBuild())
    .catch(() => {})
}

function runBuild() {
  resetBuild()
  status.value = 'building'
  buildStartAt.value = Date.now()

  // 全局时间更新
  tickTimer = setInterval(() => {
    if (status.value === 'building') {
      totalDuration.value = Date.now() - buildStartAt.value
    }
  }, 200)

  resetStuckTimer()

  // 初始化日志
  pushLog('INFO', `Starting build for ${imageName.value}:${imageVersion.value} (env=${env.value})`)
  pushLog('INFO', `Build ID: build-${Date.now().toString(36)}`)

  const stageDurations = STAGE_DEFS.map(() => 1400 + Math.floor(Math.random() * 400)) // ~1.4-1.8s
  // 决定是否在第 4 阶段模拟失败（20% 概率）
  const willFail = Math.random() < 0.2
  const failStageIndex = 3 // 第 4 阶段（索引 3）：优化产物

  let stageIndex = 0
  const runNextStage = () => {
    if (stageIndex >= stages.value.length) {
      finishBuild('success')
      return
    }

    const stage = stages.value[stageIndex]
    stage.status = 'running'
    stage.percent = 0

    // 阶段初始日志
    pushLog('INFO', `Step ${stageIndex + 1}/${stages.value.length} : ${stage.name} ...`)

    if (stageIndex === 0) {
      pushLog('INFO', `Digest: sha256:${Math.random().toString(36).slice(2, 10)}...${Math.random().toString(36).slice(2, 10)}`)
    }
    if (stageIndex === 1) {
      pushLog('INFO', `npm ci --production ...`)
    }
    if (stageIndex === 2) {
      pushLog('INFO', `npm run build (mode=${env.value}) ...`)
    }
    if (stageIndex === 5) {
      pushLog('INFO', `Pushing to registry.example.com/${imageName.value}:${imageVersion.value}`)
    }

    const duration = stageDurations[stageIndex]
    const startAt = Date.now()
    const isFailTarget = willFail && stageIndex === failStageIndex

    buildTimer = setInterval(() => {
      const elapsed = Date.now() - startAt
      stage.duration = elapsed
      const ratio = Math.min(1, elapsed / duration)
      stage.percent = Math.round(ratio * 100)

      // 过程随机日志
      if (Math.random() < 0.25) {
        const samples = [
          { level: 'INFO', msg: `  -> layer ${Math.floor(Math.random() * 99) + 1} cached` },
          { level: 'INFO', msg: `  -> running intermediate step ...` },
          { level: 'DEBUG', msg: `  cache HIT (key=${Math.random().toString(36).slice(2, 10)})` },
          { level: 'INFO', msg: `  -> file processed ${Math.random().toFixed(3)}.js` },
          { level: 'WARNING', msg: `  -> optional dependency not found, skipping` }
        ]
        const pick = samples[Math.floor(Math.random() * samples.length)]
        pushLog(pick.level, pick.msg)
      }

      if (ratio >= 1) {
        clearInterval(buildTimer)
        buildTimer = null
        stage.percent = 100

        if (isFailTarget) {
          // 模拟失败
          stage.status = 'failed'
          pushLog('ERROR', `npm ERR! code ELIFECYCLE`)
          pushLog('ERROR', `npm ERR! errno 1`)
          pushLog('ERROR', `${imageName.value}@${imageVersion.value} build: \`vite build\``)
          pushLog('ERROR', `Exit status 1`)
          status.value = 'failed'
          totalDuration.value = Date.now() - buildStartAt.value
          pushLog('ERROR', `Build failed after ${formatDuration(totalDuration.value)}`)
          clearInterval(tickTimer)
          clearStuckTimer()
          pushHistory('failed', totalDuration.value)
          notificationStore.pushWithDesktop({
            type: 'danger',
            title: '构建失败',
            message: `${imageName.value}:${imageVersion.value} 在「${stage.name}」阶段失败`,
            source: 'system'
          })
          ElMessage.error('构建失败，详见日志')
          return
        }

        stage.status = 'done'
        pushLog('INFO', `  -> done in ${formatDuration(stage.duration)}`)
        stageIndex++
        setTimeout(runNextStage, 200)
      }
    }, 180)
  }

  runNextStage()
}

function finishBuild(result) {
  status.value = result
  totalDuration.value = Date.now() - buildStartAt.value
  clearInterval(tickTimer)
  clearStuckTimer()
  if (buildTimer) clearInterval(buildTimer)
  if (result === 'success') {
    pushLog('INFO', `Build succeeded in ${formatDuration(totalDuration.value)}`)
    pushLog('SUCCESS', `Image ${imageName.value}:${imageVersion.value} ready`)
    pushHistory('success', totalDuration.value)
    notificationStore.pushWithDesktop({
      type: 'success',
      title: '构建成功',
      message: `${imageName.value}:${imageVersion.value} 已成功构建`,
      source: 'system'
    })
    ElMessage.success('构建成功')
  }
}

function stopBuild() {
  if (status.value !== 'building') return
  ElMessageBox.confirm('确认要停止当前构建吗？', '停止构建', {
    confirmButtonText: '确认停止',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(() => {
      if (buildTimer) clearInterval(buildTimer)
      if (tickTimer) clearInterval(tickTimer)
      clearStuckTimer()
      // 将所有未完成阶段置为失败/中止
      stages.value.forEach(s => {
        if (s.status === 'running' || s.status === 'pending') s.status = 'failed'
      })
      status.value = 'failed'
      totalDuration.value = Date.now() - buildStartAt.value
      pushLog('ERROR', 'Build cancelled by user')
      pushHistory('failed', totalDuration.value)
      ElMessage.warning('构建已停止')
    })
    .catch(() => {})
}

onBeforeUnmount(() => {
  if (buildTimer) clearInterval(buildTimer)
  if (tickTimer) clearInterval(tickTimer)
  clearStuckTimer()
})
</script>

<style scoped>
.docker-build {
  padding: 20px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #1f2937;
  padding-left: 10px;
  border-left: 4px solid #409EFF;
}

.demo-alert {
  margin-bottom: 16px;
}

.stuck-alert {
  margin-bottom: 16px;
}

.section-card {
  border-radius: 10px;
  margin-bottom: 16px;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.toolbar-right {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.status-tag {
  margin-left: 8px;
}

.w-140 {
  width: 140px;
}

.w-180 {
  width: 180px;
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
  gap: 12px;
  font-weight: normal;
  font-size: 13px;
  color: #6b7280;
}

.total-percent {
  color: #1f2937;
  font-weight: 600;
  font-size: 15px;
}

.duration {
  color: #6b7280;
}

.main-progress {
  margin: 8px 0 16px 0;
}

.stages {
  margin-top: 4px;
}

.stage-card {
  border-radius: 10px;
  margin-bottom: 12px;
  border: 1px solid #e4e7ed;
  transition: all 0.25s ease;
}

.stage-card.active {
  border-color: #e6a23c;
  box-shadow: 0 2px 12px 0 rgba(230, 162, 60, 0.15);
}

.stage-card.done {
  border-color: #67c23a;
}

.stage-card.failed {
  border-color: #f56c6c;
}

.stage-header {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.stage-index {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #ecf5ff;
  color: #409eff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
}

.stage-card.active .stage-index {
  background: #fdf6ec;
  color: #e6a23c;
}

.stage-card.done .stage-index {
  background: #f0f9eb;
  color: #67c23a;
}

.stage-card.failed .stage-index {
  background: #fef0f0;
  color: #f56c6c;
}

.stage-title {
  flex: 1;
  min-width: 0;
}

.stage-name {
  font-weight: 600;
  color: #1f2937;
  font-size: 14px;
}

.stage-desc {
  color: #6b7280;
  font-size: 12px;
  margin-top: 2px;
}

.stage-progress {
  margin: 12px 0 4px 0;
}

.stage-footer {
  color: #909399;
  font-size: 12px;
  text-align: right;
}

/* 日志面板 */
.log-panel {
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 8px;
  padding: 12px 14px;
  height: 320px;
  overflow-y: auto;
  font-family: 'SFMono-Regular', Menlo, Consolas, monospace;
  font-size: 12.5px;
  line-height: 1.7;
}

.log-panel::-webkit-scrollbar {
  width: 8px;
}

.log-panel::-webkit-scrollbar-thumb {
  background: #334155;
  border-radius: 4px;
}

.log-line {
  white-space: pre-wrap;
  word-break: break-all;
}

.log-time {
  color: #64748b;
}

.log-level {
  color: #94a3b8;
  margin-right: 6px;
}

.log-msg {
  color: #cbd5e1;
}

.log-info .log-level {
  color: #60a5fa;
}

.log-warning .log-level,
.log-warning .log-msg {
  color: #fbbf24;
}

.log-error .log-level,
.log-error .log-msg {
  color: #f87171;
}

.log-debug .log-level {
  color: #a78bfa;
}

.log-success .log-level,
.log-success .log-msg {
  color: #4ade80;
}

.log-empty {
  color: #64748b;
  text-align: center;
  padding: 60px 0;
  font-style: italic;
}
</style>
