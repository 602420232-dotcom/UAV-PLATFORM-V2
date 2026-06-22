/**
 * v-permission 权限指令
 * 用于按钮级别的权限控制，无权限时自动移除 DOM 元素
 *
 * 使用示例：
 * <el-button v-permission="'write'">编辑</el-button>
 * <el-button v-permission="'delete'">删除</el-button>
 */
import { type Directive } from 'vue'
import { useAuthStore } from '@/stores/auth'

export const permission: Directive<HTMLElement, string> = {
  mounted(el, binding) {
    const authStore = useAuthStore()
    const requiredPermission = binding.value
    if (!authStore.hasPermission(requiredPermission)) {
      // 无权限时从 DOM 中移除该元素
      el.parentNode?.removeChild(el)
    }
  },
  updated(el, binding) {
    const authStore = useAuthStore()
    const requiredPermission = binding.value
    if (!authStore.hasPermission(requiredPermission)) {
      el.parentNode?.removeChild(el)
    }
  },
}
