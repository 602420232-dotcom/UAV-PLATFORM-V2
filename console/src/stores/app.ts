import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ServiceStatus {
  name: string
  status: 'UP' | 'DOWN' | 'DEGRADED'
  responseTime?: number
  lastCheck?: string
}

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const loading = ref(false)
  const serviceStatuses = ref<ServiceStatus[]>([])

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setLoading(value: boolean) {
    loading.value = value
  }

  function setServiceStatuses(statuses: ServiceStatus[]) {
    serviceStatuses.value = statuses
  }

  return {
    sidebarCollapsed,
    loading,
    serviceStatuses,
    toggleSidebar,
    setLoading,
    setServiceStatuses,
  }
})
