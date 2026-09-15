<script setup>
import { PhCaretLeft, PhCaretRight } from '@phosphor-icons/vue'
import { addDays, formatDay, mondayOf } from '../../lib/dates'

const props = defineProps({ weekStart: { type: String, required: true } })
const emit = defineEmits(['change'])
</script>

<template>
  <div class="weeknav">
    <button type="button" class="icon-btn" aria-label="Previous week" @click="emit('change', addDays(props.weekStart, -7))"><PhCaretLeft /></button>
    <span class="label num">Week of {{ formatDay(props.weekStart) }}</span>
    <button type="button" class="icon-btn" aria-label="Next week" @click="emit('change', addDays(props.weekStart, 7))"><PhCaretRight /></button>
    <button v-if="props.weekStart !== mondayOf()" type="button" class="link-btn" @click="emit('change', mondayOf())">This week</button>
  </div>
</template>

<style scoped>
.weeknav { display: inline-flex; align-items: center; gap: 4px; font-size: var(--fs-md); }
.label { min-width: 132px; text-align: center; color: var(--ink-2); font-weight: 500; }
.link-btn { margin-left: var(--sp-2); }
</style>
