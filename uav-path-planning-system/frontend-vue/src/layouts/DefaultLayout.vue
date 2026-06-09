<template>
  <div class="uav-layout" :class="{ 'is-collapsed': appStore.collapsed, 'is-dark': appStore.isDark, 'is-mobile': isMobile }">
    <!-- 演示模式顶部提示条 -->
    <div v-if="authStore.demoMode" class="demo-banner">
      <el-icon class="demo-icon"><InfoFilled /></el-icon>
      <span>当前为<strong>演示模式</strong>，部分数据为模拟数据。配置真实 API 后可切换为生产模式。</span>
      <el-button type="primary" link @click="goToApiConfig" v-if="canAccessApiConfig">
        前往 API 配置 →
      </el-button>
    </div>

    <!-- 首次进入 Toast 提示 -->
    <el-alert
      v-if="showDemoToast"
      class="demo-toast"
      :title="'欢迎使用演示模式'"
      type="info"
      description="您正在使用演示模式体验系统功能。所有数据均为模拟数据。"
      show-icon
      :closable="true"
      @close="onDemoToastClose"
    />

    <el-container class="uav-container">
      <!-- 左侧边栏（桌面端） -->
      <el-aside
        v-show="!isMobile"
        :width="appStore.collapsed ? '64px' : '220px'"
        class="uav-aside"
        :class="{ collapsed: appStore.collapsed }"
      >
        <div class="logo-area" @click="goHome">
          <div class="logo-icon">
            <el-icon :size="22"><PartlyCloudy /></el-icon>
          </div>
          <span v-if="!appStore.collapsed" class="logo-text">
            WRF 无人机路径规划
          </span>
        </div>

        <el-menu
          :default-active="currentRoute"
          :collapse="appStore.collapsed"
          :collapse-transition="false"
          class="uav-menu"
          background-color="#001529"
          text-color="#c9d1d9"
          active-text-color="#52c41a"
          router
        >
          <template v-for="item in menuItems" :key="item.key">
            <el-menu-item v-if="!item.children" :index="item.path" :disabled="item.disabled">
              <el-icon><component :is="item.icon" /></el-icon>
              <template #title>{{ item.title }}</template>
            </el-menu-item>

            <el-sub-menu v-else :index="'sub-' + item.key">
              <template #title>
                <el-icon><component :is="item.icon" /></el-icon>
                <span>{{ item.title }}</span>
              </template>
              <el-menu-item
                v-for="child in item.children"
                :key="child.key"
                :index="child.path"
                :disabled="child.disabled"
              >
                <el-icon><component :is="child.icon" /></el-icon>
                <template #title>{{ child.title }}</template>
              </el-menu-item>
            </el-sub-menu>
          </template>

          <el-menu-divider />
          <el-menu-item index="/docs">
            <el-icon><Document /></el-icon>
            <template #title>使用文档</template>
          </el-menu-item>
          <el-sub-menu index="sub-settings">
            <template #title>
              <el-icon><Tools /></el-icon>
              <span>设置</span>
            </template>
            <el-menu-item index="/settings">
              <el-icon><Setting /></el-icon>
              <template #title>系统设置</template>
            </el-menu-item>
            <el-menu-item index="/theme-customizer">
              <el-icon><MagicStick /></el-icon>
              <template #title>主题定制</template>
            </el-menu-item>
            <el-menu-item
              v-if="authStore.hasRouteAccess('permission-debug')"
              index="/permission-debug"
            >
              <el-icon><MagicStick /></el-icon>
              <template #title>权限调试工具</template>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-aside>

      <!-- 移动端抽屉 -->
      <el-drawer
        v-model="drawerVisible"
        direction="ltr"
        size="280px"
        :with-header="false"
        class="uav-drawer"
      >
        <div class="drawer-logo" @click="goHomeDrawer">
          <div class="logo-icon">
            <el-icon :size="22"><PartlyCloudy /></el-icon>
          </div>
          <span class="logo-text">WRF 无人机路径规划</span>
        </div>
        <el-menu
          :default-active="currentRoute"
          class="uav-menu drawer-menu"
          background-color="#001529"
          text-color="#c9d1d9"
          active-text-color="#52c41a"
          router
          @select="onDrawerSelect"
        >
          <template v-for="item in menuItems" :key="item.key">
            <el-menu-item v-if="!item.children" :index="item.path" :disabled="item.disabled">
              <el-icon><component :is="item.icon" /></el-icon>
              <template #title>{{ item.title }}</template>
            </el-menu-item>
            <el-sub-menu v-else :index="'sub-' + item.key">
              <template #title>
                <el-icon><component :is="item.icon" /></el-icon>
                <span>{{ item.title }}</span>
              </template>
              <el-menu-item
                v-for="child in item.children"
                :key="child.key"
                :index="child.path"
                :disabled="child.disabled"
              >
                <el-icon><component :is="child.icon" /></el-icon>
                <template #title>{{ child.title }}</template>
              </el-menu-item>
            </el-sub-menu>
          </template>
          <el-menu-divider />
          <el-menu-item index="/docs">
            <el-icon><Document /></el-icon>
            <template #title>使用文档</template>
          </el-menu-item>
          <el-sub-menu index="sub-settings">
            <template #title>
              <el-icon><Tools /></el-icon>
              <span>设置</span>
            </template>
            <el-menu-item index="/settings">
              <el-icon><Setting /></el-icon>
              <template #title>系统设置</template>
            </el-menu-item>
            <el-menu-item index="/theme-customizer">
              <el-icon><MagicStick /></el-icon>
              <template #title>主题定制</template>
            </el-menu-item>
            <el-menu-item
              v-if="authStore.hasRouteAccess('permission-debug')"
              index="/permission-debug"
            >
              <el-icon><MagicStick /></el-icon>
              <template #title>权限调试工具</template>
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
      </el-drawer>

      <!-- 通知中心抽屉 -->
      <NotificationDrawer
        v-model="notificationDrawerVisible"
      />

      <!-- 右侧主区域 -->
      <el-container class="uav-main-container">
        <!-- 顶部栏 -->
        <el-header class="uav-header" height="52px">
          <div class="header-left">
            <!-- 移动端汉堡按钮 -->
            <el-button
              v-if="isMobile"
              text
              class="hamburger-btn"
              @click="drawerVisible = true"
            >
              <el-icon :size="20"><Menu /></el-icon>
            </el-button>
            <el-button
              v-else
              text
              class="collapse-btn"
              @click="appStore.toggleSidebar()"
            >
              <el-icon :size="18">
                <Fold v-if="!appStore.collapsed" />
                <Expand v-else />
              </el-icon>
            </el-button>
            <span class="breadcrumb-title">{{ currentTitle }}</span>
          </div>

          <div class="header-right">
            <!-- 演示模式标识 -->
            <el-tag
              v-if="authStore.demoMode"
              type="info"
              effect="plain"
              size="default"
              class="demo-tag"
            >
              <el-icon><MagicStick /></el-icon>&nbsp;<span class="hide-on-mobile">演示模式</span>
            </el-tag>
            <el-tag v-else type="success" effect="plain" size="default" class="demo-tag">
              <el-icon><Sunny /></el-icon>&nbsp;<span class="hide-on-mobile">生产模式</span>
            </el-tag>

            <!-- 主题切换 -->
            <el-button text @click="appStore.toggleTheme()" class="theme-btn">
              <el-icon :size="18"><Moon v-if="!appStore.isDark" /><Sunny v-else /></el-icon>
            </el-button>

            <!-- 通知铃铛 -->
            <el-badge
              :value="notificationStore.unreadCount"
              :hidden="notificationStore.unreadCount === 0"
              class="notification-badge"
              :max="99"
            >
              <el-button text class="notification-btn" @click="notificationDrawerVisible = true">
                <el-icon :size="18"><Bell /></el-icon>
              </el-button>
            </el-badge>

            <!-- 用户下拉 -->
            <el-dropdown @command="onUserCommand">
              <span class="user-info">
                <el-avatar :size="30" class="user-avatar">
                  {{ (authStore.displayName || 'U').charAt(0).toUpperCase() }}
                </el-avatar>
                <span class="user-name hide-on-mobile">{{ authStore.displayName }}</span>
                <el-tag size="small" class="role-tag hide-on-mobile" :type="roleTagType">
                  {{ authStore.roleLabel }}
                </el-tag>
                <el-icon class="hide-on-mobile"><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">
                    <el-icon><User /></el-icon>个人信息
                  </el-dropdown-item>
                  <el-dropdown-item command="settings">
                    <el-icon><Setting /></el-icon>系统设置
                  </el-dropdown-item>
                  <el-dropdown-item divided command="logout">
                    <el-icon><SwitchButton /></el-icon>退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <!-- 内容区 -->
        <el-main class="uav-main">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>

        <!-- 底部 -->
        <el-footer class="uav-footer" height="32px">
          <span>{{ t('app.title') }} · v3.3.0 · MIT License</span>
        </el-footer>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import {
  HomeFilled, PartlyCloudy, Goods, Monitor, List, Position, Connection,
  DataAnalysis, Coin, Box, Setting, Tools, Document,
  Fold, Expand, Moon, Sunny, ArrowDown, User, SwitchButton,
  MagicStick, InfoFilled, Cpu, Menu, Bell
} from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useAppStore } from '../stores/app'
import { useNotificationStore } from '../stores/notification'
import NotificationDrawer from '../components/shared/NotificationDrawer.vue'

const authStore = useAuthStore()
const appStore = useAppStore()
const notificationStore = useNotificationStore()
const router = useRouter()
const route = useRoute()
const { t } = useI18n()

const showDemoToast = ref(false)
const drawerVisible = ref(false)
const notificationDrawerVisible = ref(false)

// 响应式：移动端判定
const isMobile = ref(false)
let mqHandler = null

function updateIsMobile() {
  if (typeof window === 'undefined' || !window.matchMedia) return
  isMobile.value = window.matchMedia('(max-width: 768px)').matches
}

onMounted(() => {
  if (authStore.demoMode && !authStore.demoShownOnce) {
    showDemoToast.value = true
    authStore.markDemoShown()
  }
  if (typeof window !== 'undefined' && window.matchMedia) {
    const mql = window.matchMedia('(max-width: 768px)')
    mqHandler = (e) => {
      isMobile.value = e.matches
      if (e.matches) drawerVisible.value = false
    }
    if (typeof mql.addEventListener === 'function') {
      mql.addEventListener('change', mqHandler)
    } else if (typeof mql.addListener === 'function') {
      mql.addListener(mqHandler)
    }
    isMobile.value = mql.matches
  }

  // 系统上线通知（首次进入或每日一次）
  try {
    const today = new Date().toISOString().slice(0, 10)
    const lastShown = localStorage.getItem('uav_system_notify_date_v1')
    if (lastShown !== today) {
      notificationStore.pushWithDesktop({
        type: 'info',
        title: '系统已上线',
        message: '欢迎使用无人机路径规划系统，当前为演示模式。',
        source: 'system'
      })
      localStorage.setItem('uav_system_notify_date_v1', today)
    }
  } catch (_) {}

  // 启动健康检查定时器（演示模式每 2 分钟推送一条）
  if (authStore.demoMode) {
    notificationStore.startHealthCheck(120000)
  }
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined' && window.matchMedia && mqHandler) {
    const mql = window.matchMedia('(max-width: 768px)')
    if (typeof mql.removeEventListener === 'function') {
      mql.removeEventListener('change', mqHandler)
    } else if (typeof mql.removeListener === 'function') {
      mql.removeListener(mqHandler)
    }
  }
})

function onDemoToastClose() {
  showDemoToast.value = false
}

function onDrawerSelect() {
  drawerVisible.value = false
}

function goHomeDrawer() {
  drawerVisible.value = false
  goHome()
}

const currentRoute = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || '首页')

const canAccessApiConfig = computed(() =>
  authStore.hasRouteAccess('api-config')
)

const roleTagType = computed(() => {
  const map = {
    admin: 'danger',
    deployment: 'warning',
    flight: 'success',
    production: '',
    tester: 'info',
    user: 'info'
  }
  return map[authStore.role] || 'info'
})

const menuItems = computed(() => {
  const all = [
    { key: 'dashboard', title: t('menu.dashboard'), icon: 'HomeFilled', path: '/dashboard' },
    { key: 'weather', title: t('menu.weather'), icon: 'PartlyCloudy', path: '/weather' },
    { key: 'weather-station', title: t('menu.weather'), icon: 'Position', path: '/weather-station' },
    { key: 'orders', title: t('menu.orders'), icon: 'Goods', path: '/orders' },
    { key: 'cockpit', title: t('menu.cockpit'), icon: 'Monitor', path: '/cockpit' },
    { key: 'tasks', title: t('menu.tasks'), icon: 'List', path: '/tasks' },
    { key: 'task-report', title: t('menu.taskReport'), icon: 'Document', path: '/task-report' },
    { key: 'utm-integration', title: t('menu.utmIntegration'), icon: 'Connection', path: '/utm-integration' },
    { key: 'path-planning', title: t('menu.pathPlanning'), icon: 'Position', path: '/path-planning' },
    { key: 'airworthiness', title: t('common.info'), icon: 'DataAnalysis', path: '/airworthiness' },
    { key: 'model-evaluation', title: t('menu.modelEvaluation'), icon: 'DataAnalysis', path: '/model-evaluation' },
    { key: 'parameter-tuning', title: t('menu.parameterTuning'), icon: 'Tools', path: '/parameter-tuning' },
    { key: 'sensitivity-analysis', title: t('paramsTuning.sensitivity'), icon: 'DataAnalysis', path: '/sensitivity-analysis' },
    { key: 'experiment-compare', title: t('common.info'), icon: 'DataAnalysis', path: '/experiment-compare' },
    { key: 'assimilation', title: t('menu.dataAssimilation'), icon: 'Connection', path: '/assimilation' },
    { key: 'monitoring', title: t('menu.monitoring'), icon: 'DataAnalysis', path: '/monitoring' },
    { key: 'database', title: t('menu.database'), icon: 'Coin', path: '/database' },
    { key: 'docker', title: t('menu.docker'), icon: 'Box', path: '/docker' },
    { key: 'api-config', title: t('menu.apiConfig'), icon: 'Cpu', path: '/api-config' },
    { key: 'permission-templates', title: t('menu.permissionTemplates'), icon: 'Setting', path: '/permission-templates' }
  ]

  return all.filter(item => authStore.hasRouteAccess(item.key))
})

function goHome() {
  const defaultRoute = appStore.getDefaultRoute(authStore.role)
  router.push('/' + defaultRoute)
}

function goToApiConfig() {
  router.push('/api-config')
}

function onUserCommand(cmd) {
  switch (cmd) {
    case 'profile':
      router.push('/settings')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      ElMessage.success('已退出登录')
      authStore.logout()
      router.push('/login')
      break
  }
}
</script>

<style scoped>
.uav-layout {
  min-height: 100vh;
  background: #f0f2f5;
}
.uav-layout.is-dark {
  background: #0d1117;
  color: #c9d1d9;
}

/* 演示模式顶部提示条 */
.demo-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: linear-gradient(90deg, #fff7e6, #fffbe6);
  color: #d48806;
  font-size: 13px;
  border-bottom: 1px solid #ffe58f;
}
.demo-banner .demo-icon { font-size: 16px; }
.demo-banner strong { color: #ad6800; margin: 0 2px; }
.is-dark .demo-banner {
  background: linear-gradient(90deg, #1a1200, #1a1400);
  color: #d4a94c;
  border-bottom-color: #3a2a00;
}

.demo-toast {
  margin: 8px 16px;
}

.uav-container {
  height: calc(100vh - (var(--banner-height, 0px)));
}

/* 侧边栏 */
.uav-aside {
  background: #001529;
  transition: width 0.2s;
  overflow: hidden;
}
.uav-aside.collapsed {
  overflow: hidden;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  height: 52px;
  color: #fff;
  font-weight: 600;
  font-size: 15px;
  border-bottom: 1px solid #1f2a3d;
  cursor: pointer;
  user-select: none;
}
.logo-area:hover { background: #0a1a2e; }
.logo-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: linear-gradient(135deg, #1890ff, #52c41a);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.logo-text {
  white-space: nowrap;
  overflow: hidden;
}

.uav-menu {
  border-right: none;
  height: calc(100% - 52px);
}
.uav-menu:not(.el-menu--collapse) {
  width: 220px;
}

/* 主容器 */
.uav-main-container {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.uav-header {
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}
.is-dark .uav-header {
  background: #161b22;
  border-bottom-color: #30363d;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.collapse-btn { color: #333 !important; padding: 0 8px !important; }
.is-dark .collapse-btn { color: #c9d1d9 !important; }
.breadcrumb-title {
  font-size: 15px;
  font-weight: 500;
  color: #24292f;
}
.is-dark .breadcrumb-title { color: #c9d1d9; }

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.demo-tag { margin-right: 8px; }
.theme-btn { color: #666 !important; padding: 0 8px !important; }
.notification-btn { color: #666 !important; padding: 0 8px !important; }
.notification-badge { margin-right: 4px; }
.is-dark .theme-btn { color: #e5c07b !important; }
.is-dark .notification-btn { color: #c9d1d9 !important; }

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 0 8px;
  color: #24292f;
}
.is-dark .user-info { color: #c9d1d9; }
.user-avatar {
  background: linear-gradient(135deg, #1890ff, #52c41a);
  color: #fff;
  font-weight: 600;
}
.user-name {
  font-size: 14px;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.role-tag {
  margin-left: 4px;
}

.uav-main {
  padding: 20px;
  overflow-y: auto;
  flex: 1;
}

.uav-footer {
  text-align: center;
  font-size: 12px;
  color: #8c8c8c;
  border-top: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}
.is-dark .uav-footer {
  border-top-color: #30363d;
  color: #6e7681;
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 移动端抽屉与抽屉专用 */
.uav-layout.is-mobile .uav-main {
  padding: 12px;
}

.uav-layout.is-mobile .breadcrumb-title {
  font-size: 14px;
}

.hamburger-btn {
  color: #333 !important;
  padding: 0 8px !important;
}
.is-dark .hamburger-btn {
  color: #c9d1d9 !important;
}

.uav-drawer :deep(.el-drawer) {
  background: #001529;
}
.uav-drawer :deep(.el-drawer__body) {
  padding: 0;
  background: #001529;
}

.drawer-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  height: 52px;
  color: #fff;
  font-weight: 600;
  font-size: 15px;
  border-bottom: 1px solid #1f2a3d;
  cursor: pointer;
}

.drawer-menu {
  border-right: none;
  height: calc(100vh - 52px);
  height: calc(100vh - 52px);
  overflow-y: auto;
}

.hide-on-mobile {
  display: inline;
}

@media (max-width: 768px) {
  .hide-on-mobile {
    display: none !important;
  }

  .uav-footer {
    font-size: 11px;
    padding: 0 8px;
  }

  .header-right {
    gap: 8px;
  }

  .demo-tag {
    margin-right: 0;
    font-size: 12px;
  }

  .demo-banner {
    font-size: 12px;
    padding: 6px 10px;
  }

  .uav-header {
    padding: 0 10px;
  }
}

@media (max-width: 480px) {
  .breadcrumb-title {
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}
</style>
