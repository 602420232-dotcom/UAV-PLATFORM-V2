import 'element-plus/dist/index.css'
import '../src/styles/index.css'
import '../src/styles/theme-vars.css'

// 初始化 data-theme 为 light
if (typeof document !== 'undefined') {
  document.documentElement.setAttribute('data-theme', 'light')
}

export const parameters = {
  actions: { argTypesRegex: '^on[A-Z].*' },
  controls: { matchers: { color: /(background|color)$/i, date: /Date$/ } },
  backgrounds: {
    default: '浅色',
    values: [
      { name: '浅色', value: '#f5f7fa' },
      { name: '深色', value: '#0f172a' },
      { name: '品牌', value: '#0c1a2f' },
      { name: '高对比度', value: '#000000' }
    ]
  }
}

export const globalTypes = {
  theme: {
    name: '主题',
    description: '应用主题',
    defaultValue: 'light',
    toolbar: {
      icon: 'paintbrush',
      items: [
        { value: 'light', title: '浅色' },
        { value: 'dark', title: '深色' },
        { value: 'brand', title: '品牌' },
        { value: 'highContrast', title: '高对比度' }
      ]
    }
  }
}

const withTheme = (Story, context) => {
  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('data-theme', context.globals.theme)
  }
  return { template: '<story />' }
}

export const decorators = [withTheme]
