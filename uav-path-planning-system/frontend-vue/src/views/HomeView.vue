<template>
  <a-card title="系统概览" class="home-card">
    <a-row :gutter="[16, 16]">
      <!-- 系统状态 -->
      <a-col :span="8">
        <a-card size="small" title="系统状态" class="status-card">
          <a-statistic title="在线无人机" :value="8" suffix="架" />
          <a-statistic title="待执行任务" :value="12" suffix="个" />
          <a-statistic title="系统运行" :value="'正常'" />
        </a-card>
      </a-col>
      
      <!-- 气象预警 -->
      <a-col :span="8">
        <a-card size="small" title="气象预警" class="weather-card">
          <a-statistic title="当前风速" :value="5.2" suffix="m/s" />
          <a-statistic title="风险等级" :value="'低'" />
          <a-statistic title="更新时间" :value="'10:30'" />
        </a-card>
      </a-col>
      
      <!-- 任务统计 -->
      <a-col :span="8">
        <a-card size="small" title="任务统计" class="task-card">
          <a-statistic title="今日完成" :value="24" suffix="个" />
          <a-statistic title="本周完成" :value="156" suffix="个" />
          <a-statistic title="成功率" :value="98.5" suffix="%" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 快速操作 -->
    <div class="quick-actions" style="margin-top: 24px">
      <a-card title="快速操作">
        <a-row :gutter="[16, 16]">
          <a-col :span="6">
            <a-button type="primary" block @click="$router.push('/path-planning')">
              <template #icon>
                <OrderedListOutlined />
              </template>
              路径规划
            </a-button>
          </a-col>
          <a-col :span="6">
            <a-button block @click="$router.push('/weather')">
              <template #icon>
                <CloudOutlined />
              </template>
              气象数据
            </a-button>
          </a-col>
          <a-col :span="6">
            <a-button block @click="$router.push('/tasks')">
              <template #icon>
                <CheckCircleOutlined />
              </template>
              任务管理
            </a-button>
          </a-col>
          <a-col :span="6">
            <a-button block @click="$router.push('/drones')">
              <template #icon>
                <RocketOutlined />
              </template>
              无人机管理
            </a-button>
          </a-col>
        </a-row>
      </a-card>
    </div>

    <!-- 系统介绍 -->
    <div class="system-intro" style="margin-top: 24px">
      <a-card title="系统介绍">
        <p>无人机路径规划系统是一个基于WRF气象预报和智能算法的综合解决方案，主要功能包括：</p>
        <ul>
          <li>WRF低空气象预报与贝叶斯同化</li>
          <li>LSTM+XGBoost气象预测与订正</li>
          <li>VRPTW+A*+DWA三层路径规划</li>
          <li>多无人机协同任务调度</li>
          <li>实时气象风险评估与预警</li>
          <li>完整的Web管理界面</li>
        </ul>
        <p>系统支持城市物流配送、电力巡检、应急救援等多种应用场景，为无人机安全高效作业提供技术保障。</p>
      </a-card>
    </div>
  </a-card>
</template>

<script setup>
import {
  OrderedListOutlined,
  CloudOutlined,
  CheckCircleOutlined,
  RocketOutlined
} from '@ant-design/icons-vue'
</script>

<style scoped>
.home-card {
  margin-bottom: 24px;
}

.status-card,
.weather-card,
.task-card {
  height: 200px;
}

.quick-actions {
  margin-top: 24px;
}

.system-intro {
  margin-top: 24px;
}

ul {
  margin: 16px 0;
  padding-left: 20px;
}

li {
  margin: 8px 0;
}
</style>