import { get, post } from './request'

export interface WeatherGrid {
  lon: number
  lat: number
  altitude: number
  windSpeed: number
  windDirection: number
  temperature: number
  humidity: number
  pressure: number
  visibility: number
  weatherCode: number
  source: string
  forecastTime: string
}

export interface WindProfile {
  lon: number
  lat: number
  levels: WindLevel[]
}

export interface WindLevel {
  altitude: number
  windSpeed: number
  windDirection: number
  temperature: number
}

export interface WeatherQueryRequest {
  lon: number
  lat: number
  altitude?: number
  source?: string
  forecastTime?: string
}

export interface WindProfileQueryRequest {
  lon: number
  lat: number
  maxAltitude?: number
  levels?: number
  source?: string
}

export const weatherApi = {
  /** 单点气象查询 */
  queryPoint(data: WeatherQueryRequest): Promise<WeatherGrid> {
    return post<WeatherGrid>('/v1/weather/point', data)
  },

  /** 区域气象格点查询 */
  queryRegion(params: {
    minLon: number
    minLat: number
    maxLon: number
    maxLat: number
    altitude?: number
    source?: string
    forecastTime?: string
  }): Promise<WeatherGrid[]> {
    return get<WeatherGrid[]>('/v1/weather/region', params)
  },

  /** 风场剖面查询 */
  queryWindProfile(data: WindProfileQueryRequest): Promise<WindProfile> {
    return post<WindProfile>('/v1/weather/wind-profile', data)
  },

  /** 多源融合气象查询 */
  queryFusion(data: WeatherQueryRequest): Promise<WeatherGrid> {
    return post<WeatherGrid>('/v1/weather/fusion', data)
  },
}
