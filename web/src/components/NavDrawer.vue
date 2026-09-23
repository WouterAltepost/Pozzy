<script setup>
// Phone navigation: a 272px drawer from the left with every route in the nav, the theme row and
// log out. Slides in 8px with a fade on ease-out (design: pz-slide 240ms), scrim and Escape close.
import { onBeforeUnmount, watch } from 'vue'
import { PhMoon, PhSignOut, PhSun } from '@phosphor-icons/vue'
import { useTheme } from '../composables/useTheme'

const props = defineProps({ open: { type: Boolean, default: false }, items: { type: Array, default: () => [] }, current: { type: String, default: '' }, email: { type: String, default: '' } })
const emit = defineEmits(['close', 'logout'])
const theme = useTheme()

function onKey(e) {
  if (e.key === 'Escape') emit('close')
}
watch(
  () => props.open,
  (open) => {
    if (open) {
      document.addEventListener('keydown', onKey)
      document.body.style.overflow = 'hidden'
    } else {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  },
)
onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="open" class="drawer-root" role="dialog" aria-modal="true" aria-label="Menu">
        <div class="scrim" @click="emit('close')"></div>
        <nav class="drawer" aria-label="Main">
          <div class="brand">
            <img :src="theme.isDark.value ? '/mark-dark.svg' : '/favicon.svg'" alt="" width="26" height="26" class="mark" />
            <span class="word">Pozzy</span>
          </div>
          <RouterLink v-for="item in items" :key="item.name" :to="{ name: item.name }" class="nav-item" :class="{ active: current === item.name }" :aria-current="current === item.name ? 'page' : undefined" @click="emit('close')">
            <component :is="item.icon" class="nav-icon" aria-hidden="true" />
            <span>{{ item.label }}</span>
          </RouterLink>
          <span class="spacer"></span>
          <button type="button" class="nav-item row" @click="theme.toggle()">
            <PhSun v-if="theme.isDark.value" class="nav-icon" /><PhMoon v-else class="nav-icon" />
            <span>{{ theme.isDark.value ? 'Light mode' : 'Dark mode' }}</span>
          </button>
          <button type="button" class="nav-item row" @click="emit('logout')"><PhSignOut class="nav-icon" /><span>Log out</span></button>
          <span class="email muted small truncate">{{ email }}</span>
        </nav>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.drawer-root { position: fixed; inset: 0; z-index: var(--z-sheet); display: flex; }
.scrim { position: absolute; inset: 0; background: var(--scrim); }
.drawer {
  position: relative; width: 272px; max-width: 84vw; height: 100%;
  background: color-mix(in srgb, var(--surface) 90%, transparent);
  -webkit-backdrop-filter: blur(20px) saturate(160%); backdrop-filter: blur(20px) saturate(160%);
  border-right: 1px solid var(--line); box-shadow: var(--shadow-3);
  padding: calc(env(safe-area-inset-top) + 28px) 12px calc(env(safe-area-inset-bottom) + 20px);
  display: flex; flex-direction: column; gap: 2px; overflow-y: auto;
}
@media (prefers-reduced-transparency: reduce) { .drawer { background: var(--surface); -webkit-backdrop-filter: none; backdrop-filter: none; } }
.brand { display: flex; align-items: center; gap: 10px; padding: 0 12px 14px; }
.mark { width: 26px; height: 26px; }
.word { font-weight: 600; letter-spacing: -0.01em; font-size: var(--fs-lg); }
.nav-item { display: flex; align-items: center; gap: 10px; height: 42px; padding: 0 var(--sp-3); border-radius: var(--r-pill); color: var(--ink-2); text-decoration: none; font-size: var(--fs-base); font-weight: 500; border: 0; background: none; width: 100%; text-align: left; transition: background-color var(--dur-hover) ease, color var(--dur-hover) ease; }
.nav-item.active { background: var(--surface-3); color: var(--ink); }
.nav-item:active { background: var(--surface-2); }
.nav-icon { width: 18px; height: 18px; flex: none; }
.spacer { flex: 1; }
.email { padding: 8px 12px 0; }
.drawer-enter-active .scrim { transition: opacity var(--dur-ui) ease; }
.drawer-leave-active .scrim { transition: opacity var(--dur-hover) ease; }
.drawer-enter-active .drawer { transition: transform var(--dur-panel) var(--ease-out), opacity var(--dur-panel) var(--ease-out); }
.drawer-leave-active .drawer { transition: transform var(--dur-hover) ease, opacity var(--dur-hover) ease; }
.drawer-enter-from .scrim, .drawer-leave-to .scrim { opacity: 0; }
.drawer-enter-from .drawer, .drawer-leave-to .drawer { transform: translateX(-8px); opacity: 0; }
@media (prefers-reduced-motion: reduce) { .drawer-enter-from .drawer, .drawer-leave-to .drawer { transform: none; } }
</style>
