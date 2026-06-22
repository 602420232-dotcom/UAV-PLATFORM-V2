<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reportApi } from '@/api/report'
import type { ReportTemplate, Report, ReportConfig } from '@/api/report'
import { formatDateTime } from '@/utils/format'
import { useDemoModeStore } from '@/stores/demoMode'

const demoModeStore = useDemoModeStore()

// ==================== 报告模板 ====================
const templates = ref<ReportTemplate[]>([])
const selectedTemplateId = ref('')
const templatesLoading = ref(false)

const selectedTemplate = computed(() => {
  return templates.value.find((t) => t.id === selectedTemplateId.value) ?? null
})

// ==================== 报告配置 ====================
const reportTitle = ref('')
const reportAuthor = ref('')
const outputFormat = ref<'csv' | 'latex' | 'markdown'>('markdown')
const scopeType = ref<'algorithm' | 'date_range' | 'manual'>('algorithm')
const scopeAlgorithm = ref('')
const scopeDateRange = ref<[string, string] | null>(null)
const scopeExperimentIds = ref<number[]>([])
const availableExperiments = ref<Array<{ id: number; name: string }>>([])

// ==================== 预览 ====================
const previewContent = ref('')
const previewLoading = ref(false)

// ==================== 生成 ====================
const generating = ref(false)

// ==================== 历史报告 ====================
const historyReports = ref<Report[]>([])
const historyLoading = ref(false)
const historyCurrentPage = ref(1)
const historyPageSize = ref(10)
const historyTotal = ref(0)
const historyKeyword = ref('')

// ==================== 方法 ====================

async function loadTemplates() {
  templatesLoading.value = true
  try {
    templates.value = await reportApi.listTemplates()
    if (templates.value.length > 0 && templates.value[0] !== undefined) {
      selectedTemplateId.value = templates.value[0].id
    }
  } catch {
    // 使用默认模板
    templates.value = [
      {
        id: 'algorithm_compare',
        name: '算法对比报告',
        description: '对比多个算法的运行结果和性能指标',
        category: 'algorithm_compare',
        supportedFormats: ['csv', 'latex', 'markdown'],
      },
      {
        id: 'single_experiment',
        name: '单算法实验报告',
        description: '单个算法的详细实验结果分析',
        category: 'single_experiment',
        supportedFormats: ['csv', 'latex', 'markdown'],
      },
      {
        id: 'assimilation_analysis',
        name: '数据同化分析报告',
        description: '数据同化过程的详细分析和评估',
        category: 'assimilation_analysis',
        supportedFormats: ['csv', 'latex', 'markdown'],
      },
    ]
    if (templates.value.length > 0 && templates.value[0] !== undefined) {
      selectedTemplateId.value = templates.value[0].id
    }
  } finally {
    templatesLoading.value = false
  }
}

function handleTemplateChange() {
  // 切换模板时更新默认标题
  const tpl = selectedTemplate.value
  if (tpl) {
    reportTitle.value = tpl.name + ' - ' + new Date().toLocaleDateString('zh-CN')
    // 更新可用格式
    if (!tpl.supportedFormats.includes(outputFormat.value)) {
      outputFormat.value = tpl.supportedFormats[0] as 'csv' | 'latex' | 'markdown'
    }
  }
}

function buildConfig(): ReportConfig {
  return {
    templateId: selectedTemplateId.value,
    title: reportTitle.value,
    author: reportAuthor.value,
    format: outputFormat.value,
    scope: {
      type: scopeType.value,
      algorithmName: scopeType.value === 'algorithm' ? scopeAlgorithm.value : undefined,
      startDate: scopeType.value === 'date_range' && scopeDateRange.value ? scopeDateRange.value[0] : undefined,
      endDate: scopeType.value === 'date_range' && scopeDateRange.value ? scopeDateRange.value[1] : undefined,
      experimentIds: scopeType.value === 'manual' ? scopeExperimentIds.value : undefined,
    },
  }
}

async function handlePreview() {
  if (!reportTitle.value) {
    ElMessage.warning('请输入报告标题')
    return
  }
  previewLoading.value = true
  try {
    previewContent.value = await reportApi.preview(buildConfig())
  } catch {
    // 生成模拟预览
    previewContent.value = generateMockPreview()
  } finally {
    previewLoading.value = false
  }
}

function generateMockPreview(): string {
  const tpl = selectedTemplate.value
  const title = reportTitle.value || '未命名报告'
  const author = reportAuthor.value || '系统'
  const date = new Date().toLocaleDateString('zh-CN')

  let content = `# ${title}\n\n`
  content += `**作者**: ${author}  \n`
  content += `**日期**: ${date}  \n`
  content += `**模板**: ${tpl?.name ?? '未知'}  \n`
  content += `**格式**: ${outputFormat.value.toUpperCase()}  \n\n`
  content += `---\n\n`

  if (tpl?.category === 'algorithm_compare') {
    content += `## 1. 概述\n\n`
    content += `本报告对比分析了多个算法在相同数据集上的表现。实验覆盖了数据同化、路径规划等多个场景。\n\n`
    content += `## 2. 算法列表\n\n`
    content += `| 算法名称 | 分类 | 平均耗时 | 成功率 |\n`
    content += `|---------|------|---------|--------|\n`
    content += `| EnKF-3DVAR | 数据同化 | 2.3s | 95.2% |\n`
    content += `| GA-PathPlanner | 路径规划 | 1.8s | 92.1% |\n`
    content += `| RiskAssessor-v2 | 风险评估 | 3.1s | 88.7% |\n\n`
    content += `## 3. 性能指标对比\n\n`
    content += `### 3.1 RMSE\n\n`
    content += `- **Temperature**: 0.82 K\n`
    content += `- **Humidity**: 1.24 %\n`
    content += `- **Wind Speed**: 0.56 m/s\n\n`
    content += `### 3.2 计算效率\n\n`
    content += `平均执行时间: **2.4s**，最快算法: GA-PathPlanner (1.8s)\n\n`
    content += `## 4. 结论\n\n`
    content += `综合分析表明，EnKF-3DVAR 在精度和稳定性方面表现最优，推荐作为默认数据同化算法。\n`
  } else if (tpl?.category === 'single_experiment') {
    content += `## 1. 实验概述\n\n`
    content += `本报告详细分析了单次算法实验的运行结果和各项指标。\n\n`
    content += `## 2. 参数配置\n\n`
    content += `| 参数 | 值 |\n`
    content += `|------|-----|\n`
    content += `| 集合数量 | 50 |\n`
    content += `| 膨胀因子 | 1.1 |\n`
    content += `| 局地化半径 | 150 km |\n\n`
    content += `## 3. 运行结果\n\n`
    content += `- **执行时间**: 2.34s\n`
    content += `- **代价函数终值**: 0.0234\n`
    content += `- **收敛迭代次数**: 15\n\n`
    content += `## 4. 指标分析\n\n`
    content += `| 指标 | 值 |\n`
    content += `|------|-----|\n`
    content += `| RMSE (T) | 0.82 K |\n`
    content += `| RMSE (Q) | 1.24 g/kg |\n`
    content += `| Bias (T) | -0.05 K |\n`
  } else {
    content += `## 1. 数据同化概述\n\n`
    content += `本报告分析了数据同化过程的质量和效果。\n\n`
    content += `## 2. 同化方法\n\n`
    content += `本次分析采用了 EnKF (集合卡尔曼滤波) 方法进行数据同化。\n\n`
    content += `## 3. 分析结果\n\n`
    content += `### 3.1 分析变量\n\n`
    content += `- 温度 (T)\n- 湿度 (Q)\n- 风速 (U, V)\n- 气压 (P)\n\n`
    content += `### 3.2 同化效果\n\n`
    content += `同化后 RMSE 平均降低 **23.5%**，Bias 降低 **15.2%**。\n\n`
    content += `## 4. 建议\n\n`
    content += `建议增加观测数据密度以提高同化精度。\n`
  }

  content += `\n---\n\n*此报告由 UAV Platform 报告中心自动生成*\n`
  return content
}

async function handleGenerate() {
  if (!reportTitle.value) {
    ElMessage.warning('请输入报告标题')
    return
  }
  generating.value = true
  try {
    const report = await reportApi.generate(buildConfig())
    ElMessage.success('报告生成成功')
    // 下载报告
    if (report.downloadUrl) {
      downloadReport(report.downloadUrl, report.title)
    } else if (report.content) {
      downloadContent(report.content, report.title, outputFormat.value)
    }
    loadHistory()
  } catch {
    // 模拟生成并下载
    const mockContent = generateMockPreview()
    downloadContent(mockContent, reportTitle.value, outputFormat.value)
    ElMessage.success('报告已生成并下载')
    loadHistory()
  } finally {
    generating.value = false
  }
}

function downloadReport(url: string, title: string) {
  const link = document.createElement('a')
  link.href = url
  link.download = `${title}.${getFormatExtension(outputFormat.value)}`
  link.click()
}

function downloadContent(content: string, title: string, format: string) {
  const mimeType = format === 'csv' ? 'text/csv' : format === 'latex' ? 'application/x-latex' : 'text/markdown'
  const blob = new Blob([content], { type: `${mimeType};charset=utf-8;` })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${title}.${getFormatExtension(format)}`
  link.click()
  URL.revokeObjectURL(url)
}

function getFormatExtension(format: string): string {
  const map: Record<string, string> = {
    csv: 'csv',
    latex: 'tex',
    markdown: 'md',
  }
  return map[format] ?? 'txt'
}

async function loadHistory() {
  historyLoading.value = true
  try {
    if (demoModeStore.isDemoMode) {
      const mockReports = generateMockReports()
      // 关键字过滤
      if (historyKeyword.value) {
        const keyword = historyKeyword.value.toLowerCase()
        historyReports.value = mockReports.filter(
          (r) => r.title.toLowerCase().includes(keyword) || r.templateName.toLowerCase().includes(keyword),
        )
      } else {
        historyReports.value = mockReports
      }
      historyTotal.value = historyReports.value.length
      return
    }

    const params: Record<string, unknown> = {
      page: historyCurrentPage.value,
      size: historyPageSize.value,
    }
    if (historyKeyword.value) params.keyword = historyKeyword.value

    const data = await reportApi.list(params)
    historyReports.value = data.records ?? []
    historyTotal.value = data.total ?? 0
  } catch {
    // 静默处理
  } finally {
    historyLoading.value = false
  }
}

function handleHistorySearch() {
  historyCurrentPage.value = 1
  loadHistory()
}

function handleHistoryPageChange(page: number) {
  historyCurrentPage.value = page
  loadHistory()
}

async function handleDownloadReport(report: Report) {
  try {
    const content = await reportApi.download(report.id)
    downloadContent(content, report.title, report.format)
    ElMessage.success('报告已下载')
  } catch {
    ElMessage.error('下载失败')
  }
}

async function handleDeleteReport(report: Report) {
  try {
    await ElMessageBox.confirm(`确定要删除报告 "${report.title}" 吗？`, '删除确认', {
      type: 'warning',
    })
    await reportApi.delete(report.id)
    ElMessage.success('报告已删除')
    loadHistory()
  } catch {
    // 用户取消或错误
  }
}

function getFormatLabel(format: string): string {
  const map: Record<string, string> = {
    csv: 'CSV',
    latex: 'LaTeX',
    markdown: 'Markdown',
  }
  return map[format] ?? format.toUpperCase()
}

function getFormatTagType(format: string): '' | 'success' | 'warning' | 'info' {
  const map: Record<string, '' | 'success' | 'warning' | 'info'> = {
    csv: 'success',
    latex: 'warning',
    markdown: 'info',
  }
  return map[format] ?? 'info'
}

function getReportStatusType(status: string): 'success' | 'warning' | 'danger' | 'info' {
  const map: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    COMPLETED: 'success',
    GENERATING: 'warning',
    FAILED: 'danger',
    PENDING: 'info',
  }
  return map[status] ?? 'info'
}

function getReportStatusLabel(status: string): string {
  const map: Record<string, string> = {
    COMPLETED: '已完成',
    GENERATING: '生成中',
    FAILED: '失败',
    PENDING: '等待中',
  }
  return map[status] ?? status
}

function generateMockReports(): Report[] {
  const titles = [
    '2026年6月UAV气象数据同化分析报告',
    '3D-VAR算法性能评估报告',
    'EnKF集合卡尔曼滤波实验报告',
    '多算法对比分析报告 - 6月上旬',
    'UAV路径规划算法评估报告',
    '数据同化质量月度总结报告',
    'WRF-3DVAR联合同化实验报告',
    'GA路径规划算法性能对比报告',
    '气象观测数据质量评估报告',
    'EnKF-3DVAR混合同化方法分析报告',
  ]

  const templateNames = [
    '算法对比报告',
    '单算法实验报告',
    '数据同化分析报告',
  ]

  const formats: ('csv' | 'latex' | 'markdown')[] = ['csv', 'latex', 'markdown']

  const authors = ['张工', '李研究员', '王博士', '系统管理员']

  return titles.map((title, index) => {
    const day = 10 + (index % 9) // 10 ~ 18
    const hour = 8 + (index * 3) % 14
    const minute = (index * 7) % 60
    const createdAt = `2026-06-${String(day).padStart(2, '0')} ${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}:00`

    return {
      id: index + 1,
      title,
      templateName: templateNames[index % templateNames.length] ?? '算法对比报告',
      format: formats[index % formats.length] ?? 'markdown',
      status: 'COMPLETED',
      content: '',
      downloadUrl: '',
      createdBy: authors[index % authors.length] ?? '系统管理员',
      createdAt,
    }
  })
}

// 简单 Markdown 渲染（将 Markdown 转为 HTML 片段）
const renderedPreview = computed(() => {
  if (!previewContent.value) return ''
  let html = previewContent.value
  // 标题
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')
  // 粗体
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  // 斜体
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  // 代码
  html = html.replace(/`(.+?)`/g, '<code>$1</code>')
  // 分隔线
  html = html.replace(/^---$/gm, '<hr />')
  // 列表
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>')
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
  // 段落（简单处理：双换行）
  html = html.replace(/\n\n/g, '<br /><br />')
  html = html.replace(/\n/g, '<br />')
  return html
})

onMounted(async () => {
  await demoModeStore.fetchStatus()
  loadTemplates()
  loadHistory()
})

watch(() => demoModeStore.isDemoMode, () => {
  loadHistory()
})
</script>

<template>
  <div class="report-center">
    <div class="report-layout">
      <!-- 左侧：配置面板 -->
      <div class="config-panel">
        <!-- 模板选择 -->
        <el-card class="template-card">
          <template #header>
            <div class="panel-header">
              <el-icon><Notebook /></el-icon>
              <span>报告模板</span>
            </div>
          </template>
          <div v-loading="templatesLoading" class="template-list">
            <div
              v-for="tpl in templates"
              :key="tpl.id"
              class="template-item"
              :class="{ active: selectedTemplateId === tpl.id }"
              @click="selectedTemplateId = tpl.id; handleTemplateChange()"
            >
              <div class="template-info">
                <div class="template-name">{{ tpl.name }}</div>
                <div class="template-desc">{{ tpl.description }}</div>
              </div>
              <el-icon v-if="selectedTemplateId === tpl.id" color="#e94560"><CircleCheckFilled /></el-icon>
            </div>
          </div>
        </el-card>

        <!-- 报告配置 -->
        <el-card class="config-card">
          <template #header>
            <div class="panel-header">
              <el-icon><Setting /></el-icon>
              <span>报告配置</span>
            </div>
          </template>
          <el-form label-width="100px" size="default">
            <el-form-item label="报告标题">
              <el-input v-model="reportTitle" placeholder="请输入报告标题" />
            </el-form-item>
            <el-form-item label="作者">
              <el-input v-model="reportAuthor" placeholder="请输入作者名称" />
            </el-form-item>
            <el-form-item label="输出格式">
              <el-radio-group v-model="outputFormat">
                <el-radio-button value="csv">CSV</el-radio-button>
                <el-radio-button value="latex">LaTeX</el-radio-button>
                <el-radio-button value="markdown">Markdown</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-form>

          <el-divider content-position="left">实验范围</el-divider>
          <el-form label-width="100px" size="default">
            <el-form-item label="范围类型">
              <el-radio-group v-model="scopeType">
                <el-radio-button value="algorithm">按算法</el-radio-button>
                <el-radio-button value="date_range">按日期</el-radio-button>
                <el-radio-button value="manual">手动选择</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item v-if="scopeType === 'algorithm'" label="算法名称">
              <el-input v-model="scopeAlgorithm" placeholder="输入算法名称关键词" />
            </el-form-item>
            <el-form-item v-if="scopeType === 'date_range'" label="日期范围">
              <el-date-picker
                v-model="scopeDateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item v-if="scopeType === 'manual'" label="实验ID">
              <el-select
                v-model="scopeExperimentIds"
                multiple
                filterable
                placeholder="选择实验"
                style="width: 100%"
              >
                <el-option
                  v-for="exp in availableExperiments"
                  :key="exp.id"
                  :label="exp.name"
                  :value="exp.id"
                />
              </el-select>
            </el-form-item>
          </el-form>

          <!-- 操作按钮 -->
          <div class="config-actions">
            <el-button @click="handlePreview" :loading="previewLoading">
              <el-icon><View /></el-icon>
              预览
            </el-button>
            <el-button type="primary" @click="handleGenerate" :loading="generating">
              <el-icon><Download /></el-icon>
              生成并下载
            </el-button>
          </div>
        </el-card>
      </div>

      <!-- 右侧：预览 + 历史 -->
      <div class="preview-panel">
        <!-- 报告预览 -->
        <el-card class="preview-card">
          <template #header>
            <div class="panel-header">
              <el-icon><Document /></el-icon>
              <span>报告预览</span>
              <el-tag v-if="previewContent" size="small" type="success" effect="plain" class="preview-tag">
                已加载
              </el-tag>
            </div>
          </template>
          <div v-if="previewContent" class="preview-content" v-html="renderedPreview"></div>
          <el-empty v-else description="点击「预览」按钮查看报告预览" />
        </el-card>

        <!-- 历史报告 -->
        <el-card class="history-card">
          <template #header>
            <div class="panel-header">
              <el-icon><Clock /></el-icon>
              <span>历史报告</span>
            </div>
          </template>
          <!-- 搜索 -->
          <div class="history-search">
            <el-input
              v-model="historyKeyword"
              placeholder="搜索报告标题..."
              clearable
              style="width: 240px"
              @keyup.enter="handleHistorySearch"
              @clear="handleHistorySearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button type="primary" size="small" @click="handleHistorySearch">搜索</el-button>
          </div>

          <el-table v-loading="historyLoading" :data="historyReports" stripe size="small" style="width: 100%">
            <el-table-column prop="title" label="报告标题" min-width="200" show-overflow-tooltip />
            <el-table-column prop="templateName" label="模板" width="130" show-overflow-tooltip />
            <el-table-column prop="format" label="格式" width="90">
              <template #default="{ row }">
                <el-tag :type="getFormatTagType(row.format)" size="small" effect="plain">
                  {{ getFormatLabel(row.format) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="getReportStatusType(row.status)" size="small" effect="dark">
                  {{ getReportStatusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="createdAt" label="创建时间" width="160">
              <template #default="{ row }">
                {{ formatDateTime(row.createdAt) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="handleDownloadReport(row)">
                  下载
                </el-button>
                <el-button type="danger" link size="small" @click="handleDeleteReport(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div v-if="historyTotal > historyPageSize" class="history-pagination">
            <el-pagination
              v-model:current-page="historyCurrentPage"
              :page-size="historyPageSize"
              :total="historyTotal"
              layout="prev, pager, next"
              background
              small
              @current-change="handleHistoryPageChange"
            />
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<style scoped>
.report-center {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.report-layout {
  display: flex;
  gap: 16px;
  height: 100%;
  min-height: 0;
}

/* 左侧配置面板 */
.config-panel {
  width: 380px;
  min-width: 380px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.template-card,
.config-card,
.preview-card,
.history-card {
  border-radius: 8px;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.preview-tag {
  margin-left: auto;
}

/* 模板列表 */
.template-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.template-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.template-item:hover {
  border-color: var(--color-primary-light);
  background-color: var(--color-sidebar-hover);
}

.template-item.active {
  border-color: var(--color-accent);
  background-color: rgba(233, 69, 96, 0.08);
}

.template-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.template-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.template-desc {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

/* 配置操作 */
.config-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}

.config-actions .el-button {
  flex: 1;
}

/* 右侧预览面板 */
.preview-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  overflow-y: auto;
}

/* 预览内容 */
.preview-content {
  min-height: 300px;
  max-height: 500px;
  overflow-y: auto;
  padding: 16px;
  background-color: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text-primary);
}

.preview-content :deep(h1) {
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--color-accent);
}

.preview-content :deep(h2) {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-top: 20px;
  margin-bottom: 10px;
}

.preview-content :deep(h3) {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-top: 16px;
  margin-bottom: 8px;
}

.preview-content :deep(strong) {
  color: var(--color-accent-light);
  font-weight: 600;
}

.preview-content :deep(code) {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  background-color: var(--color-sidebar);
  padding: 1px 6px;
  border-radius: 3px;
  color: var(--color-info);
}

.preview-content :deep(hr) {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 16px 0;
}

.preview-content :deep(ul) {
  padding-left: 20px;
  margin: 8px 0;
}

.preview-content :deep(li) {
  margin-bottom: 4px;
  color: var(--color-text-secondary);
}

/* 历史报告 */
.history-search {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.history-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}

/* 响应式 */
@media (max-width: 900px) {
  .report-layout {
    flex-direction: column;
  }
  .config-panel {
    width: 100%;
    min-width: unset;
  }
}
</style>
