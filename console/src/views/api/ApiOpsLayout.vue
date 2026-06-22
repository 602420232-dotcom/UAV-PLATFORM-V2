<template>
  <div class="api-ops-layout">
    <el-container>
      <!-- 左侧菜单 -->
      <el-aside width="220px" class="api-sidebar">
        <div class="sidebar-header">
          <el-icon size="24"><Connection /></el-icon>
          <span class="title">API运营</span>
        </div>

        <el-menu
          :default-active="activeMenu"
          router
          class="api-menu"
          background-color="transparent"
          text-color="var(--color-text)"
          active-text-color="var(--color-primary)"
        >
          <el-menu-item index="/api-ops/dashboard">
            <el-icon><Odometer /></el-icon>
            <span>运营仪表盘</span>
          </el-menu-item>
          
          <el-menu-item index="/api-ops/api-keys">
            <el-icon><Key /></el-icon>
            <span>API密钥管理</span>
          </el-menu-item>
          
          <el-menu-item index="/api-ops/tenants">
            <el-icon><OfficeBuilding /></el-icon>
            <span>租户管理</span>
          </el-menu-item>
          
          <el-menu-item index="/api-ops/usage">
            <el-icon><TrendCharts /></el-icon>
            <span>用量分析</span>
          </el-menu-item>
          
          <el-menu-item index="/api-ops/health">
            <el-icon><FirstAidKit /></el-icon>
            <span>服务健康</span>
          </el-menu-item>
          
          <el-menu-item index="/api-ops/alerts">
            <el-icon><Bell /></el-icon>
            <span>告警规则</span>
          </el-menu-item>

          <el-menu-item index="/api-ops/utm-env">
            <el-icon><Monitor /></el-icon>
            <span>UTM环境配置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <!-- 主内容区 -->
      <el-main class="api-main">
        <!-- 返回控制台 -->
        <div class="back-to-console">
          <el-button
            class="back-btn"
            @click="goToConsole"
          >
            <el-icon class="back-icon"><ArrowLeft /></el-icon>
            返回控制台
          </el-button>
        </div>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const activeMenu = computed(() => route.path)

function goToConsole() {
  router.push('/dashboard')
}
</script>

<style scoped>
.api-ops-layout {
  height: 100vh;
}

.api-sidebar {
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border);
}

.sidebar-header {
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid var(--color-border);
}

.sidebar-header .title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-primary);
}

.api-menu {
  border-right: none;
}

.api-main {
  background: var(--color-bg);
  padding: 20px;
  overflow-y: auto;
  position: relative;
}

.back-to-console {
  position: absolute;
  top: 16px;
  right: 20px;
  z-index: 100;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: 10px;
  border: 2px solid #0f3460;
  background: #1a1a2e;
  color: #e0e0e0;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.back-btn:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(233, 69, 96, 0.35);
  border-color: #e94560;
  color: #e94560;
  background: #1a1a2e;
}

.back-icon {
  font-size: 16px;
  transition: transform 0.3s ease;
}

.back-btn:hover .back-icon {
  transform: translateX(-3px);
}
</style>
