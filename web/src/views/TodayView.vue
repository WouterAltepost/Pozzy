<script setup>
// Home: today's habits. A ring for the day, the week to step back and fill in, the habits due
// on the chosen day, the week targets, and the habits that are not due (collapsed). One tap
// checks a habit off with Undo in the toast; the body of a row opens the check-in sheet.
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { PhCaretDown, PhPlus, PhSparkle } from '@phosphor-icons/vue'
import CheckInSheet from '../components/habits/CheckInSheet.vue'
import HabitEditor from '../components/habits/HabitEditor.vue'
import HabitRow from '../components/habits/HabitRow.vue'
import ProgressRing from '../components/habits/ProgressRing.vue'
import WeekStrip from '../components/habits/WeekStrip.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiEmpty from '../components/ui/UiEmpty.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import { useReady } from '../composables/useReady'
import { useToast } from '../composables/useToast'
import { formatDay, mondayOf, today as todayFn } from '../lib/dates'
import { cellOf, fmt, isBool, isWeekly } from '../lib/habits'
import { useTrackersStore } from '../stores/trackers'

const store = useTrackersStore()
const toast = useToast()
const route = useRoute()
const router = useRouter()
const error = ref('')
const today = ref(todayFn())

async function refresh(d) {
  today.value = todayFn()
  store.includeInactive = false
  store.day = d && d <= today.value ? d : today.value
  store.weekStart = mondayOf(store.day)
  await store.load()
}
const ready = useReady(() => refresh(route.query.day ? String(route.query.day) : null))

// An installed PWA stays open overnight: coming back on a new day moves to that day.
function onVisible() {
  if (document.visibilityState !== 'visible') return
  if (todayFn() !== today.value) refresh(null)
  else store.load()
}
onMounted(() => document.addEventListener('visibilitychange', onVisible))
onBeforeUnmount(() => document.removeEventListener('visibilitychange', onVisible))

const day = computed(() => store.day)
const isToday = computed(() => day.value === today.value)
const active = computed(() => store.trackers.filter((t) => t.active))
const dayHabits = computed(() => active.value.filter((t) => !isWeekly(t)))
const due = computed(() => dayHabits.value.filter((t) => {
  const c = cellOf(t, day.value)
  return c && (c.due || c.met || c.status === 'skipped')
}))
const notDue = computed(() => dayHabits.value.filter((t) => !due.value.includes(t)))
const weekly = computed(() => active.value.filter(isWeekly))
const counted = computed(() => due.value.filter((t) => cellOf(t, day.value)?.status !== 'skipped'))
const doneCount = computed(() => counted.value.filter((t) => cellOf(t, day.value)?.met).length)
const allDone = computed(() => counted.value.length > 0 && doneCount.value === counted.value.length)
const showOff = ref(false)

const now = new Date()
const weekNo = (() => {
  const jan4 = new Date(now.getFullYear(), 0, 4)
  return Math.ceil(((now - jan4) / 86400000 + ((jan4.getDay() + 6) % 7) + 1) / 7)
})()
const eyebrow = computed(() => (isToday.value ? `${now.toLocaleDateString('en-GB', { weekday: 'long' })} · Week ${weekNo}` : 'Catching up'))
const heading = computed(() => (isToday.value ? 'Today' : formatDay(day.value)))
const summary = computed(() => {
  if (!counted.value.length) return dayHabits.value.length ? 'Nothing due. A free day.' : ''
  if (allDone.value) return isToday.value ? 'All done for today.' : 'Everything done that day.'
  const left = counted.value.length - doneCount.value
  return `${left} to go`
})

async function selectDay(d) {
  error.value = ''
  try {
    await store.setDay(d)
    router.replace({ query: d === today.value ? {} : { day: d } })
  } catch (err) {
    error.value = err.message
  }
}

function describe(t, value, status) {
  const when = isToday.value ? 'today' : formatDay(day.value)
  if (status === 'skipped') return `${t.name} skipped ${when}`
  if (isBool(t)) return `${t.name} ${value ? 'done' : 'not done'} ${when}`
  if (value === null || value === undefined) return `${t.name} cleared ${when}`
  return `${t.name}: ${fmt(value)}${t.unit ? ' ' + t.unit : ''} ${when}`
}

async function write(t, fn) {
  error.value = ''
  try {
    const d = day.value
    const { previous, value, status } = await fn()
    toast.undo(describe(t, value, status), async () => {
      try {
        await store.revert(t.id, d, previous)
      } catch (err) {
        toast.error(err.message)
      }
    })
  } catch (err) {
    error.value = err.message
  }
}

// One tap: a check toggles, a count adds one, a value habit opens the sheet for its number.
function act(t) {
  if (isBool(t) || t.type === 'weekly_count') write(t, () => store.tick(t.id, day.value))
  else openSheet(t)
}

const sheet = ref(null)
const sheetBusy = ref(false)
function openSheet(t) {
  sheet.value = t.id
}
const sheetTracker = computed(() => (sheet.value ? store.byId(sheet.value) : null))
async function saveSheet(body) {
  const t = sheetTracker.value
  if (!t) return
  sheetBusy.value = true
  try {
    await write(t, () => store.setEntry(t.id, day.value, body.value, body.note, body.status))
    sheet.value = null
  } finally {
    sheetBusy.value = false
  }
}
async function clearSheet() {
  const t = sheetTracker.value
  if (!t) return
  sheetBusy.value = true
  try {
    await write(t, () => store.clearEntry(t.id, day.value))
    sheet.value = null
  } finally {
    sheetBusy.value = false
  }
}

const editing = ref(false)
const saving = ref(false)
const editError = ref('')
async function createHabit(body) {
  saving.value = true
  editError.value = ''
  try {
    await store.create(body)
    editing.value = false
    toast.success(`${body.name} added`)
  } catch (err) {
    editError.value = err.message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="today">
    <header class="hero">
      <div class="titles">
        <span class="eyebrow">{{ eyebrow }}</span>
        <h1>{{ heading }}</h1>
        <p class="summary" :class="{ ok: allDone }">
          <PhSparkle v-if="allDone" weight="fill" aria-hidden="true" />{{ summary }}
          <button v-if="!isToday" type="button" class="link-btn back" @click="selectDay(today)">Back to today</button>
        </p>
      </div>
      <ProgressRing v-if="counted.length" :value="doneCount" :total="counted.length" :size="76" :stroke="7" />
    </header>

    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>

    <UiLoadGate :ready="ready" label="Loading habits">
      <WeekStrip v-if="store.week && active.length" class="strip" :week-start="store.week.week_start" :trackers="active" :day="day" :today="today" @select="selectDay" />

      <section v-if="!active.length" class="card">
        <UiEmpty title="No habits yet" hint="Add the first thing you want to do every day, a few times a week, or on set days.">
          <template #icon><PhSparkle /></template>
          <template #action><UiButton variant="primary" @click="editing = true">New habit</UiButton></template>
        </UiEmpty>
      </section>

      <template v-else>
        <section v-if="due.length" class="card list">
          <HabitRow v-for="t in due" :key="t.id" :tracker="t" :day="day" :today="today" @act="act(t)" @open="openSheet(t)" />
        </section>

        <section v-if="weekly.length" class="card list">
          <div class="card-head"><h2>This week</h2><span class="meta">{{ weekly.filter((t) => t.week_met).length }} of {{ weekly.length }} met</span></div>
          <div v-for="t in weekly" :key="t.id" class="weekly">
            <HabitRow :tracker="t" :day="day" :today="today" @act="act(t)" @open="openSheet(t)" />
            <div v-if="t.target_value" class="bar"><div class="fill" :class="{ full: t.week_met }" :style="{ width: Math.min(100, (t.week_total / t.target_value) * 100) + '%' }"></div></div>
          </div>
        </section>

        <section v-if="notDue.length" class="off">
          <button type="button" class="off-toggle" :aria-expanded="showOff" @click="showOff = !showOff">
            <span class="eyebrow">Not due {{ isToday ? 'today' : 'that day' }} · {{ notDue.length }}</span>
            <PhCaretDown class="caret" :class="{ open: showOff }" aria-hidden="true" />
          </button>
          <div v-if="showOff" class="card list">
            <HabitRow v-for="t in notDue" :key="t.id" :tracker="t" :day="day" :today="today" @act="act(t)" @open="openSheet(t)" />
          </div>
        </section>

        <div class="foot">
          <UiButton variant="ghost" @click="editing = true"><PhPlus />New habit</UiButton>
          <RouterLink :to="{ name: 'trackers' }" class="link-btn">All habits and stats</RouterLink>
        </div>
      </template>
    </UiLoadGate>

    <CheckInSheet :open="Boolean(sheetTracker)" :tracker="sheetTracker" :day="day" :busy="sheetBusy" @save="saveSheet" @clear="clearSheet" @close="sheet = null" />
    <HabitEditor :open="editing" :busy="saving" :error="editError" @save="createHabit" @close="editing = false" />
  </div>
</template>

<style scoped>
.today { max-width: 680px; margin: 0 auto; }
.hero { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-4); margin-bottom: var(--sp-6); }
.titles { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.summary { display: flex; align-items: center; flex-wrap: wrap; gap: 6px 10px; margin: 0; color: var(--ink-3); font-size: var(--fs-base); }
.summary.ok { color: var(--ok); font-weight: 500; }
.summary :deep(svg) { width: 15px; height: 15px; }
.back { font-size: var(--fs-md); color: var(--brand); }
.strip { margin-bottom: var(--sp-5); }
.list { padding-top: var(--sp-2); padding-bottom: var(--sp-2); }
.list .card-head { padding-top: var(--sp-3); margin-bottom: var(--sp-1); }
.weekly { border-top: 1px solid var(--line); padding-bottom: 12px; }
.weekly:first-of-type { border-top: 0; }
.weekly :deep(.habit) { border-top: 0; }
.weekly .bar { margin-left: 54px; }
.off { margin-bottom: var(--sp-5); }
.off-toggle { display: flex; align-items: center; gap: 6px; width: 100%; padding: 6px 4px 10px; border: 0; background: none; color: var(--ink-3); }
.caret { width: 12px; height: 12px; transition: transform var(--dur-hover) var(--ease-out); }
.caret.open { transform: rotate(180deg); }
.foot { display: flex; align-items: center; justify-content: space-between; gap: var(--sp-3); padding: 0 4px; }
.today :deep(.card) { animation: rise 520ms var(--ease-spring) both; }
.today :deep(.card:nth-of-type(2)) { animation-delay: 50ms; }
@keyframes rise { from { opacity: 0; transform: translateY(10px); } }
@media (prefers-reduced-motion: reduce) { .today :deep(.card) { animation: none; } }
@media (max-width: 720px) {
  .hero { margin-bottom: var(--sp-4); }
  .card.list { padding-left: var(--sp-4); padding-right: var(--sp-4); }
}
</style>
