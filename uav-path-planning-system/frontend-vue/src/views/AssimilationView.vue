<template>
  <a-card title="数据同化服务">
    <a-row :gutter="[16, 16]">
      <a-col :xs="24" :sm="12">
        <a-card size="small" title="同化参数">
          <a-form layout="vertical">
            <a-form-item label="同化算法">
              <a-select v-model:value="formData.algorithm" style="width: 100%">
                <a-select-option value="hybrid">混合方法 (Hybrid)</a-select-option>
                <a-select-option value="3dvar">3D-VAR</a-select-option>
                <a-select-option value="enkf">集合卡尔曼滤波 (EnKF)</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="背景场误差">
              <a-input-number v-model:value="formData.backgroundError" :min="0" :max="1" :step="0.01" style="width: 100%" />
            </a-form-item>
            <a-form-item label="观测误差">
              <a-input-number v-model:value="formData.observationError" :min="0" :max="1" :step="0.01" style="width: 100%" />
            </a-form-item>
            <a-form-item>
              <a-space>
                <a-button type="primary" @click="executeAssimilation" :loading="loading">执行同化</a-button>
                <a-button @click="loadSampleData">加载示例数据</a-button>
                <a-button @click="resetForm">重置</a-button>
              </a-space>
            </a-form-item>
          </a-form>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12">
        <a-card size="small" title="数据输入">
          <a-tabs v-model:activeKey="activeTab">
            <a-tab-pane key="background" tab="背景场">
              <a-textarea v-model:value="backgroundJson" placeholder="输入背景场JSON数据" :rows="8" />
            </a-tab-pane>
            <a-tab-pane key="observations" tab="观测数据">
              <a-textarea v-model:value="observationsJson" placeholder="输入观测数据JSON" :rows="8" />
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </a-col>
    </a-row>
    <a-divider />
    <a-spin :spinning="loading">
      <a-alert v-if="error" :message="error" type="error" show-icon style="margin-bottom:16px" />
      <a-alert v-if="result && result.success" :message="`${result.data.method} 同化完成`" type="success" show-icon style="margin-bottom:16px" />
      <a-empty v-if="!result" description="请执行同化查看结果" />
      <a-row v-if="result && result.success" :gutter="[16, 16]">
        <a-col :xs="24">
          <a-card size="small" title="分析场结果">
            <pre>{{ JSON.stringify(result.data.analysis, null, 2) }}</pre>
          </a-card>
        </a-col>
        <a-col :xs="24">
          <a-card size="small" title="不确定性">
            <pre>{{ JSON.stringify(result.data.uncertainty, null, 2) }}</pre>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>
  </a-card>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { message } from 'ant-design-vue'
import { executeAssimilation as executeAssimilationApi } from '../api/assimilation'

const loading = ref(false)
const error = ref('')
const result = ref(null)
const activeTab = ref('background')

const formData = reactive({
  algorithm: 'hybrid',
  backgroundError: 0.1,
  observationError: 0.05
})

const backgroundJson = ref(JSON.stringify({
  temperature: [20.0, 21.0, 22.0, 23.0, 24.0],
  humidity: [50, 55, 60, 65, 70],
  windSpeed: [5.0, 6.0, 7.0, 8.0, 9.0]
}, null, 2))

const observationsJson = ref(JSON.stringify({
  temperature: [20.5, 21.5, 22.5, 23.5, 24.5],
  humidity: [52, 57, 62, 67, 72],
  windSpeed: [5.2, 6.3, 7.1, 8.2, 9.1]
}, null, 2))

const loadSampleData = () => {
  backgroundJson.value = JSON.stringify({
    temperature: [20.0, 21.0, 22.0, 23.0, 24.0],
    humidity: [50, 55, 60, 65, 70],
    windSpeed: [5.0, 6.0, 7.0, 8.0, 9.0]
  }, null, 2)
  observationsJson.value = JSON.stringify({
    temperature: [20.5, 21.5, 22.5, 23.5, 24.5],
    humidity: [52, 57, 62, 67, 72],
    windSpeed: [5.2, 6.3, 7.1, 8.2, 9.1]
  }, null, 2)
  message.success('示例数据已加载')
}

const resetForm = () => {
  result.value = null
  error.value = ''
  message.info('表单已重置')
}

const executeAssimilation = async () => {
  loading.value = true
  error.value = ''
  try {
    let background, observations
    try {
      background = JSON.parse(backgroundJson.value)
      observations = JSON.parse(observationsJson.value)
    } catch (e) {
      throw new Error('JSON数据格式错误')
    }
    
    const response = await executeAssimilationApi({
      algorithm: formData.algorithm,
      background: background,
      observations: observations,
      config: {
        backgroundError: formData.backgroundError,
        observationError: formData.observationError
      }
    })
    result.value = response
    message.success('同化执行成功')
  } catch (e) {
    error.value = e.message || '同化执行失败'
    console.error('Assimilation error:', e)
  } finally {
    loading.value = false
  }
}
</script>

