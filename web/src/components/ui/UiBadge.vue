<script setup>
// tone: neutral | brand | ok | warn | danger | info. Pass `color` for a data colour (area, account).
defineProps({
  tone: { type: String, default: 'neutral' },
  color: { type: String, default: '' },
  dot: { type: Boolean, default: false },
})
</script>

<template>
  <span class="badge" :class="`tone-${tone}`" :style="color ? { '--data': color } : null">
    <span v-if="dot" class="dot" aria-hidden="true"></span>
    <slot />
  </span>
</template>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 20px;
  padding: 0 7px;
  border-radius: var(--r-pill);
  font-size: var(--fs-xs);
  font-weight: 600;
  letter-spacing: 0.02em;
  line-height: 1;
  white-space: nowrap;
  background: var(--surface-2);
  color: var(--ink-2);
  font-variant-numeric: tabular-nums;
}
.dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.tone-brand { background: var(--brand-soft); color: var(--brand); }
.tone-ok { background: var(--ok-soft); color: var(--ok); }
.tone-warn { background: var(--warn-soft); color: var(--warn); }
.tone-danger { background: var(--danger-soft); color: var(--danger); }
.tone-info { background: var(--info-soft); color: var(--info); }
.badge[style*='--data'] { background: color-mix(in srgb, var(--data) 14%, transparent); color: color-mix(in srgb, var(--data) 78%, var(--ink)); }
</style>
