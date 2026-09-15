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
  height: var(--control-h);
  padding: 0 var(--sp-3);
  border-radius: var(--r-md);
  border: 1px solid transparent;
  font-weight: 500;
  font-size: var(--fs-base);
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  transition: background-color var(--dur-hover) ease, border-color var(--dur-hover) ease, color var(--dur-hover) ease, transform var(--dur-press) var(--ease-out), box-shadow var(--dur-hover) ease;
}
.btn:active:not(:disabled) { transform: scale(0.97); }
.btn:disabled { opacity: 0.55; cursor: default; }
.btn-block { width: 100%; }
.btn-sm { height: var(--control-h-sm); padding: 0 10px; font-size: var(--fs-md); }
.btn .label { display: inline-flex; align-items: center; gap: 6px; }
.btn :deep(svg) { width: 16px; height: 16px; flex: none; }

.btn-primary { background: var(--ink); color: var(--on-ink); border-color: var(--ink); }
.btn-secondary { background: var(--surface); color: var(--ink); border-color: var(--line-2); }
.btn-ghost { background: transparent; color: var(--ink-2); }
.btn-danger { background: var(--danger-soft); color: var(--danger); border-color: transparent; }
.btn-link { background: none; color: var(--ink-2); padding: 0; height: auto; border: 0; text-decoration: underline; text-underline-offset: 3px; text-decoration-thickness: 1px; font-weight: 400; border-radius: 2px; }
.btn-link:active:not(:disabled) { transform: none; }

@media (hover: hover) and (pointer: fine) {
  .btn-primary:hover:not(:disabled) { background: var(--ink-2); border-color: var(--ink-2); }
  .btn-secondary:hover:not(:disabled) { background: var(--surface-2); }
  .btn-ghost:hover:not(:disabled) { background: var(--surface-2); color: var(--ink); }
  .btn-danger:hover:not(:disabled) { background: color-mix(in srgb, var(--danger) 22%, var(--danger-soft)); }
  .btn-link:hover:not(:disabled) { color: var(--ink); }
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
