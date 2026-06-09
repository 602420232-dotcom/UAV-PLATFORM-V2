<template>
  <el-select
    :model-value="currentLocale"
    style="width: 100px"
    size="small"
    @change="switchLanguage"
  >
    <el-option value="zh-CN" label="中文" />
    <el-option value="en-US" label="English" />
  </el-select>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()
const currentLocale = ref(localStorage.getItem('locale') || 'zh-CN')

watch(locale, (newVal) => {
  currentLocale.value = newVal
})

const switchLanguage = (lang) => {
  locale.value = lang
  currentLocale.value = lang
  localStorage.setItem('locale', lang)
}
</script>