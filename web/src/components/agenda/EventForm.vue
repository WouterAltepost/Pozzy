<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { toDay } from '../../lib/dates'

// Create (event = null) or edit a single event. Times are edited as local date + time
// inputs and sent as ISO strings with the browser offset.
const props = defineProps({
  event: { type: Object, default: null },
  defaults: { type: Object, default: () => ({}) }, // { day, hour, minute, allDay }
  calendars: { type: Array, default: () => [] }, // [{ name, url }]
  defaultCalendarUrl: { type: String, default: '' },
  saving: { type: Boolean, default: false },
  error: { type: String, default: '' },
})
const emit = defineEmits(['save', 'delete', 'close'])

const form = reactive({ title: '', all_day: false, startDay: '', startTime: '09:00', endDay: '', endTime: '10:00', location: '', description: '', calendar_url: '' })
const confirmDelete = ref(false)

const isEdit = computed(() => !!props.event)
const readOnly = computed(() => !!props.event?.recurrence_id)

function pad(n) {
  return String(n).padStart(2, '0')
}
function localTime(iso) {
  const d = new Date(iso)
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function reset() {
  confirmDelete.value = false
  if (props.event) {
    const e = props.event
    const end = new Date(e.end)
    form.title = e.title
    form.all_day = e.all_day
    form.startDay = toDay(new Date(e.start))
    form.startTime = localTime(e.start)
    // All-day end is exclusive; show the last day inclusive in the form.
    form.endDay = toDay(e.all_day ? new Date(end.getTime() - 86400000) : end)
    form.endTime = localTime(e.end)
    form.location = e.location || ''
    form.description = e.description || ''
    form.calendar_url = e.calendar_url
  } else {
    const d = props.defaults
    const day = d.day || toDay(new Date())
    const hour = d.hour ?? 9
    const minute = d.minute ?? 0
    form.title = ''
    form.all_day = !!d.allDay
    form.startDay = day
    form.endDay = day
    form.startTime = `${pad(hour)}:${pad(minute)}`
    const endMinutes = hour * 60 + minute + 60
    form.endTime = `${pad(Math.min(23, Math.floor(endMinutes / 60)))}:${pad(endMinutes % 60)}`
    form.location = ''
    form.description = ''
    form.calendar_url = props.defaultCalendarUrl
  }
}
watch(() => [props.event, props.defaults], reset, { immediate: true })

function iso(day, time) {
  const [y, m, d] = day.split('-').map(Number)
  const [hh, mm] = (time || '00:00').split(':').map(Number)
  return new Date(y, m - 1, d, hh, mm).toISOString()
}

function submit() {
  const body = {
    title: form.title,
    all_day: form.all_day,
    location: form.location || null,
    description: form.description || null,
  }
  if (form.all_day) {
    body.start = iso(form.startDay, '00:00')
    // Inclusive last day in the form, exclusive end for the API.
    const [y, m, d] = form.endDay.split('-').map(Number)
    body.end = new Date(y, m - 1, d + 1).toISOString()
  } else {
    body.start = iso(form.startDay, form.startTime)
    body.end = iso(form.endDay, form.endTime)
  }
  if (!isEdit.value && form.calendar_url) body.calendar_url = form.calendar_url
  emit('save', body)
}
</script>

<template>
  <form class="event-form" @submit.prevent="submit">
    <div class="head">
      <h2>{{ isEdit ? 'Event' : 'New event' }}</h2>
      <button type="button" class="link" @click="emit('close')">Close</button>
    </div>
    <p v-if="readOnly" class="muted small">This is one occurrence of a recurring event. Edit or delete it on your phone; the change syncs back.</p>
    <p v-if="event?.task_id" class="muted small">Linked to a scheduled task. Moving it here moves the task too.</p>
    <fieldset :disabled="readOnly || saving">
      <label>Title <input v-model="form.title" type="text" required maxlength="500" autofocus /></label>
      <label class="inline"><input v-model="form.all_day" type="checkbox" /> All day</label>
      <div class="row">
        <label>Start <input v-model="form.startDay" type="date" required /></label>
        <label v-if="!form.all_day">&nbsp;<input v-model="form.startTime" type="time" required /></label>
      </div>
      <div class="row">
        <label>End <input v-model="form.endDay" type="date" required /></label>
        <label v-if="!form.all_day">&nbsp;<input v-model="form.endTime" type="time" required /></label>
      </div>
      <label>Location <input v-model="form.location" type="text" maxlength="500" /></label>
      <label>Notes <textarea v-model="form.description" rows="3" maxlength="5000"></textarea></label>
      <label v-if="!isEdit && calendars.length > 1">
        Calendar
        <select v-model="form.calendar_url">
          <option v-for="c in calendars" :key="c.url" :value="c.url">{{ c.name }}</option>
        </select>
      </label>
      <p v-else-if="isEdit" class="muted small">Calendar: {{ calendars.find((c) => c.url === form.calendar_url)?.name || form.calendar_url }}</p>
    </fieldset>
    <p v-if="error" class="error">{{ error }}</p>
    <div class="actions" v-if="!readOnly">
      <button type="submit" :disabled="saving">{{ saving ? 'Saving...' : isEdit ? 'Save' : 'Create' }}</button>
      <template v-if="isEdit">
        <button v-if="!confirmDelete" type="button" class="danger" :disabled="saving" @click="confirmDelete = true">Delete</button>
        <template v-else>
          <span class="small">Delete from iCloud?</span>
          <button type="button" class="danger" :disabled="saving" @click="emit('delete')">Yes, delete</button>
          <button type="button" class="link" @click="confirmDelete = false">No</button>
        </template>
      </template>
    </div>
  </form>
</template>

<style scoped>
.event-form { display: flex; flex-direction: column; gap: 0.6rem; }
.head { display: flex; justify-content: space-between; align-items: center; }
.head h2 { margin: 0; font-size: 1rem; }
fieldset { border: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.5rem; min-width: 0; }
label { display: flex; flex-direction: column; gap: 0.2rem; font-size: 0.85rem; color: #4b5563; }
label.inline { flex-direction: row; align-items: center; gap: 0.4rem; }
input, textarea, select { font: inherit; padding: 0.35rem; border: 1px solid #d1d5db; border-radius: 4px; width: 100%; box-sizing: border-box; }
.row { display: flex; gap: 0.5rem; }
.row label { flex: 1; }
.actions { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.link { border: none; background: none; color: #2563eb; padding: 0.2rem 0.4rem; }
.danger { color: #b91c1c; border-color: #fecaca; }
.small { font-size: 0.8rem; }
</style>
