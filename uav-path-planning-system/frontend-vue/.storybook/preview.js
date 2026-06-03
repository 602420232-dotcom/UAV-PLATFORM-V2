import { setup } from '@storybook/vue3'
import { createI18n } from 'vue-i18n'
import zhCN from '../src/locales/zh-CN'
import enUS from '../src/locales/en-US'

const i18n = createI18n({
  legacy: false,
  locale: 'zh-CN',
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS
  }
})

setup((app) => {
  app.use(i18n)
})

export const parameters = {
  actions: { argTypesRegex: "^on[A-Z].*" },
  controls: {
    matchers: {
      color: /(background|color)$/i,
      date: /Date$/,
    },
  },
}
