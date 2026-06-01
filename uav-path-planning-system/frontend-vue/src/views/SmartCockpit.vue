<template>
  <div class="smart-cockpit">
    <!-- 顶部状态栏 -->
    <div class="status-bar">
      <div class="status-item" v-for="s in statusItems" :key="s.label">
        <span class="status-icon" :class="s.status">{{ s.icon }}</span>
        <span class="status-label">{{ s.label }}</span>
        <span class="status-value">{{ s.value }}</span>
      </div>
    </div>

    <!-- 主布局：4x2 态势感知面板 -->
    <div class="cockpit-grid">
      <!-- 气象态势 -->
      <div class="panel weather-panel">
        <div class="panel-header">🌤 气象态势</div>
        <div class="panel-body">
          <div ref="weatherChart" class="chart"></div>
          <div class="weather-metrics">
            <div v-for="(m, i) in weatherMetrics" :key="i" class="metric">
              <span class="metric-label">{{ m.label }}</span>
              <span class="metric-value" :class="m.level">{{ m.value }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 飞行态势 -->
      <div class="panel flight-panel">
        <div class="panel-header">🚁 飞行态势</div>
        <div class="panel-body">
          <div ref="flightChart" class="chart"></div>
          <div class="drone-list">
            <div v-for="(d, i) in drones" :key="i" class="drone-item">
              <span class="drone-id">{{ d.id }}</span>
              <span class="drone-status" :class="d.status">{{ d.status }}</span>
              <span class="drone-battery">{{ d.battery }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 任务态势 -->
      <div class="panel mission-panel">
        <div class="panel-header">📋 任务态势</div>
        <div class="panel-body">
          <div class="mission-progress">
            <div class="progress-ring">
              <svg viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="50" class="progress-bg"/>
                <circle cx="60" cy="60" r="50" class="progress-fill"
                        :style="{ strokeDashoffset: 314 - 314 * missionProgress / 100 }"/>
              </svg>
              <span class="progress-text">{{ missionProgress }}%</span>
            </div>
            <div class="mission-stats">
              <div>已完成: {{ completedTasks }}</div>
              <div>进行中: {{ activeTasks }}</div>
              <div>待执行: {{ pendingTasks }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 地理信息态势 -->
      <div class="panel geo-panel">
        <div class="panel-header">🗺 地理信息态势</div>
        <div class="panel-body">
          <div ref="mapContainer" class="map-container"></div>
        </div>
      </div>

      <!-- 风险预警 -->
      <div class="panel alert-panel">
        <div class="panel-header">⚠ 风险预警</div>
        <div class="panel-body">
          <div v-for="(a, i) in alerts" :key="i" class="alert-item" :class="a.level">
            <span class="alert-time">{{ a.time }}</span>
            <span class="alert-msg">{{ a.message }}</span>
          </div>
        </div>
      </div>

      <!-- 资源调度 -->
      <div class="panel resource-panel">
        <div class="panel-header">🔄 资源调度</div>
        <div class="panel-body">
          <div class="resource-list">
            <div v-for="(r, i) in resources" :key="i" class="resource-item">
              <span>{{ r.name }}</span>
              <div class="resource-bar">
                <div class="resource-fill" :style="{ width: r.utilization + '%' }"></div>
              </div>
              <span>{{ r.utilization }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 历史回放 -->
      <div class="panel history-panel">
        <div class="panel-header">⏪ 历史回放</div>
        <div class="panel-body">
          <div ref="historyChart" class="chart"></div>
          <div class="timeline-controls">
            <button @click="togglePlay">⏯</button>
            <input type="range" v-model="timelinePosition" min="0" max="100" />
            <span>{{ currentTime }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import { ARDigitalMap } from '@/utils/ar_digital_map';
import { ref, onMounted, onUnmounted, reactive, computed } from 'vue';

export default {
  name: 'SmartCockpit',
  setup() {
    const weatherChart = ref(null);
    const flightChart = ref(null);
    const historyChart = ref(null);
    const mapContainer = ref(null);

    const statusItems = reactive([
      { icon: '🟢', label: '系统状态', value: '正常运行', status: 'ok' },
      { icon: '🔗', label: '连接数', value: '12', status: 'ok' },
      { icon: '📡', label: '信号强度', value: '95%', status: 'ok' },
      { icon: '🔋', label: '集群电量', value: '78%', status: 'ok' },
      { icon: '🌡', label: '平均温度', value: '25°C', status: 'ok' },
      { icon: '💨', label: '平均风速', value: '4.2m/s', status: 'ok' }
    ]);

    const weatherMetrics = reactive([
      { label: '风速', value: '4.2m/s', level: 'low' },
      { label: '能见度', value: '15km', level: 'low' },
      { label: '温度', value: '25°C', level: 'normal' },
      { label: '湿度', value: '65%', level: 'normal' }
    ]);

    const drones = reactive([
      { id: 'UAV-001', status: '飞行中', battery: 85 },
      { id: 'UAV-002', status: '悬停', battery: 72 },
      { id: 'UAV-003', status: '返航', battery: 35 },
      { id: 'UAV-004', status: '待命', battery: 100 }
    ]);

    const missionProgress = ref(67);
    const completedTasks = ref(14);
    const activeTasks = ref(5);
    const pendingTasks = ref(3);

    const alerts = reactive([
      { time: '14:23:05', message: 'UAV-002 电池低于30%', level: 'warning' },
      { time: '14:20:12', message: '航路#5 风速突增至12m/s', level: 'warning' },
      { time: '14:15:00', message: 'UAV-001 任务完成', level: 'info' }
    ]);

    const resources = reactive([
      { name: 'WRF处理', utilization: 65 },
      { name: '同化计算', utilization: 45 },
      { name: '路径规划', utilization: 80 },
      { name: '网络带宽', utilization: 30 }
    ]);

    const timelinePosition = ref(0);
    const currentTime = ref('00:00:00');
    const isPlaying = ref(false);

    function initWeatherChart() {
      const chart = echarts.init(weatherChart.value);
      chart.setOption({
        series: [{
          type: 'gauge',
          startAngle: 90, endAngle: -270,
          axisLine: { lineStyle: { width: 20 } },
          detail: { formatter: '{value}°' },
          data: [{ value: 25, name: '温度' }]
        }]
      });
    }

    function initFlightChart() {
      const chart = echarts.init(flightChart.value);
      chart.setOption({
        xAxis: { type: 'category', data: ['UAV-1', 'UAV-2', 'UAV-3', 'UAV-4'] },
        yAxis: { type: 'value', max: 100 },
        series: [
          { type: 'bar', data: [85, 72, 35, 100], name: '电量', color: '#00d4ff' },
          { type: 'line', data: [60, 45, 80, 0], name: '高度(m)', color: '#ff6b6b', yAxisIndex: 0 }
        ]
      });
    }

    function initHistoryChart() {
      const chart = echarts.init(historyChart.value);
      chart.setOption({
        xAxis: { type: 'time' },
        yAxis: { type: 'value' },
        series: [{ type: 'line', data: [], smooth: true, areaStyle: {} }]
      });
    }

    let updateInterval = null
    onMounted(() => {
      initWeatherChart();
      initFlightChart();
      initHistoryChart();

      const arMap = new ARDigitalMap(mapContainer.value);
      updateInterval = setInterval(() => {
        arMap.trackDrone('UAV-001', () => ({
          lon: 116.39 + Math.random() * 0.02,
          lat: 39.90 + Math.random() * 0.02,
          alt: 100 + Math.random() * 20
        }));
      }, 2000);
    });

    onUnmounted(() => {
      if (updateInterval) clearInterval(updateInterval)
      if (weatherChart.value) weatherChart.value.dispose()
      if (flightChart.value) flightChart.value.dispose()
      if (historyChart.value) historyChart.value.dispose()
    })

    function togglePlay() {
      isPlaying.value = !isPlaying.value;
    }

    return {
      weatherChart, flightChart, historyChart, mapContainer,
      statusItems, weatherMetrics, drones, missionProgress,
      completedTasks, activeTasks, pendingTasks,
      alerts, resources, timelinePosition, currentTime, togglePlay
    };
  }
};
</script>

<style scoped>
.smart-cockpit { height: 100vh; background: #0a0e1a; color: #e0e0e0; padding: 16px; }
.status-bar { display: flex; gap: 20px; padding: 12px 20px; background: rgba(255,255,255,0.05); border-radius: 12px; margin-bottom: 16px; }
.status-item { display: flex; align-items: center; gap: 8px; }
.status-icon.ok { color: #00ff88; }
.cockpit-grid { display: grid; grid-template-columns: repeat(4, 1fr); grid-template-rows: repeat(2, 1fr); gap: 16px; height: calc(100vh - 100px); }
.panel { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 16px; overflow: hidden; }
.panel-header { font-size: 14px; font-weight: 600; margin-bottom: 12px; color: #00d4ff; }
.chart, .map-container { height: 120px; }
.weather-panel { grid-column: 1; grid-row: 1; }
.flight-panel { grid-column: 2; grid-row: 1; }
.mission-panel { grid-column: 3; grid-row: 1; }
.geo-panel { grid-column: 4; grid-row: 1; }
.alert-panel { grid-column: 1; grid-row: 2; }
.resource-panel { grid-column: 2; grid-row: 2; }
.history-panel { grid-column: 3 / 5; grid-row: 2; }
.alert-item { padding: 8px; border-left: 3px solid; margin-bottom: 4px; }
.alert-item.warning { border-color: #ff9800; }
.alert-item.info { border-color: #2196f3; }
.resource-bar { height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; flex: 1; }
.resource-fill { height: 100%; background: linear-gradient(90deg, #00d4ff, #00ff88); border-radius: 3px; }
.resource-item { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.drone-item { display: flex; justify-content: space-between; padding: 4px 0; }
.drone-status.flight { color: #00ff88; }
.drone-status.悬停 { color: #ffd700; }
.drone-status.返航 { color: #ff9800; }
.drone-status.待命 { color: #90a4ae; }
.mission-progress { display: flex; gap: 16px; }
.progress-ring { position: relative; width: 100px; height: 100px; }
.progress-bg { fill: none; stroke: rgba(255,255,255,0.1); stroke-width: 8; }
.progress-fill { fill: none; stroke: #00d4ff; stroke-width: 8; stroke-dasharray: 314; transition: stroke-dashoffset 0.5s; }
.progress-text { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 20px; font-weight: bold; }
.metric { display: flex; flex-direction: column; align-items: center; }
.metric-value.low { color: #00ff88; }
.metric-value.normal { color: #ffd700; }
</style>
