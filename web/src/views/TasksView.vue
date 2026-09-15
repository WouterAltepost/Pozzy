<script setup>
import { computed, onMounted, ref } from 'vue'
import { PhCheckSquare } from '@phosphor-icons/vue'
import SlotPanel from '../components/tasks/SlotPanel.vue'
import TaskCard from '../components/tasks/TaskCard.vue'
import TaskForm from '../components/tasks/TaskForm.vue'
import AreaSelect from '../components/shared/AreaSelect.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiEmpty from '../components/ui/UiEmpty.vue'
import UiSegmented from '../components/ui/UiSegmented.vue'
import UiSheet from '../components/ui/UiSheet.vue'
import UiSkeleton from '../components/ui/UiSkeleton.vue'
import { useMediaQuery } from '../composables/useMediaQuery'
import { QUADRANTS, useTasksStore } from '../stores/tasks'

const store = useTasksStore()
const mode = ref('board') // board | list
const selectedId = ref(null)
const creating = ref(false)
const showSlots = ref(false)
const quickTitle = ref('')
const busy = ref(false)
const error = ref('')
const dragOver = ref(null)
const narrow = useMediaQuery('(max-width: 899px)')

const selected = computed(() => (selectedId.value ? store.byId(selectedId.value) : null))
const listItems = computed(() => (store.filters.include_closed ? store.items : store.open))
const panelOpen = computed(() => creating.value || Boolean(selected.value))
const MODES = [
  { value: 'board', label: 'Board' },
  { value: 'list', label: 'List' },
]

onMounted(() => store.load())

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

function closePanel() {
  creating.value = false
  selectedId.value = null
  showSlots.value = false
}

async function save(body) {
  await run(async () => {
    if (creating.value) {
      const task = await store.create(body)
      selectedId.value = task.id
      creating.value = false
    } else if (selected.value) {
      await store.update(selected.value.id, body)
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

function onDragStart(task, event) {
  event.dataTransfer.setData('text/plain', task.id)
  event.dataTransfer.effectAllowed = 'move'
}

async function onDrop(quadrant, event) {
  const id = event.dataTransfer.getData('text/plain')
  dragOver.value = null
  if (!id) return
  await run(() => store.move(id, quadrant))
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
</script>

<template>
  <div class="tasks">
    <PageHeader title="Tasks">
      <template #meta><span class="num">{{ store.open.length }} open</span></template>
      <form class="quick" @submit.prevent="quickAdd">
        <input v-model="quickTitle" type="text" placeholder="Quick add to inbox" aria-label="Quick add to inbox" />
        <UiButton type="submit" :disabled="busy || !quickTitle.trim()">Add</UiButton>
      </form>
      <UiSegmented v-model="mode" :options="MODES" />
      <AreaSelect v-model="store.filters.area_id" aria-label="Area" @update:model-value="store.load()" />
      <input v-model="store.filters.q" type="search" placeholder="Search" aria-label="Search tasks" class="search" @change="store.load()" />
      <label class="check"><input v-model="store.filters.include_closed" type="checkbox" @change="store.load()" /> Show done</label>
      <UiButton variant="primary" @click="creating = true; selectedId = null">New task</UiButton>
    </PageHeader>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="store.error" class="error">{{ store.error }}</p>

    <div class="layout" :class="{ split: panelOpen && !narrow }">
      <div class="main">
        <div v-if="mode === 'board'" class="board">
          <section
            v-for="q in QUADRANTS"
            :key="q.key"
            class="quadrant"
            :class="[q.key, { over: dragOver === q.key }]"
            @dragover.prevent="dragOver = q.key"
            @dragleave="dragOver = null"
            @drop.prevent="onDrop(q.key, $event)"
          >
            <header>
              <h2>{{ q.label }}</h2>
              <span class="muted small">{{ q.hint }}</span>
            </header>
            <p v-if="!store.byQuadrant(q.key).length" class="muted small empty">Drop tasks here</p>
            <TaskCard
              v-for="t in store.byQuadrant(q.key)"
              :key="t.id"
              :task="t"
              :selected="t.id === selectedId"
              @select="select"
              @complete="complete"
              @dragstart="onDragStart"
            />
          </section>
        </div>

        <div v-else class="list">
          <UiSkeleton v-if="store.loading" :lines="4" />
          <UiEmpty v-else-if="!listItems.length" title="No tasks" hint="Quick add one above, or capture it from the top bar.">
            <template #icon><PhCheckSquare /></template>
          </UiEmpty>
          <TaskCard
            v-for="t in listItems"
            :key="t.id"
            :task="t"
            :selected="t.id === selectedId"
            :draggable="false"
            @select="select"
            @complete="complete"
          />
        </div>
      </div>

      <Transition name="panel">
        <aside v-if="panelOpen && !narrow" class="side card">
          <div class="card-head">
            <h2>{{ creating ? 'New task' : 'Edit task' }}</h2>
            <span class="meta"><button type="button" class="link-btn" @click="closePanel">Close</button></span>
          </div>
          <TaskForm :task="creating ? null : selected" :busy="busy" @save="save" @cancel="closePanel" @delete="removeSelected" />
          <div v-if="selected" class="side-actions">
            <UiButton @click="showSlots = !showSlots">{{ showSlots ? 'Hide slots' : 'Suggest a slot' }}</UiButton>
            <span v-if="selected.source !== 'manual'" class="muted small">source: {{ selected.source }}</span>
          </div>
          <SlotPanel v-if="selected && showSlots" :task="selected" @scheduled="showSlots = false" @close="showSlots = false" />
        </aside>
      </Transition>
    </div>

    <UiSheet :open="panelOpen && narrow" :title="creating ? 'New task' : 'Edit task'" @close="closePanel">
      <TaskForm :task="creating ? null : selected" :busy="busy" @save="save" @cancel="closePanel" @delete="removeSelected" />
      <div v-if="selected" class="side-actions">
        <UiButton @click="showSlots = !showSlots">{{ showSlots ? 'Hide slots' : 'Suggest a slot' }}</UiButton>
        <span v-if="selected.source !== 'manual'" class="muted small">source: {{ selected.source }}</span>
      </div>
      <SlotPanel v-if="selected && showSlots" :task="selected" @scheduled="showSlots = false" @close="showSlots = false" />
    </UiSheet>
  </div>
</template>

<style scoped>
.quick { display: flex; gap: var(--sp-2); flex: 1 1 260px; min-width: 200px; }
.quick input { flex: 1; }
.search { width: 150px; }
.check { display: flex; align-items: center; gap: 6px; font-size: var(--fs-md); white-space: nowrap; }
.layout { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--sp-5); align-items: start; }
@media (min-width: 900px) { .layout.split { grid-template-columns: minmax(0, 1fr) 360px; } }
.board { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--sp-3); }
@media (min-width: 640px) { .board { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); } }
.quadrant {
  --q: var(--ink-3);
  position: relative;
  background: var(--surface-2);
  border: 1px solid transparent;
  border-top: 2px solid var(--q);
  border-radius: var(--r-lg);
  padding: var(--sp-3);
  min-height: 180px;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  transition: background-color var(--dur-hover) ease, border-color var(--dur-hover) ease;
}
.quadrant.do { --q: var(--danger); }
.quadrant.schedule { --q: var(--info); }
.quadrant.delegate { --q: var(--warn); }
.quadrant.eliminate { --q: var(--ink-3); }
.quadrant.over { background: var(--surface-3); border-color: var(--ink); }
.quadrant header { display: flex; justify-content: space-between; align-items: baseline; gap: var(--sp-2); margin-bottom: 2px; }
.quadrant h2 { font-size: var(--fs-base); }
.empty { text-align: center; padding: var(--sp-4) 0; margin: auto 0; }
.list { display: flex; flex-direction: column; gap: var(--sp-2); }
.side { align-self: start; position: sticky; top: calc(var(--bar-h) + var(--sp-4)); margin: 0; }
.side-actions { display: flex; gap: var(--sp-2); align-items: center; margin-top: var(--sp-4); }
.panel-enter-active { transition: opacity var(--dur-panel) var(--ease-out), transform var(--dur-panel) var(--ease-out); }
.panel-leave-active { transition: opacity var(--dur-hover) ease; }
.panel-enter-from { opacity: 0; transform: translateX(8px); }
.panel-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) { .panel-enter-from { transform: none; } }
</style>
