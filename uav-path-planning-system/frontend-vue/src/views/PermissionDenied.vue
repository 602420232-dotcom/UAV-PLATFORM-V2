<template>
  <div class="denied-page">
    <div class="denied-card">
      <div class="denied-icon">
        <el-icon :size="120"><Lock /></el-icon>
      </div>

      <h1 class="denied-title">抱歉，您没有访问权限</h1>
      <p class="denied-subtitle">
        当前角色为
        <el-tag type="primary" size="default" round>{{ authStore.roleLabel }}</el-tag>
        ，无法访问此模块或页面。
      </p>

      <div class="denied-actions">
        <el-button type="primary" size="large" @click="goHome">
          <el-icon><House /></el-icon>
          返回首页
        </el-button>
        <el-button size="large" @click="logout">
          <el-icon><SwitchButton /></el-icon>
          退出登录
        </el-button>
      </div>

      <div class="accessible-block">
        <h3 class="accessible-title">您当前可访问的模块</h3>
        <div class="accessible-list">
          <div
            v-for="item in accessibleItems"
            :key="item.key"
            class="accessible-chip"
            @click="router.push('/' + item.key)"
          >
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </div>
          <div v-if="accessibleItems.length === 0" class="accessible-empty">
            暂无可用模块
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Lock, House, SwitchButton, HomeFilled, PartlyCloudy, Goods,
  Monitor, List, Position, Connection, DataAnalysis, Coin, Box,
  Setting, Tools, Document
} from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useAppStore } from '../stores/app'

const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()

const MODULE_META = {
  dashboard: { title: '项目简介 / 首页', icon: 'HomeFilled' },
  weather: { title: '气象数据', icon: 'PartlyCloudy' },
  orders: { title: '下单 / 选择运输地点', icon: 'Goods' },
  cockpit: { title: '智能驾驶舱', icon: 'Monitor' },
  tasks: { title: '运输任务管理', icon: 'List' },
  'path-planning': { title: '路径规划', icon: 'Position' },
  assimilation: { title: '数据同化', icon: 'Connection' },
  monitoring: { title: '系统监控面板', icon: 'DataAnalysis' },
  database: { title: '数据库管理', icon: 'Coin' },
  docker: { title: 'Docker / 服务器状态', icon: 'Box' },
  'api-config': { title: '气象模型 API 配置', icon: 'Setting' },
  settings: { title: '设置', icon: 'Tools' },
  docs: { title: '使用文档', icon: 'Document' }
}

const ICON_MAP = {
  HomeFilled, PartlyCloudy, Goods, Monitor, List,
  Position, Connection, DataAnalysis, Coin, Box,
  Setting, Tools, Document
}

const accessibleItems = computed(() => {
  return authStore.accessibleRoutes
    .filter((k) => MODULE_META[k])
    .map((k) => ({
      key: k,
      title: MODULE_META[k].title,
      icon: ICON_MAP[MODULE_META[k].icon] || Document
    }))
})

function goHome() {
  const defaultKey = authStore.role ? appStore.getDefaultRoute(authStore.role) : 'dashboard'
  router.push('/' + defaultKey)
}

function logout() {
  authStore.logout()
  router.push('/login')
  ElMessage.success('已退出登录')
}
</script>

<style scoped>
.denied-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #eef2ff 0%, #f5f7fa 60%, #e0f2fe 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.denied-card {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(64, 158, 255, 0.12);
  padding: 48px 48px 36px;
  max-width: 640px;
  width: 100%;
  text-align: center;
}

.denied-icon {
  color: #409eff;
  margin-bottom: 12px;
}

.denied-title {
  font-size: 24px;
  font-weight: 700;
  color: #1f2937;
  margin: 4px 0 12px;
}

.denied-subtitle {
  color: #6b7280;
  font-size: 14px;
  margin: 0 0 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.denied-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 32px;
}

.accessible-block {
  text-align: left;
  border-top: 1px dashed #e5e7eb;
  padding-top: 20px;
}

.accessible-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 12px;
}

.accessible-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.accessible-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #ecf5ff;
  color: #409eff;
  border: 1px solid #d9ecff;
  border-radius: 999px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.accessible-chip:hover {
  background: #409eff;
  color: #ffffff;
  border-color: #409eff;
}

.accessible-empty {
  color: #9ca3af;
  font-size: 13px;
}
</style>
