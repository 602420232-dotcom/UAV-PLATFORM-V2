<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

if (!authStore.isAuthenticated) {
  router.push('/login')
}
</script>

<template>
  <router-view />
</template>
