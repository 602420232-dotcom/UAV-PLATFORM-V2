<template>
  <a-layout style="min-height: 100vh">
    <!-- 移动端抽屉菜单 -->
    <a-drawer
      v-model:open="drawerVisible"
      placement="left"
      :closable="true"
      class="mobile-drawer"
      @close="drawerVisible = false"
    >
      <template #title>
        <div class="drawer-header">
          <span class="logo">无人机路径规划系统</span>
        </div>
      </template>
      <a-menu
        mode="inline"
        :selected-keys="[currentRoute]"
        @click="handleMenuClick"
        class="mobile-menu"
      >
        <a-menu-item key="/">
          <template #icon><HomeOutlined /></template>
          首页
        </a-menu-item>
        <a-menu-item key="/smart-cockpit">
          <template #icon><RadarChartOutlined /></template>
          智能驾驶舱
        </a-menu-item>
        <a-menu-item key="/path-planning">
          <template #icon><OrderedListOutlined /></template>
          路径规划
        </a-menu-item>
        <a-menu-item key="/weather">
          <template #icon><CloudOutlined /></template>
          气象数据
        </a-menu-item>
        <a-menu-item key="/tasks">
          <template #icon><CheckCircleOutlined /></template>
          任务管理
        </a-menu-item>
        <a-menu-item key="/drones">
          <template #icon><RocketOutlined /></template>
          无人机管理
        </a-menu-item>
        <a-menu-item key="/history">
          <template #icon><HistoryOutlined /></template>
          历史记录
        </a-menu-item>
        <a-menu-item key="/data-sources">
          <template #icon><DatabaseOutlined /></template>
          数据源管理
        </a-menu-item>
        <a-menu-item key="/monitoring">
          <template #icon><DashboardOutlined /></template>
          系统监控
        </a-menu-item>
        <a-menu-item key="/example">
          <template #icon><BookOutlined /></template>
          功能示范
        </a-menu-item>
      </a-menu>
    </a-drawer>

    <!-- 顶部导航栏 -->
    <a-layout-header class="header">
      <div class="logo">无人机路径规划系统</div>
      
      <!-- 移动端菜单按钮 -->
      <div class="mobile-menu-btn" @click="drawerVisible = true">
        <MenuOutlined />
      </div>
      
      <!-- 桌面端菜单 -->
      <a-menu
        mode="horizontal"
        :selected-keys="[currentRoute]"
        class="nav-menu desktop-menu"
      >
        <a-menu-item key="/">
          <template #icon>
            <HomeOutlined />
          </template>
          首页
        </a-menu-item>
        <a-menu-item key="/smart-cockpit">
          <template #icon>
            <RadarChartOutlined />
          </template>
          智能驾驶舱
        </a-menu-item>
        <a-menu-item key="/path-planning">
          <template #icon>
            <OrderedListOutlined />
          </template>
          路径规划
        </a-menu-item>
        <a-menu-item key="/weather">
          <template #icon>
            <CloudOutlined />
          </template>
          气象数据
        </a-menu-item>
        <a-menu-item key="/tasks">
          <template #icon>
            <CheckCircleOutlined />
          </template>
          任务管理
        </a-menu-item>
        <a-menu-item key="/drones">
          <template #icon>
            <RocketOutlined />
          </template>
          无人机管理
        </a-menu-item>
        <a-menu-item key="/history">
          <template #icon>
            <HistoryOutlined />
          </template>
          历史记录
        </a-menu-item>
        <a-menu-item key="/data-sources">
          <template #icon>
            <DatabaseOutlined />
          </template>
          数据源管理
        </a-menu-item>
        <a-menu-item key="/monitoring">
          <template #icon>
            <DashboardOutlined />
          </template>
          系统监控
        </a-menu-item>
        <a-menu-item key="/example">
          <template #icon>
            <BookOutlined />
          </template>
          功能示范
        </a-menu-item>
      </a-menu>
    </a-layout-header>

    <!-- 内容区域 -->
    <a-layout-content class="content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </a-layout-content>

    <!-- 底部 -->
    <a-layout-footer class="footer">
      无人机路径规划系统 ©2024
    </a-layout-footer>
  </a-layout>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  HomeOutlined,
  OrderedListOutlined,
  CloudOutlined,
  CheckCircleOutlined,
  RocketOutlined,
  HistoryOutlined,
  DatabaseOutlined,
  DashboardOutlined,
  BookOutlined,
  RadarChartOutlined,
  MenuOutlined
} from '@ant-design/icons-vue'

const route = useRoute()
const router = useRouter()
const currentRoute = ref('/')
const drawerVisible = ref(false)

// 监听路由变化
watch(() => route.path, (newPath) => {
  currentRoute.value = newPath
}, { immediate: true })

// 处理菜单点击
const handleMenuClick = ({ key }) => {
  router.push(key)
  drawerVisible.value = false
}
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  background: #001529;
  padding: 0 24px;
  position: relative;
}

.logo {
  color: #fff;
  font-size: 20px;
  font-weight: bold;
  margin-right: 30px;
  white-space: nowrap;
}

.nav-menu {
  flex: 1;
  background: transparent;
}

.mobile-menu-btn {
  display: none;
  color: #fff;
  font-size: 20px;
  cursor: pointer;
  padding: 8px;
  margin-left: auto;
}

.content {
  padding: 24px;
  margin: 0;
  min-height: 280px;
  background: #f5f5f5;
}

.footer {
  text-align: center;
  background: #fff;
  border-top: 1px solid #e8e8e8;
}

/* 页面过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 移动端适配 */
@media (max-width: 1200px) {
  .desktop-menu {
    display: none;
  }
  
  .mobile-menu-btn {
    display: block;
  }
  
  .logo {
    font-size: 16px;
  }
}

@media (max-width: 768px) {
  .header {
    padding: 0 16px;
  }
  
  .logo {
    font-size: 14px;
    margin-right: 16px;
  }
  
  .content {
    padding: 16px;
  }
}

@media (max-width: 576px) {
  .header {
    padding: 0 12px;
  }
  
  .logo {
    font-size: 13px;
    margin-right: 12px;
  }
  
  .content {
    padding: 12px;
  }
  
  .footer {
    font-size: 12px;
    padding: 12px;
  }
}

/* 移动端抽屉样式 */
:deep(.mobile-drawer .ant-drawer-body) {
  padding: 12px;
}

:deep(.mobile-menu) {
  border: none;
}

:deep(.mobile-menu .ant-menu-item) {
  margin: 4px 0;
  border-radius: 8px;
}

.drawer-header {
  display: flex;
  align-items: center;
}

.drawer-header .logo {
  color: #001529;
  font-size: 16px;
  font-weight: bold;
}
</style>
