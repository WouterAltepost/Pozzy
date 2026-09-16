<script setup>
// Tasks as one list grouped by when they are due. Urgent and important show as chips on the
// row instead of as boxes on a board. The editor opens in a dialog.
import { computed, ref } from 'vue'
import { PhCheckSquare } from '@phosphor-icons/vue'
import SlotPanel from '../components/tasks/SlotPanel.vue'
import TaskCard from '../components/tasks/TaskCard.vue'
import TaskForm from '../components/tasks/TaskForm.vue'
import AreaSelect from '../components/shared/AreaSelect.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiEmpty from '../components/ui/UiEmpty.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import UiModal from '../components/ui/UiModal.vue'
import UiSegmented from '../components/ui/UiSegmented.vue'
import { useReady } from '../composables/useReady'
import { addDays, daysUntil, today } from '../lib/dates'
import { useTasksStore } from '../stores/tasks'

const store = useTasksStore()
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

async function complete(task) {
  await run(async () => {
    if (task.status === 'done') await store.update(task.id, { status: 'todo' })
    else {
      let minutes
      if (task.estimated_minutes) {
        const answer = window.prompt(`Log hours for "${task.title}"? Minutes spent:`, task.estimated_minutes)
        if (answer === null) return
        minutes = Number(answer) || undefined
      }
      await store.complete(task.id, minutes)
      if (selectedId.value === task.id) selectedId.value = null
    }
  })
}

async function removeSelected() {
  if (!selected.value || !window.confirm('Delete this task?')) return
  await run(async () => {
    await store.remove(selected.value.id)
    selectedId.value = null
  })
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
  <div class="tasks">
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
      <UiButton variant="primary" @click="creating = true; selectedId = null">New task</UiButton>
    </PageHeader>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="store.error" class="error">{{ store.error }}</p>

    <UiLoadGate :ready="ready" label="Loading tasks">
      <div v-if="!sections.length" class="card">
        <UiEmpty title="No tasks" hint="Quick add one above, or press Cmd or Ctrl plus K to capture it.">
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
          <TaskCard v-for="t in s.tasks" :key="t.id" :task="t" :selected="t.id === selectedId" :draggable="false" @select="select" @complete="complete" />
        </div>
      </section>
    </UiLoadGate>

    <UiModal :open="editorOpen" :title="creating ? 'New task' : 'Edit task'" size="md" @close="closeEditor">
      <TaskForm :task="creating ? null : selected" :busy="busy" @save="save" @cancel="closeEditor" @delete="removeSelected" />
      <div v-if="selected" class="side-actions">
        <UiButton @click="showSlots = !showSlots">{{ showSlots ? 'Hide slots' : 'Suggest a slot' }}</UiButton>
        <span v-if="selected.source !== 'manual'" class="muted small">source: {{ selected.source }}</span>
      </div>
      <SlotPanel v-if="selected && showSlots" :task="selected" @scheduled="showSlots = false" @close="showSlots = false" />
    </UiModal>
  </div>
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
/* Phone (design: Pozzy Phone, Tasks): each group is a card, rows are hairline-separated. */
@media (max-width: 699px) {
  .quick, .search { display: none; }
  .section { background: var(--surface); border: 1px solid var(--line); border-radius: var(--r-lg); box-shadow: var(--shadow-1); padding: 12px 16px 4px; margin-bottom: var(--sp-4); }
  .section-head { margin-bottom: 2px; justify-content: space-between; }
  .section-head h2 { font-size: var(--fs-md); text-transform: none; letter-spacing: 0.01em; color: var(--ink-2); }
  .section.overdue .section-head h2 { color: var(--danger); }
  .section.today .section-head h2, .section.tomorrow .section-head h2 { color: var(--ink); }
  .section.none .section-head h2 { color: var(--ink-3); }
  .section.done .section-head h2 { color: var(--ok); }
  .count-word { display: inline; }
  .daylabel { display: none; }
  .list { gap: 0; }
}
</style>
