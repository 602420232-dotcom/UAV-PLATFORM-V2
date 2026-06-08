<template>
  <a-layout class="default-layout" style="min-height: 100vh">
    <!-- 侧边栏 -->
    <a-layout-sider
      v-model:collapsed="appStore.collapsed"
      collapsible
      :trigger="null"
      theme="dark"
      width="220"
      class="layout-sider"
    >
      <div class="logo">
        <span class="logo-icon">✈</span>
        <span v-if="!appStore.collapsed" class="logo-text">无人机路径规划系统</span>
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        v-model:openKeys="openKeys"
        theme="dark"
        mode="inline"
        @click="handleMenuClick"
      >
        <a-menu-item key="/dashboard">
          <template #icon><DashboardOutlined /></template>
          <span>{{ $t('nav.dashboard') }}</span>
        </a-menu-item>

        <a-menu-item key="/path-planning">
          <template #icon><OrderedListOutlined /></template>
          <span>{{ $t('nav.planning') }}</span>
        </a-menu-item>

        <a-menu-item key="/weather">
          <template #icon><CloudOutlined /></template>
          <span>{{ $t('nav.weather') }}</span>
        </a-menu-item>

        <a-sub-menu key="operation">
          <template #icon><ClusterOutlined /></template>
          <template #title>{{ $t('nav.operation') }}</template>
          <a-menu-item key="/tasks">{{ $t('nav.tasks') }}</a-menu-item>
          <a-menu-item key="/drones">{{ $t('nav.drones') }}</a-menu-item>
          <a-menu-item key="/history">{{ $t('nav.history') }}</a-menu-item>
        </a-sub-menu>

        <a-sub-menu key="data">
          <template #icon><DatabaseOutlined /></template>
          <template #title>{{ $t('nav.data') }}</template>
          <a-menu-item key="/data-sources">{{ $t('nav.dataSources') }}</a-menu-item>
          <a-menu-item key="/assimilation">{{ $t('nav.assimilation') }}</a-menu-item>
        </a-sub-menu>

        <a-menu-item key="/monitoring">
          <template #icon><MonitorOutlined /></template>
          <span>{{ $t('nav.monitoring') }}</span>
        </a-menu-item>

        <a-menu-item key="/cockpit">
          <template #icon><ControlOutlined /></template>
          <span>{{ $t('nav.cockpit') }}</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>

    <!-- 主区域 -->
    <a-layout>
      <!-- 顶栏 -->
      <a-layout-header class="layout-header">
        <div class="header-left">
          <span class="collapse-trigger" @click="toggleCollapse">
            <MenuUnfoldOutlined v-if="appStore.collapsed" />
            <MenuFoldOutlined v-else />
          </span>
          <span class="breadcrumb">{{ currentTitle }}</span>
        </div>
        <div class="header-right">
          <LanguageSwitcher />
          <a-dropdown>
            <div class="user-info">
              <a-avatar :size="32" style="background-color: #1677ff">
                {{ userInitials }}
              </a-avatar>
              <span class="user-name">{{ authStore.user?.username || 'Guest' }}</span>
            </div>
            <template #overlay>
              <a-menu @click="handleUserMenuClick">
                <a-menu-item key="profile">
                  <UserOutlined /> 个人中心
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item key="logout">
                  <LogoutOutlined /> 退出登录
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>

      <!-- 内容区 -->
      <a-layout-content class="layout-content">
        <router-view v-slot="{ Component, route }">
          <transition name="fade" mode="out-in">
            <component :is="Component" :key="route.fullPath" />
          </transition>
        </router-view>
      </a-layout-content>

      <!-- 页脚 -->
      <a-layout-footer class="layout-footer">
        无人机路径规划系统 © {{ new Date().getFullYear() }}
      </a-layout-footer>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  DashboardOutlined,
  OrderedListOutlined,
  CloudOutlined,
  ClusterOutlined,
  DatabaseOutlined,
  MonitorOutlined,
  ControlOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  LogoutOutlined
} from '@ant-design/icons-vue'
import { message, Modal } from 'ant-design-vue'
import LanguageSwitcher from '../components/LanguageSwitcher.vue'
import { useAppStore } from '../stores/app'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()

const selectedKeys = ref([route.path])
const openKeys = ref([])

const currentTitle = computed(() => {
  return route.meta?.title || '无人机路径规划系统'
})

const userInitials = computed(() => {
  const username = authStore.user?.username || 'G'
  return username.charAt(0).toUpperCase()
})

watch(
  () => route.path,
  (newPath) => {
    selectedKeys.value = [newPath]
    if (newPath.startsWith('/tasks') || newPath.startsWith('/drones') || newPath.startsWith('/history')) {
      openKeys.value = ['operation']
    } else if (newPath.startsWith('/data-sources') || newPath.startsWith('/assimilation')) {
      openKeys.value = ['data']
    }
  },
  { immediate: true }
)

const toggleCollapse = () => {
  appStore.toggleCollapse()
}

const handleMenuClick = ({ key }) => {
  if (key !== route.path) {
    router.push(key)
  }
}

const handleUserMenuClick = ({ key }) => {
  if (key === 'logout') {
    Modal.confirm({
      title: '确认退出',
      content: '您确定要退出登录吗？',
      okText: '确认退出',
      cancelText: '取消',
      onOk: async () => {
        await authStore.logout()
        message.success('已退出登录')
        router.push('/login')
      }
    })
  } else if (key === 'profile') {
    message.info('个人中心功能开发中')
  }
}

onMounted(() => {
  authStore.initFromStorage()
})
</script>

<style scoped>
.default-layout {
  height: 100vh;
}

.layout-sider {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 10;
  overflow: auto;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 64px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  overflow: hidden;
  white-space: nowrap;
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-icon {
  font-size: 22px;
  margin-right: 8px;
  color: #1677ff;
}

.logo-text {
  font-size: 14px;
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  position: sticky;
  top: 0;
  z-index: 10;
  margin-left: 220px;
  transition: margin-left 0.2s;
}

.default-layout :deep(.ant-layout-sider-collapsed) + .ant-layout .layout-header {
  margin-left: 80px;
}

.layout-header :deep(.ant-layout-header) {
  margin-left: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-trigger {
  font-size: 18px;
  cursor: pointer;
  color: rgba(0, 0, 0, 0.65);
  transition: color 0.2s;
  display: inline-flex;
  align-items: center;
}

.collapse-trigger:hover {
  color: #1677ff;
}

.breadcrumb {
  font-size: 15px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.88);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.user-info:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.user-name {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.85);
}

.layout-content {
  margin: 24px 24px 0 244px;
  padding: 0;
  min-height: 280px;
  transition: margin-left 0.2s;
}

.default-layout :deep(.ant-layout-sider-collapsed) ~ .ant-layout .layout-content {
  margin-left: 104px;
}

.layout-footer {
  text-align: center;
  color: rgba(0, 0, 0, 0.45);
  background: transparent;
  padding: 16px 24px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式处理 */
@media (max-width: 992px) {
  .layout-header,
  .layout-content {
    margin-left: 0;
  }
}
</style>
