import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import * as parserVue from 'vue-eslint-parser'
import tseslint from '@typescript-eslint/eslint-plugin'
import tsparser from '@typescript-eslint/parser'
import prettierConfig from 'eslint-config-prettier'
import globals from 'globals'

export default [
  // 忽略目录（必须放在最前面）
  {
    ignores: ['dist/', 'node_modules/', 'src/__tests__/', 'src/mock/'],
  },

  // 浏览器全局变量（所有文件）
  {
    files: ['**/*'],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
        WebSocket: 'readonly',
        Event: 'readonly',
        CloseEvent: 'readonly',
        MessageEvent: 'readonly',
        EventTarget: 'readonly',
        EventListenerOrEventListenerObject: 'readonly',
        AddEventListenerOptions: 'readonly',
        HTMLElement: 'readonly',
        setTimeout: 'readonly',
        setInterval: 'readonly',
        clearTimeout: 'readonly',
        clearInterval: 'readonly',
        console: 'readonly',
      },
    },
  },

  // 基础 JS 规则
  js.configs.recommended,

  // TypeScript 解析器配置
  {
    files: ['**/*.ts', '**/*.tsx', '**/*.vue'],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
    },
    plugins: {
      '@typescript-eslint': tseslint,
    },
    rules: {
      // TypeScript 规则
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
    },
  },

  // Vue 插件配置
  ...pluginVue.configs['flat/essential'],

  {
    files: ['**/*.vue'],
    languageOptions: {
      parser: parserVue,
      parserOptions: {
        parser: tsparser,
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
    },
    rules: {
      'vue/multi-word-component-names': 'off',
      'vue/no-v-html': 'warn',
    },
  },

  // 通用规则
  {
    rules: {
      'no-console': 'warn',
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
    },
  },

  // Prettier 兼容（必须放在最后，关闭与 Prettier 冲突的规则）
  prettierConfig,
]
