<script setup lang="ts">
import { ref, shallowRef, onMounted, onUnmounted, reactive } from 'vue'
import * as echarts from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import {
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsOption } from 'echarts'

echarts.use([
  GraphChart,
  TooltipComponent,
  LegendComponent,
  CanvasRenderer,
])

type ServiceStatus = 'healthy' | 'warning' | 'error' | 'offline'

export interface ServiceNode {
  id: string
  name: string
  category: string
  status: ServiceStatus
  cpu?: number
  memory?: number
  requests?: number
  errorRate?: number
}

export interface ServiceEdge {
  source: string
  target: string
  qps?: number
  label?: string
}

const props = withDefaults(defineProps<{
  height?: string
  autoRefreshInterval?: number
}>(), {
  height: '500px',
  autoRefreshInterval: 15000,
})

const emit = defineEmits<{
  (e: 'node-click', node: ServiceNode): void
}>()

const chartRef = ref<HTMLDivElement>()
const chartInstance = shallowRef<echarts.ECharts>()
const refreshTimer = ref<ReturnType<typeof setInterval>>()
const selectedNode = ref<ServiceNode | null>(null)

const statusColorMap: Record<ServiceStatus, string> = {
  healthy: '#67c23a',
  warning: '#e6a23c',
  error: '#f56c6c',
  offline: '#909399',
}

const statusLabelMap: Record<ServiceStatus, string> = {
  healthy: '健康',
  warning: '警告',
  error: '故障',
  offline: '离线',
}

const categoryMap: Record<string, string> = {
  gateway: 'API Gateway',
  service: '业务服务',
  database: '数据库',
  cache: '缓存',
  mq: '消息队列',
}

const categorySymbolMap: Record<string, string> = {
  gateway: 'roundRect',
  service: 'rect',
  database: 'diamond',
  cache: 'circle',
  mq: 'triangle',
}

const categoryColorMap: Record<string, string> = {
  gateway: '#409eff',
  service: '#e94560',
  database: '#f39c12',
  cache: '#e74c3c',
  mq: '#9b59b6',
}

const serviceNodes = reactive<ServiceNode[]>([
  { id: 'gateway', name: 'API Gateway', category: 'gateway', status: 'healthy', cpu: 32, memory: 1.2, requests: 4500, errorRate: 0.1 },
  { id: 'auth', name: '认证服务', category: 'service', status: 'healthy', cpu: 18, memory: 0.8, requests: 1200, errorRate: 0.05 },
  { id: 'user', name: '用户服务', category: 'service', status: 'healthy', cpu: 25, memory: 1.0, requests: 800, errorRate: 0.02 },
  { id: 'mission', name: '任务管理', category: 'service', status: 'warning', cpu: 78, memory: 2.1, requests: 600, errorRate: 1.2 },
  { id: 'weather', name: '气象服务', category: 'service', status: 'healthy', cpu: 45, memory: 1.5, requests: 950, errorRate: 0.08 },
  { id: 'algorithm', name: '算法引擎', category: 'service', status: 'healthy', cpu: 62, memory: 3.8, requests: 300, errorRate: 0.15 },
  { id: 'data-assim', name: '数据同化', category: 'service', status: 'healthy', cpu: 55, memory: 2.8, requests: 200, errorRate: 0.03 },
  { id: 'report', name: '报告服务', category: 'service', status: 'offline', cpu: 0, memory: 0, requests: 0, errorRate: 0 },
  { id: 'mysql', name: 'MySQL', category: 'database', status: 'healthy', cpu: 38, memory: 4.2, requests: 3200, errorRate: 0.01 },
  { id: 'redis', name: 'Redis', category: 'cache', status: 'healthy', cpu: 12, memory: 1.8, requests: 8500, errorRate: 0 },
  { id: 'kafka', name: 'Kafka', category: 'mq', status: 'healthy', cpu: 28, memory: 2.5, requests: 4200, errorRate: 0.02 },
])

const serviceEdges: ServiceEdge[] = [
  { source: 'gateway', target: 'auth', qps: 1200, label: '认证' },
  { source: 'gateway', target: 'user', qps: 800, label: '用户' },
  { source: 'gateway', target: 'mission', qps: 600, label: '任务' },
  { source: 'gateway', target: 'weather', qps: 950, label: '气象' },
  { source: 'gateway', target: 'algorithm', qps: 300, label: '算法' },
  { source: 'gateway', target: 'data-assim', qps: 200, label: '同化' },
  { source: 'gateway', target: 'report', qps: 50, label: '报告' },
  { source: 'auth', target: 'mysql', qps: 800, label: '读写' },
  { source: 'auth', target: 'redis', qps: 1200, label: '缓存' },
  { source: 'user', target: 'mysql', qps: 600, label: '读写' },
  { source: 'user', target: 'redis', qps: 400, label: '缓存' },
  { source: 'mission', target: 'mysql', qps: 500, label: '读写' },
  { source: 'mission', target: 'kafka', qps: 300, label: '事件' },
  { source: 'weather', target: 'redis', qps: 950, label: '缓存' },
  { source: 'weather', target: 'kafka', qps: 200, label: '推送' },
  { source: 'algorithm', target: 'redis', qps: 300, label: '缓存' },
  { source: 'algorithm', target: 'kafka', qps: 150, label: '事件' },
  { source: 'data-assim', target: 'mysql', qps: 200, label: '读写' },
  { source: 'data-assim', target: 'kafka', qps: 100, label: '事件' },
  { source: 'report', target: 'mysql', qps: 50, label: '读取' },
]

function simulateStatusChange() {
  for (const node of serviceNodes) {
    if (node.id === 'report') continue // 保持离线
    const rand = Math.random()
    if (rand < 0.05) {
      node.status = 'warning'
      node.cpu = Math.min(99, (node.cpu ?? 50) + Math.random() * 20)
    } else if (rand < 0.01) {
      node.status = 'error'
    } else {
      node.status = 'healthy'
      node.cpu = Math.max(5, (node.cpu ?? 50) + (Math.random() - 0.5) * 10)
      node.memory = Math.max(0.5, (node.memory ?? 2) + (Math.random() - 0.5) * 0.3)
      node.requests = Math.max(0, Math.round((node.requests ?? 0) + (Math.random() - 0.5) * 100))
      node.errorRate = Math.max(0, +((node.errorRate ?? 0) + (Math.random() - 0.5) * 0.1).toFixed(2))
    }
  }
}

function initChart() {
  if (!chartRef.value) return
  chartInstance.value = echarts.init(chartRef.value)
  updateChart()

  chartInstance.value.on('click', (params: any) => {
    if (params.dataType === 'node') {
      const node = serviceNodes.find((n) => n.id === params.data.id)
      if (node) {
        selectedNode.value = node
        emit('node-click', node)
      }
    }
  })
}

function updateChart() {
  if (!chartInstance.value) return

  const categories = Object.entries(categoryMap).map(([key, name]) => ({
    name,
    itemStyle: { color: categoryColorMap[key] },
    symbol: categorySymbolMap[key] || 'circle',
  }))

  const nodes = serviceNodes.map((node) => ({
    id: node.id,
    name: node.name,
    category: Object.keys(categoryMap).indexOf(node.category),
    symbolSize: node.category === 'gateway' ? 60 : node.category === 'service' ? 50 : 45,
    itemStyle: {
      color: statusColorMap[node.status],
      borderColor: statusColorMap[node.status],
      borderWidth: 2,
      shadowBlur: 10,
      shadowColor: statusColorMap[node.status] + '60',
    },
    label: {
      show: true,
      color: '#e0e0e0',
      fontSize: 12,
      fontWeight: 500,
    },
    value: node,
  }))

  const edges = serviceEdges.map((edge) => ({
    source: edge.source,
    target: edge.target,
    lineStyle: {
      color: '#2a2a40',
      width: 1.5,
      curveness: 0.15,
    },
    label: {
      show: true,
      formatter: () => `${edge.qps || ''} req/s`,
      color: '#a0a0b0',
      fontSize: 10,
      backgroundColor: 'rgba(26, 26, 46, 0.8)',
      padding: [2, 4],
      borderRadius: 2,
    },
  }))

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: '#1f1f35',
      borderColor: '#2a2a40',
      textStyle: { color: '#e0e0e0', fontSize: 12 },
      formatter: (params: any) => {
        if (params.dataType === 'node') {
          const node = params.data.value as ServiceNode
          return `<div style="font-weight:600;margin-bottom:6px">${node.name}</div>
            <div>状态: <span style="color:${statusColorMap[node.status]}">${statusLabelMap[node.status]}</span></div>
            <div>CPU: ${node.cpu?.toFixed(1) || '-'}%</div>
            <div>内存: ${node.memory?.toFixed(1) || '-'} GB</div>
            <div>请求数: ${node.requests || '-'}</div>
            <div>错误率: ${node.errorRate || '-'}%</div>`
        }
        if (params.dataType === 'edge') {
          return `${params.data.source} → ${params.data.target}<br/>QPS: ${params.data.label?.formatter?.() || '-'}`
        }
        return ''
      },
    },
    legend: {
      data: categories.map((c) => c.name),
      textStyle: { color: '#a0a0b0', fontSize: 12 },
      bottom: 10,
      icon: 'circle',
    },
    series: [{
        type: 'graph',
        layout: 'force',
        data: nodes,
        links: edges,
        categories,
        roam: true,
        draggable: true,
        force: {
          repulsion: 400,
          edgeLength: [120, 250],
          gravity: 0.05,
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: { width: 3 },
          itemStyle: { borderWidth: 3 },
        },
        lineStyle: {
          opacity: 0.8,
        },
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: [0, 8],
      }] as any,
  }

  chartInstance.value.setOption(option as any, true)
}

function handleResize() {
  chartInstance.value?.resize()
}

function startAutoRefresh() {
  stopAutoRefresh()
  if (props.autoRefreshInterval > 0) {
    refreshTimer.value = setInterval(() => {
      simulateStatusChange()
      updateChart()
    }, props.autoRefreshInterval)
  }
}

function stopAutoRefresh() {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = undefined
  }
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
  window.removeEventListener('resize', handleResize)
  chartInstance.value?.dispose()
})
</script>

<template>
  <div class="service-topology">
    <!-- Legend -->
    <div class="topo-legend">
      <span class="legend-title">节点状态:</span>
      <div
        v-for="(color, status) in statusColorMap"
        :key="status"
        class="legend-item"
      >
        <span
          class="legend-dot"
          :style="{ backgroundColor: color }"
        ></span>
        <span class="legend-label">{{ statusLabelMap[status as ServiceStatus] }}</span>
      </div>
      <span class="legend-separator">|</span>
      <span class="legend-hint">点击节点查看详情 / 拖拽平移 / 滚轮缩放</span>
    </div>

    <!-- Chart -->
    <div ref="chartRef" :style="{ width: '100%', height }"></div>

    <!-- Node Detail Drawer -->
    <el-drawer
      v-model="selectedNode"
      :title="selectedNode?.name || '节点详情'"
      direction="rtl"
      size="360px"
      :modal="false"
    >
      <template v-if="selectedNode">
        <div class="detail-content">
          <div class="detail-section">
            <h4 class="detail-section-title">基本信息</h4>
            <div class="detail-row">
              <span class="detail-label">服务名称</span>
              <span class="detail-value">{{ selectedNode.name }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">分类</span>
              <span class="detail-value">{{ categoryMap[selectedNode.category] }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">状态</span>
              <el-tag
                :type="selectedNode.status === 'healthy' ? 'success' : selectedNode.status === 'warning' ? 'warning' : selectedNode.status === 'error' ? 'danger' : 'info'"
                size="small"
              >
                {{ statusLabelMap[selectedNode.status] }}
              </el-tag>
            </div>
          </div>

          <div class="detail-section">
            <h4 class="detail-section-title">性能指标</h4>
            <div class="detail-row">
              <span class="detail-label">CPU 使用率</span>
              <div class="detail-bar-wrapper">
                <el-progress
                  :percentage="selectedNode.cpu || 0"
                  :color="selectedNode.cpu && selectedNode.cpu > 80 ? '#f56c6c' : selectedNode.cpu && selectedNode.cpu > 60 ? '#e6a23c' : '#67c23a'"
                  :stroke-width="8"
                  :show-text="true"
                  :text-inside="true"
                />
              </div>
            </div>
            <div class="detail-row">
              <span class="detail-label">内存使用</span>
              <span class="detail-value">{{ selectedNode.memory?.toFixed(1) || '-' }} GB</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">请求数</span>
              <span class="detail-value">{{ selectedNode.requests?.toLocaleString() || '-' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">错误率</span>
              <span
                class="detail-value"
                :style="{ color: selectedNode.errorRate && selectedNode.errorRate > 1 ? '#f56c6c' : '#e0e0e0' }"
              >
                {{ selectedNode.errorRate || '-' }}%
              </span>
            </div>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.service-topology {
  background: var(--color-bg-secondary, #1a1a2e);
  border-radius: 8px;
  border: 1px solid var(--color-border, #2a2a40);
  overflow: hidden;
}

.topo-legend {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-border, #2a2a40);
  flex-wrap: wrap;
}

.legend-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary, #e0e0e0);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-label {
  font-size: 12px;
  color: var(--color-text-secondary, #a0a0b0);
}

.legend-separator {
  color: var(--color-border, #2a2a40);
}

.legend-hint {
  font-size: 11px;
  color: var(--color-text-secondary, #909399);
  margin-left: auto;
}

.detail-content {
  padding: 0 4px;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section-title {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary, #e0e0e0);
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border, #2a2a40);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.detail-label {
  font-size: 13px;
  color: var(--color-text-secondary, #a0a0b0);
}

.detail-value {
  font-size: 13px;
  color: var(--color-text-primary, #e0e0e0);
  font-weight: 500;
}

.detail-bar-wrapper {
  flex: 1;
  margin-left: 16px;
  max-width: 180px;
}
</style>
