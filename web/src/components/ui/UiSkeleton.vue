<script setup>
defineProps({
  lines: { type: Number, default: 3 },
  height: { type: String, default: '' }, // one block of this height instead of lines
})
</script>

<template>
  <div class="skeleton" aria-busy="true" aria-live="polite">
    <span class="visually-hidden">Loading</span>
    <div v-if="height" class="sk block" :style="{ height }"></div>
    <template v-else>
      <div v-for="i in lines" :key="i" class="sk line" :style="{ width: i === lines ? '60%' : '100%' }"></div>
    </template>
  </div>
</template>

<style scoped>
.skeleton { display: flex; flex-direction: column; gap: 10px; padding: 2px 0; }
.sk { border-radius: var(--r-sm); background: var(--surface-2); position: relative; overflow: hidden; }
.line { height: 12px; }
.sk::after {
  content: '';
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--surface) 70%, transparent), transparent);
  animation: shimmer 1.6s linear infinite;
}
@keyframes shimmer { to { transform: translateX(100%); } }
@media (prefers-reduced-motion: reduce) { .sk::after { animation: none; display: none; } }
</style>
