<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { reportApi, type ReportConfig } from '@/api/report'

const props = withDefaults(defineProps<{
  experimentIds: number[]
}>(), {
  experimentIds: () => [],
})

const emit = defineEmits<{
  (e: 'generated', report: any): void
  (e: 'error', error: Error): void
}>()

const templateOptions = [
  {
    label: '算法对比报告',
    value: 'algorithm-compare',
    description: '对比多个算法在同一数据集上的表现差异',
  },
  {
    label: '单算法实验报告',
    value: 'single-algorithm',
    description: '单个算法的详细实验结果与分析',
  },
  {
    label: '数据同化分析报告',
    value: 'data-assimilation',
    description: '数据同化过程的详细分析报告',
  },
]

const formatOptions = [
  { label: 'Markdown', value: 'markdown' },
  { label: 'CSV', value: 'csv' },
  { label: 'LaTeX', value: 'latex' },
]

const form = reactive<ReportConfig>({
  templateId: 'algorithm-compare',
  title: '',
  author: '',
  format: 'markdown',
  scope: {
    type: 'manual',
    experimentIds: [...props.experimentIds],
  },
})

const exportStatus = ref<'idle' | 'generating' | 'success' | 'error'>('idle')
const previewContent = ref('')
const showPreview = ref(false)

const selectedTemplateInfo = computed(() => {
  return templateOptions.find((t) => t.value === form.templateId)
})

const canGenerate = computed(() => {
  return (
    form.title.trim() !== '' &&
    ((form.scope?.experimentIds ?? []).length > 0) &&
    exportStatus.value !== 'generating'
  )
})

const statusText = computed(() => {
  const map: Record<string, string> = {
    idle: '',
    generating: '报告生成中...',
    success: '报告生成完成',
    error: '报告生成失败',
  }
  return map[exportStatus.value]
})

const statusType = computed(() => {
  const map: Record<string, string> = {
    idle: 'info',
    generating: 'warning',
    success: 'success',
    error: 'danger',
  }
  return map[exportStatus.value]
})

function handleTemplateChange(templateId: string) {
  form.templateId = templateId as ReportConfig['templateId']
  const defaultTitles: Record<string, string> = {
    'algorithm-compare': '算法对比分析报告',
    'single-algorithm': '单算法实验报告',
    'data-assimilation': '数据同化分析报告',
  }
  if (!form.title) {
    form.title = defaultTitles[templateId] || ''
  }
}

async function generatePreview() {
  if (!canGenerate.value) return
  exportStatus.value = 'generating'
  try {
    const result = await reportApi.preview(form)
    previewContent.value = result || ''
    showPreview.value = true
    exportStatus.value = 'success'
    ElMessage.success('预览生成成功')
  } catch (err: any) {
    exportStatus.value = 'error'
    ElMessage.error(err.message || '预览生成失败')
    emit('error', err)
  }
}

async function generateAndDownload() {
  if (!canGenerate.value) return
  exportStatus.value = 'generating'
  try {
    const result = await reportApi.generate(form)
    const blob = new Blob([result.content], {
      type: getMimeType(form.format),
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${form.title}.${getExtension(form.format)}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    exportStatus.value = 'success'
    emit('generated', result)
    ElMessage.success('报告已下载')
  } catch (err: any) {
    exportStatus.value = 'error'
    ElMessage.error(err.message || '报告生成失败')
    emit('error', err)
  }
}

function getMimeType(format: string): string {
  const map: Record<string, string> = {
    markdown: 'text/markdown;charset=utf-8',
    csv: 'text/csv;charset=utf-8',
    latex: 'application/x-latex;charset=utf-8',
  }
  return map[format] || 'text/plain'
}

function getExtension(format: string): string {
  const map: Record<string, string> = {
    markdown: 'md',
    csv: 'csv',
    latex: 'tex',
  }
  return map[format] || 'txt'
}

function renderMarkdown(content: string): string {
  return content
    .replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^## (.*$)/gm, '<h2>$1</h2>')
    .replace(/^# (.*$)/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br/>')
}
</script>

<template>
  <div class="report-exporter">
    <div class="exporter-header">
      <h3 class="exporter-title">报告导出</h3>
      <el-tag v-if="exportStatus !== 'idle'" :type="(statusType as any)" effect="plain">
        {{ statusText }}
      </el-tag>
    </div>

    <el-form label-width="100px" label-position="left" class="exporter-form">
      <!-- Template Selection -->
      <el-form-item label="报告模板">
        <el-radio-group v-model="form.templateId" @change="handleTemplateChange">
          <el-radio-button
            v-for="opt in templateOptions"
            :key="opt.value"
            :value="opt.value"
          >
            {{ opt.label }}
          </el-radio-button>
        </el-radio-group>
        <div class="template-desc">
          {{ selectedTemplateInfo?.description }}
        </div>
      </el-form-item>

      <!-- Title -->
      <el-form-item label="报告标题" required>
        <el-input
          v-model="form.title"
          placeholder="请输入报告标题"
          clearable
        />
      </el-form-item>

      <!-- Author -->
      <el-form-item label="作者">
        <el-input
          v-model="form.author"
          placeholder="请输入作者名称"
          clearable
        />
      </el-form-item>

      <!-- Format -->
      <el-form-item label="输出格式">
        <el-radio-group v-model="form.format">
          <el-radio-button
            v-for="opt in formatOptions"
            :key="opt.value"
            :value="opt.value"
          >
            {{ opt.label }}
          </el-radio-button>
        </el-radio-group>
      </el-form-item>

      <!-- Experiment IDs -->
      <el-form-item label="实验范围">
        <el-select
          v-model="form.scope.experimentIds"
          multiple
          collapse-tags
          collapse-tags-tooltip
          placeholder="选择实验"
          style="width: 100%"
        >
          <el-option
            v-for="id in experimentIds"
            :key="id"
            :label="`实验 #${id}`"
            :value="id"
          />
        </el-select>
        <div class="selected-count">
          已选择 {{ (form.scope.experimentIds ?? []).length }} 个实验
        </div>
      </el-form-item>

      <!-- Actions -->
      <el-form-item>
        <el-button
          type="primary"
          :disabled="!canGenerate"
          :loading="exportStatus === 'generating'"
          @click="generateAndDownload"
        >
          生成并下载
        </el-button>
        <el-button
          :disabled="!canGenerate"
          @click="generatePreview"
        >
          预览报告
        </el-button>
      </el-form-item>
    </el-form>

    <!-- Preview -->
    <el-collapse-transition>
      <div v-if="showPreview && previewContent" class="preview-section">
        <div class="preview-header">
          <span class="preview-label">报告预览</span>
          <el-button size="small" text @click="showPreview = false">
            关闭预览
          </el-button>
        </div>
        <div
          class="preview-content"
          v-html="renderMarkdown(previewContent)"
        />
      </div>
    </el-collapse-transition>
  </div>
</template>

<style scoped>
.report-exporter {
  padding: 16px;
  background: var(--color-bg-secondary, #1a1a2e);
  border-radius: 8px;
  border: 1px solid var(--color-border, #2a2a40);
}

.exporter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border, #2a2a40);
}

.exporter-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary, #e0e0e0);
}

.exporter-form {
  max-width: 700px;
}

.template-desc {
  margin-top: 6px;
  font-size: 12px;
  color: var(--color-text-secondary, #a0a0b0);
}

.selected-count {
  margin-top: 4px;
  font-size: 12px;
  color: var(--color-text-secondary, #a0a0b0);
}

.exporter-form :deep(.el-form-item__label) {
  color: var(--color-text-primary, #e0e0e0);
}

.exporter-form :deep(.el-input__wrapper) {
  background-color: var(--color-bg-input, #16213e);
  border-color: var(--color-border, #2a2a40);
  color: var(--color-text-primary, #e0e0e0);
  box-shadow: none;
}

.exporter-form :deep(.el-radio-button__inner) {
  background: var(--color-bg-input, #16213e);
  border-color: var(--color-border, #2a2a40);
  color: var(--color-text-secondary, #a0a0b0);
}

.exporter-form :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: var(--color-primary, #e94560);
  border-color: var(--color-primary, #e94560);
  color: #fff;
}

.preview-section {
  margin-top: 20px;
  border-top: 1px solid var(--color-border, #2a2a40);
  padding-top: 16px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.preview-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary, #e0e0e0);
}

.preview-content {
  padding: 16px;
  background: var(--color-bg-primary, #0f0f23);
  border-radius: 6px;
  border: 1px solid var(--color-border, #2a2a40);
  max-height: 400px;
  overflow-y: auto;
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text-primary, #e0e0e0);
}

.preview-content :deep(h1),
.preview-content :deep(h2),
.preview-content :deep(h3) {
  color: var(--color-text-primary, #e0e0e0);
  margin: 12px 0 8px;
}

.preview-content :deep(code) {
  padding: 2px 6px;
  background: var(--color-bg-input, #16213e);
  border-radius: 3px;
  font-size: 13px;
  color: var(--color-primary, #e94560);
}

.preview-content :deep(strong) {
  color: var(--color-text-primary, #e0e0e0);
}
</style>
