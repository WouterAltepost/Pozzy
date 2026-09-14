<script setup>
defineProps({ priority: { type: Number, default: 3 } })
const LABELS = { 1: 'P1', 2: 'P2', 3: 'P3', 4: 'P4' }
const TITLES = { 1: 'Urgent', 2: 'Important', 3: 'Normal', 4: 'Low or noise' }
</script>

<template>
  <span class="badge" :class="'p' + priority" :title="TITLES[priority]">{{ LABELS[priority] || 'P3' }}</span>
</template>

<style scoped>
.badge { font-size: 0.7rem; font-weight: 700; padding: 0.05rem 0.35rem; border-radius: 3px; background: #f3f4f6; color: #374151; letter-spacing: 0.02em; }
.p1 { background: #fee2e2; color: #b91c1c; }
.p2 { background: #ffedd5; color: #c2410c; }
.p3 { background: #e5e7eb; color: #374151; }
.p4 { background: #f3f4f6; color: #9ca3af; }
</style>
