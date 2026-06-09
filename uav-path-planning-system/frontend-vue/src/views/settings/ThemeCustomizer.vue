<template>
  <div class="theme-customizer">
    <!-- 顶部栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">
          <el-icon :size="22"><MagicStick /></el-icon>
          主题定制
        </h2>
        <el-tag type="info" effect="plain" class="demo-tag" v-if="authStore.demoMode">
          <el-icon><MagicStick /></el-icon>&nbsp;演示模式
        </el-tag>
      </div>
      <div class="header-right">
        <span class="label-text">当前主题：</span>
        <el-tag :type="currentTagType" effect="light" size="large">
          {{ currentThemeLabel }}
        </el-tag>
        <el-button type="primary" :icon="RefreshLeft" @click="resetToDefault">
          重置为默认
        </el-button>
      </div>
    </div>

    <!-- 主体区域（左右双栏） -->
    <el-row :gutter="20" class="main-body">
      <!-- 顶部：主题模式下拉（含自动） -->
      <el-col :span="24" class="mode-selector-col">
        <el-card shadow="hover" class="mode-selector-card">
          <div class="mode-selector-row">
            <el-icon :size="18"><Brush /></el-icon>
            <span class="mode-label">主题模式：</span>
            <el-select
              v-model="modeValue"
              style="width: 220px"
              placeholder="选择主题模式"
              @change="onModeChange"
            >
              <el-option
                v-for="opt in modeOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
            <el-tag
              v-if="modeValue === 'auto'"
              :type="isNightNow ? 'info' : 'warning'"
              effect="light"
              size="default"
              class="night-status-tag"
            >
              {{ isNightNow ? '🌙 夜间 · 已应用深色主题' : '☀️ 白天 · 已应用浅色主题' }}
            </el-tag>
            <el-tag v-else :type="currentTagType" effect="light" size="default">
              当前主题：{{ currentThemeLabel }}
            </el-tag>
            <el-button
              v-if="modeValue === 'auto'"
              type="primary"
              plain
              size="small"
              :icon="RefreshLeft"
              @click="forceRefreshNight"
            >
              刷新日夜状态
            </el-button>
          </div>
          <div class="mode-tip">
            自动模式会根据本地时间在日落（19:00 后）与日出（06:00 前）自动切换主题。深色主题默认启用 15% 蓝光过滤（CSS 变量 --color-blue-filter: 0.85）。
          </div>
        </el-card>
      </el-col>

      <!-- 左栏：主题预设卡片 -->
      <el-col :xs="24" :md="9">
        <el-card shadow="hover" class="preset-card">
          <template #header>
            <div class="card-header">
              <el-icon><Brush /></el-icon>
              <span>主题预设</span>
            </div>
          </template>

          <div class="preset-grid">
            <div
              v-for="preset in presets"
              :key="preset.key"
              class="preset-item"
              :class="{ active: currentTheme === preset.key }"
              @click="switchTheme(preset.key)"
            >
              <div class="preset-preview" :style="preset.previewStyle">
                <div class="preview-bg"></div>
                <div class="preview-block" :style="{ background: preset.colors.surface, borderColor: preset.colors.border }"></div>
                <div class="preview-dots">
                  <span :style="{ background: preset.colors.primary }"></span>
                  <span :style="{ background: preset.colors.accent }"></span>
                </div>
              </div>
              <div class="preset-meta">
                <span class="preset-name">{{ preset.label }}</span>
                <span class="preset-desc">{{ preset.description }}</span>
              </div>
              <div class="color-swatches">
                <div v-for="(color, name) in preset.colors" :key="name" class="swatch" :style="{ background: color }" :title="name"></div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右栏：自定义色板 -->
      <el-col :xs="24" :md="15">
        <el-card shadow="hover" class="custom-card">
          <template #header>
            <div class="card-header">
              <el-icon><Setting /></el-icon>
              <span>自定义色板（高级模式）</span>
            </div>
          </template>

          <!-- 颜色选择器 -->
          <div class="color-pickers">
            <div class="picker-row">
              <div
                v-for="color in colorList"
                :key="color.var"
                class="picker-item"
              >
                <label class="picker-label">{{ color.label }}</label>
                <el-color-picker
                  v-model="customColors[color.var]"
                  :show-alpha="false"
                  size="default"
                />
              </div>
            </div>
          </div>

          <el-divider />

          <!-- 滑动条 -->
          <div class="slider-group">
            <div class="slider-item">
              <div class="slider-head">
                <span>圆角大小</span>
                <el-tag size="small" type="info">{{ radiusValue }}px</el-tag>
              </div>
              <el-slider
                v-model="radiusValue"
                :min="0"
                :max="20"
                :step="1"
                show-stops
              />
            </div>

            <div class="slider-item">
              <div class="slider-head">
                <span>阴影强度</span>
                <el-tag size="small" type="info">{{ shadowLevel }}</el-tag>
              </div>
              <el-slider
                v-model="shadowLevel"
                :min="0"
                :max="3"
                :step="1"
                :marks="shadowMarks"
                show-stops
              />
            </div>
          </div>

          <el-divider />

          <!-- 应用按钮 -->
          <div class="action-bar">
            <el-button @click="loadFromCurrent">从当前主题继承</el-button>
            <el-button type="warning" @click="clearCustomColors">清空自定义</el-button>
            <el-button type="primary" :icon="MagicStickIcon" @click="applyCustom">应用自定义色板</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  MagicStick, Brush, Setting, RefreshLeft
} from '@element-plus/icons-vue'
import { useAppStore } from '../../stores/app'
import { useAuthStore } from '../../stores/auth'
import { isNightTime } from '../../composables/useSunTime'

const MagicStickIcon = MagicStick

const appStore = useAppStore()
const authStore = useAuthStore()

const THEME_KEY = 'uav_theme_v1'
const CUSTOM_VARS_KEY = 'uav_theme_custom_vars_v1'
const BLUE_FILTER_VAR = '--color-blue-filter'

const DARK_THEMES = ['dark', 'brand', 'highContrast']

const modeOptions = [
  { value: 'auto', label: '自动（跟随日落）' },
  { value: 'light', label: '浅色（固定）' },
  { value: 'dark', label: '深色（固定）' },
  { value: 'brand', label: '品牌（固定）' },
  { value: 'highContrast', label: '高对比度（固定）' }
]

const isNightNow = ref(isNightTime())
function refreshNight() {
  isNightNow.value = isNightTime()
}

const modeValue = computed({
  get() {
    return appStore.themeMode || 'auto'
  },
  set(val) {
    appStore.setThemeMode(val)
    refreshNight()
    applyBlueFilter()
  }
})

function onModeChange(val) {
  appStore.setThemeMode(val)
  refreshNight()
  applyBlueFilter()
  ElMessage.success(`已切换为 ${modeOptions.find(o => o.value === val)?.label || val} 模式`)
}

function forceRefreshNight() {
  appStore.refreshNightStatus()
  refreshNight()
  applyBlueFilter()
  ElMessage.info('日夜状态已刷新')
}

const presets = [
  {
    key: 'light',
    label: '浅色',
    description: '明亮清爽',
    colors: {
      bg: '#f5f7fa',
      surface: '#ffffff',
      text: '#1f2937',
      border: '#e5e7eb',
      primary: '#409EFF',
      success: '#67C23A',
      warning: '#E6A23C',
      danger: '#F56C6C',
      accent: '#f97316'
    },
    previewStyle: { background: '#f5f7fa', color: '#1f2937' }
  },
  {
    key: 'dark',
    label: '深色',
    description: '护眼深色',
    colors: {
      bg: '#0f172a',
      surface: '#1e293b',
      text: '#e2e8f0',
      border: '#334155',
      primary: '#60a5fa',
      success: '#4ade80',
      warning: '#fbbf24',
      danger: '#f87171',
      accent: '#fb923c'
    },
    previewStyle: { background: '#0f172a', color: '#e2e8f0' }
  },
  {
    key: 'brand',
    label: '品牌',
    description: '无人机橙蓝',
    colors: {
      bg: '#0c1a2f',
      surface: '#172554',
      text: '#f8fafc',
      border: '#334155',
      primary: '#38bdf8',
      success: '#4ade80',
      warning: '#f59e0b',
      danger: '#ef4444',
      accent: '#f97316'
    },
    previewStyle: { background: '#0c1a2f', color: '#f8fafc' }
  },
  {
    key: 'highContrast',
    label: '高对比度',
    description: '无障碍模式',
    colors: {
      bg: '#000000',
      surface: '#000000',
      text: '#ffffff',
      border: '#ffffff',
      primary: '#ffff00',
      success: '#00ff00',
      warning: '#ffaa00',
      danger: '#ff6b6b',
      accent: '#ff00ff'
    },
    previewStyle: { background: '#000000', color: '#ffffff' }
  }
]

const colorList = [
  { var: '--color-primary', label: '主色' },
  { var: '--color-bg', label: '背景色' },
  { var: '--color-surface', label: '表面色' },
  { var: '--color-text', label: '文字色' },
  { var: '--color-border', label: '边框色' },
  { var: '--color-success', label: '成功色' },
  { var: '--color-warning', label: '警告色' },
  { var: '--color-danger', label: '危险色' },
  { var: '--color-accent', label: '强调色' }
]

const defaultCustomColors = {
  '--color-primary': '#409EFF',
  '--color-bg': '#f5f7fa',
  '--color-surface': '#ffffff',
  '--color-text': '#1f2937',
  '--color-border': '#e5e7eb',
  '--color-success': '#67C23A',
  '--color-warning': '#E6A23C',
  '--color-danger': '#F56C6C',
  '--color-accent': '#f97316'
}

const customColors = ref({ ...defaultCustomColors })
const radiusValue = ref(8)
const shadowLevel = ref(1)

const shadowMarks = {
  0: '无',
  1: '轻',
  2: '中',
  3: '强'
}

const currentTheme = computed(() => (appStore.effectiveTheme || appStore.theme || 'light'))

const currentThemeLabel = computed(() => {
  const t = currentTheme.value
  const found = presets.find(p => p.key === t)
  return found ? found.label : '自定义'
})

const currentTagType = computed(() => {
  const t = currentTheme.value
  if (t === 'light') return 'success'
  if (t === 'dark') return 'info'
  if (t === 'brand') return 'warning'
  if (t === 'highContrast') return 'danger'
  return ''
})

function applyBlueFilter() {
  if (typeof document === 'undefined') return
  const activeTheme = appStore.effectiveTheme || appStore.theme || 'light'
  const isDark = DARK_THEMES.includes(activeTheme)
  document.documentElement.style.setProperty(BLUE_FILTER_VAR, isDark ? '0.85' : '1')
}

function applyDataTheme(themeKey) {
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', themeKey)
    localStorage.setItem(THEME_KEY, themeKey)
  }
  applyBlueFilter()
}

function switchTheme(key) {
  clearInlineCustomVars()
  localStorage.removeItem(CUSTOM_VARS_KEY)
  applyDataTheme(key)
  appStore.setThemeMode(key)
  refreshNight()
  ElMessage.success(`已切换为 ${presets.find(p => p.key === key)?.label || key} 主题`)
}

function resetToDefault() {
  clearInlineCustomVars()
  localStorage.removeItem(CUSTOM_VARS_KEY)
  applyDataTheme('light')
  appStore.setThemeMode('light')
  refreshNight()
  customColors.value = { ...defaultCustomColors }
  radiusValue.value = 8
  shadowLevel.value = 1
  ElMessage.success('已重置为默认浅色主题')
}

function clearInlineCustomVars() {
  if (typeof document === 'undefined') return
  colorList.forEach(item => {
    document.documentElement.style.removeProperty(item.var)
  })
  document.documentElement.style.removeProperty('--radius-md')
  document.documentElement.style.removeProperty('--shadow-md')
}

function applyCustom() {
  applyDataTheme('custom')
  appStore.setThemeMode('light')

  const vars = { ...customColors.value }
  Object.entries(vars).forEach(([k, v]) => {
    if (typeof document !== 'undefined') {
      document.documentElement.style.setProperty(k, v)
    }
  })
  if (typeof document !== 'undefined') {
    document.documentElement.style.setProperty('--radius-md', `${radiusValue.value}px`)
    document.documentElement.style.setProperty('--shadow-md', `0 ${4 * shadowLevel.value}px ${12 * shadowLevel.value}px rgba(0,0,0,0.12)`)
    vars['--radius-md'] = `${radiusValue.value}px`
    vars['--shadow-md'] = `0 ${4 * shadowLevel.value}px ${12 * shadowLevel.value}px rgba(0,0,0,0.12)`
  }

  localStorage.setItem(CUSTOM_VARS_KEY, JSON.stringify(vars))
  applyBlueFilter()
  ElMessage.success('已应用自定义色板')
}

function loadFromCurrent() {
  if (typeof document === 'undefined') return
  const styles = getComputedStyle(document.documentElement)
  colorList.forEach(item => {
    const val = styles.getPropertyValue(item.var)
    if (val) customColors.value[item.var] = val.trim()
  })
  ElMessage.info('已从当前主题继承颜色')
}

function clearCustomColors() {
  customColors.value = { ...defaultCustomColors }
  radiusValue.value = 8
  shadowLevel.value = 1
}

onMounted(() => {
  if (typeof document !== 'undefined') {
    const savedTheme = localStorage.getItem(THEME_KEY) || 'light'
    if (savedTheme && !document.documentElement.getAttribute('data-theme')) {
      document.documentElement.setAttribute('data-theme', savedTheme)
    }
    if (savedTheme === 'custom') {
      try {
        const raw = localStorage.getItem(CUSTOM_VARS_KEY)
        if (raw) {
          const vars = JSON.parse(raw)
          Object.entries(vars).forEach(([k, v]) => {
            if (k.startsWith('--color-') && customColors.value[k] !== undefined) {
              customColors.value[k] = v
            }
          })
        }
      } catch (_) {}
    }
  }
  refreshNight()
  applyBlueFilter()
})

watch(currentTheme, (newVal) => {
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', newVal)
    localStorage.setItem(THEME_KEY, newVal)
    applyBlueFilter()
  }
})
</script>

<style scoped>
.theme-customizer {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--color-surface, #fff);
  padding: 16px 20px;
  border-radius: var(--radius-md, 8px);
  border: 1px solid var(--color-border, #e5e7eb);
  box-shadow: var(--shadow-sm, 0 1px 2px rgba(0,0,0,0.08));
  color: var(--color-text, #1f2937);
  flex-wrap: wrap;
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text, #1f2937);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.label-text {
  font-size: 14px;
  color: var(--color-text-muted, #6b7280);
}

.main-body {
  margin: 0;
}

.preset-card,
.custom-card {
  background: var(--color-surface, #fff);
  color: var(--color-text, #1f2937);
  border: 1px solid var(--color-border, #e5e7eb);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
}

.preset-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.preset-item {
  padding: 12px;
  border: 2px solid var(--color-border, #e5e7eb);
  border-radius: var(--radius-md, 8px);
  cursor: pointer;
  transition: all var(--transition-fast, 0.15s ease);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preset-item:hover {
  border-color: var(--color-primary, #409EFF);
  transform: translateY(-1px);
}

.preset-item.active {
  border-color: var(--color-primary, #409EFF);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-primary, #409EFF) 25%, transparent);
}

.preset-preview {
  position: relative;
  height: 60px;
  border-radius: var(--radius-sm, 4px);
  overflow: hidden;
}

.preview-bg {
  position: absolute;
  inset: 0;
}

.preview-block {
  position: absolute;
  top: 12px;
  left: 12px;
  width: 50%;
  height: 36px;
  border: 1px solid;
  border-radius: var(--radius-sm, 4px);
}

.preview-dots {
  position: absolute;
  top: 18px;
  right: 12px;
  display: flex;
  gap: 6px;
}

.preview-dots span {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.preset-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.preset-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--color-text, #1f2937);
}

.preset-desc {
  font-size: 12px;
  color: var(--color-text-muted, #6b7280);
}

.color-swatches {
  display: flex;
  gap: 4px;
}

.swatch {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  border: 1px solid var(--color-border, #e5e7eb);
}

.color-pickers {
  margin-top: 4px;
}

.picker-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.picker-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px;
  background: color-mix(in srgb, var(--color-bg, #f5f7fa) 70%, transparent);
  border-radius: var(--radius-sm, 4px);
}

.picker-label {
  font-size: 13px;
  color: var(--color-text-muted, #6b7280);
}

.slider-group {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.slider-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.slider-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  color: var(--color-text, #1f2937);
}

.action-bar {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .picker-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
