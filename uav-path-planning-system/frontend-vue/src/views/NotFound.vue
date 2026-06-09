<template>
  <div class="notfound-page">
    <div class="notfound-card">
      <div class="notfound-icon">
        <el-icon :size="120"><Warning /></el-icon>
      </div>

      <h1 class="notfound-title">404</h1>
      <p class="notfound-subtitle">抱歉，您访问的页面不存在</p>
      <p class="notfound-desc">请检查输入的 URL 是否正确，或点击下方按钮返回首页。</p>

      <div class="notfound-actions">
        <el-button type="primary" size="large" @click="goHome">
          <el-icon><House /></el-icon>
          返回首页
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { House, Warning } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { useAppStore } from '../stores/app'

const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()

function goHome() {
  if (authStore.isLoggedIn && authStore.role) {
    router.push('/' + appStore.getDefaultRoute(authStore.role))
  } else {
    router.push('/login')
  }
}
</script>

<style scoped>
.notfound-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #fff7ed 0%, #f5f7fa 60%, #e0e7ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.notfound-card {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(245, 158, 11, 0.12);
  padding: 48px;
  max-width: 520px;
  width: 100%;
  text-align: center;
}

.notfound-icon {
  color: #f59e0b;
  margin-bottom: 8px;
}

.notfound-title {
  font-size: 80px;
  font-weight: 800;
  color: #1f2937;
  margin: 4px 0 8px;
  letter-spacing: 4px;
}

.notfound-subtitle {
  font-size: 18px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 8px;
}

.notfound-desc {
  font-size: 13px;
  color: #6b7280;
  margin: 0 0 28px;
}

.notfound-actions {
  display: flex;
  justify-content: center;
}
</style>
