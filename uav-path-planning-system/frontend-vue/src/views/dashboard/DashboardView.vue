<template>
  <div class="dashboard">
    <div class="page-title">系统概览</div>

    <!-- 顶部统计卡 -->
    <a-row :gutter="[16, 16]" class="stat-row">
      <a-col :xs="24" :sm="12" :md="6">
        <a-card class="stat-card">
          <a-statistic
            title="在线无人机"
            :value="droneStore.list.filter((d) => d.status !== '维护中').length"
            suffix="架"
          >
            <template #prefix>
              <RocketOutlined style="color: #1677ff" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :md="6">
        <a-card class="stat-card">
          <a-statistic
            title="待执行任务"
            :value="pendingTaskCount"
            suffix="个"
          >
            <template #prefix>
              <OrderedListOutlined style="color: #faad14" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :md="6">
        <a-card class="stat-card">
          <a-statistic title="风速" :value="windSpeed" suffix="m/s">
            <template #prefix>
              <CloudOutlined style="color: #13c2c2" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :xs="24" :sm="12" :md="6">
        <a-card class="stat-card">
          <a-statistic
            title="系统健康度"
            :value="systemStore.status.healthScore"
            suffix="%"
          >
            <template #prefix>
              <HeartOutlined style="color: #52c41a" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 快捷入口 -->
    <a-card title="快捷操作" class="quick-card">
      <a-row :gutter="[16, 16]">
        <a-col :xs="24" :sm="12" :md="6">
          <a-button block size="large" type="primary" @click="$router.push('/path-planning')">
            <template #icon><OrderedListOutlined /></template>
            路径规划
          </a-button>
        </a-col>
        <a-col :xs="24" :sm="12" :md="6">
          <a-button block size="large" @click="$router.push('/weather')">
            <template #icon><CloudOutlined /></template>
            气象数据
          </a-button>
        </a-col>
        <a-col :xs="24" :sm="12" :md="6">
          <a-button block size="large" @click="$router.push('/tasks')">
            <template #icon><CheckCircleOutlined /></template>
            任务管理
          </a-button>
        </a-col>
        <a-col :xs="24" :sm="12" :md="6">
          <a-button block size="large" @click="$router.push('/drones')">
            <template #icon><RocketOutlined /></template>
            无人机管理
          </a-button>
        </a-col>
      </a-row>
    </a-card>

    <!-- 内容面板 -->
    <a-row :gutter="[16, 16]" class="content-row">
      <a-col :xs="24" :lg="16">
        <a-card title="近期待办任务">
          <a-table
            :columns="taskColumns"
            :data-source="taskStore.list.slice(0, 5)"
            :pagination="false"
            size="small"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'status'">
                <a-tag :color="getStatusColor(record.status)">{{ record.status }}</a-tag>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-col>
      <a-col :xs="24" :lg="8">
        <a-card title="系统公告">
          <a-timeline>
            <a-timeline-item color="blue">
              <div class="notice-title">系统版本更新</div>
              <div class="notice-time">刚刚</div>
              <div class="notice-content">路径规划算法已升级至 v2.3</div>
            </a-timeline-item>
            <a-timeline-item color="green">
              <div class="notice-title">新增数据源接入</div>
              <div class="notice-time">2小时前</div>
              <div class="notice-content">GOES-16 卫星数据已接入</div>
            </a-timeline-item>
            <a-timeline-item>
              <div class="notice-title">定期维护通知</div>
              <div class="notice-time">昨天</div>
              <div class="notice-content">系统将于每周日凌晨 2:00 进行定期维护</div>
            </a-timeline-item>
          </a-timeline>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import {
  RocketOutlined,
  OrderedListOutlined,
  CloudOutlined,
  HeartOutlined,
  CheckCircleOutlined
} from '@ant-design/icons-vue'
import { useDroneStore } from '../../stores/drones'
import { useTaskStore } from '../../stores/tasks'
import { useWeatherStore } from '../../stores/weather'
import { useSystemStore } from '../../stores/system'

const droneStore = useDroneStore()
const taskStore = useTaskStore()
const weatherStore = useWeatherStore()
const systemStore = useSystemStore()

const taskColumns = [
  { title: '任务名称', dataIndex: 'name', key: 'name' },
  { title: '类型', dataIndex: 'type', key: 'type' },
  { title: '状态', key: 'status' },
  { title: '优先级', dataIndex: 'priority', key: 'priority' }
]

const pendingTaskCount = computed(
  () => taskStore.list.filter((t) => t.status === '待分配' || t.status === '已分配').length
)

const windSpeed = computed(() => {
  return weatherStore.current?.windSpeed || 5.2
})

function getStatusColor(status) {
  const map = {
    待分配: 'blue',
    已分配: 'orange',
    执行中: 'purple',
    已完成: 'green',
    已取消: 'red'
  }
  return map[status] || 'default'
}

onMounted(async () => {
  try {
    await Promise.all([
      droneStore.fetchAll(),
      taskStore.fetchAll(),
      weatherStore.fetchCurrent(),
      systemStore.refreshStatus()
    ])
  } catch (e) {
    // 使用演示数据
  }
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
  color: rgba(0, 0, 0, 0.88);
}

.stat-row {
  margin-bottom: 16px;
}

.stat-card {
  height: 100%;
}

.quick-card {
  margin-bottom: 16px;
}

.content-row {
  margin-bottom: 16px;
}

.notice-title {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.88);
}

.notice-time {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin: 2px 0 4px;
}

.notice-content {
  font-size: 13px;
  color: rgba(0, 0, 0, 0.65);
}
</style>
