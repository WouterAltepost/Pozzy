<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { useMediaQuery } from '../../composables/useMediaQuery'
import { toDay } from '../../lib/dates'
import UiButton from '../ui/UiButton.vue'
import UiConfirm from '../ui/UiConfirm.vue'
import UiField from '../ui/UiField.vue'

// Create (event = null) or edit a single event. Times are edited as local date + time
// inputs and sent as ISO strings with the browser offset.
const props = defineProps({
  event: { type: Object, default: null },
  defaults: { type: Object, default: () => ({}) }, // { day, hour, minute, endHour, endMinute, allDay }
  calendars: { type: Array, default: () => [] }, // [{ name, url }]
  defaultCalendarUrl: { type: String, default: '' },
  saving: { type: Boolean, default: false },
  error: { type: String, default: '' },
})
const emit = defineEmits(['save', 'delete', 'close'])

const form = reactive({ title: '', all_day: false, startDay: '', startTime: '09:00', endDay: '', endTime: '10:00', location: '', description: '', calendar_url: '' })
const confirmDelete = ref(false)
// iOS layer: below 1024px the same fields read as Calendar's grouped rows (title and location,
// then all-day, starts and ends, calendar, notes), and Delete asks with an action sheet.
const ios = useMediaQuery('(max-width: 1023px)')
const calendarName = computed(() => props.calendars.find((c) => c.url === form.calendar_url)?.name || form.calendar_url)

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
    form.title = d.title || ''
    form.all_day = !!d.allDay
    form.startDay = day
    form.endDay = day
    form.startTime = `${pad(hour)}:${pad(minute)}`
    const endMinutes = d.endHour != null ? d.endHour * 60 + (d.endMinute ?? 0) : hour * 60 + minute + 60
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
    <p v-if="readOnly" class="muted small">This is one occurrence of a recurring event. Edit or delete it on your phone; the change syncs back.</p>
    <p v-if="event?.task_id" class="muted small">Linked to a scheduled task. Moving it here moves the task too.</p>
    <fieldset v-if="ios" :disabled="readOnly || saving" class="ios-fields">
      <div class="grp">
        <div class="cell"><input v-model="form.title" type="text" required maxlength="500" placeholder="Title" aria-label="Title" class="free" /></div>
        <div class="cell"><input v-model="form.location" type="text" maxlength="500" placeholder="Location" aria-label="Location" class="free" /></div>
      </div>
      <div class="grp">
        <label class="row"><span class="lbl">All-day</span><input v-model="form.all_day" type="checkbox" role="switch" /></label>
        <div class="row">
          <span class="lbl">Starts</span>
          <span class="vals"><input v-model="form.startDay" type="date" required aria-label="Start day" class="pill" /><input v-if="!form.all_day" v-model="form.startTime" type="time" required aria-label="Start time" class="pill" /></span>
        </div>
        <div class="row">
          <span class="lbl">Ends</span>
          <span class="vals"><input v-model="form.endDay" type="date" required aria-label="End day" class="pill" /><input v-if="!form.all_day" v-model="form.endTime" type="time" required aria-label="End time" class="pill" /></span>
        </div>
      </div>
      <div v-if="(!isEdit && calendars.length > 1) || isEdit" class="grp">
        <label v-if="!isEdit" class="row">
          <span class="lbl">Calendar</span>
          <select v-model="form.calendar_url" class="val">
            <option v-for="c in calendars" :key="c.url" :value="c.url">{{ c.name }}</option>
          </select>
        </label>
        <div v-else class="row"><span class="lbl">Calendar</span><span class="val truncate">{{ calendarName }}</span></div>
      </div>
      <div class="grp">
        <div class="cell"><textarea v-model="form.description" rows="4" maxlength="5000" placeholder="Notes" aria-label="Notes" class="free"></textarea></div>
      </div>
    </fieldset>
    <fieldset v-else :disabled="readOnly || saving" class="fields">
      <UiField label="Title"><input v-model="form.title" type="text" required maxlength="500" autofocus /></UiField>
      <label class="check"><input v-model="form.all_day" type="checkbox" /> All day</label>
      <div class="pair">
        <UiField label="Start"><input v-model="form.startDay" type="date" required /></UiField>
        <UiField v-if="!form.all_day" label="Time"><input v-model="form.startTime" type="time" required /></UiField>
      </div>
      <div class="pair">
        <UiField label="End"><input v-model="form.endDay" type="date" required /></UiField>
        <UiField v-if="!form.all_day" label="Time"><input v-model="form.endTime" type="time" required /></UiField>
      </div>
      <UiField label="Location"><input v-model="form.location" type="text" maxlength="500" /></UiField>
      <UiField label="Notes"><textarea v-model="form.description" rows="3" maxlength="5000"></textarea></UiField>
      <UiField v-if="!isEdit && calendars.length > 1" label="Calendar">
        <select v-model="form.calendar_url">
          <option v-for="c in calendars" :key="c.url" :value="c.url">{{ c.name }}</option>
        </select>
      </UiField>
      <p v-else-if="isEdit" class="muted small">Calendar: {{ calendars.find((c) => c.url === form.calendar_url)?.name || form.calendar_url }}</p>
    </fieldset>
    <p v-if="error" class="error">{{ error }}</p>
    <div v-if="!readOnly && ios" class="ios-actions">
      <UiButton type="submit" variant="primary" class="save" :loading="saving">{{ isEdit ? 'Save' : 'Add event' }}</UiButton>
      <button v-if="isEdit" type="button" class="delete-row" :disabled="saving" @click="confirmDelete = true">Delete event</button>
      <UiConfirm :open="confirmDelete" title="Delete this event?" message="It is removed from iCloud as well." confirm-label="Delete event" danger :busy="saving" @confirm="emit('delete')" @cancel="confirmDelete = false" />
    </div>
    <div v-else-if="!readOnly" class="actions">
      <UiButton type="submit" variant="primary" :loading="saving">{{ isEdit ? 'Save' : 'Create' }}</UiButton>
      <template v-if="isEdit">
        <UiButton v-if="!confirmDelete" variant="danger" class="push" :disabled="saving" @click="confirmDelete = true">Delete</UiButton>
        <template v-else>
          <span class="small push">Delete from iCloud?</span>
          <UiButton variant="danger" :disabled="saving" @click="emit('delete')">Yes, delete</UiButton>
          <UiButton variant="ghost" @click="confirmDelete = false">No</UiButton>
        </template>
      </template>
    </div>
  </form>
</template>

<style scoped>
.event-form { display: flex; flex-direction: column; gap: var(--sp-3); }
.fields { display: flex; flex-direction: column; gap: var(--sp-3); }
.check { display: flex; align-items: center; gap: 6px; }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: var(--sp-2); }
.actions { display: flex; align-items: center; gap: var(--sp-2); flex-wrap: wrap; }
.push { margin-left: auto; }
/* iOS layer (only rendered below 1024px): grouped rows on the sheet, 44pt each, hairlines
   from the text; dates and times are grey capsules on the right, as in Calendar. */
.ios-fields { display: flex; flex-direction: column; gap: var(--sp-5); }
.grp { display: flex; flex-direction: column; background: var(--surface-2); border-radius: var(--r-md); overflow: hidden; }
.grp > * { position: relative; min-height: 44px; }
.grp > * + *::before { content: ''; position: absolute; top: 0; left: 16px; right: 0; height: 0.5px; background: var(--line-2); }
.cell { display: flex; }
.grp .free { width: 100%; height: 44px; padding: 0 16px; border-radius: 0; background: transparent; font-size: 1.0625rem; }
.grp textarea.free { height: auto; min-height: 96px; padding: 11px 16px; resize: none; }
.grp .free:focus-visible { box-shadow: none; }
.row { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 0 16px; font-size: 1.0625rem; }
.lbl { flex: none; color: var(--ink); }
.vals { flex: 1; display: flex; justify-content: flex-end; gap: 6px; min-width: 0; }
.pill { height: 34px; padding: 0 10px; border-radius: 8px; background: var(--surface-2); font-size: 1.0625rem; text-align: center; min-width: 0; }
.vals .pill[type='date'] { flex: 0 1 150px; width: 150px; }
.vals .pill[type='time'] { flex: none; width: 104px; }
.row .val { min-width: 0; color: var(--ink-3); text-align: right; }
.row select.val { height: 44px; padding: 0 20px 0 0; border-radius: 0; background-color: transparent; background-position: right 0 center; text-align-last: right; }
.ios-actions { display: flex; flex-direction: column; gap: var(--sp-5); }
.ios-actions .save { height: 50px; border-radius: 12px; font-size: 1.0625rem; }
.delete-row { width: 100%; min-height: 44px; border: 0; border-radius: var(--r-md); background: var(--surface-2); color: var(--danger); font: inherit; font-size: 1.0625rem; }
.delete-row:active { background: var(--surface-3); }
@media (max-width: 1023px) { .event-form > .muted { font-size: 0.8125rem; color: var(--ink-3); } }
</style>
