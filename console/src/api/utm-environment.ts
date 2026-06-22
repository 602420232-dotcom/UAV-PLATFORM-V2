import { get, post } from './request'

export interface UtmEnvironmentConfig {
  mockEnabled: boolean
  externalUtmEnabled: boolean
  externalUtmBaseUrl: string
  externalUtmApiKey: string
  currentMode: string
}

export interface UtmModeSwitchResult {
  mockEnabled: string
  externalUtmEnabled: string
  mode: string
  message: string
}

export interface UtmConnectionTestResult {
  success: boolean
  statusCode?: number
  message: string
}

export const utmEnvironmentApi = {
  /** 获取UTM环境配置 */
  getConfig(): Promise<UtmEnvironmentConfig> {
    return get<UtmEnvironmentConfig>('/v1/utm/environment/config')
  },

  /** 切换UTM模式 */
  switchMode(mode: 'MOCK' | 'EXTERNAL' | 'HYBRID'): Promise<UtmModeSwitchResult> {
    return post<UtmModeSwitchResult>('/v1/utm/environment/switch', { mode })
  },

  /** 测试外部UTM连接 */
  testConnection(): Promise<UtmConnectionTestResult> {
    return post<UtmConnectionTestResult>('/v1/utm/environment/test-connection')
  }
}
