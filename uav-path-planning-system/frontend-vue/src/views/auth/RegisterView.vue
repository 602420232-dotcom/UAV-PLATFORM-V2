<template>
  <div class="register-page">
    <div class="register-container">
      <div class="banner-side">
        <div class="banner-inner">
          <div class="banner-top">
            <div class="logo-mark">UAV</div>
            <div class="logo-text">智能路径规划系统</div>
          </div>
          <h1 class="banner-title">欢迎加入<br/>基于 WRF 气象驱动的无人机 VRP 系统</h1>
          <p class="banner-desc">
            注册账号，体验一站式无人机集群任务规划、气象分析与实时调度能力
          </p>
          <div class="banner-features">
            <div class="feature-item">
              <span class="feature-icon">✦</span>
              <span>快速注册，即刻体验</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">✦</span>
              <span>多角色权限体系</span>
            </div>
            <div class="feature-item">
              <span class="feature-icon">✦</span>
              <span>全流程可视化管理</span>
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
            <h2>创建新账号</h2>
            <p>填写以下信息完成注册</p>
          </div>

          <el-form
            ref="registerFormRef"
            :model="form"
            :rules="rules"
            label-position="top"
            class="register-form"
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
                placeholder="请输入用户名（至少 3 个字符）"
                :prefix-icon="User"
                clearable
                size="large"
              />
            </el-form-item>

            <el-form-item label="密码" prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="请输入密码（至少 6 个字符）"
                :prefix-icon="Lock"
                show-password
                size="large"
              />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="form.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                :prefix-icon="Lock"
                show-password
                size="large"
              />
            </el-form-item>

            <template v-if="!demoMode">
              <el-form-item label="邮箱" prop="email">
                <el-input
                  v-model="form.email"
                  placeholder="请输入邮箱"
                  :prefix-icon="Message"
                  clearable
                  size="large"
                />
              </el-form-item>

              <el-form-item label="验证码" prop="verifyCode">
                <div class="verify-code-wrapper">
                  <el-input
                    v-model="form.verifyCode"
                    placeholder="请输入验证码"
                    :prefix-icon="Key"
                    clearable
                    size="large"
                  />
                  <el-button
                    type="primary"
                    plain
                    size="large"
                    class="send-code-btn"
                    :disabled="codeCountdown > 0"
                    @click="handleSendCode"
                  >
                    {{ codeCountdown > 0 ? `${codeCountdown}s 后重发` : '发送验证码' }}
                  </el-button>
                </div>
              </el-form-item>
            </template>

            <el-alert
              :title="demoMode ? '当前演示模式：无需邮箱验证，注册后将自动登录' : '当前生产模式：需通过邮箱验证码完成注册'"
              :type="demoMode ? 'info' : 'success'"
              :closable="false"
              show-icon
              class="mode-tip"
            />

            <el-form-item class="submit-item">
              <el-button
                type="primary"
                size="large"
                class="submit-btn"
                :loading="authStore.loading"
                @click="handleRegister"
              >
                注册并登录
              </el-button>
            </el-form-item>

            <div class="form-footer">
              <span>已有账号？</span>
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
import { reactive, ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Message, Key } from '@element-plus/icons-vue'
import { useAuthStore, ROLES, ROLE_LABELS } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const registerFormRef = ref(null)

const demoMode = computed(() => authStore.demoMode)

const roleOptions = Object.keys(ROLES).map((key) => ({
  value: ROLES[key],
  label: ROLE_LABELS[ROLES[key]]
}))

const form = reactive({
  selectedRole: '',
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  verifyCode: ''
})

const codeCountdown = ref(0)
let countdownTimer = null

function startCountdown() {
  codeCountdown.value = 60
  countdownTimer = setInterval(() => {
    codeCountdown.value -= 1
    if (codeCountdown.value <= 0) {
      clearInterval(countdownTimer)
      countdownTimer = null
    }
  }, 1000)
}

function handleSendCode() {
  if (!form.email) {
    ElMessage.warning('请先输入邮箱')
    return
  }
  if (demoMode.value) {
    ElMessage.success('验证码已发送（演示模式：123456）')
  } else {
    ElMessage.success('验证码已发送，5 分钟内有效')
  }
  startCountdown()
}

const validateConfirm = (_rule, value, callback) => {
  if (!value) {
    callback(new Error('请再次输入密码'))
  } else if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const validateEmail = (_rule, value, callback) => {
  if (!value) {
    callback(new Error('请输入邮箱'))
    return
  }
  const emailReg = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/
  if (!emailReg.test(value)) {
    callback(new Error('邮箱格式不正确'))
  } else {
    callback()
  }
}

const rules = computed(() => {
  const base = {
    selectedRole: [{ required: true, message: '请选择用户类型', trigger: 'change' }],
    username: [
      { required: true, message: '请输入用户名', trigger: 'blur' },
      { min: 3, message: '用户名至少 3 个字符', trigger: 'blur' }
    ],
    password: [
      { required: true, message: '请输入密码', trigger: 'blur' },
      { min: 6, message: '密码至少 6 个字符', trigger: 'blur' }
    ],
    confirmPassword: [{ required: true, validator: validateConfirm, trigger: 'blur' }]
  }

  if (!demoMode.value) {
    base.email = [{ required: true, validator: validateEmail, trigger: 'blur' }]
    base.verifyCode = [
      { required: true, message: '请输入验证码', trigger: 'blur' },
      { min: 6, max: 6, message: '验证码为 6 位数字', trigger: 'blur' }
    ]
  }

  return base
})

watch(demoMode, () => {
  if (registerFormRef.value) {
    registerFormRef.value.clearValidate()
  }
})

async function handleRegister() {
  if (!registerFormRef.value) return
  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      if (demoMode.value) {
        await authStore.register(form.username, form.password, form.selectedRole)
        ElMessage.success('注册成功，正在进入系统...')
        router.push('/dashboard')
      } else {
        ElMessage.info('演示环境，真实验证功能需生产环境部署')
      }
    } catch (err) {
      ElMessage.error(err?.message || '注册失败，请稍后重试')
    }
  })
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eaf2ff 0%, #f5f8ff 50%, #eef3ff 100%);
  padding: 20px;
}

.register-container {
  width: 100%;
  max-width: 1100px;
  min-height: 620px;
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
    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.18), transparent 45%),
    radial-gradient(circle at 70% 80%, rgba(255, 255, 255, 0.12), transparent 50%);
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

.register-form :deep(.el-form-item__label) {
  font-size: 14px;
  color: #4a5a72;
  font-weight: 500;
}

.verify-code-wrapper {
  display: flex;
  gap: 10px;
  width: 100%;
}

.verify-code-wrapper :deep(.el-input) {
  flex: 1;
}

.send-code-btn {
  flex-shrink: 0;
  min-width: 140px;
}

.mode-tip {
  margin: 4px 0 4px;
}

.submit-item {
  margin-top: 20px;
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
  .register-container {
    grid-template-columns: 1fr;
    min-height: auto;
  }

  .banner-side {
    display: none;
  }

  .form-side {
    padding: 32px 20px;
  }

  .verify-code-wrapper {
    flex-direction: column;
  }

  .send-code-btn {
    width: 100%;
    min-width: auto;
  }
}
</style>
