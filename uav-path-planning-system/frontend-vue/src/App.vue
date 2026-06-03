<template>
  <a-layout style="min-height: 100vh">
    <!-- 顶部导航栏 -->
    <a-layout-header class="header">
      <div class="logo">{{ $t('title') }}</div>
      <a-menu
        mode="horizontal"
        :selected-keys="[currentRoute]"
        class="nav-menu"
      >
        <a-menu-item key="/">
          <template #icon>
            <HomeOutlined />
          </template>
          {{ $t('nav.home') }}
        </a-menu-item>
        <a-menu-item key="/path-planning">
          <template #icon>
            <OrderedListOutlined />
          </template>
          {{ $t('nav.planning') }}
        </a-menu-item>
        <a-menu-item key="/weather">
          <template #icon>
            <CloudOutlined />
          </template>
          {{ $t('nav.weather') }}
        </a-menu-item>
        <a-menu-item key="/tasks">
          <template #icon>
            <CheckCircleOutlined />
          </template>
          {{ $t('nav.tasks') }}
        </a-menu-item>
        <a-menu-item key="/drones">
          <template #icon>
            <RocketOutlined />
          </template>
          {{ $t('nav.drones') }}
        </a-menu-item>
        <a-menu-item key="/history">
          <template #icon>
            <HistoryOutlined />
          </template>
          {{ $t('nav.history') }}
        </a-menu-item>
        <a-menu-item key="/data-sources">
          <template #icon>
            <DatabaseOutlined />
          </template>
          {{ $t('nav.dataSources') }}
        </a-menu-item>
        <a-menu-item key="/monitoring">
          <template #icon>
            <DashboardOutlined />
          </template>
          {{ $t('nav.monitoring') }}
        </a-menu-item>
        <a-menu-item key="/example">
          <template #icon>
            <BookOutlined />
          </template>
          {{ $t('nav.cockpit') }}
        </a-menu-item>
      </a-menu>
      <LanguageSwitcher />
    </a-layout-header>

    <!-- 内容区域 -->
    <a-layout-content class="content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </a-layout-content>

    <!-- 底部 -->
    <a-layout-footer class="footer">
      {{ $t('title') }} ©2024
    </a-layout-footer>
  </a-layout>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import {
  HomeOutlined,
  OrderedListOutlined,
  CloudOutlined,
  CheckCircleOutlined,
  RocketOutlined,
  HistoryOutlined,
  DatabaseOutlined,
  DashboardOutlined,
  BookOutlined
} from '@ant-design/icons-vue'

const route = useRoute()
const currentRoute = ref('/')

watch(() => route.path, (newPath) => {
  currentRoute.value = newPath
}, { immediate: true })
</script>

<style scoped>
.header {
  display: flex;
  align-items: center;
  background: #001529;
  padding: 0 24px;
}

.logo {
  color: #fff;
  font-size: 20px;
  font-weight: bold;
  margin-right: 30px;
}

.nav-menu {
  flex: 1;
  background: transparent;
}

.content {
  padding: 24px;
  margin: 0;
  min-height: 280px;
  background: #f5f5f5;
}

.footer {
  text-align: center;
  background: #fff;
  border-top: 1px solid #e8e8e8;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>