<script setup>
import { computed, onMounted, ref } from 'vue'
import { PhCaretLeft, PhCaretRight } from '@phosphor-icons/vue'
import AgendaGrid from '../components/agenda/AgendaGrid.vue'
import EventForm from '../components/agenda/EventForm.vue'
import SyncBar from '../components/agenda/SyncBar.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiSegmented from '../components/ui/UiSegmented.vue'
import UiSheet from '../components/ui/UiSheet.vue'
import UiSkeleton from '../components/ui/UiSkeleton.vue'
import { useMediaQuery } from '../composables/useMediaQuery'
import { formatDay, mondayOf, today } from '../lib/dates'
import { useCalendarStore } from '../stores/calendar'

const store = useCalendarStore()
const panel = ref(null) // null | { event } | { defaults }
const saving = ref(false)
const formError = ref('')
const narrow = useMediaQuery('(max-width: 899px)')

const title = computed(() => (store.view === 'week' ? `Week of ${formatDay(mondayOf(store.anchor))}` : formatDay(store.anchor)))
const VIEWS = [
  { value: 'week', label: 'Week' },
  { value: 'day', label: 'Day' },
]
const view = computed({ get: () => store.view, set: (v) => store.setView(v) })

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
    <PageHeader title="Agenda">
      <template #meta>{{ title }}</template>
      <div class="nav">
        <button type="button" class="icon-btn" aria-label="Previous" @click="store.step(-1)"><PhCaretLeft /></button>
        <button type="button" class="icon-btn" aria-label="Next" @click="store.step(1)"><PhCaretRight /></button>
        <button v-if="store.anchor !== today()" type="button" class="link-btn" @click="store.goToday()">Today</button>
        <input type="date" :value="store.anchor" aria-label="Go to date" @change="pickDay" />
      </div>
      <UiSegmented v-model="view" :options="VIEWS" />
      <UiButton variant="primary" @click="openNew({ day: store.anchor })">New event</UiButton>
    </PageHeader>

    <div class="status">
      <SyncBar />
      <p v-if="store.error" class="error">{{ store.error }}</p>
    </div>

    <div class="body" :class="{ split: panel && !narrow }">
      <div class="gridwrap">
        <UiSkeleton v-if="store.loading && !store.events.length" height="240px" />
        <AgendaGrid :days="store.days" :events="store.events" :tasks="store.tasks" @select-event="openEvent" @create="openNew" />
        <p class="legend muted xs">
          <span class="sw event"></span> event <span class="sw recurring"></span> recurring <span class="sw linked"></span> Pozzy task event
          <span class="sw task"></span> scheduled task (not yet on iCloud)
        </p>
      </div>
      <Transition name="panel">
        <aside v-if="panel && !narrow" class="card panel">
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
      </Transition>
    </div>

    <UiSheet :open="Boolean(panel) && narrow" :title="panel?.event ? 'Event' : 'New event'" @close="closePanel">
      <EventForm
        v-if="panel"
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
    </UiSheet>
  </div>
</template>

<style scoped>
.nav { display: flex; align-items: center; gap: 4px; }
.nav input[type='date'] { margin-left: 4px; }
.status { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; margin: calc(var(--sp-5) * -1) 0 var(--sp-3); }
.body { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--sp-5); align-items: start; }
@media (min-width: 900px) { .body.split { grid-template-columns: minmax(0, 1fr) 340px; } }
.gridwrap { min-width: 0; }
.panel { position: sticky; top: calc(var(--bar-h) + var(--sp-4)); margin: 0; }
.legend { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin: var(--sp-2) 0 0; }
.sw { display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-left: 6px; }
.sw.event { background: var(--info-soft); box-shadow: inset 3px 0 0 var(--info); }
.sw.recurring { background: var(--surface-2); box-shadow: inset 3px 0 0 var(--ink-3); }
.sw.linked { background: var(--ok-soft); box-shadow: inset 3px 0 0 var(--ok); }
.sw.task { outline: 1px dashed var(--ok); outline-offset: -1px; }
.panel-enter-active { transition: opacity var(--dur-panel) var(--ease-out), transform var(--dur-panel) var(--ease-out); }
.panel-leave-active { transition: opacity var(--dur-hover) ease; }
.panel-enter-from { opacity: 0; transform: translateX(8px); }
.panel-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) { .panel-enter-from { transform: none; } }
</style>
