<template>
  <div class="user-stats-container">
    <el-card class="stats-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">👥 用户使用统计</span>
          <el-button type="primary" size="small" @click="handleExport">
            <el-icon><Download /></el-icon>
            导出报告
          </el-button>
        </div>
      </template>

      <!-- 统计概览 -->
      <div class="stats-overview">
        <div class="stat-item">
          <div class="stat-value">{{ overviewStats.totalUsers }}</div>
          <div class="stat-label">总用户数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ overviewStats.activeUsers }}</div>
          <div class="stat-label">活跃用户</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ overviewStats.totalPosts }}</div>
          <div class="stat-label">发帖总数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ overviewStats.totalComments }}</div>
          <div class="stat-label">评论总数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ overviewStats.totalLogins }}</div>
          <div class="stat-label">登录次数</div>
        </div>
      </div>

      <!-- 用户列表 -->
      <el-table :data="userStats" stripe class="user-table">
        <el-table-column prop="userName" label="用户名" width="100" />
        <el-table-column prop="role" label="角色" width="80">
          <template #default="{ row }">
            <el-tag size="small" :type="getRoleTagType(row.role)">
              {{ row.role }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="location" label="所在地" width="100">
          <template #default="{ row }">
            <span>📍 {{ row.location }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="postCount" label="发帖数" width="80" sortable />
        <el-table-column prop="commentCount" label="评论数" width="80" sortable />
        <el-table-column prop="loginCount" label="登录次数" width="90" sortable />
        <el-table-column prop="lastActive" label="最后活跃" width="160">
          <template #default="{ row }">
            {{ formatTime(row.lastActive) }}
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 操作统计 -->
    <el-card class="stats-card" shadow="hover">
      <template #header>
        <span class="card-title">📊 操作统计</span>
      </template>
      <div class="action-stats">
        <div 
          v-for="(count, action) in overviewStats.actionStats" 
          :key="action"
          class="action-item"
        >
          <span class="action-label">{{ action }}</span>
          <el-progress 
            :percentage="getActionPercentage(count)" 
            :stroke-width="12"
            :format="format => count"
          />
        </div>
      </div>
    </el-card>

    <!-- 地域分布 -->
    <el-card class="stats-card" shadow="hover">
      <template #header>
        <span class="card-title">🗺️ 地域分布</span>
      </template>
      <div class="location-stats">
        <div 
          v-for="(count, location) in overviewStats.locationStats" 
          :key="location"
          class="location-item"
        >
          <span class="location-name">{{ location }}</span>
          <el-tag size="small" type="info">{{ count }} 人</el-tag>
        </div>
      </div>
    </el-card>

    <!-- 活动日志 -->
    <el-card class="stats-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span class="card-title">📝 活动日志</span>
          <div class="filter-actions">
            <el-select v-model="filterAction" placeholder="操作类型" clearable size="small" style="width: 120px">
              <el-option label="全部操作" value="" />
              <el-option label="登录" value="login" />
              <el-option label="发帖" value="create_post" />
              <el-option label="评论" value="comment" />
              <el-option label="访问页面" value="view_page" />
              <el-option label="算法测试" value="algorithm_test" />
            </el-select>
            <el-select v-model="filterRole" placeholder="选择角色" clearable size="small" style="width: 120px" @change="handleRoleChange">
              <el-option label="全部角色" value="" />
              <el-option label="管理员" value="管理员" />
              <el-option label="开发" value="开发" />
              <el-option label="测试" value="测试" />
              <el-option label="部署" value="部署" />
              <el-option label="飞控" value="飞控" />
              <el-option label="生产" value="生产" />
            </el-select>
            <el-select v-model="filterUser" placeholder="选择用户" clearable filterable size="small" style="width: 130px" :disabled="!filterRole && filteredUsersByRole.length === 0">
              <el-option label="全部用户" value="" />
              <el-option v-for="user in filteredUsersByRole" :key="user.userId" :label="user.userName" :value="user.userId" />
            </el-select>
            <el-date-picker
              v-model="filterDateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              size="small"
              style="width: 240px"
              :shortcuts="dateShortcuts"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              clearable
            />
            <el-button size="small" @click="resetFilters" :disabled="!hasActiveFilters">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </div>
        </div>
      </template>
      
      <el-timeline>
        <el-timeline-item
          v-for="log in filteredLogs"
          :key="log.id"
          :timestamp="formatTime(log.timestamp)"
          placement="top"
          :type="getActionType(log.action)"
        >
          <el-card shadow="hover" class="log-card">
            <div class="log-content">
              <div class="log-header">
                <el-tag size="small" :type="getActionType(log.action)">
                  {{ log.actionLabel }}
                </el-tag>
                <span class="log-user">{{ log.userName }}</span>
                <span class="log-location">📍 {{ log.ip }}</span>
              </div>
              <p class="log-details">{{ log.details }}</p>
              <span class="log-module">模块：{{ log.module }}</span>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>

      <div class="load-more" v-if="hasMoreLogs">
        <el-button @click="loadMoreLogs" :disabled="hasActiveFilters">
          加载更多
        </el-button>
        <span v-if="hasActiveFilters" class="load-hint">（请先清除筛选条件以加载全部）</span>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Download, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import activityLogApi from '@/api/activityLog'

const { t } = useI18n()

const userStats = ref([])
const overviewStats = ref({
  totalUsers: 0,
  activeUsers: 0,
  totalPosts: 0,
  totalComments: 0,
  totalLogins: 0,
  locationStats: {},
  actionStats: {}
})
const activityLogs = ref([])
const filterAction = ref('')
const filterUser = ref('')
const filterRole = ref('')
const filterDateRange = ref(null)
const currentPage = ref(1)
const pageSize = ref(10)
const totalLogs = ref(0)

// 根据角色筛选用户列表
const filteredUsersByRole = computed(() => {
  if (!filterRole.value) {
    return userStats.value
  }
  return userStats.value.filter(user => user.role === filterRole.value)
})

// 角色变更时重置用户选择
const handleRoleChange = () => {
  filterUser.value = ''
}

// 日期快捷选项
const dateShortcuts = [
  {
    text: '今天',
    value: () => {
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const tomorrow = new Date(today)
      tomorrow.setDate(tomorrow.getDate() + 1)
      return [today, tomorrow]
    }
  },
  {
    text: '最近3天',
    value: () => {
      const end = new Date()
      end.setHours(23, 59, 59, 999)
      const start = new Date()
      start.setDate(start.getDate() - 3)
      start.setHours(0, 0, 0, 0)
      return [start, end]
    }
  },
  {
    text: '最近7天',
    value: () => {
      const end = new Date()
      end.setHours(23, 59, 59, 999)
      const start = new Date()
      start.setDate(start.getDate() - 7)
      start.setHours(0, 0, 0, 0)
      return [start, end]
    }
  },
  {
    text: '最近30天',
    value: () => {
      const end = new Date()
      end.setHours(23, 59, 59, 999)
      const start = new Date()
      start.setDate(start.getDate() - 30)
      start.setHours(0, 0, 0, 0)
      return [start, end]
    }
  }
]

// 是否有激活的筛选条件
const hasActiveFilters = computed(() => {
  return filterAction.value !== '' || filterUser.value !== '' || filterRole.value !== '' || filterDateRange.value !== null
})

// 重置筛选条件
const resetFilters = () => {
  filterAction.value = ''
  filterUser.value = ''
  filterRole.value = ''
  filterDateRange.value = null
  currentPage.value = 1
  loadActivityLogs()
}

const filteredLogs = computed(() => {
  let logs = activityLogs.value

  if (filterAction.value) {
    logs = logs.filter(log => log.action === filterAction.value)
  }

  if (filterRole.value) {
    // 需要根据用户ID找到用户的角色进行筛选
    const usersInRole = userStats.value
      .filter(user => user.role === filterRole.value)
      .map(user => user.userId)
    logs = logs.filter(log => usersInRole.includes(log.userId))
  }

  if (filterUser.value) {
    logs = logs.filter(log => log.userId === filterUser.value)
  }

  if (filterDateRange.value && filterDateRange.value.length === 2) {
    const [startDate, endDate] = filterDateRange.value
    const start = new Date(startDate)
    start.setHours(0, 0, 0, 0)
    const end = new Date(endDate)
    end.setHours(23, 59, 59, 999)
    logs = logs.filter(log => {
      const logDate = new Date(log.timestamp)
      return logDate >= start && logDate <= end
    })
  }

  return logs
})

const hasMoreLogs = computed(() => {
  return activityLogs.value.length < totalLogs.value
})

const loadUserStats = async () => {
  try {
    const data = await activityLogApi.getUserStats()
    userStats.value = data
  } catch (error) {
    ElMessage.error(t('common.loadFailed') + ': ' + error.message)
  }
}

const loadOverviewStats = async () => {
  try {
    const data = await activityLogApi.getOverviewStats()
    overviewStats.value = data
  } catch (error) {
    ElMessage.error(t('common.loadFailed') + ': ' + error.message)
  }
}

const loadActivityLogs = async () => {
  try {
    const params = {
      page: currentPage.value,
      pageSize: pageSize.value
    }
    // 添加筛选参数
    if (filterAction.value) params.action = filterAction.value
    if (filterUser.value) params.userId = filterUser.value
    // 注意：角色筛选在前端进行，因为需要关联用户表
    if (filterDateRange.value && filterDateRange.value.length === 2) {
      params.startDate = filterDateRange.value[0]
      params.endDate = filterDateRange.value[1]
    }

    const result = await activityLogApi.getActivityLogs(params)
    activityLogs.value = result.list
    totalLogs.value = result.total
  } catch (error) {
    ElMessage.error(t('common.loadFailed') + ': ' + error.message)
  }
}

const loadMoreLogs = async () => {
  try {
    currentPage.value++
    const params = {
      page: currentPage.value,
      pageSize: pageSize.value
    }
    // 添加筛选参数
    if (filterAction.value) params.action = filterAction.value
    if (filterUser.value) params.userId = filterUser.value
    if (filterDateRange.value && filterDateRange.value.length === 2) {
      params.startDate = filterDateRange.value[0]
      params.endDate = filterDateRange.value[1]
    }
    
    const result = await activityLogApi.getActivityLogs(params)
    activityLogs.value = [...activityLogs.value, ...result.list]
  } catch (error) {
    ElMessage.error(t('common.loadFailed') + ': ' + error.message)
    currentPage.value--
  }
}

// 监听筛选条件变化，自动重新加载
watch([filterAction, filterUser, filterRole, filterDateRange], () => {
  currentPage.value = 1
  loadActivityLogs()
}, { deep: true })

const getRoleTagType = (role) => {
  const map = {
    '管理员': 'danger',
    '开发': 'primary',
    '测试': 'success',
    '部署': 'warning',
    '飞控': 'info',
    '生产': ''
  }
  return map[role] || ''
}

const getActionType = (action) => {
  const map = {
    'login': 'success',
    'create_post': 'primary',
    'comment': 'warning',
    'view_page': 'info',
    'algorithm_test': 'danger'
  }
  return map[action] || ''
}

const getActionPercentage = (count) => {
  const maxCount = Math.max(...Object.values(overviewStats.value.actionStats || {}))
  return maxCount > 0 ? Math.round((count / maxCount) * 100) : 0
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

const handleExport = async () => {
  try {
    // 导出用户统计
    const result = await activityLogApi.exportUserStats()
    
    // 转换为CSV格式
    const csvContent = [
      result.columns.map(col => col.label).join(','),
      ...result.data.map(row => Object.values(row).join(','))
    ].join('\n')

    // 创建下载
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `用户统计报表_${new Date().toISOString().slice(0, 10)}.csv`
    link.click()
    
    ElMessage.success('导出成功！')
  } catch (error) {
    ElMessage.error('导出失败：' + error.message)
  }
}

onMounted(async () => {
  await Promise.all([
    loadUserStats(),
    loadOverviewStats(),
    loadActivityLogs()
  ])
})
</script>

<style scoped>
.user-stats-container {
  padding: 20px;
}

.stats-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
}

.stats-overview {
  display: flex;
  justify-content: space-around;
  margin-bottom: 20px;
  padding: 20px 0;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.user-table {
  margin-top: 10px;
}

.action-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.action-label {
  width: 100px;
  font-size: 14px;
  color: #606266;
}

.action-item :deep(.el-progress) {
  flex: 1;
}

.location-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.location-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #f5f7fa;
  border-radius: 20px;
}

.location-name {
  font-size: 14px;
  color: #303133;
}

.log-card {
  margin: 0;
}

.log-content {
  padding: 8px 0;
}

.log-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.log-user {
  font-weight: 500;
  color: #303133;
}

.log-location {
  color: #909399;
  font-size: 12px;
}

.log-details {
  color: #606266;
  margin: 4px 0;
  font-size: 14px;
}

.log-module {
  font-size: 12px;
  color: #909399;
}

.load-more {
  text-align: center;
  margin-top: 20px;
}

.load-hint {
  display: block;
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

@media (max-width: 768px) {
  .stats-overview {
    flex-wrap: wrap;
    gap: 16px;
  }
  
  .stat-item {
    flex: 1 1 40%;
  }
}

/* ===== 暗色模式适配 ===== */
.is-dark .user-stats-container {
  background: var(--color-bg);
}

.is-dark .card-title {
  color: var(--color-text);
}

.is-dark .stats-overview {
  background: rgba(255, 255, 255, 0.05);
}

.is-dark .stat-value {
  color: var(--color-primary);
}

.is-dark .stat-label {
  color: var(--color-text-muted);
}

.is-dark .action-label {
  color: var(--color-text-muted);
}

.is-dark .location-item {
  background: rgba(255, 255, 255, 0.05);
}

.is-dark .location-name {
  color: var(--color-text);
}

.is-dark .log-card {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.08);
}

.is-dark .log-user {
  color: var(--color-text);
}

.is-dark .log-location {
  color: var(--color-text-muted);
}

.is-dark .log-details {
  color: var(--color-text-muted);
}

.is-dark .log-module {
  color: var(--color-text-muted);
}
</style>