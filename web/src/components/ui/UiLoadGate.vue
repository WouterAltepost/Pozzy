<script setup>
// Holds a page behind one loading figure until everything it needs has arrived, then reveals
// it all at once. Content stays mounted (so children can fetch) but hidden and taken out of the
// flow, so the figure never moves while widgets arrive underneath. The figure only appears after
// a short delay, so fast loads never flash it.
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({ ready: { type: Boolean, default: false }, label: { type: String, default: 'Loading' } })
const showFigure = ref(false)
let timer = null

onMounted(() => {
  timer = setTimeout(() => {
    if (!props.ready) showFigure.value = true
  }, 140)
})
watch(() => props.ready, (r) => r && (showFigure.value = false))
onBeforeUnmount(() => clearTimeout(timer))
</script>

<template>
  <div class="gate" :class="{ ready }">
    <Transition name="figure">
      <div v-if="showFigure && !ready" class="figure" role="status" aria-live="polite">
        <img src="/favicon.svg" alt="" class="mark" width="34" height="34" />
        <span class="muted small">{{ label }}</span>
      </div>
    </Transition>
    <div class="content" :aria-hidden="!ready" :inert="!ready || undefined"><slot /></div>
  </div>
</template>

<style scoped>
.gate { position: relative; }
.gate:not(.ready) { min-height: 56vh; overflow: hidden; }
/* Out of the flow while loading: the gate keeps one fixed height and the figure stays put. */
.content { position: absolute; inset: 0 0 auto 0; opacity: 0; transform: translateY(6px); visibility: hidden; pointer-events: none; }
.ready .content { position: static; opacity: 1; transform: none; visibility: visible; pointer-events: auto; transition: opacity 280ms var(--ease-out), transform 320ms var(--ease-spring); }
.figure { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: var(--sp-3); }
.mark { animation: spin 1.6s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite; transform-origin: 50% 50%; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.figure-enter-active { transition: opacity 200ms ease; }
.figure-leave-active { transition: opacity 120ms ease; }
.figure-enter-from, .figure-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) {
  .mark { animation: none; }
  .content { transform: none; }
  .ready .content { transition: opacity 200ms ease; }
}
</style>
