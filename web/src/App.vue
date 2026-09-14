<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function logout() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <header class="topbar">
    <RouterLink to="/" class="brand">Pozzy</RouterLink>
    <div v-if="auth.isAuthenticated" class="topbar-user">
      <span>{{ auth.user?.email }}</span>
      <button type="button" @click="logout">Log out</button>
    </div>
  </header>
  <main class="page">
    <RouterView />
  </main>
</template>
