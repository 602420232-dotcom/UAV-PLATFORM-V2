import { get, post } from './request'

export interface RiskAssessment {
  id: number
  type: string
  riskLevel: string
  score: number
  factors: RiskFactor[]
  lon: number
  lat: number
  altitude: number
  assessedAt: string
  tenantId?: number
}

export interface RiskFactor {
  name: string
  value: number
  weight: number
  level: string
}

export interface AirworthinessAssessment {
  id: number
  uavType: string
  overallScore: number
  decision: string
  factors: AirworthinessFactor[]
  assessedAt: string
}

export interface AirworthinessFactor {
  name: string
  score: number
  threshold: number
  passed: boolean
}

export interface RiskQueryRequest {
  path: Array<{ lon: number; lat: number; altitude: number }>
  time: string
  uavType?: string
}

export interface AirworthinessRequest {
  uavType: string
  weatherConditions: Record<string, number>
  route: Array<{ lon: number; lat: number; altitude: number }>
}

export const riskApi = {
  /** 综合风险评估 */
  assess(data: RiskQueryRequest): Promise<RiskAssessment> {
    return post<RiskAssessment>('/v1/risk/assess', data)
  },

  /** 区域风险栅格地图 */
  getRiskMap(params: {
    minLon: number
    minLat: number
    maxLon: number
    maxLat: number
    resolution?: number
  }): Promise<RiskAssessment[]> {
    return get<RiskAssessment[]>('/v1/risk/map', params)
  },

  /** 历史风险评估记录 */
  getHistory(params?: {
    tenantId?: number
    type?: string
    limit?: number
  }): Promise<RiskAssessment[]> {
    return get<RiskAssessment[]>('/v1/risk/history', params as Record<string, unknown>)
  },

  /** 适航评估 */
  assessAirworthiness(data: AirworthinessRequest): Promise<AirworthinessAssessment> {
    return post<AirworthinessAssessment>('/v1/risk/airworthiness', data)
  },
}
