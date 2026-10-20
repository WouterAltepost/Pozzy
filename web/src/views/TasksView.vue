<script setup>
// Tasks as one list grouped by when they are due. Urgent and important show as chips on the
// row instead of as boxes on a board. The editor opens in a dialog. On the phone the groups are
// inset grouped plates of Reminders rows with swipe actions and a long-press menu.
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { PhCalendarPlus, PhCaretRight, PhCheck, PhCheckSquare, PhDotsThreeCircle, PhEye, PhEyeSlash, PhPlus } from '@phosphor-icons/vue'
import PullToRefresh from '../components/ios/PullToRefresh.vue'
import SlotPanel from '../components/tasks/SlotPanel.vue'
import TaskCard from '../components/tasks/TaskCard.vue'
import TaskForm from '../components/tasks/TaskForm.vue'
import TaskListItem from '../components/tasks/TaskListItem.vue'
import AreaSelect from '../components/shared/AreaSelect.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiConfirm from '../components/ui/UiConfirm.vue'
import UiEmpty from '../components/ui/UiEmpty.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import UiModal from '../components/ui/UiModal.vue'
import UiSegmented from '../components/ui/UiSegmented.vue'
import { useContextMenu } from '../composables/useContextMenu'
import { useMediaQuery } from '../composables/useMediaQuery'
import { useReady } from '../composables/useReady'
import { addDays, daysUntil, today } from '../lib/dates'
import { useAreasStore } from '../stores/areas'
import { useTasksStore } from '../stores/tasks'

const store = useTasksStore()
const areas = useAreasStore()
const route = useRoute()
const menu = useContextMenu()
const phone = useMediaQuery('(max-width: 1023px)')
const selectedId = ref(null)
const creating = ref(false)
const showSlots = ref(false)
const quickTitle = ref('')
const busy = ref(false)
const error = ref('')
const focus = ref('all') // all | urgent | important
const ready = useReady(() => store.load())

const selected = computed(() => (selectedId.value ? store.byId(selectedId.value) : null))
const editorOpen = computed(() => creating.value || Boolean(selected.value))
const FOCUS = [
  { value: 'all', label: 'All' },
  { value: 'urgent', label: 'Urgent' },
  { value: 'important', label: 'Important' },
]

const visible = computed(() => {
  const items = store.filters.include_closed ? store.items : store.open
  if (focus.value === 'urgent') return items.filter((t) => t.urgent)
  if (focus.value === 'important') return items.filter((t) => t.important)
  return items
})

// Sections by due date. Within a section: urgent and important first, then earliest due.
const SECTIONS = [
  { key: 'overdue', label: 'Overdue' },
  { key: 'today', label: 'Today' },
  { key: 'tomorrow', label: 'Tomorrow' },
  { key: 'week', label: 'Next seven days' },
  { key: 'later', label: 'Later' },
  { key: 'none', label: 'No date' },
  { key: 'done', label: 'Done' },
]
function sectionOf(t) {
  if (t.status === 'done' || t.status === 'dropped') return 'done'
  const d = daysUntil(t.due_date)
  if (d === null) return 'none'
  if (d < 0) return 'overdue'
  if (d === 0) return 'today'
  if (d === 1) return 'tomorrow'
  if (d <= 7) return 'week'
  return 'later'
}
function rank(t) {
  return (t.urgent && t.important ? 0 : t.important ? 1 : t.urgent ? 2 : 3)
}
const sections = computed(() => {
  const buckets = Object.fromEntries(SECTIONS.map((s) => [s.key, []]))
  for (const t of visible.value) buckets[sectionOf(t)].push(t)
  return SECTIONS.map((s) => ({
    ...s,
    tasks: buckets[s.key].sort((a, b) => rank(a) - rank(b) || String(a.due_date || '9').localeCompare(String(b.due_date || '9')) || a.title.localeCompare(b.title)),
  })).filter((s) => s.tasks.length)
})

async function quickAdd() {
  const title = quickTitle.value.trim()
  if (!title) return
  await run(async () => {
    const task = await store.create({ title, status: 'inbox' })
    quickTitle.value = ''
    selectedId.value = task.id
  })
}

function select(task) {
  selectedId.value = task.id
  creating.value = false
  showSlots.value = false
}

function closeEditor() {
  creating.value = false
  selectedId.value = null
  showSlots.value = false
}

async function save(body) {
  await run(async () => {
    if (creating.value) {
      await store.create(body)
      creating.value = false
    } else if (selected.value) {
      await store.update(selected.value.id, body)
      closeEditor()
    }
  })
}

// Completing a task with an estimate asks for the minutes spent first (for Hours). Cancel
// leaves the task open; an empty answer completes it without logging.
const logging = ref(null) // { task, minutes }
// The row's checkbox ticks itself before the sheet opens; a cancel re-renders the rows so the
// box reads the task's real state again.
const rev = ref(0)
function cancelLog() {
  logging.value = null
  rev.value += 1
}
async function complete(task) {
  if (task.status === 'done') return run(() => store.update(task.id, { status: 'todo' }))
  if (task.estimated_minutes) {
    logging.value = { task, minutes: task.estimated_minutes }
    return
  }
  await finish(task)
}
async function finish(task, minutes) {
  await run(async () => {
    await store.complete(task.id, minutes)
    if (selectedId.value === task.id) selectedId.value = null
  })
}
async function confirmLog() {
  const { task, minutes } = logging.value
  logging.value = null
  await finish(task, Number(minutes) || undefined)
}

const removing = ref(null) // the task waiting for the delete confirmation
function removeSelected() {
  if (selected.value) removing.value = selected.value
}
async function confirmRemove() {
  const task = removing.value
  await run(async () => {
    await store.remove(task.id)
    if (selectedId.value === task.id) selectedId.value = null
  })
  removing.value = null
}

function openSlots(task) {
  select(task)
  showSlots.value = true
}

function newTask() {
  creating.value = true
  selectedId.value = null
}

// The nav bar's filter menu on the phone: what the desktop toolbar holds as controls.
function filterMenu(evt) {
  areas.load()
  const pickArea = (id) => () => {
    store.filters.area_id = id
    store.load()
  }
  menu.open(evt.currentTarget, [
    {
      label: store.filters.include_closed ? 'Hide completed' : 'Show completed',
      icon: store.filters.include_closed ? PhEyeSlash : PhEye,
      action: () => {
        store.filters.include_closed = !store.filters.include_closed
        store.load()
      },
    },
    { label: 'All areas', icon: store.filters.area_id ? null : PhCheck, action: pickArea(null) },
    ...areas.items.map((a) => ({ label: a.name, icon: store.filters.area_id === a.id ? PhCheck : null, action: pickArea(a.id) })),
  ], 'Filter')
}

async function run(fn) {
  busy.value = true
  error.value = ''
  try {
    await fn()
  } catch (err) {
    error.value = err.message
  } finally {
    busy.value = false
  }
}

function dueLabel(key) {
  if (key === 'today') return today()
  if (key === 'tomorrow') return addDays(today(), 1)
  return ''
}
</script>

<template>
  <PullToRefresh :action="() => store.load()">
  <div class="tasks">
    <Teleport v-if="phone && route.name === 'tasks'" defer to="#nav-trailing">
      <button type="button" class="icon-btn" aria-label="Filter tasks" @click="filterMenu"><PhDotsThreeCircle weight="regular" /></button>
      <button type="button" class="icon-btn" aria-label="New task" @click="newTask"><PhPlus weight="regular" /></button>
    </Teleport>
    <PageHeader title="Tasks">
      <template #meta><span class="num">{{ store.open.length }} open</span></template>
      <form class="quick" @submit.prevent="quickAdd">
        <input v-model="quickTitle" type="text" placeholder="Quick add to inbox" aria-label="Quick add to inbox" />
        <UiButton type="submit" :disabled="busy || !quickTitle.trim()">Add</UiButton>
      </form>
      <UiSegmented v-model="focus" :options="FOCUS" />
      <AreaSelect v-model="store.filters.area_id" aria-label="Area" @update:model-value="store.load()" />
      <input v-model="store.filters.q" type="search" placeholder="Search" aria-label="Search tasks" class="search" @change="store.load()" />
      <label class="check"><input v-model="store.filters.include_closed" type="checkbox" @change="store.load()" /> Show done</label>
      <UiButton variant="primary" class="new-btn" @click="newTask">New task</UiButton>
    </PageHeader>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="store.error" class="error">{{ store.error }}</p>

    <UiLoadGate :ready="ready" label="Loading tasks">
      <div v-if="!sections.length" class="card">
        <UiEmpty title="No tasks" :hint="phone ? 'Tap + to add one, or capture it with the lightning.' : 'Quick add one above, or press Cmd or Ctrl plus K to capture it.'">
          <template #icon><PhCheckSquare /></template>
        </UiEmpty>
      </div>
      <section v-for="s in sections" :key="s.key" class="section" :class="s.key">
        <header class="section-head">
          <h2>{{ s.label }}</h2>
          <span class="muted small num count">{{ s.tasks.length }}<span class="count-word">&nbsp;{{ s.tasks.length === 1 ? 'task' : 'tasks' }}</span></span>
          <span v-if="dueLabel(s.key)" class="muted small num daylabel">{{ dueLabel(s.key) }}</span>
        </header>
        <div class="list">
          <template v-if="phone">
            <TaskListItem v-for="t in s.tasks" :key="t.id + ':' + rev" :task="t" :selected="t.id === selectedId" @select="select" @complete="complete" @remove="removing = $event" @slots="openSlots" />
          </template>
          <template v-else>
            <TaskCard v-for="t in s.tasks" :key="t.id + ':' + rev" :task="t" :selected="t.id === selectedId" :draggable="false" @select="select" @complete="complete" />
          </template>
        </div>
      </section>
    </UiLoadGate>

    <UiModal :open="editorOpen" :title="creating ? 'New task' : 'Edit task'" size="md" @close="closeEditor">
      <TaskForm :task="creating ? null : selected" :busy="busy" @save="save" @cancel="closeEditor" @delete="removeSelected" />
      <div v-if="selected" class="side-actions">
        <UiButton class="slots-btn" @click="showSlots = !showSlots">{{ showSlots ? 'Hide slots' : 'Suggest a slot' }}</UiButton>
        <button type="button" class="slots-row" :aria-expanded="showSlots" @click="showSlots = !showSlots">
          <PhCalendarPlus class="ic" aria-hidden="true" /><span class="lbl">{{ showSlots ? 'Hide slots' : 'Suggest a slot' }}</span><PhCaretRight class="chev" :class="{ open: showSlots }" aria-hidden="true" />
        </button>
        <span v-if="selected.source !== 'manual'" class="muted small">source: {{ selected.source }}</span>
      </div>
      <SlotPanel v-if="selected && showSlots" :task="selected" @scheduled="showSlots = false" @close="showSlots = false" />
      <button v-if="selected" type="button" class="delete-row" @click="removeSelected">Delete task</button>
    </UiModal>

    <UiModal :open="Boolean(logging)" title="Log time" size="sm" @close="cancelLog">
      <form v-if="logging" class="log" @submit.prevent="confirmLog">
        <p class="log-msg">Minutes spent on "{{ logging.task.title }}". Leave empty to complete without logging.</p>
        <input v-model="logging.minutes" type="number" inputmode="numeric" min="0" max="1440" step="5" aria-label="Minutes spent" />
        <div class="log-actions">
          <UiButton class="log-cancel" @click="cancelLog">Cancel</UiButton>
          <UiButton type="submit" variant="primary" :loading="busy">Complete</UiButton>
        </div>
      </form>
    </UiModal>

    <UiConfirm :open="Boolean(removing)" title="Delete this task?" :message="removing ? removing.title : ''" confirm-label="Delete task" danger :busy="busy" @confirm="confirmRemove" @cancel="removing = null" />
  </div>
  </PullToRefresh>
</template>

<style scoped>
.quick { display: flex; gap: var(--sp-2); flex: 0 1 240px; min-width: 180px; }
.quick input { flex: 1; }
.search { width: 130px; }
.check { display: flex; align-items: center; gap: 6px; font-size: var(--fs-md); white-space: nowrap; }
.section { margin-bottom: var(--sp-5); }
.section-head { display: flex; align-items: baseline; gap: var(--sp-2); margin-bottom: var(--sp-2); }
.section-head h2 { font-size: var(--fs-md); font-weight: 600; letter-spacing: 0.01em; color: var(--ink-2); text-transform: uppercase; }
.section.overdue .section-head h2 { color: var(--danger); }
.section.today .section-head h2 { color: var(--ink); }
.list { display: flex; flex-direction: column; gap: var(--sp-2); }
.side-actions { display: flex; gap: var(--sp-2); align-items: center; margin-top: var(--sp-4); }
.count-word { display: none; }
/* The phone rows for the slot finder and the log-time sheet only exist in the iOS layer. */
.slots-row, .delete-row { display: none; }
.log { display: flex; flex-direction: column; gap: var(--sp-3); }
.log-msg { color: var(--ink-2); }
.log-actions { display: flex; justify-content: flex-end; gap: var(--sp-2); margin-top: var(--sp-2); }
/* iOS layer: large title with the count under it, a search field, the segmented control full
   width; New task, area and Show done live in the nav bar. Each group is an inset grouped plate
   with its title inside, rows separated by hairlines that start at the text. */
@media (max-width: 1023px) {
  .tasks :deep(.page-header) { gap: var(--sp-3); margin-bottom: var(--sp-4); }
  .tasks :deep(.page-header .title-row) { flex-direction: column; align-items: flex-start; gap: 0; }
  .tasks :deep(.page-header .meta) { font-size: 0.9375rem; }
  .tasks :deep(.page-header .toolbar) { flex-direction: column; align-items: stretch; gap: var(--sp-3); }
  .quick, .check, .new-btn, .tasks :deep(.toolbar > select) { display: none; }
  .search { display: block; order: -1; width: 100%; height: 36px; padding: 0 10px 0 32px; font-size: 1.0625rem; background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 256 256' fill='none' stroke='%238E8E93' stroke-width='22' stroke-linecap='round'><circle cx='112' cy='112' r='72'/><path d='m164 164 52 52'/></svg>"); background-repeat: no-repeat; background-position: 9px center; background-size: 16px; }
  .search::-webkit-search-decoration { -webkit-appearance: none; }
  .tasks :deep(.seg) { display: flex; width: 100%; }
  .tasks :deep(.seg-item) { flex: 1; }
  .section { background: var(--surface); border-radius: var(--r-lg); overflow: hidden; margin-bottom: var(--sp-5); }
  .section-head { justify-content: space-between; align-items: baseline; margin: 0; padding: 12px 16px 2px; }
  .section-head h2 { font-size: 1.0625rem; font-weight: 600; text-transform: none; letter-spacing: normal; color: var(--ink); }
  .section.overdue .section-head h2 { color: var(--danger); }
  .section.week .section-head h2, .section.later .section-head h2 { color: var(--ink); }
  .section.none .section-head h2 { color: var(--ink-3); }
  .section.done .section-head h2 { color: var(--ok); }
  .section-head .count { font-size: 0.9375rem; }
  .daylabel { display: none; }
  .list { gap: 0; }
  .list > * + * :deep(.task-card)::before { content: ''; position: absolute; top: 0; left: 50px; right: 0; height: 0.5px; background: var(--line-2); }
  /* The slot finder as one tappable grouped row, like a Settings link. */
  .side-actions { flex-direction: column; align-items: stretch; gap: var(--sp-2); }
  .slots-btn { display: none; }
  .slots-row { display: flex; align-items: center; gap: 12px; width: 100%; min-height: 44px; padding: 0 16px; border: 0; border-radius: var(--r-md); background: var(--surface-2); color: var(--ink); font: inherit; font-size: 1.0625rem; text-align: left; }
  .slots-row:active { background: var(--surface-3); }
  .slots-row .ic { width: 22px; height: 22px; color: var(--brand); flex: none; }
  .slots-row .lbl { flex: 1; }
  .slots-row .chev { width: 14px; height: 14px; color: var(--ink-4); transition: transform 200ms ease; }
  .slots-row .chev.open { transform: rotate(90deg); }
  .side-actions .muted { padding: 0 16px; }
  .delete-row { display: block; width: 100%; min-height: 44px; margin-top: var(--sp-5); border: 0; border-radius: var(--r-md); background: var(--surface-2); color: var(--danger); font: inherit; font-size: 1.0625rem; }
  .delete-row:active { background: var(--surface-3); }
  .log input { width: 100%; height: 44px; }
  .log-msg { font-size: 0.9375rem; color: var(--ink-3); }
  .log-actions { flex-direction: column-reverse; align-items: stretch; }
  .log-actions :deep(.btn) { height: 50px; border-radius: 12px; font-size: 1.0625rem; }
  .log-cancel { display: none; }
}
</style>
