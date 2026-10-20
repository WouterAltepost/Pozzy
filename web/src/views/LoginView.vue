<script setup>
import { useTheme } from '../composables/useTheme'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import UiButton from '../components/ui/UiButton.vue'
import UiField from '../components/ui/UiField.vue'
import { useMediaQuery } from '../composables/useMediaQuery'
import { useAuthStore } from '../stores/auth'

const theme = useTheme()

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const email = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)
// Phone: a native sign-in screen. The mark centred, both fields in one grouped plate, one
// full-width filled button.
const phone = useMediaQuery('(max-width: 1023px)')

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
  <div v-if="phone" class="ios-login">
    <div class="brand">
      <img :src="theme.isDark.value ? '/mark-dark.svg' : '/favicon.svg'" alt="" class="brand-mark" width="96" height="92" />
      <h1>Pozzy</h1>
      <p class="lede">Log in to your day</p>
    </div>
    <form class="ios-form" @submit.prevent="submit">
      <div class="plate">
        <input v-model="email" type="email" autocomplete="username" inputmode="email" autocapitalize="off" autocorrect="off" spellcheck="false" placeholder="Email" aria-label="Email" required />
        <input v-model="password" type="password" autocomplete="current-password" placeholder="Password" aria-label="Password" required />
      </div>
      <p v-if="error" class="err" role="alert">{{ error }}</p>
      <button type="submit" class="go" :disabled="busy || !email || !password">{{ busy ? 'Logging in…' : 'Log in' }}</button>
    </form>
  </div>
  <div v-else class="login-wrap">
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

/* iOS layer: the sign-in screen. */
@media (max-width: 1023px) {
  .ios-login { display: flex; flex-direction: column; justify-content: center; min-height: calc(100dvh - 120px); max-width: 420px; margin: 0 auto; padding: var(--sp-8) 0; }
  .brand { display: flex; flex-direction: column; align-items: center; text-align: center; margin-bottom: var(--sp-10); }
  .brand-mark { width: 96px; height: auto; margin-bottom: var(--sp-4); }
  .brand h1 { font-size: 2.125rem; font-weight: 700; }
  .lede { margin: 4px 0 0; font-size: 1.0625rem; color: var(--ink-3); }
  .ios-form { display: flex; flex-direction: column; gap: var(--sp-4); }
  .plate { position: relative; display: flex; flex-direction: column; background: var(--surface); border-radius: var(--r-lg); overflow: hidden; }
  .plate input { width: 100%; height: 50px; padding: 0 16px; background: transparent; border-radius: 0; font-size: 1.0625rem; }
  .plate input:focus-visible { box-shadow: none; }
  .plate input + input { border-top: 0.5px solid var(--line-2); }
  .err { margin: -4px 16px 0; font-size: 0.8125rem; color: var(--danger); }
  .go { height: 50px; border: 0; border-radius: 12px; background: var(--ink); color: var(--on-ink); font: inherit; font-size: 1.0625rem; font-weight: 600; }
  .go:active:not(:disabled) { opacity: 0.7; }
  .go:disabled { opacity: 0.4; }
}
</style>
