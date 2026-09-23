<script setup>
import { useTheme } from '../composables/useTheme'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import UiButton from '../components/ui/UiButton.vue'
import UiField from '../components/ui/UiField.vue'
import { useAuthStore } from '../stores/auth'

const theme = useTheme()

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)

async function submit() {
  busy.value = true
  error.value = ''
  try {
    await auth.login(email.value, password.value)
    router.push(typeof route.query.redirect === 'string' ? route.query.redirect : { name: 'home' })
  } catch (err) {
    error.value = err.message || 'Login failed'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <div class="card login-card">
      <div class="logo">
        <img :src="theme.isDark.value ? '/mark-dark.svg' : '/favicon.svg'" alt="" class="logo-mark" width="88" height="84" />
        <span class="logo-word">Pozzy</span>
      </div>
      <h1>Log in</h1>
      <form class="login" @submit.prevent="submit">
        <UiField label="Email"><input v-model="email" type="email" autocomplete="username" required /></UiField>
        <UiField label="Password" :error="error"><input v-model="password" type="password" autocomplete="current-password" required /></UiField>
        <UiButton type="submit" variant="primary" :loading="busy" block>Log in</UiButton>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-wrap { display: flex; justify-content: center; padding-top: var(--sp-12); }
.login-card { width: 100%; max-width: 380px; display: flex; flex-direction: column; gap: var(--sp-5); }
.logo { display: flex; flex-direction: column; align-items: center; gap: var(--sp-2); margin: var(--sp-2) auto 0; }
.logo-mark { width: 88px; height: auto; }
.logo-word { font-weight: 600; font-size: var(--fs-xl); letter-spacing: -0.01em; color: var(--ink); }
h1 { font-size: var(--fs-xl); text-align: center; }
.login { display: flex; flex-direction: column; gap: var(--sp-3); }
</style>
