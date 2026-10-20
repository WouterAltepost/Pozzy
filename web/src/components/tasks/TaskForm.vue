<script setup>
import { reactive, watch } from 'vue'
import { useMediaQuery } from '../../composables/useMediaQuery'
import AreaSelect from '../shared/AreaSelect.vue'
import TagsInput from '../shared/TagsInput.vue'
import UiButton from '../ui/UiButton.vue'
import UiField from '../ui/UiField.vue'

const props = defineProps({ task: { type: Object, default: null }, busy: { type: Boolean, default: false } })
const emit = defineEmits(['save', 'cancel', 'delete'])

const form = reactive(blank())
// iOS layer: below 1024px the form reads as grouped rows; flags become switches and the text
// fields carry placeholders instead of labels.
const ios = useMediaQuery('(max-width: 1023px)')

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
    <div class="grp grp-text">
      <UiField label="Title"><input v-model="form.title" type="text" required maxlength="200" :placeholder="ios ? 'Title' : undefined" /></UiField>
      <UiField label="Description"><textarea v-model="form.description" rows="3" :placeholder="ios ? 'Notes' : undefined"></textarea></UiField>
    </div>
    <div class="grid3 grp">
      <UiField label="Area"><AreaSelect v-model="form.area_id" /></UiField>
      <UiField label="Due"><input v-model="form.due_date" type="date" /></UiField>
      <UiField label="Minutes"><input v-model.number="form.estimated_minutes" type="number" min="5" max="1440" step="5" /></UiField>
    </div>
    <div class="grid3 grp">
      <label class="check"><input v-model="form.urgent" type="checkbox" :role="ios ? 'switch' : undefined" /> Urgent</label>
      <label class="check"><input v-model="form.important" type="checkbox" :role="ios ? 'switch' : undefined" /> Important</label>
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
    <div class="grp grp-solo">
      <UiField label="Tags" hint="Comma separated"><TagsInput v-model="form.tags" placeholder="UDefine, trading" /></UiField>
    </div>
    <div class="actions">
      <UiButton type="submit" variant="primary" class="save" :loading="busy">{{ task ? 'Save' : 'Add task' }}</UiButton>
      <UiButton class="cancel" @click="emit('cancel')">Cancel</UiButton>
      <UiButton v-if="task" variant="danger" class="push del" @click="emit('delete')">Delete</UiButton>
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
/* The wrappers only exist for the phone's groups; on the desktop they leave the layout alone. */
.grp-text, .grp-solo { display: contents; }
/* iOS layer: grouped rows. Each group is a filled plate, rows are 44pt with the label on the
   left and the value on the right, hairlines start at the text. Save is the one big button;
   the sheet's close button cancels, and Delete moves to the bottom of the sheet (TasksView),
   below the slot finder, where iOS puts destructive rows. */
@media (max-width: 1023px) {
  .task-form { gap: var(--sp-5); }
  .grp, .grp-text, .grp-solo { display: flex; flex-direction: column; align-items: stretch; gap: 0; background: var(--surface-2); border-radius: var(--r-md); overflow: hidden; }
  .grp > * { position: relative; min-height: 44px; padding: 0 16px; }
  .grp > * + *::before { content: ''; position: absolute; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line-2); }
  .task-form .grp :deep(.field) { flex-direction: row; align-items: center; gap: 12px; min-height: 44px; }
  .task-form .grp :deep(.field-label) { flex: none; font-size: 1.0625rem; font-weight: 400; letter-spacing: 0; text-transform: none; color: var(--ink); }
  .task-form .grp :deep(.field-control) { flex: 1; justify-content: flex-end; }
  .task-form .grp :deep(.field-hint) { display: none; }
  .task-form .grp :deep(input:not([type='checkbox'])), .task-form .grp :deep(select), .task-form .grp :deep(textarea) { height: 44px; padding: 0; background-color: transparent; border-radius: 0; text-align: right; color: var(--ink-3); }
  .task-form .grp :deep(select) { padding-right: 20px; background-position: right 0 center; text-align-last: right; }
  .task-form .grp :deep(input:focus-visible), .task-form .grp :deep(select:focus-visible), .task-form .grp :deep(textarea:focus-visible) { box-shadow: none; }
  .task-form .grp-text :deep(.field-label) { display: none; }
  .task-form .grp-text :deep(input), .task-form .grp-text :deep(textarea) { text-align: left; color: var(--ink); }
  .task-form .grp-text :deep(textarea) { height: auto; min-height: 88px; padding: 11px 0; resize: none; }
  .check { flex-direction: row-reverse; justify-content: space-between; height: auto; min-height: 44px; font-size: 1.0625rem; }
  .actions { flex-direction: column; align-items: stretch; gap: var(--sp-3); }
  .actions .save { height: 50px; border-radius: 12px; font-size: 1.0625rem; }
  .actions .cancel { display: none; }
  .actions .del { display: none; }
}
</style>
