import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import DefaultLayout from '../layouts/DefaultLayout.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/auth/LoginView.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/',
    component: DefaultLayout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/dashboard/DashboardView.vue'),
        meta: { title: '首页概览', icon: 'dashboard' }
      },
      {
        path: 'path-planning',
        name: 'PathPlanning',
        component: () => import('../views/planning/PathPlanningView.vue'),
        meta: { title: '路径规划', icon: 'planning' }
      },
      {
        path: 'weather',
        name: 'Weather',
        component: () => import('../views/weather/WeatherView.vue'),
        meta: { title: '气象数据', icon: 'weather' }
      },
      {
        path: 'tasks',
        name: 'Tasks',
        component: () => import('../views/operation/TasksView.vue'),
        meta: { title: '任务管理', icon: 'tasks' }
      },
      {
        path: 'drones',
        name: 'Drones',
        component: () => import('../views/operation/DronesView.vue'),
        meta: { title: '无人机管理', icon: 'drone' }
      },
      {
        path: 'history',
        name: 'History',
        component: () => import('../views/operation/HistoryView.vue'),
        meta: { title: '历史记录', icon: 'history' }
      },
      {
        path: 'data-sources',
        name: 'DataSources',
        component: () => import('../views/data/DataSourceView.vue'),
        meta: { title: '数据源管理', icon: 'data' }
      },
      {
        path: 'assimilation',
        name: 'Assimilation',
        component: () => import('../views/data/AssimilationView.vue'),
        meta: { title: '数据同化', icon: 'data' }
      },
      {
        path: 'monitoring',
        name: 'Monitoring',
        component: () => import('../views/monitoring/SystemMonitorView.vue'),
        meta: { title: '系统监控', icon: 'monitor' }
      },
      {
        path: 'cockpit',
        name: 'Cockpit',
        component: () => import('../views/cockpit/SmartCockpit.vue'),
        meta: { title: '智能驾驶舱', icon: 'cockpit' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFound.vue'),
    meta: { title: '页面未找到', public: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  authStore.initFromStorage()

  const isPublic = to.meta?.public === true
  const isLoggedIn = authStore.isLoggedIn

  if (to.path === '/login') {
    if (isLoggedIn) {
      next('/dashboard')
    } else {
      next()
    }
    return
  }

  if (!isPublic && !isLoggedIn) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }

  next()
})

router.afterEach((to) => {
  if (to.meta?.title) {
    document.title = `${to.meta.title} - 无人机路径规划系统`
  }
})

router.onError((error) => {
  console.error('Router error:', error)
})

export default router
