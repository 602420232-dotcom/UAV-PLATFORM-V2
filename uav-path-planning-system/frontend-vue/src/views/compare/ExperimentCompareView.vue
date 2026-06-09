<template>
  <div class="experiment-compare">
    <!-- 顶部栏 -->
    <div class="top-bar">
      <div class="top-bar-left">
        <h2 class="page-title">实验对比工具</h2>
        <el-tag type="warning" effect="plain" size="default" class="demo-tag">
          <el-icon><MagicStick /></el-icon>&nbsp;演示模式 · 对比数据为本地模拟
        </el-tag>
      </div>

      <div class="top-bar-controls">
        <span class="control-label">对比维度</span>
        <el-select v-model="dimension" style="width: 180px" @change="onDimensionChange">
          <el-option label="气象模型" value="weather" />
          <el-option label="路径规划算法" value="path" />
          <el-option label="数据同化方案" value="assimilation" />
        </el-select>

        <el-select
          v-model="loadedGroupId"
          placeholder="已保存对比组"
          style="width: 180px"
          clearable
          @change="onLoadSavedGroup"
        >
          <el-option
            v-for="g in savedGroups"
            :key="g.id"
            :label="`${g.name}（${dimensionLabelMap[g.dimension]}）`"
            :value="g.id"
          />
        </el-select>

        <el-button type="primary" plain @click="openAddPlan">
          <el-icon><Plus /></el-icon>&nbsp;添加方案
        </el-button>

        <el-button type="warning" @click="openSaveGroup" :disabled="plans.length < 2">
          <el-icon><CollectionTag /></el-icon>&nbsp;保存为对比组
        </el-button>

        <el-button type="success" @click="exportCSV" :disabled="plans.length < 2">
          <el-icon><Document /></el-icon>&nbsp;导出 CSV
        </el-button>

        <el-button type="primary" @click="exportReport" :disabled="plans.length < 2">
          <el-icon><Download /></el-icon>&nbsp;导出对比报告
        </el-button>

        <el-tooltip content="仅显示差异超过 10% 的行 / 指标">
          <el-switch
            v-model="showDiffOnly"
            active-text="仅显示差异"
            inactive-text="全部"
            inline-prompt
            style="margin-left: 8px"
          />
        </el-tooltip>
      </div>
    </div>

    <!-- 主体 -->
    <div class="main-body">
      <!-- 左栏 30% · 方案卡片列表 -->
      <div class="left-panel">
        <div class="panel-title-row">
          <span class="panel-title">方案列表</span>
          <span class="panel-sub">{{ plans.length }} / 4</span>
        </div>

        <div v-if="plans.length === 0" class="empty-holder">
          <el-empty description="还没有方案，点击右上角「添加方案」开始对比" />
        </div>

        <div
          v-for="p in plans"
          :key="p.id"
          class="plan-card"
          :class="{ active: focusedPlanId === p.id }"
          @click="focusedPlanId = p.id"
        >
          <div class="plan-card-header">
            <span class="plan-color-dot" :style="{ background: planColor(p.id) }" />
            <span class="plan-name">{{ p.name }}</span>
            <el-button
              v-if="plans.length > 2"
              link
              type="danger"
              size="small"
              class="delete-btn"
              @click.stop="removePlan(p.id)"
            >
              删除
            </el-button>
          </div>
          <div class="plan-card-meta">
            {{ planMetaText(p) }}
          </div>
          <div class="plan-card-time">
            创建于 {{ formatTime(p.createdAt) }}
          </div>
        </div>

        <div v-if="plans.length > 0 && plans.length < 4" class="add-card" @click="openAddPlan">
          <el-icon><Plus /></el-icon>
          <span>添加方案</span>
        </div>
      </div>

      <!-- 右栏 70% · 对比视图 -->
      <div class="right-panel">
        <el-tabs v-model="activeTab" type="card" class="compare-tabs">
          <!-- Tab 1 · 指标对比 -->
          <el-tab-pane label="指标对比" name="metrics">
            <div v-if="plans.length < 2" class="empty-holder">
              <el-empty description="请至少添加 2 个方案以进行指标对比" />
            </div>
            <el-table
              v-else
              :data="metricsTableRows"
              border
              stripe
              style="width: 100%"
              height="560"
              class="metrics-table"
            >
              <el-table-column prop="metric" label="指标" width="220" fixed />
              <el-table-column prop="unit" label="单位" width="80" />
              <el-table-column
                v-for="p in plans"
                :key="p.id"
                :label="p.name"
                align="right"
                min-width="140"
              >
                <template #default="{ row }">
                  <span
                    :class="{
                      'diff-highlight': showDiffForCell(row, p.id),
                      'best-highlight': isBestForCell(row, p.id)
                    }"
                  >
                    {{ formatMetricValue(row, p.id) }}
                  </span>
                </template>
              </el-table-column>
            </el-table>
            <div class="legend-row">
              <span class="legend-item"><i class="legend-dot best" />最优值</span>
              <span class="legend-item"><i class="legend-dot diff" />差异超过 10%</span>
            </div>
          </el-tab-pane>

          <!-- Tab 2 · 曲线对比 -->
          <el-tab-pane label="曲线对比" name="curves">
            <div v-if="plans.length < 2" class="empty-holder">
              <el-empty description="请至少添加 2 个方案以查看曲线对比" />
            </div>
            <template v-else>
              <div class="curve-toolbar">
                <span class="control-label">Y 轴指标</span>
                <el-select v-model="curveMetric" style="width: 200px">
                  <el-option
                    v-for="m in curveMetricOptions"
                    :key="m.value"
                    :label="m.label"
                    :value="m.value"
                  />
                </el-select>
                <span class="ts-hint">图例可点击切换显示 / 隐藏对应方案</span>
              </div>
              <div ref="curveChartRef" class="chart-box" style="height: 520px" />
            </template>
          </el-tab-pane>

          <!-- Tab 3 · 差异摘要 -->
          <el-tab-pane label="差异摘要" name="summary">
            <div v-if="plans.length < 2" class="empty-holder">
              <el-empty description="请至少添加 2 个方案以查看差异摘要" />
            </div>
            <template v-else>
              <div v-for="(pair, idx) in diffPairs" :key="idx" class="diff-block">
                <div class="diff-title">
                  <el-tag
                    :color="planColor(plans[pair.a].id)"
                    effect="dark"
                    size="default"
                    style="color: #fff"
                  >
                    {{ plans[pair.a].name }}
                  </el-tag>
                  <span class="diff-vs">vs</span>
                  <el-tag
                    :color="planColor(plans[pair.b].id)"
                    effect="dark"
                    size="default"
                    style="color: #fff"
                  >
                    {{ plans[pair.b].name }}
                  </el-tag>
                  <span class="diff-sub">Top 10 差异条目（按百分比排序）</span>
                </div>

                <el-table :data="pair.rows" border stripe style="width: 100%">
                  <el-table-column prop="metric" label="指标" width="220" />
                  <el-table-column
                    :label="plans[pair.a].name"
                    prop="valueA"
                    align="right"
                    width="150"
                  />
                  <el-table-column
                    :label="plans[pair.b].name"
                    prop="valueB"
                    align="right"
                    width="150"
                  />
                  <el-table-column label="差异 %" align="right" width="120">
                    <template #default="{ row }">
                      <span
                        :class="row.pctDelta > 0 ? 'positive' : 'negative'"
                      >
                        {{ row.pctDelta > 0 ? '+' : '' }}{{ row.pctDelta.toFixed(2) }}%
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column label="结论" align="center">
                    <template #default="{ row }">
                      <el-tag
                        v-if="row.isBetter === 'A'"
                        type="success"
                        effect="light"
                        size="small"
                      >
                        {{ plans[pair.a].name }} 更优
                      </el-tag>
                      <el-tag
                        v-else-if="row.isBetter === 'B'"
                        type="danger"
                        effect="light"
                        size="small"
                      >
                        {{ plans[pair.b].name }} 更优
                      </el-tag>
                      <el-tag v-else type="info" effect="light" size="small">基本持平</el-tag>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </template>
          </el-tab-pane>

          <!-- Tab 4 · 原始数据 -->
          <el-tab-pane label="原始数据" name="raw">
            <div v-if="plans.length < 1" class="empty-holder">
              <el-empty description="暂无方案" />
            </div>
            <template v-else>
              <el-tabs v-model="rawTab" type="border-card">
                <el-tab-pane v-for="p in plans" :key="p.id" :label="p.name" :name="p.id">
                  <pre class="raw-pre">{{ JSON.stringify(p, null, 2) }}</pre>
                </el-tab-pane>
              </el-tabs>
            </template>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <!-- 添加方案 Dialog -->
    <el-dialog v-model="addDialogVisible" title="添加对比方案" width="560px">
      <el-form :model="addForm" label-width="120px">
        <el-form-item label="方案名称">
          <el-input v-model="addForm.name" placeholder="例如：WRF 基线" />
        </el-form-item>
        <el-form-item label="选择预设">
          <el-select v-model="addForm.preset" style="width: 100%" @change="onPresetChange">
            <el-option
              v-for="opt in presetOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>

        <el-divider content-position="left">可调参数（影响扰动）</el-divider>

        <template v-if="dimension === 'weather'">
          <el-form-item label="区域网格">
            <el-select v-model="addForm.domain" style="width: 100%">
              <el-option label="d01 · 36km · 华东" value="d01" />
              <el-option label="d02 · 12km · 长三角" value="d02" />
              <el-option label="d03 · 4km · 上海" value="d03" />
            </el-select>
          </el-form-item>
          <el-form-item label="起报时刻">
            <el-select v-model="addForm.cycle" style="width: 100%">
              <el-option label="00Z" value="00" />
              <el-option label="06Z" value="06" />
              <el-option label="12Z" value="12" />
              <el-option label="18Z" value="18" />
            </el-select>
          </el-form-item>
          <el-form-item label="PBL 方案">
            <el-select v-model="addForm.pbl" style="width: 100%">
              <el-option label="YSU" value="YSU" />
              <el-option label="MYJ" value="MYJ" />
              <el-option label="ACM2" value="ACM2" />
              <el-option label="BouLac" value="BouLac" />
            </el-select>
          </el-form-item>
          <el-form-item label="微物理">
            <el-select v-model="addForm.microphysics" style="width: 100%">
              <el-option label="WSM6" value="WSM6" />
              <el-option label="Thompson" value="Thompson" />
              <el-option label="Morrison" value="Morrison" />
            </el-select>
          </el-form-item>
        </template>

        <template v-if="dimension === 'path'">
          <el-form-item label="目标函数">
            <el-select v-model="addForm.objective" style="width: 100%">
              <el-option label="最短距离" value="distance" />
              <el-option label="最少能耗" value="energy" />
              <el-option label="最低风险" value="risk" />
            </el-select>
          </el-form-item>
          <el-form-item label="最大转弯角 (°)">
            <el-input-number
              v-model="addForm.maxTurn"
              :min="10"
              :max="120"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="障碍避让权重">
            <el-input-number
              v-model="addForm.obstacleWeight"
              :min="0"
              :max="10"
              :step="0.1"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="迭代次数">
            <el-input-number
              v-model="addForm.iterations"
              :min="50"
              :max="5000"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>
        </template>

        <template v-if="dimension === 'assimilation'">
          <el-form-item label="同化窗口 (h)">
            <el-input-number
              v-model="addForm.window"
              :min="1"
              :max="24"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="观测密度">
            <el-select v-model="addForm.obsDensity" style="width: 100%">
              <el-option label="低 (100 站)" value="low" />
              <el-option label="中 (500 站)" value="mid" />
              <el-option label="高 (2000 站)" value="high" />
            </el-select>
          </el-form-item>
          <el-form-item label="背景误差系数">
            <el-input-number
              v-model="addForm.bgError"
              :min="0.1"
              :max="3"
              :step="0.1"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="集合成员数">
            <el-input-number
              v-model="addForm.ensemble"
              :min="10"
              :max="200"
              controls-position="right"
              style="width: 100%"
            />
          </el-form-item>
        </template>
      </el-form>

      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmAddPlan">确认添加</el-button>
      </template>
    </el-dialog>

    <!-- 保存为对比组 Dialog -->
    <el-dialog v-model="saveGroupVisible" title="保存为对比组" width="420px">
      <el-form label-width="100px">
        <el-form-item label="对比组名称">
          <el-input v-model="saveGroupName" placeholder="例如：PBL 方案对比 - 2025Q1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="saveGroupVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmSaveGroup">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  MagicStick, Plus, CollectionTag, Document, Download
} from '@element-plus/icons-vue'

// ===== 基础配置 =====
const STORAGE_KEY = 'uav_compare_groups_v1'
const MAX_PLANS = 4

const dimensionLabelMap = {
  weather: '气象模型',
  path: '路径规划算法',
  assimilation: '数据同化方案'
}

// 每类对比维度的默认预设
const PRESET_WEATHER = [
  { value: 'WRF', label: 'WRF · 中尺度数值预报', baseline: true },
  { value: 'FengWu', label: '风乌 · AI 气象大模型', baseline: false },
  { value: 'TianZi', label: '天资 · 深度学习集合', baseline: false },
  { value: 'FengLei', label: '风雷 · 短临外推模型', baseline: false }
]
const PRESET_PATH = [
  { value: 'DE-RRT*', label: 'DE-RRT* · 差分进化快速扩展随机树', baseline: true },
  { value: 'DWA', label: 'DWA · 动态窗口法', baseline: false },
  { value: 'VRPTW', label: 'VRPTW · 带时间窗车辆路径', baseline: false }
]
const PRESET_ASSIMILATION = [
  { value: '3DVAR', label: '3DVAR · 三维变分', baseline: true },
  { value: '5DVAR', label: '5DVAR · 五维变分（含时间扩展）', baseline: false },
  { value: 'EnKF', label: 'EnKF · 集合卡尔曼滤波', baseline: false }
]

// 方案颜色池
const COLOR_POOL = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2']

// ===== 响应式状态 =====
const dimension = ref('weather')
const activeTab = ref('metrics')
const plans = ref([])
const focusedPlanId = ref(null)
const showDiffOnly = ref(false)

// 添加方案 Dialog
const addDialogVisible = ref(false)
const addForm = reactive({
  name: '',
  preset: '',
  // weather
  domain: 'd02',
  cycle: '00',
  pbl: 'YSU',
  microphysics: 'WSM6',
  // path
  objective: 'distance',
  maxTurn: 60,
  obstacleWeight: 2,
  iterations: 500,
  // assimilation
  window: 6,
  obsDensity: 'mid',
  bgError: 1.0,
  ensemble: 50
})

// 保存对比组 Dialog
const saveGroupVisible = ref(false)
const saveGroupName = ref('')
const savedGroups = ref([])
const loadedGroupId = ref(null)

// 曲线
const curveMetric = ref('')
const curveChartRef = ref(null)
let curveChart = null
const rawTab = ref('')

// ===== 工具 =====
function genId() {
  return 'p_' + Math.random().toString(36).slice(2, 10)
}

function formatTime(ts) {
  const d = new Date(ts)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// 基于字符串的稳定哈希，便于按方案 id 分配稳定颜色
function planColor(planId) {
  let h = 0
  for (let i = 0; i < planId.length; i++) h = (h * 31 + planId.charCodeAt(i)) | 0
  return COLOR_POOL[Math.abs(h) % COLOR_POOL.length]
}

function seedFromStr(s) {
  // 简单字符串哈希 → 用于确定性随机
  let h = 2166136261
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return Math.abs(h)
}

function makeRng(seed) {
  let s = seed || 1
  return () => {
    s = (s * 9301 + 49297) % 233280
    return s / 233280
  }
}

// ===== 对比维度基础数据结构 =====
// 每个指标: { key, label, unit, lowerIsBetter, baseline, noise }
const metricDefs = {
  weather: [
    { key: 'temp_rmse', label: '气温 RMSE', unit: '°C', lowerIsBetter: true, baseline: 2.1 },
    { key: 'temp_mae', label: '气温 MAE', unit: '°C', lowerIsBetter: true, baseline: 1.6 },
    { key: 'ws_rmse', label: '风速 RMSE', unit: 'm/s', lowerIsBetter: true, baseline: 1.8 },
    { key: 'ws_mae', label: '风速 MAE', unit: 'm/s', lowerIsBetter: true, baseline: 1.3 },
    { key: 'pres_rmse', label: '气压 RMSE', unit: 'hPa', lowerIsBetter: true, baseline: 3.2 },
    { key: 'crps', label: 'CRPS', unit: '', lowerIsBetter: true, baseline: 1.25 },
    { key: 'r_coeff', label: '相关系数 R', unit: '', lowerIsBetter: false, baseline: 0.86 },
    { key: 'bias', label: '系统偏差 Bias', unit: '°C', lowerIsBetter: true, baseline: 0.15 }
  ],
  path: [
    { key: 'distance', label: '总路径距离', unit: 'km', lowerIsBetter: true, baseline: 128.5 },
    { key: 'duration', label: '飞行时长', unit: 'min', lowerIsBetter: true, baseline: 92 },
    { key: 'energy', label: '能耗', unit: 'kWh', lowerIsBetter: true, baseline: 14.6 },
    { key: 'risk', label: '风险评分', unit: '', lowerIsBetter: true, baseline: 0.32 },
    { key: 'turn_avg', label: '平均转弯角度', unit: '°', lowerIsBetter: true, baseline: 28 }
  ],
  assimilation: [
    { key: 'rmse', label: '分析场 RMSE', unit: '', lowerIsBetter: true, baseline: 0.72 },
    { key: 'compute_time', label: '计算时长', unit: 's', lowerIsBetter: true, baseline: 145 },
    { key: 'convergence', label: '迭代收敛残差', unit: '', lowerIsBetter: true, baseline: 0.0045 },
    { key: 'obs_coverage', label: '观测覆盖率', unit: '%', lowerIsBetter: false, baseline: 78.5 }
  ]
}

// 每类维度的曲线可选指标
const curveMetricOptions = computed(() => {
  if (dimension.value === 'weather') {
    return [
      { label: '气温 (°C)', value: 'temperature' },
      { label: '风速 (m/s)', value: 'wind_speed' },
      { label: '气压 (hPa)', value: 'pressure' }
    ]
  }
  if (dimension.value === 'path') {
    return [
      { label: '累计距离 (km)', value: 'cum_distance' },
      { label: '瞬时能耗 (kWh/h)', value: 'energy_rate' },
      { label: '风险指数', value: 'risk_idx' }
    ]
  }
  return [
    { label: 'RMSE 演变', value: 'rmse_evo' },
    { label: '观测增量', value: 'obs_inc' },
    { label: '收敛残差', value: 'residual' }
  ]
})

// ===== Mock 数据生成 =====
function planMetaText(p) {
  if (p.dimension === 'weather') {
    return `${p.params.preset} · ${p.params.domain} · ${p.params.cycle}Z · PBL=${p.params.pbl} · MP=${p.params.microphysics}`
  }
  if (p.dimension === 'path') {
    return `${p.params.preset} · 目标=${p.params.objective} · 转弯≤${p.params.maxTurn}° · iter=${p.params.iterations}`
  }
  return `${p.params.preset} · 窗口=${p.params.window}h · 观测=${p.params.obsDensity} · 集合=${p.params.ensemble}`
}

function generateMockPlan(name, params, planDimension) {
  const seed = seedFromStr(name + JSON.stringify(params) + planDimension)
  const rng = makeRng(seed)
  const defs = metricDefs[planDimension]

  // 判断是否与 baseline 相同 → 同基线即共享 baseline 值
  const isBaselinePreset = () => {
    const presets = planDimension === 'weather'
      ? PRESET_WEATHER
      : planDimension === 'path'
        ? PRESET_PATH
        : PRESET_ASSIMILATION
    const found = presets.find(p => p.value === params.preset)
    return found ? found.baseline : false
  }

  // 参数差异影响扰动因子：参数不一样 → 扰动更大
  let perturbFactor = 0.04
  if (!isBaselinePreset()) perturbFactor += 0.05
  if (planDimension === 'weather') {
    if (params.domain !== 'd02') perturbFactor += 0.02
    if (params.cycle !== '00') perturbFactor += 0.015
    if (params.pbl !== 'YSU') perturbFactor += 0.025
    if (params.microphysics !== 'WSM6') perturbFactor += 0.02
  } else if (planDimension === 'path') {
    if (params.objective !== 'distance') perturbFactor += 0.03
    perturbFactor += Math.abs(params.maxTurn - 60) * 0.002
    perturbFactor += Math.abs(params.obstacleWeight - 2) * 0.02
    perturbFactor += Math.abs(params.iterations - 500) * 0.00005
  } else {
    perturbFactor += Math.abs(params.window - 6) * 0.008
    if (params.obsDensity !== 'mid') perturbFactor += 0.02
    perturbFactor += Math.abs(params.bgError - 1.0) * 0.05
    perturbFactor += Math.abs(params.ensemble - 50) * 0.0008
  }

  const metrics = {}
  defs.forEach((m) => {
    const sign = m.lowerIsBetter ? (isBaselinePreset() ? 1 : 1.1) : (isBaselinePreset() ? 1 : 0.92)
    const base = m.baseline * sign
    const noise = base * perturbFactor * (rng() - 0.3)
    let val = base + noise
    // 约束到合理范围
    if (m.key === 'r_coeff' || m.key === 'obs_coverage') val = Math.min(0.99, Math.max(0.5, val))
    if (m.lowerIsBetter) val = Math.max(0.001, val)
    metrics[m.key] = val
  })

  // 时间序列（24 小时，逐小时）
  const seriesLength = 24
  const timeAxis = Array.from({ length: seriesLength }, (_, i) => `${String(i).padStart(2, '0')}:00`)

  function seriesBase(metricKey) {
    // 基准曲线（小时演变）
    if (planDimension === 'weather') {
      if (metricKey === 'temperature') {
        return Array.from({ length: seriesLength }, (_, i) => {
          // 气温：夜间低 日间高
          return 18 + 8 * Math.sin(((i - 6) / 24) * 2 * Math.PI)
        })
      }
      if (metricKey === 'wind_speed') {
        return Array.from({ length: seriesLength }, (_, i) => 3 + 2.5 * Math.sin(i / 3) + (i % 7) * 0.1)
      }
      if (metricKey === 'pressure') {
        return Array.from({ length: seriesLength }, (_, i) => 1012 + 3 * Math.cos(i / 4) - i * 0.05)
      }
    }
    if (planDimension === 'path') {
      if (metricKey === 'cum_distance') {
        return Array.from({ length: seriesLength }, (_, i) => (i + 1) * 5.2)
      }
      if (metricKey === 'energy_rate') {
        return Array.from({ length: seriesLength }, (_, i) => 8 + 3 * Math.sin(i / 3) + (i % 5) * 0.4)
      }
      if (metricKey === 'risk_idx') {
        return Array.from({ length: seriesLength }, (_, i) => 0.2 + 0.25 * Math.abs(Math.sin(i / 2)))
      }
    }
    if (metricKey === 'rmse_evo') {
      return Array.from({ length: seriesLength }, (_, i) => 0.6 + 0.015 * i + 0.05 * Math.sin(i / 2))
    }
    if (metricKey === 'obs_inc') {
      return Array.from({ length: seriesLength }, (_, i) => 40 + 20 * Math.sin(i / 3) + i * 0.4)
    }
    if (metricKey === 'residual') {
      return Array.from({ length: seriesLength }, (_, i) => Math.max(0.0005, 0.02 * Math.exp(-i / 6)))
    }
    return Array.from({ length: seriesLength }, () => 1)
  }

  const series = {}
  curveMetricOptions.value.forEach((opt) => {
    const baseArr = seriesBase(opt.value)
    const perturbed = baseArr.map((v) => {
      const delta = v * perturbFactor * (rng() - 0.45)
      return +(v + delta).toFixed(3)
    })
    series[opt.value] = perturbed
  })

  return {
    id: genId(),
    name: name || params.preset,
    dimension: planDimension,
    params: { ...params },
    metrics,
    series: { timeAxis, ...series },
    createdAt: Date.now()
  }
}

// ===== 计算派生数据 =====
const presetOptions = computed(() => {
  if (dimension.value === 'weather') return PRESET_WEATHER
  if (dimension.value === 'path') return PRESET_PATH
  return PRESET_ASSIMILATION
})

const metricsTableRows = computed(() => {
  const defs = metricDefs[dimension.value]
  const rows = defs.map((m) => {
    const values = {}
    plans.value.forEach((p) => {
      values[p.id] = p.metrics[m.key] ?? 0
    })
    // 判断最优值
    const arr = plans.value.map((p) => ({ id: p.id, v: values[p.id] }))
    let bestId = null
    if (arr.length > 0) {
      const sorted = [...arr].sort((a, b) => (m.lowerIsBetter ? a.v - b.v : b.v - a.v))
      bestId = sorted[0].id
    }
    // 判断是否任何一格与平均值差异 > 10%
    const vals = arr.map((x) => x.v)
    const avg = vals.reduce((a, b) => a + b, 0) / (vals.length || 1)
    const hasDiff = vals.some((v) => avg > 1e-9 && Math.abs((v - avg) / avg) > 0.1)
    return {
      metric: m.label,
      unit: m.unit,
      key: m.key,
      values,
      bestId,
      hasDiff,
      lowerIsBetter: m.lowerIsBetter
    }
  })

  if (showDiffOnly.value) {
    return rows.filter((r) => r.hasDiff)
  }
  return rows
})

function formatMetricValue(row, planId) {
  const v = row.values[planId]
  if (v === undefined || v === null) return '-'
  if (Math.abs(v) >= 100) return v.toFixed(1)
  if (Math.abs(v) >= 10) return v.toFixed(2)
  return v.toFixed(3)
}

function isBestForCell(row, planId) {
  return row.bestId === planId
}
function showDiffForCell(row, planId) {
  if (!row.hasDiff) return false
  const v = row.values[planId]
  const vals = Object.values(row.values)
  const avg = vals.reduce((a, b) => a + b, 0) / (vals.length || 1)
  return avg > 1e-9 && Math.abs((v - avg) / avg) > 0.1
}

// 差异摘要 pairs (a,b)
const diffPairs = computed(() => {
  const pairs = []
  for (let i = 0; i < plans.value.length; i++) {
    for (let j = i + 1; j < plans.value.length; j++) {
      const a = i
      const b = j
      const defs = metricDefs[dimension.value]
      const rows = defs.map((m) => {
        const vA = plans.value[a].metrics[m.key]
        const vB = plans.value[b].metrics[m.key]
        const avg = (vA + vB) / 2
        const absDelta = vB - vA
        const pctDelta = avg > 1e-9 ? (absDelta / avg) * 100 : 0
        let isBetter = 'TIE'
        if (m.lowerIsBetter) {
          if (vA < vB - 1e-6) isBetter = 'A'
          else if (vB < vA - 1e-6) isBetter = 'B'
        } else {
          if (vA > vB + 1e-6) isBetter = 'A'
          else if (vB > vA + 1e-6) isBetter = 'B'
        }
        return {
          metric: m.label,
          valueA: formatMetricValue({ values: { [plans.value[a].id]: vA } }, plans.value[a].id),
          valueB: formatMetricValue({ values: { [plans.value[b].id]: vB } }, plans.value[b].id),
          pctDelta,
          isBetter,
          absPct: Math.abs(pctDelta)
        }
      }).sort((x, y) => y.absPct - x.absPct).slice(0, 10)
      pairs.push({ a, b, rows })
    }
  }
  return pairs
})

// ===== 事件处理 =====
function onDimensionChange() {
  // 切换维度：清空方案与已加载对比组引用
  if (plans.value.length > 0) {
    ElMessage.info(`已切换维度：${dimensionLabelMap[dimension.value]}，请重新添加方案`)
  }
  plans.value = []
  focusedPlanId.value = null
  loadedGroupId.value = null
  curveMetric.value = curveMetricOptions.value[0]?.value || ''
  nextTick(() => renderCurveChart())
}

function openAddPlan() {
  if (plans.value.length >= MAX_PLANS) {
    ElMessage.warning(`最多同时对比 ${MAX_PLANS} 个方案`)
    return
  }
  // 默认参数重置
  addForm.name = ''
  addForm.preset = presetOptions.value[plans.value.length % presetOptions.value.length]?.value || presetOptions.value[0].value
  addForm.domain = 'd02'
  addForm.cycle = '00'
  addForm.pbl = 'YSU'
  addForm.microphysics = 'WSM6'
  addForm.objective = 'distance'
  addForm.maxTurn = 60
  addForm.obstacleWeight = 2
  addForm.iterations = 500
  addForm.window = 6
  addForm.obsDensity = 'mid'
  addForm.bgError = 1.0
  addForm.ensemble = 50
  addDialogVisible.value = true
}

function onPresetChange() {
  if (!addForm.name) addForm.name = addForm.preset
}

function confirmAddPlan() {
  const name = (addForm.name || addForm.preset).trim()
  if (!name) {
    ElMessage.warning('请填写方案名称')
    return
  }
  if (!addForm.preset) {
    ElMessage.warning('请选择预设')
    return
  }
  const params = {
    preset: addForm.preset,
    domain: addForm.domain,
    cycle: addForm.cycle,
    pbl: addForm.pbl,
    microphysics: addForm.microphysics,
    objective: addForm.objective,
    maxTurn: addForm.maxTurn,
    obstacleWeight: addForm.obstacleWeight,
    iterations: addForm.iterations,
    window: addForm.window,
    obsDensity: addForm.obsDensity,
    bgError: addForm.bgError,
    ensemble: addForm.ensemble
  }
  const newPlan = generateMockPlan(name, params, dimension.value)
  plans.value.push(newPlan)
  focusedPlanId.value = newPlan.id
  addDialogVisible.value = false
  ElMessage.success(`已添加方案：${newPlan.name}`)
  if (!curveMetric.value) curveMetric.value = curveMetricOptions.value[0].value
  nextTick(() => renderCurveChart())
}

function removePlan(id) {
  ElMessageBox.confirm('确认删除该方案？', '提示', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    plans.value = plans.value.filter((p) => p.id !== id)
    if (focusedPlanId.value === id && plans.value.length > 0) {
      focusedPlanId.value = plans.value[0].id
    }
    ElMessage.success('已删除')
    nextTick(() => renderCurveChart())
  }).catch(() => {})
}

// ===== 对比组保存 / 加载 =====
function loadSavedGroups() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) { savedGroups.value = []; return }
    const parsed = JSON.parse(raw)
    savedGroups.value = Array.isArray(parsed) ? parsed : []
  } catch (e) {
    console.warn('读取 savedGroups 失败', e)
    savedGroups.value = []
  }
}

function persistSavedGroups() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(savedGroups.value))
  } catch (e) {
    ElMessage.error('localStorage 写入失败：' + e.message)
  }
}

function openSaveGroup() {
  saveGroupName.value = ''
  saveGroupVisible.value = true
}

function confirmSaveGroup() {
  const name = (saveGroupName.value || '').trim()
  if (!name) {
    ElMessage.warning('请填写对比组名称')
    return
  }
  if (plans.value.length < 2) {
    ElMessage.warning('至少需要 2 个方案')
    return
  }
  const group = {
    id: 'g_' + Math.random().toString(36).slice(2, 10),
    name,
    dimension: dimension.value,
    plans: plans.value.map((p) => ({
      id: p.id,
      name: p.name,
      params: p.params
    })),
    createdAt: Date.now()
  }
  savedGroups.value.push(group)
  persistSavedGroups()
  saveGroupVisible.value = false
  ElMessage.success(`对比组「${name}」已保存`)
}

function onLoadSavedGroup(id) {
  if (!id) return
  const group = savedGroups.value.find((g) => g.id === id)
  if (!group) return
  // 切换到对应维度
  if (dimension.value !== group.dimension) {
    dimension.value = group.dimension
  }
  // 根据方案 params 重新生成数据（保持可复现）
  plans.value = group.plans.map((gp) => {
    const p = generateMockPlan(gp.name, gp.params, group.dimension)
    p.createdAt = group.createdAt
    return p
  })
  focusedPlanId.value = plans.value[0]?.id || null
  if (!curveMetric.value && curveMetricOptions.value.length > 0) {
    curveMetric.value = curveMetricOptions.value[0].value
  }
  ElMessage.success(`已加载对比组：${group.name}`)
  nextTick(() => renderCurveChart())
}

// ===== 曲线渲染 =====
function renderCurveChart() {
  if (!curveChartRef.value) return
  if (plans.value.length < 2) {
    if (curveChart) { curveChart.dispose(); curveChart = null }
    return
  }
  if (!curveChart) curveChart = echarts.init(curveChartRef.value)

  const metric = curveMetric.value
  const option = {
    tooltip: { trigger: 'axis' },
    legend: {
      data: plans.value.map((p) => p.name),
      top: 8
    },
    grid: { left: 48, right: 24, top: 48, bottom: 40 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: plans.value[0].series.timeAxis || []
    },
    yAxis: { type: 'value', scale: true },
    series: plans.value.map((p) => ({
      name: p.name,
      type: 'line',
      smooth: true,
      showSymbol: false,
      lineStyle: { width: 2 },
      itemStyle: { color: planColor(p.id) },
      data: p.series[metric] || []
    }))
  }
  curveChart.setOption(option, true)
}

function onResize() {
  if (curveChart) curveChart.resize()
}

// ===== 导出 =====
function exportCSV() {
  if (plans.value.length < 2) return
  const defs = metricDefs[dimension.value]
  const header = ['指标', '单位', ...plans.value.map((p) => p.name)]
  const lines = [header.join(',')]
  defs.forEach((m) => {
    const row = [m.label, m.unit]
    plans.value.forEach((p) => row.push(String(p.metrics[m.key] ?? '')))
    lines.push(row.join(','))
  })
  lines.push('')
  lines.push(`对比维度,${dimensionLabelMap[dimension.value]}`)
  lines.push(`导出时间,${new Date().toISOString()}`)

  const blob = new Blob(['\uFEFF' + lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
  triggerDownload(blob, `实验对比-${dimensionLabelMap[dimension.value]}-${Date.now()}.csv`)
  ElMessage.success('CSV 已导出')
}

function exportReport() {
  if (plans.value.length < 2) return
  const defs = metricDefs[dimension.value]
  const lines = []
  lines.push('=== 实验对比报告 ===')
  lines.push(`维度：${dimensionLabelMap[dimension.value]}`)
  lines.push(`导出时间：${new Date().toLocaleString()}`)
  lines.push('')
  lines.push(`方案：${plans.value.map((p) => p.name).join(' / ')}`)
  lines.push('')
  lines.push('--- 指标对比 ---')
  const header = ['指标', '单位', ...plans.value.map((p) => p.name), '最优']
  lines.push(header.join('\t'))
  defs.forEach((m) => {
    const vals = plans.value.map((p) => (p.metrics[m.key] ?? '').toString())
    const arr = plans.value.map((p) => ({ id: p.id, v: p.metrics[m.key] ?? 0 }))
    const sorted = [...arr].sort((a, b) => (m.lowerIsBetter ? a.v - b.v : b.v - a.v))
    const best = sorted[0] ? plans.value.find((p) => p.id === sorted[0].id)?.name : '-'
    lines.push([m.label, m.unit, ...vals, best].join('\t'))
  })
  lines.push('')
  lines.push('--- 方案参数 ---')
  plans.value.forEach((p) => {
    lines.push(`[${p.name}]`)
    Object.entries(p.params).forEach(([k, v]) => lines.push(`  ${k}: ${v}`))
    lines.push('')
  })

  const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8;' })
  triggerDownload(blob, `实验对比报告-${dimensionLabelMap[dimension.value]}-${Date.now()}.txt`)
  ElMessage.success('对比报告已导出')
}

function triggerDownload(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

// ===== 生命周期 =====
onMounted(() => {
  loadSavedGroups()
  // 默认 Y 轴指标
  if (curveMetricOptions.value.length > 0 && !curveMetric.value) {
    curveMetric.value = curveMetricOptions.value[0].value
  }
  window.addEventListener('resize', onResize)
  nextTick(() => renderCurveChart())
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  if (curveChart) { curveChart.dispose(); curveChart = null }
})

watch(curveMetric, () => renderCurveChart())
watch(activeTab, (tab) => {
  if (tab === 'curves') {
    nextTick(() => {
      if (curveChart) curveChart.resize()
      else renderCurveChart()
    })
  }
})
</script>

<style scoped>
.experiment-compare {
  min-height: 100%;
  background: #f5f7fa;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #24292f;
  margin: 0;
}

.top-bar-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.control-label {
  font-size: 13px;
  color: #606266;
}

.main-body {
  display: grid;
  grid-template-columns: 30% 1fr;
  gap: 16px;
}

.left-panel {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
  min-height: 600px;
}

.panel-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 6px 12px;
  border-bottom: 1px dashed #e4e7ed;
  margin-bottom: 12px;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.panel-sub {
  font-size: 12px;
  color: #909399;
}

.empty-holder {
  padding: 24px 0;
}

.plan-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
  background: #fafbfc;
}

.plan-card:hover {
  background: #f0f6ff;
  border-color: #91caff;
  transform: translateY(-1px);
}

.plan-card.active {
  border-color: #1890ff;
  background: #e6f4ff;
  box-shadow: 0 2px 6px rgba(24, 144, 255, 0.12);
}

.plan-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.plan-color-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.plan-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delete-btn {
  flex-shrink: 0;
}

.plan-card-meta {
  font-size: 12px;
  color: #606266;
  line-height: 1.6;
  margin-top: 6px;
  word-break: break-all;
}

.plan-card-time {
  font-size: 11px;
  color: #909399;
  margin-top: 6px;
}

.add-card {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  color: #909399;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 13px;
}

.add-card:hover {
  border-color: #1890ff;
  color: #1890ff;
  background: #f0f6ff;
}

.right-panel {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 12px;
  min-height: 600px;
}

.compare-tabs {
  margin-top: 4px;
}

.metrics-table {
  margin-top: 8px;
}

.diff-highlight {
  color: #f5222d;
  font-weight: 600;
}

.best-highlight {
  color: #389e0d;
  font-weight: 700;
  background: #f6ffed;
  padding: 2px 6px;
  border-radius: 4px;
}

.legend-row {
  margin-top: 12px;
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #606266;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.legend-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-dot.best { background: #52c41a; }
.legend-dot.diff { background: #f5222d; }

.curve-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.ts-hint {
  font-size: 12px;
  color: #909399;
  margin-left: 8px;
}

.chart-box {
  width: 100%;
}

.diff-block {
  margin-top: 12px;
}

.diff-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 14px;
}

.diff-vs {
  color: #909399;
  font-weight: 600;
}

.diff-sub {
  color: #909399;
  font-size: 12px;
  margin-left: 8px;
}

.positive { color: #f5222d; font-weight: 600; }
.negative { color: #52c41a; font-weight: 600; }

.raw-pre {
  background: #f6f8fa;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 16px;
  max-height: 520px;
  overflow: auto;
  font-size: 12px;
  line-height: 1.6;
  color: #303133;
}

@media (max-width: 980px) {
  .main-body {
    grid-template-columns: 1fr;
  }
  .left-panel { min-height: auto; }
}
</style>
