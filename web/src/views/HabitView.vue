<script setup>
// One habit in depth: current and best streak, rates, a year heatmap, completion per month and
// per weekday, the history chart and the notes written on check-ins. Check in for today, edit,
// archive or delete from here.
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { PhArrowLeft, PhBell, PhFlame, PhTrophy } from '@phosphor-icons/vue'
import CheckInSheet from '../components/habits/CheckInSheet.vue'
import HabitEditor from '../components/habits/HabitEditor.vue'
import HabitIcon from '../components/habits/HabitIcon.vue'
import Heatmap from '../components/habits/Heatmap.vue'
import RateBars from '../components/habits/RateBars.vue'
import LineChart from '../components/trackers/LineChart.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiConfirm from '../components/ui/UiConfirm.vue'
import UiEmpty from '../components/ui/UiEmpty.vue'
import UiSkeleton from '../components/ui/UiSkeleton.vue'
import { useToast } from '../composables/useToast'
import { formatDay, today as todayFn } from '../lib/dates'
import { WEEKDAYS, cellOf, fmt, isBool, isCount, isWeekly, nextDueLabel, scheduleLabel, targetLabel, unitOf } from '../lib/habits'
import { useTrackersStore } from '../stores/trackers'

const route = useRoute()
const router = useRouter()
const store = useTrackersStore()
const toast = useToast()
const today = todayFn()
const id = computed(() => String(route.params.id))
const stats = ref(null)
const history = ref(null)
const error = ref('')
const loading = ref(true)

async function load() {
  loading.value = true
  error.value = ''
  try {
    if (!store.byId(id.value) || store.weekStart !== store.week?.week_start) {
      store.includeInactive = true
      await store.load()
    }
    const [s, h] = await Promise.all([store.loadStats(id.value), store.history(id.value, 'all')])
    stats.value = s
    history.value = h
  } catch (err) {
    error.value = err.status === 404 ? 'This habit does not exist any more.' : err.message
  } finally {
    loading.value = false
  }
}
watch(id, load, { immediate: true })
// Any write (here or in the sheet) drops the cached stats; fetch them again.
watch(() => store.version, async () => {
  if (!stats.value) return
  try {
    const [s, h] = await Promise.all([store.loadStats(id.value), store.history(id.value, 'all')])
    stats.value = s
    history.value = h
  } catch {
    // keep the last numbers on screen
  }
})

const row = computed(() => store.byId(id.value))
const t = computed(() => (row.value ? row.value : stats.value?.tracker ? { ...stats.value.tracker, days: [] } : null))
const unit = computed(() => (stats.value?.unit === 'week' ? 'week' : 'day'))
const plural = (n, word) => `${word}${n === 1 ? '' : 's'}`
const allNotes = ref(false)
const notes = computed(() => (allNotes.value ? stats.value?.notes || [] : (stats.value?.notes || []).slice(0, 6)))
const pct = (r) => (r === null || r === undefined ? '-' : `${Math.round(r * 100)}%`)

const monthItems = computed(() => (stats.value?.months || []).map((m) => ({ key: m.month, label: new Date(m.month + '-15T12:00:00').toLocaleDateString('en-GB', { month: 'narrow' }), ...m })))
const weekdayItems = computed(() => (stats.value?.weekdays || []).map((w) => ({ key: w.weekday, label: WEEKDAYS[w.weekday].slice(0, 2), ...w })))
const bestWeekday = computed(() => {
  const ws = (stats.value?.weekdays || []).filter((w) => w.counted >= 2 && w.rate !== null)
  if (ws.length < 3) return null
  const best = ws.reduce((a, b) => (b.rate > a.rate ? b : a))
  const worst = ws.reduce((a, b) => (b.rate < a.rate ? b : a))
  return best.rate - worst.rate >= 0.2 ? { best: WEEKDAYS[best.weekday], worst: WEEKDAYS[worst.weekday] } : null
})

// History chart: value habits plot their days; check and count habits plot weekly totals once
// there are three weeks, the days before that so a young habit still shows a line.
const weeklyChart = computed(() => t.value && (isBool(t.value) || isCount(t.value)) && history.value?.weeks >= 3)
const chartPoints = computed(() => {
  if (!history.value) return []
  // The running week is not finished; leaving it out keeps the line from diving at the end.
  if (weeklyChart.value) return history.value.weekly.slice(0, -1).map((w) => ({ date: w.week_start, value: w.sum }))
  return history.value.points
})
const chartTarget = computed(() => {
  if (!t.value) return null
  if (weeklyChart.value) return isBool(t.value) ? null : t.value.target_value || null
  return t.value.target_period === 'day' ? t.value.target_value : null
})

// Check-in for today
const sheetOpen = ref(false)
const sheetBusy = ref(false)
const todayCell = computed(() => (row.value ? cellOf(row.value, today) : null))
function describe(value, status) {
  if (status === 'skipped') return `${t.value.name} skipped today`
  if (isBool(t.value)) return `${t.value.name} ${value ? 'done' : 'not done'} today`
  return value === null || value === undefined ? `${t.value.name} cleared today` : `${t.value.name} today: ${fmt(value)}`
}
async function write(fn) {
  sheetBusy.value = true
  try {
    const { previous, value, status } = await fn()
    sheetOpen.value = false
    toast.undo(describe(value, status), () => store.revert(id.value, today, previous).catch((err) => toast.error(err.message)))
  } catch (err) {
    toast.error(err.message)
  } finally {
    sheetBusy.value = false
  }
}
const saveSheet = (b) => write(() => store.setEntry(id.value, today, b.value, b.note, b.status))
const clearSheet = () => write(() => store.clearEntry(id.value, today))

// Edit, archive, delete
const editing = ref(false)
const saving = ref(false)
const editError = ref('')
async function save(body) {
  saving.value = true
  editError.value = ''
  try {
    await store.update(id.value, body)
    editing.value = false
    stats.value = await store.loadStats(id.value)
  } catch (err) {
    editError.value = err.message
  } finally {
    saving.value = false
  }
}
async function archive() {
  try {
    const active = !t.value.active
    await store.update(id.value, { active })
    toast.success(active ? `${t.value.name} restored` : `${t.value.name} archived`)
  } catch (err) {
    toast.error(err.message)
  }
}
const deleting = ref(false)
const deleteBusy = ref(false)
async function remove() {
  deleteBusy.value = true
  try {
    await store.remove(id.value)
    router.push({ name: 'trackers' })
  } catch (err) {
    toast.error(err.message)
  } finally {
    deleteBusy.value = false
  }
}
</script>

<template>
  <div class="habit-page">
    <RouterLink :to="{ name: 'trackers' }" class="back"><PhArrowLeft /> Habits</RouterLink>

    <p v-if="error" class="error">{{ error }}</p>

    <template v-if="t">
      <header class="head">
        <HabitIcon :tracker="t" :size="56" :done="Boolean(todayCell?.met)" />
        <div class="titles">
          <span class="eyebrow">{{ t.area_name || 'No area' }} · {{ scheduleLabel(t) }}<template v-if="!t.active"> · archived</template></span>
          <h1>{{ t.name }}</h1>
          <span class="muted small sub">
            <template v-if="targetLabel(t) && !isWeekly(t)">{{ targetLabel(t) }} · </template>
            <template v-if="stats?.next_due && stats.next_due !== today">Next {{ nextDueLabel(stats.next_due, today).toLowerCase() }} · </template>
            <template v-if="stats">Since {{ formatDay(stats.since) }}</template>
            <span v-if="t.reminder_time" class="rem"><PhBell /> {{ t.reminder_time }}</span>
          </span>
        </div>
        <div class="head-actions">
          <UiButton v-if="row && t.active" variant="primary" @click="sheetOpen = true">{{ todayCell?.met ? 'Today: done' : todayCell?.status === 'skipped' ? 'Today: skipped' : 'Check in today' }}</UiButton>
          <UiButton @click="editing = true">Edit</UiButton>
        </div>
      </header>

      <div v-if="loading && !stats" class="tiles"><UiSkeleton v-for="i in 4" :key="i" height="104px" /></div>
      <div v-else-if="stats" class="tiles">
        <div class="tile">
          <span class="eyebrow">Current streak</span>
          <span class="big num"><PhFlame weight="fill" class="flame" />{{ stats.current_streak }}</span>
          <span class="muted xs">{{ plural(stats.current_streak, unit) }}</span>
        </div>
        <div class="tile">
          <span class="eyebrow">Best streak</span>
          <span class="big num"><PhTrophy weight="fill" class="trophy" />{{ stats.best_streak }}</span>
          <span class="muted xs">{{ plural(stats.best_streak, unit) }}</span>
        </div>
        <div class="tile">
          <span class="eyebrow">Last 30 days</span>
          <span class="big num">{{ pct(stats.rate_30) }}</span>
          <span class="muted xs">of the {{ unit }}s it was due</span>
        </div>
        <div class="tile">
          <template v-if="!isBool(t) && stats.value_avg !== null && !isCount(t)">
            <span class="eyebrow">Average</span>
            <span class="big num">{{ fmt(stats.value_avg) }}</span>
            <span class="muted xs">{{ unitOf(t) || 'per check-in' }}, {{ fmt(stats.value_total) }} total</span>
          </template>
          <template v-else>
            <span class="eyebrow">All time</span>
            <span class="big num">{{ pct(stats.rate_all) }}</span>
            <span class="muted xs">{{ stats.met_total }} of {{ stats.counted_total }} {{ unit }}s<template v-if="stats.skipped_total">, {{ stats.skipped_total }} skipped</template></span>
          </template>
        </div>
      </div>

      <section v-if="stats" class="card">
        <div class="card-head"><h2>Last 12 months</h2><span class="meta">{{ stats.met_total }} {{ unit === 'week' ? 'weeks met' : 'days done' }}</span></div>
        <Heatmap :cells="stats.heatmap" :color="t.area_color || ''" :target="t.target_period === 'day' ? t.target_value : null" :bool="isBool(t) || isWeekly(t)" :unit="unitOf(t)" />
        <div class="legend muted xs">
          <span><i class="sw hit" :style="{ background: t.area_color || 'var(--ok)' }"></i>done</span>
          <span><i class="sw miss"></i>missed</span>
          <span><i class="sw skip"></i>skipped</span>
          <span><i class="sw off"></i>not due</span>
        </div>
      </section>

      <div v-if="stats" class="two">
        <section class="card">
          <div class="card-head"><h2>Per month</h2><span class="meta">% of due {{ unit }}s done</span></div>
          <RateBars :items="monthItems" :color="t.area_color || ''" />
        </section>
        <section v-if="weekdayItems.length" class="card">
          <div class="card-head"><h2>Per weekday</h2><span class="meta">since the start</span></div>
          <RateBars :items="weekdayItems" :color="t.area_color || ''" />
          <p v-if="bestWeekday" class="muted small insight">Strongest on {{ bestWeekday.best }}, weakest on {{ bestWeekday.worst }}.</p>
        </section>
      </div>

      <section v-if="history && chartPoints.length > 1" class="card">
        <div class="card-head"><h2>History</h2><span class="meta">{{ weeklyChart ? 'per week' : unitOf(t) || 'per day' }}</span></div>
        <LineChart :points="chartPoints" :target="chartTarget" :unit="weeklyChart ? 'per week' : unitOf(t)" />
      </section>

      <section v-if="stats" class="card">
        <div class="card-head"><h2>Notes</h2><span class="meta">{{ stats.notes.length }}</span></div>
        <ul v-if="stats.notes.length" class="notes">
          <li v-for="n in notes" :key="n.date" class="note">
            <span class="muted xs date">{{ formatDay(n.date) }}<template v-if="n.status === 'skipped'"> · skipped</template><template v-else-if="!isBool(t) && n.value"> · {{ fmt(n.value) }} {{ unitOf(t) }}</template></span>
            <span>{{ n.note }}</span>
          </li>
        </ul>
        <button v-if="stats.notes.length > 6" type="button" class="link-btn more" @click="allNotes = !allNotes">{{ allNotes ? 'Show fewer' : `Show all ${stats.notes.length}` }}</button>
        <UiEmpty v-else-if="!stats.notes.length" compact title="No notes yet" hint="Add one when you check in: how it went, why you skipped." />
      </section>

      <div class="danger-zone">
        <UiButton variant="ghost" @click="archive">{{ t.active ? 'Archive habit' : 'Restore habit' }}</UiButton>
        <UiButton variant="danger" @click="deleting = true">Delete</UiButton>
      </div>
    </template>
    <div v-else-if="loading" class="tiles"><UiSkeleton v-for="i in 4" :key="i" height="104px" /></div>

    <CheckInSheet :open="sheetOpen" :tracker="row" :day="today" :busy="sheetBusy" @save="saveSheet" @clear="clearSheet" @close="sheetOpen = false" />
    <HabitEditor :open="editing" :tracker="t" :busy="saving" :error="editError" @save="save" @close="editing = false" />
    <UiConfirm :open="deleting" title="Delete habit?" :message="t ? `${t.name} and every check-in it has will be gone. Archive keeps the history instead.` : ''" confirm-label="Delete" danger :busy="deleteBusy" @confirm="remove" @cancel="deleting = false" />
  </div>
</template>

<style scoped>
.habit-page { max-width: 880px; margin: 0 auto; }
.back { display: inline-flex; align-items: center; gap: 6px; font-size: var(--fs-md); font-weight: 500; color: var(--ink-3); margin-bottom: var(--sp-5); }
.back :deep(svg) { width: 14px; height: 14px; }
.back:hover { color: var(--brand); text-decoration: none; }
.head { display: flex; align-items: center; gap: var(--sp-4); margin-bottom: var(--sp-6); flex-wrap: wrap; }
.titles { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 200px; }
.sub { display: inline-flex; flex-wrap: wrap; align-items: center; gap: 4px; }
.rem { display: inline-flex; align-items: center; gap: 3px; margin-left: 6px; }
.rem :deep(svg) { width: 12px; height: 12px; }
.head-actions { display: flex; gap: var(--sp-2); }
.tiles { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--sp-4); margin-bottom: var(--sp-5); }
.tile { display: flex; flex-direction: column; gap: 4px; padding: var(--sp-4) var(--sp-5); background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg); box-shadow: inset 0 1px 0 var(--edge), var(--shadow-1); min-width: 0; }
.tile-skel { height: 104px; border-radius: var(--r-lg); }
.big { display: inline-flex; align-items: center; gap: 6px; font-size: var(--fs-3xl); font-weight: 650; letter-spacing: -0.03em; line-height: 1.1; color: var(--ink); }
.big :deep(svg) { width: 22px; height: 22px; }
.flame { color: var(--warn); }
.trophy { color: var(--ink-4); }
.legend { display: flex; flex-wrap: wrap; gap: 6px 16px; margin-top: var(--sp-3); }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.sw { display: inline-block; width: 11px; height: 11px; border-radius: 3px; }
.sw.miss { background: var(--surface-3); }
.sw.off { box-shadow: inset 0 0 0 1px var(--line-2); }
.sw.skip { background: repeating-linear-gradient(135deg, var(--surface-2) 0 2px, var(--surface-3) 2px 4px); }
.two { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--sp-5); }
.two .card { margin-bottom: var(--sp-5); }
.insight { margin-top: var(--sp-3); }
.notes { display: flex; flex-direction: column; }
.note { display: flex; flex-direction: column; gap: 2px; padding: 10px 0; border-top: 1px solid var(--line); }
.note:first-child { border-top: 0; padding-top: 0; }
.date { font-variant-numeric: tabular-nums; }
.more { margin-top: var(--sp-3); }
.danger-zone { display: flex; justify-content: flex-end; gap: var(--sp-2); margin-top: var(--sp-2); }
@media (max-width: 760px) {
  .tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--sp-3); }
  .tile { padding: var(--sp-3) var(--sp-4); }
  .two { grid-template-columns: minmax(0, 1fr); gap: 0; }
  .head-actions { width: 100%; }
  .head-actions > * { flex: 1; }
}
</style>
