<script setup>
import { addDays, formatDay, mondayOf } from '../../lib/dates'

const props = defineProps({ weekStart: { type: String, required: true } })
const emit = defineEmits(['change'])
</script>

<template>
  <div class="weeknav">
    <button type="button" @click="emit('change', addDays(props.weekStart, -7))">&lsaquo;</button>
    <span>Week of {{ formatDay(props.weekStart) }}</span>
    <button type="button" @click="emit('change', addDays(props.weekStart, 7))">&rsaquo;</button>
    <button v-if="props.weekStart !== mondayOf()" type="button" class="link" @click="emit('change', mondayOf())">This week</button>
  </div>
</template>

<style scoped>
.weeknav { display: flex; align-items: center; gap: 0.5rem; font-size: 0.9rem; }
.link { border: none; background: none; color: #2563eb; padding: 0.2rem 0.4rem; }
</style>
