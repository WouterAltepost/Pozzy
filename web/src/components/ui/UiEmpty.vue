<script setup>
defineProps({
  title: { type: String, required: true },
  hint: { type: String, default: '' },
  compact: { type: Boolean, default: false },
})
</script>

<template>
  <div class="empty" :class="{ compact }">
    <span v-if="$slots.icon" class="icon" aria-hidden="true"><slot name="icon" /></span>
    <div class="text">
      <div class="title">{{ title }}</div>
      <div v-if="hint" class="hint">{{ hint }}</div>
    </div>
    <div v-if="$slots.action" class="action"><slot name="action" /></div>
  </div>
</template>

<style scoped>
.empty { display: flex; flex-direction: column; align-items: center; text-align: center; gap: var(--sp-2); padding: var(--sp-6) var(--sp-4); color: var(--ink-2); }
.empty.compact { flex-direction: row; text-align: left; padding: var(--sp-2) 0; gap: var(--sp-3); }
.icon { color: var(--ink-3); display: inline-flex; }
.icon :deep(svg) { width: 26px; height: 26px; }
.compact .icon :deep(svg) { width: 18px; height: 18px; }
.title { font-size: var(--fs-base); font-weight: 500; color: var(--ink-2); }
.hint { font-size: var(--fs-sm); color: var(--ink-3); }
.action { margin-top: var(--sp-1); }
.compact .action { margin: 0 0 0 auto; }
</style>
