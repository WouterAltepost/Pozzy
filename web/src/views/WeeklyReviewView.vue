<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import WeekNav from '../components/shared/WeekNav.vue'
import { formatDateTime } from '../lib/dates'
import { useAreasStore } from '../stores/areas'
import { useReviewsStore } from '../stores/reviews'

const store = useReviewsStore()
const areas = useAreasStore()
const busy = ref(false)
const error = ref('')
const notes = ref('')
const focus = ref([])
const createdGoals = ref([])

const review = computed(() => store.review)
const stats = computed(() => review.value?.stats || null)
const locked = computed(() => !!review.value?.finalized)
const paragraphs = computed(() => (review.value?.reflection || '').split(/\n{2,}/).map((p) => p.trim()).filter(Boolean))
const pct = (v) => (v == null ? '-' : Math.round(v * 100) + '%')

watch(review, (r) => {
  notes.value = r?.notes || ''
  focus.value = (r?.next_week_focus || []).map((f) => ({ ...f }))
  createdGoals.value = []
}, { immediate: true })

onMounted(() => {
  areas.load()
  store.load()
})

async function run(fn) {
  error.value = ''
  busy.value = true
  try {
    await fn()
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}

function changeWeek(week) {
  store.load(week)
}

function addFocus() {
  focus.value.push({ title: '', area: null, target_value: null, task_id: null, reason: '' })
}

function saveFocus() {
  const items = focus.value.filter((f) => f.title.trim()).map((f) => ({ ...f, target_value: f.target_value === '' || f.target_value == null ? null : Number(f.target_value) }))
  run(() => store.update({ next_week_focus: items }))
}

function saveNotes() {
  if ((review.value?.notes || '') === notes.value) return
  run(() => store.update({ notes: notes.value }))
}

function finalize() {
  if (!window.confirm('Finalize this review and create next week\'s goals from the focus list?')) return
  run(async () => {
    const items = focus.value.filter((f) => f.title.trim())
    await store.update({ notes: notes.value, next_week_focus: items })
    createdGoals.value = await store.finalize()
  })
}
</script>

<template>
  <div class="review">
    <div class="head">
      <h1>Weekly review</h1>
      <WeekNav :week-start="store.week" @change="changeWeek" />
    </div>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>

    <div v-if="!review && !store.loading" class="card">
      <p class="muted">No review for this week yet. The draft job runs Sunday 18:00, or generate it now.</p>
      <button type="button" :disabled="busy" @click="run(() => store.generate())">{{ busy ? 'Working' : 'Generate review' }}</button>
    </div>

    <template v-if="review">
      <section class="card">
        <h2>
          Numbers
          <span class="muted small">
            <template v-if="review.finalized">finalized {{ formatDateTime(review.finalized_at) }}</template>
            <template v-else><button type="button" class="link" :disabled="busy" @click="run(() => store.refreshStats())">refresh</button></template>
          </span>
        </h2>
        <div v-if="stats" class="tiles">
          <div class="tile"><div class="big">{{ stats.goals.done }}/{{ stats.goals.total }}</div><div class="muted small">weekly goals</div></div>
          <div class="tile"><div class="big">{{ pct(stats.dos.rate) }}</div><div class="muted small">do's done, {{ stats.dos.rolled }} rolled</div></div>
          <div class="tile"><div class="big">{{ stats.tasks.done }}</div><div class="muted small">tasks done, {{ stats.tasks.overdue }} overdue</div></div>
          <div class="tile"><div class="big">{{ stats.hours.total_hours }}h</div><div class="muted small">logged</div></div>
          <div v-if="stats.emails" class="tile"><div class="big">{{ stats.emails.handled }}/{{ stats.emails.received }}</div><div class="muted small">emails handled</div></div>
        </div>
        <div v-if="stats" class="cols">
          <div>
            <h3>Goals</h3>
            <ul><li v-for="g in stats.goals.items" :key="g.title" :class="{ done: g.done }">{{ g.title }} <span v-if="g.progress" class="muted small">{{ g.progress }}</span></li><li v-if="!stats.goals.items.length" class="muted">none</li></ul>
            <h3>Hours</h3>
            <ul><li v-for="h in stats.hours.areas" :key="h.area">{{ h.area }}: {{ h.hours }}h<span v-if="h.target_hours" class="muted"> / {{ h.target_hours }}h</span></li><li v-if="!stats.hours.areas.length" class="muted">none</li></ul>
          </div>
          <div>
            <h3>Habits</h3>
            <ul><li v-for="t in stats.trackers" :key="t.name">{{ t.name }}: {{ pct(t.completion) }}<span class="muted small"> streak {{ t.streak }}</span></li><li v-if="!stats.trackers.length" class="muted">none</li></ul>
            <h3>Missed do's</h3>
            <ul><li v-for="m in stats.dos.missed" :key="m">{{ m }}</li><li v-if="!stats.dos.missed.length" class="muted">none</li></ul>
            <h3 v-if="stats.deadlines.upcoming.length">Deadlines next week</h3>
            <ul><li v-for="d in stats.deadlines.upcoming" :key="d.title">{{ d.title }} <span class="muted small">{{ d.course }} {{ d.due }}</span></li></ul>
          </div>
        </div>
      </section>

      <section class="card">
        <h2>
          Reflection
          <span class="muted small">
            {{ review.reflection_source === 'claude' ? 'Claude' : review.reflection_source === 'edited' ? 'edited' : 'rules' }}
            <template v-if="!locked"> · <button type="button" class="link" :disabled="busy" @click="run(() => store.generate())">regenerate</button></template>
          </span>
        </h2>
        <p v-for="(p, i) in paragraphs" :key="i">{{ p }}</p>
        <p v-if="!paragraphs.length" class="muted">No reflection yet.</p>
      </section>

      <section class="card">
        <h2>Your notes</h2>
        <textarea v-model="notes" rows="4" :disabled="locked" placeholder="What the numbers do not show" @blur="saveNotes"></textarea>
      </section>

      <section class="card">
        <h2>Next week focus <span class="muted small">becomes next week's goals on finalize</span></h2>
        <div v-for="(f, i) in focus" :key="i" class="focus-row">
          <input v-model="f.title" type="text" placeholder="Goal" :disabled="locked" />
          <select v-model="f.area" :disabled="locked">
            <option :value="null">No area</option>
            <option v-for="a in areas.items" :key="a.id" :value="a.name">{{ a.name }}</option>
          </select>
          <input v-model="f.target_value" type="number" step="any" min="0" placeholder="target" class="narrow" :disabled="locked" />
          <button v-if="!locked" type="button" class="tiny" @click="focus.splice(i, 1)">x</button>
          <div v-if="f.reason" class="muted small reason">{{ f.reason }}</div>
        </div>
        <p v-if="!focus.length" class="muted">Nothing yet.</p>
        <div v-if="!locked" class="actions">
          <button type="button" @click="addFocus">Add</button>
          <button type="button" :disabled="busy" @click="saveFocus">Save</button>
          <button type="button" class="primary" :disabled="busy" @click="finalize">Finalize week</button>
        </div>
        <p v-if="createdGoals.length" class="ok small">Created {{ createdGoals.length }} goal(s) for next week. <RouterLink :to="{ name: 'goals' }">Open goals</RouterLink></p>
      </section>
    </template>
  </div>
</template>

<style scoped>
h1 { font-size: 1.3rem; margin: 0; }
h2 { font-size: 1rem; margin: 0 0 0.5rem; display: flex; justify-content: space-between; align-items: baseline; gap: 0.5rem; }
h3 { font-size: 0.85rem; margin: 0.6rem 0 0.2rem; color: #4b5563; }
.head { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 0.5rem; margin-bottom: 1rem; }
.small { font-size: 0.78rem; font-weight: normal; }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 0.5rem; margin-bottom: 0.5rem; }
.tile { background: #f9fafb; border-radius: 4px; padding: 0.5rem; text-align: center; }
.big { font-size: 1.3rem; font-weight: 600; }
.cols { display: grid; grid-template-columns: 1fr; gap: 0 1rem; }
@media (min-width: 640px) { .cols { grid-template-columns: 1fr 1fr; } }
ul { list-style: none; padding: 0; margin: 0; font-size: 0.9rem; }
li.done { text-decoration: line-through; color: #9ca3af; }
p { margin: 0 0 0.6rem; font-size: 0.92rem; line-height: 1.45; }
textarea { width: 100%; font: inherit; padding: 0.4rem; border: 1px solid #d1d5db; border-radius: 4px; }
.focus-row { display: grid; grid-template-columns: 1fr auto auto auto; gap: 0.4rem; align-items: center; margin-bottom: 0.3rem; }
.focus-row input, .focus-row select { font: inherit; padding: 0.35rem; border: 1px solid #d1d5db; border-radius: 4px; }
.narrow { width: 5rem; }
.reason { grid-column: 1 / -1; }
.tiny { padding: 0 0.4rem; font-size: 0.75rem; }
.actions { display: flex; gap: 0.5rem; margin-top: 0.5rem; }
.primary { background: #111827; color: #fff; border-color: #111827; }
.link { border: none; background: none; padding: 0; color: #2563eb; font-size: 0.78rem; cursor: pointer; }
</style>
