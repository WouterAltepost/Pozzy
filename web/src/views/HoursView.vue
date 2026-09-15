<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { PhX } from '@phosphor-icons/vue'
import AreaDot from '../components/shared/AreaDot.vue'
import AreaSelect from '../components/shared/AreaSelect.vue'
import TagsInput from '../components/shared/TagsInput.vue'
import WeekNav from '../components/shared/WeekNav.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiField from '../components/ui/UiField.vue'
import { formatDay, minutesToHours, today, weekDays } from '../lib/dates'
import { useHoursStore } from '../stores/hours'

const store = useHoursStore()
const error = ref('')
const now = ref(Date.now())
let ticker = null

const form = reactive({ date: today(), minutes: 30, area_id: null, tags: [], note: '' })
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

onMounted(() => {
  store.load()
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

function addLog() {
  run(async () => {
    await store.create({ date: form.date, minutes: Number(form.minutes), area_id: form.area_id || null, tags: form.tags, note: form.note || null })
    form.note = ''
  })
}

function startTimer() {
  store.startTimer({ area_id: timerForm.area_id, note: timerForm.note, tags: timerForm.tags })
}

function stopTimer() {
  run(async () => {
    await store.stopTimer({ area_id: timerForm.area_id || store.timer.area_id || null, note: timerForm.note || store.timer.note || null, tags: timerForm.tags.length ? timerForm.tags : store.timer.tags })
    timerForm.note = ''
  })
}

function pct(row) {
  if (!row.target_minutes) return null
  return Math.min(100, Math.round((row.minutes / row.target_minutes) * 100))
}
</script>

<template>
  <div class="hours">
    <PageHeader title="Hours">
      <WeekNav :week-start="store.weekStart" @change="run(() => store.setWeek($event))" />
    </PageHeader>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>

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
          <UiButton variant="primary" @click="stopTimer">Stop and log</UiButton>
          <UiButton variant="ghost" @click="store.cancelTimer()">Discard</UiButton>
        </template>
      </div>
      <p v-if="store.timerRunning" class="muted small started">Started {{ new Date(store.timer.startedAt).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) }}. The timer survives a page reload.</p>
    </section>

    <section v-if="store.summary" class="card">
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

    <section class="card">
      <div class="card-head"><h2>Log time</h2></div>
      <form class="log-form" @submit.prevent="addLog">
        <UiField label="Date"><input v-model="form.date" type="date" required /></UiField>
        <UiField label="Minutes"><input v-model.number="form.minutes" type="number" min="1" max="1440" step="5" required class="minutes" /></UiField>
        <UiField label="Area"><AreaSelect v-model="form.area_id" /></UiField>
        <UiField label="Tags"><TagsInput v-model="form.tags" placeholder="tags" /></UiField>
        <UiField label="Note" class="grow"><input v-model="form.note" type="text" /></UiField>
        <UiButton type="submit" variant="primary">Add</UiButton>
      </form>
    </section>

    <section class="card">
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
  </div>
</template>

<style scoped>
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
