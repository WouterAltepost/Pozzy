<script setup>
// One habit on the Today screen. The body opens the check-in sheet (value, note, skip); the
// control on the right is the one-tap action: a check for yes/no habits, +1 for counts, and
// "Log" for values. A long press or right-click on the control opens the sheet too.
import { computed } from 'vue'
import { PhCheck, PhFlame, PhNotePencil, PhPlus, PhSkipForward } from '@phosphor-icons/vue'
import HabitIcon from './HabitIcon.vue'
import { useLongPress } from '../../composables/useLongPress'
import { cellOf, dayState, fmt, isBool, isCount, isWeekly, nextDueLabel, scheduleLabel, unitOf } from '../../lib/habits'

const props = defineProps({
  tracker: { type: Object, required: true },
  day: { type: String, required: true },
  today: { type: String, required: true },
})
const emit = defineEmits(['act', 'open'])

const t = computed(() => props.tracker)
const cell = computed(() => cellOf(t.value, props.day))
const state = computed(() => dayState(t.value, cell.value, props.today))
const weekly = computed(() => isWeekly(t.value))
const done = computed(() => (weekly.value ? Boolean(t.value.week_met) : state.value === 'done'))
const skipped = computed(() => state.value === 'skipped')

const meta = computed(() => {
  const parts = []
  if (weekly.value) {
    const target = t.value.target_value
    parts.push(target ? `${fmt(t.value.week_total)} of ${fmt(target)}${isCount(t.value) ? '' : ' ' + unitOf(t.value)} this week` : `${fmt(t.value.week_total)} this week`)
  } else if (!isBool(t.value)) {
    const v = cell.value?.value
    const target = t.value.target_value
    if (v) parts.push(`${fmt(v)}${target ? ' / ' + fmt(target) : ''} ${unitOf(t.value)}`.trim())
    else if (target) parts.push(`Goal ${fmt(target)} ${unitOf(t.value)}`.trim())
  }
  if (state.value === 'off') parts.push(`Next ${nextDueLabel(t.value.next_due, props.today).toLowerCase()}`)
  else if (t.value.schedule !== 'daily' && !weekly.value) parts.push(scheduleLabel(t.value))
  return parts.join(' · ')
})

const press = useLongPress(() => emit('open'))
function act() {
  if (press.consumed()) return
  emit('act')
}
const actionLabel = computed(() => {
  const name = t.value.name
  if (isBool(t.value)) return done.value ? `Mark ${name} not done` : `Mark ${name} done`
  if (isCount(t.value)) return `Add one to ${name}`
  return `Log ${name}`
})
</script>

<template>
  <div class="habit" :class="[`is-${state}`, { done, skipped }]">
    <button type="button" class="body" @click="emit('open')">
      <HabitIcon :tracker="t" :done="done" />
      <span class="text">
        <span class="name">{{ t.name }}</span>
        <span class="meta">
          <span v-if="skipped" class="skip-tag"><PhSkipForward weight="bold" />Skipped</span>
          <span v-if="t.streak > 1" class="streak num"><PhFlame weight="fill" />{{ t.streak }}</span>
          <span v-if="meta" class="truncate">{{ meta }}</span>
          <PhNotePencil v-if="cell?.note" class="note-mark" :aria-label="'Note: ' + cell.note" />
        </span>
      </span>
    </button>
    <button
      type="button"
      class="action"
      :class="{ bool: isBool(t), count: isCount(t), value: !isBool(t) && !isCount(t) }"
      :aria-label="actionLabel"
      :aria-pressed="isBool(t) ? done : undefined"
      :disabled="day > today"
      v-bind="press.handlers()"
      @click="act"
    >
      <template v-if="isBool(t)">
        <PhCheck v-if="done" weight="bold" class="tick" />
      </template>
      <template v-else-if="isCount(t)">
        <PhCheck v-if="done" weight="bold" class="tick" />
        <template v-else><PhPlus weight="bold" /></template>
      </template>
      <template v-else>
        <span v-if="cell?.value && cell.status !== 'skipped'" class="num">{{ fmt(cell.value) }}</span>
        <span v-else>Log</span>
      </template>
    </button>
  </div>
</template>

<style scoped>
.habit { display: flex; align-items: center; gap: var(--sp-3); padding: 10px 0; border-top: 1px solid var(--line); }
.habit:first-child { border-top: 0; }
.body { flex: 1; min-width: 0; display: flex; align-items: center; gap: 14px; padding: 4px 0; border: 0; background: none; color: inherit; text-align: left; font: inherit; border-radius: var(--r-md); touch-action: manipulation; }
.text { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.name { font-size: var(--fs-lg); font-weight: 600; letter-spacing: -0.01em; color: var(--ink); transition: color var(--dur-ui) ease; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.meta { display: flex; align-items: center; gap: 8px; min-width: 0; font-size: var(--fs-sm); color: var(--ink-3); }
.meta :deep(svg) { width: 13px; height: 13px; flex: none; }
.streak { display: inline-flex; align-items: center; gap: 3px; color: var(--warn); font-weight: 600; }
.skip-tag { display: inline-flex; align-items: center; gap: 4px; color: var(--ink-2); font-weight: 500; }
.note-mark { color: var(--ink-4); }
.done .name { color: var(--ink-2); }
.is-off { opacity: 0.6; }

.action {
  flex: none;
  min-width: 44px;
  height: 44px;
  padding: 0;
  display: inline-grid;
  place-items: center;
  border-radius: var(--r-pill);
  border: 2px solid var(--line-2);
  background: var(--surface);
  color: var(--ink-2);
  font-size: var(--fs-md);
  font-weight: 600;
  touch-action: manipulation;
  -webkit-touch-callout: none;
  user-select: none;
  -webkit-user-select: none;
  transition: background-color var(--dur-ui) ease, border-color var(--dur-ui) ease, color var(--dur-ui) ease, transform var(--dur-press) var(--ease-out);
}
.action:active:not(:disabled) { transform: scale(0.9); }
.action:disabled { opacity: 0.35; }
.action :deep(svg) { width: 18px; height: 18px; }
.action.value { padding: 0 14px; min-width: 64px; }
.action.count { color: var(--brand); border-color: color-mix(in srgb, var(--brand) 35%, transparent); }
.done .action { background: var(--ok); border-color: var(--ok); color: #fff; }
.done .action .tick { animation: pop 420ms var(--ease-spring); }
.skipped .action { border-style: dashed; }
.is-part .action.value { border-color: color-mix(in srgb, var(--warn) 55%, transparent); color: var(--warn); }
@keyframes pop { 0% { transform: scale(0.4); } 60% { transform: scale(1.18); } 100% { transform: scale(1); } }
@media (hover: hover) and (pointer: fine) {
  .action:hover:not(:disabled) { border-color: var(--ink-4); }
  .done .action:hover:not(:disabled) { border-color: var(--ok); filter: brightness(1.05); }
  .body:hover .name { color: var(--brand); }
}
@media (prefers-reduced-motion: reduce) { .done .action .tick { animation: none; } }
</style>
