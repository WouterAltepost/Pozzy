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
.toaster { position: fixed; left: 0; right: 0; bottom: calc(var(--tab-h) + var(--sp-4) + env(safe-area-inset-bottom)); display: flex; justify-content: center; pointer-events: none; z-index: var(--z-toast); }
.toast { pointer-events: auto; display: flex; align-items: center; gap: 12px; max-width: min(420px, calc(100vw - 32px)); padding: 10px 16px; border-radius: var(--r-pill); background: var(--material); -webkit-backdrop-filter: var(--material-blur); backdrop-filter: var(--material-blur); color: var(--ink); font-size: var(--fs-md); font-weight: 500; box-shadow: var(--shadow-float), inset 0 1px 0 var(--material-edge); }
.toast.danger { background: var(--danger); color: #fff; }
.toast .text { min-width: 0; }
.toast .act { flex: none; height: 28px; padding: 0 10px; margin: -4px -8px -4px 0; border: 0; border-radius: var(--r-pill); background: transparent; color: var(--brand); font: inherit; font-weight: 600; cursor: pointer; }
.toast.danger .act { color: #fff; }
@media (prefers-reduced-transparency: reduce) { .toast { background: var(--surface); -webkit-backdrop-filter: none; backdrop-filter: none; } }
.toast .act:active { transform: scale(0.97); }
.toast-enter-active { transition: opacity var(--dur-ui) var(--ease-out), transform var(--dur-ui) var(--ease-out); }
.toast-leave-active { transition: opacity var(--dur-hover) ease, transform var(--dur-hover) ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateY(8px); }
@media (prefers-reduced-motion: reduce) { .toast-enter-from, .toast-leave-to { transform: none; } }
</style>
