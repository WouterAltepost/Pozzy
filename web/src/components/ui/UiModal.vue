<script setup>
// One dialog component for every editor and detail popup. On a phone it is a bottom sheet:
// it springs up from the bottom edge, the grabber and head follow the finger, pulling up past
// the top rubber-bands, and a downward flick dismisses it at the finger's speed. It leaves the
// way it came. At desktop widths it is a centred panel that materialises from its resting
// place. Escape and scrim close, focus moves in and returns, body scroll locks.
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { PhX } from '@phosphor-icons/vue'
import { useDrag } from '../../composables/useDrag'
import { useMediaQuery } from '../../composables/useMediaQuery'
import { createSpring, project, reducedMotion, rubberband } from '../../lib/spring'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  size: { type: String, default: 'md' }, // sm 440 | md 600 | lg 780
})
const emit = defineEmits(['close'])
const panel = ref(null)
const phone = useMediaQuery('(max-width: 720px)')
let previousFocus = null

// Sheet motion (phone). y = translateY in px, 0 = resting, height = off screen.
const mounted = ref(false)
const y = ref(0)
const sheetHeight = () => panel.value?.offsetHeight || window.innerHeight
const spring = createSpring({
  value: 0,
  damping: 1,
  response: 0.4,
  onUpdate: (v) => (y.value = v),
  onRest: () => {
    if (!props.open) mounted.value = false
  },
})

async function show() {
  previousFocus = document.activeElement
  document.addEventListener('keydown', onKey)
  document.body.style.overflow = 'hidden'
  mounted.value = true
  await nextTick()
  if (phone.value) {
    if (spring.value <= 0.5 || !spring.running) spring.jump(sheetHeight())
    spring.set(0)
  }
  const body = panel.value?.querySelector('.dialog-body')
  const first = body?.querySelector('input:not([type=checkbox]):not([type=radio]), textarea, select') || body?.querySelector('button, a[href]')
  if (!phone.value) first?.focus({ preventScroll: true })
}
function hide(velocity = 0) {
  document.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
  previousFocus?.focus?.({ preventScroll: true })
  previousFocus = null
  if (phone.value && mounted.value && !reducedMotion()) spring.set(sheetHeight(), { velocity: Math.max(0, velocity) })
  else mounted.value = false
}
function onKey(e) {
  if (e.key === 'Escape') emit('close')
}
watch(
  () => props.open,
  (on) => (on ? show() : hide()),
)
onMounted(() => props.open && show())
onBeforeUnmount(() => {
  spring.stop()
  document.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})

// Drag from the grabber or the head. The body keeps native scrolling.
let startY = 0
const drag = useDrag({
  axis: 'y',
  enabled: () => phone.value,
  onStart: () => {
    startY = spring.value
    spring.stop()
  },
  onMove: ({ dy }) => {
    const raw = startY + dy
    spring.jump(raw < 0 ? rubberband(raw, sheetHeight()) : raw)
  },
  onEnd: ({ vy }) => {
    const h = sheetHeight()
    const rest = spring.value + project(vy)
    const dismiss = Math.abs(vy) > 300 ? vy > 0 : rest > h / 2
    if (dismiss) {
      emit('close')
      spring.set(h, { velocity: vy })
    } else {
      spring.set(0, { velocity: vy })
    }
  },
})
const scrimOpacity = computed(() => (phone.value ? Math.max(0, Math.min(1, 1 - y.value / Math.max(1, sheetHeight()))) : 1))
const sheetStyle = computed(() => (phone.value ? { transform: `translate3d(0, ${y.value}px, 0)` } : undefined))
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="mounted" class="modal-root" :class="{ phone, reduced: reducedMotion(), open }" role="dialog" aria-modal="true" :aria-label="title || 'Dialog'">
        <div class="scrim" :style="{ opacity: scrimOpacity }" @click="emit('close')"></div>
        <div ref="panel" class="dialog" :class="`size-${size}`" :style="sheetStyle">
          <div class="plate">
            <div v-if="phone" class="grab" aria-hidden="true" v-bind="drag.handlers" @dragstart.prevent><span class="grabber"></span></div>
            <div v-if="title" class="dialog-head" v-bind="phone ? drag.handlers : {}" @dragstart.prevent>
              <h2>{{ title }}</h2>
              <button type="button" class="icon-btn" aria-label="Close" @click="emit('close')"><PhX :size="18" /></button>
            </div>
            <div class="dialog-body"><slot /></div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-root { position: fixed; inset: 0; z-index: var(--z-sheet); display: flex; align-items: center; justify-content: center; padding: var(--sp-6); }
.scrim { position: absolute; inset: 0; background: var(--scrim); -webkit-backdrop-filter: blur(6px); backdrop-filter: blur(6px); }
/* Double bezel: a tray with a hairline holding the plate, concentric corners. */
.dialog {
  --tray: 6px;
  position: relative;
  width: 100%;
  max-height: min(88vh, 88dvh);
  display: flex;
  flex-direction: column;
  padding: var(--tray);
  background: color-mix(in srgb, var(--surface-2) 70%, var(--surface));
  border: 1px solid var(--line-2);
  border-radius: calc(var(--r-xl) + var(--tray));
  box-shadow: var(--shadow-3);
}
.plate { display: flex; flex-direction: column; min-height: 0; background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-xl); box-shadow: inset 0 1px 0 var(--edge), 0 1px 2px rgb(14 17 32 / 0.04); overflow: hidden; }
.size-sm { max-width: 452px; }
.size-md { max-width: 612px; }
.size-lg { max-width: 792px; }
.dialog-head { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-3); padding: var(--sp-5) var(--sp-6) 0; }
.dialog-head h2 { font-size: var(--fs-xl); font-weight: 650; letter-spacing: -0.02em; }
.dialog-body { overflow-y: auto; padding: var(--sp-4) var(--sp-6) var(--sp-6); overscroll-behavior: contain; }
.dialog-body :deep(.card-head h2) { font-size: var(--fs-lg); }
.grab { display: none; }

/* Desktop: the panel materialises in place, scale and opacity together, and leaves the same way. */
.modal-enter-active .scrim { transition: opacity var(--dur-ui) ease; }
.modal-leave-active .scrim { transition: opacity var(--dur-hover) ease; }
.modal-enter-active:not(.phone) .dialog { transition: opacity var(--dur-ui) ease, transform var(--dur-modal) var(--ease-spring); }
.modal-leave-active:not(.phone) .dialog { transition: opacity var(--dur-hover) ease, transform var(--dur-hover) ease; }
.modal-enter-from .scrim, .modal-leave-to .scrim { opacity: 0 !important; }
.modal-enter-from:not(.phone) .dialog { opacity: 0; transform: translateY(10px) scale(0.97); }
.modal-leave-to:not(.phone) .dialog { opacity: 0; transform: scale(0.985); }
@media (prefers-reduced-motion: reduce) { .modal-enter-from .dialog, .modal-leave-to .dialog { transform: none; } }

/* Phone: a sheet from the bottom edge. The spring drives transform; CSS only draws the material. */
.phone { align-items: flex-end; padding: 0 6px; }
.phone .dialog {
  max-width: none;
  max-height: calc(100dvh - env(safe-area-inset-top) - 24px);
  border-radius: calc(var(--r-xl) + var(--tray)) calc(var(--r-xl) + var(--tray)) 0 0;
  border-bottom: 0;
  padding-bottom: 0;
  will-change: transform;
  touch-action: none;
}
.phone .plate { border-radius: var(--r-xl) var(--r-xl) 0 0; border-bottom: 0; padding-bottom: env(safe-area-inset-bottom); }
.phone .grab { display: flex; justify-content: center; padding: 10px 0 2px; touch-action: none; cursor: grab; user-select: none; -webkit-user-select: none; }
.phone .grabber { width: 36px; height: 5px; border-radius: 3px; background: var(--ink-4); }
.phone .dialog-head { padding: var(--sp-2) var(--sp-5) 0; touch-action: none; user-select: none; -webkit-user-select: none; }
.phone .dialog-body { padding: var(--sp-4) var(--sp-5) var(--sp-6); touch-action: pan-y; }
.reduced.phone .dialog { transform: none !important; transition: opacity 200ms ease; }
</style>
