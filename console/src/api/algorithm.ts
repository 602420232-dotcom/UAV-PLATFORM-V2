import { get, post } from './request'

export interface Algorithm {
  id: number
  name: string
  category: string
  version: string
  status: string
  description: string
  registeredAt: string
  lastRunAt: string | null
  runCount: number
  config: string | null
}

export interface AlgorithmListParams {
  category?: string
  keyword?: string
  page?: number
  size?: number
}

export interface AlgorithmListResult {
  records: Algorithm[]
  total: number
  size: number
  current: number
  pages: number
}

export interface AlgorithmCategoryStats {
  total: number
  assimilation: number
  planning: number
  model_engine: number
  edge: number
  risk: number
  observation: number
}

export interface AlgorithmExecuteParams {
  params?: Record<string, unknown>
}

export interface AlgorithmExecuteResult {
  success: boolean
  executionTime: string
  output: Record<string, unknown>
}

export const algorithmApi = {
  /** 获取算法列表（分页） */
  list(params?: AlgorithmListParams): Promise<AlgorithmListResult> {
    return get<AlgorithmListResult>('/v1/algorithms/list', params as Record<string, unknown>)
  },

  /** 获取算法详情 */
  getDetail(id: number): Promise<Algorithm> {
    return get<Algorithm>(`/v1/algorithms/${id}`)
  },

  /** 获取算法分类统计 */
  getCategoryStats(): Promise<AlgorithmCategoryStats> {
    return get<AlgorithmCategoryStats>('/v1/algorithms/stats')
  },

  /** 执行算法 */
  execute(id: number, data?: AlgorithmExecuteParams): Promise<AlgorithmExecuteResult> {
    return post<AlgorithmExecuteResult>(`/v1/algorithms/${id}/execute`, data)
  },

  /** 获取指定分类的算法列表（用于路径规划算法选择） */
  listByCategory(category: string): Promise<Algorithm[]> {
    return get<Algorithm[]>('/v1/algorithms/list', { category, size: 200 })
  },
}
