<script setup>
// A confirm in place of window.confirm. Desktop: a small dialog with Cancel and the action.
// Phone: an iOS action sheet from the bottom edge, the message and the action in one rounded
// group, Cancel on its own below; a tap on the dimmed page cancels.
import { onBeforeUnmount, watch } from 'vue'
import UiButton from './UiButton.vue'
import UiModal from './UiModal.vue'
import { useMediaQuery } from '../../composables/useMediaQuery'
import { bump } from '../../lib/haptics'

const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: 'Are you sure?' },
  message: { type: String, default: '' },
  confirmLabel: { type: String, default: 'Confirm' },
  danger: { type: Boolean, default: false },
  busy: { type: Boolean, default: false },
})
const emit = defineEmits(['confirm', 'cancel'])
const phone = useMediaQuery('(max-width: 720px)')

function onKey(e) {
  if (e.key === 'Escape') emit('cancel')
}
watch(
  () => props.open && phone.value,
  (on) => {
    if (on) {
      bump()
      document.addEventListener('keydown', onKey)
    } else document.removeEventListener('keydown', onKey)
  },
)
onBeforeUnmount(() => document.removeEventListener('keydown', onKey))
</script>

<template>
  <template v-if="phone">
    <Teleport to="body">
      <Transition name="as">
        <div v-if="open" class="as-root" role="alertdialog" aria-modal="true" :aria-label="title">
          <div class="as-scrim" @click="emit('cancel')"></div>
          <div class="as-panel">
            <div class="as-group">
              <div class="as-head">
                <span class="as-title">{{ title }}</span>
                <span v-if="message" class="as-msg">{{ message }}</span>
              </div>
              <button type="button" class="as-btn" :class="{ danger }" :disabled="busy" @click="emit('confirm')">{{ busy ? 'Working…' : confirmLabel }}</button>
            </div>
            <div class="as-group">
              <button type="button" class="as-btn cancel" :disabled="busy" @click="emit('cancel')">Cancel</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </template>
  <UiModal v-else :open="open" :title="title" size="sm" @close="emit('cancel')">
    <p v-if="message" class="msg">{{ message }}</p>
    <div class="actions">
      <UiButton :disabled="busy" @click="emit('cancel')">Cancel</UiButton>
      <UiButton :variant="danger ? 'danger' : 'primary'" :loading="busy" @click="emit('confirm')">{{ confirmLabel }}</UiButton>
    </div>
  </UiModal>
</template>

<style scoped>
.msg { color: var(--ink-2); }
.actions { display: flex; justify-content: flex-end; gap: var(--sp-2); margin-top: var(--sp-5); }

.as-root { position: fixed; inset: 0; z-index: var(--z-sheet); display: flex; flex-direction: column; justify-content: flex-end; }
.as-scrim { position: absolute; inset: 0; background: rgb(0 0 0 / 0.35); }
.as-panel { position: relative; display: flex; flex-direction: column; gap: 8px; padding: 0 8px calc(8px + env(safe-area-inset-bottom)); }
.as-group { border-radius: 14px; overflow: hidden; background: var(--material); -webkit-backdrop-filter: blur(30px) saturate(180%); backdrop-filter: blur(30px) saturate(180%); }
.as-head { display: flex; flex-direction: column; gap: 4px; padding: 14px 16px; text-align: center; border-bottom: 0.5px solid var(--line-2); }
.as-title { font-size: 0.8125rem; font-weight: 600; color: var(--ink-3); }
.as-msg { font-size: 0.8125rem; color: var(--ink-3); }
.as-btn { display: block; width: 100%; height: 57px; border: 0; background: transparent; color: var(--brand); font: inherit; font-size: 1.25rem; }
.as-btn.danger { color: var(--danger); }
.as-btn.cancel { font-weight: 600; background: var(--surface); }
.as-btn:active { background: var(--surface-3); }
.as-btn:disabled { opacity: 0.5; }
.as-enter-active, .as-leave-active { transition: opacity 300ms ease; }
.as-enter-active .as-panel, .as-leave-active .as-panel { transition: transform 420ms cubic-bezier(0.32, 0.72, 0, 1); }
.as-enter-from, .as-leave-to { opacity: 0; }
.as-enter-from .as-panel, .as-leave-to .as-panel { transform: translateY(100%); }
.as-leave-active .as-panel { transition-duration: 280ms; }
@media (prefers-reduced-motion: reduce) { .as-enter-from .as-panel, .as-leave-to .as-panel { transform: none; } }
</style>
