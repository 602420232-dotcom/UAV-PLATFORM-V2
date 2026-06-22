<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

export interface LogEntry {
  timestamp: string
  level: string
  message: string
}

const props = withDefaults(defineProps<{
  experimentId: number
  logs: LogEntry[]
  maxHeight?: string
}>(), {
  maxHeight: '500px',
})

const emit = defineEmits<{
  (e: 'filter-change', level: string): void
  (e: 'search', keyword: string): void
}>()

const logContainerRef = ref<HTMLDivElement>()
const selectedLevel = ref('all')
const searchKeyword = ref('')
const autoScroll = ref(true)
const prevLogCount = ref(0)

const levelOptions = [
  { label: '全部', value: 'all' },
  { label: 'INFO', value: 'INFO' },
  { label: 'WARN', value: 'WARN' },
  { label: 'ERROR', value: 'ERROR' },
  { label: 'DEBUG', value: 'DEBUG' },
]

const levelColorMap: Record<string, string> = {
  INFO: 'var(--color-info, #409eff)',
  WARN: 'var(--color-warning, #e6a23c)',
  ERROR: 'var(--color-danger, #f56c6c)',
  DEBUG: 'var(--color-text-secondary, #909399)',
}

const levelTagMap: Record<string, string> = {
  INFO: '',
  WARN: 'warning',
  ERROR: 'danger',
  DEBUG: 'info',
}

const filteredLogs = computed(() => {
  let result = props.logs
  if (selectedLevel.value !== 'all') {
    result = result.filter((log) => log.level === selectedLevel.value)
  }
  if (searchKeyword.value.trim()) {
    const kw = searchKeyword.value.trim().toLowerCase()
    result = result.filter(
      (log) =>
        log.message.toLowerCase().includes(kw) ||
        log.level.toLowerCase().includes(kw) ||
        log.timestamp.toLowerCase().includes(kw)
    )
  }
  return result
})

const logStats = computed(() => {
  const stats: Record<string, number> = { INFO: 0, WARN: 0, ERROR: 0, DEBUG: 0 }
  for (const log of props.logs) {
    if (stats[log.level] !== undefined) {
      stats[log.level]!++
    }
  }
  return stats
})

const hasErrors = computed(() => (logStats.value.ERROR ?? 0) > 0)

function formatTimestamp(ts: string): string {
  try {
    const date = new Date(ts)
    return date.toLocaleString('zh-CN', {
      hour12: false,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  } catch {
    return ts
  }
}

function scrollToBottom() {
  if (!autoScroll.value || !logContainerRef.value) return
  nextTick(() => {
    const el = logContainerRef.value
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  })
}

function handleLevelChange(level: string) {
  emit('filter-change', level)
  scrollToBottom()
}

function handleSearch() {
  emit('search', searchKeyword.value)
}

function toggleAutoScroll() {
  autoScroll.value = !autoScroll.value
  if (autoScroll.value) {
    scrollToBottom()
  }
}

function exportLogs() {
  const lines = filteredLogs.value.map(
    (log) => `[${log.timestamp}] [${log.level}] ${log.message}`
  )
  const content = lines.join('\n')
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `experiment-${props.experimentId}-logs.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  ElMessage.success('日志已导出')
}

watch(
  () => props.logs.length,
  () => {
    if (props.logs.length > prevLogCount.value) {
      scrollToBottom()
    }
    prevLogCount.value = props.logs.length
  }
)

onMounted(() => {
  scrollToBottom()
})
</script>

<template>
  <div class="experiment-log-viewer">
    <!-- Toolbar -->
    <div class="log-toolbar">
      <div class="toolbar-left">
        <span class="toolbar-title">
          实验日志 #{{ experimentId }}
        </span>
        <div class="log-stats">
          <el-tag
            v-for="(count, level) in logStats"
            :key="level"
            :type="(levelTagMap[level] as any) || 'info'"
            size="small"
            effect="plain"
            class="stat-tag"
          >
            {{ level }}: {{ count }}
          </el-tag>
        </div>
      </div>
      <div class="toolbar-right">
        <el-select
          v-model="selectedLevel"
          size="small"
          style="width: 120px"
          @change="handleLevelChange"
        >
          <el-option
            v-for="opt in levelOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
        <el-input
          v-model="searchKeyword"
          size="small"
          placeholder="搜索日志..."
          clearable
          style="width: 200px"
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-tooltip :content="autoScroll ? '暂停自动滚动' : '继续自动滚动'">
          <el-button
            size="small"
            :type="autoScroll ? 'primary' : 'default'"
            plain
            @click="toggleAutoScroll"
          >
            <el-icon>
              <component :is="autoScroll ? 'Bottom' : 'VideoPause'" />
            </el-icon>
          </el-button>
        </el-tooltip>
        <el-button size="small" plain @click="exportLogs">
          导出日志
        </el-button>
      </div>
    </div>

    <!-- Log Content -->
    <div
      ref="logContainerRef"
      class="log-container"
      :style="{ maxHeight }"
    >
      <div v-if="filteredLogs.length === 0" class="log-empty">
        <el-empty description="暂无日志" :image-size="60" />
      </div>
      <div
        v-for="(log, index) in filteredLogs"
        :key="index"
        class="log-entry"
        :class="{ 'log-entry--error': log.level === 'ERROR' }"
      >
        <span class="log-timestamp">{{ formatTimestamp(log.timestamp) }}</span>
        <span
          class="log-level"
          :style="{ color: levelColorMap[log.level] || '#909399' }"
        >
          [{{ log.level.padEnd(5) }}]
        </span>
        <span class="log-message">{{ log.message }}</span>
      </div>
    </div>

    <!-- Footer Stats -->
    <div class="log-footer">
      <span class="footer-info">
        共 {{ filteredLogs.length }} 条日志
        <template v-if="searchKeyword"> (已过滤) </template>
      </span>
      <span v-if="hasErrors" class="footer-error">
        存在 {{ logStats.ERROR }} 条错误日志
      </span>
    </div>
  </div>
</template>

<script lang="ts">
import { Search, Bottom, VideoPause } from '@element-plus/icons-vue'
export default {
  components: { Search, Bottom, VideoPause },
}
</script>

<style scoped>
.experiment-log-viewer {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-secondary, #1a1a2e);
  border-radius: 8px;
  border: 1px solid var(--color-border, #2a2a40);
  overflow: hidden;
}

.log-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-border, #2a2a40);
  flex-wrap: wrap;
  gap: 8px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary, #e0e0e0);
}

.log-stats {
  display: flex;
  gap: 6px;
}

.stat-tag {
  font-size: 11px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.log-container {
  overflow-y: auto;
  overflow-x: hidden;
  padding: 8px 12px;
  background: var(--color-bg-primary, #0f0f23);
  font-family: 'Fira Code', 'Consolas', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  scroll-behavior: smooth;
}

.log-container::-webkit-scrollbar {
  width: 6px;
}

.log-container::-webkit-scrollbar-track {
  background: transparent;
}

.log-container::-webkit-scrollbar-thumb {
  background: var(--color-border, #2a2a40);
  border-radius: 3px;
}

.log-empty {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.log-entry {
  display: flex;
  gap: 8px;
  padding: 2px 0;
  border-radius: 2px;
  transition: background-color 0.15s;
}

.log-entry:hover {
  background: var(--color-bg-hover, rgba(255, 255, 255, 0.03));
}

.log-entry--error {
  background: rgba(245, 108, 108, 0.06);
}

.log-entry--error:hover {
  background: rgba(245, 108, 108, 0.1);
}

.log-timestamp {
  flex-shrink: 0;
  color: var(--color-text-secondary, #909399);
  font-size: 12px;
}

.log-level {
  flex-shrink: 0;
  font-weight: 600;
  font-size: 12px;
}

.log-message {
  color: var(--color-text-primary, #e0e0e0);
  word-break: break-all;
}

.log-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  border-top: 1px solid var(--color-border, #2a2a40);
  font-size: 12px;
}

.footer-info {
  color: var(--color-text-secondary, #909399);
}

.footer-error {
  color: var(--color-danger, #f56c6c);
  font-weight: 500;
}
</style>
