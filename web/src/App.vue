<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import CaptureBar from './components/CaptureBar.vue'
import { NAV } from './router'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const router = useRouter()
const menuOpen = ref(false)

async function logout() {
  menuOpen.value = false
  await auth.logout()
  router.push({ name: 'login' })
}

router.afterEach(() => {
  menuOpen.value = false
})
</script>

<template>
  <header class="topbar">
    <div class="topbar-row">
      <RouterLink to="/" class="brand">Pozzy</RouterLink>
      <CaptureBar v-if="auth.isAuthenticated" class="topbar-capture" />
      <div v-if="auth.isAuthenticated" class="topbar-user">
        <span class="topbar-email">{{ auth.user?.email }}</span>
        <button type="button" @click="logout">Log out</button>
        <button type="button" class="menu-toggle" aria-label="Menu" @click="menuOpen = !menuOpen">&#9776;</button>
      </div>
    </div>
    <nav v-if="auth.isAuthenticated" class="mainnav" :class="{ open: menuOpen }">
      <RouterLink v-for="item in NAV" :key="item.name" :to="{ name: item.name }" :class="{ active: $route.name === item.name }">
        {{ item.label }}
      </RouterLink>
    </nav>
  </header>
  <main class="page">
    <RouterView />
  </main>
</template>
