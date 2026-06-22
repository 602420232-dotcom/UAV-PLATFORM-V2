<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'
import { ElButton, ElResult, ElText } from 'element-plus'

interface Props {
  /** 错误回退时显示的提示文本 */
  fallback?: string
}

withDefaults(defineProps<Props>(), {
  fallback: '组件加载失败',
})

/** 是否处于错误状态 */
const hasError = ref<boolean>(false)

/** 捕获到的错误信息 */
const errorMessage = ref<string>('')

/** 捕获到的错误堆栈 */
const errorStack = ref<string>('')

/**
 * 捕获子组件生命周期钩子中的错误
 */
onErrorCaptured((err: Error, instance, info: string) => {
  hasError.value = true
  errorMessage.value = err.message || String(err)
  errorStack.value = err.stack || ''

  // 阻止错误继续向上传播
  console.error('[ErrorBoundary] 捕获到组件错误:', err)
  console.error('[ErrorBoundary] 错误来源:', info)
  console.error('[ErrorBoundary] 组件实例:', instance)

  return false
})

/**
 * 重试：清除错误状态，重新渲染子组件
 */
function handleRetry(): void {
  hasError.value = false
  errorMessage.value = ''
  errorStack.value = ''
}

/**
 * 复制错误信息到剪贴板，便于开发者调试
 */
async function handleCopyError(): Promise<void> {
  try {
    const text = `Error: ${errorMessage.value}\n\nStack:\n${errorStack.value}`
    await navigator.clipboard.writeText(text)
    ElMessage.success('错误信息已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}
</script>

<template>
  <div v-if="hasError" class="error-boundary">
    <div class="error-boundary__container">
      <ElResult icon="error" :title="fallback" sub-title="子组件渲染过程中发生了错误">
        <template #extra>
          <div class="error-boundary__actions">
            <ElButton type="primary" @click="handleRetry">
              <el-icon><RefreshRight /></el-icon>
              重试
            </ElButton>
            <ElButton type="info" plain @click="handleCopyError">
              <el-icon><CopyDocument /></el-icon>
              复制错误
            </ElButton>
          </div>
        </template>
      </ElResult>

      <!-- 错误详情折叠区域 -->
      <div class="error-boundary__detail">
        <el-collapse>
          <el-collapse-item title="查看错误详情">
            <ElText type="danger" tag="p" class="error-boundary__message">
              {{ errorMessage }}
            </ElText>
            <pre v-if="errorStack" class="error-boundary__stack">{{ errorStack }}</pre>
          </el-collapse-item>
        </el-collapse>
      </div>
    </div>
  </div>

  <!-- 正常状态：渲染子组件 -->
  <slot v-else />
</template>

<script lang="ts">
import { RefreshRight, CopyDocument } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

export default {
  components: { RefreshRight, CopyDocument },
}
</script>

<style scoped>
.error-boundary {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  padding: 24px;
}

.error-boundary__container {
  max-width: 600px;
  width: 100%;
  text-align: center;
}

.error-boundary__actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 8px;
}

.error-boundary__detail {
  margin-top: 16px;
  text-align: left;
}

.error-boundary__message {
  word-break: break-word;
  margin-bottom: 8px;
}

.error-boundary__stack {
  max-height: 200px;
  overflow: auto;
  padding: 12px;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--el-text-color-secondary);
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
