/**
 * TypeScript 类型定义
 * 无人机路径规划系统前端类型定义
 */

// ==================== 基础类型 ====================

/**
 * 坐标类型
 */
export interface Coordinates {
  lat: number
  lng: number
  alt?: number
}

/**
 * 分页参数
 */
export interface Pagination {
  page: number
  size: number
  total?: number
}

/**
 * API 响应类型
 */
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  code?: number
}

// ==================== 无人机类型 ====================

/**
 * 无人机类型
 */
export type DroneType = 'multirotor' | 'fixed-wing' | 'vtol'

/**
 * 无人机状态
 */
export type DroneStatus = 'online' | 'offline' | 'mission' | 'standby' | 'maintenance'

/**
 * 无人机信息
 */
export interface Drone {
  id: string
  name: string
  type: DroneType
  status: DroneStatus
  battery: number
  location: string
  coordinates?: Coordinates
  maxSpeed?: number
  maxAltitude?: number
  payload?: number
  createdAt?: string
  updatedAt?: string
}

/**
 * 无人机列表响应
 */
export interface DroneListResponse {
  content: Drone[]
  totalElements: number
  totalPages: number
  size: number
  number: number
}

// ==================== 任务类型 ====================

/**
 * 任务类型
 */
export type TaskType = 'delivery' | 'inspection' | 'rescue' | 'survey' | 'patrol'

/**
 * 任务状态
 */
export type TaskStatus = 'pending' | 'assigned' | 'in-progress' | 'completed' | 'cancelled'

/**
 * 任务优先级
 */
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent'

/**
 * 任务信息
 */
export interface Task {
  id: number | string
  name: string
  type: TaskType
  location: string
  coordinates?: Coordinates
  priority: TaskPriority
  status: TaskStatus
  description?: string
  assignedDrone?: string
  estimatedTime?: number
  actualTime?: number
  distance?: number
  createdAt?: string
  updatedAt?: string
  completedAt?: string
}

/**
 * 任务创建参数
 */
export interface TaskCreateParams {
  name: string
  type: TaskType
  location: string
  priority: TaskPriority
  description?: string
}

/**
 * 任务更新参数
 */
export interface TaskUpdateParams extends Partial<TaskCreateParams> {
  status?: TaskStatus
  assignedDrone?: string
}

// ==================== 气象数据类型 ====================

/**
 * 风场数据点
 */
export interface WindFieldPoint {
  lat: number
  lng: number
  speed: number
  direction: number
  temperature: number
  humidity: number
  pressure?: number
}

/**
 * 气象数据
 */
export interface WeatherData {
  windSpeed: number
  windDirection: number
  temperature: number
  humidity: number
  visibility?: number
  pressure?: number
  precipitation?: number
  cloudCover?: number
  windField?: WindFieldPoint[]
  forecastTime?: string
  updateTime?: string
}

/**
 * 气象风险评估
 */
export interface WeatherRisk {
  level: 'low' | 'medium' | 'high' | 'extreme'
  score: number
  factors: {
    wind: number
    visibility: number
    precipitation: number
    temperature: number
  }
  recommendation?: string
}

// ==================== 路径规划类型 ====================

/**
 * 任务点
 */
export interface TaskPoint {
  id: number
  name: string
  lat: number
  lng: number
  demand?: number
  timeWindow?: {
    start: number
    end: number
  }
}

/**
 * 路径
 */
export interface Route {
  droneId: number
  path: string[]
  distance: number
  time: number
  riskLevel?: 'low' | 'medium' | 'high'
  coordinates?: Coordinates[]
}

/**
 * 路径规划结果
 */
export interface PlanningResult {
  droneCount: number
  taskCount: number
  totalDistance: number
  totalTime: number
  routes: Route[]
  status: 'success' | 'partial' | 'failed'
  message?: string
}

/**
 * 路径规划参数
 */
export interface PlanningParams {
  taskPoints: TaskPoint[]
  droneCount: number
  riskThreshold: number
  weatherData?: WeatherData
  constraints?: {
    maxDistance?: number
    maxTime?: number
    avoidAreas?: Coordinates[][]
  }
}

// ==================== 方案管理类型 ====================

/**
 * 规划方案
 */
export interface Plan {
  id: number | string
  name: string
  description?: string
  taskPoints: TaskPoint[]
  result?: PlanningResult
  createdAt: string
  updatedAt?: string
}

// ==================== 实时数据类型 ====================

/**
 * 实时监控数据
 */
export interface RealtimeData {
  windSpeed: number
  windDirection: number
  temperature: number
  humidity: number
  droneStatus: string
  taskProgress: number
  riskLevel: string
  alertCount: number
  timestamp?: string
}

/**
 * 告警信息
 */
export interface Alert {
  id: string
  time: string
  message: string
  level: 'info' | 'warning' | 'error' | 'critical'
  source?: string
  acknowledged?: boolean
}

/**
 * 资源使用情况
 */
export interface ResourceUsage {
  name: string
  utilization: number
  status?: 'normal' | 'warning' | 'critical'
}

// ==================== 系统监控类型 ====================

/**
 * 系统状态
 */
export interface SystemStatus {
  status: 'normal' | 'warning' | 'error'
  uptime: number
  connections: number
  signalStrength: number
  clusterBattery: number
  averageTemperature: number
  averageWindSpeed: number
}

/**
 * 性能指标
 */
export interface PerformanceMetrics {
  cpuUsage: number
  memoryUsage: number
  diskUsage: number
  networkLatency: number
  requestCount: number
  errorRate: number
}

// ==================== 表单验证类型 ====================

/**
 * 表单验证规则
 */
export interface FormRule {
  required?: boolean
  message?: string
  trigger?: 'blur' | 'change'
  validator?: (rule: any, value: any) => Promise<void>
  pattern?: RegExp
  min?: number
  max?: number
  len?: number
  type?: 'string' | 'number' | 'boolean' | 'array' | 'object'
}

/**
 * 表单字段定义
 */
export interface FormField {
  name: string
  label: string
  type: 'text' | 'number' | 'select' | 'textarea' | 'date' | 'coordinates'
  rules?: FormRule[]
  placeholder?: string
  options?: { label: string; value: any }[]
  defaultValue?: any
}

// ==================== 用户认证类型 ====================

/**
 * 用户信息
 */
export interface User {
  id: string
  username: string
  email?: string
  role: 'admin' | 'operator' | 'viewer'
  permissions?: string[]
  createdAt?: string
  lastLogin?: string
}

/**
 * 登录参数
 */
export interface LoginParams {
  username: string
  password: string
  remember?: boolean
}

/**
 * 登录响应
 */
export interface LoginResponse {
  token: string
  user: User
  expiresIn: number
}

// ==================== 数据源类型 ====================

/**
 * 数据源类型
 */
export type DataSourceType = 'weather' | 'drone' | 'task' | 'map' | 'custom'

/**
 * 数据源状态
 */
export type DataSourceStatus = 'connected' | 'disconnected' | 'error' | 'syncing'

/**
 * 数据源信息
 */
export interface DataSource {
  id: string
  name: string
  type: DataSourceType
  status: DataSourceStatus
  url?: string
  lastSync?: string
  recordCount?: number
  config?: Record<string, any>
}

// ==================== 历史记录类型 ====================

/**
 * 历史记录项
 */
export interface HistoryRecord {
  id: string
  type: 'task' | 'flight' | 'plan' | 'alert'
  title: string
  description?: string
  timestamp: string
  data?: any
}

/**
 * 历史记录查询参数
 */
export interface HistoryQueryParams {
  type?: string
  startDate?: string
  endDate?: string
  keyword?: string
  page?: number
  size?: number
}

// ==================== 导出类型 ====================

export type {
  DroneType,
  DroneStatus,
  TaskType,
  TaskStatus,
  TaskPriority,
  DataSourceType,
  DataSourceStatus
}
