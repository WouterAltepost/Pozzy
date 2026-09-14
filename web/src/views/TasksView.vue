<script setup>
import { computed, onMounted, ref } from 'vue'
import SlotPanel from '../components/tasks/SlotPanel.vue'
import TaskCard from '../components/tasks/TaskCard.vue'
import TaskForm from '../components/tasks/TaskForm.vue'
import AreaSelect from '../components/shared/AreaSelect.vue'
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

const selected = computed(() => (selectedId.value ? store.byId(selectedId.value) : null))
const listItems = computed(() => (store.filters.include_closed ? store.items : store.open))

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
    <div class="toolbar">
      <h1>Tasks</h1>
      <form class="quick" @submit.prevent="quickAdd">
        <input v-model="quickTitle" type="text" placeholder="Quick add to inbox..." />
        <button type="submit" :disabled="busy || !quickTitle.trim()">Add</button>
      </form>
      <div class="controls">
        <button type="button" :class="{ active: mode === 'board' }" @click="mode = 'board'">Board</button>
        <button type="button" :class="{ active: mode === 'list' }" @click="mode = 'list'">List</button>
        <AreaSelect v-model="store.filters.area_id" @update:model-value="store.load()" />
        <input v-model="store.filters.q" type="search" placeholder="Search" @change="store.load()" />
        <label class="check"><input v-model="store.filters.include_closed" type="checkbox" @change="store.load()" /> show done</label>
        <button type="button" @click="creating = true; selectedId = null">New task</button>
      </div>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="store.error" class="error">{{ store.error }}</p>

    <div class="layout">
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
              <strong>{{ q.label }}</strong>
              <span class="muted">{{ q.hint }}</span>
            </header>
            <p v-if="!store.byQuadrant(q.key).length" class="muted empty">Drop tasks here</p>
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
          <p v-if="store.loading" class="muted">Loading...</p>
          <p v-else-if="!listItems.length" class="muted">No tasks.</p>
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

      <aside v-if="creating || selected" class="side card">
        <h2>{{ creating ? 'New task' : 'Edit task' }}</h2>
        <TaskForm :task="creating ? null : selected" :busy="busy" @save="save" @cancel="creating = false; selectedId = null" @delete="removeSelected" />
        <div v-if="selected" class="side-actions">
          <button type="button" @click="showSlots = !showSlots">{{ showSlots ? 'Hide slots' : 'Suggest a slot' }}</button>
          <span v-if="selected.source !== 'manual'" class="muted">source: {{ selected.source }}</span>
        </div>
        <SlotPanel v-if="selected && showSlots" :task="selected" @scheduled="showSlots = false" @close="showSlots = false" />
      </aside>
    </div>
  </div>
</template>

<style scoped>
.tasks h1 { font-size: 1.3rem; margin: 0; }
.toolbar { display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center; margin-bottom: 1rem; }
.quick { display: flex; gap: 0.4rem; flex: 1; min-width: 240px; }
.quick input { flex: 1; font: inherit; padding: 0.4rem; border: 1px solid #d1d5db; border-radius: 4px; }
.controls { display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: center; font-size: 0.85rem; }
.controls input[type='search'], .controls select { font: inherit; padding: 0.35rem; border: 1px solid #d1d5db; border-radius: 4px; }
.controls button.active { background: #111827; color: #fff; border-color: #111827; }
.check { display: flex; align-items: center; gap: 0.3rem; }
.layout { display: grid; grid-template-columns: 1fr; gap: 1rem; }
@media (min-width: 900px) { .layout { grid-template-columns: 1fr 360px; } }
.board { display: grid; grid-template-columns: 1fr; gap: 0.75rem; }
@media (min-width: 640px) { .board { grid-template-columns: 1fr 1fr; } }
.quadrant { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 0.6rem; min-height: 160px; display: flex; flex-direction: column; gap: 0.4rem; }
.quadrant.over { border-color: #2563eb; background: #eff6ff; }
.quadrant header { display: flex; justify-content: space-between; align-items: baseline; gap: 0.5rem; margin-bottom: 0.2rem; }
.quadrant.do { border-top: 3px solid #dc2626; }
.quadrant.schedule { border-top: 3px solid #2563eb; }
.quadrant.delegate { border-top: 3px solid #d97706; }
.quadrant.eliminate { border-top: 3px solid #9ca3af; }
.empty { text-align: center; padding: 1rem 0; }
.list { display: flex; flex-direction: column; gap: 0.4rem; }
.side { align-self: start; position: sticky; top: 1rem; }
.side h2 { margin-top: 0; }
.side-actions { display: flex; gap: 0.5rem; align-items: center; margin-top: 0.75rem; }
</style>
