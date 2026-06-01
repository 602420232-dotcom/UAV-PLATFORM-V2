import { createRouter, createWebHistory } from 'vue-router'
import { message } from 'ant-design-vue'

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
    path: '/assimilation',
    name: 'assimilation',
    component: () => import('../views/AssimilationView.vue'),
    meta: { title: '数据同化' }
  },
  {
    path: '/example',
    name: 'example',
    component: () => import('../views/ExampleView.vue'),
    meta: { title: '示例页面' }
  },
  {
    path: '/smart-cockpit',
    name: 'smartCockpit',
    component: () => import('../views/SmartCockpit.vue'),
    meta: { title: '智能驾驶舱' }
  },
  // 404 页面
  {
    path: '/:pathMatch(.*)*',
    name: 'notFound',
    component: () => import('../views/HomeView.vue'),
    meta: { title: '页面未找到' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由加载状态
let isLoading = false
let loadingMessage = null

// 全局前置守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title || '无人机路径规划系统'
  
  // 显示加载状态（可选）
  if (to.name !== from.name) {
    // 可以在这里显示全局加载指示器
  }
  
  next()
})

// 全局后置守卫
router.afterEach((to, from) => {
  // 隐藏加载状态
  if (loadingMessage) {
    loadingMessage()
    loadingMessage = null
  }
})

// 路由错误处理
router.onError((error, to) => {
  console.error('[Router Error]', {
    error: error.message,
    name: error.name,
    to: to?.path,
    from: router.currentRoute?.value?.path
  })
  
  // 区分错误类型
  const isChunkLoadError = error.name === 'ChunkLoadError' || 
                           error.message?.includes('Failed to fetch dynamically imported module') ||
                           error.message?.includes('Loading chunk')
  
  if (isChunkLoadError) {
    // 资源加载失败
    message.error({
      content: '页面资源加载失败，正在尝试重新加载...',
      duration: 3,
      key: 'route-chunk-error'
    })
    
    // 自动刷新重试（仅一次）
    if (!isLoading) {
      isLoading = true
      
      // 清除缓存后重试
      setTimeout(() => {
        // 强制刷新页面
        window.location.reload()
      }, 1500)
    }
  } else if (error.message?.includes('Failed to resolve async component')) {
    // 组件解析失败
    message.error({
      content: '页面组件加载失败，请刷新页面重试',
      duration: 5,
      key: 'route-component-error'
    })
    
    // 跳转到首页
    if (to?.path !== '/') {
      router.push('/')
    }
  } else {
    // 其他错误
    message.error({
      content: `页面加载失败: ${error.message || '未知错误'}`,
      duration: 5,
      key: 'route-error'
    })
    
    // 跳转到首页
    if (to?.path !== '/') {
      router.push('/')
    }
  }
  
  // 重置加载状态
  isLoading = false
})

/**
 * 安全导航方法
 * @param {string} path - 目标路径
 * @returns {Promise} 导航结果
 */
export async function safeNavigate(path) {
  try {
    await router.push(path)
    return true
  } catch (error) {
    // 忽略导航重复错误
    if (error.name === 'NavigationDuplicated') {
      return true
    }
    
    console.error('[Navigation Error]', error)
    return false
  }
}

/**
 * 预加载路由组件
 * @param {string} name - 路由名称
 */
export function prefetchRoute(name) {
  const route = router.getRoutes().find(r => r.name === name)
  if (route?.components?.default) {
    // 触发组件加载
    route.components.default()
  }
}

export default router
