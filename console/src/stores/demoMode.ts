import { defineStore } from 'pinia'
import { ref } from 'vue'
import { systemConfigApi } from '@/api/systemConfig'

export const useDemoModeStore = defineStore('demoMode', () => {
  const isDemoMode = ref(false)
  const loading = ref(false)

  async function fetchStatus() {
    try {
      const data = await systemConfigApi.getDemoMode()
      isDemoMode.value = data.demoMode
    } catch {
      isDemoMode.value = false
    }
  }

  async function toggle(enabled: boolean) {
    loading.value = true
    try {
      await systemConfigApi.setDemoMode(enabled)
      isDemoMode.value = enabled
    } finally {
      loading.value = false
    }
  }

  return { isDemoMode, loading, fetchStatus, toggle }
})
