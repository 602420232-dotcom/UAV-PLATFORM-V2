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
        meta: { title: '仪表盘', icon: 'Odometer' },
      },
      {
        path: 'tenants',
        name: 'TenantList',
        component: () => import('@/views/TenantList.vue'),
        meta: { title: '租户管理', icon: 'OfficeBuilding' },
      },
      {
        path: 'tenants/:id',
        name: 'TenantDetail',
        component: () => import('@/views/TenantDetail.vue'),
        meta: { title: '租户详情', icon: 'OfficeBuilding' },
      },
      {
        path: 'api-keys',
        name: 'ApiKeyList',
        component: () => import('@/views/ApiKeyList.vue'),
        meta: { title: 'API Key 管理', icon: 'Key' },
      },
      {
        path: 'weather',
        name: 'Weather',
        component: () => import('@/views/WeatherView.vue'),
        meta: { title: '气象数据', icon: 'Cloudy' },
      },
      {
        path: 'planning',
        name: 'Planning',
        component: () => import('@/views/PlanningView.vue'),
        meta: { title: '路径规划', icon: 'Map' },
      },
      {
        path: 'assimilation',
        name: 'Assimilation',
        component: () => import('@/views/AssimilationView.vue'),
        meta: { title: '数据同化', icon: 'Connection' },
      },
      {
        path: 'risk',
        name: 'Risk',
        component: () => import('@/views/RiskView.vue'),
        meta: { title: '风险/适航', icon: 'Warning' },
      },
      {
        path: 'observation',
        name: 'Observation',
        component: () => import('@/views/ObservationView.vue'),
        meta: { title: '观测决策', icon: 'View' },
      },
      {
        path: 'utm',
        name: 'Utm',
        component: () => import('@/views/UtmView.vue'),
        meta: { title: 'UTM 管理', icon: 'Position' },
      },
      {
        path: 'algorithms',
        name: 'Algorithms',
        component: () => import('@/views/AlgorithmList.vue'),
        meta: { title: '算法管理', icon: 'Cpu' },
      },
      {
        path: 'sandbox',
        name: 'Sandbox',
        component: () => import('@/views/SandboxView.vue'),
        meta: { title: '科研沙箱', icon: 'Flask' },
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
    next()
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
    result.push({ ...route, path: fullPath })
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
