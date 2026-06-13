<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()

function handleLogout() {
  authStore.logout()
  router.push('/login')
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
      <el-tag v-if="authStore.currentTenantName" type="info" effect="plain" size="small">
        {{ authStore.currentTenantName }}
      </el-tag>
      <el-dropdown trigger="click">
        <span class="user-info">
          <el-icon :size="18"><User /></el-icon>
          <span class="username">{{ authStore.username || '管理员' }}</span>
          <el-icon :size="14"><ArrowDown /></el-icon>
        </span>
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
  padding: 0 20px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: color 0.2s;
}

.collapse-btn:hover {
  color: var(--color-text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: color 0.2s;
}

.user-info:hover {
  color: var(--color-text-primary);
}

.username {
  font-size: 14px;
}
</style>
