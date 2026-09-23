<script setup>
import { toastState, useToast } from '../../composables/useToast'

const toast = useToast()
async function act() {
  const action = toastState.current?.action
  toast.dismiss()
  if (action) await action.run()
}
</script>

<template>
  <Teleport to="body">
    <div class="toaster" aria-live="polite">
      <Transition name="toast">
        <div v-if="toastState.current" class="toast" :class="toastState.current.tone" role="status">
          <span class="text">{{ toastState.current.text }}</span>
          <button v-if="toastState.current.action" type="button" class="act" @click="act">{{ toastState.current.action.label }}</button>
        </div>
      </Transition>
    </div>
  </Teleport>
</template>

<style scoped>
.toaster { position: fixed; left: 0; right: 0; bottom: calc(var(--sp-6) + env(safe-area-inset-bottom)); display: flex; justify-content: center; pointer-events: none; z-index: var(--z-toast); }
.toast { pointer-events: auto; display: flex; align-items: center; gap: 12px; max-width: min(420px, calc(100vw - 32px)); padding: 10px 14px; border-radius: var(--r-md); background: var(--ink); color: var(--on-ink); font-size: var(--fs-md); font-weight: 500; box-shadow: var(--shadow-3); }
.toast .text { min-width: 0; }
.toast .act { flex: none; height: 28px; padding: 0 10px; margin: -4px -6px -4px 0; border: 0; border-radius: var(--r-sm); background: color-mix(in srgb, var(--on-ink) 16%, transparent); color: inherit; font: inherit; font-weight: 600; cursor: pointer; }
.toast .act:active { transform: scale(0.97); }
.toast.danger { background: var(--danger); color: #fff; }
.toast-enter-active { transition: opacity var(--dur-ui) var(--ease-out), transform var(--dur-ui) var(--ease-out); }
.toast-leave-active { transition: opacity var(--dur-hover) ease, transform var(--dur-hover) ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(8px); }
@media (prefers-reduced-motion: reduce) { .toast-enter-from, .toast-leave-to { transform: none; } }
</style>
