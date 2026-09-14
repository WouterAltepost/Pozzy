<script setup>
import { ref } from 'vue'
import { formatDateTime } from '../../lib/dates'
import { useTasksStore } from '../../stores/tasks'

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
      <strong>Suggest a slot</strong>
      <button type="button" class="link" @click="emit('close')">close</button>
    </div>
    <p v-if="task.scheduled_start" class="muted">
      Currently scheduled {{ formatDateTime(task.scheduled_start) }} to {{ formatDateTime(task.scheduled_end) }}.
      <button type="button" class="link" @click="unschedule">Unschedule</button>
    </p>
    <p v-if="loading" class="muted">Computing free slots...</p>
    <p v-else-if="error" class="error">{{ error }}</p>
    <template v-else-if="result">
      <p class="muted">{{ result.duration_minutes }} min, {{ result.candidates_considered }} free candidates, ranked by {{ result.ranked_by }}.</p>
      <p v-if="!result.slots.length" class="muted">No free slot in the next working days. Pick a time manually below.</p>
      <ul class="slots">
        <li v-for="s in result.slots" :key="s.start">
          <div>
            <strong>{{ s.day_label }}</strong> {{ formatDateTime(s.start).split(', ').pop() }} to {{ formatDateTime(s.end).split(', ').pop() }}
            <div class="muted">{{ s.reason }}</div>
          </div>
          <button type="button" @click="accept(s)">Accept</button>
        </li>
      </ul>
    </template>
    <div class="manual">
      <label>Start <input v-model="manualStart" type="datetime-local" /></label>
      <label>End <input v-model="manualEnd" type="datetime-local" /></label>
      <button type="button" :disabled="!manualStart" @click="acceptManual">Schedule manually</button>
    </div>
  </div>
</template>

<style scoped>
.slot-panel { border-top: 1px solid #e5e7eb; margin-top: 0.75rem; padding-top: 0.75rem; }
.head { display: flex; justify-content: space-between; align-items: center; }
.link { border: none; background: none; color: #2563eb; padding: 0; }
.slots { list-style: none; padding: 0; margin: 0.5rem 0; display: flex; flex-direction: column; gap: 0.4rem; }
.slots li { display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; background: #f3f4f6; padding: 0.5rem 0.6rem; border-radius: 4px; }
.manual { display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: flex-end; font-size: 0.85rem; }
.manual label { display: flex; flex-direction: column; gap: 0.2rem; }
.manual input { font: inherit; padding: 0.3rem; border: 1px solid #d1d5db; border-radius: 4px; }
</style>
