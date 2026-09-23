<script setup>
// App shell. Desktop: one sidebar carries everything (brand, the capture command, grouped
// navigation with eyebrows, the account row); the content area is a quiet canvas with room to
// breathe and no bar glued to the top. Phone: a slim toolbar with the capture command and a
// floating dark pill for navigation at the bottom.
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
// Sidebar groups: what you look at, what you plan, what you track.
const GROUPS = [
  { label: 'Today', names: ['home', 'agenda', 'tasks', 'mail'] },
  { label: 'Plan', names: ['goals', 'review', 'capture'] },
  { label: 'Track', names: ['trackers', 'hours', 'study'] },
]
const groups = computed(() => GROUPS.map((g) => ({ ...g, items: g.names.map((n) => items.value.find((i) => i.name === n)).filter(Boolean) })))
const settingsItem = computed(() => items.value.find((i) => i.name === 'settings'))
const TAB_NAMES = new Set(['home', 'agenda', 'tasks', 'mail'])
const moreItems = computed(() => items.value.filter((n) => !TAB_NAMES.has(n.name)))
const initial = computed(() => (auth.user?.email || '?')[0].toUpperCase())

async function logout() {
  moreOpen.value = false
  await auth.logout()
  router.push({ name: 'login' })
}

watch(() => route.fullPath, () => (moreOpen.value = false))

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
  <div class="shell" :class="{ authed: auth.isAuthenticated }">
    <header v-if="auth.isAuthenticated" class="topbar" :class="{ scrolled }">
      <CaptureBar class="topbar-capture" />
      <button type="button" class="icon-btn" :aria-label="theme.isDark.value ? 'Switch to light mode' : 'Switch to dark mode'" @click="theme.toggle()">
        <PhSun v-if="theme.isDark.value" />
        <PhMoon v-else />
      </button>
    </header>

    <div class="body">
      <nav v-if="auth.isAuthenticated" class="rail" aria-label="Main">
        <RouterLink to="/" class="brand" aria-label="Pozzy home">
          <img :src="theme.isDark.value ? '/mark-dark.svg' : '/favicon.svg'" alt="" class="mark" width="26" height="26" />
          <span class="wordmark">Pozzy</span>
        </RouterLink>
        <CaptureBar class="rail-capture" />
        <div v-for="g in groups" :key="g.label" class="group">
          <span class="eyebrow group-label">{{ g.label }}</span>
          <RouterLink v-for="item in g.items" :key="item.name" :to="{ name: item.name }" class="nav-item" :class="{ active: route.name === item.name }" :aria-current="route.name === item.name ? 'page' : undefined">
            <component :is="item.icon" class="nav-icon" aria-hidden="true" />
            <span>{{ item.label }}</span>
          </RouterLink>
        </div>
        <span class="spacer"></span>
        <RouterLink v-if="settingsItem" :to="{ name: 'settings' }" class="nav-item" :class="{ active: route.name === 'settings' }">
          <component :is="settingsItem.icon" class="nav-icon" aria-hidden="true" />
          <span>Settings</span>
        </RouterLink>
        <div class="account">
          <span class="avatar" aria-hidden="true">{{ initial }}</span>
          <span class="email truncate">{{ auth.user?.email }}</span>
          <button type="button" class="icon-btn" :title="theme.isDark.value ? 'Switch to light mode' : 'Switch to dark mode'" :aria-label="theme.isDark.value ? 'Switch to light mode' : 'Switch to dark mode'" @click="theme.toggle()">
            <PhSun v-if="theme.isDark.value" />
            <PhMoon v-else />
          </button>
          <button type="button" class="icon-btn" title="Log out" aria-label="Log out" @click="logout"><PhSignOut /></button>
        </div>
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
.route-leave-active { transition: opacity 100ms ease; }
.route-enter-from { opacity: 0; transform: translateY(8px); }
.route-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) { .route-enter-from { transform: none; } }

/* The phone toolbar. Hidden on the desktop, where the sidebar carries the same commands. */
.topbar { display: none; }

.body { display: flex; flex: 1; align-items: stretch; }
.rail {
  position: sticky;
  top: 0;
  align-self: flex-start;
  height: 100dvh;
  width: var(--rail-w);
  flex: none;
  padding: var(--sp-6) var(--sp-4) var(--sp-5);
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  overflow-y: auto;
  border-right: 1px solid var(--line);
}
.brand { display: flex; align-items: center; gap: 10px; padding: 0 var(--sp-2) var(--sp-4); text-decoration: none; color: var(--ink); }
.brand:hover { text-decoration: none; }
.mark { width: 26px; height: 26px; }
.wordmark { font-weight: 650; font-size: var(--fs-lg); letter-spacing: -0.02em; }
.rail-capture { margin-bottom: var(--sp-4); }
.group { display: flex; flex-direction: column; gap: 1px; margin-bottom: var(--sp-3); }
.group-label { padding: 0 var(--sp-2) var(--sp-2); }
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 34px;
  padding: 0 var(--sp-2);
  border-radius: var(--r-md);
  color: var(--ink-2);
  text-decoration: none;
  font-size: var(--fs-base);
  font-weight: 500;
  transition: background-color var(--dur-hover) ease, color var(--dur-hover) ease, box-shadow var(--dur-hover) ease;
}
.nav-item:hover { text-decoration: none; }
.nav-item.active { background: var(--surface); color: var(--ink); box-shadow: inset 0 1px 0 var(--edge), 0 1px 2px rgb(14 17 32 / 0.05), 0 0 0 1px var(--line); }
.nav-item.active .nav-icon { color: var(--brand); }
.nav-icon { width: 18px; height: 18px; flex: none; color: var(--ink-3); transition: color var(--dur-hover) ease; }
@media (hover: hover) and (pointer: fine) { .nav-item:not(.active):hover { background: var(--surface-2); color: var(--ink); } }
.spacer { flex: 1; }
.account { display: flex; align-items: center; gap: var(--sp-2); padding: var(--sp-3) var(--sp-2) 0; border-top: 1px solid var(--line); margin-top: var(--sp-2); }
.avatar { width: 28px; height: 28px; border-radius: 50%; display: inline-grid; place-items: center; background: linear-gradient(180deg, var(--brand-2), var(--brand)); color: #fff; font-size: var(--fs-sm); font-weight: 600; box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.3); flex: none; }
.email { flex: 1; min-width: 0; font-size: var(--fs-sm); color: var(--ink-3); }
.page { flex: 1; min-width: 0; width: 100%; }
.tabs { display: none; }

@media (max-width: 1023px) {
  .rail { display: none; }
  .topbar {
    position: sticky;
    top: 0;
    z-index: var(--z-bar);
    height: calc(var(--bar-h) + env(safe-area-inset-top));
    padding: env(safe-area-inset-top) var(--sp-4) 0;
    display: flex;
    align-items: center;
    gap: var(--sp-2);
    background: var(--material);
    -webkit-backdrop-filter: var(--material-blur);
    backdrop-filter: var(--material-blur);
    border-bottom: 1px solid transparent;
    transition: border-color var(--dur-ui) ease;
  }
  .topbar.scrolled { border-bottom-color: var(--line); }
  @media (prefers-reduced-transparency: reduce) { .topbar { background: var(--bg); backdrop-filter: none; -webkit-backdrop-filter: none; } }
  .topbar-capture { flex: 1; min-width: 0; }
  .tabs { display: flex; }
}
</style>
