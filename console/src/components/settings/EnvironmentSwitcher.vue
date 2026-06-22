<template>
  <div class="environment-switcher">
    <!-- 当前环境指示器 -->
    <div class="env-indicator">
      <div class="env-indicator__label">当前运行环境</div>
      <div class="env-indicator__badge">
        <span
          class="env-dot"
          :class="`env-dot--${currentEnv.type}`"
        ></span>
        <span class="env-name">{{ currentEnv.label }}</span>
        <el-tag :type="currentEnv.tagType" size="small" effect="dark">
          {{ currentEnv.tagLabel }}
        </el-tag>
      </div>
    </div>

    <!-- 环境切换（仅管理员） -->
    <el-card shadow="never" class="env-card">
      <template #header>
        <div class="card-header">
          <span>环境切换</span>
          <el-tag v-if="!isAdmin" type="warning" size="small" effect="plain">
            仅管理员可操作
          </el-tag>
        </div>
      </template>
      <el-radio-group
        v-model="targetEnv"
        :disabled="!isAdmin || switching"
        @change="handleEnvSwitch"
        class="env-radio-group"
      >
        <el-radio-button
          v-for="env in environmentList"
          :key="env.value"
          :value="env.value"
          :class="{ 'is-current': currentEnv.value === env.value }"
        >
          <span class="radio-dot" :style="{ background: env.color }"></span>
          {{ env.label }}
        </el-radio-button>
      </el-radio-group>
      <div v-if="switching" class="switching-hint">
        <el-icon class="is-loading"><el-icon-loading /></el-icon>
        正在切换环境，请稍候...
      </div>
    </el-card>

    <!-- 环境配置信息 -->
    <el-card shadow="never" class="env-card">
      <template #header>
        <div class="card-header">
          <span>环境配置信息</span>
          <el-button size="small" @click="handleRefreshStatus" :loading="refreshing">
            刷新状态
          </el-button>
        </div>
      </template>
      <el-descriptions :column="2" border size="default">
        <el-descriptions-item label="API地址">
          <span class="config-value">{{ envConfig.apiBaseUrl || '--' }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="数据库">
          <div class="connection-status">
            <span
              class="status-dot"
              :class="`status-dot--${envConfig.dbStatus}`"
            ></span>
            <span>{{ envConfig.dbHost || '--' }}:{{ envConfig.dbPort || '--' }}</span>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="Kafka">
          <div class="connection-status">
            <span
              class="status-dot"
              :class="`status-dot--${envConfig.kafkaStatus}`"
            ></span>
            <span>{{ envConfig.kafkaHost || '--' }}:{{ envConfig.kafkaPort || '--' }}</span>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="Redis">
          <div class="connection-status">
            <span
              class="status-dot"
              :class="`status-dot--${envConfig.redisStatus}`"
            ></span>
            <span>{{ envConfig.redisHost || '--' }}:{{ envConfig.redisPort || '--' }}</span>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="WRF计算节点">
          <div class="connection-status">
            <span
              class="status-dot"
              :class="`status-dot--${envConfig.wrfStatus}`"
            ></span>
            <span>{{ envConfig.wrfHost || '未配置' }}</span>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="数据版本">
          <span class="config-value">{{ envConfig.dataVersion || '--' }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 功能差异提示 -->
    <el-card shadow="never" class="env-card">
      <template #header>
        <span>功能可用性对比</span>
      </template>
      <el-table :data="featureComparison" stripe style="width: 100%">
        <el-table-column prop="feature" label="功能模块" width="200" />
        <el-table-column
          v-for="env in environmentList"
          :key="env.value"
          :label="env.label"
          :prop="env.value"
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <el-icon v-if="row[env.value]" color="var(--color-success, #4caf50)">
              <el-icon-check />
            </el-icon>
            <el-icon v-else color="var(--color-text-muted, #6a6a80)">
              <el-icon-close />
            </el-icon>
          </template>
        </el-table-column>
      </el-table>
      <el-alert
        v-if="currentEnv.value === 'development'"
        type="info"
        :closable="false"
        show-icon
        style="margin-top: 12px"
      >
        <template #title>
          开发环境使用模拟数据，部分高级功能（如WRF实时计算、数据同化）不可用
        </template>
      </el-alert>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { get } from '@/api/request'

// ---- 环境定义 ----
const environmentList = [
  { value: 'development', label: '开发', color: '#4fc3f7', tagType: 'info' as const, tagLabel: 'DEV' },
  { value: 'testing', label: '测试', color: '#ffb74d', tagType: 'warning' as const, tagLabel: 'TEST' },
  { value: 'staging', label: '预发布', color: '#ba68c8', tagType: 'warning' as const, tagLabel: 'STAGING' },
  { value: 'production', label: '生产', color: '#ef5350', tagType: 'danger' as const, tagLabel: 'PROD' },
]

interface EnvironmentInfo {
  value: string
  label: string
  type: string
  color: string
  tagType: 'info' | 'warning' | 'danger' | 'success'
  tagLabel: string
}

const currentEnv = ref<EnvironmentInfo>({
  value: 'development',
  label: '开发',
  type: 'development',
  color: '#4fc3f7',
  tagType: 'info',
  tagLabel: 'DEV',
})

const targetEnv = ref('development')
const switching = ref(false)
const refreshing = ref(false)
const isAdmin = ref(false)

// ---- 环境配置 ----
const envConfig = reactive({
  apiBaseUrl: '',
  dbHost: '',
  dbPort: '',
  dbStatus: 'unknown' as 'connected' | 'disconnected' | 'unknown',
  kafkaHost: '',
  kafkaPort: '',
  kafkaStatus: 'unknown' as 'connected' | 'disconnected' | 'unknown',
  redisHost: '',
  redisPort: '',
  redisStatus: 'unknown' as 'connected' | 'disconnected' | 'unknown',
  wrfHost: '',
  wrfStatus: 'unknown' as 'connected' | 'disconnected' | 'unknown',
  dataVersion: '',
})

// ---- 功能对比 ----
const featureComparison = ref([
  { feature: '实时气象数据', development: true, testing: true, staging: true, production: true },
  { feature: 'WRF数值模拟', development: false, testing: true, staging: true, production: true },
  { feature: '数据同化', development: false, testing: false, staging: true, production: true },
  { feature: '航线规划', development: true, testing: true, staging: true, production: true },
  { feature: '风险评估', development: true, testing: true, staging: true, production: true },
  { feature: '历史数据回放', development: false, testing: true, staging: true, production: true },
  { feature: '多租户管理', development: false, testing: false, staging: true, production: true },
  { feature: 'API密钥管理', development: true, testing: true, staging: true, production: true },
])

// ---- 方法 ----
async function fetchEnvironment() {
  try {
    const data = await get<any>('/v1/system/environment')
    const envItem = environmentList.find(e => e.value === data.environment)
    if (envItem) {
      currentEnv.value = { ...currentEnv.value, ...envItem, type: envItem.value }
      targetEnv.value = data.environment
    }
    isAdmin.value = data.isAdmin || false
    // 填充配置信息
    if (data.config) {
      Object.assign(envConfig, data.config)
    }
  } catch {
    // 使用默认开发环境
    currentEnv.value = { ...currentEnv.value }
    targetEnv.value = 'development'
    envConfig.apiBaseUrl = 'http://localhost:8080'
    envConfig.dbHost = 'localhost'
    envConfig.dbPort = '5432'
    envConfig.dbStatus = 'connected'
    envConfig.redisHost = 'localhost'
    envConfig.redisPort = '6379'
    envConfig.redisStatus = 'connected'
    envConfig.kafkaHost = 'localhost'
    envConfig.kafkaPort = '9092'
    envConfig.kafkaStatus = 'disconnected'
    envConfig.dataVersion = 'v2.1.0-dev'
  }
}

async function handleEnvSwitch(env: string) {
  if (env === currentEnv.value.value) return

  const envLabel = environmentList.find(e => e.value === env)?.label || env
  try {
    await ElMessageBox.confirm(
      `确定切换到${envLabel}环境吗？切换后页面将重新加载。`,
      '环境切换确认',
      { type: 'warning', confirmButtonText: '确定切换', cancelButtonText: '取消' }
    )

    switching.value = true
    try {
      await post('/v1/system/environment/switch', { target: env })
      ElMessage.success(`正在切换到${envLabel}环境...`)
      setTimeout(() => window.location.reload(), 1500)
    } catch {
      targetEnv.value = currentEnv.value.value
      ElMessage.error('环境切换失败')
    }
  } catch {
    targetEnv.value = currentEnv.value.value
  } finally {
    switching.value = false
  }
}

async function handleRefreshStatus() {
  refreshing.value = true
  try {
    const data = await get<any>('/v1/system/environment/status')
    if (data.connections) {
      envConfig.dbStatus = data.connections.db || 'unknown'
      envConfig.kafkaStatus = data.connections.kafka || 'unknown'
      envConfig.redisStatus = data.connections.redis || 'unknown'
      envConfig.wrfStatus = data.connections.wrf || 'unknown'
    }
    ElMessage.success('状态已刷新')
  } catch {
    ElMessage.error('获取状态失败')
  } finally {
    refreshing.value = false
  }
}

// 导入post方法
import { post } from '@/api/request'

onMounted(fetchEnvironment)
</script>

<style scoped>
.environment-switcher {
  padding: 16px;
}

.env-indicator {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: var(--color-bg-card, #1a1a2e);
  border: 1px solid var(--color-border, #2a2a40);
  border-radius: 8px;
}

.env-indicator__label {
  font-size: 14px;
  color: var(--color-text-secondary, #a0a0b0);
}

.env-indicator__badge {
  display: flex;
  align-items: center;
  gap: 8px;
}

.env-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

.env-dot--development { background: #4fc3f7; }
.env-dot--testing { background: #ffb74d; }
.env-dot--staging { background: #ba68c8; }
.env-dot--production { background: #ef5350; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.env-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary, #e0e0e0);
}

.env-card {
  margin-bottom: 16px;
  background: var(--color-bg-card, #1a1a2e);
  border-color: var(--color-border, #2a2a40);
}

.env-card :deep(.el-card__header) {
  border-bottom-color: var(--color-border, #2a2a40);
  color: var(--color-text-primary, #e0e0e0);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.env-radio-group {
  display: flex;
  width: 100%;
}

.env-radio-group .el-radio-button {
  flex: 1;
}

.radio-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}

.switching-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  font-size: 13px;
  color: var(--color-text-secondary, #a0a0b0);
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot--connected { background: var(--color-success, #4caf50); }
.status-dot--disconnected { background: var(--color-danger, #ef5350); }
.status-dot--unknown { background: var(--color-text-muted, #6a6a80); }

.config-value {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: var(--color-text-primary, #e0e0e0);
}

:deep(.el-descriptions) {
  --el-descriptions-bg-color: var(--color-bg-card, #1a1a2e);
  --el-descriptions-table-border: var(--color-border, #2a2a40);
}

:deep(.el-descriptions__label) {
  color: var(--color-text-secondary, #a0a0b0) !important;
  background: var(--color-bg-secondary, #12121f) !important;
}

:deep(.el-descriptions__content) {
  color: var(--color-text-primary, #e0e0e0) !important;
}

:deep(.el-table) {
  --el-table-bg-color: var(--color-bg-card, #1a1a2e);
  --el-table-tr-bg-color: var(--color-bg-card, #1a1a2e);
  --el-table-header-bg-color: var(--color-bg-secondary, #12121f);
  --el-table-border-color: var(--color-border, #2a2a40);
  --el-table-text-color: var(--color-text-primary, #e0e0e0);
  --el-table-header-text-color: var(--color-text-secondary, #a0a0b0);
}
</style>
