import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/path-planning',
    name: 'pathPlanning',
    component: () => import('../views/PathPlanningView.vue'),
    meta: { title: '路径规划' }
  },
  {
    path: '/weather',
    name: 'weather',
    component: () => import('../views/WeatherView.vue'),
    meta: { title: '气象数据' }
  },
  {
    path: '/tasks',
    name: 'tasks',
    component: () => import('../views/TasksView.vue'),
    meta: { title: '任务管理' }
  },
  {
    path: '/drones',
    name: 'drones',
    component: () => import('../views/DronesView.vue'),
    meta: { title: '无人机管理' }
  },
  {
    path: '/history',
    name: 'history',
    component: () => import('../views/HistoryView.vue'),
    meta: { title: '历史记录' }
  },
  {
    path: '/monitoring',
    name: 'monitoring',
    component: () => import('../views/MonitoringView.vue'),
    meta: { title: '系统监控' }
  },
  {
    path: '/data-sources',
    name: 'dataSources',
    component: () => import('../views/DataSourceView.vue'),
    meta: { title: '数据源管理' }
  },
  {
    path: '/example',
    name: 'example',
    component: () => import('../views/ExampleView.vue'),
    meta: { title: '示例页面' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || '无人机路径规划系统'
  next()
})

router.onError((error) => {
  console.error('路由加载失败:', error)
})

export default router