<script setup lang="ts">
import { ref, computed } from 'vue'

export interface AlgorithmParamInfo {
  name: string
  type: string
  default: any
  description: string
}

export interface AlgorithmReference {
  title: string
  authors: string
  year: number
  doi?: string
  url?: string
}

const props = withDefaults(defineProps<{
  algorithmName: string
  description: string
  category: string
  version: string
  params: Record<string, any>
  paramInfos?: AlgorithmParamInfo[]
  references?: AlgorithmReference[]
  relatedAlgorithms?: Array<{ name: string; category: string }>
}>(), {
  paramInfos: () => [],
  references: () => [],
  relatedAlgorithms: () => [],
})

const emit = defineEmits<{
  (e: 'select-algorithm', name: string): void
}>()

const activeSection = ref('description')

const categoryColorMap: Record<string, string> = {
  'data-assimilation': 'primary',
  'ensemble': 'success',
  'optimization': 'warning',
  'interpolation': 'info',
  'machine-learning': 'danger',
}

const categoryLabelMap: Record<string, string> = {
  'data-assimilation': '数据同化',
  ensemble: '集合方法',
  optimization: '优化方法',
  interpolation: '插值方法',
  'machine-learning': '机器学习',
}

const displayCategory = computed(() => {
  return categoryLabelMap[props.category] || props.category
})

const categoryTagType = computed(() => {
  return (categoryColorMap[props.category] || 'info') as any
})

const paramTableData = computed(() => {
  if (props.paramInfos.length > 0) {
    return props.paramInfos
  }
  return Object.entries(props.params).map(([key, value]) => ({
    name: key,
    type: typeof value,
    default: Array.isArray(value) ? JSON.stringify(value) : String(value),
    description: '',
  }))
})

function formatDefaultValue(val: any): string {
  if (val === undefined || val === null) return '-'
  if (typeof val === 'object') return JSON.stringify(val)
  return String(val)
}

function renderMarkdown(text: string): string {
  return text
    .replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^## (.*$)/gm, '<h2>$1</h2>')
    .replace(/^# (.*$)/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br/>')
}

function handleSelectRelated(algo: { name: string; category: string }) {
  emit('select-algorithm', algo.name)
}

const sections = [
  { key: 'description', label: '算法描述' },
  { key: 'params', label: '参数说明' },
  { key: 'related', label: '相关算法' },
  { key: 'references', label: '引用文献' },
]
</script>

<template>
  <div class="algorithm-description">
    <!-- Header -->
    <div class="algo-header">
      <div class="algo-title-row">
        <h2 class="algo-name">{{ algorithmName }}</h2>
        <el-tag :type="categoryTagType" effect="dark" size="small">
          {{ displayCategory }}
        </el-tag>
        <el-tag effect="plain" size="small" type="info">
          v{{ version }}
        </el-tag>
      </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="section-nav">
      <div
        v-for="sec in sections"
        :key="sec.key"
        class="nav-item"
        :class="{ 'nav-item--active': activeSection === sec.key }"
        @click="activeSection = sec.key"
      >
        {{ sec.label }}
      </div>
    </div>

    <!-- Description Section -->
    <div v-show="activeSection === 'description'" class="section-content">
      <div
        class="description-body"
        v-html="renderMarkdown(description)"
      />
    </div>

    <!-- Params Section -->
    <div v-show="activeSection === 'params'" class="section-content">
      <el-table
        :data="paramTableData"
        stripe
        style="width: 100%"
        :header-cell-style="{
          background: 'var(--color-bg-input, #16213e)',
          color: 'var(--color-text-primary, #e0e0e0)',
          borderColor: 'var(--color-border, #2a2a40)',
        }"
        :cell-style="{
          borderColor: 'var(--color-border, #2a2a40)',
          color: 'var(--color-text-primary, #e0e0e0)',
        }"
      >
        <el-table-column prop="name" label="参数名" width="180" />
        <el-table-column prop="type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" type="info">
              {{ row.type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="默认值" width="180">
          <template #default="{ row }">
            <code class="default-value">{{ formatDefaultValue(row.default) }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200">
          <template #default="{ row }">
            <span :class="{ 'no-desc': !row.description }">
              {{ row.description || '暂无描述' }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Related Algorithms Section -->
    <div v-show="activeSection === 'related'" class="section-content">
      <div v-if="relatedAlgorithms.length > 0" class="related-grid">
        <div
          v-for="algo in relatedAlgorithms"
          :key="algo.name"
          class="related-card"
          @click="handleSelectRelated(algo)"
        >
          <div class="related-name">{{ algo.name }}</div>
          <el-tag size="small" effect="plain" type="info">
            {{ categoryLabelMap[algo.category] || algo.category }}
          </el-tag>
        </div>
      </div>
      <el-empty v-else description="暂无相关算法推荐" :image-size="60" />
    </div>

    <!-- References Section -->
    <div v-show="activeSection === 'references'" class="section-content">
      <div v-if="references.length > 0" class="references-list">
        <div v-for="(ref, index) in references" :key="index" class="ref-item">
          <span class="ref-index">[{{ index + 1 }}]</span>
          <div class="ref-content">
            <span class="ref-title">{{ ref.title }}</span>
            <span class="ref-meta">
              {{ ref.authors }} ({{ ref.year }})
            </span>
            <a
              v-if="ref.doi"
              :href="`https://doi.org/${ref.doi}`"
              target="_blank"
              class="ref-link"
            >
              DOI: {{ ref.doi }}
            </a>
            <a
              v-else-if="ref.url"
              :href="ref.url"
              target="_blank"
              class="ref-link"
            >
              查看链接
            </a>
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无引用文献" :image-size="60" />
    </div>
  </div>
</template>

<style scoped>
.algorithm-description {
  padding: 16px;
  background: var(--color-bg-secondary, #1a1a2e);
  border-radius: 8px;
  border: 1px solid var(--color-border, #2a2a40);
}

.algo-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border, #2a2a40);
}

.algo-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.algo-name {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-primary, #e0e0e0);
}

.section-nav {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  border-bottom: 1px solid var(--color-border, #2a2a40);
}

.nav-item {
  padding: 8px 16px;
  font-size: 14px;
  color: var(--color-text-secondary, #a0a0b0);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.nav-item:hover {
  color: var(--color-text-primary, #e0e0e0);
}

.nav-item--active {
  color: var(--color-primary, #e94560);
  border-bottom-color: var(--color-primary, #e94560);
}

.section-content {
  min-height: 120px;
}

.description-body {
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text-primary, #e0e0e0);
}

.description-body :deep(h1),
.description-body :deep(h2),
.description-body :deep(h3) {
  color: var(--color-text-primary, #e0e0e0);
  margin: 16px 0 8px;
}

.description-body :deep(code) {
  padding: 2px 6px;
  background: var(--color-bg-input, #16213e);
  border-radius: 3px;
  font-size: 13px;
  color: var(--color-primary, #e94560);
}

.default-value {
  padding: 2px 6px;
  background: var(--color-bg-input, #16213e);
  border-radius: 3px;
  font-size: 12px;
  color: var(--color-primary, #e94560);
  font-family: 'Fira Code', 'Consolas', monospace;
}

.no-desc {
  color: var(--color-text-secondary, #909399);
  font-style: italic;
}

.related-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
}

.related-card {
  padding: 14px;
  background: var(--color-bg-input, #16213e);
  border: 1px solid var(--color-border, #2a2a40);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.related-card:hover {
  border-color: var(--color-primary, #e94560);
  background: rgba(233, 69, 96, 0.05);
}

.related-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary, #e0e0e0);
}

.references-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ref-item {
  display: flex;
  gap: 10px;
  padding: 10px 12px;
  background: var(--color-bg-input, #16213e);
  border-radius: 6px;
  border: 1px solid var(--color-border, #2a2a40);
}

.ref-index {
  flex-shrink: 0;
  color: var(--color-primary, #e94560);
  font-weight: 600;
  font-size: 13px;
}

.ref-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ref-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary, #e0e0e0);
}

.ref-meta {
  font-size: 12px;
  color: var(--color-text-secondary, #a0a0b0);
}

.ref-link {
  font-size: 12px;
  color: var(--color-primary, #e94560);
  text-decoration: none;
}

.ref-link:hover {
  text-decoration: underline;
}
</style>
