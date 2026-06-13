import { get, post } from './request'

export interface AssimilationTask {
  id: number
  type: string
  status: string
  algorithm: string
  createdAt: string
  completedAt: string | null
  errorMessage: string | null
}

export interface AssimilationResult {
  taskId: number
  analysisTime: string
  variables: string[]
  gridInfo: {
    minLon: number
    minLat: number
    maxLon: number
    maxLat: number
    resolution: number
    levels: number
  }
  dataUrl: string
}

export interface SubmitTaskRequest {
  type: string
  algorithm: string
  startTime: string
  endTime: string
  region?: {
    minLon: number
    minLat: number
    maxLon: number
    maxLat: number
  }
  observationSources?: string[]
}

export interface TaskQueryRequest {
  status?: string
  type?: string
  page?: number
  size?: number
}

export const assimilationApi = {
  /** 提交同化任务 */
  submitTask(data: SubmitTaskRequest): Promise<number> {
    return post<number>('/v1/assimilation/tasks', data)
  },

  /** 查询任务状态 */
  getTaskStatus(id: number): Promise<AssimilationTask> {
    return get<AssimilationTask>(`/v1/assimilation/tasks/${id}`)
  },

  /** 查询任务结果 */
  getTaskResult(id: number): Promise<AssimilationResult> {
    return get<AssimilationResult>(`/v1/assimilation/tasks/${id}/result`)
  },

  /** 查询任务列表 */
  listTasks(params?: TaskQueryRequest): Promise<unknown> {
    return get('/v1/assimilation/tasks', params as Record<string, unknown>)
  },

  /** 取消任务 */
  cancelTask(id: number): Promise<void> {
    return post<void>(`/v1/assimilation/tasks/${id}/cancel`)
  },
}
