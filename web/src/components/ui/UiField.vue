<script setup>
// Label above control, hint or error below. Wrap any native input, select or textarea.
defineProps({
  label: { type: String, default: '' },
  hint: { type: String, default: '' },
  error: { type: String, default: '' },
  inline: { type: Boolean, default: false },
})
</script>

<template>
  <label class="field" :class="{ inline, invalid: Boolean(error) }">
    <span v-if="label" class="field-label">{{ label }}</span>
    <span class="field-control"><slot /></span>
    <span v-if="error" class="field-error">{{ error }}</span>
    <span v-else-if="hint" class="field-hint">{{ hint }}</span>
  </label>
</template>

<style scoped>
.field { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.field.inline { flex-direction: row; align-items: center; gap: var(--sp-2); }
.field-label { font-size: var(--fs-xs); letter-spacing: 0.02em; font-weight: 500; color: var(--ink-2); }
.field-control { display: flex; min-width: 0; }
.field-control :deep(input), .field-control :deep(select), .field-control :deep(textarea) { width: 100%; }
.field-hint { font-size: var(--fs-sm); color: var(--ink-3); }
.field-error { font-size: var(--fs-sm); color: var(--danger); }
.invalid .field-control :deep(input), .invalid .field-control :deep(select), .invalid .field-control :deep(textarea) { border-color: var(--danger); }
</style>
