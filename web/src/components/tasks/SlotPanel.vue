<script setup>
import { ref } from 'vue'
import { formatDateTime } from '../../lib/dates'
import { useTasksStore } from '../../stores/tasks'
import UiButton from '../ui/UiButton.vue'
import UiField from '../ui/UiField.vue'
import UiSkeleton from '../ui/UiSkeleton.vue'

const props = defineProps({ task: { type: Object, required: true } })
const emit = defineEmits(['scheduled', 'close'])
const store = useTasksStore()

const result = ref(null)
const loading = ref(false)
const error = ref('')
const manualStart = ref('')
const manualEnd = ref('')

async function fetchSlots() {
  loading.value = true
  error.value = ''
  try {
    result.value = await store.suggestSlot(props.task.id, {})
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function accept(slot) {
  error.value = ''
  try {
    await store.schedule(props.task.id, { start: slot.start, end: slot.end })
    emit('scheduled')
  } catch (err) {
    error.value = err.message
  }
}

async function acceptManual() {
  if (!manualStart.value) return
  const body = { start: new Date(manualStart.value).toISOString() }
  if (manualEnd.value) body.end = new Date(manualEnd.value).toISOString()
  try {
    await store.schedule(props.task.id, body)
    emit('scheduled')
  } catch (err) {
    error.value = err.message
  }
}

async function unschedule() {
  await store.unschedule(props.task.id)
  emit('scheduled')
}

fetchSlots()
</script>

<template>
  <div class="slot-panel">
    <div class="head">
      <h3>Suggest a slot</h3>
      <button type="button" class="link-btn" @click="emit('close')">Close</button>
    </div>
    <p v-if="task.scheduled_start" class="muted small">
      Scheduled {{ formatDateTime(task.scheduled_start) }} to {{ formatDateTime(task.scheduled_end) }}.
      <button type="button" class="link-btn" @click="unschedule">Unschedule</button>
    </p>
    <UiSkeleton v-if="loading" :lines="3" />
    <p v-else-if="error" class="error">{{ error }}</p>
    <template v-else-if="result">
      <p class="muted small num">{{ result.duration_minutes }} min, {{ result.candidates_considered }} free candidates, ranked by {{ result.ranked_by }}.</p>
      <p v-if="!result.slots.length" class="muted small">No free slot in the next working days. Pick a time manually below.</p>
      <ul class="slots">
        <li v-for="s in result.slots" :key="s.start" class="inset slot">
          <div class="slot-text">
            <span class="when num"><strong>{{ s.day_label }}</strong> {{ formatDateTime(s.start).split(', ').pop() }} to {{ formatDateTime(s.end).split(', ').pop() }}</span>
            <span class="muted small">{{ s.reason }}</span>
          </div>
          <UiButton size="sm" variant="primary" @click="accept(s)">Accept</UiButton>
        </li>
      </ul>
    </template>
    <div class="manual">
      <div class="manual-rows">
        <UiField label="Start"><input v-model="manualStart" type="datetime-local" /></UiField>
        <UiField label="End"><input v-model="manualEnd" type="datetime-local" /></UiField>
      </div>
      <UiButton :disabled="!manualStart" class="manual-btn" @click="acceptManual">Schedule manually</UiButton>
    </div>
  </div>
</template>

<style scoped>
.slot-panel { border-top: 1px solid var(--line); margin-top: var(--sp-4); padding-top: var(--sp-4); display: flex; flex-direction: column; gap: var(--sp-3); }
.head { display: flex; justify-content: space-between; align-items: center; }
.slots { display: flex; flex-direction: column; gap: var(--sp-2); }
.slot { display: flex; justify-content: space-between; align-items: center; gap: var(--sp-3); }
.slot-text { display: flex; flex-direction: column; gap: 2px; min-width: 0; font-size: var(--fs-md); }
.manual { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-2); align-items: end; }
.manual > :last-child { grid-column: 1 / -1; }
/* Only the phone groups Start and End; on the desktop they stay two grid cells. */
.manual-rows { display: contents; }
/* iOS layer: the row that opened the panel is its header, so the panel's own goes; the suggestions are one grouped list
   with Accept on the right of each row, and the manual times are two rows of their own. */
@media (max-width: 1023px) {
  .slot-panel { border-top: 0; margin-top: var(--sp-2); padding-top: 0; gap: var(--sp-2); }
  .head { display: none; }
  .slot-panel > .muted, .slot-panel > .error { padding: 0 16px; font-size: 0.8125rem; }
  .slots { gap: 0; background: var(--surface-2); border-radius: var(--r-md); overflow: hidden; }
  .slots:empty { display: none; }
  .slot { position: relative; padding: 10px 16px; min-height: 44px; background: transparent; border: 0; border-radius: 0; }
  .slot + .slot::before { content: ''; position: absolute; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line-2); }
  .slot-text { font-size: 1.0625rem; }
  .slot-text .muted { font-size: 0.8125rem; }
  .manual { display: flex; flex-direction: column; align-items: stretch; gap: var(--sp-3); margin-top: var(--sp-3); }
  .slot-panel .manual-rows { display: flex; flex-direction: column; background: var(--surface-2); border-radius: var(--r-md); overflow: hidden; }
  .slot-panel .manual-rows > * { position: relative; flex-direction: row; align-items: center; justify-content: space-between; gap: 12px; min-height: 44px; padding: 0 16px; }
  .slot-panel .manual-rows > * + *::before { content: ''; position: absolute; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line-2); }
  .slot-panel .manual-rows :deep(.field-label) { font-size: 1.0625rem; font-weight: 400; letter-spacing: 0; text-transform: none; color: var(--ink); }
  .slot-panel .manual-rows :deep(.field-control) { flex: 1; justify-content: flex-end; }
  .slot-panel .manual-rows :deep(input) { width: auto; max-width: 100%; height: 34px; padding: 0 10px; background: var(--surface-2); border-radius: 8px; font-size: 1.0625rem; }
  .manual-btn { height: 44px; border-radius: var(--r-md); }
}
</style>
