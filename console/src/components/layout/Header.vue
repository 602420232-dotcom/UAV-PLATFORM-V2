<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { useDemoModeStore } from '@/stores/demoMode'
import { UserRole } from '@/utils/roles'

const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()
const demoModeStore = useDemoModeStore()

/** 当前用户是否可以操作演示模式开关（仅 SUPER_ADMIN / TENANT_ADMIN） */
const canToggleDemoMode = computed(() => {
  const role = authStore.currentRole
  return role === UserRole.SUPER_ADMIN || role === UserRole.TENANT_ADMIN
})

onMounted(() => {
  demoModeStore.fetchStatus()
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}

function handleModuleSwitch(path: string) {
  router.push(path)
}

async function handleDemoModeChange(val: boolean) {
  try {
    await ElMessageBox.confirm(
      val ? '切换到演示模式后，空数据页面将展示模拟数据用于演示。确定开启？' : '确定关闭演示模式？关闭后将恢复使用真实数据。',
      '切换演示模式',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    await demoModeStore.toggle(val)
  } catch {
    // 用户取消，不做任何操作
  }
}
</script>

<template>
  <el-header class="app-header">
    <div class="header-left">
      <el-icon
        class="collapse-btn"
        :size="20"
        @click="appStore.toggleSidebar()"
      >
        <Fold v-if="!appStore.sidebarCollapsed" />
        <Expand v-else />
      </el-icon>
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item v-if="$route.meta.title">
          {{ $route.meta.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <div class="header-right">
      <!-- 模块切换 -->
      <el-dropdown trigger="click" @command="handleModuleSwitch">
        <el-button size="small" type="primary" plain class="module-switch-btn">
          <el-icon><Switch /></el-icon>
          <span class="btn-text">切换模块</span>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="/dashboard">
              <el-icon><Odometer /></el-icon> 综合仪表盘
            </el-dropdown-item>
            <el-dropdown-item command="/research/sandbox">
              <el-icon><Flask /></el-icon> 科研平台
            </el-dropdown-item>
            <el-dropdown-item command="/api-ops/dashboard">
              <el-icon><Connection /></el-icon> API运营
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <!-- 环境状态指示器 -->
      <el-tag
        :type="appStore.environment === 'prod' ? 'danger' : appStore.environment === 'staging' ? 'warning' : 'info'"
        effect="dark"
        size="small"
      >
        <el-icon><Monitor /></el-icon>
        {{ appStore.environmentLabel }}
      </el-tag>

      <!-- 演示模式切换 -->
      <div class="demo-mode-switch">
        <span class="demo-mode-label">演示模式</span>
        <el-switch
          v-model="demoModeStore.isDemoMode"
          :loading="demoModeStore.loading"
          :disabled="!canToggleDemoMode"
          inline-prompt
          active-text="开"
          inactive-text="关"
          @change="handleDemoModeChange"
        />
      </div>

      <el-tag v-if="authStore.currentTenantName" type="info" effect="plain" size="small">
        {{ authStore.currentTenantName }}
      </el-tag>
      <el-dropdown trigger="click">
        <div class="user-info">
          <div class="user-avatar">
            <el-icon :size="16"><User /></el-icon>
          </div>
          <span class="username">{{ authStore.username || '管理员' }}</span>
          <el-icon :size="12" class="arrow-icon"><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item disabled>
              <el-icon><User /></el-icon>
              {{ authStore.username || '管理员' }}
            </el-dropdown-item>
            <el-dropdown-item divided @click="handleLogout">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>

<style scoped>
.app-header {
  height: var(--header-height);
  background-color: var(--color-sidebar);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
  box-shadow: 0 1px 8px rgba(0, 0, 0, 0.15);
  position: relative;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all 0.25s ease;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm, 6px);
}

.collapse-btn:hover {
  color: var(--color-text-primary);
  background-color: rgba(255, 255, 255, 0.06);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 模块切换按钮 */
.module-switch-btn {
  border-radius: var(--radius-sm, 6px);
  font-size: 13px;
}

.module-switch-btn .btn-text {
  margin-left: 4px;
}

/* 用户信息区域 */
.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px 4px 4px;
  border-radius: var(--radius-md, 8px);
  transition: all 0.25s ease;
}

.user-info:hover {
  background-color: rgba(255, 255, 255, 0.06);
}

/* 用户头像圆圈 */
.user-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--color-primary, #0f3460), var(--color-primary-light, #1a4a7a));
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-primary);
  border: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
}

.username {
  font-size: 13px;
  color: var(--color-text-secondary);
  transition: color 0.25s ease;
}

.user-info:hover .username {
  color: var(--color-text-primary);
}

.arrow-icon {
  color: var(--color-text-muted);
  transition: transform 0.25s ease, color 0.25s ease;
}

.user-info:hover .arrow-icon {
  color: var(--color-text-secondary);
}

/* 演示模式切换 */
.demo-mode-switch {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-radius: var(--radius-sm, 6px);
  transition: background-color 0.25s ease;
}

.demo-mode-switch:hover {
  background-color: rgba(255, 255, 255, 0.04);
}

.demo-mode-label {
  font-size: 12px;
  color: var(--color-text-muted);
  white-space: nowrap;
}

/* 环境标签美化 */
.header-right :deep(.el-tag) {
  border-radius: var(--radius-sm, 6px);
  font-size: 12px;
  letter-spacing: 0.02em;
}
</style>
