<script setup>
import { computed, onMounted, ref } from 'vue'
import AreaDot from '../components/shared/AreaDot.vue'
import AreaSelect from '../components/shared/AreaSelect.vue'
import WeekNav from '../components/shared/WeekNav.vue'
import { formatDay, today, tomorrow } from '../lib/dates'
import { useGoalsStore } from '../stores/goals'

const store = useGoalsStore()
const error = ref('')
const newGoal = ref({ title: '', area_id: null, target_value: null })
const newDo = ref({ [today()]: '', [tomorrow()]: '' })
const suggestFor = ref(tomorrow())

const days = computed(() => [
  { key: today(), label: `Today, ${formatDay(today())}` },
  { key: tomorrow(), label: `Tomorrow, ${formatDay(tomorrow())}` },
])

onMounted(() => store.load())

async function run(fn) {
  error.value = ''
  try {
    await fn()
  } catch (err) {
    error.value = err.message
  }
}

function addGoal() {
  if (!newGoal.value.title.trim()) return
  run(async () => {
    await store.createGoal({ title: newGoal.value.title, area_id: newGoal.value.area_id || null, target_value: newGoal.value.target_value || null })
    newGoal.value = { title: '', area_id: null, target_value: null }
  })
}

function addDo(day) {
  const title = (newDo.value[day] || '').trim()
  if (!title) return
  run(async () => {
    await store.createDo({ date: day, title })
    newDo.value[day] = ''
  })
}

function renameDo(item, event) {
  const title = event.target.value.trim()
  if (title && title !== item.title) run(() => store.updateDo(item.id, { title }))
}

function suggest() {
  run(() => store.suggest(suggestFor.value))
}

function acceptSuggestion(s) {
  run(async () => {
    await store.createDo({ date: suggestFor.value, title: s.title, task_id: s.task_id || undefined })
    store.suggestions.suggestions = store.suggestions.suggestions.filter((x) => x !== s)
  })
}
</script>

<template>
  <div class="goals">
    <h1>Goals</h1>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>

    <section class="dos">
      <div v-for="d in days" :key="d.key" class="card day">
        <h2>{{ d.label }}</h2>
        <ul>
          <li v-for="item in store.dosFor(d.key)" :key="item.id" :class="{ done: item.done }">
            <input type="checkbox" :checked="item.done" @change="run(() => store.toggleDo(item))" />
            <input class="title" type="text" :value="item.title" @change="renameDo(item, $event)" />
            <span v-if="item.warning" class="warn" :title="`Rolled over ${item.roll_count} times since ${item.rolled_from_date}`">rolled {{ item.roll_count }}x</span>
            <span v-else-if="item.roll_count" class="muted">rolled</span>
            <button type="button" class="x" @click="run(() => store.removeDo(item.id))">&times;</button>
          </li>
        </ul>
        <form class="add" @submit.prevent="addDo(d.key)">
          <input v-model="newDo[d.key]" type="text" :placeholder="store.dosFor(d.key).length >= 3 ? 'Add another (three is the aim)' : 'Add a do'" />
          <button type="submit">Add</button>
        </form>
      </div>
    </section>

    <section class="card suggest">
      <div class="row">
        <strong>Suggest three do's</strong>
        <select v-model="suggestFor">
          <option :value="today()">for today</option>
          <option :value="tomorrow()">for tomorrow</option>
        </select>
        <button type="button" @click="suggest">Suggest</button>
        <button type="button" class="link" @click="run(() => store.rolloverNow())">Run rollover now</button>
      </div>
      <ul v-if="store.suggestions">
        <li v-if="!store.suggestions.suggestions.length" class="muted">Nothing to suggest, no open tasks or deadlines.</li>
        <li v-for="s in store.suggestions.suggestions" :key="s.title">
          <span>{{ s.title }} <span class="muted">{{ s.reason }}</span></span>
          <button type="button" @click="acceptSuggestion(s)">Add</button>
        </li>
        <li class="muted small">picked by {{ store.suggestions.source }}</li>
      </ul>
    </section>

    <section class="card">
      <div class="row">
        <h2>Weekly goals</h2>
        <WeekNav :week-start="store.weekStart" @change="run(() => store.loadWeek($event))" />
      </div>
      <ul class="goal-list">
        <li v-for="g in store.goals" :key="g.id" :class="{ done: g.done }">
          <input type="checkbox" :checked="g.done" @change="run(() => store.updateGoal(g.id, { done: !g.done }))" />
          <div class="goal-body">
            <div class="goal-title">{{ g.title }} <AreaDot :area-id="g.area_id" label /></div>
            <div v-if="g.target_value" class="progress">
              <div class="bar"><div class="fill" :style="{ width: Math.round((g.progress || 0) * 100) + '%' }"></div></div>
              <span>{{ g.current_value }} / {{ g.target_value }}</span>
              <button type="button" @click="run(() => store.progressGoal(g.id, 1))">+1</button>
              <button type="button" @click="run(() => store.progressGoal(g.id, -1))">-1</button>
            </div>
          </div>
          <button type="button" class="x" @click="run(() => store.removeGoal(g.id))">&times;</button>
        </li>
        <li v-if="!store.goals.length" class="muted">No goals for this week yet.</li>
      </ul>
      <form class="add goal-add" @submit.prevent="addGoal">
        <input v-model="newGoal.title" type="text" placeholder="New weekly goal" />
        <AreaSelect v-model="newGoal.area_id" />
        <input v-model.number="newGoal.target_value" type="number" min="1" step="any" placeholder="target (optional)" />
        <button type="submit">Add</button>
      </form>
    </section>
  </div>
</template>

<style scoped>
h1 { font-size: 1.3rem; }
h2 { font-size: 1rem; margin: 0 0 0.5rem; }
.dos { display: grid; grid-template-columns: 1fr; gap: 1rem; }
@media (min-width: 720px) { .dos { grid-template-columns: 1fr 1fr; } }
ul { list-style: none; padding: 0; margin: 0; }
li { display: flex; align-items: center; gap: 0.5rem; padding: 0.3rem 0; }
li.done .title, li.done .goal-title { text-decoration: line-through; color: #9ca3af; }
.title { flex: 1; font: inherit; border: 1px solid transparent; padding: 0.2rem; border-radius: 3px; }
.title:focus { border-color: #d1d5db; background: #fff; }
.warn { color: #b91c1c; font-size: 0.75rem; font-weight: 600; }
.x { border: none; background: none; color: #9ca3af; font-size: 1.1rem; padding: 0 0.3rem; }
.add { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.5rem; }
.goal-add :deep(select) { flex: 1; min-width: 110px; }
.add input[type='text'] { flex: 1; font: inherit; padding: 0.35rem; border: 1px solid #d1d5db; border-radius: 4px; }
.goal-add input[type='number'] { width: 130px; font: inherit; padding: 0.35rem; border: 1px solid #d1d5db; border-radius: 4px; }
.row { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
.link { border: none; background: none; color: #2563eb; }
.small { font-size: 0.75rem; }
.goal-body { flex: 1; }
.progress { display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; margin-top: 0.2rem; }
.bar { flex: 1; height: 6px; background: #e5e7eb; border-radius: 3px; overflow: hidden; max-width: 200px; }
.fill { height: 100%; background: #059669; }
.progress button { padding: 0 0.4rem; font-size: 0.75rem; }
</style>
