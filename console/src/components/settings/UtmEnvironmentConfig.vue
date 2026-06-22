<template>
  <div class="utm-environment-config">
    <h3>UTM 双环境配置</h3>
    
    <!-- 当前状态卡片 -->
    <el-row :gutter="16" class="status-cards">
      <el-col :span="8">
        <el-card :body-style="{ padding: '20px' }" :class="['mode-card', currentMode]">
          <div class="mode-icon">
            <el-icon size="32"><Monitor v-if="currentMode === 'MOCK'" /><Connection v-else-if="currentMode === 'EXTERNAL'" /><Switch v-else /></el-icon>
          </div>
          <div class="mode-info">
            <div class="mode-label">当前模式</div>
            <div class="mode-value">{{ modeLabel }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card :body-style="{ padding: '20px' }">
          <div class="mode-info">
            <div class="mode-label">模拟适配器</div>
            <div class="mode-value">
              <el-tag :type="config.mockEnabled ? 'success' : 'info'">
                {{ config.mockEnabled ? '启用' : '禁用' }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card :body-style="{ padding: '20px' }">
          <div class="mode-info">
            <div class="mode-label">外部UTM</div>
            <div class="mode-value">
              <el-tag :type="config.externalUtmEnabled ? 'success' : 'info'">
                {{ config.externalUtmEnabled ? '启用' : '禁用' }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 模式切换 -->
    <el-card class="switch-card">
      <template #header>
        <span>模式切换</span>
      </template>
      
      <el-radio-group v-model="selectedMode" size="large">
        <el-radio-button label="MOCK">
          <el-icon><Monitor /></el-icon>
          模拟模式
        </el-radio-button>
        <el-radio-button label="HYBRID">
          <el-icon><Switch /></el-icon>
          混合模式
        </el-radio-button>
        <el-radio-button label="EXTERNAL">
          <el-icon><Connection /></el-icon>
          真实模式
        </el-radio-button>
      </el-radio-group>
      
      <div class="mode-description">
        <el-alert
          :type="modeAlertType"
          :title="modeAlertTitle"
          :description="modeAlertDescription"
          show-icon
          :closable="false"
        />
      </div>
      
      <el-button
        type="primary"
        size="large"
        :loading="switching"
        :disabled="selectedMode === currentMode"
        @click="handleSwitchMode"
      >
        切换模式
      </el-button>
    </el-card>
    
    <!-- 外部UTM配置 -->
    <el-card class="external-config-card">
      <template #header>
        <span>外部UTM配置</span>
        <el-tag v-if="config.externalUtmEnabled" type="success" size="small">已启用</el-tag>
      </template>
      
      <el-form label-width="120px">
        <el-form-item label="服务地址">
          <el-input v-model="config.externalUtmBaseUrl" readonly />
        </el-form-item>
        <el-form-item label="API密钥">
          <el-input v-model="config.externalUtmApiKey" readonly />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :loading="testing"
            :disabled="!config.externalUtmEnabled"
            @click="handleTestConnection"
          >
            测试连接
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 环境说明 -->
    <el-card class="info-card">
      <template #header>
        <span>环境说明</span>
      </template>
      <el-timeline>
        <el-timeline-item type="success">
          <h4>开发/测试环境</h4>
          <p>使用模拟模式（MOCK），所有UTM操作返回模拟数据，不连接外部系统。适合快速调试空域申请、冲突消解逻辑。</p>
        </el-timeline-item>
        <el-timeline-item type="warning">
          <h4>灰度/准生产环境</h4>
          <p>使用混合模式（HYBRID）或真实模式（EXTERNAL），启用真实外部UTM对接，验证双向空域申请、冲突实时同步、熔断降级全流程。</p>
        </el-timeline-item>
        <el-timeline-item type="danger">
          <h4>生产环境</h4>
          <p>必须使用真实模式（EXTERNAL），所有飞行计划提交到真实UTM系统审批，位置实时上报，告警实时接收。</p>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { utmEnvironmentApi, type UtmEnvironmentConfig } from '@/api/utm-environment'

const config = ref<UtmEnvironmentConfig>({
  mockEnabled: true,
  externalUtmEnabled: false,
  externalUtmBaseUrl: '',
  externalUtmApiKey: '',
  currentMode: 'MOCK'
})

const selectedMode = ref('MOCK')
const switching = ref(false)
const testing = ref(false)

const currentMode = computed(() => config.value.currentMode)

const modeLabel = computed(() => {
  const labels: Record<string, string> = {
    MOCK: '模拟模式',
    EXTERNAL: '真实模式',
    HYBRID: '混合模式'
  }
  return labels[currentMode.value] || currentMode.value
})

const modeAlertType = computed(() => {
  const types: Record<string, string> = {
    MOCK: 'info',
    EXTERNAL: 'success',
    HYBRID: 'warning'
  }
  return types[selectedMode.value] || 'info'
})

const modeAlertTitle = computed(() => {
  const titles: Record<string, string> = {
    MOCK: '模拟模式',
    EXTERNAL: '真实模式',
    HYBRID: '混合模式'
  }
  return titles[selectedMode.value] || selectedMode.value
})

const modeAlertDescription = computed(() => {
  const descs: Record<string, string> = {
    MOCK: '使用本地模拟数据，不连接外部UTM系统。飞行计划本地审批，位置数据本地存储，适合开发和测试环境。',
    EXTERNAL: '连接真实外部UTM系统。飞行计划提交到外部审批，位置实时上报，告警实时接收。适合生产环境。',
    HYBRID: '本地处理+外部UTM同步。飞行计划本地处理同时同步到外部UTM，适合灰度验证环境。'
  }
  return descs[selectedMode.value] || ''
})

async function loadConfig() {
  try {
    const data = await utmEnvironmentApi.getConfig()
    config.value = data
    selectedMode.value = data.currentMode
  } catch (e) {
    ElMessage.error('加载UTM配置失败')
  }
}

async function handleSwitchMode() {
  if (selectedMode.value === 'EXTERNAL') {
    try {
      await ElMessageBox.confirm(
        '切换到真实模式将连接外部UTM系统，所有飞行计划将提交到真实UTM审批。确认继续？',
        '切换到真实UTM模式',
        {
          confirmButtonText: '确认切换',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
    } catch {
      return
    }
  }

  switching.value = true
  try {
    const result = await utmEnvironmentApi.switchMode(selectedMode.value as 'MOCK' | 'EXTERNAL' | 'HYBRID')
    ElMessage.success(result.message)
    await loadConfig()
  } catch (e) {
    ElMessage.error('切换失败')
  } finally {
    switching.value = false
  }
}

async function handleTestConnection() {
  testing.value = true
  try {
    const result = await utmEnvironmentApi.testConnection()
    ElMessage[result.success ? 'success' : 'error'](result.message)
  } finally {
    testing.value = false
  }
}

onMounted(loadConfig)
</script>

<style scoped>
.utm-environment-config {
  padding: 20px;
}

.status-cards {
  margin-bottom: 20px;
}

.mode-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.mode-card.MOCK {
  border-left: 4px solid var(--el-color-info);
}

.mode-card.EXTERNAL {
  border-left: 4px solid var(--el-color-success);
}

.mode-card.HYBRID {
  border-left: 4px solid var(--el-color-warning);
}

.mode-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.mode-info {
  flex: 1;
}

.mode-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.mode-value {
  font-size: 18px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.switch-card {
  margin-bottom: 20px;
}

.mode-description {
  margin: 16px 0;
}

.external-config-card {
  margin-bottom: 20px;
}

.info-card {
  margin-bottom: 20px;
}

.info-card h4 {
  margin: 0 0 8px;
  font-size: 14px;
}

.info-card p {
  margin: 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}
</style>
