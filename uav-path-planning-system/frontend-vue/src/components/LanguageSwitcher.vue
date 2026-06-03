<template>
  <a-select
    :value="currentLocale"
    style="width: 120px"
    @change="switchLanguage"
  >
    <a-select-option value="zh-CN">中文</a-select-option>
    <a-select-option value="en-US">English</a-select-option>
  </a-select>
</template>

<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()
const currentLocale = ref(localStorage.getItem('locale') || 'zh-CN')

const switchLanguage = (lang) => {
  locale.value = lang
  currentLocale.value = lang
  localStorage.setItem('locale', lang)
}
</script>
