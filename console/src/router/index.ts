import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  // 科研功能模块
  {
    path: '/research',
    component: () => import('@/views/research/ResearchLayout.vue'),
    meta: { requiresAuth: true, roles: ['SUPER_ADMIN', 'TENANT_ADMIN', 'OPERATOR', 'ALGORITHM_ADMIN'] },
    redirect: '/research/sandbox',
    children: [
      {
        path: 'sandbox',
        name: 'ResearchSandbox',
        component: () => import('@/views/SandboxView.vue'),
        meta: { title: '科研沙箱', icon: 'Flask', roles: ['SUPER_ADMIN', 'TENANT_ADMIN', 'OPERATOR', 'ALGORITHM_ADMIN'] },
      },
      {
        path: 'algorithm-lab',
        name: 'AlgorithmLab',
        component: () => import('@/views/research/AlgorithmLab.vue'),
        meta: { title: '算法实验室', icon: 'Cpu', roles: ['SUPER_ADMIN', 'ALGORITHM_ADMIN'] },
      },
      {
        path: 'experiments',
        name: 'ExperimentManager',
        component: () => import('@/views/research/ExperimentManager.vue'),
        meta: { title: '实验管理', icon: 'List', roles: ['SUPER_ADMIN', 'TENANT_ADMIN', 'OPERATOR', 'ALGORITHM_ADMIN'] },
      },
      {
        path: 'reports',
        name: 'ReportCenter',
        component: () => import('@/views/research/ReportCenter.vue'),
        meta: { title: '报告中心', icon: 'Document', roles: ['SUPER_ADMIN', 'TENANT_ADMIN', 'OPERATOR', 'ALGORITHM_ADMIN'] },
      },
      {
        path: 'wrf-analysis',
        name: 'WRFAnalysis',
        component: () => import('@/views/research/WRFTerrainAnalysisView.vue'),
        meta: { title: 'WRF地形分析', icon: 'MapLocation', roles: ['SUPER_ADMIN', 'ALGORITHM_ADMIN'] },
      },
      {
        path: 'pbl-analysis',
        name: 'PBLAnalysis',
        component: () => import('@/views/research/PBLAnalysisView.vue'),
        meta: { title: '边界层分析', icon: 'WindPower', roles: ['SUPER_ADMIN', 'ALGORITHM_ADMIN'] },
      },
      {
        path: 'cu-analysis',
        name: 'CumulusAnalysis',
        component: () => import('@/views/research/CumulusAnalysisView.vue'),
        meta: { title: '积云参数化', icon: 'Cloudy', roles: ['SUPER_ADMIN', 'ALGORITHM_ADMIN'] },
      },
    ],
  },
  // API运营管理模块
  {
    path: '/api-ops',
    component: () => import('@/views/api/ApiOpsLayout.vue'),
    meta: { requiresAuth: true, roles: ['SUPER_ADMIN', 'TENANT_ADMIN'] },
    redirect: '/api-ops/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'ApiDashboard',
        component: () => import('@/views/api/DashboardView.vue'),
        meta: { title: '运营仪表盘', icon: 'Odometer', roles: ['SUPER_ADMIN', 'TENANT_ADMIN'] },
      },
      {
        path: 'api-keys',
        name: 'ApiKeyManager',
        component: () => import('@/views/api/ApiKeyManager.vue'),
        meta: { title: 'API密钥管理', icon: 'Key', roles: ['SUPER_ADMIN', 'TENANT_ADMIN'] },
      },
      {
        path: 'tenants',
        name: 'ApiTenantManager',
        component: () => import('@/views/api/TenantManager.vue'),
        meta: { title: '租户管理', icon: 'OfficeBuilding', roles: ['SUPER_ADMIN'] },
      },
      {
        path: 'usage',
        name: 'UsageAnalytics',
        component: () => import('@/views/api/UsageAnalytics.vue'),
        meta: { title: '用量分析', icon: 'TrendCharts', roles: ['SUPER_ADMIN', 'TENANT_ADMIN'] },
      },
      {
        path: 'health',
        name: 'ServiceHealth',
        component: () => import('@/views/api/ServiceHealth.vue'),
        meta: { title: '服务健康', icon: 'FirstAidKit', roles: ['SUPER_ADMIN', 'TENANT_ADMIN'] },
      },
      {
        path: 'alerts',
        name: 'AlertRules',
        component: () => import('@/views/api/AlertRules.vue'),
        meta: { title: '告警规则', icon: 'Bell', roles: ['SUPER_ADMIN', 'TENANT_ADMIN'] },
      },
      {
        path: 'utm-env',
        name: 'UtmEnvironment',
        component: () => import('@/components/settings/UtmEnvironmentConfig.vue'),
        meta: { title: 'UTM环境配置', icon: 'Monitor', roles: ['SUPER_ADMIN', 'TENANT_ADMIN'] },
      },
    ],
  },
  // 业务中台布局 - 只包含通用业务功能（API运营和科研功能已分离到独立模块）
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘', icon: 'Odometer', roles: ['SUPER_ADMIN', 'TENANT_ADMIN', 'OPERATOR', 'OBSERVER', 'ALGORITHM_ADMIN'] },
      },
      {
        path: 'weather',
        name: 'Weather',
        component: () => import('@/views/WeatherView.vue'),
        meta: { title: '气象数据', icon: 'Cloudy', roles: ['SUPER_ADMIN', 'TENANT_ADMIN', 'OPERATOR', 'OBSERVER'] },
      },
      {
        path: 'planning',
        name: 'Planning',
        component: () => import('@/views/PlanningView.vue'),
        meta: { title: '路径规划', icon: 'Map', roles: ['SUPER_ADMIN', 'TENANT_ADMIN', 'OPERATOR'] },
      },
      {
        path: 'assimilation',
        name: 'Assimilation',
        component: () => import('@/views/AssimilationView.vue'),
        meta: { title: '数据同化', icon: 'Connection', roles: ['SUPER_ADMIN', 'TENANT_ADMIN', 'OPERATOR'] },
      },
      {
        path: 'risk',
        name: 'Risk',
        component: () => import('@/views/RiskView.vue'),
        meta: { title: '风险/适航', icon: 'Warning', roles: ['SUPER_ADMIN', 'TENANT_ADMIN', 'OPERATOR'] },
      },
      {
        path: 'observation',
        name: 'Observation',
        component: () => import('@/views/ObservationView.vue'),
        meta: { title: '观测决策', icon: 'View', roles: ['SUPER_ADMIN', 'TENANT_ADMIN', 'OPERATOR', 'OBSERVER'] },
      },
      {
        path: 'utm',
        name: 'Utm',
        component: () => import('@/views/UtmView.vue'),
        meta: { title: 'UTM 管理', icon: 'Position', roles: ['SUPER_ADMIN', 'TENANT_ADMIN', 'OPERATOR'] },
      },
      {
        path: 'algorithms',
        name: 'Algorithms',
        component: () => import('@/views/AlgorithmList.vue'),
        meta: { title: '算法管理', icon: 'Cpu', roles: ['SUPER_ADMIN', 'ALGORITHM_ADMIN'] },
      },
      {
        path: 'manual',
        name: 'UserManual',
        component: () => import('@/views/UserManual.vue'),
        meta: { title: '操作手册', icon: 'Document', roles: ['SUPER_ADMIN', 'TENANT_ADMIN', 'OPERATOR', 'OBSERVER', 'ALGORITHM_ADMIN'] },
      },
    ],
  },
  // 系统管理模块（独立布局）
  {
    path: '/system',
    component: () => import('@/components/layout/AppLayout.vue'),
    meta: { requiresAuth: true, roles: ['SUPER_ADMIN', 'TENANT_ADMIN'] },
    redirect: '/system/tenants',
    children: [
      {
        path: 'tenants',
        name: 'TenantList',
        component: () => import('@/views/TenantList.vue'),
        meta: { title: '租户管理', icon: 'OfficeBuilding', roles: ['SUPER_ADMIN'] },
      },
      {
        path: 'tenants/:id',
        name: 'TenantDetail',
        component: () => import('@/views/TenantDetail.vue'),
        meta: { title: '租户详情', icon: 'OfficeBuilding', roles: ['SUPER_ADMIN'] },
      },
      {
        path: 'api-keys',
        name: 'ApiKeyList',
        component: () => import('@/views/ApiKeyList.vue'),
        meta: { title: 'API Key 管理', icon: 'Key', roles: ['SUPER_ADMIN', 'TENANT_ADMIN'] },
      },
      {
        path: 'users',
        name: 'UserList',
        component: () => import('@/views/UserList.vue'),
        meta: { title: '用户管理', icon: 'User', roles: ['SUPER_ADMIN'] },
      },
      {
        path: 'roles',
        name: 'RoleList',
        component: () => import('@/views/RoleList.vue'),
        meta: { title: '角色管理', icon: 'Lock', roles: ['SUPER_ADMIN'] },
      },
      {
        path: 'database',
        name: 'Database',
        component: () => import('@/views/DatabaseView.vue'),
        meta: { title: '数据库管理', icon: 'Database', roles: ['SUPER_ADMIN'] },
      },
      {
        path: 'weather-source',
        name: 'WeatherSource',
        component: () => import('@/views/settings/WeatherSourceView.vue'),
        meta: { title: '气象数据源', icon: 'Cloudy', roles: ['SUPER_ADMIN', 'TENANT_ADMIN'] },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    next({ name: 'Login' })
  } else if (to.name === 'Login' && authStore.isAuthenticated) {
    next({ name: 'Dashboard' })
  } else {
    // 角色权限检查：如果路由配置了允许的角色列表，则检查当前用户角色
    const allowedRoles = to.meta.roles as string[] | undefined
    if (allowedRoles && !allowedRoles.includes(authStore.currentRole)) {
      // 无权限时跳转到仪表盘
      next({ name: 'Dashboard' })
    } else {
      next()
    }
  }
})

// 路由预加载策略：鼠标悬停时预加载目标路由组件
const preloadMap = new Map<string, () => Promise<void>>()
const preloadedRoutes = new Set<string>()

function setupRoutePreloading() {
  // 收集所有懒加载路由的预加载函数
  routes.forEach((route) => {
    collectPreloadFunctions(route)
  })

  // 在 document 上监听 mouseover 事件，匹配导航链接
  document.addEventListener('mouseover', (event) => {
    const target = event.target as HTMLElement
    const anchor = target.closest('a[href]') as HTMLAnchorElement | null
    if (!anchor) return

    const href = anchor.getAttribute('href')
    if (!href || href.startsWith('http') || href.startsWith('#')) return

    // 解析路由名称
    const routeName = resolveRouteName(href)
    if (routeName && !preloadedRoutes.has(routeName)) {
      const preloadFn = preloadMap.get(routeName)
      if (preloadFn) {
        preloadedRoutes.add(routeName)
        preloadFn().catch(() => {
          // 预加载失败不影响用户体验，静默处理
          preloadedRoutes.delete(routeName)
        })
      }
    }
  })
}

function collectPreloadFunctions(route: RouteRecordRaw) {
  if (route.name && typeof route.component === 'function') {
    preloadMap.set(route.name as string, () =>
      (route.component as () => Promise<any>)().catch(() => {})
    )
  }
  route.children?.forEach((child) => collectPreloadFunctions(child))
}

function resolveRouteName(href: string): string | null {
  // 处理相对路径，如 /dashboard, /planning 等
  const path = href.replace(/^\.\//, '/')

  // 扁平化搜索路由表
  const allRoutes = flattenRoutes(routes)
  const matched = allRoutes.find((r) => r.path === path || r.path.endsWith(path))
  return matched?.name?.toString() ?? null
}

function flattenRoutes(
  routes: RouteRecordRaw[],
  parentPath = ''
): (RouteRecordRaw & { fullPath: string })[] {
  const result: (RouteRecordRaw & { fullPath: string })[] = []
  for (const route of routes) {
    const fullPath = parentPath
      ? `${parentPath.replace(/\/$/, '')}/${route.path.replace(/^\//, '')}`
      : route.path
    result.push({ ...route, path: fullPath, fullPath } as RouteRecordRaw & { fullPath: string })
    if (route.children) {
      result.push(...flattenRoutes(route.children, fullPath))
    }
  }
  return result
}

// 路由就绪后启动预加载
router.isReady().then(() => {
  setupRoutePreloading()
})

export default router
