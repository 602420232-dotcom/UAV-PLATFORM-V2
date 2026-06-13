<script setup lang="ts">
import { useAppStore } from '@/stores/app'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'

const appStore = useAppStore()
</script>

<template>
  <el-container class="app-layout">
    <Sidebar />
    <el-container class="main-container">
      <Header />
      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.app-layout {
  height: 100vh;
  width: 100%;
}

.main-container {
  flex-direction: column;
  overflow: hidden;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: var(--color-bg);
}
</style>
