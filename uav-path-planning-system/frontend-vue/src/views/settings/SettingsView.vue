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
            <span>个人信息</span>
          </el-menu-item>
          <el-menu-item index="permission">
            <el-icon><Lock /></el-icon>
            <span>权限与角色</span>
          </el-menu-item>
          <el-menu-item index="preference">
            <el-icon><Setting /></el-icon>
            <span>偏好设置</span>
          </el-menu-item>
          <el-menu-item index="notification">
            <el-icon><Bell /></el-icon>
            <span>通知订阅</span>
          </el-menu-item>
          <el-menu-item index="docs">
            <el-icon><Document /></el-icon>
            <span>使用文档</span>
          </el-menu-item>
          <el-menu-item index="license">
            <el-icon><Collection /></el-icon>
            <span>License 信息</span>
          </el-menu-item>
          <el-menu-divider />
          <el-menu-item index="logout" class="logout-item">
            <el-icon><SwitchButton /></el-icon>
            <span>退出登录</span>
          </el-menu-item>
        </el-menu>
      </aside>

      <!-- 右侧内容 -->
      <section class="settings-content">
        <!-- 个人信息 -->
        <el-card v-show="activeMenu === 'profile'" shadow="never" class="card-panel">
          <template #header>
            <div class="card-header">
              <span>个人信息</span>
              <el-tag type="success" size="small">已登录</el-tag>
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
              <el-descriptions-item label="用户名">{{ authStore.username }}</el-descriptions-item>
              <el-descriptions-item label="显示名称">{{ authStore.displayName }}</el-descriptions-item>
              <el-descriptions-item label="角色">
                <el-tag type="primary" size="small">{{ authStore.roleLabel }}</el-tag>
                <span class="text-muted ml-8">({{ authStore.role }})</span>
              </el-descriptions-item>
              <el-descriptions-item label="登录时间">{{ formattedLoginTime }}</el-descriptions-item>
              <el-descriptions-item label="邮箱">
                <span v-if="userEmail">{{ userEmail }}</span>
                <span v-else class="text-muted">未绑定邮箱（演示账号）</span>
              </el-descriptions-item>
            </el-descriptions>

            <div class="card-actions">
              <el-button type="primary" @click="openPwdDialog">
                <el-icon><Key /></el-icon>
                修改密码
              </el-button>
            </div>
          </div>
        </el-card>

        <!-- 权限与角色 -->
        <el-card v-show="activeMenu === 'permission'" shadow="never" class="card-panel">
          <template #header>权限与角色</template>

          <h4 class="section-title">我的角色</h4>
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

          <h4 class="section-title">我的权限清单</h4>
          <el-table
            :data="permissionTableData"
            stripe
            border
            style="width: 100%"
          >
            <el-table-column prop="module" label="模块" width="200" />
            <el-table-column prop="key" label="权限 Key" width="220" />
            <el-table-column prop="description" label="说明" />
            <el-table-column label="状态" width="100">
              <template #default>
                <el-tag type="success" size="small">已授权</el-tag>
              </template>
            </el-table-column>
          </el-table>

          <h4 class="section-title">可访问模块</h4>
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
          <template #header>偏好设置</template>

          <el-form :model="prefForm" label-width="140px" class="preference-form">
            <el-form-item label="主题">
              <el-radio-group v-model="prefForm.theme">
                <el-radio-button label="light">
                  <el-icon><Sunny /></el-icon>&nbsp;浅色
                </el-radio-button>
                <el-radio-button label="dark">
                  <el-icon><Moon /></el-icon>&nbsp;深色
                </el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="语言">
              <el-radio-group v-model="prefForm.language">
                <el-radio-button label="zh">中文</el-radio-button>
                <el-radio-button label="en">English</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="默认进入页面">
              <el-select
                v-model="prefForm.defaultRoute"
                placeholder="请选择默认进入页面"
                style="width: 280px"
              >
                <el-option
                  v-for="opt in defaultRouteOptions"
                  :key="opt.key"
                  :label="opt.title"
                  :value="opt.key"
                />
              </el-select>
              <div class="text-muted form-tip">根据您当前的角色动态过滤可选首页。</div>
            </el-form-item>

            <el-form-item label="侧边栏折叠">
              <el-switch v-model="prefForm.collapsed" active-text="展开" inactive-text="折叠" />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="savePreference">
                <el-icon><Check /></el-icon>
                保存偏好
              </el-button>
              <el-button @click="resetPreference">恢复默认</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 通知订阅 -->
        <el-card v-show="activeMenu === 'notification'" shadow="never" class="card-panel">
          <template #header>
            <div class="card-header">
              <span>通知订阅设置</span>
              <el-tag type="info" size="small">共 {{ enabledSubscriptionCount }} 项已启用</el-tag>
            </div>
          </template>

          <el-form :model="notificationStore.subscriptionPrefs" label-width="160px" class="preference-form">
            <el-form-item label="任务通知">
              <el-switch v-model="notificationStore.subscriptionPrefs.task" @change="saveNotificationPrefs" />
              <span class="text-muted form-tip">任务新增、完成、失败等相关通知</span>
            </el-form-item>

            <el-form-item label="气象预警">
              <el-switch v-model="notificationStore.subscriptionPrefs.weather" @change="saveNotificationPrefs" />
              <span class="text-muted form-tip">风速过大、强降雨等气象预警</span>
            </el-form-item>

            <el-form-item label="无人机状态">
              <el-switch v-model="notificationStore.subscriptionPrefs.uav" @change="saveNotificationPrefs" />
              <span class="text-muted form-tip">低电量、信号丢失、禁飞区入侵</span>
            </el-form-item>

            <el-form-item label="路径规划">
              <el-switch v-model="notificationStore.subscriptionPrefs.planning" @change="saveNotificationPrefs" />
              <span class="text-muted form-tip">路径规划完成 / 失败结果</span>
            </el-form-item>

            <el-form-item label="配置变更">
              <el-switch v-model="notificationStore.subscriptionPrefs.config" @change="saveNotificationPrefs" />
              <span class="text-muted form-tip">API 配置保存、环境切换</span>
            </el-form-item>

            <el-form-item label="UTM 报备">
              <el-switch v-model="notificationStore.subscriptionPrefs.utm" @change="saveNotificationPrefs" />
              <span class="text-muted form-tip">报备通过 / 驳回 / 人工审核</span>
            </el-form-item>

            <el-form-item label="系统通知">
              <el-switch v-model="notificationStore.subscriptionPrefs.system" @change="saveNotificationPrefs" />
              <span class="text-muted form-tip">系统健康检查、启动上线</span>
            </el-form-item>

            <el-divider content-position="left">桌面通知</el-divider>

            <el-form-item label="启用桌面通知">
              <el-switch v-model="notificationStore.subscriptionPrefs.desktop" @change="saveNotificationPrefs" />
              <span class="text-muted form-tip">通过浏览器推送桌面通知（需要授权后生效）</span>
            </el-form-item>

            <el-form-item label="桌面通知权限">
              <el-button type="primary" @click="requestDesktopPermission">
                <el-icon><Bell /></el-icon>
                请求桌面通知权限
              </el-button>
              <el-tag size="small" type="success" v-if="notificationPermission === 'granted'">已授权</el-tag>
              <el-tag size="small" type="info" v-else-if="notificationPermission === 'denied'">已拒绝</el-tag>
              <el-tag size="small" v-else>未授权</el-tag>
            </el-form-item>

            <el-form-item>
              <el-button @click="clearAllNotifications">清空所有通知（{{ notificationStore.notifications.length }} 条）</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 使用文档跳转 -->
        <el-card v-show="activeMenu === 'docs'" shadow="never" class="card-panel">
          <template #header>使用文档</template>
          <div class="docs-redirect">
            <el-empty description="点击下方按钮跳转到完整使用文档页面">
              <el-button type="primary" @click="goDocs">
                <el-icon><Document /></el-icon>
                打开使用文档
              </el-button>
            </el-empty>
          </div>
        </el-card>

        <!-- License 信息 -->
        <el-card v-show="activeMenu === 'license'" shadow="never" class="card-panel">
          <template #header>License 信息</template>
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
    <el-dialog v-model="pwdDialogVisible" title="修改密码" width="480px">
      <el-form
        ref="pwdFormRef"
        :model="pwdForm"
        :rules="pwdRules"
        label-width="100px"
      >
        <el-form-item label="原密码" prop="oldPwd">
          <el-input v-model="pwdForm.oldPwd" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码" prop="newPwd">
          <el-input v-model="pwdForm.newPwd" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPwd">
          <el-input v-model="pwdForm.confirmPwd" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPwd">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User, Lock, Setting, Document, Collection, SwitchButton, Bell,
  Key, Sunny, Moon, Check, HomeFilled, PartlyCloudy, Goods,
  Monitor, List, Position, Connection, DataAnalysis, Coin, Box, Tools
} from '@element-plus/icons-vue'
import { useAuthStore, PERMISSION_MATRIX } from '../../stores/auth'
import { useAppStore } from '../../stores/app'
import { useNotificationStore } from '../../stores/notification'

const router = useRouter()
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
  const keys = ['dashboard', 'weather', 'path-planning', 'cockpit', 'monitoring', 'tasks', 'orders', 'assimilation']
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
  background: #f5f7fa;
}

.settings-grid {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 16px;
  max-width: 1280px;
  margin: 0 auto;
}

.settings-nav {
  background: #ffffff;
  border-radius: 10px;
  padding: 8px 0;
  height: fit-content;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.04);
}

.nav-menu {
  border-right: none;
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
  background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
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
  color: #303133;
  margin-bottom: 6px;
}

.avatar-sub {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 13px;
}

.text-muted {
  color: #909399;
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
  color: #303133;
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
  background: #ecf5ff;
  color: #409eff;
  border: 1px solid #d9ecff;
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
  background: #1e1e1e;
  color: #dcdcdc;
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
  color: #606266;
  font-size: 13px;
  line-height: 1.9;
}
</style>
