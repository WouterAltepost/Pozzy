<script setup>
import { computed, ref, watch } from 'vue'
import { PhX } from '@phosphor-icons/vue'
import WeekNav from '../components/shared/WeekNav.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import { useReady } from '../composables/useReady'
import UiButton from '../components/ui/UiButton.vue'
import UiSkeleton from '../components/ui/UiSkeleton.vue'
import UiField from '../components/ui/UiField.vue'
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

const ready = useReady(() => Promise.all([areas.load(), store.load()]))

// `pending` names the action in flight so only its own control spins.
const pending = ref('')
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
async function runAs(name, fn) {
  pending.value = name
  try {
    await run(fn)
  } finally {
    pending.value = ''
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
    <PageHeader title="Weekly review">
      <WeekNav :week-start="store.week" @change="changeWeek" />
    </PageHeader>
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>
    <UiLoadGate :ready="ready" label="Loading review">

    <div v-if="!review && !store.loading" class="card">
      <p class="muted">No review for this week yet. The draft job runs Sunday 18:00, or generate it now.</p>
      <UiButton variant="primary" :loading="busy" @click="run(() => store.generate())">Generate review</UiButton>
    </div>

    <template v-if="review">
      <section class="card">
        <div class="card-head">
          <h2>Numbers</h2>
          <span class="meta">
            <template v-if="review.finalized">finalized {{ formatDateTime(review.finalized_at) }}</template>
            <button v-else type="button" class="link-btn" :disabled="busy" @click="runAs('stats', () => store.refreshStats())">{{ pending === 'stats' ? 'Refreshing' : 'Refresh' }}</button>
          </span>
        </div>
        <div v-if="stats" class="tiles">
          <div class="tile inset"><div class="big num">{{ stats.goals.done }}/{{ stats.goals.total }}</div><div class="muted xs">weekly goals</div></div>
          <div class="tile inset"><div class="big num">{{ pct(stats.dos.rate) }}</div><div class="muted xs">do's done, {{ stats.dos.rolled }} rolled</div></div>
          <div class="tile inset"><div class="big num">{{ stats.tasks.done }}</div><div class="muted xs">tasks done, {{ stats.tasks.overdue }} overdue</div></div>
          <div class="tile inset"><div class="big num">{{ stats.hours.total_hours }}h</div><div class="muted xs">logged</div></div>
          <div v-if="stats.emails" class="tile inset"><div class="big num">{{ stats.emails.handled }}/{{ stats.emails.received }}</div><div class="muted xs">emails handled</div></div>
        </div>
        <div v-if="stats" class="cols">
          <div>
            <h3>Goals</h3>
            <ul class="plain"><li v-for="g in stats.goals.items" :key="g.title" :class="{ done: g.done }">{{ g.title }} <span v-if="g.progress" class="muted small num">{{ g.progress }}</span></li><li v-if="!stats.goals.items.length" class="muted">none</li></ul>
            <h3>Hours</h3>
            <ul class="plain"><li v-for="h in stats.hours.areas" :key="h.area" class="num">{{ h.area }}: {{ h.hours }}h<span v-if="h.target_hours" class="muted"> / {{ h.target_hours }}h</span></li><li v-if="!stats.hours.areas.length" class="muted">none</li></ul>
          </div>
          <div>
            <h3>Habits</h3>
            <ul class="plain"><li v-for="t in stats.trackers" :key="t.name" class="num">{{ t.name }}: {{ pct(t.completion) }}<span class="muted small"> streak {{ t.streak }}</span></li><li v-if="!stats.trackers.length" class="muted">none</li></ul>
            <h3>Missed do's</h3>
            <ul class="plain"><li v-for="m in stats.dos.missed" :key="m">{{ m }}</li><li v-if="!stats.dos.missed.length" class="muted">none</li></ul>
            <h3 v-if="stats.deadlines.upcoming.length">Deadlines next week</h3>
            <ul class="plain"><li v-for="d in stats.deadlines.upcoming" :key="d.title">{{ d.title }} <span class="muted small">{{ d.course }} {{ d.due }}</span></li></ul>
          </div>
        </div>
      </section>

      <section class="card">
        <div class="card-head">
          <h2>Reflection</h2>
          <span class="meta">
            {{ review.reflection_source === 'claude' ? 'Claude' : review.reflection_source === 'edited' ? 'edited' : 'rules' }}
            <UiButton v-if="!locked" size="sm" variant="ghost" :loading="pending === 'reflection'" :disabled="busy" @click="runAs('reflection', () => store.generate())">Regenerate</UiButton>
          </span>
        </div>
        <UiSkeleton v-if="pending === 'reflection'" :lines="5" />
        <div v-else class="prose">
          <p v-for="(p, i) in paragraphs" :key="i">{{ p }}</p>
          <p v-if="!paragraphs.length" class="muted">No reflection yet.</p>
        </div>
      </section>

      <section class="card">
        <div class="card-head"><h2>Your notes</h2></div>
        <textarea v-model="notes" rows="4" :disabled="locked" placeholder="What the numbers do not show" aria-label="Your notes" @blur="saveNotes"></textarea>
      </section>

      <section class="card">
        <div class="card-head"><h2>Next week focus</h2><span class="meta">becomes next week's goals on finalize</span></div>
        <div v-for="(f, i) in focus" :key="i" class="focus-row">
          <input v-model="f.title" type="text" placeholder="Goal" aria-label="Goal" :disabled="locked" />
          <select v-model="f.area" aria-label="Area" :disabled="locked">
            <option :value="null">No area</option>
            <option v-for="a in areas.items" :key="a.id" :value="a.name">{{ a.name }}</option>
          </select>
          <input v-model="f.target_value" type="number" step="any" min="0" placeholder="target" aria-label="Target" class="narrow" :disabled="locked" />
          <button v-if="!locked" type="button" class="icon-btn" aria-label="Remove" @click="focus.splice(i, 1)"><PhX /></button>
          <div v-if="f.reason" class="muted small reason">{{ f.reason }}</div>
        </div>
        <p v-if="!focus.length" class="muted small">Nothing yet.</p>
        <div v-if="!locked" class="actions">
          <UiButton @click="addFocus">Add</UiButton>
          <UiButton :loading="busy" @click="saveFocus">Save</UiButton>
          <UiButton variant="primary" class="push" :loading="busy" @click="finalize">Finalize week</UiButton>
        </div>
        <p v-if="createdGoals.length" class="ok small created">Created {{ createdGoals.length }} goal(s) for next week. <RouterLink :to="{ name: 'goals' }">Open goals</RouterLink></p>
      </section>
    </template>
    </UiLoadGate>
  </div>
</template>

<style scoped>
.review { max-width: 820px; }
@media (max-width: 699px) { .page-header :deep(.weeknav) { font-size: var(--fs-sm); } }
.tiles { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--sp-2); margin-bottom: var(--sp-4); }
@media (min-width: 640px) { .tiles { grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); } }
.tile { text-align: center; }
.big { font-size: var(--fs-2xl); font-weight: 600; letter-spacing: -0.02em; }
.cols { display: grid; grid-template-columns: 1fr; gap: 0 var(--sp-5); }
@media (min-width: 640px) { .cols { grid-template-columns: 1fr 1fr; } }
h3 { font-size: var(--fs-xs); letter-spacing: 0.02em; color: var(--ink-3); font-weight: 500; margin: var(--sp-3) 0 var(--sp-1); }
.plain li { font-size: var(--fs-md); padding: 2px 0; }
.plain li.done { text-decoration: line-through; color: var(--ink-3); }
.prose { max-width: 68ch; }
.prose p { line-height: 1.6; }
textarea { width: 100%; }
.focus-row { display: grid; grid-template-columns: minmax(0, 1fr) auto auto auto; gap: var(--sp-2); align-items: center; margin-bottom: var(--sp-2); }
.narrow { width: 96px; }
.reason { grid-column: 1 / -1; }
.actions { display: flex; gap: var(--sp-2); margin-top: var(--sp-3); }
.push { margin-left: auto; }
.created { margin-top: var(--sp-3); }
@media (max-width: 520px) { .focus-row { grid-template-columns: 1fr auto; } .focus-row select { grid-column: 1 / -1; } }
</style>
