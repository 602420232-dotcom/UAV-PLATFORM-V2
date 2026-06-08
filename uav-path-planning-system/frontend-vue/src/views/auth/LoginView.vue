<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-brand">
        <div class="brand-icon">✈</div>
        <h1 class="brand-title">无人机路径规划系统</h1>
        <p class="brand-subtitle">UAV Path Planning Platform</p>
      </div>

      <a-card class="login-card" bordered="false">
        <h2 class="login-title">账号登录</h2>

        <a-form
          :model="formState"
          layout="vertical"
          @finish="handleLogin"
          class="login-form"
        >
          <a-form-item
            name="username"
            label="用户名"
            :rules="[{ required: true, message: '请输入用户名' }]"
          >
            <a-input
              v-model:value="formState.username"
              placeholder="请输入用户名"
              size="large"
            >
              <template #prefix><UserOutlined /></template>
            </a-input>
          </a-form-item>

          <a-form-item
            name="password"
            label="密码"
            :rules="[{ required: true, message: '请输入密码' }]"
          >
            <a-input-password
              v-model:value="formState.password"
              placeholder="请输入密码"
              size="large"
            >
              <template #prefix><LockOutlined /></template>
            </a-input-password>
          </a-form-item>

          <a-form-item>
            <a-button
              type="primary"
              html-type="submit"
              size="large"
              block
              :loading="authStore.loading"
            >
              登录
            </a-button>
          </a-form-item>
        </a-form>

        <a-alert
          v-if="showDemoTip"
          class="demo-tip"
          type="info"
          show-icon
          message="提示：当前为演示模式，任意账号均可登录"
        />
      </a-card>

      <div class="login-footer">
        <span>© {{ new Date().getFullYear() }} 无人机路径规划系统</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const formState = reactive({
  username: '',
  password: ''
})

const showDemoTip = ref(false)

async function handleLogin() {
  if (!formState.username || !formState.password) {
    message.warning('请输入用户名和密码')
    return
  }
  try {
    const user = await authStore.login(formState.username, formState.password)
    if (user?.demo) {
      message.success(`欢迎回来，${user.username}（演示模式）')
    } else {
      message.success(`欢迎回来，${user.username}')
    }
    const redirect = route.query.redirect || '/dashboard'
    router.push(redirect)
  } catch (e) {
    message.error(e?.message || '登录失败')
  }
}

onMounted(() => {
  authStore.initFromStorage()
  if (authStore.isLoggedIn) {
    router.push('/dashboard')
  }
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #1677ff 0%, #0050b3 50%, #002766 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.login-container {
  width: 100%;
  max-width: 420px;
}

.login-brand {
  text-align: center;
  margin-bottom: 32px;
  color: #fff;
}

.brand-icon {
  font-size: 56px;
  line-height: 1;
  margin-bottom: 16px;
  color: #fff;
}

.brand-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px;
  color: #fff;
}

.brand-subtitle {
  font-size: 14px;
  margin: 0;
  opacity: 0.85;
}

.login-card {
  background: #fff;
  border-radius: 12px;
  padding: 32px 24px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
}

.login-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 24px;
  text-align: center;
  color: rgba(0, 0, 0, 0.88);
}

.login-form {
  margin-top: 16px;
}

.demo-tip {
  margin-top: 16px;
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
}
</style>
