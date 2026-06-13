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

export default router
