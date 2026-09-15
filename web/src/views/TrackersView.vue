<script setup>
import { onMounted, ref } from 'vue'
import { PhChartLineUp, PhCheck } from '@phosphor-icons/vue'
import LineChart from '../components/trackers/LineChart.vue'
import TrackerForm from '../components/trackers/TrackerForm.vue'
import WeekNav from '../components/shared/WeekNav.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiEmpty from '../components/ui/UiEmpty.vue'
import UiSkeleton from '../components/ui/UiSkeleton.vue'
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
    <PageHeader title="Tracking">
      <WeekNav :week-start="store.weekStart" @change="run(() => store.setWeek($event))" />
      <label class="check"><input v-model="store.includeInactive" type="checkbox" @change="store.load()" /> Show archived</label>
      <UiButton variant="primary" @click="editing = 'new'">New tracker</UiButton>
    </PageHeader>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>
    <div v-if="editing" class="card">
      <div class="card-head"><h2>{{ editing === 'new' ? 'New tracker' : 'Edit tracker' }}</h2></div>
      <TrackerForm :tracker="editing === 'new' ? null : editing" @save="save" @cancel="editing = null" />
    </div>

    <div v-if="store.loading && !store.week" class="card"><UiSkeleton :lines="4" /></div>
    <div v-else-if="!store.trackers.length" class="card">
      <UiEmpty title="No trackers yet" hint="Creatine, vitamins, sauna, weight, sleep: anything you want to see per week.">
        <template #icon><PhChartLineUp /></template>
        <template #action><UiButton variant="primary" @click="editing = 'new'">New tracker</UiButton></template>
      </UiEmpty>
    </div>

    <section v-for="group in store.grouped" :key="group.area" class="card group">
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
                  <div class="tname">{{ t.name }}</div>
                  <div class="muted xs">
                    {{ t.type.replace('_', ' ') }}<span v-if="t.target_value && t.type !== 'daily_bool'">, target {{ t.target_value }}{{ t.unit ? ' ' + t.unit : '' }} per {{ t.target_period }}</span>
                  </div>
                </td>
                <td v-for="d in t.days" :key="d.date" class="cell" :class="{ met: d.met, has: d.value !== null, today: d.date === today(), future: d.date > today() }">
                  <button v-if="isGrid(t)" type="button" class="tick" :class="{ bool: t.type === 'daily_bool' }" :title="d.note || d.date" :aria-label="`${t.name} ${d.date}`" :aria-pressed="t.type === 'daily_bool' ? Boolean(d.met) : undefined" @click="run(() => store.tick(t.id, d.date))">
                    <PhCheck v-if="t.type === 'daily_bool' && d.met" weight="bold" class="mark" />
                    <span v-else class="num">{{ cellLabel(t, d) }}</span>
                  </button>
                  <button v-else type="button" class="tick value" :title="d.note || d.date" :aria-label="`${t.name} ${d.date}`" @click="promptValue(t, d)"><span class="num">{{ cellLabel(t, d) }}</span></button>
                </td>
                <td class="num">
                  <span v-if="t.type === 'daily_bool'">{{ Math.round(t.completion * 100) }}%</span>
                  <span v-else>{{ Math.round(t.week_total * 10) / 10 }}<span v-if="t.target_value && t.target_period === 'week'" class="muted"> / {{ t.target_value }}</span></span>
                </td>
                <td class="num">{{ t.streak }}</td>
                <td class="actions">
                  <button v-if="!isGrid(t)" type="button" class="link-btn" @click="toggleChart(t)">{{ charts[t.id] ? 'hide chart' : 'chart' }}</button>
                  <button type="button" class="link-btn" @click="editing = t">edit</button>
                  <button type="button" class="link-btn" @click="archive(t)">{{ t.active ? 'archive' : 'restore' }}</button>
                  <button type="button" class="link-btn danger" @click="remove(t)">delete</button>
                </td>
              </tr>
              <tr v-if="charts[t.id]" class="chart-row">
                <td :colspan="11">
                  <LineChart :points="charts[t.id].points" :target="t.target_period === 'day' ? t.target_value : null" :unit="t.unit || ''" />
                  <div class="muted xs sums">Last 8 weeks, weekly sums:
                    <span v-for="w in charts[t.id].weekly" :key="w.week_start" class="num">{{ w.week_start.slice(5) }}: {{ Math.round(w.sum * 10) / 10 }}</span>
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
.check { display: flex; align-items: center; gap: 6px; font-size: var(--fs-md); white-space: nowrap; }
.card-head h2 { display: flex; align-items: center; gap: 8px; }
.dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.grid th.day { text-align: center; }
.grid th.today { color: var(--brand); }
.grid td { text-align: center; padding: 6px 4px; }
.grid td.name { text-align: left; min-width: 150px; padding-left: 0; }
.tname { font-weight: 500; }
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
.sums { display: flex; flex-wrap: wrap; gap: var(--sp-2); margin-top: 4px; }
</style>
