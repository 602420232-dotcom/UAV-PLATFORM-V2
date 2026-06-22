import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import App from './App.vue'
import router from './router'
import { permission } from './directives/permission'

// 全局设置 passive 事件监听器，消除 ECharts 等库的性能警告
try {
  const originalAddEventListener = EventTarget.prototype.addEventListener
  EventTarget.prototype.addEventListener = function (
    type: string,
    listener: EventListenerOrEventListenerObject | null,
    options?: boolean | AddEventListenerOptions
  ) {
    const passiveEvents = ['wheel', 'mousewheel', 'touchstart', 'touchmove', 'scroll']
    if (typeof options === 'object' && options !== null && passiveEvents.includes(type)) {
      options = { ...options, passive: true }
    }
    return originalAddEventListener.call(this, type, listener, options)
  }
} catch (e) {
  // ignore
}

const app = createApp(App)

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: undefined }) // 后续可引入中文语言包

// 注册全局权限指令
app.directive('permission', permission)

// 全局错误处理器
app.config.errorHandler = (err, _instance, info) => {
  console.error('[Global Error]', err, info)
  ElMessage.error(`运行时错误: ${err instanceof Error ? err.message : String(err)}`)
}

app.mount('#app')

// 全局样式必须在 Element Plus 之后导入，确保深色主题变量覆盖生效
import './styles/global.css'
