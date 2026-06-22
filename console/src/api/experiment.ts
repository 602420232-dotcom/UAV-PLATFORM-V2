import { get, post, del } from './request'
import type { PageResult } from './request'

export interface Experiment {
  id: number
  experimentName: string
  algorithmName: string
  algorithmCategory: string
  status: string
  configJson: string
  resultJson: string
  metricsJson: string
  snapshotHash: string
  durationMs: number
  createdBy: string
  createdAt: string
  updatedAt: string
}

export interface ExperimentListParams {
  keyword?: string
  status?: string
  startDate?: string
  endDate?: string
  page?: number
  size?: number
}

export interface CompareResult {
  experiments: Experiment[]
  metrics: Array<{
    name: string
    key: string
    values: Array<{ experimentId: number; experimentName: string; value: number }>
  }>
}

export interface MetricsSummary {
  algorithmName: string
  avgDurationMs: number
  successRate: number
  totalRuns: number
  bestMetrics: Record<string, number>
}

export const experimentApi = {
  /** 获取实验列表（分页） */
  list(params?: ExperimentListParams): Promise<PageResult<Experiment>> {
    return get<PageResult<Experiment>>('/v1/experiments', params as Record<string, unknown>)
  },

  /** 获取实验详情 */
  getById(id: number): Promise<Experiment> {
    return get<Experiment>(`/v1/experiments/${id}`)
  },

  /** 创建实验 */
  create(data: Partial<Experiment>): Promise<Experiment> {
    return post<Experiment>('/v1/experiments', data)
  },

  /** 删除实验 */
  delete(id: number): Promise<void> {
    return del<void>(`/v1/experiments/${id}`)
  },

  /** 创建快照 */
  createSnapshot(id: number): Promise<{ hash: string }> {
    return post<{ hash: string }>(`/v1/experiments/${id}/snapshot`)
  },

  /** 获取快照 */
  getSnapshot(id: number): Promise<{ hash: string; data: string }> {
    return get<{ hash: string; data: string }>(`/v1/experiments/${id}/snapshot`)
  },

  /** 恢复快照 */
  restore(id: number): Promise<{ config: string; weatherContext: string }> {
    return post<{ config: string; weatherContext: string }>(`/v1/experiments/${id}/restore`)
  },

  /** 对比实验 */
  compare(ids: number[]): Promise<CompareResult> {
    return post<CompareResult>('/v1/experiments/compare', { ids })
  },

  /** 生成报告 */
  generateReport(id: number, format: string): Promise<string> {
    return get<string>(`/v1/experiments/${id}/report`, { format })
  },

  /** 获取算法指标摘要 */
  getMetricsSummary(algorithmName: string): Promise<MetricsSummary> {
    return get<MetricsSummary>('/v1/experiments/metrics/summary', { algorithmName })
  },
}
