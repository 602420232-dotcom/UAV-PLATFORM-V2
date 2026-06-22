import { get, post } from './request'

export interface WeatherSource {
  sourceType: string
  name: string
  enabled: boolean
  priority: number
  forecastHours: number
  resolution: string
  config: Record<string, unknown>
}

export interface WeatherSourceUpdateRequest {
  enabled?: boolean
  priority?: number
  config?: Record<string, unknown>
}

export const weatherSourceApi = {
  /** 获取所有气象数据源配置 */
  list(): Promise<WeatherSource[]> {
    return get<WeatherSource[]>('/v1/weather/sources')
  },

  /** 获取指定数据源详情 */
  getDetail(sourceType: string): Promise<WeatherSource> {
    return get<WeatherSource>(`/v1/weather/sources/${sourceType}`)
  },

  /** 更新数据源配置 */
  update(sourceType: string, data: WeatherSourceUpdateRequest): Promise<void> {
    return post<void>(`/v1/weather/sources/${sourceType}/config`, data)
  },

  /** 测试数据源连接 */
  testConnection(sourceType: string): Promise<{ success: boolean; message: string }> {
    return post<{ success: boolean; message: string }>(`/v1/weather/sources/${sourceType}/test`)
  },

  /** 获取数据源状态 */
  getStatus(): Promise<Record<string, { status: string; lastUpdate: string }>> {
    return get<Record<string, { status: string; lastUpdate: string }>>('/v1/weather/sources/status')
  }
}
