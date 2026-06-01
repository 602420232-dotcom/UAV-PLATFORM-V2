import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import axios from 'axios'

// 配置axios
axios.defaults.baseURL = '/api'
axios.defaults.timeout = 30000

// 创建应用
const app = createApp(App)

// 使用插件
app.use(createPinia())
app.use(router)
app.use(Antd)

// 全局属性
app.config.globalProperties.$axios = axios

// 挂载应用
app.config.errorHandler = (err, instance, info) => {
  console.error('[Global Error]', { message: err?.message, component: instance?.$options?.name, info })
}
app.mount('#app')