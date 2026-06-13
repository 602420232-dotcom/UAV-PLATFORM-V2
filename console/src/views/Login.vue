<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref()
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不少于 6 位', trigger: 'blur' },
  ],
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.login(loginForm.username, loginForm.password)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (err) {
    // 错误已在 request.ts 拦截器中处理
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <el-icon :size="40" color="#e94560"><Promotion /></el-icon>
        <h1 class="login-title">UAV Platform</h1>
        <p class="login-subtitle">无人机气象服务平台 - 管理控制台</p>
      </div>

      <el-form
        ref="formRef"
        :model="loginForm"
        :rules="rules"
        class="login-form"
        label-position="top"
        @keyup.enter="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <span>UAV Platform v2.0</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  width: 100%;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.login-container {
  width: 400px;
  padding: 40px;
  background-color: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--color-border);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-top: 12px;
}

.login-subtitle {
  font-size: 13px;
  color: var(--color-text-muted);
  margin-top: 4px;
}

.login-form :deep(.el-form-item__label) {
  color: var(--color-text-secondary) !important;
}

.login-btn {
  width: 100%;
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  font-size: 16px;
  height: 44px;
}

.login-btn:hover {
  background-color: var(--color-primary-light);
  border-color: var(--color-primary-light);
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  color: var(--color-text-muted);
  font-size: 12px;
}
</style>
