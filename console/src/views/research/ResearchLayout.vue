<template>
  <div class="research-layout">
    <el-container>
      <!-- 左侧菜单 -->
      <el-aside width="220px" class="research-sidebar">
        <div class="sidebar-header">
          <el-icon size="24"><Flask /></el-icon>
          <span class="title">科研平台</span>
        </div>

        <el-menu
          :default-active="activeMenu"
          router
          class="research-menu"
          background-color="transparent"
          text-color="var(--color-text)"
          active-text-color="var(--color-primary)"
        >
          <el-menu-item index="/research/sandbox">
            <el-icon><Monitor /></el-icon>
            <span>科研沙箱</span>
          </el-menu-item>
          
          <el-menu-item index="/research/algorithm-lab">
            <el-icon><Cpu /></el-icon>
            <span>算法实验室</span>
          </el-menu-item>
          
          <el-menu-item index="/research/experiments">
            <el-icon><List /></el-icon>
            <span>实验管理</span>
          </el-menu-item>
          
          <el-menu-item index="/research/reports">
            <el-icon><Document /></el-icon>
            <span>报告中心</span>
          </el-menu-item>
          
          <el-sub-menu index="/research/wrf">
            <template #title>
              <el-icon><MapLocation /></el-icon>
              <span>WRF分析</span>
            </template>
            <el-menu-item index="/research/wrf-analysis">地形分析</el-menu-item>
            <el-menu-item index="/research/pbl-analysis">边界层分析</el-menu-item>
            <el-menu-item index="/research/cu-analysis">积云参数化</el-menu-item>
          </el-sub-menu>
        </el-menu>
        
        <!-- 环境状态 -->
        <div class="env-info">
          <el-divider />
          <div class="env-tags">
            <el-tag size="small" :type="dataSourceStatus.type" effect="plain">
              数据源: {{ dataSourceStatus.label }}
            </el-tag>
          </div>
        </div>
      </el-aside>
      
      <!-- 主内容区 -->
      <el-main class="research-main">
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
import { useAppStore } from '@/stores/app'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const activeMenu = computed(() => route.path)

function goToConsole() {
  router.push('/dashboard')
}

const dataSourceStatus = computed(() => {
  const isReal = appStore.environment !== 'dev'
  return {
    type: isReal ? 'success' : 'info',
    label: isReal ? '真实数据' : '模拟数据'
  }
})
</script>

<style scoped>
.research-layout {
  height: 100vh;
}

.research-sidebar {
  background: var(--color-bg-secondary);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
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

.research-menu {
  flex: 1;
  border-right: none;
}

.env-info {
  padding: 12px;
}

.env-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.research-main {
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
