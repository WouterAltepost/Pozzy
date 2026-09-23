<script setup>
// App shell. Desktop: a macOS window, translucent sidebar (source list) at the leading edge,
// a toolbar across the top with the capture command and account controls. Phone: a floating
// tab bar at the bottom with four destinations and More, the toolbar holds capture and the
// appearance toggle. Chrome is the only translucent layer; content scrolls underneath it.
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
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
  PhMoon,
  PhNote,
  PhSignOut,
  PhSun,
  PhTarget,
  PhTimer,
} from '@phosphor-icons/vue'
import CaptureBar from './components/CaptureBar.vue'
import MoreSheet from './components/MoreSheet.vue'
import TabBar from './components/TabBar.vue'
import UiToast from './components/ui/UiToast.vue'
import { useTheme } from './composables/useTheme'
import { NAV } from './router'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const moreOpen = ref(false)
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
const items = computed(() => NAV.filter((n) => !n.hidden).map((n) => ({ ...n, icon: ICONS[n.name] })))
const TAB_NAMES = new Set(['home', 'agenda', 'tasks', 'mail'])
const moreItems = computed(() => items.value.filter((n) => !TAB_NAMES.has(n.name)))

async function logout() {
  moreOpen.value = false
  await auth.logout()
  router.push({ name: 'login' })
}

watch(() => route.fullPath, () => (moreOpen.value = false))

// Scroll edge: the bar is a floating material; its hairline shows only when content is under it.
const scrolled = ref(false)
function onScroll() {
  scrolled.value = window.scrollY > 2
}
onMounted(() => {
  onScroll()
  window.addEventListener('scroll', onScroll, { passive: true })
})
onBeforeUnmount(() => window.removeEventListener('scroll', onScroll))
</script>

<template>
  <div class="shell">
    <header class="topbar" :class="{ scrolled }">
      <RouterLink to="/" class="brand" aria-label="Pozzy home">
        <img :src="theme.isDark.value ? '/mark-dark.svg' : '/favicon.svg'" alt="" class="mark" width="24" height="24" />
        <span class="wordmark">Pozzy</span>
      </RouterLink>
      <CaptureBar v-if="auth.isAuthenticated" class="topbar-capture" />
      <div v-if="auth.isAuthenticated" class="topbar-user">
        <span class="topbar-email muted">{{ auth.user?.email }}</span>
        <button type="button" class="icon-btn" :title="theme.isDark.value ? 'Switch to light mode' : 'Switch to dark mode'" :aria-label="theme.isDark.value ? 'Switch to light mode' : 'Switch to dark mode'" @click="theme.toggle()">
          <PhSun v-if="theme.isDark.value" />
          <PhMoon v-else />
        </button>
        <button type="button" class="icon-btn logout" title="Log out" aria-label="Log out" @click="logout"><PhSignOut /></button>
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

    <TabBar v-if="auth.isAuthenticated" class="tabs" :current="String(route.name || '')" :more-active="moreOpen" @more="moreOpen = true" />
    <MoreSheet :open="moreOpen" :items="moreItems" :current="String(route.name || '')" :email="auth.user?.email || ''" @close="moreOpen = false" @logout="logout" />
    <UiToast />
  </div>
</template>

<style scoped>
.shell { min-height: 100dvh; display: flex; flex-direction: column; }
.route-enter-active { transition: opacity var(--dur-route) var(--ease-out), transform var(--dur-route) var(--ease-spring); }
.route-leave-active { transition: opacity 90ms ease; }
.route-enter-from { opacity: 0; transform: translateY(6px); }
.route-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) { .route-enter-from { transform: none; } }

/* Toolbar: chrome material with a scroll edge instead of a permanent rule. */
.topbar {
  position: sticky;
  top: 0;
  z-index: var(--z-bar);
  height: calc(var(--bar-h) + env(safe-area-inset-top));
  padding: env(safe-area-inset-top) var(--sp-5) 0;
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  background: var(--material);
  -webkit-backdrop-filter: var(--material-blur);
  backdrop-filter: var(--material-blur);
  border-bottom: 0.5px solid transparent;
  transition: border-color var(--dur-ui) ease;
}
.topbar.scrolled { border-bottom-color: var(--line); }
@media (prefers-reduced-transparency: reduce) { .topbar { background: var(--surface); backdrop-filter: none; -webkit-backdrop-filter: none; } }
.brand { display: inline-flex; align-items: center; gap: 8px; text-decoration: none; color: var(--ink); flex: none; width: calc(var(--rail-w) - var(--sp-5)); }
.brand:hover { text-decoration: none; }
.mark { width: 24px; height: 24px; }
.wordmark { font-weight: 600; font-size: var(--fs-lg); }
.topbar-capture { flex: 1; display: flex; justify-content: center; min-width: 0; }
.topbar-user { display: flex; align-items: center; gap: var(--sp-1); flex: none; margin-left: auto; }
.topbar-email { font-size: var(--fs-sm); margin-right: var(--sp-2); }

.body { display: flex; flex: 1; align-items: stretch; }
/* Sidebar: a source list on the sidebar material, 28 px rows, tinted symbols, grey selection. */
.rail {
  position: sticky;
  top: var(--bar-h);
  align-self: flex-start;
  height: calc(100dvh - var(--bar-h));
  width: var(--rail-w);
  flex: none;
  padding: var(--sp-3) var(--sp-3);
  display: flex;
  flex-direction: column;
  gap: 1px;
  overflow-y: auto;
  background: color-mix(in srgb, var(--bg) 60%, var(--surface-2));
  border-right: 0.5px solid var(--line);
}
.page { flex: 1; min-width: 0; width: 100%; padding-bottom: env(safe-area-inset-bottom); }

.nav-item {
  display: flex;
  align-items: center;
  gap: 9px;
  height: 30px;
  padding: 0 10px;
  border-radius: var(--r-sm);
  color: var(--ink);
  text-decoration: none;
  font-size: var(--fs-md);
  font-weight: 500;
  transition: background-color var(--dur-hover) ease;
}
.nav-item:hover { text-decoration: none; }
.nav-item.active { background: var(--surface-3); }
.nav-icon { width: 17px; height: 17px; flex: none; color: var(--brand); }
@media (hover: hover) and (pointer: fine) { .nav-item:not(.active):hover { background: var(--surface-2); } }
.tabs { display: none; }

@media (max-width: 1023px) {
  .rail { display: none; }
  .brand { width: auto; }
  .logout { display: none; }
}
/* Phone: tab bar navigation, toolbar holds capture and appearance, the mark lives in the tab bar's More sheet. */
@media (max-width: 720px) {
  .topbar { padding-left: var(--sp-3); padding-right: var(--sp-3); gap: 10px; }
  .topbar-email { display: none; }
  .brand { display: none; }
  .topbar-capture { justify-content: stretch; }
  .topbar-user { margin-left: 0; }
  .tabs { display: flex; }
}
</style>
