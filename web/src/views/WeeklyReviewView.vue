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
import UiConfirm from '../components/ui/UiConfirm.vue'
import PullToRefresh from '../components/ios/PullToRefresh.vue'
import { useMediaQuery } from '../composables/useMediaQuery'
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
// Below 1024px this is the iOS app: the numbers become grouped rows, the focus list a form.
const phone = useMediaQuery('(max-width: 1023px)')
const confirming = ref(false)

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
  confirming.value = true
}
function doFinalize() {
  confirming.value = false
  run(async () => {
    const items = focus.value.filter((f) => f.title.trim())
    await store.update({ notes: notes.value, next_week_focus: items })
    createdGoals.value = await store.finalize()
  })
}
</script>

<template>
  <component :is="phone ? PullToRefresh : 'div'" :action="phone ? () => store.load() : undefined">
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
      <section class="card numbers">
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
        <div v-if="stats && phone" class="igroups">
          <p class="ghead">Goals</p>
          <ul class="grp"><li v-for="g in stats.goals.items" :key="g.title" class="vrow" :class="{ done: g.done }"><span class="vl">{{ g.title }}</span><span v-if="g.progress" class="vv num">{{ g.progress }}</span></li><li v-if="!stats.goals.items.length" class="vrow none">None</li></ul>
          <p class="ghead">Hours</p>
          <ul class="grp"><li v-for="h in stats.hours.areas" :key="h.area" class="vrow"><span class="vl">{{ h.area }}</span><span class="vv num">{{ h.hours }}h<template v-if="h.target_hours"> of {{ h.target_hours }}h</template></span></li><li v-if="!stats.hours.areas.length" class="vrow none">None</li></ul>
          <p class="ghead">Habits</p>
          <ul class="grp"><li v-for="t in stats.trackers" :key="t.name" class="vrow"><span class="vl">{{ t.name }}</span><span class="vv num">{{ pct(t.completion) }}<span class="vs">, streak {{ t.streak }}</span></span></li><li v-if="!stats.trackers.length" class="vrow none">None</li></ul>
          <p class="ghead">Missed do's</p>
          <ul class="grp"><li v-for="m in stats.dos.missed" :key="m" class="vrow"><span class="vl">{{ m }}</span></li><li v-if="!stats.dos.missed.length" class="vrow none">None</li></ul>
          <template v-if="stats.deadlines.upcoming.length">
            <p class="ghead">Deadlines next week</p>
            <ul class="grp"><li v-for="d in stats.deadlines.upcoming" :key="d.title" class="vrow"><span class="vl">{{ d.title }}</span><span class="vv">{{ d.course }} {{ d.due }}</span></li></ul>
          </template>
        </div>
        <div v-else-if="stats" class="cols">
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

      <section class="card focus">
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
          <UiButton class="add-focus" @click="addFocus">Add</UiButton>
          <UiButton :loading="busy" @click="saveFocus">Save</UiButton>
          <UiButton variant="primary" class="push" :loading="busy" @click="finalize">Finalize week</UiButton>
        </div>
        <p v-if="createdGoals.length" class="ok small created">Created {{ createdGoals.length }} goal(s) for next week. <RouterLink :to="{ name: 'goals' }">Open goals</RouterLink></p>
      </section>
    </template>
    </UiLoadGate>
    <UiConfirm :open="confirming" title="Finalize this review?" message="Next week's goals are created from the focus list. The review cannot be edited after this." confirm-label="Finalize week" @confirm="doFinalize" @cancel="confirming = false" />
  </div>
  </component>
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
/* iOS: the numbers as tiles over grouped rows, reflection at body size, the focus list as a
   form with one filled field per line and the week's one primary action at the bottom. */
@media (max-width: 1023px) {
  .page-header :deep(.weeknav) { display: flex; width: 100%; justify-content: space-between; padding: 0 2px; }
  .page-header :deep(.weeknav .label) { flex: 1; font-size: var(--fs-md); }
  .tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-bottom: 0; }
  .tile { padding: 12px 8px; border-radius: 10px; background: var(--surface-2); border: 0; }
  .tile:last-child:nth-child(odd) { grid-column: 1 / -1; }
  .big { font-size: 1.75rem; font-weight: 700; letter-spacing: normal; line-height: 1.15; }
  .tile .xs { font-size: var(--fs-sm); color: var(--ink-3); }
  .numbers { margin-bottom: 0; }
  .igroups { margin: 0 calc(var(--sp-4) * -1) calc(var(--sp-4) * -1); padding: var(--sp-1) 0 var(--sp-6); background: var(--bg); }
  .ghead { margin: var(--sp-5) 16px 6px; font-size: var(--fs-sm); text-transform: uppercase; color: var(--ink-3); }
  .grp { background: var(--surface); border-radius: var(--r-lg); overflow: hidden; }
  .vrow { position: relative; display: flex; align-items: baseline; gap: var(--sp-3); min-height: 44px; padding: 11px 16px; font-size: 1.0625rem; line-height: 1.3; }
  .vrow + .vrow::before { content: ''; position: absolute; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line); }
  .vl { flex: 1; min-width: 0; }
  .vv { flex: none; max-width: 50%; text-align: right; color: var(--ink-3); }
  .vs { font-size: var(--fs-md); }
  .vrow.done .vl { color: var(--ink-3); text-decoration: line-through; }
  .vrow.none { color: var(--ink-3); }
  .prose { max-width: none; }
  .prose p { font-size: 1.0625rem; line-height: 1.47; margin-bottom: var(--sp-3); }
  .prose p:last-child { margin-bottom: 0; }
  textarea { font-size: 1.0625rem; line-height: 1.47; }
  .focus .card-head { flex-wrap: wrap; }
  .focus .card-head .meta { flex-basis: 100%; margin: 0; text-align: left; }
  .focus-row { grid-template-columns: minmax(0, 1fr) 96px auto; gap: 8px; padding: var(--sp-3) 0; margin: 0; border-top: 0.5px solid var(--line); }
  .card-head + .focus-row { border-top: 0; padding-top: var(--sp-1); }
  .focus-row > input[type='text'] { grid-column: 1 / -1; }
  .focus-row select { grid-column: auto; }
  .focus-row .narrow { width: 100%; }
  .focus-row .icon-btn { width: 36px; height: 36px; color: var(--danger); }
  .reason { font-size: var(--fs-sm); }
  .actions { flex-wrap: wrap; margin-top: var(--sp-2); }
  .actions > * { flex: 1; }
  .actions .add-focus { flex-basis: 100%; }
  .actions .push { flex-basis: 100%; margin: var(--sp-1) 0 0; height: 50px; font-size: 1.0625rem; }
}
</style>
