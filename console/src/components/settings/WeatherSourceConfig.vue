<template>
  <div class="weather-source-config">
    <div class="section-header">
      <h3 class="section-title">气象数据源配置</h3>
      <el-button type="primary" size="small" @click="handleRefresh" :loading="loading">
        刷新列表
      </el-button>
    </div>

    <!-- 未配置数据源警告 -->
    <el-alert
      v-if="hasUnconfiguredSources"
      type="warning"
      :closable="false"
      show-icon
      style="margin-bottom: 16px"
    >
      <template #title>
        以下数据源尚未配置API密钥，将在获取权限后自动启用：
        <el-tag
          v-for="s in unconfiguredSources"
          :key="s.sourceType"
          size="small"
          type="warning"
          effect="plain"
          style="margin-left: 4px"
        >
          {{ s.name }}
        </el-tag>
      </template>
    </el-alert>

    <!-- 离线数据源警告 -->
    <el-alert
      v-if="hasOfflineSources"
      type="error"
      :closable="false"
      show-icon
      style="margin-bottom: 16px"
    >
      <template #title>
        以下数据源当前离线，请检查网络连接或联系管理员：
        <el-tag
          v-for="s in offlineSources"
          :key="s.sourceType"
          size="small"
          type="danger"
          effect="plain"
          style="margin-left: 4px"
        >
          {{ s.name }}
        </el-tag>
      </template>
    </el-alert>

    <!-- 数据源列表 -->
    <el-table
      :data="sources"
      stripe
      style="width: 100%"
      v-loading="loading"
      row-key="sourceType"
    >
      <el-table-column prop="name" label="数据源" width="140" fixed>
        <template #default="{ row }">
          <div class="source-name">
            <span class="source-name__text">{{ row.name }}</span>
            <el-tooltip :content="getSourceDescription(row.sourceType)" placement="top">
              <el-icon class="source-name__icon"><el-icon-info-filled /></el-icon>
            </el-tooltip>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="sourceType" label="类型" width="100">
        <template #default="{ row }">
          <el-tag size="small" effect="plain">{{ row.sourceType }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="resolution" label="分辨率" width="90" align="center">
        <template #default="{ row }">
          <span class="mono-value">{{ row.resolution }}°</span>
        </template>
      </el-table-column>
      <el-table-column prop="forecastHours" label="预报时效" width="100" align="center">
        <template #default="{ row }">
          <span class="mono-value">{{ row.forecastHours }}h</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="120" align="center">
        <template #default="{ row }">
          <div class="source-status">
            <span
              class="status-indicator"
              :class="getStatusClass(row)"
            ></span>
            <span class="status-text">{{ getStatusLabel(row) }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="启用" width="80" align="center">
        <template #default="{ row }">
          <el-switch
            v-model="row.enabled"
            :disabled="isSourceDisabled(row)"
            size="small"
            @change="handleToggle(row)"
          />
        </template>
      </el-table-column>
      <el-table-column label="优先级" width="130" align="center">
        <template #default="{ row }">
          <div class="priority-control">
            <el-button
              size="small"
              :icon="Top"
              :disabled="row.priority <= 1"
              @click="handleMovePriority(row, 'up')"
              circle
              plain
            />
            <span class="priority-value">{{ row.priority }}</span>
            <el-button
              size="small"
              :icon="Bottom"
              :disabled="row.priority >= sources.length"
              @click="handleMovePriority(row, 'down')"
              circle
              plain
            />
          </div>
        </template>
      </el-table-column>
      <el-table-column label="最后更新" width="160">
        <template #default="{ row }">
          <span class="mono-value">{{ getLastUpdate(row) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button
            size="small"
            type="primary"
            plain
            @click="handleTest(row)"
            :loading="testing[row.sourceType]"
          >
            测试连接
          </el-button>
          <el-button
            v-if="isConfigurable(row)"
            size="small"
            type="warning"
            plain
            @click="openConfigDialog(row)"
          >
            配置
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 优先级说明 -->
    <div class="priority-legend">
      <el-icon><el-icon-info-filled /></el-icon>
      <span>优先级数值越小，优先级越高。系统按优先级顺序获取气象数据。</span>
    </div>

    <!-- 风雷API配置弹窗 -->
    <el-dialog
      v-model="fengleiDialogVisible"
      title="风雷API配置"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      >
        <template #title>
          风雷气象提供高分辨率区域数值天气预报数据，需申请API密钥后使用。
        </template>
      </el-alert>
      <el-form
        ref="fengleiFormRef"
        :model="fengleiConfig"
        :rules="apiConfigRules"
        label-width="120px"
      >
        <el-form-item label="API地址" prop="apiEndpoint">
          <el-input
            v-model="fengleiConfig.apiEndpoint"
            placeholder="https://api.fenglei.com/v1"
          />
        </el-form-item>
        <el-form-item label="API密钥" prop="apiKey">
          <el-input
            v-model="fengleiConfig.apiKey"
            type="password"
            show-password
            placeholder="请输入风雷API密钥"
          />
        </el-form-item>
        <el-form-item label="备用密钥">
          <el-input
            v-model="fengleiConfig.backupKey"
            type="password"
            show-password
            placeholder="可选，用于主密钥失效时切换"
          />
        </el-form-item>
        <el-form-item label="请求超时">
          <el-input-number
            v-model="fengleiConfig.timeout"
            :min="5"
            :max="60"
            :step="5"
            style="width: 100%"
          />
          <span class="form-hint">单位：秒</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="fengleiDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveFengleiConfig" :loading="saving">
          保存配置
        </el-button>
      </template>
    </el-dialog>

    <!-- 天资API配置弹窗 -->
    <el-dialog
      v-model="tianziDialogVisible"
      title="天资API配置"
      width="520px"
      :close-on-click-modal="false"
    >
      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      >
        <template #title>
          天资气象提供全球GFS/ECMWF再分析数据及预报产品。
        </template>
      </el-alert>
      <el-form
        ref="tianziFormRef"
        :model="tianziConfig"
        :rules="apiConfigRules"
        label-width="120px"
      >
        <el-form-item label="API地址" prop="apiEndpoint">
          <el-input
            v-model="tianziConfig.apiEndpoint"
            placeholder="https://api.tianzi.com/v1"
          />
        </el-form-item>
        <el-form-item label="API密钥" prop="apiKey">
          <el-input
            v-model="tianziConfig.apiKey"
            type="password"
            show-password
            placeholder="请输入天资API密钥"
          />
        </el-form-item>
        <el-form-item label="备用密钥">
          <el-input
            v-model="tianziConfig.backupKey"
            type="password"
            show-password
            placeholder="可选，用于主密钥失效时切换"
          />
        </el-form-item>
        <el-form-item label="请求超时">
          <el-input-number
            v-model="tianziConfig.timeout"
            :min="5"
            :max="60"
            :step="5"
            style="width: 100%"
          />
          <span class="form-hint">单位：秒</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="tianziDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveTianziConfig" :loading="saving">
          保存配置
        </el-button>
      </template>
    </el-dialog>

    <!-- WRF服务器配置弹窗 -->
    <el-dialog
      v-model="wrfDialogVisible"
      title="WRF服务器配置"
      width="640px"
      :close-on-click-modal="false"
    >
      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      >
        <template #title>
          配置远程 WRF 数值模式计算服务器的 SSH 连接和 WRF 安装路径。
        </template>
      </el-alert>
      <el-form
        ref="wrfFormRef"
        :model="wrfConfig"
        :rules="wrfConfigRules"
        label-width="140px"
      >
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="服务器地址" prop="host">
              <el-input v-model="wrfConfig.host" placeholder="wrf-server.example.com" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="SSH端口" prop="port">
              <el-input-number v-model="wrfConfig.port" :min="1" :max="65535" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="wrfConfig.username" placeholder="wrf_user" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="认证方式" prop="authType">
              <el-select v-model="wrfConfig.authType" style="width: 100%">
                <el-option label="密码认证" value="password" />
                <el-option label="SSH密钥" value="sshkey" />
                <el-option label="Kerberos" value="kerberos" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item v-if="wrfConfig.authType === 'password'" label="密码" prop="password">
              <el-input v-model="wrfConfig.password" type="password" show-password placeholder="输入密码" />
            </el-form-item>
            <el-form-item v-else-if="wrfConfig.authType === 'sshkey'" label="SSH密钥路径" prop="sshKeyPath">
              <el-input v-model="wrfConfig.sshKeyPath" placeholder="~/.ssh/id_rsa" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="WRF安装路径" prop="wrfPath">
              <el-input v-model="wrfConfig.wrfPath" placeholder="/home/wrf/WRFV4" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="24">
          <el-col :span="12">
            <el-form-item label="WPS路径" prop="wpsPath">
              <el-input v-model="wrfConfig.wpsPath" placeholder="/home/wrf/WPS" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="输出路径" prop="outputPath">
              <el-input v-model="wrfConfig.outputPath" placeholder="/home/wrf/output" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="wrfDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveWrfConfig" :loading="saving">
          保存配置
        </el-button>
      </template>
    </el-dialog>

    <!-- 测试结果弹窗 -->
    <el-dialog
      v-model="testResultVisible"
      title="连接测试结果"
      width="480px"
    >
      <div v-if="testResult" class="test-result">
        <div class="test-result__status">
          <el-icon
            :size="32"
            :color="testResult.success ? 'var(--color-success, #4caf50)' : 'var(--color-danger, #ef5350)'"
          >
            <el-icon-circle-check v-if="testResult.success" />
            <el-icon-circle-close v-else />
          </el-icon>
          <span :class="testResult.success ? 'text-success' : 'text-danger'">
            {{ testResult.message }}
          </span>
        </div>
        <el-descriptions v-if="testResult.details" :column="1" border size="small" style="margin-top: 16px">
          <el-descriptions-item label="响应时间">{{ testResult.details.latency }}ms</el-descriptions-item>
          <el-descriptions-item label="数据版本">{{ testResult.details.version }}</el-descriptions-item>
          <el-descriptions-item label="可用预报时效">{{ testResult.details.availableHours }}h</el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="testResultVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Top, Bottom } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { weatherSourceApi, type WeatherSource } from '@/api/weather-source'

// ---- 状态 ----
const sources = ref<WeatherSource[]>([])
const sourceStatuses = ref<Record<string, { status: string; lastUpdate: string }>>({})
const testing = ref<Record<string, boolean>>({})
const loading = ref(false)
const saving = ref(false)

// ---- 弹窗状态 ----
const fengleiDialogVisible = ref(false)
const tianziDialogVisible = ref(false)
const testResultVisible = ref(false)
const testResult = ref<{ success: boolean; message: string; details?: any } | null>(null)

// ---- 表单引用 ----
const fengleiFormRef = ref<FormInstance>()
const tianziFormRef = ref<FormInstance>()
const wrfDialogVisible = ref(false)
const wrfFormRef = ref<FormInstance>()

// ---- 配置表单 ----
const fengleiConfig = reactive({
  apiEndpoint: '',
  apiKey: '',
  backupKey: '',
  timeout: 30,
})

const tianziConfig = reactive({
  apiEndpoint: '',
  apiKey: '',
  backupKey: '',
  timeout: 30,
})

const wrfConfig = reactive({
  host: '',
  port: 22,
  username: '',
  authType: 'password' as 'password' | 'sshkey' | 'kerberos',
  password: '',
  sshKeyPath: '',
  wrfPath: '',
  wpsPath: '',
  outputPath: '',
})

const wrfConfigRules = reactive<FormRules>({
  host: [{ required: true, message: '请输入服务器地址', trigger: 'blur' }],
  port: [{ required: true, message: '请输入端口号', trigger: 'blur' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  authType: [{ required: true, message: '请选择认证方式', trigger: 'change' }],
  wrfPath: [{ required: true, message: '请输入WRF安装路径', trigger: 'blur' }],
})

const apiConfigRules = reactive<FormRules>({
  apiEndpoint: [
    { required: true, message: '请输入API地址', trigger: 'blur' },
    { type: 'url', message: '请输入有效的URL地址', trigger: 'blur' },
  ],
  apiKey: [
    { required: true, message: '请输入API密钥', trigger: 'blur' },
    { min: 16, message: 'API密钥长度不少于16位', trigger: 'blur' },
  ],
})

// ---- 计算属性 ----
const unconfiguredSources = computed(() =>
  sources.value.filter(s => ['fenglei', 'tianzi'].includes(s.sourceType) && !s.config?.apiKey)
)

const hasUnconfiguredSources = computed(() => unconfiguredSources.value.length > 0)

const offlineSources = computed(() =>
  sources.value.filter(s => {
    const status = sourceStatuses.value[s.sourceType]
    return status && status.status === 'offline'
  })
)

const hasOfflineSources = computed(() => offlineSources.value.length > 0)

// ---- 数据源描述 ----
function getSourceDescription(sourceType: string): string {
  const descriptions: Record<string, string> = {
    fenglei: '风雷气象 — 高分辨率区域数值天气预报',
    tianzi: '天资气象 — 全球GFS/ECMWF再分析数据',
    ecmwf: 'ECMWF — 欧洲中期天气预报中心',
    gfs: 'GFS — 美国全球预报系统',
    wrf: 'WRF — 中尺度数值天气预报模式',
  }
  return descriptions[sourceType] || '气象数据源'
}

// ---- 状态相关 ----
function getStatusClass(row: WeatherSource): string {
  if (!row.enabled) return 'status-indicator--disabled'
  const status = sourceStatuses.value[row.sourceType]?.status
  if (status === 'online') return 'status-indicator--online'
  if (status === 'offline') return 'status-indicator--offline'
  return 'status-indicator--unknown'
}

function getStatusLabel(row: WeatherSource): string {
  if (!row.enabled) return '已禁用'
  const status = sourceStatuses.value[row.sourceType]?.status
  if (status === 'online') return '在线'
  if (status === 'offline') return '离线'
  return '未配置'
}

function getLastUpdate(row: WeatherSource): string {
  const status = sourceStatuses.value[row.sourceType]
  return status?.lastUpdate || '--'
}

// ---- 判断 ----
function isSourceDisabled(row: WeatherSource): boolean {
  if (['fenglei', 'tianzi'].includes(row.sourceType)) {
    return !row.config?.apiKey
  }
  return false
}

function isConfigurable(row: WeatherSource): boolean {
  return ['fenglei', 'tianzi', 'wrf'].includes(row.sourceType)
}

// ---- 加载数据 ----
async function loadSources() {
  loading.value = true
  try {
    sources.value = await weatherSourceApi.list()
  } catch {
    ElMessage.error('加载数据源配置失败')
  } finally {
    loading.value = false
  }
}

async function loadStatuses() {
  try {
    sourceStatuses.value = await weatherSourceApi.getStatus()
  } catch {
    // 静默处理
  }
}

async function handleRefresh() {
  await Promise.all([loadSources(), loadStatuses()])
  ElMessage.success('已刷新')
}

// ---- 启用/禁用 ----
async function handleToggle(row: WeatherSource) {
  try {
    await weatherSourceApi.update(row.sourceType, { enabled: row.enabled })
    ElMessage.success(`${row.name} 已${row.enabled ? '启用' : '禁用'}`)
  } catch {
    row.enabled = !row.enabled
    ElMessage.error('更新失败')
  }
}

// ---- 优先级调整 ----
async function handleMovePriority(row: WeatherSource, direction: 'up' | 'down') {
  const delta = direction === 'up' ? -1 : 1
  const newPriority = row.priority + delta
  if (newPriority < 1 || newPriority > sources.value.length) return

  // 找到被交换的数据源
  const swapSource = sources.value.find(s => s.priority === newPriority)
  if (swapSource) {
    try {
      await weatherSourceApi.update(row.sourceType, { priority: newPriority })
      await weatherSourceApi.update(swapSource.sourceType, { priority: row.priority })
      swapSource.priority = row.priority
      row.priority = newPriority
      ElMessage.success('优先级已调整')
    } catch {
      ElMessage.error('优先级调整失败')
    }
  }
}

// ---- 测试连接 ----
async function handleTest(row: WeatherSource) {
  testing.value[row.sourceType] = true
  try {
    const result = await weatherSourceApi.testConnection(row.sourceType)
    testResult.value = result
    testResultVisible.value = true
  } catch {
    testResult.value = { success: false, message: '连接测试失败' }
    testResultVisible.value = true
  } finally {
    testing.value[row.sourceType] = false
  }
}

// ---- 配置弹窗 ----
function openConfigDialog(row: WeatherSource) {
  if (row.sourceType === 'fenglei') {
    fengleiConfig.apiEndpoint = (row.config?.apiEndpoint as string) || ''
    fengleiConfig.apiKey = (row.config?.apiKey as string) || ''
    fengleiConfig.backupKey = (row.config?.backupKey as string) || ''
    fengleiConfig.timeout = (row.config?.timeout as number) || 30
    fengleiDialogVisible.value = true
  } else if (row.sourceType === 'tianzi') {
    tianziConfig.apiEndpoint = (row.config?.apiEndpoint as string) || ''
    tianziConfig.apiKey = (row.config?.apiKey as string) || ''
    tianziConfig.backupKey = (row.config?.backupKey as string) || ''
    tianziConfig.timeout = (row.config?.timeout as number) || 30
    tianziDialogVisible.value = true
  } else if (row.sourceType === 'wrf') {
    wrfConfig.host = (row.config?.host as string) || ''
    wrfConfig.port = (row.config?.port as number) || 22
    wrfConfig.username = (row.config?.username as string) || ''
    wrfConfig.authType = (row.config?.authType as any) || 'password'
    wrfConfig.password = (row.config?.password as string) || ''
    wrfConfig.sshKeyPath = (row.config?.sshKeyPath as string) || ''
    wrfConfig.wrfPath = (row.config?.wrfPath as string) || ''
    wrfConfig.wpsPath = (row.config?.wpsPath as string) || ''
    wrfConfig.outputPath = (row.config?.outputPath as string) || ''
    wrfDialogVisible.value = true
  }
}

async function saveFengleiConfig() {
  if (!fengleiFormRef.value) return
  try {
    await fengleiFormRef.value.validate()
    saving.value = true
    await weatherSourceApi.update('fenglei', {
      config: { ...fengleiConfig },
    })
    fengleiDialogVisible.value = false
    ElMessage.success('风雷API配置已保存')
    await loadSources()
  } catch (e) {
    if (e !== false) {
      ElMessage.error('保存失败')
    }
  } finally {
    saving.value = false
  }
}

async function saveTianziConfig() {
  if (!tianziFormRef.value) return
  try {
    await tianziFormRef.value.validate()
    saving.value = true
    await weatherSourceApi.update('tianzi', {
      config: { ...tianziConfig },
    })
    tianziDialogVisible.value = false
    ElMessage.success('天资API配置已保存')
    await loadSources()
  } catch (e) {
    if (e !== false) {
      ElMessage.error('保存失败')
    }
  } finally {
    saving.value = false
  }
}

async function saveWrfConfig() {
  if (!wrfFormRef.value) return
  try {
    await wrfFormRef.value.validate()
    saving.value = true
    await weatherSourceApi.update('wrf', {
      config: { ...wrfConfig },
    })
    wrfDialogVisible.value = false
    ElMessage.success('WRF服务器配置已保存')
    await loadSources()
  } catch (e) {
    if (e !== false) {
      ElMessage.error('保存失败')
    }
  } finally {
    saving.value = false
  }
}

// ---- 初始化 ----
onMounted(() => {
  loadSources()
  loadStatuses()
})
</script>

<style scoped>
.weather-source-config {
  padding: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary, #e0e0e0);
  margin: 0;
}

.source-name {
  display: flex;
  align-items: center;
  gap: 4px;
}

.source-name__icon {
  color: var(--color-text-muted, #6a6a80);
  cursor: help;
}

.source-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-indicator--online {
  background: var(--color-success, #4caf50);
  box-shadow: 0 0 6px var(--color-success, #4caf50);
}

.status-indicator--offline {
  background: var(--color-danger, #ef5350);
  box-shadow: 0 0 6px var(--color-danger, #ef5350);
}

.status-indicator--unknown {
  background: var(--color-text-muted, #6a6a80);
}

.status-indicator--disabled {
  background: var(--color-text-muted, #6a6a80);
  opacity: 0.5;
}

.status-text {
  font-size: 12px;
  color: var(--color-text-secondary, #a0a0b0);
}

.mono-value {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: var(--color-text-primary, #e0e0e0);
}

.priority-control {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.priority-value {
  display: inline-block;
  width: 24px;
  text-align: center;
  font-weight: 600;
  font-size: 14px;
  color: var(--color-primary, #4fc3f7);
}

.priority-legend {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 12px;
  font-size: 12px;
  color: var(--color-text-muted, #6a6a80);
}

.form-hint {
  font-size: 12px;
  color: var(--color-text-muted, #6a6a80);
  margin-left: 8px;
}

.test-result__status {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
}

.text-success {
  color: var(--color-success, #4caf50);
}

.text-danger {
  color: var(--color-danger, #ef5350);
}

:deep(.el-table) {
  --el-table-bg-color: var(--color-bg-card, #1a1a2e);
  --el-table-tr-bg-color: var(--color-bg-card, #1a1a2e);
  --el-table-header-bg-color: var(--color-bg-secondary, #12121f);
  --el-table-border-color: var(--color-border, #2a2a40);
  --el-table-text-color: var(--color-text-primary, #e0e0e0);
  --el-table-header-text-color: var(--color-text-secondary, #a0a0b0);
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

:deep(.el-dialog) {
  --el-dialog-bg-color: var(--color-bg-card, #1a1a2e);
  --el-dialog-title-font-size: 16px;
}

:deep(.el-dialog__header) {
  color: var(--color-text-primary, #e0e0e0);
  border-bottom: 1px solid var(--color-border, #2a2a40);
}

:deep(.el-dialog__body) {
  color: var(--color-text-primary, #e0e0e0);
}
</style>
