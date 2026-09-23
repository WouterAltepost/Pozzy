<script setup>
defineProps({
  variant: { type: String, default: 'secondary' }, // primary | secondary | ghost | danger | link
  size: { type: String, default: 'md' }, // sm | md
  type: { type: String, default: 'button' },
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  block: { type: Boolean, default: false },
})
</script>

<template>
  <button :type="type" class="btn" :class="[`btn-${variant}`, `btn-${size}`, { 'is-loading': loading, 'btn-block': block }]" :disabled="disabled || loading" :aria-busy="loading || undefined">
    <span v-if="loading" class="spin" aria-hidden="true"></span>
    <span class="label"><slot /></span>
  </button>
</template>

<style scoped>
.btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: var(--control-h-sm);
  min-height: 32px;
  padding: 0 14px;
  border-radius: var(--r-md);
  border: 0;
  font-weight: 500;
  font-size: var(--fs-base);
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  transition: background-color var(--dur-hover) ease, color var(--dur-hover) ease, transform var(--dur-press) var(--ease-out), opacity var(--dur-hover) ease;
}
.btn:active:not(:disabled) { transform: scale(0.97); opacity: 0.8; }
.btn:disabled { opacity: 0.4; cursor: default; }
.btn-block { width: 100%; }
.btn-sm { min-height: 28px; height: 28px; padding: 0 10px; font-size: var(--fs-md); }
.btn .label { display: inline-flex; align-items: center; gap: 6px; }
.btn :deep(svg) { width: 16px; height: 16px; flex: none; }

/* filled: the one prominent action */
.btn-primary { background: var(--brand); color: var(--on-tint); font-weight: 600; }
/* gray: fill with tinted text */
.btn-secondary { background: var(--surface-2); color: var(--brand); }
/* plain: tinted text only */
.btn-ghost { background: transparent; color: var(--brand); }
/* tinted red: destructive, never prominent */
.btn-danger { background: var(--danger-soft); color: var(--danger); }
.btn-link { background: none; color: var(--brand); padding: 0; height: auto; min-height: 0; border: 0; font-weight: 500; border-radius: 2px; }
.btn-link:active:not(:disabled) { transform: none; }

@media (hover: hover) and (pointer: fine) {
  .btn-primary:hover:not(:disabled) { background: color-mix(in srgb, var(--brand) 88%, #000); }
  .btn-secondary:hover:not(:disabled) { background: var(--surface-3); }
  .btn-ghost:hover:not(:disabled) { background: var(--surface-2); }
  .btn-danger:hover:not(:disabled) { background: color-mix(in srgb, var(--danger) 22%, var(--danger-soft)); }
  .btn-link:hover:not(:disabled) { opacity: 0.75; }
}

.is-loading .label { opacity: 0; }
.spin {
  position: absolute;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid currentColor;
  border-right-color: transparent;
  animation: spin 700ms linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .spin { animation: none; border-right-color: currentColor; opacity: 0.5; } }
</style>
