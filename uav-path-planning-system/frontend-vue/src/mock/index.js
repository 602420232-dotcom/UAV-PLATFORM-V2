import axios from 'axios'

/* ============================================================
 * 前端 Mock 服务（轻量方案 · 浏览器端拦截 · 无需外部插件）
 *
 * 设计：
 *   1. 仅在 import.meta.env.DEV 下注册 axios request 拦截器
 *   2. 对 URL 前缀为 /mock-api/ 的请求走本地 handler 返回 JSON
 *   3. 不影响生产构建（setupMock 在生产环境直接短路返回）
 *
 * 使用：在 main.js 中
 *   import { setupMock } from '@/mock'
 *   setupMock()
 *
 * 业务代码：
 *   axios.get('/mock-api/weather')
 *   axios.post('/mock-api/auth/login', { username, password })
 * ============================================================ */

const MOCK_PREFIX = '/mock-api/'
const routes = []

function normalize(url) {
  if (!url) return ''
  return String(url).replace(/^\/?api\//, '/').replace(/\/+$/, '')
}

function registerRoute(method, url, handler) {
  routes.push({ method: String(method).toLowerCase(), url: normalize(url), handler })
}
function mockGet(url, handler) { registerRoute('get', url, handler) }
function mockPost(url, handler) { registerRoute('post', url, handler) }
function mockPut(url, handler) { registerRoute('put', url, handler) }
function mockDelete(url, handler) { registerRoute('delete', url, handler) }

function matchPattern(pattern, path) {
  const pp = pattern.split('/').filter(Boolean)
  const p = path.split('/').filter(Boolean)
  if (pp.length !== p.length) return null
  const params = {}
  for (let i = 0; i < pp.length; i++) {
    const seg = pp[i]
    if (seg.startsWith(':')) params[seg.slice(1)] = decodeURIComponent(p[i])
    else if (seg !== p[i]) return null
  }
  return params
}

function matchConfig(config) {
  const method = (config.method || 'get').toLowerCase()
  const url = normalize(config.url || '')
  const prefix = normalize(MOCK_PREFIX)
  if (!url.startsWith(prefix)) return null
  const requestPath = url.slice(prefix.length)
  for (const r of routes) {
    if (r.method !== method) continue
    const routePath = r.url.slice(prefix.length)
    const params = matchPattern(routePath, requestPath)
    if (params) return { route: r, params }
  }
  return null
}

function parseBody(data) {
  if (!data) return {}
  if (typeof data === 'string') {
    try { return JSON.parse(data) } catch (_) { return {} }
  }
  return data
}

/* ================== 1. 认证 / Token ================== */

mockPost('/mock-api/auth/login', (config) => {
  const body = parseBody(config.data)
  const username = body.username || 'admin01'
  const roleMap = {
    user01: 'user', prod01: 'production', flight01: 'flight',
    test01: 'tester', deploy01: 'deployment', admin01: 'admin'
  }
  return {
    code: 0, message: 'ok',
    data: {
      token: 'mock-token-' + Date.now(),
      user: {
        id: 'mock-user-' + username,
        username, displayName: username,
        role: roleMap[username] || 'user',
        email: username + '@mock.local',
        avatar: '', permissions: ['read', 'write']
      }
    }
  }
})

mockGet('/mock-api/auth/info', () => ({ code: 0, data: { username: 'admin01', role: 'admin' } }))
mockPost('/mock-api/auth/refresh', () => ({ code: 0, data: { token: 'mock-refreshed-' + Date.now() } }))
mockPost('/mock-api/auth/logout', () => ({ code: 0, message: 'logged out' }))

mockGet('/mock-api/auth/permission-matrix', () => ({
  code: 0,
  data: {
    user: ['dashboard', 'weather', 'orders', 'settings'],
    production: ['dashboard', 'weather', 'cockpit', 'tasks', 'settings'],
    flight: ['dashboard', 'weather', 'cockpit', 'tasks', 'planning', 'assimilation', 'settings'],
    tester: ['dashboard', 'weather', 'planning', 'assimilation', 'monitoring', 'settings'],
    deployment: ['dashboard', 'weather', 'monitoring', 'docker', 'api-config:view', 'settings'],
    admin: ['dashboard', 'weather', 'cockpit', 'tasks', 'planning', 'assimilation', 'monitoring', 'database', 'docker', 'api-config', 'settings']
  }
}))

/* ================== 2. 气象数据 ================== */

mockGet('/mock-api/weather', () => {
  const models = ['WRF', '风乌', '天资', '风雷']
  const hours = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0') + ':00')
  const data = models.map((name) => ({
    model: name,
    timestamps: hours,
    temperature: hours.map(() => +(18 + Math.random() * 12).toFixed(1)),
    windSpeed: hours.map(() => +(2 + Math.random() * 8).toFixed(1)),
    humidity: hours.map(() => +(40 + Math.random() * 40).toFixed(1)),
    pressure: hours.map(() => +(1000 + Math.random() * 20).toFixed(1))
  }))
  return { code: 0, data }
})

mockGet('/mock-api/weather/wind-field', () => {
  const grid = []
  for (let lat = 30; lat <= 40; lat += 0.5) {
    for (let lon = 110; lon <= 120; lon += 0.5) {
      grid.push({
        lat: +lat.toFixed(2), lon: +lon.toFixed(2),
        u: +(Math.random() * 10 - 5).toFixed(2),
        v: +(Math.random() * 10 - 5).toFixed(2),
        speed: +(Math.random() * 10).toFixed(2)
      })
    }
  }
  return { code: 0, data: grid }
})

mockGet('/mock-api/weather/heatmap', () => {
  const data = []
  for (let i = 0; i < 500; i++) {
    data.push([
      +(30 + Math.random() * 10).toFixed(3),
      +(110 + Math.random() * 10).toFixed(3),
      +(Math.random() * 100).toFixed(1)
    ])
  }
  return { code: 0, data }
})

mockGet('/mock-api/weather/variance', () => {
  const data = []
  for (let i = 0; i < 300; i++) {
    data.push([
      +(30 + Math.random() * 10).toFixed(3),
      +(110 + Math.random() * 10).toFixed(3),
      +(Math.random() * 0.8).toFixed(3)
    ])
  }
  return { code: 0, data, confidence: +(0.72 + Math.random() * 0.2).toFixed(3) }
})

mockGet('/mock-api/weather/models', () => ({
  code: 0,
  data: [
    { name: 'WRF', rmse: 2.3, bias: -0.4, score: 92 },
    { name: '风乌', rmse: 1.9, bias: 0.1, score: 95 },
    { name: '天资', rmse: 2.6, bias: -0.6, score: 88 },
    { name: '风雷', rmse: 2.8, bias: 0.3, score: 86 }
  ]
}))

mockPost('/mock-api/weather/netcdf/upload', (config) => {
  const body = parseBody(config.data)
  return {
    code: 0,
    data: {
      fileId: 'nc-' + Date.now(),
      filename: body.filename || 'demo.nc',
      variables: ['T2', 'U10', 'V10', 'RH', 'P', 'PBLH', 'WSPD10'],
      levels: [1000, 950, 900, 850, 800, 700, 600, 500],
      latMin: 30, latMax: 40, lonMin: 110, lonMax: 120,
      timeSteps: 24,
      gridSize: [100, 100],
      size: body.size || 5242880
    }
  }
})

/* ================== 3. 路径规划 ================== */

mockGet('/mock-api/planning/path', (config) => {
  const params = config.params || {}
  const start = params.start || '31.23,121.47'
  const end = params.end || '39.90,116.40'
  const [sLat, sLon] = String(start).split(',').map(Number)
  const [eLat, eLon] = String(end).split(',').map(Number)
  const midLat = (sLat + eLat) / 2
  const midLon = (sLon + eLon) / 2
  const waypoints = [
    { lat: sLat, lon: sLon },
    { lat: +(midLat + 1).toFixed(4), lon: +(midLon - 1).toFixed(4) },
    { lat: +midLat.toFixed(4), lon: +midLon.toFixed(4) },
    { lat: +(midLat - 1).toFixed(4), lon: +(midLon + 1).toFixed(4) },
    { lat: eLat, lon: eLon }
  ]
  const algorithms = ['DE-RRT*', 'DWA', 'VRPTW'].map((name) => ({
    algorithm: name,
    waypoints,
    distance: +(800 + Math.random() * 400).toFixed(1),
    duration: +(45 + Math.random() * 60).toFixed(1),
    energy: +(1200 + Math.random() * 800).toFixed(1),
    risk: +(0.1 + Math.random() * 0.4).toFixed(3)
  }))
  return { code: 0, data: { start: [sLat, sLon], end: [eLat, eLon], algorithms } }
})

mockPost('/mock-api/planning/calculate', (config) => {
  const body = parseBody(config.data)
  return {
    code: 0,
    data: {
      taskId: 'plan-' + Date.now(),
      algorithm: body.algorithm || 'DE-RRT*',
      distance: +(1200 + Math.random() * 300).toFixed(1),
      duration: +(45 + Math.random() * 30).toFixed(1),
      risk: +(0.15 + Math.random() * 0.2).toFixed(3),
      waypoints: (body.waypoints && body.waypoints.length) ? body.waypoints : []
    }
  }
})

mockGet('/mock-api/planning/algorithms', () => ({
  code: 0,
  data: [
    { key: 'de-rrt-star', name: 'DE-RRT*', description: '差分进化快速扩展随机树', avgRisk: 0.18 },
    { key: 'dwa', name: 'DWA', description: '动态窗口法', avgRisk: 0.22 },
    { key: 'vrptw', name: 'VRPTW', description: '带时间窗车辆路径问题', avgRisk: 0.25 }
  ]
}))

/* ================== 4. 任务管理 ================== */

mockGet('/mock-api/tasks', () => {
  const statusList = ['pending', 'running', 'completed', 'cancelled']
  const priorities = ['low', 'normal', 'high', 'urgent']
  const list = Array.from({ length: 12 }).map((_, i) => ({
    id: 'task-' + (1000 + i),
    title: '运输任务 #' + (i + 1),
    status: statusList[i % 4],
    priority: priorities[i % 4],
    origin: '上海浦东',
    destination: '北京首都',
    cargoWeight: +(50 + Math.random() * 200).toFixed(1),
    createdAt: '2026-06-0' + ((i % 9) + 1),
    eta: '2026-06-' + (10 + (i % 20)),
    progress: Math.round(Math.random() * 100),
    operator: ['prod01', 'flight01', 'admin01'][i % 3]
  }))
  return { code: 0, data: { list, total: list.length } }
})

mockPost('/mock-api/tasks', (config) => {
  const body = parseBody(config.data)
  return {
    code: 0,
    data: {
      id: 'task-' + Date.now(),
      ...body,
      status: 'pending',
      createdAt: new Date().toISOString().slice(0, 10)
    }
  }
})

mockGet('/mock-api/tasks/:id', (config, params) => ({
  code: 0,
  data: {
    id: params.id || 'task-1000',
    title: '运输任务详情',
    status: 'running',
    origin: '上海浦东',
    destination: '北京首都',
    cargoWeight: 120.5,
    cargoType: '普通货物',
    priority: 'high',
    progress: 65,
    createdAt: '2026-06-08',
    eta: '2026-06-12',
    operator: 'flight01',
    waypoints: [
      { lat: 31.23, lon: 121.47, name: '起点' },
      { lat: 35.0, lon: 118.0, name: '中转' },
      { lat: 39.90, lon: 116.40, name: '终点' }
    ],
    logs: [
      { time: '08:00', event: '任务创建' },
      { time: '09:30', event: '路径规划完成' },
      { time: '10:15', event: '无人机起飞' },
      { time: '11:00', event: '飞行中' }
    ]
  }
}))

mockPut('/mock-api/tasks/:id', (config, params) => {
  const body = parseBody(config.data)
  return { code: 0, data: { id: params.id, ...body } }
})

mockDelete('/mock-api/tasks/:id', (config, params) => ({
  code: 0, data: { id: params.id, deleted: true }
}))

/* ================== 5. 无人机 ================== */

mockGet('/mock-api/drones', () => {
  const list = Array.from({ length: 8 }).map((_, i) => ({
    id: 'drone-' + (100 + i),
    name: 'UAV-' + (i + 1),
    model: 'DJI-Matrice-300',
    status: ['idle', 'flying', 'charging', 'maintenance'][i % 4],
    battery: Math.round(40 + Math.random() * 60),
    lat: +(30 + Math.random() * 10).toFixed(4),
    lon: +(110 + Math.random() * 10).toFixed(4),
    altitude: Math.round(Math.random() * 500),
    heading: Math.round(Math.random() * 360),
    speed: +(Math.random() * 20).toFixed(1)
  }))
  return { code: 0, data: list }
})

mockGet('/mock-api/drones/:id', (config, params) => ({
  code: 0,
  data: {
    id: params.id,
    name: 'UAV-DEMO',
    model: 'DJI-Matrice-300',
    status: 'flying',
    battery: 78,
    speed: 15.5,
    altitude: 320,
    signal: 92,
    missionId: 'task-1000'
  }
}))

/* ================== 6. 数据同化 ================== */

mockPost('/mock-api/assimilation/status', () => ({
  code: 0,
  data: {
    status: 'running',
    method: '3DVAR',
    progress: 68,
    observationsProcessed: 12450,
    startTime: '2026-06-09 08:00:00',
    estimatedEnd: '2026-06-09 12:30:00',
    rmse: 1.85
  }
}))

mockGet('/mock-api/assimilation/results', () => ({
  code: 0,
  data: {
    method: '3DVAR',
    analysisTime: '2026-06-09 12:00:00',
    rmse: 1.85,
    bias: -0.12,
    spread: 2.12,
    observations: 12450,
    innovations: Array.from({ length: 24 }).map((_, i) => +(Math.random() * 2 - 1).toFixed(3))
  }
}))

mockPost('/mock-api/assimilation/config', (config) => {
  const body = parseBody(config.data)
  return { code: 0, data: { ...body, updatedAt: new Date().toISOString() } }
})

/* ================== 7. 系统指标 / 监控 ================== */

mockGet('/mock-api/metrics', () => ({
  code: 0,
  data: {
    cpu: +(25 + Math.random() * 40).toFixed(1),
    memory: +(40 + Math.random() * 30).toFixed(1),
    disk: +(30 + Math.random() * 40).toFixed(1),
    networkIn: +(10 + Math.random() * 100).toFixed(1),
    networkOut: +(10 + Math.random() * 80).toFixed(1),
    uptime: 86400 + Math.round(Math.random() * 100000),
    requestCount: 12450 + Math.round(Math.random() * 5000),
    errorRate: +(Math.random() * 0.5).toFixed(3),
    avgResponseTime: +(50 + Math.random() * 200).toFixed(0)
  }
}))

mockGet('/mock-api/system/health', () => ({
  code: 0,
  data: {
    overall: 'healthy',
    services: [
      { name: 'api-gateway', status: 'healthy', latency: 45 },
      { name: 'wrf-engine', status: 'healthy', latency: 120 },
      { name: 'assimilation', status: 'healthy', latency: 88 },
      { name: 'model-engine', status: 'degraded', latency: 320 },
      { name: 'database', status: 'healthy', latency: 12 }
    ]
  }
}))

mockGet('/mock-api/system/logs', () => {
  const levels = ['info', 'warn', 'error', 'debug']
  const list = Array.from({ length: 20 }).map((_, i) => ({
    id: 'log-' + (10000 + i),
    level: levels[i % 4],
    service: ['api', 'wrf', 'assimilation'][i % 3],
    message: '系统日志条目 #' + (i + 1),
    timestamp: new Date(Date.now() - i * 60000).toISOString()
  }))
  return { code: 0, data: list }
})

/* ================== 8. 模型评估 ================== */

mockGet('/mock-api/evaluation/models', () => ({
  code: 0,
  data: [
    { name: 'WRF', rmse: 2.3, crps: 0.8, score: 92, rank: 2 },
    { name: '风乌', rmse: 1.9, crps: 0.6, score: 95, rank: 1 },
    { name: '天资', rmse: 2.6, crps: 0.9, score: 88, rank: 3 },
    { name: '风雷', rmse: 2.8, crps: 1.1, score: 86, rank: 4 }
  ]
}))

mockGet('/mock-api/evaluation/curve', () => {
  const thresholds = Array.from({ length: 20 }).map((_, i) => +(i * 0.5).toFixed(2))
  const hitRates = thresholds.map((t) => +(1 - Math.exp(-t / 5)).toFixed(3))
  return { code: 0, data: { thresholds, hitRates } }
})

/* ================== 9. 数据源 / API 配置 ================== */

mockGet('/mock-api/data-sources', () => ({
  code: 0,
  data: [
    { id: 'cma', name: '中国气象局', status: 'online', latency: 120 },
    { id: 'nmc', name: '国家气象中心', status: 'online', latency: 95 },
    { id: 'shlab', name: '上海 AI Lab', status: 'online', latency: 180 },
    { id: 'ecmwf', name: 'ECMWF', status: 'degraded', latency: 420 }
  ]
}))

mockGet('/mock-api/api-config', () => ({
  code: 0,
  data: {
    tianzi: { enabled: true, apiKey: '****-mock', endpoint: 'https://api.cma.gov.cn/mock' },
    fenglei: { enabled: true, apiKey: '****-mock', endpoint: 'https://fenglei.mock' },
    fengwu: { enabled: true, apiKey: '****-mock', endpoint: 'https://fengwu.mock' },
    wrf: { enabled: true, outputDir: '/data/wrf/output', timeStep: 3600 },
    database: { mysql: 'mock-host:3306', redis: 'mock-host:6379' },
    gateway: { rateLimit: 1000, circuitBreak: 5000 }
  }
}))

/* ================== 10. 审计 / 权限模板 ================== */

mockGet('/mock-api/audit/logs', () => {
  const actions = ['login', 'logout', 'create_task', 'update_config', 'export_report']
  const list = Array.from({ length: 15 }).map((_, i) => ({
    id: 'audit-' + (1000 + i),
    user: ['admin01', 'flight01', 'prod01'][i % 3],
    action: actions[i % actions.length],
    ip: '192.168.1.' + (10 + i),
    result: i % 5 === 0 ? 'failed' : 'success',
    timestamp: new Date(Date.now() - i * 300000).toISOString()
  }))
  return { code: 0, data: list }
})

mockGet('/mock-api/permission-templates', () => ({
  code: 0,
  data: [
    { id: 'tpl-admin', name: '管理员模板', roles: ['admin'], permissions: ['*'] },
    { id: 'tpl-flight', name: '飞控人员模板', roles: ['flight'], permissions: ['planning:*', 'cockpit:*'] }
  ]
}))

/* ================== 11. Docker / 部署 ================== */

mockGet('/mock-api/docker/containers', () => ({
  code: 0,
  data: [
    { id: 'c1', name: 'api-gateway', status: 'running', cpu: 12.5, memory: 256 },
    { id: 'c2', name: 'wrf-engine', status: 'running', cpu: 45.3, memory: 2048 },
    { id: 'c3', name: 'database', status: 'running', cpu: 8.2, memory: 512 },
    { id: 'c4', name: 'model-engine', status: 'exited', cpu: 0, memory: 0 }
  ]
}))

/* ================== 12. UTM / 低空 ================== */

mockGet('/mock-api/utm/status', () => ({
  code: 0, data: { connected: true, pendingTasks: 3, approved: 127, rejected: 2 }
}))

mockPost('/mock-api/utm/submit', () => ({
  code: 0, data: { submissionId: 'utm-' + Date.now(), status: 'pending' }
}))

/* ================== 拦截器注册 ================== */

let mockInterceptorId = null
let enabled = false

function enableMockInterceptor() {
  if (enabled) return
  enabled = true
  if (typeof window !== 'undefined') window.__MOCK_ENABLED__ = true

  mockInterceptorId = axios.interceptors.request.use(
    (config) => {
      const match = matchConfig(config)
      if (!match) return config
      const body = parseBody(config.data)
      const result = match.route.handler(config, match.params, body)
      const payload = result && typeof result.then === 'function' ? result : Promise.resolve(result)
      return payload.then((data) => ({
        ...config,
        __uav_mock__: true,
        adapter: () => Promise.resolve({
          data,
          status: 200,
          statusText: 'OK (mock)',
          headers: { 'x-mock': 'enabled', 'content-type': 'application/json' },
          config
        })
      }))
    },
    (error) => Promise.reject(error)
  )
  console.info('[Mock] 已启用 mock 拦截器，共注册 ' + routes.length + ' 条路由（前缀 ' + MOCK_PREFIX + '）')
}

function disableMockInterceptor() {
  if (mockInterceptorId !== null) {
    axios.interceptors.request.eject(mockInterceptorId)
    mockInterceptorId = null
  }
  enabled = false
  if (typeof window !== 'undefined') window.__MOCK_ENABLED__ = false
}

function setupMock() {
  const isDev = typeof import.meta !== 'undefined' &&
    import.meta.env &&
    import.meta.env.DEV
  if (!isDev) return { enabled: false, reason: 'non-dev' }
  enableMockInterceptor()
  return { enabled: true, count: routes.length, prefix: MOCK_PREFIX }
}

export {
  setupMock,
  mockGet, mockPost, mockPut, mockDelete,
  enableMockInterceptor, disableMockInterceptor,
  routes as mockRoutes
}

export default { setupMock }
