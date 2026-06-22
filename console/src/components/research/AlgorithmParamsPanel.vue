<script setup lang="ts">
import { ref, computed, watch, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'

export interface ParamDefinition {
  key: string
  label: string
  type: 'number' | 'string' | 'boolean' | 'object'
  default: any
  min?: number
  max?: number
  step?: number
  enum?: string[]
  description?: string
  group?: 'basic' | 'advanced' | 'meteorological'
  required?: boolean
}

const props = withDefaults(defineProps<{
  algorithmName: string
  category: string
  params: Record<string, any>
  paramDefinitions?: ParamDefinition[]
}>(), {
  paramDefinitions: () => [],
})

const emit = defineEmits<{
  (e: 'update:params', params: Record<string, any>): void
  (e: 'reset'): void
  (e: 'export', params: Record<string, any>): void
}>()

const formRef = ref<FormInstance>()
const activeGroup = ref('basic')
const localParams = reactive<Record<string, any>>({ ...props.params })
const validationErrors = reactive<Record<string, string>>({})

const groupLabels: Record<string, string> = {
  basic: '基础参数',
  advanced: '高级参数',
  meteorological: '气象参数',
}

const groupedParams = computed(() => {
  const groups: Record<string, ParamDefinition[]> = {
    basic: [],
    advanced: [],
    meteorological: [],
  }
  for (const def of props.paramDefinitions) {
    const group = def.group || 'basic'
    if (!groups[group]) groups[group] = []
    groups[group].push(def)
  }
  return groups
})

const groupNames = computed(() => {
  return Object.keys(groupedParams.value).filter(
    (key) => (groupedParams.value[key]?.length ?? 0) > 0
  )
})

function inferParamDef(key: string): ParamDefinition {
  const val = props.params[key]
  const type = Array.isArray(val) ? 'object' : typeof val
  return {
    key,
    label: key,
    type: type as ParamDefinition['type'],
    default: val,
    group: 'basic',
  }
}

function getParamDef(key: string): ParamDefinition {
  return (
    props.paramDefinitions.find((d) => d.key === key) || inferParamDef(key)
  )
}

function validateParam(key: string, value: any): string | null {
  const def = getParamDef(key)
  if (def.type === 'number') {
    if (def.min !== undefined && value < def.min) {
      return `值不能小于 ${def.min}`
    }
    if (def.max !== undefined && value > def.max) {
      return `值不能大于 ${def.max}`
    }
  }
  if (def.type === 'string' && def.required && !value) {
    return '此参数为必填项'
  }
  if (def.type === 'object' && typeof value === 'string') {
    try {
      JSON.parse(value)
    } catch {
      return 'JSON 格式不正确'
    }
  }
  return null
}

function handleParamChange(key: string, value: any) {
  localParams[key] = value
  const error = validateParam(key, value)
  if (error) {
    validationErrors[key] = error
  } else {
    delete validationErrors[key]
  }
  emit('update:params', { ...localParams })
}

function handleObjectInput(key: string, value: string) {
  const error = validateParam(key, value)
  if (error) {
    validationErrors[key] = error
  } else {
    delete validationErrors[key]
    try {
      localParams[key] = JSON.parse(value)
      emit('update:params', { ...localParams })
    } catch {
      // 编辑中，暂不更新
    }
  }
}

function resetParams() {
  ElMessageBox.confirm('确定要重置所有参数为默认值吗？', '参数重置', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  })
    .then(() => {
      for (const def of props.paramDefinitions) {
        localParams[def.key] = def.default
      }
      Object.keys(validationErrors).forEach((k) => delete validationErrors[k])
      emit('update:params', { ...localParams })
      emit('reset')
      ElMessage.success('参数已重置为默认值')
    })
    .catch(() => {})
}

async function exportParams() {
  const json = JSON.stringify(localParams, null, 2)
  try {
    await navigator.clipboard.writeText(json)
    ElMessage.success('参数 JSON 已复制到剪贴板')
    emit('export', { ...localParams })
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

function formatObjectValue(val: any): string {
  if (typeof val === 'object' && val !== null) {
    return JSON.stringify(val, null, 2)
  }
  return String(val ?? '')
}

watch(
  () => props.params,
  (newParams) => {
    Object.assign(localParams, newParams)
  },
  { deep: true }
)
</script>

<template>
  <div class="algorithm-params-panel">
    <div class="panel-header">
      <div class="header-left">
        <span class="algorithm-name">{{ algorithmName }}</span>
        <el-tag size="small" effect="plain">{{ category }}</el-tag>
      </div>
      <div class="header-actions">
        <el-button size="small" @click="exportParams">
          导出参数
        </el-button>
        <el-button size="small" type="warning" plain @click="resetParams">
          重置默认
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeGroup" class="param-tabs">
      <el-tab-pane
        v-for="group in groupNames"
        :key="group"
        :label="groupLabels[group] || group"
        :name="group"
      >
        <el-form
          ref="formRef"
          label-width="140px"
          label-position="left"
          class="param-form"
        >
          <el-form-item
            v-for="def in groupedParams[group]"
            :key="def.key"
            :label="def.label"
            :required="def.required"
          >
            <template #label>
              <span class="param-label">{{ def.label }}</span>
              <el-tooltip
                v-if="def.description"
                :content="def.description"
                placement="top"
              >
                <el-icon class="param-help"><QuestionFilled /></el-icon>
              </el-tooltip>
            </template>

            <!-- Number: slider or input-number -->
            <template v-if="def.type === 'number'">
              <el-slider
                v-if="def.min !== undefined && def.max !== undefined"
                :model-value="localParams[def.key]"
                :min="def.min"
                :max="def.max"
                :step="def.step || 1"
                show-input
                :show-input-controls="false"
                input-size="small"
                class="param-slider"
                @change="(val: number) => handleParamChange(def.key, val)"
              />
              <el-input-number
                v-else
                :model-value="localParams[def.key]"
                :min="def.min"
                :max="def.max"
                :step="def.step || 1"
                :precision="def.step && def.step < 1 ? 2 : 0"
                size="default"
                controls-position="right"
                @change="(val: number) => handleParamChange(def.key, val)"
              />
            </template>

            <!-- String: input or select -->
            <template v-else-if="def.type === 'string'">
              <el-select
                v-if="def.enum && def.enum.length > 0"
                :model-value="localParams[def.key]"
                clearable
                @change="(val: string) => handleParamChange(def.key, val)"
              >
                <el-option
                  v-for="opt in def.enum"
                  :key="opt"
                  :label="opt"
                  :value="opt"
                />
              </el-select>
              <el-input
                v-else
                :model-value="localParams[def.key]"
                clearable
                @input="(val: string) => handleParamChange(def.key, val)"
              />
            </template>

            <!-- Boolean: switch -->
            <template v-else-if="def.type === 'boolean'">
              <el-switch
                :model-value="localParams[def.key]"
                @change="(val: boolean) => handleParamChange(def.key, val)"
              />
            </template>

            <!-- Object: JSON editor -->
            <template v-else-if="def.type === 'object'">
              <el-input
                type="textarea"
                :model-value="formatObjectValue(localParams[def.key])"
                :rows="4"
                class="json-editor"
                spellcheck="false"
                @input="(val: string) => handleObjectInput(def.key, val)"
              />
              <div class="json-hint">请输入合法的 JSON 格式数据</div>
            </template>

            <!-- Validation error -->
            <div v-if="validationErrors[def.key]" class="param-error">
              <el-icon><WarningFilled /></el-icon>
              {{ validationErrors[def.key] }}
            </div>
          </el-form-item>
        </el-form>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script lang="ts">
import { QuestionFilled, WarningFilled } from '@element-plus/icons-vue'
export default {
  components: { QuestionFilled, WarningFilled },
}
</script>

<style scoped>
.algorithm-params-panel {
  padding: 16px;
  background: var(--color-bg-secondary, #1a1a2e);
  border-radius: 8px;
  border: 1px solid var(--color-border, #2a2a40);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border, #2a2a40);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.algorithm-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary, #e0e0e0);
}

.header-actions {
  display: flex;
  gap: 8px;
}

.param-tabs {
  --el-tabs-header-height: 40px;
}

.param-tabs :deep(.el-tabs__nav-wrap::after) {
  background-color: var(--color-border, #2a2a40);
}

.param-tabs :deep(.el-tabs__item) {
  color: var(--color-text-secondary, #a0a0b0);
}

.param-tabs :deep(.el-tabs__item.is-active) {
  color: var(--color-primary, #e94560);
}

.param-form {
  margin-top: 12px;
}

.param-label {
  color: var(--color-text-primary, #e0e0e0);
}

.param-help {
  margin-left: 4px;
  color: var(--color-text-secondary, #a0a0b0);
  cursor: help;
  font-size: 14px;
}

.param-slider {
  width: 100%;
}

.param-slider :deep(.el-input-number) {
  width: 120px;
}

.json-editor {
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.json-hint {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-secondary, #a0a0b0);
}

.param-error {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-danger, #f56c6c);
}

.param-form :deep(.el-form-item__label) {
  color: var(--color-text-primary, #e0e0e0);
}

.param-form :deep(.el-input__wrapper),
.param-form :deep(.el-textarea__inner) {
  background-color: var(--color-bg-input, #16213e);
  border-color: var(--color-border, #2a2a40);
  color: var(--color-text-primary, #e0e0e0);
  box-shadow: none;
}

.param-form :deep(.el-input__wrapper:hover),
.param-form :deep(.el-textarea__inner:hover) {
  border-color: var(--color-primary, #e94560);
}

.param-form :deep(.el-input-number__decrease),
.param-form :deep(.el-input-number__increase) {
  background-color: var(--color-bg-input, #16213e);
  border-color: var(--color-border, #2a2a40);
  color: var(--color-text-primary, #e0e0e0);
}
</style>
