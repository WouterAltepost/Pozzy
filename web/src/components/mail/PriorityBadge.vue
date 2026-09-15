<script setup>
import UiBadge from '../ui/UiBadge.vue'

defineProps({ priority: { type: Number, default: 3 } })
const LABELS = { 1: 'P1', 2: 'P2', 3: 'P3', 4: 'P4' }
const TITLES = { 1: 'Urgent', 2: 'Important', 3: 'Normal', 4: 'Low or noise' }
const TONES = { 1: 'danger', 2: 'warn', 3: 'info', 4: 'neutral' }
</script>

<template>
  <UiBadge :tone="TONES[priority] || 'info'" :title="TITLES[priority]" class="num">{{ LABELS[priority] || 'P3' }}</UiBadge>
</template>
