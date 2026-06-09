<template>
  <el-drawer
    :model-value="visible"
    title="通知中心"
    direction="rtl"
    size="420px"
    :with-header="true"
    :append-to-body="false"
    @update:model-value="onVisibleUpdate"
    @close="onClose"
  >
    <div class="notification-drawer">
      <!-- 顶部搜索与筛选 -->
      <div class="drawer-toolbar">
        <el-input
          v-model="keyword"
          placeholder="搜索标题或内容..."
          clearable
          size="default"
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <div class="filter-tabs">
          <el-button
            v-for="tab in sourceTabs"
            :key="tab.key"
            :type="currentSource === tab.key ? 'primary' : 'default'"
            size="small"
            @click="currentSource = tab.key"
          >
            {{ tab.label }}
          </el-button>
        </div>
      </div>

      <!-- 通知列表 -->
      <div class="notification-list" v-if="filteredList.length > 0">
        <div
          v-for="item in filteredList"
          :key="item.id"
          class="notification-card"
          :class="[
            'type-' + item.type,
            { 'is-read': item.read }
          ]"
          @click="handleCardClick(item)"
        >
          <div class="card-icon">
            <el-icon :size="16">
              <component :is="typeIconMap[item.type] || InfoFilled" />
            </el-icon>
          </div>
          <div class="card-body">
            <div class="card-header-row">
              <span class="card-title">{{ item.title }}</span>
              <span class="card-time">{{ formatTime(item.createdAt) }}</span>
            </div>
            <div class="card-message">{{ item.message }}</div>
            <div class="card-meta">
              <el-tag size="small" :type="tagTypeMap[item.type] || 'info'">
                {{ sourceLabelMap[item.source] || item.source }}
              </el-tag>
              <el-button
                link
                type="danger"
                size="small"
                class="card-close"
                @click.stop="handleRemove(item.id)"
              >
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <el-empty
        v-else
        description="暂无通知"
        class="empty-state"
      />

      <!-- 底部操作栏 -->
      <div class="drawer-footer">
        <el-button size="small" @click="handleMarkAllRead">
          <el-icon><Check /></el-icon>&nbsp;标记全部已读
        </el-button>
        <el-button size="small" type="danger" @click="handleClearAll">
          <el-icon><Delete /></el-icon>&nbsp;清空通知
        </el-button>
        <el-button size="small" type="primary" @click="prefDialogVisible = true">
          <el-icon><Setting /></el-icon>&nbsp;订阅设置
        </el-button>
      </div>
    </div>

    <!-- 订阅设置弹窗 -->
    <el-dialog v-model="prefDialogVisible" title="通知订阅设置" width="420px">
      <div class="pref-block">
        <h4 class="pref-title">通知来源</h4>
        <div class="pref-list">
          <div class="pref-row" v-for="src in sourceOptions" :key="src.key">
            <span class="pref-label">{{ src.label }}</span>
            <el-switch
              :model-value="prefs[src.key]"
              active-text="接收"
              inactive-text="关闭"
              inline-prompt
              @update:model-value="(v) => handlePrefChange(src.key, v)"
            />
          </div>
        </div>
        <h4 class="pref-title">桌面通知</h4>
        <div class="pref-row">
          <span class="pref-label">启用桌面推送</span>
          <el-switch
            :model-value="prefs.desktop"
            active-text="开启"
            inactive-text="关闭"
            inline-prompt
            @update:model-value="(v) => handlePrefChange('desktop', v)"
          />
        </div>
        <div class="pref-row">
          <el-button size="small" @click="handleRequestPermission">
            <el-icon><Bell /></el-icon>&nbsp;请求桌面通知权限
          </el-button>
          <span class="pref-status">当前权限：{{ desktopPermissionLabel }}</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="prefDialogVisible = false">完成</el-button>
      </template>
    </el-dialog>
  </el-drawer>
</template>

<script setup>
import { computed, ref, watch, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search, Check, Delete, Setting, Bell, Close,
  InfoFilled, SuccessFilled, Warning, CircleClose
} from '@element-plus/icons-vue'
import { useNotificationStore } from '../../stores/notification'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'close'])

const store = useNotificationStore()
const keyword = ref('')
const currentSource = ref('all')
const prefDialogVisible = ref(false)

const prefs = reactive({
  task: store.subscriptionPrefs.task,
  weather: store.subscriptionPrefs.weather,
  uav: store.subscriptionPrefs.uav,
  planning: store.subscriptionPrefs.planning,
  apiConfig: store.subscriptionPrefs.apiConfig,
  utm: store.subscriptionPrefs.utm,
  system: store.subscriptionPrefs.system,
  desktop: store.subscriptionPrefs.desktop
})

const sourceTabs = [
  { key: 'all', label: '全部' },
  { key: 'task', label: '任务' },
  { key: 'weather', label: '气象' },
  { key: 'uav', label: '无人机' },
  { key: 'planning', label: '规划' },
  { key: 'apiConfig', label: '配置' },
  { key: 'utm', label: 'UTM' },
  { key: 'system', label: '系统' }
]

const sourceOptions = [
  { key: 'task', label: '任务通知' },
  { key: 'weather', label: '气象预警' },
  { key: 'uav', label: '无人机状态' },
  { key: 'planning', label: '路径规划' },
  { key: 'apiConfig', label: 'API 配置' },
  { key: 'utm', label: 'UTM 对接' },
  { key: 'system', label: '系统消息' }
]

const sourceLabelMap = {
  task: '任务',
  weather: '气象',
  uav: '无人机',
  planning: '规划',
  apiConfig: '配置',
  utm: 'UTM',
  system: '系统'
}

const typeIconMap = {
  info: InfoFilled,
  success: SuccessFilled,
  warning: Warning,
  danger: CircleClose
}

const tagTypeMap = {
  info: 'info',
  success: 'success',
  warning: 'warning',
  danger: 'danger'
}

const filteredList = computed(() => {
  const base = currentSource.value === 'all'
    ? store.notifications
    : store.filterBySource(currentSource.value)
  if (!keyword.value) return base
  const kw = keyword.value.toLowerCase()
  return base.filter(
    (n) =>
      (n.title || '').toLowerCase().includes(kw) ||
      (n.message || '').toLowerCase().includes(kw)
  )
})

const desktopPermissionLabel = computed(() => {
  if (typeof window === 'undefined' || typeof Notification === 'undefined') {
    return '浏览器不支持'
  }
  const map = {
    granted: '已授权',
    denied: '已拒绝',
    default: '未设置'
  }
  return map[Notification.permission] || Notification.permission
})

function formatTime(iso) {
  try {
    const d = new Date(iso)
    const now = new Date()
    const diff = now - d
    if (diff < 60 * 1000) return '刚刚'
    if (diff < 60 * 60 * 1000) return Math.floor(diff / 60000) + ' 分钟前'
    if (diff < 24 * 60 * 60 * 1000) return Math.floor(diff / 3600000) + ' 小时前'
    const pad = (n) => String(n).padStart(2, '0')
    return (
      d.getFullYear() +
      '-' +
      pad(d.getMonth() + 1) +
      '-' +
      pad(d.getDate()) +
      ' ' +
      pad(d.getHours()) +
      ':' +
      pad(d.getMinutes())
    )
  } catch (_) {
    return iso || ''
  }
}

function onVisibleUpdate(val) {
  emit('update:visible', val)
}

function onClose() {
  emit('close')
}

function handleCardClick(item) {
  if (!item.read) {
    store.markAsRead(item.id)
  }
}

function handleRemove(id) {
  store.removeNotification(id)
}

function handleMarkAllRead() {
  if (store.unreadCount === 0) {
    ElMessage.info('没有未读通知')
    return
  }
  store.markAllRead()
  ElMessage.success('已全部标记为已读')
}

function handleClearAll() {
  if (store.notifications.length === 0) {
    ElMessage.info('通知列表为空')
    return
  }
  ElMessageBox.confirm('确认清空全部通知？此操作不可撤销。', '提示', {
    confirmButtonText: '清空',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(() => {
      store.clearAll()
      ElMessage.success('已清空通知')
    })
    .catch(() => {})
}

function handlePrefChange(key, value) {
  prefs[key] = value
  const patch = {}
  patch[key] = value
  store.updateSubscriptionPrefs(patch)
}

function handleRequestPermission() {
  store.requestDesktopPermission().then((result) => {
    if (result === 'granted') {
      ElMessage.success('已授权桌面通知')
      prefs.desktop = true
      store.updateSubscriptionPrefs({ desktop: true })
    } else if (result === 'denied') {
      ElMessage.warning('浏览器已拒绝桌面通知权限')
    } else if (result === 'unsupported') {
      ElMessage.info('当前环境不支持桌面通知')
    } else {
      ElMessage.info('权限状态：' + result)
    }
  })
}

watch(
  () => store.subscriptionPrefs,
  (val) => {
    Object.keys(prefs).forEach((k) => {
      if (val[k] !== undefined) prefs[k] = val[k]
    })
  },
  { deep: true }
)
</script>

<style scoped>
.notification-drawer {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.drawer-toolbar {
  padding: 8px 4px 12px;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 8px;
}

.search-input {
  margin-bottom: 10px;
}

.filter-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.notification-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.notification-card {
  display: flex;
  gap: 10px;
  padding: 12px 12px;
  margin-bottom: 8px;
  border-radius: 8px;
  background: #fafbfc;
  border: 1px solid #e4e7ed;
  cursor: pointer;
  transition: all 0.2s;
}

.notification-card:hover {
  background: #f0f7ff;
  border-color: #a0cfff;
}

.notification-card.is-read {
  opacity: 0.75;
  background: #ffffff;
}

.notification-card.type-info {
  border-left: 4px solid #409eff;
}

.notification-card.type-success {
  border-left: 4px solid #67c23a;
}

.notification-card.type-warning {
  border-left: 4px solid #e6a23c;
}

.notification-card.type-danger {
  border-left: 4px solid #f56c6c;
}

.card-icon {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  background: #409eff;
}

.type-info .card-icon {
  background: #409eff;
}

.type-success .card-icon {
  background: #67c23a;
}

.type-warning .card-icon {
  background: #e6a23c;
}

.type-danger .card-icon {
  background: #f56c6c;
}

.card-body {
  flex: 1;
  min-width: 0;
}

.card-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  gap: 8px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-time {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
}

.card-message {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
  margin-bottom: 6px;
  word-break: break-word;
}

.card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-close {
  padding: 0 !important;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.drawer-footer {
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pref-block {
  padding: 4px 0;
}

.pref-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 10px;
}

.pref-list {
  margin-bottom: 16px;
}

.pref-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  gap: 12px;
}

.pref-label {
  font-size: 13px;
  color: #606266;
}

.pref-status {
  font-size: 12px;
  color: #909399;
}
</style>
