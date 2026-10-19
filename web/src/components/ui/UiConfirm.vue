<script setup>
// A small confirm dialog in place of window.confirm: title, one sentence, Cancel and the action.
import UiButton from './UiButton.vue'
import UiModal from './UiModal.vue'

defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: 'Are you sure?' },
  message: { type: String, default: '' },
  confirmLabel: { type: String, default: 'Confirm' },
  danger: { type: Boolean, default: false },
  busy: { type: Boolean, default: false },
})
const emit = defineEmits(['confirm', 'cancel'])
</script>

<template>
  <UiModal :open="open" :title="title" size="sm" @close="emit('cancel')">
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
</style>
