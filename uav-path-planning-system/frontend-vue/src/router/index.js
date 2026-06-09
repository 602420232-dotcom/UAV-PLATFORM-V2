import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore, PERMISSION_MATRIX } from '../stores/auth'
import { useAppStore } from '../stores/app'

const routes = [
  // ===== 认证相关（公开路由）=====
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/auth/LoginView.vue'),
    meta: { public: true, title: '登录', hideLayout: true }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/auth/RegisterView.vue'),
    meta: { public: true, title: '注册', hideLayout: true }
  },
  {
    path: '/forgot-password',
    name: 'forgot-password',
    component: () => import('../views/auth/ForgotPasswordView.vue'),
    meta: { public: true, title: '忘记密码', hideLayout: true }
  },

  // ===== 带 Layout 的主路由 =====
  {
    path: '/',
    component: () => import('../layouts/DefaultLayout.vue'),
    redirect: '/dashboard',
    children: [
      // 首页
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('../views/dashboard/DashboardView.vue'),
        meta: { title: '项目简介 / 首页', icon: 'HomeFilled', key: 'dashboard' }
      },
      // 气象数据
      {
        path: 'weather',
        name: 'weather',
        component: () => import('../views/weather/WeatherView.vue'),
        meta: { title: '气象数据', icon: 'PartlyCloudy', key: 'weather' }
      },
      // 下单
      {
        path: 'orders',
        name: 'orders',
        component: () => import('../views/orders/OrderView.vue'),
        meta: { title: '下单 / 选择运输地点', icon: 'Goods', key: 'orders' }
      },
      // 智能驾驶舱
      {
        path: 'cockpit',
        name: 'cockpit',
        component: () => import('../views/cockpit/SmartCockpit.vue'),
        meta: { title: '智能驾驶舱', icon: 'Monitor', key: 'cockpit' }
      },
      // 任务管理
      {
        path: 'tasks',
        name: 'tasks',
        component: () => import('../views/operation/TasksView.vue'),
        meta: { title: '运输任务管理', icon: 'List', key: 'tasks' }
      },
      // 路径规划
      {
        path: 'path-planning',
        name: 'path-planning',
        component: () => import('../views/planning/PathPlanningView.vue'),
        meta: { title: '路径规划', icon: 'Position', key: 'path-planning' }
      },
      // 模型评估
      {
        path: 'model-evaluation',
        name: 'model-evaluation',
        component: () => import('../views/evaluation/ModelEvaluationView.vue'),
        meta: { title: '模型评估', icon: 'DataAnalysis', key: 'model-evaluation', roles: ['flight', 'tester', 'admin'] }
      },
      // 算法参数调优
      {
        path: 'parameter-tuning',
        name: 'parameter-tuning',
        component: () => import('../views/params/ParameterTuningView.vue'),
        meta: { title: '算法参数调优', icon: 'Tools', key: 'parameter-tuning', roles: ['flight', 'tester', 'admin'] }
      },
      // 实验对比工具
      {
        path: 'experiment-compare',
        name: 'experiment-compare',
        component: () => import('../views/compare/ExperimentCompareView.vue'),
        meta: { title: '实验对比工具', icon: 'DataAnalysis', key: 'experiment-compare', roles: ['flight', 'tester', 'admin'] }
      },
      // 数据同化
      {
        path: 'assimilation',
        name: 'assimilation',
        component: () => import('../views/assimilation/DataAssimilationView.vue'),
        meta: { title: '数据同化', icon: 'Connection', key: 'assimilation' }
      },
      // 系统监控
      {
        path: 'monitoring',
        name: 'monitoring',
        component: () => import('../views/monitoring/SystemMonitorView.vue'),
        meta: { title: '系统监控面板', icon: 'DataAnalysis', key: 'monitoring' }
      },
      // 数据库管理
      {
        path: 'database',
        name: 'database',
        component: () => import('../views/database/DatabaseManager.vue'),
        meta: { title: '数据库管理', icon: 'Coin,', key: 'database' }
      },
      // Docker / 服务器状态
      {
        path: 'docker',
        name: 'docker',
        component: () => import('../views/deployment/DockerStatusView.vue'),
        meta: { title: 'Docker / 服务器状态', icon: 'Box', key: 'docker' }
      },
      // Docker 构建可视化
      {
        path: 'docker-build',
        name: 'docker-build',
        component: () => import('../views/deployment/DockerBuildView.vue'),
        meta: { title: 'Docker 构建', icon: 'Box', key: 'docker-build', roles: ['deployment', 'admin'] }
      },
      // API 配置
      {
        path: 'api-config',
        name: 'api-config',
        component: () => import('../views/config/ApiConfigView.vue'),
        meta: { title: '气象模型 API 配置', icon: 'Setting', key: 'api-config' }
      },
      // 权限模板管理（仅管理员）
      {
        path: 'permission-templates',
        name: 'permission-templates',
        component: () => import('../views/permission/PermissionTemplateView.vue'),
        meta: {
          title: '权限模板管理',
          icon: 'Key',
          key: 'permission-templates',
          adminOnly: true
        }
      },
      // 低空 UTM 对接
      {
        path: 'utm-integration',
        name: 'utm-integration',
        component: () => import('../views/utm/UtmIntegrationView.vue'),
        meta: {
          title: '低空 UTM 对接',
          icon: 'Connection',
          key: 'utm-integration',
          roles: ['production', 'flight', 'admin']
        }
      },
      // 任务报告中心
      {
        path: 'task-report',
        name: 'task-report',
        component: () => import('../views/reports/TaskReportView.vue'),
        meta: {
          title: '任务报告中心',
          icon: 'Document',
          key: 'task-report',
          roles: ['production', 'flight', 'admin']
        }
      },
      // 气象站点管理
      {
        path: 'weather-station',
        name: 'weather-station',
        component: () => import('../views/weather/WeatherStationView.vue'),
        meta: {
          title: '气象站点管理',
          icon: 'Location',
          key: 'weather-station',
          roles: ['tester', 'deployment', 'admin']
        }
      },
      // 适航性评估
      {
        path: 'airworthiness',
        name: 'airworthiness',
        component: () => import('../views/airworthiness/AirworthinessView.vue'),
        meta: {
          title: '适航性评估',
          icon: 'Checked',
          key: 'airworthiness',
          roles: ['flight', 'tester', 'admin']
        }
      },
      // 参数敏感性分析
      {
        path: 'sensitivity-analysis',
        name: 'sensitivity-analysis',
        component: () => import('../views/sensitivity/SensitivityAnalysisView.vue'),
        meta: {
          title: '参数敏感性分析',
          icon: 'DataLine',
          key: 'sensitivity-analysis',
          roles: ['flight', 'tester', 'admin']
        }
      },
      // 设置
      {
        path: 'settings',
        name: 'settings',
        component: () => import('../views/settings/SettingsView.vue'),
        meta: { title: '设置', icon: 'Tools', key: 'settings' }
      },
      // 主题定制
      {
        path: 'theme-customizer',
        name: 'theme-customizer',
        component: () => import('../views/settings/ThemeCustomizer.vue'),
        meta: { title: '主题定制', icon: 'MagicStick', key: 'theme-customizer', roles: ['user','production','flight','tester','deployment','admin'] }
      },
      // 使用文档
      {
        path: 'docs',
        name: 'docs',
        component: () => import('../views/settings/DocsView.vue'),
        meta: { title: '使用文档', icon: 'Document', key: 'docs' }
      },
      {
        path: 'permission-debug',
        name: 'permission-debug',
        component: () => import('../views/debug/PermissionDebugView.vue'),
        meta: {
          title: '权限调试',
          icon: 'MagicStick',
          key: 'permission-debug',
          roles: ['admin']
        }
      }
    ]
  },

  // 权限不足
  {
    path: '/permission-denied',
    name: 'permission-denied',
    component: () => import('../views/PermissionDenied.vue'),
    meta: { public: true, title: '权限不足', hideLayout: false }
  },

  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../views/NotFound.vue'),
    meta: { public: true, title: '页面未找到', hideLayout: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// ===== 路由守卫 =====
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const appStore = useAppStore()

  // 初始化 store（仅首次调用）
  authStore.initFromStorage()

  // 设置页面标题
  if (to.meta?.title) {
    document.title = `${to.meta.title} - 基于 WRF 气象驱动的无人机路径规划系统`
  }

  // 公开路由：直接放行
  if (to.meta?.public) {
    // 已登录用户访问 login/register 时，跳转至默认首页
    if (authStore.isLoggedIn && ['login', 'register', 'forgot-password'].includes(to.name)) {
      const defaultPath = '/' + appStore.getDefaultRoute(authStore.role)
      next(defaultPath)
      return
    }
    next()
    return
  }

  // 未登录：重定向到登录
  if (!authStore.isLoggedIn) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  // 已登录：检查 adminOnly 限制
  if (to.meta?.adminOnly && authStore.role !== 'admin') {
    next({ name: 'permission-denied', query: { route: to.path } })
    return
  }

  // 已登录：检查路由权限
  const routeKey = to.meta?.key
  if (routeKey && !authStore.hasRouteAccess(routeKey)) {
    // 权限不足
    next({ name: 'permission-denied', query: { route: to.path } })
    return
  }

  next()
})

export default router
