<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { PhCalendarCheck, PhCheck, PhPlus, PhSkipForward, PhTrash, PhX } from '@phosphor-icons/vue'
import PullToRefresh from '../components/ios/PullToRefresh.vue'
import SwipeRow from '../components/ios/SwipeRow.vue'
import UiConfirm from '../components/ui/UiConfirm.vue'
import { tick } from '../lib/haptics'
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
const route = useRoute()
// Phone: deletes and the timer discard go through an iOS action sheet instead of happening at once.
const confirmDelete = ref(null) // the log to delete
const confirmDiscard = ref(false)
function deleteLog() {
  const log = confirmDelete.value
  confirmDelete.value = null
  if (log) {
    tick()
    run(() => store.remove(log.id))
  }
}
function discardTimer() {
  confirmDiscard.value = false
  store.cancelTimer()
}
const dayTotal = computed(() => (byDay.value[entriesDay.value] || []).reduce((s, l) => s + l.minutes, 0))
const weekdayLetter = (day) => formatDay(day).slice(0, 1)
const isToday = (day) => day === today()
const startedAt = computed(() => (store.timer ? new Date(store.timer.startedAt).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) : ''))

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
  tick()
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
  tick()
  store.startTimer({ area_id: timerForm.area_id, note: timerForm.note, tags: timerForm.tags })
}

async function stopTimer() {
  tick()
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

// Phone bars: progress to the target when there is one, otherwise the share of the busiest area.
function barWidth(row) {
  if (row.target_minutes) return pct(row)
  const most = Math.max(1, ...(store.summary?.areas || []).map((r) => r.minutes))
  return Math.round((row.minutes / most) * 100)
}

function pct(row) {
  if (!row.target_minutes) return null
  return Math.min(100, Math.round((row.minutes / row.target_minutes) * 100))
}
</script>

<template>
  <PullToRefresh :action="() => store.load()">
  <div class="hours">
    <PageHeader v-if="!phone" title="Hours">
      <WeekNav :week-start="store.weekStart" @change="run(() => store.setWeek($event))" />
    </PageHeader>
    <div v-else class="phead">
      <h1>Hours</h1><span class="psub num">{{ store.summary ? minutesToHours(store.summary.total_minutes) : '0m' }} this week</span>
    </div>
    <Teleport v-if="phone && route.name === 'hours'" defer to="#nav-trailing">
      <button type="button" class="icon-btn" aria-label="Log time" @click="logOpen = true"><PhPlus weight="regular" /></button>
    </Teleport>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>
    <UiLoadGate :ready="ready" label="Loading hours">

    <template v-if="phone">
      <!-- The timer as the Clock app's stopwatch: big thin digits, Discard and Start or Stop as
           round buttons, the details as grouped rows under it. -->
      <section class="stopwatch" :class="{ running: store.timerRunning }">
        <span class="sw-clock num" aria-live="off">{{ store.timerRunning ? elapsedLabel : '00:00' }}</span>
        <span class="sw-sub">{{ store.timerRunning ? `Started ${startedAt}` : 'Timer' }}</span>
        <div class="sw-btns">
          <button type="button" class="round grey" :disabled="!store.timerRunning || stopping" @click="confirmDiscard = true">Discard</button>
          <button v-if="!store.timerRunning" type="button" class="round go" @click="startTimer">Start</button>
          <button v-else type="button" class="round stop" :disabled="stopping" @click="stopTimer">{{ stopping ? 'Saving' : 'Stop' }}</button>
        </div>
      </section>
      <div class="plate form">
        <label class="row"><span class="lbl">Area</span><AreaSelect v-model="timerForm.area_id" class="pick" aria-label="Area" /></label>
        <label class="row"><input v-model="timerForm.note" type="text" placeholder="What are you working on?" aria-label="Note" class="bare" /></label>
        <label class="row"><TagsInput v-model="timerForm.tags" placeholder="Tags" class="bare" aria-label="Tags" /></label>
      </div>
      <p class="foot tfoot">Stop logs the time. The timer keeps running when you leave the app.</p>
    </template>
    <section v-else class="card timer" :class="{ running: store.timerRunning }">
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

    <section v-if="suggested.length && phone" class="grp">
      <div class="ghead"><h2>From your agenda</h2><button type="button" class="hlink" :disabled="Boolean(allBusy)" @click="decideAll('log')">Log all</button></div>
      <template v-for="[day, items] in suggestedByDay" :key="day">
        <h3 class="subhead">{{ formatDay(day) }}</h3>
        <ul class="plate">
          <li v-for="i in items" :key="i.ref" :class="{ busy: deciding[i.ref] }">
            <SwipeRow :leading="[{ label: 'Log', icon: PhCheck, color: 'var(--ok)', action: () => decide([i], 'log') }]" :trailing="[{ label: 'Skip', icon: PhSkipForward, color: '#8E8E93', action: () => decide([i], 'skip') }]">
              <div class="row srow-p">
                <button type="button" class="logc" :aria-label="'Log ' + i.title" :disabled="deciding[i.ref] || Boolean(allBusy)" @click="decide([i], 'log')"><PhCheck weight="bold" /></button>
                <span class="txt"><span class="t truncate">{{ i.title }}</span><span class="s truncate num">{{ suggestionTime(i) }}<template v-if="i.location">, {{ i.location }}</template></span></span>
                <AreaSelect v-model="drafts[i.ref].area_id" class="pick sm" :aria-label="'Area for ' + i.title" />
                <input v-model.number="drafts[i.ref].minutes" type="number" min="5" max="1440" step="5" class="pill num" :aria-label="'Minutes for ' + i.title" :disabled="deciding[i.ref]" />
              </div>
            </SwipeRow>
          </li>
        </ul>
      </template>
      <p class="foot">{{ suggestedSummary }}. Tap the circle or swipe right to log, swipe left to skip; nothing is logged until you confirm.</p>
    </section>
    <section v-if="suggested.length && !phone" class="card suggest">
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

    <section v-if="store.summary && phone" class="grp">
      <div class="ghead"><h2>By life area</h2><WeekNav :week-start="store.weekStart" compact class="wnav" @change="run(() => store.setWeek($event))" /></div>
      <ul class="plate">
        <li v-for="row in store.summary.areas.filter((r) => r.area_id || r.minutes)" :key="row.area" class="row arow-p">
          <span class="adot" :style="{ background: row.color }" aria-hidden="true"></span>
          <span class="acol">
            <span class="aline"><span class="lbl">{{ row.area }}</span><span class="aval num">{{ minutesToHours(row.minutes) }}<span v-if="row.target_minutes" class="of"> of {{ minutesToHours(row.target_minutes) }}</span></span></span>
            <span class="thin"><span class="tfill" :class="{ full: pct(row) >= 100 }" :style="{ width: barWidth(row) + '%', background: pct(row) >= 100 ? undefined : row.color }"></span></span>
          </span>
        </li>
        <li class="row total"><span class="lbl">Total</span><span class="num">{{ minutesToHours(store.summary.total_minutes) }}</span></li>
      </ul>
    </section>
    <section v-if="phone" class="grp">
      <div class="ghead"><h2>Entries</h2><span class="hval num">{{ formatDay(entriesDay) }}<template v-if="dayTotal">, {{ minutesToHours(dayTotal) }}</template></span></div>
      <div class="week" role="tablist" aria-label="Day">
        <button v-for="day in Object.keys(byDay)" :key="day" type="button" role="tab" class="wd" :class="{ active: day === entriesDay, today: isToday(day), has: byDay[day].length }" :aria-selected="day === entriesDay" :aria-label="formatDay(day)" @click="entriesDay = day">
          <span class="wl">{{ weekdayLetter(day) }}</span><span class="wn num">{{ dayNum(day) }}</span><span class="wdot" aria-hidden="true"></span>
        </button>
      </div>
      <ul v-if="byDay[entriesDay]?.length" class="plate">
        <li v-for="log in byDay[entriesDay]" :key="log.id">
          <SwipeRow :trailing="[{ label: 'Delete', icon: PhTrash, color: 'var(--danger)', action: () => (confirmDelete = log) }]">
            <div class="row entry">
              <AreaDot :area-id="log.area_id" />
              <span class="txt"><span class="t truncate" :class="{ none: !log.note }">{{ log.note || 'No note' }}</span><span v-if="log.tags?.length" class="s truncate">{{ log.tags.join(', ') }}</span></span>
              <span class="eval num">{{ minutesToHours(log.minutes) }}</span>
            </div>
          </SwipeRow>
        </li>
      </ul>
      <p v-else class="plate row nothing-p">Nothing logged</p>
      <p v-if="byDay[entriesDay]?.length" class="foot">Swipe an entry left to delete it.</p>
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
      <form class="sheet-form" @submit.prevent="addLog">
        <div class="plate">
          <label class="row"><span class="lbl">Date</span><input v-model="form.date" type="date" required class="pill" /></label>
          <label class="row"><span class="lbl">Minutes</span><input v-model.number="form.minutes" type="number" min="5" max="1440" step="5" required class="pill num" /></label>
          <label class="row"><span class="lbl">Area</span><AreaSelect v-model="form.area_id" class="pick" /></label>
        </div>
        <div class="plate">
          <label class="row"><input v-model="form.note" type="text" placeholder="Note" aria-label="Note" class="bare" /></label>
          <label class="row"><TagsInput v-model="form.tags" placeholder="Tags, comma separated" aria-label="Tags" class="bare" /></label>
        </div>
        <UiButton type="submit" variant="primary" block :loading="adding" class="big">Add</UiButton>
      </form>
    </UiModal>
    <UiConfirm :open="Boolean(confirmDelete)" title="Delete this entry?" :message="confirmDelete ? `${minutesToHours(confirmDelete.minutes)}${confirmDelete.note ? ', ' + confirmDelete.note : ''}` : ''" confirm-label="Delete entry" danger @confirm="deleteLog" @cancel="confirmDelete = null" />
    <UiConfirm :open="confirmDiscard" title="Discard the running timer?" message="The time is not logged." confirm-label="Discard timer" danger @confirm="discardTimer" @cancel="confirmDiscard = false" />
  </div>
  </PullToRefresh>
</template>

<style scoped>
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

/* iOS layer (phone layout, under 700px). Inset grouped plates of 44pt rows with separators
   from the text, footnote headers above and footers below, the timer as the stopwatch. */
@media (max-width: 699px) {
  .phead { margin: 4px 0 var(--sp-5); }
  .psub { display: block; margin-top: 2px; font-size: 0.9375rem; color: var(--ink-3); }
  .grp { margin-bottom: var(--sp-8); }
  .ghead { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 22px; margin: 0 16px 6px; }
  .ghead h2, .subhead { font-size: 0.8125rem; font-weight: 400; text-transform: uppercase; color: var(--ink-3); }
  .subhead { margin: var(--sp-3) 16px 6px; }
  .hval { font-size: 0.8125rem; color: var(--ink-3); }
  .hlink { border: 0; background: none; padding: 0; color: var(--brand); font: inherit; font-size: 0.9375rem; }
  .hlink:disabled { color: var(--ink-4); }
  .plate { background: var(--surface); border-radius: var(--r-lg); overflow: hidden; }
  .plate > li, .plate > .row { position: relative; }
  .plate > li + li::before, .plate > .row + .row::before { content: ''; position: absolute; z-index: 2; top: 0; left: var(--sep, 16px); right: 0; height: 0.5px; background: var(--line-2); }
  .row { display: flex; align-items: center; gap: 12px; min-height: 44px; padding: 6px 16px; font-size: 1.0625rem; color: var(--ink); }
  .lbl { flex: 1; min-width: 0; }
  .foot { margin: 6px 16px 0; font-size: 0.8125rem; line-height: 1.4; color: var(--ink-3); }
  .txt { flex: 1; min-width: 0; display: flex; flex-direction: column; }
  .txt .t { font-size: 1.0625rem; }
  .txt .t.none { color: var(--ink-3); }
  .txt .s { font-size: 0.9375rem; color: var(--ink-3); }
  /* Field kinds inside rows: a pop-up value, a grey pill (compact picker), a bare full-row field. */
  .pick { flex: none; width: auto; max-width: 50%; height: 32px; padding: 0 20px 0 0; background: transparent url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 256 256' fill='none' stroke='%238E8E93' stroke-width='22' stroke-linecap='round' stroke-linejoin='round'><polyline points='80 96 128 48 176 96'/><polyline points='80 160 128 208 176 160'/></svg>") right center / 13px no-repeat; color: var(--ink-3); text-align: right; text-align-last: right; }
  .pick.sm { max-width: 92px; font-size: 0.9375rem; }
  .pick:focus-visible { box-shadow: none; color: var(--ink); }
  .row .pill { flex: none; width: auto; min-width: 64px; max-width: 150px; height: 34px; padding: 0 10px; border-radius: 8px; text-align: center; }
  .row .bare { flex: 1; width: 100%; height: 32px; padding: 0; background: transparent; border-radius: 0; }
  .row .bare:focus-visible { box-shadow: none; }

  .stopwatch { display: flex; flex-direction: column; align-items: center; padding: var(--sp-6) 16px var(--sp-5); margin-bottom: var(--sp-3); background: var(--surface); border-radius: var(--r-lg); }
  .sw-clock { font-size: 4.25rem; font-weight: 200; line-height: 1; letter-spacing: -0.01em; color: var(--ink); }
  .sw-sub { margin-top: 8px; font-size: 0.9375rem; color: var(--ink-3); }
  .sw-btns { display: flex; justify-content: space-between; width: 100%; max-width: 320px; margin-top: var(--sp-6); }
  /* Round buttons with a hairline ring inside, like the stopwatch's. */
  .round { --ring: currentColor; width: 80px; height: 80px; border-radius: 50%; border: 0; font: inherit; font-size: 1.0625rem; font-weight: 500; box-shadow: inset 0 0 0 2px var(--surface), inset 0 0 0 3.5px var(--ring); }
  .round:active:not(:disabled) { opacity: 0.6; }
  .round.grey { --ring: var(--surface-3); background: var(--surface-2); color: var(--ink); }
  .round.grey:disabled { color: var(--ink-4); }
  .round.go { background: color-mix(in srgb, var(--ok) 22%, transparent); color: var(--ok); }
  .round.stop { background: color-mix(in srgb, var(--danger) 20%, transparent); color: var(--danger); }
  .form { --sep: 16px; }
  .tfoot { margin-bottom: var(--sp-8); }

  .wnav { margin-right: -6px; }
  .wnav :deep(.label) { font-size: 0.8125rem; color: var(--ink-3); font-weight: 400; }
  .arow-p { --sep: 40px; align-items: flex-start; padding-top: 11px; padding-bottom: 10px; }
  .plate > li.arow-p + li::before { left: 40px; }
  .adot { width: 12px; height: 12px; margin-top: 6px; border-radius: 50%; flex: none; }
  .acol { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 7px; }
  .aline { display: flex; align-items: baseline; gap: 12px; }
  .aval { font-size: 1.0625rem; }
  .of { color: var(--ink-3); }
  .thin { display: block; height: 4px; border-radius: 2px; background: var(--surface-2); overflow: hidden; }
  .tfill { display: block; height: 100%; border-radius: 2px; }
  .tfill.full { background: var(--ok); }
  .total { font-weight: 600; }

  /* The week as Calendar's week row: letters, then the date in a circle. */
  .week { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); margin: 0 0 var(--sp-2); }
  .wd { display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 2px 0; border: 0; background: none; color: var(--ink); font: inherit; }
  .wl { font-size: 0.6875rem; font-weight: 600; color: var(--ink-3); }
  .wn { display: grid; place-items: center; width: 36px; height: 36px; border-radius: 50%; font-size: 1.25rem; transition: background-color 150ms ease, color 150ms ease; }
  .wd.today .wn { color: var(--brand); font-weight: 600; }
  .wd.active .wn { background: var(--ink); color: var(--bg); font-weight: 600; }
  .wd.active.today .wn { background: var(--brand); color: #fff; }
  .wdot { width: 5px; height: 5px; border-radius: 50%; background: transparent; }
  .wd.has .wdot { background: var(--ink-4); }
  .entry { --sep: 40px; }
  .plate > li:has(.entry) + li::before { left: 40px; }
  .entry :deep(.area-dot), .entry > :first-child { flex: none; }
  .eval { flex: none; font-size: 1.0625rem; color: var(--ink-3); }
  .nothing-p { color: var(--ink-3); margin: 0; }

  .srow-p { gap: 10px; }
  .logc { display: grid; place-items: center; flex: none; width: 24px; height: 24px; padding: 0; border-radius: 50%; border: 1.5px solid var(--ink-4); background: none; color: transparent; }
  .logc:active { background: var(--ok); border-color: var(--ok); color: #fff; }
  .logc svg { width: 13px; height: 13px; }
  .plate > li:has(.srow-p) + li::before { left: 50px; }
  li.busy { opacity: 0.5; }

  .sheet-form { display: flex; flex-direction: column; gap: var(--sp-5); }
  .sheet-form .plate { background: var(--surface-2); }
  .sheet-form .plate .pill { background: var(--surface-3); }
  .sheet-form .big { height: 50px; min-height: 50px; border-radius: 12px; font-size: 1.0625rem; }
}
</style>
