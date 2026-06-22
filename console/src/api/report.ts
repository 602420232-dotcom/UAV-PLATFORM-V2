import { get, post } from './request'
import type { PageResult } from './request'

export interface ReportTemplate {
  id: string
  name: string
  description: string
  category: 'algorithm_compare' | 'single_experiment' | 'assimilation_analysis'
  supportedFormats: string[]
}

export interface ReportConfig {
  templateId: string
  title: string
  author: string
  format: 'csv' | 'latex' | 'markdown'
  scope: {
    type: 'algorithm' | 'date_range' | 'manual'
    algorithmName?: string
    startDate?: string
    endDate?: string
    experimentIds?: number[]
  }
}

export interface Report {
  id: number
  title: string
  templateName: string
  format: string
  status: string
  content: string
  downloadUrl: string
  createdBy: string
  createdAt: string
}

export interface ReportListParams {
  keyword?: string
  format?: string
  page?: number
  size?: number
}

export const reportApi = {
  /** 获取报告模板列表 */
  listTemplates(): Promise<ReportTemplate[]> {
    return get<ReportTemplate[]>('/v1/reports/templates')
  },

  /** 生成报告 */
  generate(config: ReportConfig): Promise<Report> {
    return post<Report>('/v1/reports/generate', config)
  },

  /** 获取报告列表（分页） */
  list(params?: ReportListParams): Promise<PageResult<Report>> {
    return get<PageResult<Report>>('/v1/reports/list', params as Record<string, unknown>)
  },

  /** 获取报告详情 */
  getById(id: number): Promise<Report> {
    return get<Report>(`/v1/reports/${id}`)
  },

  /** 下载报告 */
  download(id: number): Promise<string> {
    return get<string>(`/v1/reports/${id}/download`)
  },

  /** 删除报告 */
  delete(id: number): Promise<void> {
    return post<void>(`/v1/reports/${id}/delete`)
  },

  /** 预览报告 */
  preview(config: ReportConfig): Promise<string> {
    return post<string>('/v1/reports/preview', config)
  },
}
