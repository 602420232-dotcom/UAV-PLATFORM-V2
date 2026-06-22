<template>
  <div class="cumulus-analysis-view">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="page-header__left">
        <el-button
          class="back-btn"
          :icon="ArrowLeft"
          text
          @click="router.back()"
        >
          返回
        </el-button>
        <h1 class="page-title">积云参数化方案评估</h1>
      </div>
    </div>

    <!-- 方案选择区域 -->
    <el-card shadow="never" class="content-card">
      <template #header>
        <div class="card-header">
          <span>积云参数化方案选择</span>
          <el-tag type="info" effect="plain" size="small">基于 PBLSchemeSelector 扩展</el-tag>
        </div>
      </template>

      <PBLSchemeSelector
        v-model:selected-pbl="selectedPblScheme"
        v-model:selected-cumulus="selectedCumulusScheme"
        v-model:selected-micro="selectedMicroScheme"
        v-model:selected-radiation="selectedRadiationScheme"
        v-model:selected-lsm="selectedLsmScheme"
      />
    </el-card>

    <!-- 积云方案详细评估 -->
    <el-card shadow="never" class="content-card">
      <template #header>
        <div class="card-header">
          <span>积云方案性能评估</span>
          <el-radio-group v-model="evaluationMetric" size="small">
            <el-radio-button value="precipitation">降水预报</el-radio-button>
            <el-radio-button value="convection">对流触发</el-radio-button>
            <el-radio-button value="efficiency">计算效率</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="12">
          <div class="metric-chart" ref="cumulusChartRef" style="height: 360px"></div>
        </el-col>
        <el-col :span="12">
          <div class="scheme-evaluation">
            <h3 class="evaluation-title">{{ selectedCumulusScheme }} 方案评估详情</h3>
            <el-descriptions :column="1" border>
              <el-descriptions-item label="方案名称">{{ getCumulusLabel(selectedCumulusScheme) }}</el-descriptions-item>
              <el-descriptions-item label="适用尺度">{{ getCumulusScale(selectedCumulusScheme) }}</el-descriptions-item>
              <el-descriptions-item label="对流类型">{{ getCumulusType(selectedCumulusScheme) }}</el-descriptions-item>
              <el-descriptions-item label="计算开销">{{ getCumulusCost(selectedCumulusScheme) }}</el-descriptions-item>
              <el-descriptions-item label="推荐场景">{{ getCumulusRecommendation(selectedCumulusScheme) }}</el-descriptions-item>
            </el-descriptions>

            <div class="score-section">
              <div class="score-item">
                <span class="score-label">降水预报评分</span>
                <el-progress :percentage="getPrecipScore(selectedCumulusScheme)" :color="scoreColor" :stroke-width="16" />
              </div>
              <div class="score-item">
                <span class="score-label">对流触发准确性</span>
                <el-progress :percentage="getConvectionScore(selectedCumulusScheme)" :color="scoreColor" :stroke-width="16" />
              </div>
              <div class="score-item">
                <span class="score-label">计算效率</span>
                <el-progress :percentage="getEfficiencyScore(selectedCumulusScheme)" :color="scoreColor" :stroke-width="16" />
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 积云方案对比表 -->
    <el-card shadow="never" class="content-card">
      <template #header>
        <div class="card-header">
          <span>积云参数化方案综合对比</span>
        </div>
      </template>

      <el-table :data="cumulusComparisonData" stripe style="width: 100%">
        <el-table-column prop="scheme" label="方案" width="160" fixed />
        <el-table-column prop="physics" label="物理基础" width="140" />
        <el-table-column prop="scale" label="适用网格距" width="120" />
        <el-table-column prop="deepConv" label="深对流" width="100">
          <template #default="{ row }">
            <el-tag :type="row.deepConv ? 'success' : 'info'" size="small">
              {{ row.deepConv ? '支持' : '不支持' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="shallowConv" label="浅对流" width="100">
          <template #default="{ row }">
            <el-tag :type="row.shallowConv ? 'success' : 'info'" size="small">
              {{ row.shallowConv ? '支持' : '不支持' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ensemble" label="集合方法" width="100">
          <template #default="{ row }">
            <el-tag :type="row.ensemble ? 'success' : 'info'" size="small">
              {{ row.ensemble ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="strengths" label="优势" min-width="200" show-overflow-tooltip />
        <el-table-column prop="weaknesses" label="局限性" min-width="200" show-overflow-tooltip />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import PBLSchemeSelector from '@/components/research/PBLSchemeSelector.vue'
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'

echarts.use([
  BarChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  CanvasRenderer,
])

const router = useRouter()

// 方案选择状态
const selectedPblScheme = ref('YSU')
const selectedCumulusScheme = ref('Kain-Fritsch')
const selectedMicroScheme = ref('Thompson')
const selectedRadiationScheme = ref('RRTMG')
const selectedLsmScheme = ref('Noah')

// 评估指标
const evaluationMetric = ref('precipitation')
const cumulusChartRef = ref<HTMLDivElement>()
const cumulusChart = shallowRef<echarts.ECharts>()

const scoreColor = '#4fc3f7'

// 积云方案标签
function getCumulusLabel(scheme: string): string {
  const map: Record<string, string> = {
    'Kain-Fritsch': 'Kain-Fritsch (KF)',
    'BMJ': 'Betts-Miller-Janjic (BMJ)',
    'GD': 'Grell-Devenyi (GD)',
    'G3': 'Grell 3D (G3)',
    'Multi-scale KF': 'Multi-scale Kain-Fritsch (MSKF)',
    'Tiedtke': 'Tiedtke',
    'none': '无积云参数化',
  }
  return map[scheme] || scheme
}

// 适用尺度
function getCumulusScale(scheme: string): string {
  const map: Record<string, string> = {
    'Kain-Fritsch': '5-50 km',
    'BMJ': '10-50 km',
    'GD': '5-40 km',
    'G3': '5-40 km',
    'Multi-scale KF': '2-50 km',
    'Tiedtke': '10-100 km',
    'none': '< 5 km (显式对流)',
  }
  return map[scheme] || '未知'
}

// 对流类型
function getCumulusType(scheme: string): string {
  const map: Record<string, string> = {
    'Kain-Fritsch': '深对流 + 浅对流',
    'BMJ': '深对流',
    'GD': '深对流',
    'G3': '深对流 + 浅对流',
    'Multi-scale KF': '深对流 + 浅对流',
    'Tiedtke': '深对流 + 浅对流',
    'none': '显式解析',
  }
  return map[scheme] || '未知'
}

// 计算开销
function getCumulusCost(scheme: string): string {
  const map: Record<string, string> = {
    'Kain-Fritsch': '中等',
    'BMJ': '低',
    'GD': '高 (集合计算)',
    'G3': '高',
    'Multi-scale KF': '中等偏高',
    'Tiedtke': '中等',
    'none': '无额外开销',
  }
  return map[scheme] || '未知'
}

// 推荐场景
function getCumulusRecommendation(scheme: string): string {
  const map: Record<string, string> = {
    'Kain-Fritsch': '中尺度对流模拟，业务预报',
    'BMJ': '大尺度降水预报，热带区域',
    'GD': '研究用途，需要集合统计',
    'G3': '高分辨率模拟，复杂地形',
    'Multi-scale KF': '多尺度模拟，网格自适应',
    'Tiedtke': '全球/区域模式，ECMWF系统',
    'none': '大涡模拟，网格距 < 4km',
  }
  return map[scheme] || '通用'
}

// 评分数据
function getPrecipScore(scheme: string): number {
  const map: Record<string, number> = {
    'Kain-Fritsch': 85,
    'BMJ': 72,
    'GD': 78,
    'G3': 80,
    'Multi-scale KF': 88,
    'Tiedtke': 75,
    'none': 90,
  }
  return map[scheme] || 70
}

function getConvectionScore(scheme: string): number {
  const map: Record<string, number> = {
    'Kain-Fritsch': 82,
    'BMJ': 68,
    'GD': 85,
    'G3': 83,
    'Multi-scale KF': 86,
    'Tiedtke': 74,
    'none': 92,
  }
  return map[scheme] || 70
}

function getEfficiencyScore(scheme: string): number {
  const map: Record<string, number> = {
    'Kain-Fritsch': 80,
    'BMJ': 92,
    'GD': 55,
    'G3': 60,
    'Multi-scale KF': 70,
    'Tiedtke': 78,
    'none': 95,
  }
  return map[scheme] || 70
}

// 对比表格数据
const cumulusComparisonData = ref([
  {
    scheme: 'Kain-Fritsch',
    physics: '质量通量',
    scale: '5-50 km',
    deepConv: true,
    shallowConv: true,
    ensemble: false,
    strengths: '对流触发机制完善，浅对流处理较好',
    weaknesses: '对强对流的垂直输送可能过强',
  },
  {
    scheme: 'BMJ',
    physics: '调整方案',
    scale: '10-50 km',
    deepConv: true,
    shallowConv: false,
    ensemble: false,
    strengths: '计算效率高，大尺度降水预报稳定',
    weaknesses: '对流触发过于敏感，浅对流缺失',
  },
  {
    scheme: 'GD',
    physics: '集合平均',
    scale: '5-40 km',
    deepConv: true,
    shallowConv: false,
    ensemble: true,
    strengths: '集合方法减少方案依赖，统计稳健',
    weaknesses: '计算量大，对浅对流处理不足',
  },
  {
    scheme: 'G3',
    physics: '3D集合',
    scale: '5-40 km',
    deepConv: true,
    shallowConv: true,
    ensemble: true,
    strengths: '3D效果支持，浅对流改进',
    weaknesses: '计算复杂度高，参数调试困难',
  },
  {
    scheme: 'Multi-scale KF',
    physics: '多尺度质量通量',
    scale: '2-50 km',
    deepConv: true,
    shallowConv: true,
    ensemble: false,
    strengths: '自适应多尺度，灰区模拟表现好',
    weaknesses: '方案较新，验证案例相对较少',
  },
  {
    scheme: 'Tiedtke',
    physics: '质量通量',
    scale: '10-100 km',
    deepConv: true,
    shallowConv: true,
    ensemble: false,
    strengths: 'ECMWF验证，全球模式兼容性好',
    weaknesses: '对中尺度对流的细节刻画不足',
  },
])

// 图表数据
const chartData = computed(() => {
  const schemes = ['Kain-Fritsch', 'BMJ', 'GD', 'G3', 'Multi-scale KF', 'Tiedtke']
  let data: number[] = []
  if (evaluationMetric.value === 'precipitation') {
    data = schemes.map(s => getPrecipScore(s))
  } else if (evaluationMetric.value === 'convection') {
    data = schemes.map(s => getConvectionScore(s))
  } else {
    data = schemes.map(s => getEfficiencyScore(s))
  }
  return { schemes, data }
})

function initCumulusChart() {
  if (!cumulusChartRef.value) return
  cumulusChart.value = echarts.init(cumulusChartRef.value)
  updateCumulusChart()
}

function updateCumulusChart() {
  if (!cumulusChart.value) return
  const { schemes, data } = chartData.value
  const metricNames: Record<string, string> = {
    precipitation: '降水预报评分',
    convection: '对流触发准确性',
    efficiency: '计算效率评分',
  }
  const option: EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 15, 30, 0.9)',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0' },
      axisPointer: { type: 'shadow' },
    },
    grid: { left: 60, right: 30, top: 30, bottom: 60 },
    xAxis: {
      type: 'category',
      data: schemes,
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0', rotate: 20 },
    },
    yAxis: {
      type: 'value',
      max: 100,
      name: metricNames[evaluationMetric.value],
      nameTextStyle: { color: '#a0a0b0' },
      axisLine: { lineStyle: { color: '#2a2a40' } },
      axisLabel: { color: '#a0a0b0' },
      splitLine: { lineStyle: { color: '#2a2a40', type: 'dashed' } },
    },
    series: [{
      type: 'bar',
      data: data.map((val, idx) => ({
        value: val,
        itemStyle: {
          color: schemes[idx] === selectedCumulusScheme.value ? '#4fc3f7' : '#2a2a5a',
        },
      })),
      barWidth: '50%',
      label: {
        show: true,
        position: 'top',
        color: '#e0e0e0',
        formatter: '{c}',
      },
    }],
  }
  cumulusChart.value.setOption(option, true)
}

watch([evaluationMetric, selectedCumulusScheme], updateCumulusChart)

function handleResize() {
  cumulusChart.value?.resize()
}

onMounted(() => {
  initCumulusChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  cumulusChart.value?.dispose()
})
</script>

<style scoped>
.cumulus-analysis-view {
  padding: 24px;
  background: #1a1a2e;
  min-height: 100vh;
  color: #e0e0e0;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-header__left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  color: #a0a0b0;
  font-size: 14px;
  padding: 8px 12px;
}

.back-btn:hover {
  color: #e0e0e0;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #e0e0e0;
  margin: 0;
}

.content-card {
  background: #1f1f35;
  border-color: #2a2a40;
  color: #e0e0e0;
  margin-bottom: 20px;
}

.content-card :deep(.el-card__body) {
  padding: 20px;
}

.content-card :deep(.el-card__header) {
  border-bottom-color: #2a2a40;
  color: #e0e0e0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.metric-chart {
  width: 100%;
}

.scheme-evaluation {
  padding: 8px;
}

.evaluation-title {
  font-size: 16px;
  font-weight: 600;
  color: #e0e0e0;
  margin: 0 0 16px 0;
}

.score-section {
  margin-top: 20px;
}

.score-item {
  margin-bottom: 16px;
}

.score-label {
  display: block;
  font-size: 13px;
  color: #a0a0b0;
  margin-bottom: 6px;
}

:deep(.el-descriptions) {
  --el-descriptions-bg-color: #1a1a2e;
  --el-descriptions-table-border: 1px solid #2a2a40;
}

:deep(.el-descriptions__label) {
  background: #12121f;
  color: #a0a0b0;
}

:deep(.el-descriptions__content) {
  color: #e0e0e0;
}

:deep(.el-table) {
  --el-table-bg-color: #1f1f35;
  --el-table-tr-bg-color: #1f1f35;
  --el-table-header-bg-color: #12121f;
  --el-table-border-color: #2a2a40;
  --el-table-text-color: #e0e0e0;
  --el-table-header-text-color: #a0a0b0;
}
</style>
