<script setup>
// Centred dialog at every width (the phone design keeps editors as popups too). One component
// for every editor and detail popup so they all open the same way: scrim fade, panel rises and
// settles on the spring curve. Escape and scrim close, focus moves in and returns, body scroll locks.
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { PhX } from '@phosphor-icons/vue'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  size: { type: String, default: 'md' }, // sm 440 | md 600 | lg 780
})
const emit = defineEmits(['close'])
const panel = ref(null)
let previousFocus = null

function onKey(e) {
  if (e.key === 'Escape') emit('close')
}

watch(
  () => props.open,
  async (on) => {
    if (on) {
      previousFocus = document.activeElement
      document.addEventListener('keydown', onKey)
      document.body.style.overflow = 'hidden'
      await nextTick()
      const body = panel.value?.querySelector('.dialog-body')
      const first = body?.querySelector('input:not([type=checkbox]):not([type=radio]), textarea, select') || body?.querySelector('button, a[href]')
      first?.focus({ preventScroll: true })
    } else {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
      previousFocus?.focus?.({ preventScroll: true })
      previousFocus = null
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
    <Transition name="modal">
      <div v-if="open" class="modal-root" role="dialog" aria-modal="true" :aria-label="title || 'Dialog'">
        <div class="scrim" @click="emit('close')"></div>
        <div ref="panel" class="dialog" :class="`size-${size}`">
          <div v-if="title" class="dialog-head">
            <h2>{{ title }}</h2>
            <button type="button" class="icon-btn" aria-label="Close" @click="emit('close')"><PhX :size="18" /></button>
          </div>
          <div class="dialog-body"><slot /></div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-root { position: fixed; inset: 0; z-index: var(--z-sheet); display: flex; align-items: center; justify-content: center; padding: var(--sp-6); }
@media (max-width: 720px) { .modal-root { padding: calc(env(safe-area-inset-top) + 16px) 16px calc(env(safe-area-inset-bottom) + 16px); } .dialog-head { padding: var(--sp-4) var(--sp-4) 0; } .dialog-body { padding: var(--sp-3) var(--sp-4) var(--sp-4); } }
.scrim { position: absolute; inset: 0; background: var(--scrim); }
.dialog {
  position: relative;
  width: 100%;
  max-height: min(88vh, 88dvh);
  display: flex;
  flex-direction: column;
  background: color-mix(in srgb, var(--surface) 86%, transparent);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  backdrop-filter: blur(24px) saturate(160%);
  border: 1px solid color-mix(in srgb, var(--line) 80%, transparent);
  border-radius: var(--r-xl);
  box-shadow: var(--shadow-3), inset 0 1px 0 rgb(255 255 255 / 0.5);
}
.size-sm { max-width: 440px; }
.size-md { max-width: 600px; }
.size-lg { max-width: 780px; }
@media (prefers-reduced-transparency: reduce) { .dialog { background: var(--surface); -webkit-backdrop-filter: none; backdrop-filter: none; } }
.dialog-head { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-3); padding: var(--sp-4) var(--sp-5) 0; }
.dialog-head h2 { font-size: var(--fs-lg); }
.dialog-body { overflow-y: auto; padding: var(--sp-4) var(--sp-5) var(--sp-5); }
.dialog-body :deep(.card-head h2) { font-size: var(--fs-lg); }

.modal-enter-active .scrim { transition: opacity var(--dur-ui) ease; }
.modal-leave-active .scrim { transition: opacity var(--dur-hover) ease; }
.modal-enter-active .dialog { transition: opacity var(--dur-ui) ease, transform var(--dur-modal) var(--ease-spring); }
.modal-leave-active .dialog { transition: opacity var(--dur-hover) ease, transform var(--dur-hover) ease; }
.modal-enter-from .scrim, .modal-leave-to .scrim { opacity: 0; }
.modal-enter-from .dialog { opacity: 0; transform: translateY(14px) scale(0.98); }
.modal-leave-to .dialog { opacity: 0; transform: translateY(6px) scale(0.99); }
@media (prefers-reduced-motion: reduce) { .modal-enter-from .dialog, .modal-leave-to .dialog { transform: none; } }
</style>
