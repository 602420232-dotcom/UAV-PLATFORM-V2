import { get, post } from './request'

export interface Airspace {
  id: number
  name: string
  type: string
  status: string
  minAltitude: number
  maxAltitude: number
  geometry: unknown
  restrictions: string[]
  createdAt: string
}

export interface FlightPlan {
  id: number
  uavId: string
  status: string
  waypoints: FlightWaypoint[]
  submittedAt: string
  approvedAt: string | null
}

export interface FlightWaypoint {
  lon: number
  lat: number
  altitude: number
  speed: number
  timestamp: string
}

export interface UavPosition {
  uavId: string
  lon: number
  lat: number
  altitude: number
  heading: number
  speed: number
  timestamp: string
}

export interface ConflictAlert {
  id: number
  type: string
  severity: string
  status: string
  uavId1: string
  uavId2: string
  location: { lon: number; lat: number; altitude: number }
  timeToConflict: number
  createdAt: string
}

export interface SubmitFlightPlanRequest {
  uavId: string
  waypoints: Array<{
    lon: number
    lat: number
    altitude: number
    speed?: number
  }>
  estimatedDepartureTime: string
}

export interface ConflictCheckRequest {
  plannedPath: Array<{
    lon: number
    lat: number
    altitude: number
    timestamp: string
  }>
  timeWindow: {
    start: string
    end: string
  }
}

export const utmApi = {
  /** 获取空域列表 */
  listAirspaces(): Promise<Airspace[]> {
    return get<Airspace[]>('/v1/airspaces')
  },

  /** 创建动态空域 */
  createAirspace(data: Partial<Airspace>): Promise<Airspace> {
    return post<Airspace>('/v1/airspaces', data)
  },

  /** 检查空域限制 */
  checkRestriction(lon: number, lat: number, altitude: number): Promise<boolean> {
    return get<boolean>('/v1/airspaces/check', { lon, lat, altitude })
  },

  /** 提交飞行计划 */
  submitFlightPlan(data: SubmitFlightPlanRequest): Promise<FlightPlan> {
    return post<FlightPlan>('/v1/flight-plans', data)
  },

  /** 获取飞行计划列表 */
  listFlightPlans(): Promise<FlightPlan[]> {
    return get<FlightPlan[]>('/v1/flight-plans')
  },

  /** 冲突检测 */
  checkConflict(data: ConflictCheckRequest): Promise<ConflictAlert[]> {
    return post<ConflictAlert[]>('/v1/flight-plans/conflict-check', data)
  },

  /** 获取冲突告警列表 */
  listConflictAlerts(): Promise<ConflictAlert[]> {
    return get<ConflictAlert[]>('/v1/conflict-alerts')
  },
}
