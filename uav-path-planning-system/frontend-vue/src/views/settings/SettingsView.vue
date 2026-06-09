<template>
  <div class="settings-page">
    <div class="settings-grid">
      <!-- 左侧导航 -->
      <aside class="settings-nav">
        <el-menu
          :default-active="activeMenu"
          class="nav-menu"
          @select="handleMenuSelect"
        >
          <el-menu-item index="profile">
            <el-icon><User /></el-icon>
            <span>{{ t('settings.profile') }}</span>
          </el-menu-item>
          <el-menu-item index="permission">
            <el-icon><Lock /></el-icon>
            <span>{{ t('settings.permission') }}</span>
          </el-menu-item>
          <el-menu-item index="preference">
            <el-icon><Setting /></el-icon>
            <span>{{ t('settings.preference') }}</span>
          </el-menu-item>
          <el-menu-item index="notification">
            <el-icon><Bell /></el-icon>
            <span>{{ t('settings.notification') }}</span>
          </el-menu-item>
          <el-menu-item index="docs">
            <el-icon><Document /></el-icon>
            <span>{{ t('settings.docs') }}</span>
          </el-menu-item>
          <el-menu-item index="license">
            <el-icon><Collection /></el-icon>
            <span>{{ t('settings.license') }}</span>
          </el-menu-item>
          <li class="menu-divider"></li>
          <el-menu-item index="logout" class="logout-item">
            <el-icon><SwitchButton /></el-icon>
            <span>{{ t('settings.logout') }}</span>
          </el-menu-item>
        </el-menu>
      </aside>

      <!-- 右侧内容 -->
      <section class="settings-content">
        <!-- 个人信息 -->
        <el-card v-show="activeMenu === 'profile'" shadow="never" class="card-panel">
          <template #header>
            <div class="card-header">
              <span>{{ t('settings.profile') }}</span>
              <el-tag type="success" size="small">{{ t('settings.loggedIn') }}</el-tag>
            </div>
          </template>
          <div class="profile-inner">
            <div class="avatar-block">
              <div class="avatar-circle">{{ avatarLetter }}</div>
              <div class="avatar-meta">
                <div class="avatar-name">{{ authStore.displayName }}</div>
                <div class="avatar-sub">
                  <el-tag size="small" type="primary">{{ authStore.roleLabel }}</el-tag>
                  <span class="text-muted">@{{ authStore.username }}</span>
                </div>
              </div>
            </div>

            <el-descriptions :column="1" border class="info-desc">
              <el-descriptions-item :label="t('settings.username')">{{ authStore.username }}</el-descriptions-item>
              <el-descriptions-item :label="t('settings.displayName')">{{ authStore.displayName }}</el-descriptions-item>
              <el-descriptions-item :label="t('settings.role')">
                <el-tag type="primary" size="small">{{ authStore.roleLabel }}</el-tag>
                <span class="text-muted ml-8">({{ authStore.role }})</span>
              </el-descriptions-item>
              <el-descriptions-item :label="t('settings.loginTime')">{{ formattedLoginTime }}</el-descriptions-item>
              <el-descriptions-item :label="t('settings.email')">
                <span v-if="userEmail">{{ userEmail }}</span>
                <span v-else class="text-muted">{{ t('settings.noEmail') }}</span>
              </el-descriptions-item>
            </el-descriptions>

            <div class="card-actions">
              <el-button type="primary" @click="openPwdDialog">
                <el-icon><Key /></el-icon>
                {{ t('settings.changePassword') }}
              </el-button>
            </div>
          </div>
        </el-card>

        <!-- 权限与角色 -->
        <el-card v-show="activeMenu === 'permission'" shadow="never" class="card-panel">
          <template #header>{{ t('settings.permission') }}</template>

          <h4 class="section-title">{{ t('settings.myRole') }}</h4>
          <div class="role-tags">
            <el-tag
              size="large"
              type="primary"
              effect="dark"
              round
            >
              {{ authStore.roleLabel }}
            </el-tag>
            <el-tag size="large" round>{{ authStore.roleLabelEn }}</el-tag>
          </div>

          <h4 class="section-title">{{ t('settings.permissionList') }}</h4>
          <el-table
            :data="permissionTableData"
            stripe
            border
            style="width: 100%"
          >
            <el-table-column prop="module" :label="t('settings.module')" width="200" />
            <el-table-column prop="key" :label="t('settings.permissionKey')" width="220" />
            <el-table-column prop="description" :label="t('settings.description')" />
            <el-table-column :label="t('settings.status')" width="100">
              <template #default>
                <el-tag type="success" size="small">{{ t('settings.authorized') }}</el-tag>
              </template>
            </el-table-column>
          </el-table>

          <h4 class="section-title">{{ t('settings.accessibleModules') }}</h4>
          <div class="accessible-modules">
            <div
              v-for="mod in accessibleModules"
              :key="mod.key"
              class="module-chip"
            >
              <el-icon class="mod-icon"><component :is="mod.icon" /></el-icon>
              <span>{{ mod.title }}</span>
            </div>
          </div>
        </el-card>

        <!-- 偏好设置 -->
        <el-card v-show="activeMenu === 'preference'" shadow="never" class="card-panel">
          <template #header>{{ t('settings.preference') }}</template>

          <el-form :model="prefForm" label-width="140px" class="preference-form">
            <el-form-item :label="t('settings.theme')">
              <el-radio-group v-model="prefForm.theme">
                <el-radio-button value="light">
                  <el-icon><Sunny /></el-icon>&nbsp;{{ t('settings.light') }}
                </el-radio-button>
                <el-radio-button value="dark">
                  <el-icon><Moon /></el-icon>&nbsp;{{ t('settings.dark') }}
                </el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item :label="t('settings.language')">
              <el-radio-group v-model="prefForm.language">
                <el-radio-button value="zh">{{ t('settings.chinese') }}</el-radio-button>
                <el-radio-button value="en">{{ t('settings.english') }}</el-radio-button>
                <el-radio-button value="ja">{{ t('settings.japanese') }}</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item :label="t('settings.defaultPage')">
              <el-select
                v-model="prefForm.defaultRoute"
                :placeholder="t('settings.selectDefaultPage')"
                style="width: 280px"
              >
                <el-option
                  v-for="opt in defaultRouteOptions"
                  :key="opt.key"
                  :label="opt.title"
                  :value="opt.key"
                />
              </el-select>
              <div class="text-muted form-tip">{{ t('settings.pageFilterTip') }}</div>
            </el-form-item>

            <el-form-item :label="t('settings.sidebar')">
              <el-switch v-model="prefForm.collapsed" :active-text="t('settings.expand')" :inactive-text="t('settings.collapse')" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="savePreference">
                <el-icon><Check /></el-icon>
                {{ t('settings.savePreference') }}
              </el-button>
              <el-button @click="resetPreference">{{ t('settings.reset') }}</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 通知订阅 -->
        <el-card v-show="activeMenu === 'notification'" shadow="never" class="card-panel">
          <template #header>
            <div class="card-header">
              <span>{{ t('settings.notification') }}</span>
              <el-tag type="info" size="small">{{ t('settings.enabledCount', { count: enabledSubscriptionCount }) }}</el-tag>
            </div>
          </template>

          <el-form :model="notificationStore.subscriptionPrefs" label-width="160px" class="preference-form">
            <el-form-item :label="t('settings.taskNotification')">
              <el-switch v-model="notificationStore.subscriptionPrefs.task" @change="saveNotificationPrefs" />
              <span class="text-muted form-tip">{{ t('settings.taskNotificationTip') }}</span>
            </el-form-item>

            <el-form-item :label="t('settings.weatherAlert')">
              <el-switch v-model="notificationStore.subscriptionPrefs.weather" @change="saveNotificationPrefs" />
              <span class="text-muted form-tip">{{ t('settings.weatherAlertTip') }}</span>
            </el-form-item>

            <el-form-item :label="t('settings.droneStatus')">
              <el-switch v-model="notificationStore.subscriptionPrefs.uav" @change="saveNotificationPrefs" />
              <span class="text-muted form-tip">{{ t('settings.droneStatusTip') }}</span>
            </el-form-item>

            <el-form-item :label="t('settings.planning')">
              <el-switch v-model="notificationStore.subscriptionPrefs.planning" @change="saveNotificationPrefs" />
              <span class="text-muted form-tip">{{ t('settings.planningTip') }}</span>
            </el-form-item>

            <el-form-item :label="t('settings.configChange')">
              <el-switch v-model="notificationStore.subscriptionPrefs.config" @change="saveNotificationPrefs" />
              <span class="text-muted form-tip">{{ t('settings.configChangeTip') }}</span>
            </el-form-item>

            <el-form-item :label="t('settings.utmReport')">
              <el-switch v-model="notificationStore.subscriptionPrefs.utm" @change="saveNotificationPrefs" />
              <span class="text-muted form-tip">{{ t('settings.utmReportTip') }}</span>
            </el-form-item>

            <el-form-item :label="t('settings.systemNotification')">
              <el-switch v-model="notificationStore.subscriptionPrefs.system" @change="saveNotificationPrefs" />
              <span class="text-muted form-tip">{{ t('settings.systemNotificationTip') }}</span>
            </el-form-item>

            <el-divider :content-position="'left'">{{ t('settings.desktopNotification') }}</el-divider>

            <el-form-item :label="t('settings.enableDesktop')">
              <el-switch v-model="notificationStore.subscriptionPrefs.desktop" @change="saveNotificationPrefs" />
              <span class="text-muted form-tip">{{ t('settings.enableDesktopTip') }}</span>
            </el-form-item>

            <el-form-item :label="t('settings.desktopPermission')">
              <el-button type="primary" @click="requestDesktopPermission">
                <el-icon><Bell /></el-icon>
                {{ t('settings.requestPermission') }}
              </el-button>
              <el-tag size="small" type="success" v-if="notificationPermission === 'granted'">{{ t('settings.granted') }}</el-tag>
              <el-tag size="small" type="info" v-else-if="notificationPermission === 'denied'">{{ t('settings.denied') }}</el-tag>
              <el-tag size="small" v-else>{{ t('settings.notGranted') }}</el-tag>
            </el-form-item>

            <el-form-item>
              <el-button @click="clearAllNotifications">{{ t('settings.clearNotifications', { count: notificationStore.notifications.length }) }}</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 使用文档跳转 -->
        <el-card v-show="activeMenu === 'docs'" shadow="never" class="card-panel">
          <template #header>{{ t('settings.docs') }}</template>
          <div class="docs-redirect">
            <el-empty :description="t('settings.docsRedirect')">
              <el-button type="primary" @click="goDocs">
                <el-icon><Document /></el-icon>
                {{ t('settings.openDocs') }}
              </el-button>
            </el-empty>
          </div>
        </el-card>

        <!-- License 信息 -->
        <el-card v-show="activeMenu === 'license'" shadow="never" class="card-panel">
          <template #header>{{ t('settings.license') }}</template>
          <h4 class="section-title">MIT License</h4>
          <pre class="license-box"><code>MIT License

Copyright (c) 2026 UAV Path Planning System

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.</code></pre>

          <div class="license-deps">
            <h4 class="section-title">主要依赖</h4>
            <ul class="deps-list">
              <li>Vue 3 — MIT License</li>
              <li>Element Plus — MIT License</li>
              <li>Pinia — MIT License</li>
              <li>Vue Router — MIT License</li>
              <li>Cesium — Apache-2.0 License</li>
            </ul>
          </div>
        </el-card>
      </section>
    </div>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="pwdDialogVisible" :title="t('settings.changePassword')" width="480px">
      <el-form
        ref="pwdFormRef"
        :model="pwdForm"
        :rules="pwdRules"
        label-width="100px"
      >
        <el-form-item :label="t('settings.oldPassword')" prop="oldPwd">
          <el-input v-model="pwdForm.oldPwd" type="password" show-password />
        </el-form-item>
        <el-form-item :label="t('settings.newPassword')" prop="newPwd">
          <el-input v-model="pwdForm.newPwd" type="password" show-password />
        </el-form-item>
        <el-form-item :label="t('settings.confirmPassword')" prop="confirmPwd">
          <el-input v-model="pwdForm.confirmPwd" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitPwd">{{ t('settings.confirmChange') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User, Lock, Setting, Document, Collection, SwitchButton, Bell,
  Key, Sunny, Moon, Check, HomeFilled, PartlyCloudy, Goods,
  Monitor, List, Position, Connection, DataAnalysis, DataLine, Coin, Box, Tools,
  Location, Checked, ChatDotRound, MagicStick, Cpu
} from '@element-plus/icons-vue'
import { useAuthStore, PERMISSION_MATRIX } from '../../stores/auth'
import { useAppStore } from '../../stores/app'
import { useNotificationStore } from '../../stores/notification'

const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()
const appStore = useAppStore()
const notificationStore = useNotificationStore()

// ===== 通知订阅 =====
const notificationPermission = ref(
  typeof Notification !== 'undefined' ? Notification.permission : 'unsupported'
)
const enabledSubscriptionCount = computed(() => {
  if (!notificationStore.subscriptionPrefs) return 0
  return Object.values(notificationStore.subscriptionPrefs).filter(Boolean).length
})
function saveNotificationPrefs() {
  notificationStore.persist()
  ElMessage.success('通知订阅设置已保存')
}
async function requestDesktopPermission() {
  try {
    if (typeof Notification === 'undefined') {
      ElMessage.warning('当前浏览器不支持桌面通知')
      return
    }
    const result = await notificationStore.requestDesktopPermission()
    notificationPermission.value = result
    if (result === 'granted') {
      ElMessage.success('已获得桌面通知权限')
      notificationStore.pushWithDesktop({
        type: 'info',
        title: '桌面通知测试',
        message: '这是一条测试消息，用于验证桌面通知是否正常工作',
        source: 'system'
      })
    } else if (result === 'denied') {
      ElMessage.warning('用户已拒绝桌面通知权限，请在浏览器设置中手动开启')
    } else {
      ElMessage.info('已请求桌面通知权限')
    }
  } catch (e) {
    ElMessage.error('请求桌面通知权限失败：' + e.message)
  }
}
function clearAllNotifications() {
  ElMessageBox.confirm('确认清空所有通知？此操作不可撤销。', '清空确认', {
    type: 'warning'
  }).then(() => {
    notificationStore.clearAll()
    ElMessage.success('已清空所有通知')
  }).catch(() => {})
}

// ===== 左侧导航 =====
const activeMenu = ref('profile')

const NAV_DOCS = 'docs'

function handleMenuSelect(index) {
  if (index === NAV_DOCS) {
    router.push('/docs')
    return
  }
  if (index === 'logout') {
    ElMessageBox.confirm('确认退出当前登录？', '提示', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning'
    }).then(() => {
      authStore.logout()
      router.push('/login')
      ElMessage.success('已退出登录')
    }).catch(() => {})
    return
  }
  activeMenu.value = index
}

// ===== 个人信息 =====
const avatarLetter = computed(() => {
  const name = authStore.displayName || authStore.username || 'U'
  return name.charAt(0).toUpperCase()
})

const formattedLoginTime = computed(() => {
  const t = authStore.user?.loginTime
  if (!t) return '—'
  try {
    return new Date(t).toLocaleString()
  } catch {
    return '—'
  }
})

const userEmail = computed(() => {
  return authStore.user?.email || ''
})

// ===== 修改密码 =====
const pwdDialogVisible = ref(false)
const pwdFormRef = ref(null)
const pwdForm = reactive({
  oldPwd: '',
  newPwd: '',
  confirmPwd: ''
})
const pwdRules = {
  oldPwd: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPwd: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 位', trigger: 'blur' }
  ],
  confirmPwd: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== pwdForm.newPwd) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

function openPwdDialog() {
  pwdForm.oldPwd = ''
  pwdForm.newPwd = ''
  pwdForm.confirmPwd = ''
  pwdDialogVisible.value = true
}

function submitPwd() {
  if (!pwdFormRef.value) return
  pwdFormRef.value.validate((valid) => {
    if (valid) {
      ElMessage.success('密码修改成功（演示模式，不实际持久化）')
      pwdDialogVisible.value = false
    }
  })
}

// ===== 权限与角色 =====
const MODULE_META = {
  dashboard: { title: '项目简介 / 首页', icon: 'HomeFilled' },
  weather: { title: '气象数据', icon: 'PartlyCloudy' },
  'weather-station': { title: '气象站点管理', icon: 'Location' },
  orders: { title: '下单 / 选择运输地点', icon: 'Goods' },
  cockpit: { title: '智能驾驶舱', icon: 'Monitor' },
  tasks: { title: '运输任务管理', icon: 'List' },
  'task-report': { title: '任务报告中心', icon: 'Document' },
  'path-planning': { title: '路径规划', icon: 'Position' },
  airworthiness: { title: '适航性评估', icon: 'Checked' },
  'model-evaluation': { title: '模型评估', icon: 'DataAnalysis' },
  'parameter-tuning': { title: '算法参数调优', icon: 'Tools' },
  'sensitivity-analysis': { title: '参数敏感性分析', icon: 'DataLine' },
  'experiment-compare': { title: '实验对比工具', icon: 'DataAnalysis' },
  assimilation: { title: '数据同化', icon: 'Connection' },
  monitoring: { title: '系统监控面板', icon: 'DataAnalysis' },
  database: { title: '数据库管理', icon: 'Coin' },
  docker: { title: 'Docker / 服务器状态', icon: 'Box' },
  'docker-build': { title: 'Docker 构建', icon: 'Box' },
  'api-config': { title: '气象模型 API 配置', icon: 'Cpu' },
  'permission-templates': { title: '权限模板管理', icon: 'Key' },
  'utm-integration': { title: '低空 UTM 对接', icon: 'Connection' },
  forum: { title: '团队论坛', icon: 'ChatDotRound' },
  'user-stats': { title: '用户统计', icon: 'DataAnalysis' },
  settings: { title: '设置', icon: 'Tools' },
  'theme-customizer': { title: '主题定制', icon: 'MagicStick' },
  docs: { title: '使用文档', icon: 'Document' },
  'permission-debug': { title: '权限调试', icon: 'MagicStick' }
}

const ICON_MAP = {
  HomeFilled, PartlyCloudy, Goods, Monitor, List, Position, Connection,
  DataAnalysis, DataLine, Coin, Box, Setting, Tools, Document,
  Location, Checked, Key, ChatDotRound, MagicStick, Cpu
}

const accessibleModules = computed(() => {
  return authStore.accessibleRoutes
    .filter((k) => MODULE_META[k])
    .map((k) => ({
      key: k,
      title: MODULE_META[k].title,
      icon: ICON_MAP[MODULE_META[k].icon] || Document
    }))
})

const permissionTableData = computed(() => {
  return authStore.accessibleRoutes
    .filter((k) => MODULE_META[k])
    .map((k) => ({
      module: MODULE_META[k].title,
      key: k,
      description: `允许访问 "${MODULE_META[k].title}" 模块`
    }))
})

// ===== 偏好设置 =====
const prefForm = reactive({
  theme: appStore.theme || 'light',
  language: appStore.language || 'zh',
  defaultRoute: appStore.defaultRoute || 'dashboard',
  collapsed: !!appStore.collapsed
})

const defaultRouteOptions = computed(() => {
  const keys = [
    'dashboard', 'weather', 'weather-station', 'orders', 'cockpit', 'tasks', 'task-report',
    'path-planning', 'airworthiness', 'model-evaluation', 'parameter-tuning', 'sensitivity-analysis',
    'experiment-compare', 'assimilation', 'monitoring', 'database', 'docker', 'docker-build',
    'api-config', 'forum', 'user-stats', 'settings', 'docs'
  ]
  return keys
    .filter((k) => authStore.hasRouteAccess(k) && MODULE_META[k])
    .map((k) => ({ key: k, title: MODULE_META[k].title }))
})

onMounted(() => {
  prefForm.theme = appStore.theme
  prefForm.language = appStore.language
  prefForm.defaultRoute = appStore.defaultRoute || (authStore.role ? appStore.getDefaultRoute(authStore.role) : 'dashboard')
  prefForm.collapsed = !!appStore.collapsed

  // 确保 defaultRoute 存在于可选值
  if (!defaultRouteOptions.value.some((o) => o.key === prefForm.defaultRoute)) {
    prefForm.defaultRoute = defaultRouteOptions.value[0]?.key || 'dashboard'
  }
})

function savePreference() {
  appStore.setTheme(prefForm.theme)
  appStore.setLanguage(prefForm.language)
  appStore.setDefaultRoute(prefForm.defaultRoute)
  appStore.setCollapsed(prefForm.collapsed)
  ElMessage.success('偏好设置已保存')
}

function resetPreference() {
  prefForm.theme = 'light'
  prefForm.language = 'zh'
  prefForm.defaultRoute = authStore.role ? appStore.getDefaultRoute(authStore.role) : 'dashboard'
  prefForm.collapsed = false
  appStore.setTheme(prefForm.theme)
  appStore.setLanguage(prefForm.language)
  appStore.setDefaultRoute('')
  appStore.setCollapsed(false)
  ElMessage.info('已恢复默认偏好')
}

function goDocs() {
  router.push('/docs')
}
</script>

<style scoped>
.settings-page {
  padding: 16px;
  min-height: 100%;
  background: var(--color-bg);
}

.settings-grid {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 16px;
  max-width: 1280px;
  margin: 0 auto;
}

.settings-nav {
  background: var(--color-surface);
  border-radius: 10px;
  padding: 8px 0;
  height: fit-content;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.04);
}

.nav-menu {
  border-right: none;
}

.nav-menu .menu-divider {
  height: 1px;
  margin: 8px 16px;
  background-color: var(--el-border-color-light, #e4e7ed);
  list-style: none;
}

.nav-menu .logout-item :deep(.el-menu-item__icon),
.nav-menu .logout-item :deep(.el-menu-item__title) {
  color: #f56c6c;
}

.nav-menu .logout-item:hover :deep(.el-menu-item__icon),
.nav-menu .logout-item:hover :deep(.el-menu-item__title) {
  color: #ffffff;
}

.settings-content {
  min-width: 0;
}

.card-panel {
  border-radius: 10px;
}

.card-panel + .card-panel {
  margin-top: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.profile-inner {
  padding: 8px 4px 4px;
}

.avatar-block {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.avatar-circle {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-success) 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 600;
  letter-spacing: 1px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.25);
}

.avatar-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 6px;
}

.avatar-sub {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-muted);
  font-size: 13px;
}

.text-muted {
  color: var(--color-text-muted);
  font-size: 13px;
}

.ml-8 {
  margin-left: 8px;
}

.info-desc {
  margin-top: 8px;
}

.card-actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.section-title {
  margin: 18px 0 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.role-tags {
  display: flex;
  gap: 10px;
  margin-bottom: 6px;
}

.accessible-modules {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.module-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(64, 158, 255, 0.1);
  color: var(--color-primary);
  border: 1px solid rgba(64, 158, 255, 0.2);
  border-radius: 999px;
  font-size: 13px;
}

.mod-icon {
  font-size: 14px;
}

.preference-form {
  max-width: 640px;
}

.form-tip {
  display: block;
  margin-top: 4px;
  font-size: 12px;
}

.docs-redirect {
  padding: 24px 0;
}

.license-box {
  background: var(--color-surface);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  padding: 16px 18px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 12.5px;
  line-height: 1.7;
  margin-top: 4px;
}

.license-box code {
  font-family: Menlo, Consolas, 'Courier New', monospace;
  white-space: pre;
}

.deps-list {
  margin: 0;
  padding-left: 20px;
  color: var(--color-text-muted);
  font-size: 13px;
  line-height: 1.9;
}
</style>
