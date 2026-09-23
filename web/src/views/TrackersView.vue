<script setup>
import { computed, ref, watch } from 'vue'
import { PhCaretDown, PhChartLineUp, PhCheck, PhMinus } from '@phosphor-icons/vue'
import LineChart from '../components/trackers/LineChart.vue'
import TrackerForm from '../components/trackers/TrackerForm.vue'
import TrackerSeriesChart from '../components/trackers/TrackerSeriesChart.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import { useReady } from '../composables/useReady'
import { useMediaQuery } from '../composables/useMediaQuery'
import { useLongPress } from '../composables/useLongPress'
import { useToast } from '../composables/useToast'
import WeekNav from '../components/shared/WeekNav.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiEmpty from '../components/ui/UiEmpty.vue'
import { shortDay, today } from '../lib/dates'
import { useTrackersStore } from '../stores/trackers'

const store = useTrackersStore()
const toast = useToast()
const error = ref('')
const editing = ref(null) // null | 'new' | tracker
const saving = ref(false)
const charts = ref({})

const ready = useReady(() => store.load())
const phone = useMediaQuery('(max-width: 699px)')

const metToday = computed(() => store.trackers.filter((t) => isGrid(t) && t.days.find((d) => d.date === today())?.met).length)
const gridTrackers = computed(() => store.trackers.filter(isGrid))
// A tap on a bool or count cell counts one; the toast offers Undo for a mis-tap. Value cells
// ask for the number. A long press or right-click on any cell asks for the exact value
// (empty clears it), so a count can be corrected as well as taken back.
const press = useLongPress((payload) => promptValue(payload.t, payload.d))
function cellTap(t, d) {
  if (press.consumed()) return
  if (!d || d.date > today()) return
  if (isGrid(t)) change(t, d, () => store.tick(t.id, d.date))
  else promptValue(t, d)
}
function cellPress(t, d) {
  return !d || d.date > today() ? {} : press.handlers({ t, d })
}
function cellMinus(t, d) {
  change(t, d, () => store.untick(t.id, d.date))
}
function describe(t, d, value) {
  const day = d.date === today() ? 'today' : shortDay(d.date)
  if (t.type === 'daily_bool') return `${t.name} ${value ? 'ticked' : 'unticked'} ${day}`
  if (value === null || value === undefined) return `${t.name} ${day} cleared`
  return `${t.name} ${day}: ${value}${t.unit ? ' ' + t.unit : ''}`
}
// Runs a cell write and shows a toast with Undo that puts the previous value back.
async function change(t, d, write) {
  await run(async () => {
    const { previous, value } = await write()
    toast.undo(describe(t, d, value), () => run(() => store.revert(t.id, d.date, previous)))
  })
}
function cellState(t, d) {
  if (d.date > today()) return 'future'
  if (d.met) return 'hit'
  if (d.value) return 'part'
  return 'none'
}
function cellText(t, d) {
  if (d.date > today()) return ''
  if (t.type === 'daily_bool') return d.met ? '\u2022' : ''
  return d.value === null || d.value === undefined ? '' : String(d.value)
}

async function run(fn) {
  error.value = ''
  try {
    await fn()
  } catch (err) {
    error.value = err.message
  }
}

function isGrid(t) {
  return t.type === 'daily_bool' || t.type === 'weekly_count'
}

async function save(body) {
  saving.value = true
  try {
    await run(async () => {
      if (editing.value === 'new') await store.create(body)
      else await store.update(editing.value.id, body)
      editing.value = null
    })
  } finally {
    saving.value = false
  }
}

// Clicking a habit opens its chart for the whole run since it was created.
async function toggleChart(t) {
  if (charts.value[t.id]) {
    delete charts.value[t.id]
    return
  }
  await run(async () => {
    charts.value[t.id] = await store.history(t.id, 'all')
  })
}

// Value trackers plot the daily values; bool and count trackers plot the weekly totals once
// there are at least three weeks, and the daily values before that so a young habit still shows a line.
function weeklyChart(t, h) {
  return isGrid(t) && h.weeks >= 3
}
function chartPoints(t, h) {
  if (weeklyChart(t, h)) return h.weekly.map((w) => ({ date: w.week_start, value: w.sum }))
  return h.points
}
function chartTarget(t, h) {
  if (weeklyChart(t, h)) return t.type === 'daily_bool' ? 7 : t.target_value || null
  return t.target_period === 'day' ? t.target_value : null
}
function chartSummary(t, h) {
  const n = h.points.length
  const since = h.from
  if (t.type === 'daily_bool') {
    const done = h.points.filter((p) => p.value >= 1).length
    return `${done} of ${n} days done since ${since}, ${h.weeks} weeks`
  }
  const total = h.points.reduce((a, p) => a + (p.value || 0), 0)
  const avg = n ? Math.round((total / n) * 10) / 10 : 0
  if (t.type === 'weekly_count') return `${Math.round(total * 10) / 10} total since ${since}, ${h.weeks} weeks`
  return `${n} entries since ${since}, average ${avg}${t.unit ? ' ' + t.unit : ''}`
}

function promptValue(t, day) {
  if (day.date > today()) return
  const current = day.value ?? ''
  const what = t.type === 'daily_bool' ? '1 for done, 0 or empty for not done' : t.type === 'weekly_count' ? 'count, empty to clear' : (t.unit || 'value') + ', empty to clear'
  const answer = window.prompt(`${t.name} on ${day.date} (${what}):`, current)
  if (answer === null) return
  if (answer.trim() === '') return change(t, day, () => store.clearEntry(t.id, day.date))
  const value = Number(answer)
  if (Number.isNaN(value) || value < 0) return
  change(t, day, async () => {
    const out = await store.setEntry(t.id, day.date, value)
    if (charts.value[t.id]) charts.value[t.id] = await store.history(t.id, 'all')
    return out
  })
}

watch(() => store.version, async () => {
  for (const id of Object.keys(charts.value)) charts.value[id] = await store.history(id, 'all')
})

function cellLabel(t, day) {
  if (day.value === null || day.value === undefined) return ''
  if (t.type === 'daily_bool') return ''
  return day.value
}

function archive(t) {
  run(() => store.update(t.id, { active: !t.active }))
}

function remove(t) {
  if (window.confirm(`Delete tracker "${t.name}" and all its entries?`)) run(() => store.remove(t.id))
}
</script>

<template>
  <div class="trackers">
    <PageHeader v-if="!phone" title="Tracking">
      <WeekNav :week-start="store.weekStart" @change="run(() => store.setWeek($event))" />
      <label class="check"><input v-model="store.includeInactive" type="checkbox" @change="store.load()" /> Show archived</label>
      <UiButton variant="primary" @click="editing = 'new'">New tracker</UiButton>
    </PageHeader>
    <div v-else class="phead">
      <div><h1>Tracking</h1><span class="muted small">{{ metToday }} of {{ gridTrackers.length }} met today</span></div>
      <UiButton variant="primary" size="sm" @click="editing = 'new'">New tracker</UiButton>
    </div>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>
    <UiLoadGate :ready="ready" label="Loading trackers">
    <TrackerSeriesChart v-if="store.trackers.length" :refresh-key="store.week" />
    <div v-if="editing" class="card">
      <div class="card-head"><h2>{{ editing === 'new' ? 'New tracker' : 'Edit tracker' }}</h2></div>
      <TrackerForm :tracker="editing === 'new' ? null : editing" :busy="saving" @save="save" @cancel="editing = null" />
    </div>

    <div v-if="!store.trackers.length" class="card">
      <UiEmpty title="No trackers yet" hint="Creatine, vitamins, sauna, weight, sleep: anything you want to see per week.">
        <template #icon><PhChartLineUp /></template>
        <template #action><UiButton variant="primary" @click="editing = 'new'">New tracker</UiButton></template>
      </UiEmpty>
    </div>

    <template v-if="phone && store.trackers.length">
      <section class="card">
        <h2 class="ptitle">Today</h2>
        <div class="chips">
          <button v-for="t in store.trackers" :key="t.id" type="button" class="chip" :class="{ met: t.days.find((d) => d.date === today())?.met, some: t.days.find((d) => d.date === today())?.value && !t.days.find((d) => d.date === today())?.met }" v-bind="cellPress(t, t.days.find((d) => d.date === today()))" @click="cellTap(t, t.days.find((d) => d.date === today()))">
            <span class="dot" :style="{ background: t.area_color || 'var(--ink-3)' }"></span>{{ t.name }}
            <span v-if="t.type === 'weekly_count'" class="count num">{{ t.week_total }}<span v-if="t.target_value">/{{ t.target_value }}</span></span>
            <span v-else-if="!isGrid(t)" class="count num">{{ cellLabel(t, t.days.find((d) => d.date === today())) || (t.unit || '') }}</span>
            <PhCheck v-else-if="t.days.find((d) => d.date === today())?.met" class="mark" weight="bold" />
          </button>
        </div>
      </section>
      <section class="card">
        <div class="card-head"><h2>This week</h2><span class="meta"><WeekNav :week-start="store.weekStart" compact @change="run(() => store.setWeek($event))" /></span></div>
        <template v-for="t in store.trackers" :key="t.id">
          <div class="wrow">
            <button type="button" class="tname" :aria-expanded="Boolean(charts[t.id])" @click="toggleChart(t)"><span class="dot" :style="{ background: t.area_color || 'var(--ink-3)' }"></span>{{ t.name }}</button>
            <span class="cells">
              <button v-for="d in t.days" :key="d.date" type="button" class="dcell" :class="[cellState(t, d), { today: d.date === today() }]" :aria-label="`${t.name} ${d.date}`" :disabled="d.date > today()" v-bind="cellPress(t, d)" @click="cellTap(t, d)">{{ cellText(t, d) }}</button>
            </span>
            <button type="button" class="link-btn edit" @click="editing = t">edit</button>
          </div>
          <div v-if="charts[t.id]" class="pchart">
            <LineChart :points="chartPoints(t, charts[t.id])" :target="chartTarget(t, charts[t.id])" :unit="weeklyChart(t, charts[t.id]) ? 'per week' : t.unit || ''" />
            <div class="muted xs">{{ chartSummary(t, charts[t.id]) }}</div>
          </div>
        </template>
      </section>
    </template>

    <section v-for="group in store.grouped" v-else :key="group.area" class="card group">
      <div class="card-head">
        <h2><span class="dot" :style="{ background: group.color }" aria-hidden="true"></span>{{ group.area }}</h2>
      </div>
      <div class="table-wrap">
        <table class="ui grid">
          <thead>
            <tr>
              <th class="name"></th>
              <th v-for="d in store.week.trackers[0].days" :key="d.date" class="day" :class="{ today: d.date === today() }">{{ shortDay(d.date) }}</th>
              <th class="num">week</th>
              <th class="num">streak</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <template v-for="t in group.trackers" :key="t.id">
              <tr :class="{ inactive: !t.active }">
                <td class="name">
                  <button type="button" class="tname" :aria-expanded="Boolean(charts[t.id])" :title="charts[t.id] ? 'Hide chart' : 'Show chart since created'" @click="toggleChart(t)">
                    {{ t.name }}<PhCaretDown class="caret" :class="{ open: charts[t.id] }" aria-hidden="true" />
                  </button>
                  <div class="muted xs">
                    {{ t.type.replace('_', ' ') }}<span v-if="t.target_value && t.type !== 'daily_bool'">, target {{ t.target_value }}{{ t.unit ? ' ' + t.unit : '' }} per {{ t.target_period }}</span>
                  </div>
                </td>
                <td v-for="d in t.days" :key="d.date" class="cell" :class="{ met: d.met, has: d.value !== null, today: d.date === today(), future: d.date > today(), count: t.type !== 'daily_bool' }">
                  <button v-if="isGrid(t)" type="button" class="tick" :class="{ bool: t.type === 'daily_bool' }" :title="d.note || (t.type === 'daily_bool' ? 'Click to toggle' : 'Click for +1, right-click to set a value')" :aria-label="`${t.name} ${d.date}`" :aria-pressed="t.type === 'daily_bool' ? Boolean(d.met) : undefined" :disabled="d.date > today()" v-bind="cellPress(t, d)" @click="cellTap(t, d)">
                    <PhCheck v-if="t.type === 'daily_bool' && d.met" weight="bold" class="mark" />
                    <span v-else class="num">{{ cellLabel(t, d) }}</span>
                  </button>
                  <button v-else type="button" class="tick value" :title="d.note || 'Click to set a value'" :aria-label="`${t.name} ${d.date}`" :disabled="d.date > today()" @click="promptValue(t, d)"><span class="num">{{ cellLabel(t, d) }}</span></button>
                  <button v-if="t.type !== 'daily_bool' && d.value" type="button" class="minus" :aria-label="`${t.name} ${d.date}: one less`" title="One less" @click.stop="cellMinus(t, d)"><PhMinus weight="bold" /></button>
                </td>
                <td class="num">
                  <span v-if="t.type === 'daily_bool'">{{ Math.round(t.completion * 100) }}%</span>
                  <span v-else>{{ Math.round(t.week_total * 10) / 10 }}<span v-if="t.target_value && t.target_period === 'week'" class="muted"> / {{ t.target_value }}</span></span>
                </td>
                <td class="num">{{ t.streak }}</td>
                <td class="actions">
                  <button type="button" class="link-btn" @click="toggleChart(t)">{{ charts[t.id] ? 'hide chart' : 'chart' }}</button>
                  <button type="button" class="link-btn" @click="editing = t">edit</button>
                  <button type="button" class="link-btn" @click="archive(t)">{{ t.active ? 'archive' : 'restore' }}</button>
                  <button type="button" class="link-btn danger" @click="remove(t)">delete</button>
                </td>
              </tr>
              <tr v-if="charts[t.id]" class="chart-row">
                <td :colspan="11">
                  <LineChart :points="chartPoints(t, charts[t.id])" :target="chartTarget(t, charts[t.id])" :unit="weeklyChart(t, charts[t.id]) ? 'per week' : t.unit || ''" />
                  <div class="muted xs sums">
                    <span>{{ chartSummary(t, charts[t.id]) }}</span>
                    <span v-if="!isGrid(t)" class="weeks">Weekly sums:
                      <span v-for="w in charts[t.id].weekly.slice(-8)" :key="w.week_start" class="num">{{ w.week_start.slice(5) }}: {{ Math.round(w.sum * 10) / 10 }}</span>
                    </span>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </section>
    </UiLoadGate>
  </div>
</template>

<style scoped>
.phead { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-2); margin-bottom: var(--sp-4); }
.phead h1 { font-size: var(--fs-title); }
.ptitle { margin-bottom: 10px; }
.chips { display: flex; flex-wrap: wrap; gap: var(--sp-2); }
.chip { display: inline-flex; align-items: center; gap: 8px; height: 32px; padding: 0 12px; border-radius: var(--r-pill); border: 1px solid var(--line-2); background: var(--surface); color: var(--ink); font-size: var(--fs-md); font-weight: 500; transition: background-color var(--dur-hover) ease, border-color var(--dur-hover) ease, color var(--dur-hover) ease, transform var(--dur-press) var(--ease-out); }
.chip:active { transform: scale(0.97); }
.chip.met { background: var(--ok-soft); border-color: transparent; color: var(--ok); }
.chip.some { background: var(--warn-soft); border-color: transparent; color: var(--warn); }
.chip .count { color: var(--ink-3); font-size: var(--fs-sm); }
.chip.met .count { color: inherit; }
.wrow { display: grid; grid-template-columns: minmax(0, 1fr) auto; grid-template-areas: 'name edit' 'cells cells'; gap: 6px 8px; align-items: center; padding: 10px 0; border-top: 1px solid var(--line); }
.wrow > .tname { grid-area: name; }
.wrow > .cells { grid-area: cells; }
.wrow > .edit { grid-area: edit; }
.wrow .tname { display: inline-flex; align-items: center; gap: 8px; font-size: var(--fs-base); font-weight: 500; min-width: 0; max-width: 100%; min-height: 36px; }
.wrow .tname > span:last-child, .wrow .tname { white-space: nowrap; }
.wrow .tname { overflow: hidden; text-overflow: ellipsis; display: block; }
.wrow .tname .dot { display: inline-block; margin-right: 8px; vertical-align: middle; }
.cells { display: flex; gap: 4px; width: 100%; }
.dcell { flex: 1; max-width: 40px; height: 34px; border-radius: var(--r-sm); border: 0; padding: 0; background: var(--surface-2); color: var(--ink-3); font-size: var(--fs-xs); font-weight: 500; display: inline-flex; align-items: center; justify-content: center; }
.dcell.hit { background: var(--ok-soft); color: var(--ok); }
.dcell.part { background: var(--warn-soft); color: var(--warn); }
.dcell.future { opacity: 0.35; }
.dcell.today { box-shadow: 0 0 0 1px var(--brand) inset; }
.wrow .edit { font-size: var(--fs-xs); }
.pchart { padding: 4px 0 10px; }
.check { display: flex; align-items: center; gap: 6px; font-size: var(--fs-md); white-space: nowrap; }
.card-head h2 { display: flex; align-items: center; gap: 8px; }
.dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.grid th.day { text-align: center; }
.grid th.today { color: var(--brand); }
.grid td { text-align: center; padding: 6px 4px; }
.grid td.name { text-align: left; min-width: 150px; padding-left: 0; }
.tname { font: inherit; font-weight: 500; color: var(--ink); background: none; border: 0; padding: 0; cursor: pointer; display: inline-flex; align-items: center; gap: 4px; text-align: left; }
.caret { width: 12px; height: 12px; color: var(--ink-3); transition: transform var(--dur-hover) var(--ease-out); }
.caret.open { transform: rotate(180deg); }
@media (hover: hover) and (pointer: fine) { .tname:hover { text-decoration: underline; text-underline-offset: 3px; } }
tr.inactive { opacity: 0.55; }
.tick {
  width: 34px;
  height: 32px;
  padding: 0;
  border-radius: var(--r-md);
  border: 1px solid var(--line);
  background: var(--surface);
  color: var(--ink-3);
  font-size: var(--fs-md);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: background-color var(--dur-hover) ease, border-color var(--dur-hover) ease, color var(--dur-hover) ease, transform var(--dur-press) var(--ease-out);
}
.tick.value { width: 48px; }
.cell { position: relative; }
.minus { position: absolute; top: 1px; right: 2px; width: 16px; height: 16px; padding: 0; border: 0; border-radius: 50%; background: var(--ink); color: var(--on-ink); display: none; align-items: center; justify-content: center; cursor: pointer; box-shadow: var(--shadow-1); }
.minus :deep(svg) { width: 10px; height: 10px; }
@media (hover: hover) and (pointer: fine) { .cell.count:hover .minus { display: inline-flex; } }
.tick, .dcell, .chip { touch-action: manipulation; -webkit-touch-callout: none; user-select: none; -webkit-user-select: none; }
.tick:active { transform: scale(0.94); }
.mark { width: 14px; height: 14px; }
.cell.has .tick { color: var(--ink); background: var(--surface-2); }
.cell.met .tick { background: var(--ok-soft); border-color: transparent; color: var(--ok); }
.cell.today .tick { border-color: var(--brand); }
.cell.future .tick { opacity: 0.5; }
@media (hover: hover) and (pointer: fine) { .tick:hover { border-color: var(--line-2); } }
.actions { white-space: nowrap; text-align: right; }
.actions .link-btn { margin-left: var(--sp-2); }
.link-btn.danger { color: var(--danger); }
.chart-row td { padding: var(--sp-3) 0 var(--sp-4); text-align: left; }
.sums { display: flex; flex-wrap: wrap; gap: var(--sp-3); margin-top: 4px; }
.weeks { display: inline-flex; flex-wrap: wrap; gap: var(--sp-2); }
</style>
