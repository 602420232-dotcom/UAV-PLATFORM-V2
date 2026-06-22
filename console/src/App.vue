<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import ErrorBoundary from '@/components/common/ErrorBoundary.vue'

const authStore = useAuthStore()
const router = useRouter()

if (!authStore.isAuthenticated) {
  router.push('/login')
}
</script>

<template>
  <ErrorBoundary>
    <router-view />
  </ErrorBoundary>
</template>
