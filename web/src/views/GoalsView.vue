<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { PhCheck, PhMinus, PhPlus, PhPlusCircle, PhTarget, PhTrash, PhArrowCounterClockwise, PhX } from '@phosphor-icons/vue'
import AreaDot from '../components/shared/AreaDot.vue'
import AreaSelect from '../components/shared/AreaSelect.vue'
import WeekNav from '../components/shared/WeekNav.vue'
import PullToRefresh from '../components/ios/PullToRefresh.vue'
import SwipeRow from '../components/ios/SwipeRow.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import { useReady } from '../composables/useReady'
import { useMediaQuery } from '../composables/useMediaQuery'
import UiBadge from '../components/ui/UiBadge.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiEmpty from '../components/ui/UiEmpty.vue'
import UiModal from '../components/ui/UiModal.vue'
import UiSegmented from '../components/ui/UiSegmented.vue'
import UiSkeleton from '../components/ui/UiSkeleton.vue'
import { formatDay, today, tomorrow } from '../lib/dates'
import { tick } from '../lib/haptics'
import { useAreasStore } from '../stores/areas'
import { useGoalsStore } from '../stores/goals'

const store = useGoalsStore()
const route = useRoute()
const error = ref('')
const newGoal = ref({ title: '', area_id: null, target_value: null })
const newDo = ref({ [today()]: '', [tomorrow()]: '' })
const suggestFor = ref(tomorrow())
// Below 1024px this is the iOS app: Reminders rows with swipe actions, add in a sheet.
const phone = useMediaQuery('(max-width: 1023px)')
const goalSheet = ref(false)
const SUGGEST_FOR = [
  { value: today(), label: 'Today' },
  { value: tomorrow(), label: 'Tomorrow' },
]

const days = computed(() => [
  { key: today(), label: 'Today', date: formatDay(today()) },
  { key: tomorrow(), label: 'Tomorrow', date: formatDay(tomorrow()) },
])

const areas = useAreasStore()
// Areas load here too: on the phone no AreaSelect is mounted to load them for the labels.
const ready = useReady(() => Promise.all([store.load(), areas.load()]))

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
    goalSheet.value = false
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

// Phone commits tick like a Reminders checkbox. Swipe actions tick in SwipeRow.
function toggleDo(item) {
  tick()
  run(() => store.toggleDo(item))
}
function toggleGoal(g) {
  tick()
  run(() => store.updateGoal(g.id, { done: !g.done }))
}
const doLeading = (item) => [item.done ? { label: 'Undo', icon: PhArrowCounterClockwise, color: '#8E8E93', action: () => run(() => store.toggleDo(item)) } : { label: 'Done', icon: PhCheck, color: 'var(--ok)', action: () => run(() => store.toggleDo(item)) }]
const doTrailing = (item) => [{ label: 'Delete', icon: PhTrash, color: 'var(--danger)', action: () => run(() => store.removeDo(item.id)) }]
const goalLeading = (g) => [g.done ? { label: 'Undo', icon: PhArrowCounterClockwise, color: '#8E8E93', action: () => run(() => store.updateGoal(g.id, { done: false })) } : { label: 'Done', icon: PhCheck, color: 'var(--ok)', action: () => run(() => store.updateGoal(g.id, { done: true })) }]
const goalTrailing = (g) => [{ label: 'Delete', icon: PhTrash, color: 'var(--danger)', action: () => run(() => store.removeGoal(g.id)) }]

const suggesting = ref(false)
const rolling = ref(false)
async function suggest() {
  suggesting.value = true
  try {
    await run(() => store.suggest(suggestFor.value))
  } finally {
    suggesting.value = false
  }
}
async function rollover() {
  rolling.value = true
  try {
    await run(() => store.rolloverNow())
  } finally {
    rolling.value = false
  }
}

function acceptSuggestion(s) {
  run(async () => {
    await store.createDo({ date: suggestFor.value, title: s.title, task_id: s.task_id || undefined })
    store.suggestions.suggestions = store.suggestions.suggestions.filter((x) => x !== s)
  })
}
</script>

<template>
  <component :is="phone ? PullToRefresh : 'div'" :action="phone ? () => store.load() : undefined">
  <div class="goals">
    <Teleport v-if="phone && route.name === 'goals'" defer to="#nav-trailing">
      <button type="button" class="icon-btn" aria-label="New weekly goal" @click="goalSheet = true"><PhPlus weight="regular" /></button>
    </Teleport>
    <PageHeader title="Goals" />
    <p v-if="error || store.error" class="error">{{ error || store.error }}</p>
    <UiLoadGate :ready="ready" label="Loading goals">

    <section class="dos">
      <div v-for="d in days" :key="d.key" class="card day">
        <div class="card-head">
          <h2>{{ d.label }}</h2>
          <span class="meta">{{ d.date }}</span>
        </div>
        <ul v-if="phone" class="ilist">
          <li v-for="item in store.dosFor(d.key)" :key="item.id" class="ili">
            <SwipeRow :leading="doLeading(item)" :trailing="doTrailing(item)">
              <div class="irow" :class="{ done: item.done }">
                <input type="checkbox" :checked="item.done" :aria-label="item.title" @change="toggleDo(item)" />
                <input class="ititle" type="text" :value="item.title" aria-label="Do title" enterkeyhint="done" @change="renameDo(item, $event)" />
                <UiBadge v-if="item.warning" tone="warn" :title="`Rolled over ${item.roll_count} times since ${item.rolled_from_date}`">rolled {{ item.roll_count }}x</UiBadge>
                <UiBadge v-else-if="item.roll_count" tone="neutral">rolled</UiBadge>
                <button type="button" class="icon-btn rm" aria-label="Remove" @click="run(() => store.removeDo(item.id))"><PhX /></button>
              </div>
            </SwipeRow>
          </li>
          <li class="ili">
            <form class="irow iadd" @submit.prevent="addDo(d.key)">
              <PhPlusCircle class="plus" weight="fill" aria-hidden="true" />
              <input v-model="newDo[d.key]" class="ititle" type="text" enterkeyhint="done" :placeholder="store.dosFor(d.key).length >= 3 ? 'Add another (three is the aim)' : 'New do'" :aria-label="'Add a do for ' + d.label" />
            </form>
          </li>
        </ul>
        <template v-else>
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
        </template>
      </div>
    </section>

    <section class="card suggest">
      <div class="card-head">
        <h2>Suggest three do's</h2>
        <span class="meta"><button type="button" class="link-btn" :disabled="rolling" @click="rollover">{{ rolling ? 'Running rollover' : 'Run rollover now' }}</button></span>
      </div>
      <div class="toolbar">
        <UiSegmented v-if="phone" v-model="suggestFor" :options="SUGGEST_FOR" class="pseg" />
        <select v-else v-model="suggestFor" aria-label="Suggest for">
          <option :value="today()">for today</option>
          <option :value="tomorrow()">for tomorrow</option>
        </select>
        <UiButton variant="primary" :block="phone" :loading="suggesting" @click="suggest">Suggest</UiButton>
      </div>
      <UiSkeleton v-if="suggesting" :lines="3" />
      <ul v-else-if="store.suggestions" class="suggestions">
        <li v-if="!store.suggestions.suggestions.length" class="muted small hint">Nothing to suggest, no open tasks or deadlines.</li>
        <li v-for="s in store.suggestions.suggestions" :key="s.title" class="list-row">
          <span class="title"><span>{{ s.title }}</span> <span class="muted small">{{ s.reason }}</span></span>
          <button v-if="phone" type="button" class="icon-btn accept" :aria-label="'Add ' + s.title" @click="acceptSuggestion(s)"><PhPlusCircle weight="fill" /></button>
          <UiButton v-else size="sm" @click="acceptSuggestion(s)">Add</UiButton>
        </li>
        <li class="muted xs picked">picked by {{ store.suggestions.source }}</li>
      </ul>
    </section>

    <section class="card weekly">
      <div class="card-head">
        <h2>Weekly goals</h2>
        <span class="meta"><WeekNav :week-start="store.weekStart" @change="run(() => store.loadWeek($event))" /></span>
      </div>
      <ul v-if="phone" class="ilist">
        <li v-for="g in store.goals" :key="g.id" class="ili">
          <SwipeRow :leading="goalLeading(g)" :trailing="goalTrailing(g)">
            <div class="irow goal" :class="{ done: g.done }">
              <input type="checkbox" :checked="g.done" :aria-label="g.title" @change="toggleGoal(g)" />
              <div class="gbody">
                <div class="gtitle">{{ g.title }}</div>
                <div class="gmeta"><AreaDot :area-id="g.area_id" label /></div>
                <div v-if="g.target_value" class="gprog">
                  <div class="bar"><div class="fill" :class="{ full: g.done }" :style="{ width: Math.round((g.progress || 0) * 100) + '%' }"></div></div>
                  <span class="num gcount">{{ g.current_value }} / {{ g.target_value }}</span>
                  <span class="stepper">
                    <button type="button" aria-label="Remove one" @click="tick(); run(() => store.progressGoal(g.id, -1))"><PhMinus weight="bold" /></button>
                    <button type="button" aria-label="Add one" @click="tick(); run(() => store.progressGoal(g.id, 1))"><PhPlus weight="bold" /></button>
                  </span>
                </div>
              </div>
              <button type="button" class="icon-btn rm" aria-label="Remove goal" @click="run(() => store.removeGoal(g.id))"><PhX /></button>
            </div>
          </SwipeRow>
        </li>
        <li class="ili">
          <button type="button" class="irow iadd addgoal" @click="goalSheet = true"><PhPlusCircle class="plus" weight="fill" aria-hidden="true" /><span>New goal</span></button>
        </li>
      </ul>
      <template v-else>
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
      </template>
    </section>
    <p v-if="phone && !store.goals.length" class="gfoot">No goals for this week yet. Add one, or finalize a weekly review to draft them.</p>
    </UiLoadGate>

    <UiModal v-if="phone" :open="goalSheet" title="New weekly goal" size="sm" @close="goalSheet = false">
      <form class="gform" @submit.prevent="addGoal">
        <div class="grp">
          <label class="frow"><input v-model="newGoal.title" type="text" class="fin" placeholder="Title" aria-label="Title" enterkeyhint="done" /></label>
          <label class="frow"><span class="flabel">Area</span><AreaSelect v-model="newGoal.area_id" class="fval" /></label>
          <label class="frow"><span class="flabel">Target</span><input v-model.number="newGoal.target_value" type="number" min="1" step="any" inputmode="decimal" placeholder="None" class="fval" /></label>
        </div>
        <p class="gnote">A target turns the goal into a counter you step up during the week.</p>
        <UiButton type="submit" variant="primary" block :disabled="!newGoal.title.trim()">Add goal</UiButton>
      </form>
    </UiModal>
  </div>
  </component>
</template>

<style scoped>
@media (max-width: 699px) { :deep(.weeknav .label) { min-width: 0; font-size: var(--fs-sm); } :deep(.weeknav .link-btn) { display: none; } }
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

/* iOS: each plate is a Reminders list. Rows reach the plate edges so swipe actions do too;
   the separator starts at the title, past the circle. */
@media (max-width: 1023px) {
  .dos { gap: 0; }
  .dos .card, .card.weekly { padding: 0; overflow: hidden; margin-bottom: var(--sp-6); }
  .dos .card-head, .weekly .card-head { padding: 12px 16px 4px; margin: 0; }
  .weekly .card-head { align-items: center; }
  .ilist { margin: 0; }
  .ili { position: relative; }
  .ili + .ili::before { content: ''; position: absolute; z-index: 2; top: 0; left: 52px; right: 0; height: 0.5px; background: var(--line); pointer-events: none; }
  .irow { display: flex; align-items: center; gap: 14px; min-height: 44px; padding: 0 16px; background: var(--surface); }
  .irow > input[type='checkbox'] { flex: none; }
  .irow.done .ititle, .irow.done .gtitle { color: var(--ink-3); }
  .irow input.ititle { flex: 1; min-width: 0; height: 44px; padding: 0; border: 0; border-radius: 0; background: transparent; box-shadow: none; font-size: 1.0625rem; color: var(--ink); }
  .irow input.ititle:focus-visible { box-shadow: none; }
  .ititle::placeholder { color: var(--ink-3); }
  .iadd { width: 100%; border: 0; border-radius: 0; box-shadow: none; font: inherit; font-size: 1.0625rem; color: var(--brand); text-align: left; }
  .plus { flex: none; width: 24px; height: 24px; color: var(--brand); margin-left: -1px; }
  .rm { display: none; }
  .goal { align-items: flex-start; padding-top: 11px; padding-bottom: 11px; }
  .goal > input[type='checkbox'] { margin-top: 0; }
  .gbody { flex: 1; min-width: 0; }
  .gtitle { font-size: 1.0625rem; line-height: 1.3; }
  .gmeta { margin-top: 2px; font-size: var(--fs-sm); color: var(--ink-3); }
  .gmeta:empty { display: none; }
  .gprog { display: flex; align-items: center; gap: var(--sp-3); margin-top: 8px; }
  .gprog .bar { flex: 1; }
  .gcount { font-size: var(--fs-md); color: var(--ink-3); }
  .stepper { display: inline-flex; flex: none; height: 32px; border-radius: 8px; background: var(--surface-2); overflow: hidden; }
  .stepper button { position: relative; display: grid; place-items: center; width: 47px; height: 32px; padding: 0; border: 0; border-radius: 0; background: none; box-shadow: none; color: var(--ink); }
  .stepper button + button::before { content: ''; position: absolute; left: 0; top: 8px; bottom: 8px; width: 1px; background: var(--line-2); }
  .stepper button:active { background: var(--surface-3); }
  .stepper svg { width: 15px; height: 15px; }
  .suggest .toolbar { flex-direction: column; align-items: stretch; gap: var(--sp-3); }
  .pseg { display: flex; width: 100%; }
  .pseg :deep(.seg-item) { flex: 1; }
  .suggestions .list-row { align-items: center; gap: var(--sp-3); }
  .suggestions .title { display: flex; flex-direction: column; font-size: 1.0625rem; }
  .accept { flex: none; width: 44px; height: 44px; margin-right: -10px; }
  .accept svg { width: 26px; height: 26px; }
  .gfoot { margin: calc(var(--sp-4) * -1) 16px var(--sp-4); font-size: var(--fs-sm); color: var(--ink-3); }
  .gform { display: flex; flex-direction: column; gap: var(--sp-3); }
  .grp { background: var(--surface-2); border-radius: var(--r-lg); overflow: hidden; }
  .frow { position: relative; display: flex; align-items: center; gap: var(--sp-3); min-height: 44px; padding: 0 16px; font-size: 1.0625rem; }
  .frow + .frow::before { content: ''; position: absolute; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line-2); }
  .flabel { flex: 1; min-width: 0; }
  .fin { flex: 1; min-width: 0; height: 44px; padding: 0; border: 0; background: transparent; box-shadow: none; }
  .fval { flex: none; width: auto; max-width: 60%; height: 44px; padding: 0 22px 0 8px; border: 0; background-color: transparent; box-shadow: none; color: var(--ink-3); text-align: right; text-align-last: right; background-position: right 2px center; }
  input.fval { width: 110px; padding: 0; }
  .fin:focus-visible, .fval:focus-visible { box-shadow: none; }
  .gnote { margin: 0 16px var(--sp-2); font-size: var(--fs-sm); color: var(--ink-3); }
}
/* A mouse on an iPad has no swipe, so the remove buttons come back. */
@media (max-width: 1023px) and (hover: hover) and (pointer: fine) { .rm { display: inline-flex; } }
</style>
