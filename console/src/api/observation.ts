import { get, post } from './request'

export interface ObservationTask {
  id: number
  type: string
  status: string
  priority: number
  region: {
    minLon: number
    minLat: number
    maxLon: number
    maxLat: number
  }
  targetVariables: string[]
  platform: string
  createdAt: string
  completedAt: string | null
}

export interface ObservationDecision {
  id: number
  taskId: number
  decision: string
  reason: string
  suggestedPlatforms: string[]
  suggestedTime: string
  coverageScore: number
  createdAt: string
}

export interface CreateObservationRequest {
  type: string
  priority: number
  region: {
    minLon: number
    minLat: number
    maxLon: number
    maxLat: number
  }
  targetVariables: string[]
  platform?: string
  timeWindow?: {
    start: string
    end: string
  }
}

export interface ObservationDecisionRequest {
  region: {
    minLon: number
    minLat: number
    maxLon: number
    maxLat: number
  }
  targetVariables: string[]
  timeWindow?: {
    start: string
    end: string
  }
}

export const observationApi = {
  /** 创建观测任务 */
  createTask(data: CreateObservationRequest): Promise<ObservationTask> {
    return post<ObservationTask>('/v1/observation/tasks', data)
  },

  /** 获取观测任务详情 */
  getTask(id: number): Promise<ObservationTask> {
    return get<ObservationTask>(`/v1/observation/tasks/${id}`)
  },

  /** 列出所有观测任务 */
  listTasks(): Promise<ObservationTask[]> {
    return get<ObservationTask[]>('/v1/observation/tasks')
  },

  /** 更新任务状态 */
  updateTaskStatus(id: number, status: string): Promise<ObservationTask> {
    return post<ObservationTask>(`/v1/observation/tasks/${id}/status`, { status })
  },

  /** 获取观测决策建议 */
  getDecision(data: ObservationDecisionRequest): Promise<ObservationDecision> {
    return post<ObservationDecision>('/v1/observation/decisions', data)
  },
}
