<script setup>
import { computed, onMounted, ref } from 'vue'
import AgendaGrid from '../components/agenda/AgendaGrid.vue'
import EventForm from '../components/agenda/EventForm.vue'
import SyncBar from '../components/agenda/SyncBar.vue'
import { formatDay, mondayOf, today } from '../lib/dates'
import { useCalendarStore } from '../stores/calendar'

const store = useCalendarStore()
const panel = ref(null) // null | { event } | { defaults }
const saving = ref(false)
const formError = ref('')

const title = computed(() => (store.view === 'week' ? `Week of ${formatDay(mondayOf(store.anchor))}` : formatDay(store.anchor)))

onMounted(() => {
  store.load()
  store.loadAccount()
})

function openEvent(event) {
  formError.value = ''
  panel.value = { event }
}
function openNew(defaults = {}) {
  formError.value = ''
  panel.value = { defaults }
}
function closePanel() {
  panel.value = null
}

async function save(body) {
  saving.value = true
  formError.value = ''
  try {
    if (panel.value.event) await store.updateEvent(panel.value.event.id, body)
    else await store.createEvent(body)
    closePanel()
  } catch (err) {
    formError.value = err.message
  } finally {
    saving.value = false
  }
}

async function remove() {
  saving.value = true
  formError.value = ''
  try {
    await store.removeEvent(panel.value.event.id)
    closePanel()
  } catch (err) {
    formError.value = err.message
  } finally {
    saving.value = false
  }
}

function pickDay(evt) {
  if (evt.target.value) store.setAnchor(evt.target.value)
}
</script>

<template>
  <div class="agenda">
    <div class="toolbar">
      <h1>Agenda</h1>
      <div class="nav">
        <button type="button" @click="store.step(-1)">&lsaquo;</button>
        <span class="range">{{ title }}</span>
        <button type="button" @click="store.step(1)">&rsaquo;</button>
        <button v-if="store.anchor !== today()" type="button" class="link" @click="store.goToday()">Today</button>
        <input type="date" :value="store.anchor" @change="pickDay" />
      </div>
      <div class="views">
        <button type="button" :class="{ active: store.view === 'week' }" @click="store.setView('week')">Week</button>
        <button type="button" :class="{ active: store.view === 'day' }" @click="store.setView('day')">Day</button>
        <button type="button" class="primary" @click="openNew({ day: store.anchor })">New event</button>
      </div>
    </div>

    <SyncBar />
    <p v-if="store.error" class="error">{{ store.error }}</p>

    <div class="body">
      <div class="gridwrap">
        <p v-if="store.loading && !store.events.length" class="muted">Loading...</p>
        <AgendaGrid :days="store.days" :events="store.events" :tasks="store.tasks" @select-event="openEvent" @create="openNew" />
        <p class="legend muted">
          <span class="sw event"></span> event <span class="sw recurring"></span> recurring <span class="sw linked"></span> Pozzy task event
          <span class="sw task"></span> scheduled task (not yet on iCloud)
        </p>
      </div>
      <aside v-if="panel" class="card panel">
        <EventForm
          :event="panel.event || null"
          :defaults="panel.defaults || {}"
          :calendars="store.selectedCalendars"
          :default-calendar-url="store.account?.write_calendar_url || ''"
          :saving="saving"
          :error="formError"
          @save="save"
          @delete="remove"
          @close="closePanel"
        />
      </aside>
    </div>
  </div>
</template>

<style scoped>
.agenda { display: flex; flex-direction: column; gap: 0.75rem; }
h1 { font-size: 1.3rem; margin: 0; }
.toolbar { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
.nav, .views { display: flex; align-items: center; gap: 0.4rem; }
.range { font-size: 0.9rem; min-width: 140px; text-align: center; }
.nav input { font: inherit; font-size: 0.8rem; padding: 0.25rem; border: 1px solid #d1d5db; border-radius: 4px; }
.views .active { background: #111827; color: #fff; border-color: #111827; }
.primary { background: #2563eb; color: #fff; border-color: #2563eb; }
.link { border: none; background: none; color: #2563eb; padding: 0.2rem 0.4rem; }
.body { display: flex; gap: 1rem; align-items: flex-start; }
.gridwrap { flex: 1; min-width: 0; }
.panel { width: 320px; flex-shrink: 0; position: sticky; top: 1rem; }
.legend { font-size: 0.75rem; display: flex; gap: 0.4rem; align-items: center; flex-wrap: wrap; margin: 0.4rem 0 0; }
.sw { display: inline-block; width: 12px; height: 12px; border-radius: 3px; }
.sw.event { background: #dbeafe; border: 1px solid #bfdbfe; }
.sw.recurring { background: #dbeafe; border-left: 3px solid #60a5fa; }
.sw.linked { background: #ede9fe; border: 1px solid #ddd6fe; }
.sw.task { background: #ecfdf5; border: 1px dashed #34d399; }
@media (max-width: 860px) {
  .body { flex-direction: column; }
  .panel { width: 100%; position: static; }
}
</style>
