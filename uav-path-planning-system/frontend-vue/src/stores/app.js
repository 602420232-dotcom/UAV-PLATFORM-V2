import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  const collapsed = ref(false)
  const theme = ref('light') // 'light' | 'dark'

  const isDark = computed(() => theme.value === 'dark')

  function toggleCollapse() {
    collapsed.value = !collapsed.value
  }

  function setCollapsed(value) {
    collapsed.value = !!value
  }

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  return {
    collapsed,
    theme,
    isDark,
    toggleCollapse,
    setCollapsed,
    toggleTheme
  }
})
