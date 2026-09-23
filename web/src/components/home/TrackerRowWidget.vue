<script setup>
import { useLoadTask } from '../../composables/useReady'
import { useWidgetLink } from '../../composables/useWidgetLink'
import { useLongPress } from '../../composables/useLongPress'
import { useToast } from '../../composables/useToast'
import { computed, onMounted, ref } from 'vue'
import { PhCheck } from '@phosphor-icons/vue'
import { deleteEntry, tickTracker, trackerWeek, upsertEntry } from '../../api/trackers'
import { today } from '../../lib/dates'

const settle = useLoadTask()
const toast = useToast()

const week = ref(null)
const failed = ref(false)

const quick = computed(() => (week.value?.trackers || []).filter((t) => t.type === 'daily_bool' || t.type === 'weekly_count'))

function todayCell(t) {
  return t.days.find((d) => d.date === today())
}

async function load() {
  try {
    week.value = await trackerWeek()
    failed.value = false
  } catch {
    failed.value = true
  }
}

// The response carries the tracker's refreshed row; swap it in instead of reloading the week.
function patch(res) {
  if (!res?.row || !week.value) return
  const i = week.value.trackers.findIndex((t) => t.id === res.row.id)
  if (i !== -1) week.value.trackers[i] = res.row
}

function describe(t, value) {
  if (t.type === 'daily_bool') return `${t.name} ${value ? 'ticked' : 'unticked'} today`
  return value === null || value === undefined ? `${t.name} today cleared` : `${t.name} today: ${value}`
}

async function write(t, call) {
  const previous = todayCell(t)?.value ?? null
  try {
    const res = await call()
    patch(res)
    toast.undo(describe(t, res?.value ?? null), async () => {
      try {
        patch(previous === null ? await deleteEntry(t.id, today()) : await upsertEntry(t.id, { date: today(), value: previous }))
      } catch (err) {
        toast.error(err.message)
      }
    })
  } catch (err) {
    toast.error(err.message)
  }
}

// Tap counts one; a long press or right-click asks for the exact value (empty clears).
const press = useLongPress((t) => {
  const current = todayCell(t)?.value ?? ''
  const answer = window.prompt(`${t.name} today (${t.type === 'daily_bool' ? '1 done, 0 not done' : 'count, empty to clear'}):`, current)
  if (answer === null) return
  if (answer.trim() === '') return write(t, () => deleteEntry(t.id, today()))
  const value = Number(answer)
  if (Number.isNaN(value) || value < 0) return
  write(t, () => upsertEntry(t.id, { date: today(), value }))
})
function tick(t) {
  if (press.consumed()) return
  write(t, () => tickTracker(t.id, today()))
}

onMounted(() => load().finally(settle))
const link = useWidgetLink('trackers')
</script>

<template>
  <section v-if="!failed && week && quick.length" class="card widget clickable" tabindex="0" role="link" :aria-label="'Open trackers'" @click="link.onClick" @keydown="link.onKey">
    <div class="card-head">
      <h2>Trackers today</h2>
      <span class="meta"><RouterLink :to="{ name: 'trackers' }">Tracking</RouterLink></span>
    </div>
    <div class="chips">
      <button
        v-for="t in quick"
        :key="t.id"
        type="button"
        class="chip"
        :class="{ met: todayCell(t)?.met, some: todayCell(t)?.value && !todayCell(t)?.met }"
        :aria-pressed="Boolean(todayCell(t)?.met)"
        :title="t.type === 'weekly_count' ? `${t.week_total} of ${t.target_value || '?'} this week. Click for +1, right-click to set` : `streak ${t.streak}`"
        v-bind="press.handlers(t)"
        @click.stop="tick(t)"
      >
        <span class="dot" :style="{ background: t.area_color || 'var(--ink-3)' }" aria-hidden="true"></span>
        {{ t.name }}
        <span v-if="t.type === 'weekly_count'" class="count num">{{ t.week_total }}<span v-if="t.target_value">/{{ t.target_value }}</span></span>
        <PhCheck v-else-if="todayCell(t)?.met" class="check" weight="bold" />
      </button>
    </div>
  </section>
</template>

<style scoped>
.chips { display: flex; flex-wrap: wrap; gap: var(--sp-2); }
.chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 32px;
  padding: 0 12px;
  border-radius: var(--r-pill);
  border: 1px solid var(--line-2);
  background: var(--surface);
  color: var(--ink);
  font-size: var(--fs-md);
  font-weight: 500;
  touch-action: manipulation;
  -webkit-touch-callout: none;
  user-select: none;
  -webkit-user-select: none;
  transition: background-color var(--dur-hover) ease, border-color var(--dur-hover) ease, color var(--dur-hover) ease, transform var(--dur-press) var(--ease-out);
}
.chip:active { transform: scale(0.97); }
.chip.met { background: var(--ok-soft); border-color: transparent; color: var(--ok); }
.chip.some { background: var(--warn-soft); border-color: transparent; color: var(--warn); }
@media (hover: hover) and (pointer: fine) { .chip:not(.met):not(.some):hover { background: var(--surface-2); } }
.dot { width: 8px; height: 8px; border-radius: 50%; }
.count { color: var(--ink-3); font-size: var(--fs-sm); }
.chip.met .count { color: inherit; }
.check { width: 14px; height: 14px; }
</style>
