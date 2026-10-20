<script setup>
// iOS swipe actions on a list row. Drag the row sideways: actions are revealed behind it in
// their colours. Let go past the buttons to leave them open; swipe far (past 60% of the row)
// or flick to run the outermost action at once, the way Mail and Reminders do. A tap on an
// open row closes it instead of opening the row. Touch only; the desktop keeps its buttons.
//
//   <SwipeRow :leading="[{ label: 'Done', icon: PhCheck, color: 'var(--ok)', action }]"
//             :trailing="[{ label: 'Skip', icon: PhSkipForward, color: '#8E8E93', action }]">
//     <HabitRow ... />
//   </SwipeRow>
import { computed, onBeforeUnmount, ref } from 'vue'
import { createSpring, project, rubberband } from '../../lib/spring'
import { tick } from '../../lib/haptics'
import { useMediaQuery } from '../../composables/useMediaQuery'

const props = defineProps({
  leading: { type: Array, default: () => [] },
  trailing: { type: Array, default: () => [] },
})

const BTN = 74
const root = ref(null)
const x = ref(0)
const touch = useMediaQuery('(pointer: coarse)')
const enabled = computed(() => touch.value && (props.leading.length || props.trailing.length))
const spring = createSpring({ value: 0, damping: 1, response: 0.32, onUpdate: (v) => (x.value = v) })
let g = null
let armed = false

const width = () => root.value?.offsetWidth || 360
const openLead = () => props.leading.length * BTN
const openTrail = () => props.trailing.length * BTN

function start(e) {
  if (!enabled.value || e.touches.length !== 1) return
  const t = e.touches[0]
  g = { x0: t.clientX, y0: t.clientY, base: spring.value, active: false, samples: [] }
  spring.stop()
}
function move(e) {
  if (!g) return
  const t = e.touches[0]
  const dx = t.clientX - g.x0
  const dy = t.clientY - g.y0
  if (!g.active) {
    if (Math.abs(dx) < 10 && Math.abs(dy) < 10) return
    if (Math.abs(dy) > Math.abs(dx)) {
      g = null
      return
    }
    g.active = true
  }
  e.preventDefault()
  const now = performance.now()
  g.samples.push({ t: now, x: t.clientX })
  g.samples = g.samples.filter((s) => now - s.t < 100)
  let next = g.base + dx
  if (next > 0 && !props.leading.length) next = rubberband(next, width()) * 0.3
  if (next < 0 && !props.trailing.length) next = rubberband(next, width()) * 0.3
  spring.jump(next)
  // Crossing the full-swipe line ticks once each way, like iOS.
  const full = Math.abs(next) > width() * 0.6
  if (full !== armed) {
    armed = full
    tick()
  }
}
function end() {
  if (!g) return
  const was = g
  g = null
  if (!was.active) return
  const s = was.samples
  const v = s.length > 1 ? ((s[s.length - 1].x - s[0].x) / Math.max(1, s[s.length - 1].t - s[0].t)) * 1000 : 0
  const at = spring.value
  const rest = at + project(v, 0.99)
  armed = false
  if (at > width() * 0.6 && props.leading.length) return run(props.leading[0], 1, v)
  if (at < -width() * 0.6 && props.trailing.length) return run(props.trailing[0], -1, v)
  if (rest > openLead() / 2 && props.leading.length) spring.set(openLead(), { velocity: v })
  else if (rest < -openTrail() / 2 && props.trailing.length) spring.set(-openTrail(), { velocity: v })
  else spring.set(0, { velocity: v })
}
function run(action, dir, velocity = 0) {
  tick()
  spring.set(dir * width(), { velocity })
  setTimeout(() => {
    action.action?.()
    spring.set(0)
  }, 220)
}
function close() {
  spring.set(0)
}
// A tap while open closes the row and swallows the click.
function onClickCapture(e) {
  if (Math.abs(spring.value) > 2) {
    e.stopPropagation()
    e.preventDefault()
    close()
  }
}
onBeforeUnmount(() => spring.stop())
defineExpose({ close })

const leadW = computed(() => Math.max(0, x.value))
const trailW = computed(() => Math.max(0, -x.value))
</script>

<template>
  <div ref="root" class="swipe" :class="{ moving: x !== 0 }" @touchstart.passive="start" @touchmove="move" @touchend="end" @touchcancel="end">
    <div v-if="leading.length && x > 0" class="acts lead" :style="{ width: leadW + 'px' }">
      <button v-for="(a, i) in leading" :key="i" type="button" class="act" :style="{ background: a.color, flex: i === 0 && leadW > openLead() ? `1 0 ${BTN}px` : `0 0 ${leadW / leading.length}px` }" @click="run(a, 1)">
        <component :is="a.icon" v-if="a.icon" weight="fill" class="ai" /><span class="al">{{ a.label }}</span>
      </button>
    </div>
    <div v-if="trailing.length && x < 0" class="acts trail" :style="{ width: trailW + 'px' }">
      <button v-for="(a, i) in [...trailing].reverse()" :key="i" type="button" class="act" :style="{ background: a.color, flex: i === trailing.length - 1 && trailW > openTrail() ? `1 0 ${BTN}px` : `0 0 ${trailW / trailing.length}px` }" @click="run(a, -1)">
        <component :is="a.icon" v-if="a.icon" weight="fill" class="ai" /><span class="al">{{ a.label }}</span>
      </button>
    </div>
    <div class="content" :style="x ? { transform: `translate3d(${x}px, 0, 0)` } : undefined" @click.capture="onClickCapture">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.swipe { position: relative; overflow: hidden; touch-action: pan-y; }
.content { position: relative; z-index: 1; background: var(--surface); will-change: transform; }
.acts { position: absolute; top: 0; bottom: 0; display: flex; overflow: hidden; }
.acts.lead { left: 0; }
.acts.trail { right: 0; justify-content: flex-end; }
.act { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; min-width: 0; overflow: hidden; border: 0; color: #fff; font: inherit; font-size: 0.8125rem; font-weight: 500; transition: flex-basis 200ms ease; }
.ai { width: 22px; height: 22px; flex: none; }
.al { white-space: nowrap; }
</style>
