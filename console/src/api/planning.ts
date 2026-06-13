import { get, post } from './request'

export interface PlanningTask {
  id: number
  type: string
  status: string
  createdAt: string
  completedAt: string | null
  errorMessage: string | null
}

export interface PathResult {
  taskId: number
  waypoints: Waypoint[]
  totalDistance: number
  estimatedTime: number
  fuelConsumption: number
}

export interface Waypoint {
  lon: number
  lat: number
  altitude: number
  speed: number
  timestamp: string
}

export interface MissionPlan {
  taskId: number
  segments: MissionSegment[]
  totalDistance: number
  estimatedDuration: number
}

export interface MissionSegment {
  startPoint: Waypoint
  endPoint: Waypoint
  altitude: number
  speed: number
  distance: number
}

export interface PlanPathRequest {
  startPoint: { lon: number; lat: number; altitude: number }
  endPoint: { lon: number; lat: number; altitude: number }
  waypoints?: Array<{ lon: number; lat: number; altitude: number }>
  algorithm?: string
}

export interface PlanMissionRequest {
  area: {
    minLon: number
    minLat: number
    maxLon: number
    maxLat: number
  }
  altitude: number
  overlap: number
  algorithm?: string
}

export const planningApi = {
  /** 提交路径规划任务 */
  planPath(data: PlanPathRequest): Promise<PlanningTask> {
    return post<PlanningTask>('/v1/planning/path', data)
  },

  /** 提交任务规划 */
  planMission(data: PlanMissionRequest): Promise<PlanningTask> {
    return post<PlanningTask>('/v1/planning/mission', data)
  },

  /** 获取任务状态 */
  getTask(id: number): Promise<PlanningTask> {
    return get<PlanningTask>(`/v1/planning/tasks/${id}`)
  },

  /** 获取路径规划结果 */
  getPathResult(id: number): Promise<PathResult> {
    return get<PathResult>(`/v1/planning/tasks/${id}/result`)
  },

  /** 获取任务规划结果 */
  getMissionPlan(id: number): Promise<MissionPlan> {
    return get<MissionPlan>(`/v1/planning/tasks/${id}/mission`)
  },

  /** 列出所有任务 */
  listTasks(): Promise<PlanningTask[]> {
    return get<PlanningTask[]>('/v1/planning/tasks')
  },

  /** 取消任务 */
  cancelTask(id: number): Promise<void> {
    return post<void>(`/v1/planning/tasks/${id}/cancel`)
  },
}
