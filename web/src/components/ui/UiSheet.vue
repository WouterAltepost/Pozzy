<script setup>
// Bottom sheet for mobile: nav, editors, details. Drag to dismiss with pointer capture,
// rubber-band above the rest position, flick dismissal by velocity, scrim and Escape close,
// focus moves inside while open and returns on close. Reduced motion fades instead of sliding.
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({ open: { type: Boolean, default: false }, title: { type: String, default: '' } })
const emit = defineEmits(['close'])

const panel = ref(null)
const dragging = ref(false)
let startY = 0
let lastY = 0
let lastT = 0
let velocity = 0
let previousFocus = null

function reduceMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function onKey(e) {
  if (e.key === 'Escape') emit('close')
}

watch(
  () => props.open,
  async (open) => {
    if (open) {
      previousFocus = document.activeElement
      document.addEventListener('keydown', onKey)
      document.body.style.overflow = 'hidden'
      await nextTick()
      const first = panel.value?.querySelector('input, select, textarea, button, a[href]')
      first?.focus({ preventScroll: true })
    } else {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
      if (panel.value) panel.value.style.transform = ''
      previousFocus?.focus?.({ preventScroll: true })
      previousFocus = null
    }
  },
)

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})

function rubber(overshoot, dimension = 120, constant = 0.55) {
  return (overshoot * dimension * constant) / (dimension + constant * Math.abs(overshoot))
}

function onPointerDown(e) {
  if (reduceMotion()) return
  dragging.value = true
  startY = lastY = e.clientY
  lastT = performance.now()
  velocity = 0
  e.currentTarget.setPointerCapture(e.pointerId)
}

function onPointerMove(e) {
  if (!dragging.value || !panel.value) return
  const now = performance.now()
  const dy = e.clientY - startY
  const dt = Math.max(1, now - lastT)
  velocity = (e.clientY - lastY) / dt
  lastY = e.clientY
  lastT = now
  const y = dy >= 0 ? dy : -rubber(-dy)
  panel.value.style.transition = 'none'
  panel.value.style.transform = `translateY(${y}px)`
}

function onPointerUp() {
  if (!dragging.value || !panel.value) return
  dragging.value = false
  const dy = lastY - startY
  const height = panel.value.getBoundingClientRect().height
  const shouldClose = dy > height * 0.35 || velocity > 0.11
  panel.value.style.transition = ''
  if (shouldClose) {
    emit('close')
  } else {
    // Settle back from the live position on the drawer curve.
    panel.value.animate([{ transform: panel.value.style.transform }, { transform: 'translateY(0)' }], {
      duration: 300,
      easing: 'cubic-bezier(0.23, 1, 0.32, 1)',
      fill: 'forwards',
    }).onfinish = () => {
      if (panel.value) panel.value.style.transform = ''
    }
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="open" class="sheet-root" role="dialog" aria-modal="true" :aria-label="title || 'Panel'">
        <div class="scrim" @click="emit('close')"></div>
        <div ref="panel" class="panel">
          <div class="grab" @pointerdown="onPointerDown" @pointermove="onPointerMove" @pointerup="onPointerUp" @pointercancel="onPointerUp">
            <span class="handle" aria-hidden="true"></span>
          </div>
          <div v-if="title" class="sheet-head">
            <h2>{{ title }}</h2>
            <button type="button" class="close" aria-label="Close" @click="emit('close')">
              <svg viewBox="0 0 256 256" width="18" height="18" fill="none" stroke="currentColor" stroke-width="18" stroke-linecap="round"><path d="M200 56 56 200M56 56l144 144" /></svg>
            </button>
          </div>
          <div class="sheet-body"><slot /></div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.sheet-root { position: fixed; inset: 0; z-index: var(--z-sheet); display: flex; flex-direction: column; justify-content: flex-end; }
.scrim { position: absolute; inset: 0; background: var(--scrim); }
.panel {
  position: relative;
  max-height: min(88vh, 88dvh);
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border-radius: var(--r-xl) var(--r-xl) 0 0;
  box-shadow: var(--shadow-3);
  padding-bottom: env(safe-area-inset-bottom);
  touch-action: pan-y;
}
.grab { display: flex; justify-content: center; padding: 10px 0 6px; cursor: grab; touch-action: none; }
.handle { width: 36px; height: 4px; border-radius: 2px; background: var(--line-2); }
.sheet-head { display: flex; align-items: center; justify-content: space-between; padding: 0 var(--sp-4) var(--sp-2); }
.sheet-head h2 { font-size: var(--fs-lg); }
.close { display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; border: 0; border-radius: 50%; background: var(--surface-2); color: var(--ink-2); }
.sheet-body { overflow-y: auto; padding: var(--sp-2) var(--sp-4) var(--sp-5); }

.sheet-enter-active .scrim, .sheet-leave-active .scrim { transition: opacity var(--dur-panel) ease; }
.sheet-enter-active .panel { transition: transform var(--dur-sheet) var(--ease-drawer); }
.sheet-leave-active .panel { transition: transform var(--dur-panel) var(--ease-drawer); }
.sheet-enter-from .scrim, .sheet-leave-to .scrim { opacity: 0; }
.sheet-enter-from .panel, .sheet-leave-to .panel { transform: translateY(100%); }
@media (prefers-reduced-motion: reduce) {
  .sheet-enter-active .panel, .sheet-leave-active .panel { transition: opacity 120ms ease; }
  .sheet-enter-from .panel, .sheet-leave-to .panel { transform: none; opacity: 0; }
}
</style>
