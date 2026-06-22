<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

interface MenuChild {
  index: string
  title: string
  icon: string
  menuName: string
}

interface MenuItem {
  index: string
  title: string
  icon: string
  menuName?: string
  children?: MenuChild[]
}

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()

const isCollapsed = computed(() => appStore.sidebarCollapsed)

/** 判断当前用户是否是科研角色 */
const isResearchRole = computed(() => {
  return authStore.currentRole === 'ALGORITHM_ADMIN' || authStore.currentRole === 'OPERATOR'
})

/** 判断当前用户是否是API运营角色 */
const isApiOpsRole = computed(() => {
  return authStore.currentRole === 'SUPER_ADMIN' || authStore.currentRole === 'TENANT_ADMIN'
})

/** 通用菜单（所有角色可见） */
const commonMenuItems: MenuItem[] = [
  { index: '/dashboard', title: '仪表盘', icon: 'Odometer', menuName: 'dashboard' },
]

/** 操作手册菜单（所有角色可见，放在最后） */
const manualMenuItem: MenuItem[] = [
  { index: '/manual', title: '操作手册', icon: 'Document', menuName: 'manual' },
]

/** 核心业务菜单（通用功能） */
const serviceMenuItems: MenuItem[] = [
  {
    index: '/services',
    title: '业务服务',
    icon: 'Grid',
    children: [
      { index: '/weather', title: '气象数据', icon: 'Cloudy', menuName: 'weather' },
      { index: '/planning', title: '路径规划', icon: 'Guide', menuName: 'planning' },
      { index: '/assimilation', title: '数据同化', icon: 'Connection', menuName: 'assimilation' },
      { index: '/risk', title: '风险/适航', icon: 'Warning', menuName: 'risk' },
      { index: '/observation', title: '观测决策', icon: 'View', menuName: 'observation' },
      { index: '/utm', title: 'UTM 管理', icon: 'Position', menuName: 'utm' },
    ],
  },
]

/** 系统管理菜单 */
const systemMenuItems: MenuItem[] = [
  {
    index: '/system',
    title: '系统管理',
    icon: 'Setting',
    children: [
      { index: '/system/tenants', title: '租户管理', icon: 'OfficeBuilding', menuName: 'tenants' },
      { index: '/system/api-keys', title: 'API Key 管理', icon: 'Key', menuName: 'api-keys' },
      { index: '/system/users', title: '用户管理', icon: 'User', menuName: 'users' },
      { index: '/system/roles', title: '角色管理', icon: 'Lock', menuName: 'roles' },
      { index: '/system/database', title: '数据库管理', icon: 'Coin', menuName: 'database' },
    ],
  },
]

/** API 运营管理菜单（SUPER_ADMIN / TENANT_ADMIN） */
const apiOpsMenuItems: MenuItem[] = [
  {
    index: '/api-ops',
    title: 'API 运营管理',
    icon: 'Management',
    children: [
      { index: '/api-ops/dashboard', title: '运营仪表盘', icon: 'Odometer', menuName: 'api-ops-dashboard' },
      { index: '/api-ops/api-keys', title: 'API Key 管理', icon: 'Key', menuName: 'api-keys-ops' },
      { index: '/api-ops/tenants', title: '租户管理', icon: 'OfficeBuilding', menuName: 'tenants-ops' },
      { index: '/api-ops/usage', title: '用量分析', icon: 'DataAnalysis', menuName: 'usage' },
      { index: '/api-ops/health', title: '服务健康', icon: 'Monitor', menuName: 'health' },
      { index: '/api-ops/alerts', title: '告警规则', icon: 'Bell', menuName: 'alerts' },
    ],
  },
]

/** 科研平台菜单（SUPER_ADMIN / ALGORITHM_ADMIN / OPERATOR） */
const researchMenuItems: MenuItem[] = [
  {
    index: '/research',
    title: '科研平台',
    icon: 'SetUp',
    children: [
      { index: '/research/sandbox', title: '科研沙箱', icon: 'Box', menuName: 'research-sandbox' },
      { index: '/research/algorithm-lab', title: '算法实验室', icon: 'Cpu', menuName: 'algorithm-lab' },
      { index: '/research/experiments', title: '实验管理', icon: 'Notebook', menuName: 'experiments' },
      { index: '/research/reports', title: '报告中心', icon: 'Document', menuName: 'reports' },
    ],
  },
]

/** 根据角色动态组装菜单 */
const menuItems = computed(() => {
  const items = [...commonMenuItems]
  const role = authStore.currentRole

  // 所有角色都看到业务服务
  items.push(...serviceMenuItems)

  // SUPER_ADMIN: common + apiOps + research + service + system
  if (role === 'SUPER_ADMIN') {
    items.push(...apiOpsMenuItems)
    items.push(...researchMenuItems)
    items.push(...systemMenuItems)
    items.push(...manualMenuItem)
    return items
  }

  // TENANT_ADMIN: common + apiOps + service
  if (role === 'TENANT_ADMIN') {
    items.push(...apiOpsMenuItems)
    items.push(...manualMenuItem)
    return items
  }

  // OPERATOR: common + research + service
  if (role === 'OPERATOR') {
    items.push(...researchMenuItems)
    items.push(...manualMenuItem)
    return items
  }

  // ALGORITHM_ADMIN: common + research
  if (role === 'ALGORITHM_ADMIN') {
    items.push(...researchMenuItems)
    items.push(...manualMenuItem)
    return items
  }

  // OBSERVER: common + service（只读）
  items.push(...manualMenuItem)
  return items
})

/** 根据当前角色权限过滤菜单项 */
const filteredMenuItems = computed(() => {
  return menuItems.value
    .map((item) => {
      // 如果有子菜单，过滤子菜单项
      if (item.children) {
        const filteredChildren = item.children.filter((child) =>
          authStore.hasMenuAccess(child.menuName)
        )
        // 如果子菜单全部被过滤掉，则不显示该分组
        if (filteredChildren.length === 0) return null
        return { ...item, children: filteredChildren }
      }
      // 无子菜单，直接检查权限（入口菜单不需要检查）
      if (!item.menuName) return item
      return authStore.hasMenuAccess(item.menuName) ? item : null
    })
    .filter(Boolean) as MenuItem[]
})

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

    <!-- 角色标签 -->
    <div v-show="!isCollapsed" class="role-badge">
      <el-tag
        :type="isResearchRole ? 'success' : isApiOpsRole ? 'primary' : 'info'"
        size="small"
        effect="dark"
      >
        {{ isResearchRole ? '科研模式' : isApiOpsRole ? '运营模式' : '访客模式' }}
      </el-tag>
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
      <template v-for="(item, idx) in filteredMenuItems" :key="item.index">
        <!-- 菜单分组分隔线（非首项且有子菜单时显示） -->
        <div v-if="idx > 0 && item.children" class="menu-divider">
          <span v-show="!isCollapsed" class="menu-divider-label">{{ item.title }}</span>
        </div>

        <!-- 有子菜单 -->
        <el-sub-menu v-if="item.children" :index="item.index" class="menu-parent">
          <template #title>
            <el-icon class="menu-icon"><component :is="item.icon" /></el-icon>
            <span class="menu-title">{{ item.title }}</span>
          </template>
          <el-menu-item
            v-for="child in item.children"
            :key="child.index"
            :index="child.index"
            class="menu-child"
          >
            <el-icon class="menu-icon"><component :is="child.icon" /></el-icon>
            <span class="menu-title">{{ child.title }}</span>
          </el-menu-item>
        </el-sub-menu>

        <!-- 无子菜单 -->
        <el-menu-item v-else :index="item.index" class="menu-parent">
          <el-icon class="menu-icon"><component :is="item.icon" /></el-icon>
          <span class="menu-title">{{ item.title }}</span>
        </el-menu-item>
      </template>
    </el-menu>
  </el-aside>
</template>

<style scoped>
.sidebar {
  background-color: #16213e;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
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
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
  padding: 0 12px;
}

.logo-text {
  font-size: 16px;
  font-weight: 700;
  color: #e0e0e0;
  white-space: nowrap;
  transition: opacity 0.3s ease;
  background: linear-gradient(135deg, #e0e0e0 0%, #a0a0b0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.role-badge {
  padding: 8px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  justify-content: center;
}

.sidebar-menu {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  border-right: none;
  padding: 8px 0;
}

/* ============================================
   菜单分组分隔线
   ============================================ */
.menu-divider {
  display: flex;
  align-items: center;
  padding: 12px 20px 6px;
  margin-top: 4px;
}

.menu-divider::before {
  content: '';
  flex: 1;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.08) 20%,
    rgba(255, 255, 255, 0.08) 80%,
    transparent 100%
  );
}

.menu-divider-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 0 10px;
  white-space: nowrap;
}

/* ============================================
   菜单项基础样式
   ============================================ */
.sidebar-menu :deep(.el-menu-item),
.sidebar-menu :deep(.el-sub-menu__title) {
  height: auto !important;
  line-height: normal !important;
  padding: 10px 20px !important;
  margin: 2px 10px;
  border-radius: var(--radius-sm, 6px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

/* 图标与文字间距 */
.sidebar-menu :deep(.el-menu-item .el-icon),
.sidebar-menu :deep(.el-sub-menu__title .el-icon) {
  margin-right: 12px;
  font-size: 18px;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), color 0.3s ease;
}

/* ============================================
   Hover 效果：左侧高亮条 + 背景渐变
   ============================================ */
.sidebar-menu :deep(.el-menu-item:hover),
.sidebar-menu :deep(.el-sub-menu__title:hover) {
  background: linear-gradient(135deg, #1a2745 0%, #1e2d4d 100%) !important;
}

.sidebar-menu :deep(.el-menu-item:hover)::before,
.sidebar-menu :deep(.el-sub-menu__title:hover)::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: var(--color-accent, #e94560);
  border-radius: 0 2px 2px 0;
  opacity: 0.6;
  transition: opacity 0.3s ease, height 0.3s ease;
}

.sidebar-menu :deep(.el-menu-item:hover)::after,
.sidebar-menu :deep(.el-sub-menu__title:hover)::after {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: var(--color-accent, #e94560);
  border-radius: 0 2px 2px 0;
  opacity: 0;
  filter: blur(4px);
  transition: opacity 0.3s ease;
}

.sidebar-menu :deep(.el-menu-item:hover .el-icon),
.sidebar-menu :deep(.el-sub-menu__title:hover .el-icon) {
  transform: translateY(-1px);
  color: var(--color-accent-light, #ff6b81);
}

/* ============================================
   当前选中项高亮 - 左侧高亮指示器
   ============================================ */
.sidebar-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(135deg, #0f3460 0%, #134070 100%) !important;
  font-weight: 600;
  position: relative;
}

/* 左侧高亮条 */
.sidebar-menu :deep(.el-menu-item.is-active)::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 70%;
  background: var(--color-accent, #e94560);
  border-radius: 0 2px 2px 0;
  box-shadow: 0 0 8px rgba(233, 69, 96, 0.4);
}

/* 右侧微光效果 */
.sidebar-menu :deep(.el-menu-item.is-active)::after {
  content: '';
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 70%;
  background: linear-gradient(90deg, transparent, rgba(233, 69, 96, 0.05));
  border-radius: 0 6px 6px 0;
}

.sidebar-menu :deep(.el-menu-item.is-active .el-icon) {
  color: var(--color-accent-light, #ff6b81);
}

/* ============================================
   子菜单层级缩进
   ============================================ */
.sidebar-menu :deep(.el-sub-menu .el-menu-item) {
  padding-left: 52px !important;
  font-size: 13px;
  opacity: 0.9;
}

.sidebar-menu :deep(.el-sub-menu .el-menu-item.is-active) {
  opacity: 1;
}

/* 父菜单与子菜单间距 */
.sidebar-menu :deep(.el-sub-menu) {
  margin-bottom: 2px;
}

/* 子菜单展开动画 */
.sidebar-menu :deep(.el-sub-menu .el-menu) {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 子菜单展开箭头 */
.sidebar-menu :deep(.el-sub-menu__title .el-sub-menu__icon-arrow) {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: var(--color-text-muted);
}

.sidebar-menu :deep(.el-sub-menu.is-opened > .el-sub-menu__title .el-sub-menu__icon-arrow) {
  transform: rotate(180deg);
  color: var(--color-text-secondary);
}

/* ============================================
   折叠状态样式
   ============================================ */
.sidebar-menu :deep(.el-menu--collapse) {
  width: 64px;
}

.sidebar-menu :deep(.el-menu--collapse .el-menu-item),
.sidebar-menu :deep(.el-menu--collapse .el-sub-menu__title) {
  padding: 12px 0 !important;
  margin: 4px 10px;
  justify-content: center;
  border-radius: var(--radius-sm, 6px);
}

.sidebar-menu :deep(.el-menu--collapse .el-icon) {
  margin-right: 0 !important;
  font-size: 20px;
}

/* 折叠时 tooltip 样式优化 */
.sidebar-menu :deep(.el-menu--collapse .el-sub-menu.is-active .el-sub-menu__title) {
  background: linear-gradient(135deg, #0f3460 0%, #134070 100%) !important;
}

/* 折叠时隐藏分隔线 */
.sidebar-menu :deep(.el-menu--collapse + .menu-divider),
.sidebar-menu :deep(.el-menu--collapse ~ .menu-divider) {
  display: none;
}

/* 菜单文字过渡 */
.menu-title {
  transition: opacity 0.25s ease;
}

/* ============================================
   滚动条美化
   ============================================ */
.sidebar-menu::-webkit-scrollbar {
  width: 4px;
}

.sidebar-menu::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-menu::-webkit-scrollbar-thumb {
  background: rgba(160, 160, 176, 0.15);
  border-radius: 2px;
  transition: background 0.3s ease;
}

.sidebar-menu::-webkit-scrollbar-thumb:hover {
  background: rgba(160, 160, 176, 0.3);
}
</style>
