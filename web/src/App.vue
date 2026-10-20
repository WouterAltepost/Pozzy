<script setup>
// App shell. Desktop: one sidebar carries everything (brand, the capture command, grouped
// navigation with eyebrows, the account row); the content area is a quiet canvas with room to
// breathe and no bar glued to the top. Below 1024px Pozzy is the iPhone app (docs/briefs/DESIGN.md,
// iOS layer): an iOS navigation bar with large titles and Back, pages pushed and popped with the
// swipe from the left edge, and a tab bar (Today, Habits, Overview, More).
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  PhCalendarBlank,
  PhChartLineUp,
  PhCheckCircle,
  PhSquaresFour,
  PhCheckSquare,
  PhClipboardText,
  PhEnvelopeSimple,
  PhGearSix,
  PhGraduationCap,
  PhLightning,
  PhMoon,
  PhNote,
  PhSignOut,
  PhSun,
  PhTarget,
  PhTimer,
} from '@phosphor-icons/vue'
import CaptureBar from './components/CaptureBar.vue'
import IosContextMenu from './components/ios/IosContextMenu.vue'
import IosNavBar from './components/ios/IosNavBar.vue'
import IosTabBar from './components/ios/IosTabBar.vue'
import UiToast from './components/ui/UiToast.vue'
import { useMediaQuery } from './composables/useMediaQuery'
import { usePageStack } from './composables/usePageStack'
import { useTheme } from './composables/useTheme'
import { NAV, NAV_GROUPS } from './router'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const theme = useTheme()
const phone = useMediaQuery('(max-width: 1023px)')
const stack = usePageStack(phone)

const ICONS = {
  home: PhCheckCircle,
  overview: PhSquaresFour,
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
const groups = computed(() => NAV_GROUPS.map((g) => ({ ...g, items: g.names.map((n) => items.value.find((i) => i.name === n)).filter(Boolean) })))
const settingsItem = computed(() => items.value.find((i) => i.name === 'settings'))
// The habit detail page lights Habits in the navigation.
const currentName = computed(() => (route.name === 'habit' ? 'trackers' : String(route.name || '')))
const initial = computed(() => (auth.user?.email || '?')[0].toUpperCase())

async function logout() {
  await auth.logout()
  router.push({ name: 'login' })
}

</script>

<template>
  <div class="shell" :class="{ authed: auth.isAuthenticated }">
    <IosNavBar v-if="auth.isAuthenticated" />

    <div class="body">
      <nav v-if="auth.isAuthenticated" class="rail" aria-label="Main">
        <RouterLink to="/" class="brand" aria-label="Pozzy home">
          <img :src="theme.isDark.value ? '/mark-dark.svg' : '/favicon.svg'" alt="" class="mark" width="26" height="26" />
          <span class="wordmark">Pozzy</span>
        </RouterLink>
        <CaptureBar class="rail-capture" />
        <div v-for="g in groups" :key="g.label" class="group">
          <span class="eyebrow group-label">{{ g.label }}</span>
          <RouterLink v-for="item in g.items" :key="item.name" :to="{ name: item.name }" class="nav-item" :class="{ active: currentName === item.name }" :aria-current="currentName === item.name ? 'page' : undefined">
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
          <Transition :name="stack.transitionName.value" :mode="stack.mode.value" @before-leave="stack.onBeforeLeave">
            <component :is="Component" :key="route.name" />
          </Transition>
        </RouterView>
      </main>
    </div>

    <IosTabBar v-if="auth.isAuthenticated" :current="String(route.name || '')" />
    <IosContextMenu />
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

@media (max-width: 1023px) {
  .rail { display: none; }
}
</style>
