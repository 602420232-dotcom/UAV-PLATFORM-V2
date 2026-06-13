import { get } from './request'

export interface DashboardStats {
  totalTenants: number
  totalApiKeys: number
  todayApiCalls: number
  activeTasks: number
}

export interface ApiCallTrend {
  date: string
  calls: number
}

export interface ServiceCallDistribution {
  service: string
  calls: number
  percentage: number
}

export interface ServiceHealth {
  name: string
  status: 'UP' | 'DOWN' | 'DEGRADED'
  responseTime: number
  lastCheck: string
}

export const dashboardApi = {
  /** 获取仪表盘统计 */
  getStats(): Promise<DashboardStats> {
    return get<DashboardStats>('/v1/dashboard/stats')
  },

  /** 获取近 N 天 API 调用趋势 */
  getApiCallTrend(days = 7): Promise<ApiCallTrend[]> {
    return get<ApiCallTrend[]>('/v1/dashboard/api-trend', { days })
  },

  /** 获取各服务调用占比 */
  getServiceDistribution(): Promise<ServiceCallDistribution[]> {
    return get<ServiceCallDistribution[]>('/v1/dashboard/service-distribution')
  },

  /** 获取服务健康状态 */
  getServiceHealth(): Promise<ServiceHealth[]> {
    return get<ServiceHealth[]>('/v1/dashboard/service-health')
  },
}
