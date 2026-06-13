<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()

const isCollapsed = computed(() => appStore.sidebarCollapsed)

const menuItems = [
  { index: '/dashboard', title: '仪表盘', icon: 'Odometer' },
  {
    index: '/system',
    title: '系统管理',
    icon: 'Setting',
    children: [
      { index: '/tenants', title: '租户管理', icon: 'OfficeBuilding' },
      { index: '/api-keys', title: 'API Key 管理', icon: 'Key' },
    ],
  },
  {
    index: '/services',
    title: '业务服务',
    icon: 'Grid',
    children: [
      { index: '/weather', title: '气象数据', icon: 'Cloudy' },
      { index: '/planning', title: '路径规划', icon: 'Map' },
      { index: '/assimilation', title: '数据同化', icon: 'Connection' },
      { index: '/risk', title: '风险/适航', icon: 'Warning' },
      { index: '/observation', title: '观测决策', icon: 'View' },
      { index: '/utm', title: 'UTM 管理', icon: 'Position' },
    ],
  },
  { index: '/algorithms', title: '算法管理', icon: 'Cpu' },
]

function handleSelect(index: string) {
  router.push(index)
}
</script>

<template>
  <el-aside
    class="sidebar"
    :width="isCollapsed ? '64px' : '240px'"
  >
    <div class="sidebar-logo">
      <el-icon :size="24" color="#e94560"><Promotion /></el-icon>
      <span v-show="!isCollapsed" class="logo-text">UAV Platform</span>
    </div>

    <el-menu
      :default-active="route.path"
      :collapse="isCollapsed"
      :collapse-transition="false"
      background-color="#16213e"
      text-color="#a0a0b0"
      active-text-color="#e0e0e0"
      class="sidebar-menu"
      @select="handleSelect"
    >
      <template v-for="item in menuItems" :key="item.index">
        <!-- 有子菜单 -->
        <el-sub-menu v-if="item.children" :index="item.index">
          <template #title>
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </template>
          <el-menu-item
            v-for="child in item.children"
            :key="child.index"
            :index="child.index"
          >
            <el-icon><component :is="child.icon" /></el-icon>
            <span>{{ child.title }}</span>
          </el-menu-item>
        </el-sub-menu>

        <!-- 无子菜单 -->
        <el-menu-item v-else :index="item.index">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </template>
    </el-menu>
  </el-aside>
</template>

<style scoped>
.sidebar {
  background-color: var(--color-sidebar);
  border-right: 1px solid var(--color-border);
  transition: width 0.3s ease;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.sidebar-logo {
  height: var(--header-height);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text-primary);
  white-space: nowrap;
}

.sidebar-menu {
  flex: 1;
  overflow-y: auto;
  border-right: none;
}

.sidebar-menu .el-menu-item.is-active {
  background-color: var(--color-sidebar-active) !important;
  border-right: 3px solid var(--color-accent);
}

.sidebar-menu .el-menu-item:hover,
.sidebar-menu .el-sub-menu__title:hover {
  background-color: var(--color-sidebar-hover) !important;
}
</style>
