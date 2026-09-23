<script setup>
// Phone navigation: a 272px drawer from the left with every route in the nav, the theme row and
// log out. It is a physical sheet: it springs in from the left edge, follows the finger when
// dragged back, resists past its open position, and a flick closes it at the finger's speed.
// It leaves the way it came. Scrim and Escape close it too.
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { PhMoon, PhSignOut, PhSun } from '@phosphor-icons/vue'
import { useDrag } from '../composables/useDrag'
import { useTheme } from '../composables/useTheme'
import { createSpring, project, reducedMotion, rubberband } from '../lib/spring'

const props = defineProps({ open: { type: Boolean, default: false }, items: { type: Array, default: () => [] }, current: { type: String, default: '' }, email: { type: String, default: '' } })
const emit = defineEmits(['close', 'logout'])
const theme = useTheme()

const WIDTH = 272
const mounted = ref(false) // stays true while the exit spring runs
const x = ref(-WIDTH) // translateX of the drawer, 0 = open
const width = () => Math.min(WIDTH, window.innerWidth * 0.84)

const spring = createSpring({
  value: -WIDTH,
  damping: 1,
  response: 0.36,
  onUpdate: (v) => (x.value = v),
  onRest: (v) => {
    if (v <= -width() + 0.5 && !props.open) mounted.value = false
  },
})

function show() {
  mounted.value = true
  document.addEventListener('keydown', onKey)
  document.body.style.overflow = 'hidden'
  nextTick(() => {
    if (spring.value <= -width() + 1) spring.jump(-width())
    spring.set(0)
  })
}
function hide(velocity = 0) {
  document.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
  spring.set(-width(), { velocity: Math.min(velocity, 0) })
  if (reducedMotion()) mounted.value = false
}
function onKey(e) {
  if (e.key === 'Escape') emit('close')
}
watch(
  () => props.open,
  (on) => (on ? show() : hide()),
  { immediate: true },
)
onBeforeUnmount(() => {
  spring.stop()
  document.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})

// Drag: the drawer sticks to the finger; past the open edge it rubber-bands.
let startX = 0
const drag = useDrag({
  axis: 'x',
  onStart: () => {
    startX = spring.value
    spring.stop()
  },
  onMove: ({ dx }) => {
    const raw = startX + dx
    spring.jump(raw > 0 ? rubberband(raw, width()) : Math.max(-width(), raw))
  },
  onEnd: ({ vx }) => {
    const w = width()
    const rest = spring.value + project(vx)
    const shouldClose = Math.abs(vx) > 250 ? vx < 0 : rest < -w / 2
    if (shouldClose) {
      emit('close')
      spring.set(-w, { velocity: vx })
    } else {
      spring.set(0, { velocity: vx })
    }
  },
})
const scrimOpacity = () => Math.max(0, Math.min(1, 1 + x.value / width()))
</script>

<template>
  <Teleport to="body">
    <div v-if="mounted" class="drawer-root" :class="{ reduced: reducedMotion(), open }" role="dialog" aria-modal="true" aria-label="Menu">
      <div class="scrim" :style="{ opacity: scrimOpacity() }" @click="emit('close')"></div>
      <nav class="drawer" :style="{ transform: `translate3d(${x}px, 0, 0)` }" aria-label="Main" v-bind="drag.handlers" @dragstart.prevent>
        <div class="brand">
          <img :src="theme.isDark.value ? '/mark-dark.svg' : '/favicon.svg'" alt="" width="26" height="26" class="mark" />
          <span class="word">Pozzy</span>
        </div>
        <RouterLink v-for="item in items" :key="item.name" :to="{ name: item.name }" class="nav-item" :class="{ active: current === item.name }" :aria-current="current === item.name ? 'page' : undefined" @click="drag.wasDrag() ? $event.preventDefault() : emit('close')">
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
  </Teleport>
</template>

<style scoped>
.drawer-root { position: fixed; inset: 0; z-index: var(--z-sheet); display: flex; }
.scrim { position: absolute; inset: 0; background: var(--scrim); -webkit-backdrop-filter: blur(4px); backdrop-filter: blur(4px); }
.drawer {
  position: relative; width: 272px; max-width: 84vw; height: 100%;
  background: var(--surface);
  border-right: 1px solid var(--line); box-shadow: var(--shadow-3);
  padding: calc(env(safe-area-inset-top) + 24px) 14px calc(env(safe-area-inset-bottom) + 20px);
  display: flex; flex-direction: column; gap: 2px; overflow-y: auto;
  touch-action: pan-y; will-change: transform; user-select: none; -webkit-user-select: none;
}
.drawer a, .drawer img { -webkit-user-drag: none; }
.brand { display: flex; align-items: center; gap: 10px; padding: 0 10px 18px; }
.mark { width: 26px; height: 26px; }
.word { font-weight: 650; letter-spacing: -0.02em; font-size: var(--fs-lg); }
.nav-item { display: flex; align-items: center; gap: 12px; height: 44px; padding: 0 12px; border-radius: var(--r-md); color: var(--ink-2); text-decoration: none; font-size: var(--fs-base); font-weight: 500; border: 0; background: none; width: 100%; text-align: left; transition: background-color var(--dur-hover) ease, color var(--dur-hover) ease; }
.nav-item:hover { text-decoration: none; }
.nav-item.active { background: var(--surface-2); color: var(--ink); box-shadow: var(--inset); }
.nav-item.active .nav-icon { color: var(--brand); }
.nav-item:active { background: var(--surface-2); }
.nav-icon { width: 19px; height: 19px; flex: none; color: var(--ink-3); }
.spacer { flex: 1; }
.email { padding: 10px 12px 0; }
.reduced .drawer { transform: none !important; transition: opacity 200ms ease; opacity: 0; }
.reduced.open .drawer { opacity: 1; }
.reduced .scrim { transition: opacity 200ms ease; }
</style>
