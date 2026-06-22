<template>
  <div class="pbl-scheme-selector">
    <!-- 方案选择区域 -->
    <el-row :gutter="20">
      <el-col :span="8">
        <div class="scheme-group">
          <div class="scheme-group__title">PBL 方案</div>
          <el-select
            :model-value="selectedPbl"
            @update:model-value="$emit('update:selectedPbl', $event)"
            placeholder="选择PBL方案"
            style="width: 100%"
          >
            <el-option
              v-for="item in pblSchemes"
              :key="item.value"
              :label="`${item.label} (${item.value})`"
              :value="item.value"
            />
          </el-select>
          <div class="scheme-group__hint">{{ getPblDescription(selectedPbl) }}</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="scheme-group">
          <div class="scheme-group__title">积云方案</div>
          <el-select
            :model-value="selectedCumulus"
            @update:model-value="$emit('update:selectedCumulus', $event)"
            placeholder="选择积云方案"
            style="width: 100%"
          >
            <el-option
              v-for="item in cumulusSchemes"
              :key="item.value"
              :label="`${item.label} (${item.value})`"
              :value="item.value"
            />
          </el-select>
          <div class="scheme-group__hint">{{ getCumulusDescription(selectedCumulus) }}</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="scheme-group">
          <div class="scheme-group__title">微物理方案</div>
          <el-select
            :model-value="selectedMicro"
            @update:model-value="$emit('update:selectedMicro', $event)"
            placeholder="选择微物理方案"
            style="width: 100%"
          >
            <el-option
              v-for="item in microSchemes"
              :key="item.value"
              :label="`${item.label} (${item.value})`"
              :value="item.value"
            />
          </el-select>
          <div class="scheme-group__hint">{{ getMicroDescription(selectedMicro) }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 16px">
      <el-col :span="8">
        <div class="scheme-group">
          <div class="scheme-group__title">辐射方案</div>
          <el-select
            :model-value="selectedRadiation"
            @update:model-value="$emit('update:selectedRadiation', $event)"
            placeholder="选择辐射方案"
            style="width: 100%"
          >
            <el-option
              v-for="item in radiationSchemes"
              :key="item.value"
              :label="`${item.label} (${item.value})`"
              :value="item.value"
            />
          </el-select>
          <div class="scheme-group__hint">{{ getRadiationDescription(selectedRadiation) }}</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="scheme-group">
          <div class="scheme-group__title">陆面方案</div>
          <el-select
            :model-value="selectedLsm"
            @update:model-value="$emit('update:selectedLsm', $event)"
            placeholder="选择陆面方案"
            style="width: 100%"
          >
            <el-option
              v-for="item in lsmSchemes"
              :key="item.value"
              :label="`${item.label} (${item.value})`"
              :value="item.value"
            />
          </el-select>
          <div class="scheme-group__hint">{{ getLsmDescription(selectedLsm) }}</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="scheme-group">
          <div class="scheme-group__title">操作</div>
          <el-button type="primary" @click="handleExportConfig" style="width: 100%; margin-bottom: 8px">
            导出配置
          </el-button>
          <el-button @click="handleResetDefault" style="width: 100%">
            恢复默认
          </el-button>
        </div>
      </el-col>
    </el-row>

    <!-- 配置预览JSON -->
    <el-divider content-position="left">
      <span class="divider-text">配置预览 (namelist.input)</span>
    </el-divider>
    <div class="config-preview">
      <pre><code>{{ configPreviewJson }}</code></pre>
      <el-button
        class="copy-btn"
        size="small"
        :icon="copyIcon"
        @click="handleCopyConfig"
      >
        复制
      </el-button>
    </div>

    <!-- 方案对比表格 -->
    <el-divider content-position="left">
      <span class="divider-text">方案参数对比</span>
    </el-divider>
    <el-table :data="comparisonData" stripe style="width: 100%" max-height="360">
      <el-table-column prop="parameter" label="参数" width="200" fixed />
      <el-table-column prop="unit" label="单位" width="80" />
      <el-table-column
        v-for="scheme in selectedSchemesForCompare"
        :key="scheme"
        :label="scheme"
        :prop="scheme"
        min-width="120"
      >
        <template #default="{ row }">
          <span :class="{ 'highlight-value': row[scheme] === row.recommended }">
            {{ row[scheme] }}
          </span>
        </template>
      </el-table-column>
    </el-table>

    <!-- 方案兼容性提示 -->
    <el-alert
      v-if="compatibilityWarning"
      type="warning"
      :closable="false"
      show-icon
      style="margin-top: 16px"
    >
      <template #title>{{ compatibilityWarning }}</template>
    </el-alert>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { CopyDocument } from '@element-plus/icons-vue'

const props = defineProps<{
  selectedPbl: string
  selectedCumulus: string
  selectedMicro: string
  selectedRadiation: string
  selectedLsm: string
}>()

const emit = defineEmits<{
  'update:selectedPbl': [value: string]
  'update:selectedCumulus': [value: string]
  'update:selectedMicro': [value: string]
  'update:selectedRadiation': [value: string]
  'update:selectedLsm': [value: string]
}>()

const copyIcon = ref(CopyDocument)

// ---- 方案数据 ----
const pblSchemes = [
  { value: 'YSU', label: 'Yonsei University' },
  { value: 'MYJ', label: 'Mellor-Yamada-Janjic' },
  { value: 'MYNN', label: 'Mellor-Yamada Nakanishi-Niino' },
  { value: 'ACM2', label: 'Asymmetric Convective Model 2' },
  { value: 'BouLac', label: 'Bougeault-Lacarrere' },
  { value: 'UW', label: 'University of Washington' },
]

const cumulusSchemes = [
  { value: 'Kain-Fritsch', label: 'Kain-Fritsch' },
  { value: 'BMJ', label: 'Betts-Miller-Janjic' },
  { value: 'GD', label: 'Grell-Devenyi' },
  { value: 'G3', label: 'Grell 3D ensemble' },
  { value: 'Multi-scale KF', label: 'Multi-scale Kain-Fritsch' },
  { value: 'Tiedtke', label: 'Tiedtke' },
  { value: 'none', label: '无 (仅限高分辨率)' },
]

const microSchemes = [
  { value: 'Thompson', label: 'Thompson' },
  { value: 'Morrison', label: 'Morrison 2-moment' },
  { value: 'WSM6', label: 'WRF Single-Moment 6-class' },
  { value: 'NSSL', label: 'NSSL 2-moment' },
  { value: 'Lin', label: 'Lin et al.' },
  { value: 'WDM6', label: 'WRF Double-Moment 6-class' },
  { value: 'Goddard', label: 'NASA Goddard' },
]

const radiationSchemes = [
  { value: 'RRTMG', label: 'RRTMG (推荐)' },
  { value: 'RRTM', label: 'RRTM (长波)' },
  { value: 'Dudhia', label: 'Dudhia (短波)' },
  { value: 'CAM', label: 'CAM' },
  { value: 'Goddard', label: 'NASA Goddard' },
  { value: 'Fu-Liou-Gu', label: 'Fu-Liou-Gu' },
]

const lsmSchemes = [
  { value: 'Noah', label: 'Noah (推荐)' },
  { value: 'NoahMP', label: 'Noah-MP' },
  { value: 'CLM', label: 'Community Land Model' },
  { value: 'UCM', label: 'Urban Canopy Model' },
  { value: 'RUC', label: 'RUC Land Surface' },
  { value: 'PX', label: 'Pleim-Xiu' },
]

// ---- 方案描述 ----
function getPblDescription(scheme: string): string {
  const map: Record<string, string> = {
    YSU: '非局地闭合方案，适合大尺度模拟，对对流边界层表现好',
    MYJ: '1.5阶TKE闭合，适合稳定性边界层，分辨率要求较高',
    MYNN: 'MYJ改进版，更好的地表层处理，适合复杂地形',
    ACM2: '非局地+局地混合方案，过渡层表现好',
    BouLac: 'TKE闭合方案，适合稳定层结条件',
    UW: '简单方案，计算效率高，适合快速模拟',
  }
  return map[scheme] || '请选择方案'
}

function getCumulusDescription(scheme: string): string {
  const map: Record<string, string> = {
    'Kain-Fritsch': '最常用积云方案，基于质量通量，适合中尺度对流',
    BMJ: '基于调整的方案，对流触发机制独特',
    GD: '集合方法，每个网格独立触发，计算量大',
    G3: 'Grell 3D改进版，支持3D效果',
    'Multi-scale KF': '多尺度KF，适合不同网格分辨率',
    Tiedtke: 'ECMWF方案，适合全球/区域模式',
    none: '不使用积云参数化，网格距需<5km',
  }
  return map[scheme] || '请选择方案'
}

function getMicroDescription(scheme: string): string {
  const map: Record<string, string> = {
    Thompson: '包含冰相过程，适合冷云和混合相降水模拟',
    Morrison: '双矩方案，冰晶/水滴谱预报，适合云微物理研究',
    WSM6: '6类单矩方案，计算效率高，业务预报常用',
    NSSL: '双矩方案，适合强对流和降水预报',
    Lin: '简单高效，适合快速模拟',
    WDM6: 'WSM6双矩版本，更好的云滴谱处理',
    Goddard: 'NASA方案，包含冰相和霰过程',
  }
  return map[scheme] || '请选择方案'
}

function getRadiationDescription(scheme: string): string {
  const map: Record<string, string> = {
    RRTMG: 'GCM标准方案，长短波一体化，推荐使用',
    RRTM: '仅长波，需配合Dudhia短波使用',
    Dudhia: '仅短波，需配合RRTM长波使用',
    CAM: 'NCAR CAM方案，与CLM陆面方案配合好',
    Goddard: 'NASA方案，包含气溶胶效应',
    'Fu-Liou-Gu': '详细辐射传输，计算量大',
  }
  return map[scheme] || '请选择方案'
}

function getLsmDescription(scheme: string): string {
  const map: Record<string, string> = {
    Noah: '4层土壤方案，稳定可靠，推荐使用',
    NoahMP: 'Noah多物理版本，包含动态植被和雪盖',
    CLM: '多过程方案，生物地球化学耦合',
    UCM: '城市冠层模型，适合城市气象模拟',
    RUC: '快速更新循环方案，适合短时预报',
    PX: 'Pleim-Xiu方案，土壤水分/温度预报好',
  }
  return map[scheme] || '请选择方案'
}

// ---- 配置预览JSON ----
const configPreviewJson = computed(() => {
  const config: Record<string, string> = {
    bl_pbl_physics: props.selectedPbl,
    cu_physics: props.selectedCumulus === 'none' ? '0' : getCumulusCode(props.selectedCumulus),
    mp_physics: getMicroCode(props.selectedMicro),
    ra_lw_physics: getRadiationLwCode(props.selectedRadiation),
    ra_sw_physics: getRadiationSwCode(props.selectedRadiation),
    sf_surface_physics: getLsmCode(props.selectedLsm),
  }
  return JSON.stringify(config, null, 2)
})

function getCumulusCode(scheme: string): string {
  const map: Record<string, string> = {
    'Kain-Fritsch': '1', BMJ: '2', GD: '3', G3: '5',
    'Multi-scale KF': '11', Tiedtke: '14', none: '0',
  }
  return map[scheme] || '0'
}

function getMicroCode(scheme: string): string {
  const map: Record<string, string> = {
    Thompson: '8', Morrison: '10', WSM6: '6', NSSL: '27',
    Lin: '4', WDM6: '28', Goddard: '5',
  }
  return map[scheme] || '6'
}

function getRadiationLwCode(scheme: string): string {
  const map: Record<string, string> = {
    RRTMG: '4', RRTM: '1', Dudhia: '99', CAM: '3',
    Goddard: '5', 'Fu-Liou-Gu': '7',
  }
  return map[scheme] || '4'
}

function getRadiationSwCode(scheme: string): string {
  const map: Record<string, string> = {
    RRTMG: '4', RRTM: '99', Dudhia: '1', CAM: '3',
    Goddard: '5', 'Fu-Liou-Gu': '7',
  }
  return map[scheme] || '4'
}

function getLsmCode(scheme: string): string {
  const map: Record<string, string> = {
    Noah: '2', NoahMP: '2 (option 3)', CLM: '4', UCM: '2 (option 1)',
    RUC: '7', PX: '2 (option 7)',
  }
  return map[scheme] || '2'
}

// ---- 方案对比 ----
const selectedSchemesForCompare = computed(() => [props.selectedPbl, 'MYJ', 'MYNN'])

const comparisonData = ref([
  { parameter: '闭合类型', unit: '-', YSU: '非局地', MYJ: '局地TKE', MYNN: '局地TKE', recommended: '非局地' },
  { parameter: '垂直分层', unit: '层', YSU: '1.5', MYJ: '2.5', MYNN: '2.5', recommended: '1.5' },
  { parameter: 'TKE预报', unit: '-', YSU: '否', MYJ: '是', MYNN: '是', recommended: '是' },
  { parameter: '最小网格距', unit: 'km', YSU: '5', MYJ: '1', MYNN: '1', recommended: '1' },
  { parameter: '稳定边界层', unit: '评分', YSU: '3/5', MYJ: '4/5', MYNN: '5/5', recommended: '5/5' },
  { parameter: '对流边界层', unit: '评分', YSU: '5/5', MYJ: '3/5', MYNN: '4/5', recommended: '5/5' },
  { parameter: '计算效率', unit: '评分', YSU: '4/5', MYJ: '3/5', MYNN: '3/5', recommended: '4/5' },
  { parameter: '地形适用性', unit: '-', YSU: '一般', MYJ: '好', MYNN: '优秀', recommended: '优秀' },
])

// ---- 兼容性检查 ----
const compatibilityWarning = computed(() => {
  if (props.selectedCumulus === 'none' && props.selectedMicro === 'WSM6') {
    return 'WSM6方案在高分辨率无积云参数化时可能低估对流降水，建议使用Thompson或Morrison方案'
  }
  if (props.selectedPbl === 'BouLac' && props.selectedCumulus === 'GD') {
    return 'BouLac方案与GD积云方案组合可能导致边界层高度计算偏差'
  }
  if (props.selectedLsm === 'UCM' && props.selectedPbl === 'UW') {
    return 'UW PBL方案对城市冠层效应的处理不够精细，建议配合YSU或ACM2使用'
  }
  return ''
})

// ---- 操作 ----
function handleExportConfig() {
  const blob = new Blob([configPreviewJson.value], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'namelist_scheme_config.json'
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('配置已导出')
}

function handleCopyConfig() {
  navigator.clipboard.writeText(configPreviewJson.value).then(() => {
    ElMessage.success('配置已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

function handleResetDefault() {
  emit('update:selectedPbl', 'YSU')
  emit('update:selectedCumulus', 'Kain-Fritsch')
  emit('update:selectedMicro', 'Thompson')
  emit('update:selectedRadiation', 'RRTMG')
  emit('update:selectedLsm', 'Noah')
  ElMessage.info('已恢复默认配置')
}
</script>

<style scoped>
.pbl-scheme-selector {
  padding: 8px 0;
}

.scheme-group {
  margin-bottom: 4px;
}

.scheme-group__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary, #e0e0e0);
  margin-bottom: 8px;
}

.scheme-group__hint {
  font-size: 12px;
  color: var(--color-text-muted, #6a6a80);
  margin-top: 6px;
  line-height: 1.4;
}

.divider-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-secondary, #a0a0b0);
}

.config-preview {
  position: relative;
  background: var(--color-bg-secondary, #12121f);
  border: 1px solid var(--color-border, #2a2a40);
  border-radius: 6px;
  padding: 16px;
  max-height: 200px;
  overflow: auto;
}

.config-preview pre {
  margin: 0;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-text-primary, #e0e0e0);
}

.config-preview .copy-btn {
  position: absolute;
  top: 8px;
  right: 8px;
}

.highlight-value {
  color: var(--color-primary, #4fc3f7);
  font-weight: 600;
}

:deep(.el-divider__text) {
  background: var(--color-bg-card, #1a1a2e);
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
