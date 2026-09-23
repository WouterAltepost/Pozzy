<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { PhCalendarCheck, PhCheck, PhX } from '@phosphor-icons/vue'
import AreaDot from '../components/shared/AreaDot.vue'
import AreaSelect from '../components/shared/AreaSelect.vue'
import TagsInput from '../components/shared/TagsInput.vue'
import WeekNav from '../components/shared/WeekNav.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import { useReady } from '../composables/useReady'
import UiButton from '../components/ui/UiButton.vue'
import UiField from '../components/ui/UiField.vue'
import UiModal from '../components/ui/UiModal.vue'
import { useMediaQuery } from '../composables/useMediaQuery'
import { formatDay, formatTime, minutesToHours, today, weekDays } from '../lib/dates'
import { useToast } from '../composables/useToast'
import { useHoursStore } from '../stores/hours'

const store = useHoursStore()
const toast = useToast()
const error = ref('')
const adding = ref(false)
const stopping = ref(false)
const now = ref(Date.now())
let ticker = null

const form = reactive({ date: today(), minutes: 30, area_id: null, tags: [], note: '' })
const phone = useMediaQuery('(max-width: 699px)')
const logOpen = ref(false)
const entriesDay = ref(today())
const timerForm = reactive({ area_id: null, note: '', tags: [] })

const elapsed = computed(() => {
  if (!store.timer) return 0
  return Math.max(0, Math.floor((now.value - new Date(store.timer.startedAt).getTime()) / 1000))
})
const elapsedLabel = computed(() => {
  const s = elapsed.value
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  return `${h ? h + ':' : ''}${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
})

const byDay = computed(() => {
  const map = Object.fromEntries(weekDays(store.weekStart).map((d) => [d, []]))
  for (const log of store.logs) (map[log.date] ||= []).push(log)
  return map
})

const ready = useReady(() => store.load())
onMounted(() => {
  ticker = setInterval(() => (now.value = Date.now()), 1000)
})
onBeforeUnmount(() => clearInterval(ticker))

async function run(fn) {
  error.value = ''
  try {
    await fn()
  } catch (err) {
    error.value = err.message
  }
}

async function addLog() {
  adding.value = true
  try {
    await run(async () => {
      await store.create({ date: form.date, minutes: Number(form.minutes), area_id: form.area_id || null, tags: form.tags, note: form.note || null })
      form.note = ''
      logOpen.value = false
    })
  } finally {
    adding.value = false
  }
}

// Suggested entries from the agenda and completed tasks. Minutes and area are editable per
// row before logging; Skip remembers the choice so the item is not offered again.
const drafts = ref({}) // ref -> { minutes, area_id }
const deciding = ref({}) // ref -> true while its Log or Skip is in flight
const suggested = computed(() => store.suggestions?.items || [])
const suggestedByDay = computed(() => {
  const map = new Map()
  for (const i of suggested.value) {
    if (!map.has(i.date)) map.set(i.date, [])
    map.get(i.date).push(i)
  }
  return [...map.entries()]
})
watch(suggested, (items) => {
  for (const i of items) if (!drafts.value[i.ref]) drafts.value[i.ref] = { minutes: i.minutes, area_id: i.area_id }
}, { immediate: true })
const suggestedSummary = computed(() => {
  const s = store.suggestions
  if (!s || !s.items.length) return ''
  const parts = s.per_area.map((a) => `${a.area} ${minutesToHours(a.minutes)}`)
  return `${minutesToHours(s.total_minutes)} to confirm: ${parts.join(', ')}`
})
function pick(i) {
  const d = drafts.value[i.ref] || { minutes: i.minutes, area_id: i.area_id }
  return { ref: i.ref, date: i.date, minutes: Math.max(1, Number(d.minutes) || i.minutes), area_id: d.area_id || null, note: i.title }
}
async function decide(items, action) {
  for (const i of items) deciding.value[i.ref] = true
  try {
    await run(async () => {
      if (action === 'log') {
        const created = await store.acceptSuggestions(items.map(pick))
        toast.success(created.length === 1 ? `Logged ${minutesToHours(created[0].minutes)} for "${items[0].title}"` : `Logged ${created.length} entries`)
      } else {
        await store.dismissSuggestions(items.map((i) => i.ref))
      }
    })
  } finally {
    for (const i of items) delete deciding.value[i.ref]
  }
}
const allBusy = ref('')
async function decideAll(action) {
  allBusy.value = action
  try {
    await decide([...suggested.value], action)
  } finally {
    allBusy.value = ''
  }
}
function suggestionTime(i) {
  return i.start ? `${formatTime(i.start)} to ${formatTime(i.end)}` : 'task done'
}
function dayNum(day) {
  return Number(day.slice(8))
}

function startTimer() {
  store.startTimer({ area_id: timerForm.area_id, note: timerForm.note, tags: timerForm.tags })
}

async function stopTimer() {
  stopping.value = true
  try {
    await run(async () => {
      await store.stopTimer({ area_id: timerForm.area_id || store.timer.area_id || null, note: timerForm.note || store.timer.note || null, tags: timerForm.tags.length ? timerForm.tags : store.timer.tags })
      timerForm.note = ''
    })
  } finally {
    stopping.value = false
  }
}

function pct(row) {
  if (!row.target_minutes) return null
  return Math.min(100, Math.round((row.minutes / row.target_minutes) * 100))
}
</script>

<template>
  <div class="hours">
    <PageHeader v-if="!phone" title="Hours">
      <WeekNav :week-start="store.weekStart" @change="run(() => store.setWeek($event))" />
    </PageHeader>
    <div v-else class="phead">
      <div><h1>Hours</h1><span class="muted small num">{{ store.summary ? minutesToHours(store.summary.total_minutes) : '0m' }} this week</span></div>
      <UiButton variant="primary" size="sm" @click="logOpen = true">Log time</UiButton>
    </div>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>
    <UiLoadGate :ready="ready" label="Loading hours">

    <section class="card timer" :class="{ running: store.timerRunning }">
      <div class="timer-row">
        <div class="clock-wrap">
          <span class="lamp" aria-hidden="true"></span>
          <span class="clock num" aria-live="off">{{ store.timerRunning ? elapsedLabel : '00:00' }}</span>
        </div>
        <AreaSelect v-model="timerForm.area_id" aria-label="Area" />
        <input v-model="timerForm.note" type="text" placeholder="What are you working on?" aria-label="Note" class="grow" />
        <TagsInput v-model="timerForm.tags" placeholder="tags" class="tags" />
        <UiButton v-if="!store.timerRunning" variant="primary" @click="startTimer">Start</UiButton>
        <template v-else>
          <UiButton variant="primary" :loading="stopping" @click="stopTimer">Stop and log</UiButton>
          <UiButton variant="ghost" :disabled="stopping" @click="store.cancelTimer()">Discard</UiButton>
        </template>
      </div>
      <p v-if="store.timerRunning" class="muted small started">Started {{ new Date(store.timer.startedAt).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) }}. The timer survives a page reload.</p>
    </section>

    <section v-if="suggested.length" class="card suggest">
      <div class="card-head">
        <h2><PhCalendarCheck class="hicon" aria-hidden="true" />From your agenda</h2>
        <span class="meta">
          <UiButton size="sm" variant="ghost" :loading="allBusy === 'skip'" :disabled="Boolean(allBusy)" @click="decideAll('skip')">Skip all</UiButton>
          <UiButton size="sm" variant="primary" :loading="allBusy === 'log'" :disabled="Boolean(allBusy)" @click="decideAll('log')">Log all</UiButton>
        </span>
      </div>
      <p class="muted small lead">{{ suggestedSummary }}. Events from the last 7 days and tasks done without an estimate; nothing is logged until you confirm.</p>
      <div v-for="[day, items] in suggestedByDay" :key="day" class="sday">
        <div class="day-head"><span class="dname">{{ formatDay(day) }}</span></div>
        <ul>
          <li v-for="i in items" :key="i.ref" class="srow" :class="{ busy: deciding[i.ref] }">
            <span class="stitle">
              <span class="truncate">{{ i.title }}</span>
              <span class="muted xs num">{{ suggestionTime(i) }}<template v-if="i.location">, {{ i.location }}</template></span>
            </span>
            <input v-model.number="drafts[i.ref].minutes" type="number" min="5" max="1440" step="5" class="smin num" :aria-label="'Minutes for ' + i.title" :disabled="deciding[i.ref]" />
            <AreaSelect v-model="drafts[i.ref].area_id" class="sarea" :aria-label="'Area for ' + i.title" />
            <span class="sactions">
              <UiButton size="sm" variant="primary" :loading="deciding[i.ref]" :disabled="Boolean(allBusy)" :aria-label="'Log ' + i.title" @click="decide([i], 'log')"><PhCheck weight="bold" /><span class="lbl">Log</span></UiButton>
              <button type="button" class="icon-btn" :aria-label="'Skip ' + i.title" title="Skip" :disabled="deciding[i.ref] || Boolean(allBusy)" @click="decide([i], 'skip')"><PhX /></button>
            </span>
          </li>
        </ul>
      </div>
    </section>

    <section v-if="store.summary && phone" class="card">
      <div class="card-head"><h2>By life area</h2><span class="meta"><WeekNav :week-start="store.weekStart" compact @change="run(() => store.setWeek($event))" /></span></div>
      <div v-for="row in store.summary.areas.filter((r) => r.area_id || r.minutes)" :key="row.area" class="arow">
        <span class="aname"><span class="dot" :style="{ background: row.color }" aria-hidden="true"></span>{{ row.area }}</span>
        <div class="bar"><div class="fill" :class="{ full: pct(row) >= 100 }" :style="{ width: (row.target_minutes ? pct(row) : row.minutes ? 100 : 0) + '%' }"></div></div>
        <span class="num small">{{ minutesToHours(row.minutes) }}<span v-if="row.target_minutes" class="muted"> / {{ minutesToHours(row.target_minutes) }}</span></span>
      </div>
    </section>
    <section v-if="phone" class="card">
      <div class="card-head"><h2>Entries</h2><span class="meta">{{ formatDay(entriesDay) }}</span></div>
      <div class="strip">
        <button v-for="day in Object.keys(byDay)" :key="day" type="button" class="dbtn" :class="{ active: day === entriesDay, today: day === today() }" @click="entriesDay = day"><span class="wd">{{ formatDay(day).slice(0, 3) }}</span><span class="dn num">{{ dayNum(day) }}</span></button>
      </div>
      <ul v-if="byDay[entriesDay]?.length">
        <li v-for="log in byDay[entriesDay]" :key="log.id" class="list-row">
          <span class="mins num">{{ minutesToHours(log.minutes) }}</span>
          <span class="note truncate">{{ log.note || 'No note' }}</span>
          <AreaDot :area-id="log.area_id" />
          <button type="button" class="icon-btn" aria-label="Remove log" @click="run(() => store.remove(log.id))"><PhX /></button>
        </li>
      </ul>
      <p v-else class="muted small nothing">Nothing logged.</p>
    </section>

    <section v-if="store.summary && !phone" class="card">
      <div class="card-head"><h2>Week totals</h2><span class="meta num">{{ minutesToHours(store.summary.total_minutes) }} total</span></div>
      <table class="ui totals">
        <tbody>
          <tr v-for="row in store.summary.areas" :key="row.area">
            <td class="area"><span class="dot" :style="{ background: row.color }" aria-hidden="true"></span>{{ row.area }}</td>
            <td class="num">{{ minutesToHours(row.minutes) }}</td>
            <td class="bar-cell">
              <div v-if="row.target_minutes" class="bar"><div class="fill" :class="{ full: pct(row) >= 100 }" :style="{ width: pct(row) + '%' }"></div></div>
            </td>
            <td class="muted small num">{{ row.target_minutes ? `of ${minutesToHours(row.target_minutes)} (${pct(row)}%)` : '' }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section v-if="!phone" class="card">
      <div class="card-head"><h2>Log time</h2></div>
      <form class="log-form" @submit.prevent="addLog">
        <UiField label="Date"><input v-model="form.date" type="date" required /></UiField>
        <UiField label="Minutes"><input v-model.number="form.minutes" type="number" min="5" max="1440" step="5" required class="minutes" /></UiField>
        <UiField label="Area"><AreaSelect v-model="form.area_id" /></UiField>
        <UiField label="Tags"><TagsInput v-model="form.tags" placeholder="tags" /></UiField>
        <UiField label="Note" class="grow"><input v-model="form.note" type="text" /></UiField>
        <UiButton type="submit" variant="primary" :loading="adding">Add</UiButton>
      </form>
    </section>

    <section v-if="!phone" class="card">
      <div class="card-head"><h2>Logs this week</h2></div>
      <div v-for="(logs, day) in byDay" :key="day" class="day">
        <div class="day-head"><span class="dname">{{ formatDay(day) }}</span> <span class="muted small num">{{ minutesToHours(logs.reduce((s, l) => s + l.minutes, 0)) }}</span></div>
        <ul v-if="logs.length">
          <li v-for="log in logs" :key="log.id" class="list-row">
            <span class="mins num">{{ minutesToHours(log.minutes) }}</span>
            <AreaDot :area-id="log.area_id" label />
            <span class="note truncate">{{ log.note }}</span>
            <span v-for="tag in log.tags" :key="tag" class="tag">{{ tag }}</span>
            <button type="button" class="icon-btn" aria-label="Remove log" @click="run(() => store.remove(log.id))"><PhX /></button>
          </li>
        </ul>
        <p v-else class="muted small nothing">Nothing logged.</p>
      </div>
    </section>
    </UiLoadGate>

    <UiModal :open="logOpen" title="Log time" size="sm" @close="logOpen = false">
      <form class="log-form stacked" @submit.prevent="addLog">
        <div class="pair">
          <UiField label="Date"><input v-model="form.date" type="date" required /></UiField>
          <UiField label="Minutes"><input v-model.number="form.minutes" type="number" min="5" max="1440" step="5" required /></UiField>
        </div>
        <UiField label="Area"><AreaSelect v-model="form.area_id" /></UiField>
        <UiField label="Note"><input v-model="form.note" type="text" /></UiField>
        <UiField label="Tags"><TagsInput v-model="form.tags" placeholder="tags" /></UiField>
        <div class="actions"><UiButton type="submit" variant="primary" :loading="adding">Add</UiButton><UiButton variant="ghost" :disabled="adding" @click="logOpen = false">Cancel</UiButton></div>
      </form>
    </UiModal>
  </div>
</template>

<style scoped>
.phead { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-2); margin-bottom: var(--sp-4); }
.phead h1 { font-size: var(--fs-2xl); }
.arow { display: grid; grid-template-columns: 84px minmax(0, 1fr) auto; gap: 12px; align-items: center; font-size: var(--fs-md); padding: 6px 0; }
.aname { display: flex; align-items: center; gap: 8px; color: var(--ink-2); }
.strip { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 4px; margin-bottom: var(--sp-3); }
.dbtn { height: 44px; border: 0; border-radius: var(--r-md); background: var(--surface); color: var(--ink-2); box-shadow: 0 0 0 1px var(--line) inset; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px; }
.dbtn.today { background: var(--brand-soft); color: var(--brand); }
.dbtn.active { background: var(--ink); color: var(--on-ink); box-shadow: none; }
.dbtn .wd { font-size: 10px; letter-spacing: 0.02em; font-weight: 500; }
.dbtn .dn { font-size: var(--fs-base); font-weight: 600; }
.log-form.stacked { flex-direction: column; align-items: stretch; }
.log-form.stacked .pair { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-2); }
.log-form.stacked .actions { display: flex; gap: var(--sp-2); }
@media (max-width: 699px) {
  .timer-row { gap: var(--sp-2); }
  .timer-row .grow { flex-basis: 100%; }
  .tags { width: 100%; }
}
.suggest .card-head h2 { display: flex; align-items: center; gap: 8px; }
.hicon { width: 18px; height: 18px; color: var(--brand); }
.suggest .meta { display: inline-flex; gap: var(--sp-2); }
.lead { margin: -4px 0 var(--sp-3); }
.sday { padding: var(--sp-2) 0; border-top: 1px solid var(--line); }
.sday:first-of-type { border-top: 0; padding-top: 0; }
.srow { display: grid; grid-template-columns: minmax(0, 1fr) 76px 130px auto; gap: var(--sp-2); align-items: center; padding: 6px 0; transition: opacity var(--dur-hover) ease; }
.srow.busy { opacity: 0.6; }
.stitle { display: flex; flex-direction: column; min-width: 0; }
.smin { width: 76px; padding: 0 8px; }
.sactions { display: inline-flex; align-items: center; gap: 4px; }
.sactions .lbl { margin-left: 2px; }
@media (max-width: 699px) {
  .srow { grid-template-columns: minmax(0, 1fr) 68px auto; }
  .sarea { grid-column: 1 / 3; }
  .sactions .lbl { display: none; }
}
.timer { transition: border-color var(--dur-ui) ease; }
.timer.running { border-color: var(--brand); }
.timer-row { display: flex; flex-wrap: wrap; gap: var(--sp-2); align-items: center; }
.clock-wrap { display: inline-flex; align-items: center; gap: 10px; min-width: 130px; }
.lamp { width: 8px; height: 8px; border-radius: 50%; background: var(--line-2); transition: background-color var(--dur-ui) ease, box-shadow var(--dur-ui) ease; }
.running .lamp { background: var(--brand); box-shadow: 0 0 0 4px var(--brand-soft); }
.clock { font-size: var(--fs-3xl); font-weight: 500; letter-spacing: -0.02em; line-height: 1; }
.grow { flex: 1 1 180px; min-width: 140px; }
.tags { width: 150px; }
.started { margin-top: var(--sp-3); }
.totals td.area { display: flex; align-items: center; gap: 8px; white-space: nowrap; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.bar-cell { width: 42%; }
.log-form { display: flex; flex-wrap: wrap; gap: var(--sp-3); align-items: end; }
.minutes { width: 88px; }
.day { padding: var(--sp-2) 0; border-top: 1px solid var(--line); }
.day:first-of-type { border-top: 0; padding-top: 0; }
.day-head { display: flex; gap: var(--sp-2); align-items: baseline; }
.dname { font-weight: 500; font-size: var(--fs-md); }
.mins { min-width: 56px; color: var(--ink-2); }
.note { flex: 1; min-width: 0; color: var(--ink-2); }
.nothing { padding: 2px 0 0; }
</style>
