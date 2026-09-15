<script setup>
// Holds a page behind one loading figure until everything it needs has arrived, then reveals
// it all at once. Content stays mounted (so children can fetch) but hidden. The figure only
// appears after a short delay, so fast loads never flash it.
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
.gate:not(.ready) { min-height: 50vh; }
.content { opacity: 0; transform: translateY(6px); visibility: hidden; }
.ready .content { opacity: 1; transform: none; visibility: visible; transition: opacity 280ms var(--ease-out), transform 320ms var(--ease-spring); }
.figure { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: var(--sp-3); }
.mark { animation: breathe 1.4s var(--ease-in-out) infinite; }
@keyframes breathe { 0%, 100% { transform: scale(1); opacity: 0.9; } 50% { transform: scale(1.12); opacity: 0.55; } }
.figure-enter-active { transition: opacity 200ms ease; }
.figure-leave-active { transition: opacity 120ms ease; }
.figure-enter-from, .figure-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) {
  .mark { animation: none; }
  .content { transform: none; }
  .ready .content { transition: opacity 200ms ease; }
}
</style>
