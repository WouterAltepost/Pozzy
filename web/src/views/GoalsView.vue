<script setup>
import { computed, ref } from 'vue'
import { PhTarget, PhX } from '@phosphor-icons/vue'
import AreaDot from '../components/shared/AreaDot.vue'
import AreaSelect from '../components/shared/AreaSelect.vue'
import WeekNav from '../components/shared/WeekNav.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import { useReady } from '../composables/useReady'
import UiBadge from '../components/ui/UiBadge.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiEmpty from '../components/ui/UiEmpty.vue'
import { formatDay, today, tomorrow } from '../lib/dates'
import { useGoalsStore } from '../stores/goals'

const store = useGoalsStore()
const error = ref('')
const newGoal = ref({ title: '', area_id: null, target_value: null })
const newDo = ref({ [today()]: '', [tomorrow()]: '' })
const suggestFor = ref(tomorrow())

const days = computed(() => [
  { key: today(), label: 'Today', date: formatDay(today()) },
  { key: tomorrow(), label: 'Tomorrow', date: formatDay(tomorrow()) },
])

const ready = useReady(() => store.load())

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
    <PageHeader title="Goals" />
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>
    <UiLoadGate :ready="ready" label="Loading goals">

    <section class="dos">
      <div v-for="d in days" :key="d.key" class="card day">
        <div class="card-head">
          <h2>{{ d.label }}</h2>
          <span class="meta">{{ d.date }}</span>
        </div>
        <ul>
          <li v-for="item in store.dosFor(d.key)" :key="item.id" class="list-row" :class="{ done: item.done }">
            <input type="checkbox" :checked="item.done" :aria-label="item.title" @change="run(() => store.toggleDo(item))" />
            <input class="title" type="text" :value="item.title" aria-label="Do title" @change="renameDo(item, $event)" />
            <UiBadge v-if="item.warning" tone="warn" :title="`Rolled over ${item.roll_count} times since ${item.rolled_from_date}`">rolled {{ item.roll_count }}x</UiBadge>
            <UiBadge v-else-if="item.roll_count" tone="neutral">rolled</UiBadge>
            <button type="button" class="icon-btn" aria-label="Remove" @click="run(() => store.removeDo(item.id))"><PhX /></button>
          </li>
          <li v-if="!store.dosFor(d.key).length" class="muted small hint">Nothing set yet.</li>
        </ul>
        <form class="add" @submit.prevent="addDo(d.key)">
          <input v-model="newDo[d.key]" type="text" :placeholder="store.dosFor(d.key).length >= 3 ? 'Add another (three is the aim)' : 'Add a do'" :aria-label="'Add a do for ' + d.label" />
          <UiButton type="submit">Add</UiButton>
        </form>
      </div>
    </section>

    <section class="card suggest">
      <div class="card-head">
        <h2>Suggest three do's</h2>
        <span class="meta"><button type="button" class="link-btn" @click="run(() => store.rolloverNow())">Run rollover now</button></span>
      </div>
      <div class="toolbar">
        <select v-model="suggestFor" aria-label="Suggest for">
          <option :value="today()">for today</option>
          <option :value="tomorrow()">for tomorrow</option>
        </select>
        <UiButton variant="primary" @click="suggest">Suggest</UiButton>
      </div>
      <ul v-if="store.suggestions" class="suggestions">
        <li v-if="!store.suggestions.suggestions.length" class="muted small hint">Nothing to suggest, no open tasks or deadlines.</li>
        <li v-for="s in store.suggestions.suggestions" :key="s.title" class="list-row">
          <span class="title"><span>{{ s.title }}</span> <span class="muted small">{{ s.reason }}</span></span>
          <UiButton size="sm" @click="acceptSuggestion(s)">Add</UiButton>
        </li>
        <li class="muted xs picked">picked by {{ store.suggestions.source }}</li>
      </ul>
    </section>

    <section class="card">
      <div class="card-head">
        <h2>Weekly goals</h2>
        <span class="meta"><WeekNav :week-start="store.weekStart" @change="run(() => store.loadWeek($event))" /></span>
      </div>
      <ul class="goal-list">
        <li v-for="g in store.goals" :key="g.id" class="list-row" :class="{ done: g.done }">
          <input type="checkbox" :checked="g.done" :aria-label="g.title" @change="run(() => store.updateGoal(g.id, { done: !g.done }))" />
          <div class="goal-body">
            <div class="title">{{ g.title }} <AreaDot :area-id="g.area_id" label /></div>
            <div v-if="g.target_value" class="progress">
              <div class="bar"><div class="fill" :class="{ full: g.done }" :style="{ width: Math.round((g.progress || 0) * 100) + '%' }"></div></div>
              <span class="num small">{{ g.current_value }} / {{ g.target_value }}</span>
              <UiButton size="sm" variant="ghost" aria-label="Add one" @click="run(() => store.progressGoal(g.id, 1))">+1</UiButton>
              <UiButton size="sm" variant="ghost" aria-label="Remove one" @click="run(() => store.progressGoal(g.id, -1))">-1</UiButton>
            </div>
          </div>
          <button type="button" class="icon-btn" aria-label="Remove goal" @click="run(() => store.removeGoal(g.id))"><PhX /></button>
        </li>
      </ul>
      <UiEmpty v-if="!store.goals.length" compact title="No goals for this week yet" hint="Add one below, or finalize a weekly review to draft them.">
        <template #icon><PhTarget /></template>
      </UiEmpty>
      <form class="add goal-add" @submit.prevent="addGoal">
        <input v-model="newGoal.title" type="text" placeholder="New weekly goal" aria-label="New weekly goal" />
        <AreaSelect v-model="newGoal.area_id" aria-label="Area" />
        <input v-model.number="newGoal.target_value" type="number" min="1" step="any" placeholder="target" aria-label="Target" class="target" />
        <UiButton type="submit">Add</UiButton>
      </form>
    </section>
    </UiLoadGate>
  </div>
</template>

<style scoped>
.dos { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--sp-4); }
@media (min-width: 720px) { .dos { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: var(--sp-5); } }
.dos .card { margin-bottom: var(--sp-4); }
.list-row .title { flex: 1; min-width: 0; }
input.title { height: 30px; padding: 0 6px; margin: 0 -6px; border-color: transparent; background: transparent; }
input.title:hover { border-color: var(--line-2); background: var(--surface); }
input.title:focus-visible { border-color: var(--line-2); background: var(--surface); }
.hint { padding: var(--sp-2) 0; }
.add { display: flex; flex-wrap: wrap; gap: var(--sp-2); margin-top: var(--sp-3); }
.add input[type='text'] { flex: 1 1 160px; }
.goal-add :deep(select) { flex: 1 1 120px; min-width: 110px; }
.goal-add .target { width: 110px; }
.suggestions { margin-top: var(--sp-3); }
.picked { padding-top: var(--sp-2); }
.goal-body { flex: 1; min-width: 0; }
.progress { display: flex; align-items: center; gap: var(--sp-2); margin-top: 4px; }
.progress .bar { flex: 1; max-width: 220px; }
</style>
