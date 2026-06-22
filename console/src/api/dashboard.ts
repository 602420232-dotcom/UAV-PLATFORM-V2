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

/** 全局极简 KPI（首页用） */
export interface GlobalStats {
  totalTenants: number
  activeApiKeys: number
  todayApiCalls: number
  runningExperiments: number
}

/** API 运营聚合数据 */
export interface ApiOpsDashboard {
  stats: {
    totalApiKeys: number
    todayApiCalls: number
    todayFailedRequests: number
    peakCalls7d: number
    activeServices: number
  }
  apiTrend: ApiCallTrend[]
  serviceDistribution: ServiceCallDistribution[]
  serviceHealth: ServiceHealth[]
}

/** 科研实验统计数据 */
export interface ResearchDashboard {
  stats: {
    running: number
    completed: number
    failed: number
    total: number
    fiveDVarExecutions: number
  }
  recentExperiments: {
    id: number
    experimentName: string
    algorithmName: string
    algorithmCategory: string
    status: string
    createdAt: string
  }[]
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

  /** 全局极简 KPI（首页用） */
  getGlobalStats(): Promise<GlobalStats> {
    return get<GlobalStats>('/v1/dashboard/global')
  },

  /** API 运营聚合数据 */
  getApiOpsDashboard(): Promise<ApiOpsDashboard> {
    return get<ApiOpsDashboard>('/v1/dashboard/api-ops')
  },

  /** 科研实验统计数据 */
  getResearchDashboard(): Promise<ResearchDashboard> {
    return get<ResearchDashboard>('/v1/dashboard/research')
  },
}
