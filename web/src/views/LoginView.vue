<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import UiButton from '../components/ui/UiButton.vue'
import UiField from '../components/ui/UiField.vue'
import { useAuthStore } from '../stores/auth'

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
      <img src="/logo.png" alt="Pozzy" class="logo" width="180" />
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
.login-wrap { display: flex; justify-content: center; padding-top: var(--sp-10); }
.login-card { width: 100%; max-width: 360px; display: flex; flex-direction: column; gap: var(--sp-4); }
.logo { width: 180px; height: auto; margin: var(--sp-2) auto 0; }
h1 { font-size: var(--fs-xl); text-align: center; }
.login { display: flex; flex-direction: column; gap: var(--sp-3); }
</style>
