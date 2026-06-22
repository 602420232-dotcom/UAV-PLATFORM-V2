import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface ServiceStatus {
  name: string
  status: 'UP' | 'DOWN' | 'DEGRADED'
  responseTime?: number
  lastCheck?: string
}

export type EnvironmentType = 'dev' | 'test' | 'staging' | 'prod'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const loading = ref(false)
  const serviceStatuses = ref<ServiceStatus[]>([])
  const environment = ref<EnvironmentType>('dev')

  const environmentLabel = computed(() => {
    const labels: Record<EnvironmentType, string> = {
      dev: '开发环境',
      test: '测试环境',
      staging: '灰度环境',
      prod: '生产环境'
    }
    return labels[environment.value]
  })

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function setLoading(value: boolean) {
    loading.value = value
  }

  function setServiceStatuses(statuses: ServiceStatus[]) {
    serviceStatuses.value = statuses
  }

  function setEnvironment(env: EnvironmentType) {
    environment.value = env
    localStorage.setItem('uav-environment', env)
  }

  function loadEnvironment() {
    const saved = localStorage.getItem('uav-environment') as EnvironmentType
    if (saved && ['dev', 'test', 'staging', 'prod'].includes(saved)) {
      environment.value = saved
    }
  }

  return {
    sidebarCollapsed,
    loading,
    serviceStatuses,
    environment,
    environmentLabel,
    toggleSidebar,
    setLoading,
    setServiceStatuses,
    setEnvironment,
    loadEnvironment,
  }
})
