<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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
  <div class="card">
    <h2>Log in</h2>
    <form class="login" @submit.prevent="submit">
      <input v-model="email" type="email" placeholder="Email" autocomplete="username" required />
      <input v-model="password" type="password" placeholder="Password" autocomplete="current-password" required />
      <button type="submit" :disabled="busy">{{ busy ? 'Logging in...' : 'Log in' }}</button>
      <p v-if="error" class="error">{{ error }}</p>
    </form>
  </div>
</template>
