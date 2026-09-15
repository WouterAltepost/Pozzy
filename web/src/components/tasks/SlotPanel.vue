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
      <UiField label="Start"><input v-model="manualStart" type="datetime-local" /></UiField>
      <UiField label="End"><input v-model="manualEnd" type="datetime-local" /></UiField>
      <UiButton :disabled="!manualStart" @click="acceptManual">Schedule manually</UiButton>
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
</style>
