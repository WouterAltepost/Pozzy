<script setup>
import { reactive, watch } from 'vue'
import AreaSelect from '../shared/AreaSelect.vue'
import TagsInput from '../shared/TagsInput.vue'

const props = defineProps({ task: { type: Object, default: null }, busy: { type: Boolean, default: false } })
const emit = defineEmits(['save', 'cancel', 'delete'])

const form = reactive(blank())

function blank() {
  return { title: '', description: '', area_id: null, tags: [], urgent: false, important: false, status: 'todo', due_date: '', estimated_minutes: null }
}

watch(
  () => props.task,
  (t) => {
    Object.assign(form, blank(), t ? {
      title: t.title,
      description: t.description || '',
      area_id: t.area_id,
      tags: [...(t.tags || [])],
      urgent: t.urgent,
      important: t.important,
      status: t.status,
      due_date: t.due_date || '',
      estimated_minutes: t.estimated_minutes,
    } : {})
  },
  { immediate: true },
)

function submit() {
  const body = {
    title: form.title,
    description: form.description || null,
    area_id: form.area_id || null,
    tags: form.tags,
    urgent: form.urgent,
    important: form.important,
    status: form.status,
    due_date: form.due_date || null,
    estimated_minutes: form.estimated_minutes ? Number(form.estimated_minutes) : null,
  }
  emit('save', body)
}
</script>

<template>
  <form class="task-form" @submit.prevent="submit">
    <input v-model="form.title" type="text" placeholder="Title" required maxlength="200" />
    <textarea v-model="form.description" rows="3" placeholder="Description (optional)"></textarea>
    <div class="row">
      <label>Area <AreaSelect v-model="form.area_id" /></label>
      <label>Due <input v-model="form.due_date" type="date" /></label>
      <label>Minutes <input v-model.number="form.estimated_minutes" type="number" min="1" max="1440" step="5" /></label>
    </div>
    <div class="row">
      <label class="check"><input v-model="form.urgent" type="checkbox" /> Urgent</label>
      <label class="check"><input v-model="form.important" type="checkbox" /> Important</label>
      <label>Status
        <select v-model="form.status">
          <option value="inbox">inbox</option>
          <option value="todo">todo</option>
          <option value="scheduled">scheduled</option>
          <option value="done">done</option>
          <option value="dropped">dropped</option>
        </select>
      </label>
    </div>
    <TagsInput v-model="form.tags" />
    <div class="actions">
      <button type="submit" :disabled="busy">{{ task ? 'Save' : 'Add task' }}</button>
      <button type="button" @click="emit('cancel')">Cancel</button>
      <button v-if="task" type="button" class="danger" @click="emit('delete')">Delete</button>
    </div>
  </form>
</template>

<style scoped>
.task-form { display: flex; flex-direction: column; gap: 0.5rem; }
.task-form input[type='text'], .task-form textarea, .task-form select, .task-form input[type='date'], .task-form input[type='number'] {
  font: inherit; padding: 0.4rem; border: 1px solid #d1d5db; border-radius: 4px; width: 100%;
}
.row { display: flex; gap: 0.75rem; flex-wrap: wrap; }
.row label { display: flex; flex-direction: column; gap: 0.2rem; font-size: 0.85rem; color: #4b5563; flex: 1; min-width: 120px; }
.row label.check { flex-direction: row; align-items: center; gap: 0.4rem; flex: 0; white-space: nowrap; }
.actions { display: flex; gap: 0.5rem; }
.danger { color: #b91c1c; margin-left: auto; }
</style>
