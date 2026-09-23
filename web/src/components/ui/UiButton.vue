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
  gap: 7px;
  height: var(--control-h-sm);
  min-height: 32px;
  padding: 0 16px;
  border-radius: var(--r-pill);
  border: 1px solid transparent;
  font-weight: 500;
  font-size: var(--fs-md);
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  transition: background-color var(--dur-hover) ease, color var(--dur-hover) ease, transform var(--dur-press) var(--ease-out), box-shadow var(--dur-hover) ease, border-color var(--dur-hover) ease;
}
.btn:active:not(:disabled) { transform: translateY(1px) scale(0.98); }
.btn:disabled { opacity: 0.45; cursor: default; }
.btn-block { width: 100%; }
.btn-sm { min-height: 28px; height: 28px; padding: 0 12px; font-size: var(--fs-sm); }
.btn .label { display: inline-flex; align-items: center; gap: 6px; }
.btn :deep(svg) { width: 15px; height: 15px; flex: none; }

/* filled: the one prominent action, brighter at the top, shadow beneath */
.btn-primary { background: var(--ink); color: var(--on-ink); font-weight: 600; box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.12), 0 1px 2px rgb(14 17 32 / 0.1); }
/* raised: a plate lit from above */
.btn-secondary { background: linear-gradient(180deg, var(--surface), color-mix(in srgb, var(--surface) 95%, var(--ink))); color: var(--ink); border-color: var(--line-2); box-shadow: inset 0 1px 0 var(--edge), 0 1px 2px rgb(14 17 32 / 0.06); }
/* quiet: text only until hovered */
.btn-ghost { background: transparent; color: var(--ink-2); }
/* destructive, never prominent */
.btn-danger { background: var(--danger-soft); color: var(--danger); }
.btn-link { background: none; color: var(--brand); padding: 0; height: auto; min-height: 0; border: 0; font-weight: 500; border-radius: 2px; }
.btn-link:active:not(:disabled) { transform: none; }

@media (hover: hover) and (pointer: fine) {
  .btn-primary:hover:not(:disabled) { background: color-mix(in srgb, var(--ink) 88%, var(--surface)); }
  .btn-secondary:hover:not(:disabled) { border-color: var(--ink-4); }
  .btn-ghost:hover:not(:disabled) { background: var(--surface-2); color: var(--ink); }
  .btn-danger:hover:not(:disabled) { background: color-mix(in srgb, var(--danger) 22%, var(--danger-soft)); }
  .btn-link:hover:not(:disabled) { text-decoration: underline; text-underline-offset: 3px; }
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
