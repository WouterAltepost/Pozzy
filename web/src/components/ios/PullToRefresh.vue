<script setup>
// Pull to refresh, iOS style: at the top of the page a downward pull moves the content with
// resistance and draws the activity indicator spoke by spoke; past the threshold it ticks,
// and on release it spins while `action` runs, then the content springs back. Touch only.
import { computed, ref } from 'vue'
import { createSpring, rubberband } from '../../lib/spring'
import { bump } from '../../lib/haptics'
import { useMediaQuery } from '../../composables/useMediaQuery'

const props = defineProps({ action: { type: Function, required: true } })
const THRESHOLD = 72
const REST = 52
const y = ref(0)
const loading = ref(false)
const touch = useMediaQuery('(pointer: coarse)')
const spring = createSpring({ value: 0, damping: 1, response: 0.35, onUpdate: (v) => (y.value = v) })
let g = null
let armed = false

function blocked() {
  return document.documentElement.classList.contains('sheet-open')
}
function start(e) {
  if (!touch.value || loading.value || window.scrollY > 0 || e.touches.length !== 1 || blocked()) return
  g = { y0: e.touches[0].clientY, x0: e.touches[0].clientX, active: false }
}
function move(e) {
  if (!g) return
  const dy = e.touches[0].clientY - g.y0
  const dx = e.touches[0].clientX - g.x0
  if (!g.active) {
    if (dy < 6 || Math.abs(dx) > Math.abs(dy) || window.scrollY > 0) {
      if (Math.abs(dx) > 6 || dy < -6) g = null
      return
    }
    g.active = true
  }
  e.preventDefault()
  const pulled = rubberband(Math.max(0, dy), window.innerHeight, 0.55)
  spring.jump(pulled)
  if (pulled > THRESHOLD !== armed) {
    armed = pulled > THRESHOLD
    if (armed) bump()
  }
}
async function end() {
  if (!g) return
  const was = g
  g = null
  if (!was.active) return
  if (!armed) return spring.set(0)
  armed = false
  loading.value = true
  spring.set(REST)
  try {
    await props.action()
  } finally {
    loading.value = false
    spring.set(0)
  }
}
// 8 spokes; while pulling they appear one by one, while loading the whole wheel turns.
const shown = computed(() => (loading.value ? 8 : Math.min(8, Math.floor((y.value / THRESHOLD) * 8))))
</script>

<template>
  <div class="ptr" @touchstart.passive="start" @touchmove="move" @touchend="end" @touchcancel="end">
    <div class="spinner" :class="{ spin: loading }" :style="{ opacity: y > 8 ? 1 : 0, top: `${Math.max(0, y - 40)}px` }" aria-hidden="true">
      <span v-for="i in 8" :key="i" class="spoke" :style="{ transform: `rotate(${(i - 1) * 45}deg) translateY(-7px)`, opacity: i <= shown ? 0.25 + (i / 8) * 0.75 : 0 }"></span>
    </div>
    <span v-if="loading" class="visually-hidden" role="status">Refreshing</span>
    <div class="ptr-content" :style="y ? { transform: `translate3d(0, ${y}px, 0)` } : undefined"><slot /></div>
  </div>
</template>

<style scoped>
.ptr { position: relative; }
.spinner { position: absolute; left: 50%; width: 28px; height: 28px; margin-left: -14px; transition: opacity 150ms ease; pointer-events: none; }
.spoke { position: absolute; left: 12.5px; top: 10px; width: 3px; height: 8px; border-radius: 2px; background: var(--ink-3); transform-origin: 1.5px 4px; }
.spin { animation: turn 0.8s steps(8) infinite; }
@keyframes turn { to { transform: rotate(360deg); } }
.ptr-content { will-change: transform; }
</style>
