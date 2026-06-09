<template>
  <div class="data-assimilation">
    <el-alert
      title="演示模式 · 以下数据为本地模拟结果，仅用于前端 UI 演示"
      type="warning"
      :closable="false"
      show-icon
      class="demo-alert"
    />

    <!-- 顶部筛选栏 -->
    <el-card shadow="never" class="panel filter-panel">
      <el-form :inline="true" size="default" class="filter-form">
        <el-form-item label="同化方法">
          <el-select v-model="form.method">
            <el-option label="贝叶斯同化" value="bayes" />
            <el-option label="EnKF" value="enkf" />
            <el-option label="3D-VAR" value="3dvar" />
            <el-option label="4D-VAR" value="4dvar" />
          </el-select>
        </el-form-item>
        <el-form-item label="气象源">
          <el-select v-model="form.source">
            <el-option label="WRF" value="wrf" />
            <el-option label="风乌" value="fengwu" />
            <el-option label="天资" value="tianzi" />
            <el-option label="风雷" value="fenglei" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="form.range"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始"
            end-placeholder="结束"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="running" :disabled="!authStore.hasAction('assimilation:execute')" @click="runAssim">运行同化</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="16" class="main-row">
      <!-- 左侧 同化配置 -->
      <el-col :span="8">
        <el-card shadow="never" class="panel">
          <template #header><div class="panel-title">数据源权重</div></template>
          <div class="weight-tip">当前总和：<b>{{ weightTotal.toFixed(2) }}</b></div>
          <div v-for="(w, i) in weights" :key="i" class="slider-row">
            <div class="slider-head">
              <span class="slider-label">{{ w.label }}</span>
              <span class="slider-val">{{ Math.round(w.value * 100) }}%</span>
            </div>
            <el-slider
              v-model="w.value"
              :min="0"
              :max="1"
              :step="0.05"
              :show-tooltip="false"
            />
          </div>
        </el-card>

        <el-card shadow="never" class="panel mt-12">
          <template #header><div class="panel-title">参数设置</div></template>
          <el-form label-position="top" size="small">
            <el-form-item label="观测误差方差">
              <el-input v-model="params.obsVar" :disabled="!authStore.hasAction('assimilation:config')" />
            </el-form-item>
            <el-form-item label="模型误差方差">
              <el-input v-model="params.modelVar" :disabled="!authStore.hasAction('assimilation:config')" />
            </el-form-item>
            <el-form-item label="集合大小（EnKF）">
              <el-input v-model="params.ensemble" :disabled="!authStore.hasAction('assimilation:config')" />
            </el-form-item>
          </el-form>
        </el-card>

        <el-card shadow="never" class="panel mt-12">
          <template #header><div class="panel-title">同化区域</div></template>
          <el-form label-position="top" size="small">
            <el-row :gutter="8">
              <el-col :span="12">
                <el-form-item label="经度 起">
                  <el-input v-model="area.lngStart" :disabled="!authStore.hasAction('assimilation:config')" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="经度 止">
                  <el-input v-model="area.lngEnd" :disabled="!authStore.hasAction('assimilation:config')" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="8">
              <el-col :span="12">
                <el-form-item label="纬度 起">
                  <el-input v-model="area.latStart" :disabled="!authStore.hasAction('assimilation:config')" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="纬度 止">
                  <el-input v-model="area.latEnd" :disabled="!authStore.hasAction('assimilation:config')" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-card>

        <el-card shadow="never" class="panel mt-12">
          <template #header><div class="panel-title">同化时间窗</div></template>
          <el-form label-position="top" size="small">
            <el-form-item label="起始时间">
              <el-date-picker
                v-model="timeWin.start"
                type="datetime"
                placeholder="选择起始时间"
                style="width: 100%"
                :disabled="!authStore.hasAction('assimilation:config')"
              />
            </el-form-item>
            <el-form-item label="结束时间">
              <el-date-picker
                v-model="timeWin.end"
                type="datetime"
                placeholder="选择结束时间"
                style="width: 100%"
                :disabled="!authStore.hasAction('assimilation:config')"
              />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧 结果可视化 -->
      <el-col :span="16">
        <template v-if="authStore.hasAction('assimilation:view')">
        <!-- 同化前后误差对比 4列 -->
        <el-row :gutter="12">
          <el-col :span="6" v-for="(m, i) in metrics4" :key="i">
            <el-card shadow="never" class="panel metric-card">
              <div class="m-title">{{ m.label }}</div>
              <div class="m-block">
                <div class="m-sub">原始</div>
                <div class="m-big before">{{ m.before }}</div>
              </div>
              <div class="m-block">
                <div class="m-sub">同化后</div>
                <div class="m-big after">{{ m.after }}</div>
              </div>
              <div class="m-improve">
                <el-tag size="small" type="success" effect="dark">↓ {{ m.improve }}%</el-tag>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 多模型融合时间序列 -->
        <el-card shadow="never" class="panel mt-12">
          <template #header>
            <div class="panel-title-inline">
              <span>多模型融合时间序列（24h）</span>
              <div class="legend">
                <span class="legend-item"><i class="dot wrf"></i>WRF</span>
                <span class="legend-item"><i class="dot fengwu"></i>风乌</span>
                <span class="legend-item"><i class="dot tianzi"></i>天资</span>
                <span class="legend-item"><i class="dot fenglei"></i>风雷</span>
                <span class="legend-item"><i class="dot fusion"></i>融合值</span>
              </div>
            </div>
          </template>

          <div class="bar-chart">
            <div
              v-for="(row, hi) in barRows"
              :key="hi"
              class="bar-hour"
              :title="'小时 ' + hi + '：' + row.map((r) => r.model + '=' + r.val).join(' / ')"
            >
              <div class="bar-cols">
                <div v-for="(b, bi) in row" :key="bi" class="bar-col">
                  <div
                    class="bar"
                    :class="'bar-' + b.key"
                    :style="{ height: b.h + '%' }"
                  ></div>
                </div>
              </div>
              <div class="bar-label">{{ hi }}h</div>
            </div>
          </div>
          <div class="y-axis">
            <span>100</span><span>75</span><span>50</span><span>25</span><span>0</span>
          </div>
        </el-card>

        <!-- 不确定性热力图 -->
        <el-card shadow="never" class="panel mt-12">
          <template #header>
            <div class="panel-title-inline">
              <span>不确定性空间分布</span>
              <div class="legend">
                <span class="legend-item"><i class="heat low"></i>低</span>
                <span class="legend-item"><i class="heat mid"></i>中</span>
                <span class="legend-item"><i class="heat high"></i>高</span>
              </div>
            </div>
          </template>
          <div class="heat-grid">
            <div
              v-for="(cell, i) in heatCells"
              :key="i"
              class="heat-cell"
              :style="{ background: cell.color }"
              :title="'不确定性：' + cell.val"
            ></div>
          </div>
        </el-card>

        <!-- 同化摘要表格 -->
        <el-card shadow="never" class="panel mt-12">
          <template #header><div class="panel-title">同化摘要</div></template>
          <el-table :data="summaryTable" size="small" border stripe>
            <el-table-column prop="metric" label="指标" width="180" />
            <el-table-column prop="before" label="原始值" align="right" />
            <el-table-column prop="after" label="同化值" align="right" />
            <el-table-column label="改善程度" align="right">
              <template #default="{ row }">
                <el-tag :type="row.improve > 0 ? 'success' : 'info'" size="small">
                  {{ row.improve > 0 ? '↓ ' + row.improve + '%' : row.improve + '%' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
        </template>
        <el-empty v-else description="无权限查看同化结果" />
      </el-col>
    </el-row>

    <!-- 底部日志 -->
    <el-card shadow="never" class="panel mt-12 log-panel">
      <template #header><div class="panel-title">同化日志</div></template>
      <el-table :data="logs" size="small" border>
        <el-table-column prop="time" label="时间" width="170" />
        <el-table-column label="事件" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="row.type">{{ row.event }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="msg" label="消息" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const form = reactive({
  method: 'bayes',
  source: 'wrf',
  range: []
})

const weights = ref([
  { label: 'WRF', value: 0.3, key: 'wrf' },
  { label: '风乌', value: 0.15, key: 'fengwu' },
  { label: '天资', value: 0.25, key: 'tianzi' },
  { label: '风雷', value: 0.3, key: 'fenglei' }
])
const weightTotal = computed(() => weights.value.reduce((s, x) => s + x.value, 0))

const params = reactive({ obsVar: '0.85', modelVar: '1.20', ensemble: '64' })
const area = reactive({
  lngStart: '115.50',
  lngEnd: '117.50',
  latStart: '39.40',
  latEnd: '40.60'
})
const timeWin = reactive({ start: '', end: '' })

const running = ref(false)

const metrics4 = ref([
  { label: '温度 (°C)', before: '2.14', after: '0.78', improve: 63.5 },
  { label: '湿度 (%)', before: '4.82', after: '1.65', improve: 65.8 },
  { label: '风速 (m/s)', before: '1.92', after: '0.92', improve: 52.1 },
  { label: '气压 (hPa)', before: '2.40', after: '1.12', improve: 53.3 }
])

// 24h × 5模型 的条形数据
const models = ['wrf', 'fengwu', 'tianzi', 'fenglei', 'fusion']
const modelColors = {
  wrf: '#409eff',
  fengwu: '#67c23a',
  tianzi: '#e6a23c',
  fenglei: '#f56c6c',
  fusion: '#909399'
}
function seedRand(seed) {
  let s = seed
  return () => {
    s = (s * 9301 + 49297) % 233280
    return s / 233280
  }
}
const rand = seedRand(7)
const barRows = computed(() => {
  const rows = []
  for (let h = 0; h < 24; h++) {
    const col = []
    for (let m = 0; m < models.length; m++) {
      const base = 35 + Math.sin((h + m * 2) / 3) * 20 + rand() * 20
      col.push({
        key: models[m],
        model: models[m],
        val: Math.round(base),
        h: Math.min(100, Math.max(5, base))
      })
    }
    rows.push(col)
  }
  return rows
})

// 热力图 10x10
const heatCells = computed(() => {
  const cells = []
  const r2 = seedRand(42)
  for (let i = 0; i < 100; i++) {
    const v = r2()
    let color = 'rgba(103,194,58,0.6)'
    if (v > 0.35) color = 'rgba(230,162,60,0.7)'
    if (v > 0.7) color = 'rgba(245,108,108,0.8)'
    cells.push({ val: v.toFixed(2), color })
  }
  return cells
})

const summaryTable = ref([
  { metric: '平均绝对误差 (MAE)', before: '2.82', after: '1.12', improve: 60 },
  { metric: '均方根误差 (RMSE)', before: '3.41', after: '1.36', improve: 60 },
  { metric: '相关系数 R', before: '0.78', after: '0.93', improve: 19 },
  { metric: '偏差 Bias', before: '0.68', after: '0.12', improve: 82 },
  { metric: '空间一致性评分', before: '72', after: '91', improve: 26 },
  { metric: '集合离散度', before: '1.85', after: '0.92', improve: 50 }
])

const logs = ref([
  { time: '2025-01-10 08:00:12', event: '启动', type: 'info', msg: '同化系统初始化，加载观测数据 1.2GB' },
  { time: '2025-01-10 08:00:45', event: '观测', type: 'success', msg: '收集到 1248 个观测点，剔除异常值 18 个' },
  { time: '2025-01-10 08:01:10', event: '分析', type: 'warning', msg: 'EnKF 集合大小 64，开始卡尔曼滤波更新' },
  { time: '2025-01-10 08:01:52', event: '分析', type: 'success', msg: '分析步完成，RMSE 从 3.41 降至 1.36' },
  { time: '2025-01-10 08:02:10', event: '输出', type: 'success', msg: '融合场写入 netCDF，大小 248MB' },
  { time: '2025-01-10 08:02:33', event: '输出', type: 'info', msg: '摘要指标已上报，改善率 55%' },
  { time: '2025-01-10 08:03:01', event: '观测', type: 'success', msg: '新一批观测点 864 个，延迟 2.1s' },
  { time: '2025-01-10 08:03:40', event: '分析', type: 'info', msg: '时间窗滚动同化，进入下一周期' }
])

function runAssim() {
  running.value = true
  setTimeout(() => (running.value = false), 1500)
}
// 保留引用
void modelColors
</script>

<style scoped>
.data-assimilation {
  padding: 16px;
  background: #f5f7fa;
  min-height: 100%;
  font-size: 13px;
}
.demo-alert {
  margin-bottom: 12px;
}
.panel {
  border-radius: 8px;
}
.panel-title {
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}
.panel-title-inline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: #303133;
  font-size: 14px;
}
.mt-12 {
  margin-top: 12px;
}
.main-row {
  margin-top: 0;
}

/* 顶部筛选 */
.filter-panel :deep(.el-card__body) {
  padding: 14px 16px;
}
.filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
}

/* 权重滑块 */
.weight-tip {
  color: #606266;
  font-size: 12px;
  margin-bottom: 6px;
}
.slider-row {
  padding: 6px 0;
}
.slider-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: #303133;
  margin-bottom: 2px;
}
.slider-val {
  color: #409eff;
  font-weight: 600;
}

/* 4列指标卡 */
.metric-card {
  height: 140px;
}
.m-title {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}
.m-block {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin: 4px 0;
}
.m-sub {
  font-size: 12px;
  color: #909399;
  width: 38px;
}
.m-big {
  font-size: 22px;
  font-weight: 700;
  line-height: 1;
}
.m-big.before {
  color: #f56c6c;
}
.m-big.after {
  color: #67c23a;
}
.m-improve {
  margin-top: 6px;
}

/* 图例 */
.legend {
  display: flex;
  gap: 12px;
  font-weight: 400;
  color: #606266;
  font-size: 12px;
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.legend-item .dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 2px;
}
.dot.wrf { background: #409eff; }
.dot.fengwu { background: #67c23a; }
.dot.tianzi { background: #e6a23c; }
.dot.fenglei { background: #f56c6c; }
.dot.fusion { background: #909399; }
.legend-item .heat {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 2px;
}
.heat.low { background: rgba(103, 194, 58, 0.8); }
.heat.mid { background: rgba(230, 162, 60, 0.85); }
.heat.high { background: rgba(245, 108, 108, 0.9); }

/* 条形图 */
.bar-chart {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 220px;
  padding: 12px 6px 26px;
  background: linear-gradient(180deg, #fafbfc 0%, #f4f6f9 100%);
  border-radius: 6px;
  position: relative;
  overflow-x: auto;
}
.bar-hour {
  flex: 1 0 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  min-width: 28px;
}
.bar-cols {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 2px;
}
.bar-col {
  width: 3px;
  height: 100%;
  display: flex;
  align-items: flex-end;
}
.bar {
  width: 100%;
  border-radius: 2px 2px 0 0;
  min-height: 2px;
  transition: height 0.3s;
}
.bar-wrf { background: #409eff; }
.bar-fengwu { background: #67c23a; }
.bar-tianzi { background: #e6a23c; }
.bar-fenglei { background: #f56c6c; }
.bar-fusion { background: #909399; }
.bar-label {
  font-size: 10px;
  color: #909399;
  margin-top: 4px;
}
.y-axis {
  display: flex;
  justify-content: space-between;
  color: #c0c4cc;
  font-size: 11px;
  padding: 0 8px;
  margin-top: -8px;
}

/* 热力图 */
.heat-grid {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: 4px;
  padding: 8px;
  background: #f4f6f9;
  border-radius: 6px;
}
.heat-cell {
  aspect-ratio: 1 / 1;
  border-radius: 3px;
  transition: transform 0.15s;
  cursor: pointer;
}
.heat-cell:hover {
  transform: scale(1.12);
  box-shadow: 0 0 0 2px #409eff33;
}

/* 日志 */
.log-panel {
  margin-top: 12px;
}
</style>
