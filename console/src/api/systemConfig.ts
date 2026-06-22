import { get, put } from './request'

export interface DemoModeStatus {
  demoMode: boolean
}

export interface SystemConfig {
  id: number
  configKey: string
  configValue: string
  description: string
  updatedBy: string
  createdAt: string
  updatedAt: string
}

export const systemConfigApi = {
  /** 获取演示模式状态（公开接口） */
  getDemoMode: () => get<DemoModeStatus>('/v1/system/config/demo-mode'),

  /** 切换演示模式（需要管理员权限） */
  setDemoMode: (enabled: boolean) => put<void>('/v1/system/config/demo-mode', { enabled }),

  /** 获取所有系统配置 */
  list: () => get<SystemConfig[]>('/v1/system/config'),
}
