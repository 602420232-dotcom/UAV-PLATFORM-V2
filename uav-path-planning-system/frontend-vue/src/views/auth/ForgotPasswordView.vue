<template>
  <div class="reset-page">
    <div class="reset-container">
      <div class="banner-side">
        <div class="banner-inner">
          <div class="banner-top">
            <div class="logo-mark">UAV</div>
            <div class="logo-text">智能路径规划系统</div>
          </div>
          <h1 class="banner-title">重置您的密码<br/>安全守护您的账号</h1>
          <p class="banner-desc">
            通过用户类型和用户名快速重置密码，请设置一个您不会忘记、但他人难以猜测的新密码
          </p>
          <div class="banner-features">
            <div class="feature-item">
              <span class="feature-icon">◈</span>
              <span>安全加密存储</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">◈</span>
              <span>快速自助重置</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">◈</span>
              <span>多角色权限管理</span>
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
            <h2>重置密码</h2>
            <p>选择用户类型并填写用户名与新密码</p>
          </div>

          <el-form
            ref="resetFormRef"
            :model="form"
            :rules="rules"
            label-position="top"
            class="reset-form"
          >
            <el-form-item label="用户类型" prop="selectedRole">
              <el-select
                v-model="form.selectedRole"
                placeholder="请选择用户类型"
                size="large"
              >
                <el-option
                  v-for="role in roleOptions"
                  :key="role.value"
                  :label="role.label"
                  :value="role.value"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="form.username"
                placeholder="请输入注册时的用户名"
                :prefix-icon="User"
                clearable
                size="large"
              />
            </el-form-item>

            <el-form-item label="新密码" prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="请输入新密码（至少 6 个字符）"
                :prefix-icon="Lock"
                show-password
                size="large"
              />
            </el-form-item>

            <el-form-item label="确认新密码" prop="confirmPassword">
              <el-input
                v-model="form.confirmPassword"
                type="password"
                placeholder="请再次输入新密码"
                :prefix-icon="Lock"
                show-password
                size="large"
              />
            </el-form-item>

            <el-form-item class="submit-item">
              <el-button
                type="primary"
                size="large"
                class="submit-btn"
                :loading="authStore.loading"
                @click="handleReset"
              >
                重置密码
              </el-button>
            </el-form-item>

            <div class="form-footer">
              <span>想起密码了？</span>
              <el-link type="primary" :underline="false" @click="router.push('/login')">
                返回登录
              </el-link>
            </div>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore, ROLES, ROLE_LABELS } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const resetFormRef = ref(null)

const roleOptions = Object.keys(ROLES).map((key) => ({
  value: ROLES[key],
  label: ROLE_LABELS[ROLES[key]]
}))

const form = reactive({
  selectedRole: '',
  username: '',
  password: '',
  confirmPassword: ''
})

const validateConfirm = (_rule, value, callback) => {
  if (!value) {
    callback(new Error('请再次输入新密码'))
  } else if (value !== form.password) {
    callback(new Error('两次输入的新密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  selectedRole: [{ required: true, message: '请选择用户类型', trigger: 'change' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码至少 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [{ required: true, validator: validateConfirm, trigger: 'blur' }]
}

async function handleReset() {
  if (!resetFormRef.value) return
  await resetFormRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      await authStore.resetPassword(form.username, form.selectedRole, form.password)
      ElMessage.success('密码已重置，请使用新密码登录')
      setTimeout(() => {
        router.push('/login')
      }, 800)
    } catch (err) {
      ElMessage.error(err?.message || '重置密码失败，请稍后重试')
    }
  })
}
</script>

<style scoped>
.reset-page {
  min-height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eaf2ff 0%, #f5f8ff 50%, #eef3ff 100%);
  padding: 20px;
}

.reset-container {
  width: 100%;
  max-width: 1050px;
  min-height: 600px;
  display: grid;
  grid-template-columns: 1fr 1.1fr;
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
    radial-gradient(circle at 25% 35%, rgba(255, 255, 255, 0.18), transparent 45%),
    radial-gradient(circle at 75% 75%, rgba(255, 255, 255, 0.12), transparent 50%);
  pointer-events: none;
}

.banner-inner {
  position: relative;
  z-index: 2;
  height: 100%;
  padding: 48px 44px 40px;
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
  font-size: 30px;
  font-weight: 700;
  line-height: 1.45;
}

.banner-desc {
  margin-top: 22px;
  font-size: 14.5px;
  line-height: 1.8;
  opacity: 0.9;
  max-width: 380px;
}

.banner-features {
  margin-top: 40px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14.5px;
  opacity: 0.95;
}

.feature-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.22);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
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
  max-width: 420px;
}

.form-header h2 {
  margin: 0;
  font-size: 26px;
  color: #1f2d3d;
  font-weight: 600;
}

.form-header p {
  margin: 8px 0 24px;
  color: #8492a6;
  font-size: 14px;
}

.reset-form :deep(.el-form-item__label) {
  font-size: 14px;
  color: #4a5a72;
  font-weight: 500;
}

.submit-item {
  margin-top: 16px;
}

.submit-btn {
  width: 100%;
  letter-spacing: 2px;
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

@media (max-width: 960px) {
  .reset-container {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .banner-side {
    display: none;
  }

  .form-side {
    padding: 32px 20px;
  }
}
</style>
