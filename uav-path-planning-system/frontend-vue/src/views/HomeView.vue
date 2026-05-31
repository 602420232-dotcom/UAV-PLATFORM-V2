<template>
  <div class="home-container">
    <!-- 顶部统计卡片 -->
    <a-row :gutter="[24, 24]" class="stats-row">
      <!-- 系统状态 -->
      <a-col :xs="24" :sm="12" :lg="8">
        <a-card class="stats-card" :bordered="false">
          <template #title>
            <div class="card-title">
              <DashboardOutlined class="title-icon" />
              <span>系统状态</span>
            </div>
          </template>
          <div class="stats-content">
            <div class="stat-item">
              <span class="stat-label">在线无人机</span>
              <span class="stat-value primary">8 <small>架</small></span>
            </div>
            <a-divider />
            <div class="stat-item">
              <span class="stat-label">待执行任务</span>
              <span class="stat-value success">12 <small>个</small></span>
            </div>
            <a-divider />
            <div class="stat-item">
              <span class="stat-label">系统运行</span>
              <span class="stat-value">
                <a-badge status="processing" text="正常" />
              </span>
            </div>
          </div>
        </a-card>
      </a-col>
      
      <!-- 气象预警 -->
      <a-col :xs="24" :sm="12" :lg="8">
        <a-card class="stats-card" :bordered="false">
          <template #title>
            <div class="card-title">
              <CloudOutlined class="title-icon" />
              <span>气象预警</span>
            </div>
          </template>
          <div class="stats-content">
            <div class="stat-item">
              <span class="stat-label">当前风速</span>
              <span class="stat-value">5.2 <small>m/s</small></span>
            </div>
            <a-divider />
            <div class="stat-item">
              <span class="stat-label">风险等级</span>
              <span class="stat-value success">低</span>
            </div>
            <a-divider />
            <div class="stat-item">
              <span class="stat-label">更新时间</span>
              <span class="stat-value muted">10:30</span>
            </div>
          </div>
        </a-card>
      </a-col>
      
      <!-- 任务统计 -->
      <a-col :xs="24" :sm="12" :lg="8">
        <a-card class="stats-card" :bordered="false">
          <template #title>
            <div class="card-title">
              <BarChartOutlined class="title-icon" />
              <span>任务统计</span>
            </div>
          </template>
          <div class="stats-content">
            <div class="stat-item">
              <span class="stat-label">今日完成</span>
              <span class="stat-value primary">24 <small>个</small></span>
            </div>
            <a-divider />
            <div class="stat-item">
              <span class="stat-label">本周完成</span>
              <span class="stat-value">156 <small>个</small></span>
            </div>
            <a-divider />
            <div class="stat-item">
              <span class="stat-label">成功率</span>
              <span class="stat-value success">98.5 <small>%</small></span>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>

    <!-- 快速操作 -->
    <a-card class="action-card" :bordered="false">
      <template #title>
        <div class="card-title">
          <ThunderboltOutlined class="title-icon" />
          <span>快速操作</span>
        </div>
      </template>
      <a-row :gutter="[16, 16]">
        <a-col :xs="12" :sm="6">
          <div class="action-item" @click="$router.push('/path-planning')">
            <div class="action-icon primary">
              <OrderedListOutlined />
            </div>
            <span class="action-text">路径规划</span>
          </div>
        </a-col>
        <a-col :xs="12" :sm="6">
          <div class="action-item" @click="$router.push('/weather')">
            <div class="action-icon info">
              <CloudOutlined />
            </div>
            <span class="action-text">气象数据</span>
          </div>
        </a-col>
        <a-col :xs="12" :sm="6">
          <div class="action-item" @click="$router.push('/tasks')">
            <div class="action-icon success">
              <CheckCircleOutlined />
            </div>
            <span class="action-text">任务管理</span>
          </div>
        </a-col>
        <a-col :xs="12" :sm="6">
          <div class="action-item" @click="$router.push('/drones')">
            <div class="action-icon warning">
              <RocketOutlined />
            </div>
            <span class="action-text">无人机管理</span>
          </div>
        </a-col>
      </a-row>
    </a-card>

    <!-- 系统介绍 -->
    <a-card class="intro-card" :bordered="false">
      <template #title>
        <div class="card-title">
          <InfoCircleOutlined class="title-icon" />
          <span>系统介绍</span>
        </div>
      </template>
      <div class="intro-content">
        <p class="intro-desc">无人机路径规划系统是一个基于WRF气象预报和智能算法的综合解决方案，主要功能包括：</p>
        <a-row :gutter="[24, 16]" class="feature-list">
          <a-col :xs="24" :sm="12" :md="8">
            <div class="feature-item">
              <CheckOutlined class="feature-icon" />
              <span>WRF低空气象预报与贝叶斯同化</span>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :md="8">
            <div class="feature-item">
              <CheckOutlined class="feature-icon" />
              <span>LSTM+XGBoost气象预测与订正</span>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :md="8">
            <div class="feature-item">
              <CheckOutlined class="feature-icon" />
              <span>VRPTW+A*+DWA三层路径规划</span>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :md="8">
            <div class="feature-item">
              <CheckOutlined class="feature-icon" />
              <span>多无人机协同任务调度</span>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :md="8">
            <div class="feature-item">
              <CheckOutlined class="feature-icon" />
              <span>实时气象风险评估与预警</span>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :md="8">
            <div class="feature-item">
              <CheckOutlined class="feature-icon" />
              <span>完整的Web管理界面</span>
            </div>
          </a-col>
        </a-row>
        <p class="intro-footer">系统支持城市物流配送、电力巡检、应急救援等多种应用场景，为无人机安全高效作业提供技术保障。</p>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import {
  OrderedListOutlined,
  CloudOutlined,
  CheckCircleOutlined,
  RocketOutlined,
  DashboardOutlined,
  BarChartOutlined,
  ThunderboltOutlined,
  InfoCircleOutlined,
  CheckOutlined
} from '@ant-design/icons-vue'
</script>

<style scoped>
.home-container {
  padding: 8px;
}

/* 统计卡片行 */
.stats-row {
  margin-bottom: 24px;
}

.stats-card {
  height: 100%;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
}

.stats-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
}

.title-icon {
  font-size: 16px;
  color: #1677ff;
}

.stats-content {
  padding: 8px 0;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.stat-label {
  color: #666;
  font-size: 14px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.stat-value small {
  font-size: 12px;
  font-weight: normal;
  color: #999;
  margin-left: 2px;
}

.stat-value.primary {
  color: #1677ff;
}

.stat-value.success {
  color: #52c41a;
}

.stat-value.warning {
  color: #faad14;
}

.stat-value.muted {
  color: #999;
  font-size: 16px;
  font-weight: normal;
}

:deep(.ant-divider) {
  margin: 4px 0;
}

/* 快速操作卡片 */
.action-card {
  margin-bottom: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 20px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #fafafa;
}

.action-item:hover {
  background: #f0f5ff;
  transform: translateY(-2px);
}

.action-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-size: 24px;
  color: #fff;
}

.action-icon.primary {
  background: linear-gradient(135deg, #1677ff, #0958d9);
}

.action-icon.info {
  background: linear-gradient(135deg, #13c2c2, #08979c);
}

.action-icon.success {
  background: linear-gradient(135deg, #52c41a, #389e0d);
}

.action-icon.warning {
  background: linear-gradient(135deg, #faad14, #d48806);
}

.action-text {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

/* 系统介绍卡片 */
.intro-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.intro-content {
  padding: 8px 0;
}

.intro-desc {
  font-size: 14px;
  color: #666;
  line-height: 1.8;
  margin-bottom: 20px;
}

.feature-list {
  margin-bottom: 20px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  font-size: 14px;
  color: #333;
}

.feature-icon {
  color: #52c41a;
  font-size: 14px;
}

.intro-footer {
  font-size: 14px;
  color: #666;
  line-height: 1.8;
  margin: 0;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

/* 响应式 */
@media (max-width: 768px) {
  .home-container {
    padding: 0;
  }
  
  .stats-card {
    margin-bottom: 0;
  }
  
  .action-item {
    padding: 16px 12px;
  }
  
  .action-icon {
    width: 40px;
    height: 40px;
    font-size: 20px;
  }
  
  .action-text {
    font-size: 13px;
  }
  
  .stat-value {
    font-size: 18px;
  }
}

@media (max-width: 576px) {
  .stat-item {
    padding: 6px 0;
  }
  
  .stat-label {
    font-size: 13px;
  }
  
  .stat-value {
    font-size: 16px;
  }
}
</style>
