<script setup>
import { onMounted, ref } from 'vue'
import LineChart from '../components/trackers/LineChart.vue'
import TrackerForm from '../components/trackers/TrackerForm.vue'
import WeekNav from '../components/shared/WeekNav.vue'
import { shortDay, today } from '../lib/dates'
import { useTrackersStore } from '../stores/trackers'

const store = useTrackersStore()
const error = ref('')
const editing = ref(null) // null | 'new' | tracker
const charts = ref({})

onMounted(() => store.load())

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
  await run(async () => {
    if (editing.value === 'new') await store.create(body)
    else await store.update(editing.value.id, body)
    editing.value = null
  })
}

async function toggleChart(t) {
  if (charts.value[t.id]) {
    delete charts.value[t.id]
    return
  }
  await run(async () => {
    charts.value[t.id] = await store.history(t.id, 8)
  })
}

function promptValue(t, day) {
  const current = day.value ?? ''
  const answer = window.prompt(`${t.name} on ${day.date}${t.unit ? ' (' + t.unit + ')' : ''}:`, current)
  if (answer === null) return
  if (answer.trim() === '') return run(() => store.clearEntry(t.id, day.date))
  const value = Number(answer)
  if (Number.isNaN(value)) return
  run(async () => {
    await store.setEntry(t.id, day.date, value)
    if (charts.value[t.id]) charts.value[t.id] = await store.history(t.id, 8)
  })
}

function cellLabel(t, day) {
  if (day.value === null || day.value === undefined) return ''
  if (t.type === 'daily_bool') return day.value ? '✓' : ''
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
    <div class="head">
      <h1>Tracking</h1>
      <WeekNav :week-start="store.weekStart" @change="run(() => store.setWeek($event))" />
      <label class="check"><input v-model="store.includeInactive" type="checkbox" @change="store.load()" /> show archived</label>
      <button type="button" @click="editing = 'new'">New tracker</button>
    </div>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>
    <div v-if="editing" class="card">
      <TrackerForm :tracker="editing === 'new' ? null : editing" @save="save" @cancel="editing = null" />
    </div>

    <p v-if="store.loading && !store.week" class="muted">Loading...</p>
    <p v-else-if="!store.trackers.length" class="muted">No trackers yet. Add creatine, vitamins, sauna, weight, sleep...</p>

    <section v-for="group in store.grouped" :key="group.area" class="card group">
      <h2><span class="dot" :style="{ background: group.color }"></span>{{ group.area }}</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th class="name"></th>
              <th v-for="d in store.week.trackers[0].days" :key="d.date" :class="{ today: d.date === today() }">{{ shortDay(d.date) }}</th>
              <th>week</th>
              <th>streak</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <template v-for="t in group.trackers" :key="t.id">
              <tr :class="{ inactive: !t.active }">
                <td class="name">
                  <strong>{{ t.name }}</strong>
                  <div class="muted small">
                    {{ t.type.replace('_', ' ') }}<span v-if="t.target_value && t.type !== 'daily_bool'">, target {{ t.target_value }}{{ t.unit ? ' ' + t.unit : '' }}/{{ t.target_period }}</span>
                  </div>
                </td>
                <td v-for="d in t.days" :key="d.date" class="cell" :class="{ met: d.met, has: d.value !== null, today: d.date === today(), future: d.date > today() }">
                  <button v-if="isGrid(t)" type="button" class="tick" :title="d.note || d.date" @click="run(() => store.tick(t.id, d.date))">{{ cellLabel(t, d) || '·' }}</button>
                  <button v-else type="button" class="tick num" :title="d.note || d.date" @click="promptValue(t, d)">{{ cellLabel(t, d) || '·' }}</button>
                </td>
                <td class="num-cell">
                  <span v-if="t.type === 'daily_bool'">{{ Math.round(t.completion * 100) }}%</span>
                  <span v-else>{{ Math.round(t.week_total * 10) / 10 }}<span v-if="t.target_value && t.target_period === 'week'"> / {{ t.target_value }}</span></span>
                </td>
                <td class="num-cell">{{ t.streak }}</td>
                <td class="actions">
                  <button v-if="!isGrid(t)" type="button" class="link" @click="toggleChart(t)">{{ charts[t.id] ? 'hide chart' : 'chart' }}</button>
                  <button type="button" class="link" @click="editing = t">edit</button>
                  <button type="button" class="link" @click="archive(t)">{{ t.active ? 'archive' : 'restore' }}</button>
                  <button type="button" class="link danger" @click="remove(t)">delete</button>
                </td>
              </tr>
              <tr v-if="charts[t.id]" class="chart-row">
                <td :colspan="11">
                  <LineChart :points="charts[t.id].points" :target="t.target_period === 'day' ? t.target_value : null" :unit="t.unit || ''" />
                  <div class="muted small">Last 8 weeks. Weekly sums:
                    <span v-for="w in charts[t.id].weekly" :key="w.week_start">{{ w.week_start.slice(5) }}: {{ Math.round(w.sum * 10) / 10 }} &nbsp;</span>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
h1 { font-size: 1.3rem; margin: 0; }
h2 { font-size: 1rem; margin: 0 0 0.5rem; display: flex; align-items: center; gap: 0.4rem; }
.dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.head { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center; margin-bottom: 1rem; }
.check { display: flex; align-items: center; gap: 0.3rem; font-size: 0.85rem; }
.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 0.85rem; }
th { font-weight: 500; color: #6b7280; padding: 0.2rem 0.3rem; text-align: center; white-space: nowrap; }
th.today { color: #2563eb; font-weight: 700; }
td { padding: 0.2rem 0.3rem; text-align: center; border-top: 1px solid #f3f4f6; }
td.name { text-align: left; min-width: 140px; }
.small { font-size: 0.72rem; }
tr.inactive { opacity: 0.5; }
.tick { width: 34px; height: 30px; border-radius: 4px; border: 1px solid #e5e7eb; background: #fff; color: #9ca3af; font-size: 0.85rem; padding: 0; }
.tick.num { width: 48px; }
.cell.has .tick { color: #111827; background: #f3f4f6; }
.cell.met .tick { background: #d1fae5; border-color: #6ee7b7; color: #065f46; }
.cell.today .tick { border-color: #2563eb; }
.cell.future .tick { opacity: 0.5; }
.num-cell { white-space: nowrap; }
.actions { white-space: nowrap; text-align: right; }
.link { border: none; background: none; color: #2563eb; padding: 0.1rem 0.3rem; font-size: 0.78rem; }
.link.danger { color: #b91c1c; }
.chart-row td { padding: 0.5rem 0.3rem 0.8rem; }
</style>
