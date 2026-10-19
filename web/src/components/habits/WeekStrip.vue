<script setup>
// The week above the Today list: seven days, each with a small ring of how much of that day's
// due habits were done. Tap a day to check in for it; arrows move a week. Future days are shown
// but cannot be picked.
import { computed } from 'vue'
import { PhCaretLeft, PhCaretRight } from '@phosphor-icons/vue'
import ProgressRing from './ProgressRing.vue'
import { addDays } from '../../lib/dates'
import { WEEKDAY_LETTERS, cellOf, isWeekly } from '../../lib/habits'

const props = defineProps({
  weekStart: { type: String, required: true },
  trackers: { type: Array, default: () => [] },
  day: { type: String, required: true },
  today: { type: String, required: true },
})
const emit = defineEmits(['select'])

const days = computed(() =>
  Array.from({ length: 7 }, (_, i) => {
    const date = addDays(props.weekStart, i)
    let due = 0
    let done = 0
    for (const t of props.trackers) {
      if (isWeekly(t)) continue
      const c = cellOf(t, date)
      if (!c || c.status === 'skipped') continue
      if (c.met) {
        done += 1
        due += 1
      } else if (c.due) due += 1
    }
    return { date, n: Number(date.slice(8)), letter: WEEKDAY_LETTERS[i], due, done, future: date > props.today }
  }),
)
const canNext = computed(() => addDays(props.weekStart, 7) <= props.today)
</script>

<template>
  <div class="strip" role="group" aria-label="Pick a day">
    <button type="button" class="nav" aria-label="Previous week" @click="emit('select', addDays(day, -7))"><PhCaretLeft weight="bold" /></button>
    <div class="days">
      <button
        v-for="d in days"
        :key="d.date"
        type="button"
        class="d"
        :class="{ sel: d.date === day, now: d.date === today, future: d.future }"
        :disabled="d.future"
        :aria-pressed="d.date === day"
        :aria-label="`${d.date}: ${d.done} of ${d.due} done`"
        @click="emit('select', d.date)"
      >
        <span class="letter">{{ d.letter }}</span>
        <ProgressRing :value="d.done" :total="d.due" :size="34" :stroke="3">
          <span class="n num">{{ d.n }}</span>
        </ProgressRing>
      </button>
    </div>
    <button type="button" class="nav" aria-label="Next week" :disabled="!canNext" @click="emit('select', addDays(day, 7) > today ? today : addDays(day, 7))"><PhCaretRight weight="bold" /></button>
  </div>
</template>

<style scoped>
.strip { display: flex; align-items: center; gap: 4px; }
.days { flex: 1; display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 2px; }
.nav { flex: none; width: 32px; height: 32px; border: 0; border-radius: 50%; background: transparent; color: var(--ink-3); display: inline-grid; place-items: center; }
.nav:disabled { opacity: 0.3; }
.nav :deep(svg) { width: 14px; height: 14px; }
@media (hover: hover) and (pointer: fine) { .nav:hover:not(:disabled) { background: var(--surface-2); color: var(--ink); } }
.d { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 6px 0 8px; border: 0; border-radius: var(--r-lg); background: transparent; color: var(--ink-2); transition: background-color var(--dur-hover) ease; }
.d:disabled { opacity: 0.35; }
.letter { font-size: var(--fs-xs); font-weight: 600; letter-spacing: 0.06em; color: var(--ink-3); }
.n { font-size: var(--fs-md); font-weight: 600; color: var(--ink-2); }
.now .letter { color: var(--brand); }
.sel { background: var(--surface); box-shadow: inset 0 1px 0 var(--edge), var(--shadow-1), 0 0 0 1px var(--line); }
.sel .n { color: var(--ink); }
@media (hover: hover) and (pointer: fine) { .d:not(.sel):not(:disabled):hover { background: var(--surface-2); } }
</style>
