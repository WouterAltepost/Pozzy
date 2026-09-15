<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  PhCalendarBlank,
  PhChartLineUp,
  PhCheckSquare,
  PhClipboardText,
  PhEnvelopeSimple,
  PhGearSix,
  PhGraduationCap,
  PhHouse,
  PhLightning,
  PhList,
  PhMoon,
  PhNote,
  PhSignOut,
  PhSun,
  PhTarget,
  PhTimer,
} from '@phosphor-icons/vue'
import CaptureBar from './components/CaptureBar.vue'
import UiSheet from './components/ui/UiSheet.vue'
import UiToast from './components/ui/UiToast.vue'
import { useTheme } from './composables/useTheme'
import { NAV } from './router'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const menuOpen = ref(false)
const theme = useTheme()

// Icons by route name; labels and order stay in router/index.js.
const ICONS = {
  home: PhHouse,
  agenda: PhCalendarBlank,
  tasks: PhCheckSquare,
  goals: PhTarget,
  mail: PhEnvelopeSimple,
  trackers: PhChartLineUp,
  hours: PhTimer,
  capture: PhLightning,
  study: PhGraduationCap,
  notes: PhNote,
  review: PhClipboardText,
  settings: PhGearSix,
}
const items = computed(() => NAV.map((n) => ({ ...n, icon: ICONS[n.name] })))

async function logout() {
  menuOpen.value = false
  await auth.logout()
  router.push({ name: 'login' })
}

watch(() => route.fullPath, () => (menuOpen.value = false))
</script>

<template>
  <div class="shell">
    <div class="ambient" aria-hidden="true"></div>
    <header class="topbar">
      <RouterLink to="/" class="brand" aria-label="Pozzy home">
        <img src="/favicon.svg" alt="" class="mark" width="26" height="26" />
        <span class="wordmark">Pozzy</span>
      </RouterLink>
      <CaptureBar v-if="auth.isAuthenticated" class="topbar-capture" />
      <div v-if="auth.isAuthenticated" class="topbar-user">
        <span class="topbar-email muted">{{ auth.user?.email }}</span>
        <button type="button" class="icon-btn" :title="theme.isDark.value ? 'Switch to light mode' : 'Switch to dark mode'" :aria-label="theme.isDark.value ? 'Switch to light mode' : 'Switch to dark mode'" @click="theme.toggle()">
          <PhSun v-if="theme.isDark.value" />
          <PhMoon v-else />
        </button>
        <button type="button" class="icon-btn" title="Log out" aria-label="Log out" @click="logout"><PhSignOut /></button>
        <button type="button" class="icon-btn menu-toggle" aria-label="Menu" :aria-expanded="menuOpen" @click="menuOpen = true"><PhList /></button>
      </div>
    </header>

    <div class="body">
      <nav v-if="auth.isAuthenticated" class="rail" aria-label="Main">
        <RouterLink v-for="item in items" :key="item.name" :to="{ name: item.name }" class="nav-item" :class="{ active: route.name === item.name }" :aria-current="route.name === item.name ? 'page' : undefined">
          <component :is="item.icon" class="nav-icon" aria-hidden="true" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
      <main class="page">
        <RouterView v-slot="{ Component }">
          <Transition name="route" mode="out-in">
            <component :is="Component" :key="route.name" />
          </Transition>
        </RouterView>
      </main>
    </div>

    <UiSheet :open="menuOpen" title="Go to" @close="menuOpen = false">
      <nav class="sheet-nav" aria-label="Main">
        <RouterLink v-for="item in items" :key="item.name" :to="{ name: item.name }" class="nav-item" :class="{ active: route.name === item.name }">
          <component :is="item.icon" class="nav-icon" aria-hidden="true" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
      <button type="button" class="sheet-row" @click="theme.toggle()">
        <PhSun v-if="theme.isDark.value" class="nav-icon" /><PhMoon v-else class="nav-icon" />
        {{ theme.isDark.value ? 'Light mode' : 'Dark mode' }}
        <span class="muted small">{{ theme.preference.value === 'system' ? 'following system' : 'set here' }}</span>
      </button>
      <button type="button" class="sheet-row" @click="logout"><PhSignOut class="nav-icon" /> Log out <span class="muted small">{{ auth.user?.email }}</span></button>
    </UiSheet>
    <UiToast />
  </div>
</template>

<style scoped>
.shell { min-height: 100dvh; display: flex; flex-direction: column; }
.route-enter-active { transition: opacity var(--dur-route) var(--ease-out), transform var(--dur-route) var(--ease-spring); }
.route-leave-active { transition: opacity 90ms ease; }
.route-enter-from { opacity: 0; transform: translateY(8px); }
.route-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) { .route-enter-from { transform: none; } }
.topbar {
  position: sticky;
  top: 0;
  z-index: var(--z-bar);
  height: var(--bar-h);
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  padding: 0 var(--sp-5);
  background: color-mix(in srgb, var(--surface) 88%, transparent);
  backdrop-filter: blur(14px) saturate(160%);
  -webkit-backdrop-filter: blur(14px) saturate(160%);
  border-bottom: 1px solid var(--line);
}
@media (prefers-reduced-transparency: reduce) { .topbar { background: var(--surface); backdrop-filter: none; -webkit-backdrop-filter: none; } }
.brand { display: inline-flex; align-items: center; gap: 10px; text-decoration: none; color: var(--ink); flex: none; }
.mark { width: 26px; height: 26px; }
.wordmark { font-weight: 600; letter-spacing: -0.01em; font-size: var(--fs-lg); }
.topbar-capture { flex: 1; display: flex; justify-content: center; min-width: 0; }
.topbar-user { display: flex; align-items: center; gap: var(--sp-1); flex: none; margin-left: auto; }
.topbar-email { font-size: var(--fs-sm); margin-right: var(--sp-2); }
.menu-toggle { display: none; }

.body { display: flex; flex: 1; align-items: stretch; }
.rail {
  position: sticky;
  top: var(--bar-h);
  align-self: flex-start;
  height: calc(100dvh - var(--bar-h));
  width: var(--rail-w);
  flex: none;
  padding: var(--sp-4) var(--sp-3);
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
  border-right: 1px solid var(--line);
}
.page { flex: 1; min-width: 0; width: 100%; }

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 36px;
  padding: 0 var(--sp-3);
  border-radius: var(--r-pill);
  color: var(--ink-2);
  text-decoration: none;
  font-size: var(--fs-base);
  font-weight: 500;
  transition: background-color var(--dur-hover) ease, color var(--dur-hover) ease;
}
.nav-item.active { background: var(--surface-3); color: var(--ink); }
.nav-icon { width: 18px; height: 18px; flex: none; }
@media (hover: hover) and (pointer: fine) { .nav-item:not(.active):hover { background: var(--surface-2); color: var(--ink); } }

.sheet-nav { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; }
.sheet-nav .nav-item { height: 44px; }
.sheet-row { display: flex; align-items: center; gap: 10px; width: 100%; height: 44px; padding: 0 var(--sp-3); border: 0; border-top: 1px solid var(--line); border-radius: 0; background: none; color: var(--ink-2); font-weight: 500; }
.sheet-row:first-of-type { margin-top: var(--sp-3); }
.sheet-row .small { margin-left: auto; font-weight: 400; }

@media (max-width: 1023px) {
  .rail { display: none; }
  .menu-toggle { display: inline-flex; }
}
@media (max-width: 720px) {
  .topbar { padding: 0 var(--sp-4); gap: var(--sp-3); }
  .topbar-email { display: none; }
  .wordmark { display: none; }
}
</style>
