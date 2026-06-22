import { get, post, put } from './request'

export interface Algorithm {
  id: number
  name: string
  category: string
  version: string
  status: string | number
  description: string
  registeredAt: string
  lastRunAt: string | null
  runCount: number
  config: string | null
  type: string
  endpoint: string
  paramSchema: string | null
  createdAt: string
  updatedAt: string
}

export interface AlgorithmListParams {
  category?: string
  keyword?: string
  algorithmType?: string
  algorithmLevel?: string
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
  weather: number
  fusion: number
  generic: number
  [key: string]: number
}

export interface AlgorithmExecuteParams {
  params?: Record<string, unknown>
}

export interface AlgorithmExecuteResult {
  success: boolean
  executionTime: string
  output: Record<string, unknown>
  algorithmName?: string
  algorithmVersion?: string
  error?: string
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

  /** 获取算法分类统计（registry端点） */
  getRegistryStats(): Promise<AlgorithmCategoryStats> {
    return get<AlgorithmCategoryStats>('/v1/algorithms/registry/stats')
  },

  /** 按分类查询算法列表（registry端点） */
  listByCategory(category: string): Promise<Algorithm[]> {
    return get<Algorithm[]>(`/v1/algorithms/registry/${category}`)
  },

  /** 启用/禁用算法 */
  toggleStatus(id: number, enable: boolean): Promise<void> {
    return put<void>(`/v1/algorithms/registry/${id}/status?enable=${enable}`)
  },

  /** 测试算法运行 */
  testAlgorithm(id: number, params?: Record<string, unknown>): Promise<AlgorithmExecuteResult> {
    return post<AlgorithmExecuteResult>(`/v1/algorithms/registry/${id}/test`, params)
  },

  /** 执行算法（科研沙箱/算法实验室使用） */
  execute(id: number, payload?: Record<string, unknown>): Promise<AlgorithmExecuteResult> {
    return post<AlgorithmExecuteResult>(`/v1/algorithms/registry/${id}/test`, payload)
  },

  /** 获取指定分类的算法列表（用于路径规划算法选择） */
  listByCategoryLegacy(category: string): Promise<Algorithm[]> {
    return get<Algorithm[]>('/v1/algorithms/list', { category, size: 200 })
  },
}
