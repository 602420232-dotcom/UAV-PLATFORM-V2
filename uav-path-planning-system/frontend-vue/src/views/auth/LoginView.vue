<template>
  <div class="login-page">
    <div class="login-container">
      <div class="banner-side">
        <div class="banner-inner">
          <div class="banner-top">
            <div class="logo-mark">UAV</div>
            <div class="logo-text">智能路径规划系统</div>
          </div>
          <h1 class="banner-title">基于 WRF 气象驱动的<br/>无人机 VRP 智能路径规划系统</h1>
          <p class="banner-desc">
            融合实时气象数据与智能算法，为无人机集群提供安全、高效、可靠的航线规划能力
          </p>
          <div class="banner-features">
            <div class="feature-item">
              <span class="feature-icon">☁</span>
              <span>WRF 气象驱动</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">✈</span>
              <span>VRP 智能规划</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">◎</span>
              <span>实时监控调度</span>
            </div>
          </div>
          <div class="banner-bottom">
            <span>© 2026 UAV Path Planning System</span>
          </div>
        </div>
      </div>

      <div class="form-side">
        <div class="form-card">
          <div class="form-header">
            <h2>欢迎登录</h2>
            <p>请选择用户类型并输入账号信息</p>
          </div>

          <el-form
            ref="loginFormRef"
            :model="form"
            :rules="rules"
            label-position="top"
            class="login-form"
          >
            <el-form-item label="用户类型" prop="selectedRole">
              <el-radio-group
                v-model="form.selectedRole"
                class="role-group"
              >
                <el-radio
                  v-for="role in roleOptions"
                  :key="role.value"
                  :value="role.value"
                  size="small"
                >
                  {{ role.label }}
                </el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="form.username"
                placeholder="请输入用户名"
                :prefix-icon="User"
                clearable
                size="large"
              />
            </el-form-item>

            <el-form-item label="密码" prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="请输入密码"
                :prefix-icon="Lock"
                show-password
                size="large"
              />
            </el-form-item>

            <div class="form-extra">
              <el-checkbox v-model="form.remember">记住我</el-checkbox>
              <el-link type="primary" :underline="false" @click="router.push('/forgot-password')">
                忘记密码？
              </el-link>
            </div>

            <el-form-item>
              <el-button
                type="primary"
                size="large"
                class="submit-btn"
                :loading="authStore.loading"
                @click="handleLogin"
              >
                登 录
              </el-button>
            </el-form-item>

            <div class="form-footer">
              <span>还没有账号？</span>
              <el-link type="primary" :underline="false" @click="router.push('/register')">
                注册新账号
              </el-link>
            </div>
          </el-form>

          <el-divider>
            <span class="demo-tag">当前为演示模式 · 默认账号</span>
          </el-divider>

          <div class="demo-accounts">
            <div
              v-for="acc in demoAccounts"
              :key="acc.username"
              class="demo-item"
              @click="quickFill(acc)"
            >
              <div class="demo-role">{{ acc.displayName }}</div>
              <div class="demo-creds">
                <span class="demo-label">账号:</span>
                <span class="demo-value">{{ acc.username }}</span>
                <el-divider direction="vertical" />
                <span class="demo-label">密码:</span>
                <span class="demo-value">{{ acc.password }}</span>
              </div>
              <el-icon class="demo-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, ArrowRight } from '@element-plus/icons-vue'
import { useAuthStore, ROLES, ROLE_LABELS, DEFAULT_ACCOUNTS } from '../../stores/auth'
import { logAction, AUDIT_ACTIONS } from '../../utils/audit'

const router = useRouter()
const authStore = useAuthStore()
const loginFormRef = ref(null)

const roleOptions = Object.keys(ROLES).map((key) => ({
  value: ROLES[key],
  label: ROLE_LABELS[ROLES[key]]
}))

const demoAccounts = DEFAULT_ACCOUNTS

const form = reactive({
  username: '',
  password: '',
  selectedRole: ROLES.USER,
  remember: false
})

const rules = {
  selectedRole: [{ required: true, message: '请选择用户类型', trigger: 'change' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

function quickFill(acc) {
  form.username = acc.username
  form.password = acc.password
  form.selectedRole = acc.role
}

async function handleLogin() {
  if (!loginFormRef.value) return
  await loginFormRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      await authStore.login(form.username, form.password, form.selectedRole)
      logAction({
        user: form.username,
        action: AUDIT_ACTIONS.LOGIN,
        target: 'auth/login',
        detail: `登录成功 (${form.selectedRole || 'auto'})`,
        level: 'info'
      })
      ElMessage.success('登录成功，正在进入系统...')
      router.push('/dashboard')
    } catch (err) {
      logAction({
        user: form.username,
        action: AUDIT_ACTIONS.LOGIN_FAILED,
        target: 'auth/login',
        detail: err?.message || '登录失败',
        level: 'warning'
      })
      ElMessage.error(err?.message || '登录失败，请检查用户名和密码')
    }
  })
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eaf2ff 0%, #f5f8ff 50%, #eef3ff 100%);
  padding: 20px;
}

.login-container {
  width: 100%;
  max-width: 1200px;
  min-height: 640px;
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(30, 80, 180, 0.12);
}

.banner-side {
  position: relative;
  color: #fff;
  background: linear-gradient(135deg, #1e5ac8 0%, #2a7ae0 40%, #4a90f0 100%);
  overflow: hidden;
}

.banner-side::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 20% 20%, rgba(255, 255, 255, 0.18), transparent 45%),
    radial-gradient(circle at 80% 70%, rgba(255, 255, 255, 0.12), transparent 50%),
    linear-gradient(160deg, rgba(30, 90, 200, 0.3), transparent 70%);
  pointer-events: none;
}

.banner-side::after {
  content: '';
  position: absolute;
  right: -80px;
  top: -80px;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1), transparent 70%);
  pointer-events: none;
}

.banner-inner {
  position: relative;
  z-index: 2;
  height: 100%;
  padding: 48px 48px 40px;
  display: flex;
  flex-direction: column;
}

.banner-top {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-mark {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 15px;
  letter-spacing: 1px;
}

.logo-text {
  font-size: 16px;
  font-weight: 500;
  opacity: 0.95;
}

.banner-title {
  margin-top: 60px;
  font-size: 34px;
  font-weight: 700;
  line-height: 1.4;
  letter-spacing: 0.5px;
}

.banner-desc {
  margin-top: 22px;
  font-size: 15px;
  line-height: 1.8;
  opacity: 0.9;
  max-width: 420px;
}

.banner-features {
  margin-top: 44px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 15px;
  opacity: 0.95;
}

.feature-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.22);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.banner-bottom {
  margin-top: auto;
  font-size: 13px;
  opacity: 0.75;
}

.form-side {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 48px;
  background: #fafcff;
}

.form-card {
  width: 100%;
  max-width: 440px;
}

.form-header h2 {
  margin: 0;
  font-size: 26px;
  color: #1f2d3d;
  font-weight: 600;
}

.form-header p {
  margin: 8px 0 28px;
  color: #8492a6;
  font-size: 14px;
}

.role-group {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  width: 100%;
}

.role-group :deep(.el-radio) {
  margin-right: 0;
  padding: 8px 10px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  transition: all 0.2s;
  background: #fff;
}

.role-group :deep(.el-radio:hover) {
  border-color: #409eff;
}

.role-group :deep(.el-radio.is-checked) {
  border-color: #409eff;
  background: #ecf5ff;
}

.role-group :deep(.el-radio__label) {
  font-size: 13px;
  padding-left: 6px;
}

.login-form :deep(.el-form-item__label) {
  font-size: 14px;
  color: #4a5a72;
  font-weight: 500;
}

.form-extra {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: -4px 0 16px;
}

.submit-btn {
  width: 100%;
  letter-spacing: 4px;
  font-weight: 500;
  background: linear-gradient(135deg, #2a7ae0, #4a90f0);
  border: none;
}

.submit-btn:hover {
  background: linear-gradient(135deg, #1e5ac8, #3a80e0);
}

.form-footer {
  text-align: center;
  color: #8492a6;
  font-size: 14px;
}

.demo-tag {
  color: #409eff;
  font-size: 13px;
  font-weight: 500;
}

.demo-accounts {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 220px;
  overflow-y: auto;
  padding-right: 4px;
}

.demo-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s;
}

.demo-item:hover {
  border-color: #409eff;
  background: #f5faff;
  transform: translateY(-1px);
}

.demo-role {
  font-size: 13px;
  color: #1f2d3d;
  font-weight: 500;
  min-width: 110px;
}

.demo-creds {
  flex: 1;
  font-size: 12.5px;
  color: #5a6a82;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.demo-label {
  color: #8492a6;
}

.demo-value {
  color: #2a7ae0;
  font-family: 'Consolas', monospace;
}

.demo-arrow {
  color: #c0c4cc;
  font-size: 14px;
}

@media (max-width: 960px) {
  .login-container {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .banner-side {
    display: none;
  }

  .form-side {
    padding: 32px 20px;
  }

  .role-group {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 480px) {
  .demo-role {
    min-width: 100%;
  }

  .demo-creds {
    width: 100%;
  }
}
</style>
