<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import AreaDot from '../components/shared/AreaDot.vue'
import AreaSelect from '../components/shared/AreaSelect.vue'
import TagsInput from '../components/shared/TagsInput.vue'
import WeekNav from '../components/shared/WeekNav.vue'
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
    <div class="head">
      <h1>Hours</h1>
      <WeekNav :week-start="store.weekStart" @change="run(() => store.setWeek($event))" />
    </div>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>

    <section class="card timer" :class="{ running: store.timerRunning }">
      <div class="timer-row">
        <strong class="clock">{{ store.timerRunning ? elapsedLabel : '00:00' }}</strong>
        <AreaSelect v-model="timerForm.area_id" />
        <input v-model="timerForm.note" type="text" placeholder="What are you working on?" />
        <TagsInput v-model="timerForm.tags" placeholder="tags" />
        <button v-if="!store.timerRunning" type="button" @click="startTimer">Start</button>
        <template v-else>
          <button type="button" @click="stopTimer">Stop and log</button>
          <button type="button" class="link" @click="store.cancelTimer()">discard</button>
        </template>
      </div>
      <p v-if="store.timerRunning" class="muted small">Started {{ new Date(store.timer.startedAt).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) }}. The timer survives a page reload.</p>
    </section>

    <section class="card" v-if="store.summary">
      <h2>Week totals</h2>
      <table class="totals">
        <tbody>
          <tr v-for="row in store.summary.areas" :key="row.area">
            <td class="area"><span class="dot" :style="{ background: row.color }"></span>{{ row.area }}</td>
            <td class="num">{{ minutesToHours(row.minutes) }}</td>
            <td class="bar-cell">
              <div v-if="row.target_minutes" class="bar"><div class="fill" :class="{ full: pct(row) >= 100 }" :style="{ width: pct(row) + '%' }"></div></div>
            </td>
            <td class="muted small">{{ row.target_minutes ? `of ${minutesToHours(row.target_minutes)} (${pct(row)}%)` : '' }}</td>
          </tr>
          <tr class="total">
            <td>Total</td>
            <td class="num">{{ minutesToHours(store.summary.total_minutes) }}</td>
            <td colspan="2"></td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="card">
      <h2>Log time</h2>
      <form class="log-form" @submit.prevent="addLog">
        <input v-model="form.date" type="date" required />
        <input v-model.number="form.minutes" type="number" min="1" max="1440" step="5" required />
        <span class="muted small">min</span>
        <AreaSelect v-model="form.area_id" />
        <TagsInput v-model="form.tags" />
        <input v-model="form.note" type="text" placeholder="note" class="grow" />
        <button type="submit">Add</button>
      </form>
    </section>

    <section class="card">
      <h2>Logs this week</h2>
      <div v-for="(logs, day) in byDay" :key="day" class="day">
        <div class="day-head"><strong>{{ formatDay(day) }}</strong> <span class="muted small">{{ minutesToHours(logs.reduce((s, l) => s + l.minutes, 0)) }}</span></div>
        <ul>
          <li v-for="log in logs" :key="log.id">
            <span class="mins">{{ minutesToHours(log.minutes) }}</span>
            <AreaDot :area-id="log.area_id" label />
            <span class="note">{{ log.note }}</span>
            <span v-for="tag in log.tags" :key="tag" class="tag">{{ tag }}</span>
            <button type="button" class="x" @click="run(() => store.remove(log.id))">&times;</button>
          </li>
        </ul>
      </div>
    </section>
  </div>
</template>

<style scoped>
h1 { font-size: 1.3rem; margin: 0; }
h2 { font-size: 1rem; margin: 0 0 0.5rem; }
.head { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center; margin-bottom: 1rem; }
.timer.running { border-color: #059669; }
.timer-row { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
.timer-row input, .timer-row select { font: inherit; padding: 0.35rem; border: 1px solid #d1d5db; border-radius: 4px; }
.clock { font-variant-numeric: tabular-nums; font-size: 1.4rem; min-width: 90px; }
.link { border: none; background: none; color: #6b7280; }
.small { font-size: 0.78rem; }
.totals { border-collapse: collapse; width: 100%; font-size: 0.9rem; }
.totals td { padding: 0.25rem 0.4rem; }
.area { display: flex; align-items: center; gap: 0.4rem; white-space: nowrap; }
.dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.bar-cell { width: 40%; }
.bar { height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden; }
.fill { height: 100%; background: #2563eb; }
.fill.full { background: #059669; }
.total td { border-top: 1px solid #e5e7eb; font-weight: 600; }
.log-form { display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center; }
.log-form input, .log-form select { font: inherit; padding: 0.35rem; border: 1px solid #d1d5db; border-radius: 4px; }
.log-form input[type='number'] { width: 80px; }
.grow { flex: 1; min-width: 140px; }
.day { margin-bottom: 0.5rem; }
.day-head { display: flex; gap: 0.5rem; align-items: baseline; }
ul { list-style: none; padding: 0; margin: 0.15rem 0 0; }
li { display: flex; gap: 0.5rem; align-items: center; font-size: 0.85rem; padding: 0.15rem 0; }
.mins { font-variant-numeric: tabular-nums; min-width: 56px; }
.note { flex: 1; color: #374151; }
.tag { background: #f3f4f6; padding: 0 0.35rem; border-radius: 3px; font-size: 0.75rem; }
.x { border: none; background: none; color: #9ca3af; font-size: 1rem; }
</style>
