<script setup>
// The More tab: every module that is not a tab, as inset grouped rows with a coloured symbol
// tile and a chevron (the iOS Settings pattern), then Settings, appearance and log out. Each row
// pushes its page, so Back returns here.
import { useRouter } from 'vue-router'
import {
  PhCalendarBlank, PhCaretRight, PhCheckSquare, PhClipboardText, PhEnvelopeSimple, PhGearSix, PhGraduationCap,
  PhLightning, PhMoon, PhTarget, PhTimer,
} from '@phosphor-icons/vue'
import { useTheme } from '../composables/useTheme'
import { tick } from '../lib/haptics'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const theme = useTheme()

// Tile colours are iOS system colours, one per row, like the Settings app.
const groups = [
  [
    { name: 'agenda', label: 'Agenda', icon: PhCalendarBlank, color: '#FF3B30' },
    { name: 'tasks', label: 'Tasks', icon: PhCheckSquare, color: '#007AFF' },
    { name: 'goals', label: 'Goals', icon: PhTarget, color: '#FF9500' },
    { name: 'review', label: 'Weekly review', icon: PhClipboardText, color: '#AF52DE' },
  ],
  [
    { name: 'mail', label: 'Mail', icon: PhEnvelopeSimple, color: '#34AADC' },
    { name: 'hours', label: 'Hours', icon: PhTimer, color: '#5856D6' },
    { name: 'capture', label: 'Capture', icon: PhLightning, color: '#FFCC00' },
    { name: 'study', label: 'Study', icon: PhGraduationCap, color: '#34C759' },
  ],
]

function toggleTheme() {
  tick()
  theme.toggle()
}
async function logout() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="more">
    <h1>More</h1>
    <ul v-for="(g, i) in groups" :key="i" class="group">
      <li v-for="item in g" :key="item.name">
        <RouterLink :to="{ name: item.name }" class="cell pressable">
          <span class="tile" :style="{ background: item.color }"><component :is="item.icon" weight="fill" /></span>
          <span class="lbl">{{ item.label }}</span>
          <PhCaretRight class="chev" weight="bold" aria-hidden="true" />
        </RouterLink>
      </li>
    </ul>
    <ul class="group">
      <li>
        <RouterLink :to="{ name: 'settings' }" class="cell pressable">
          <span class="tile" style="background: #8E8E93"><PhGearSix weight="fill" /></span>
          <span class="lbl">Settings</span>
          <PhCaretRight class="chev" weight="bold" aria-hidden="true" />
        </RouterLink>
      </li>
      <li>
        <label class="cell">
          <span class="tile" style="background: #5856D6"><PhMoon weight="fill" /></span>
          <span class="lbl">Dark mode</span>
          <input type="checkbox" role="switch" :checked="theme.isDark.value" @change="toggleTheme" />
        </label>
      </li>
    </ul>
    <ul class="group">
      <li>
        <button type="button" class="cell pressable danger" @click="logout"><span class="lbl">Log out</span></button>
      </li>
    </ul>
    <p class="foot">{{ auth.user?.email }}</p>
  </div>
</template>

<style scoped>
.more { max-width: 680px; margin: 0 auto; }
h1 { margin: 4px 0 var(--sp-5); }
.group { background: var(--surface); border-radius: var(--r-lg); overflow: hidden; margin-bottom: var(--sp-8); }
.cell { position: relative; display: flex; align-items: center; gap: 14px; width: 100%; min-height: 44px; padding: 6px 16px; border: 0; background: none; color: var(--ink); text-decoration: none; font: inherit; font-size: 1.0625rem; text-align: left; }
.cell:hover { text-decoration: none; }
li + li .cell::before { content: ''; position: absolute; top: 0; left: 59px; right: 0; height: 0.5px; background: var(--line-2); }
.tile { display: inline-grid; place-items: center; width: 29px; height: 29px; border-radius: 7px; color: #fff; flex: none; }
.tile :deep(svg) { width: 18px; height: 18px; }
.lbl { flex: 1; min-width: 0; }
.chev { width: 14px; height: 14px; color: var(--ink-4); flex: none; }
.danger { color: var(--danger); justify-content: center; }
.danger .lbl { flex: none; }
.foot { text-align: center; font-size: var(--fs-sm); color: var(--ink-3); margin-top: calc(var(--sp-6) * -1); }
</style>
