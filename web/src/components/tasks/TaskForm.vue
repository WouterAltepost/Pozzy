<script setup>
import { reactive, watch } from 'vue'
import AreaSelect from '../shared/AreaSelect.vue'
import TagsInput from '../shared/TagsInput.vue'
import UiButton from '../ui/UiButton.vue'
import UiField from '../ui/UiField.vue'

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
    <UiField label="Title"><input v-model="form.title" type="text" required maxlength="200" /></UiField>
    <UiField label="Description"><textarea v-model="form.description" rows="3"></textarea></UiField>
    <div class="grid3">
      <UiField label="Area"><AreaSelect v-model="form.area_id" /></UiField>
      <UiField label="Due"><input v-model="form.due_date" type="date" /></UiField>
      <UiField label="Minutes"><input v-model.number="form.estimated_minutes" type="number" min="5" max="1440" step="5" /></UiField>
    </div>
    <div class="grid3">
      <label class="check"><input v-model="form.urgent" type="checkbox" /> Urgent</label>
      <label class="check"><input v-model="form.important" type="checkbox" /> Important</label>
      <UiField label="Status">
        <select v-model="form.status">
          <option value="inbox">inbox</option>
          <option value="todo">todo</option>
          <option value="scheduled">scheduled</option>
          <option value="done">done</option>
          <option value="dropped">dropped</option>
        </select>
      </UiField>
    </div>
    <UiField label="Tags" hint="Comma separated"><TagsInput v-model="form.tags" placeholder="UDefine, trading" /></UiField>
    <div class="actions">
      <UiButton type="submit" variant="primary" :loading="busy">{{ task ? 'Save' : 'Add task' }}</UiButton>
      <UiButton @click="emit('cancel')">Cancel</UiButton>
      <UiButton v-if="task" variant="danger" class="push" @click="emit('delete')">Delete</UiButton>
    </div>
  </form>
</template>

<style scoped>
.task-form { display: flex; flex-direction: column; gap: var(--sp-3); }
.grid3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--sp-3); align-items: end; }
@media (max-width: 720px) { .grid3 { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.check { display: flex; align-items: center; gap: 8px; height: var(--control-h); font-size: var(--fs-base); }
.actions { display: flex; gap: var(--sp-2); align-items: center; }
.push { margin-left: auto; }
</style>
