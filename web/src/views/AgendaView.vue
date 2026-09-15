<script setup>
import { computed, ref } from 'vue'
import { PhCaretLeft, PhCaretRight } from '@phosphor-icons/vue'
import AgendaGrid from '../components/agenda/AgendaGrid.vue'
import EventForm from '../components/agenda/EventForm.vue'
import EventPopover from '../components/agenda/EventPopover.vue'
import SyncBar from '../components/agenda/SyncBar.vue'
import PageHeader from '../components/ui/PageHeader.vue'
import UiButton from '../components/ui/UiButton.vue'
import UiSegmented from '../components/ui/UiSegmented.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import UiModal from '../components/ui/UiModal.vue'
import { useMediaQuery } from '../composables/useMediaQuery'
import { useReady } from '../composables/useReady'
import { formatDay, mondayOf, today } from '../lib/dates'
import { useCalendarStore } from '../stores/calendar'

const store = useCalendarStore()
const panel = ref(null) // null | { event } | { defaults }
const quick = ref(null) // { day, hour, minute, endHour, endMinute, anchor } for the popover
const saving = ref(false)
const formError = ref('')
const narrow = useMediaQuery('(max-width: 899px)')

const title = computed(() => (store.view === 'week' ? `Week of ${formatDay(mondayOf(store.anchor))}` : formatDay(store.anchor)))
const VIEWS = [
  { value: 'week', label: 'Week' },
  { value: 'day', label: 'Day' },
]
const view = computed({ get: () => store.view, set: (v) => store.setView(v) })

const ready = useReady(() => Promise.all([store.load(), store.loadAccount()]))

function openEvent(event) {
  formError.value = ''
  panel.value = { event }
}
function openNew(defaults = {}) {
  formError.value = ''
  quick.value = null
  panel.value = { defaults }
}
function closePanel() {
  panel.value = null
}

// A slot picked on the grid: popover beside it on desktop, the sheet on the phone.
function onSlot(defaults) {
  if (defaults.allDay || narrow.value) return openNew(defaults)
  formError.value = ''
  panel.value = null
  quick.value = defaults
}
const draft = computed(() => (quick.value ? { day: quick.value.day, from: quick.value.hour * 60 + quick.value.minute, to: quick.value.endHour * 60 + quick.value.endMinute } : null))

async function quickSave(body) {
  saving.value = true
  formError.value = ''
  try {
    await store.createEvent(body)
    quick.value = null
  } catch (err) {
    formError.value = err.message
  } finally {
    saving.value = false
  }
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

    <UiLoadGate :ready="ready" label="Loading your week">
      <div class="gridwrap">
        <div class="gridpos">
          <AgendaGrid :days="store.days" :events="store.events" :tasks="store.tasks" :draft="draft" @select-event="openEvent" @create="onSlot" />
          <Transition name="pop">
            <EventPopover
              v-if="quick"
              :defaults="quick"
              :calendars="store.selectedCalendars"
              :default-calendar-url="store.account?.write_calendar_url || ''"
              :saving="saving"
              :error="formError"
              @save="quickSave"
              @more="openNew"
              @close="quick = null"
            />
          </Transition>
        </div>
        <p class="legend muted xs">
          <span class="sw event"></span> event <span class="sw recurring"></span> recurring <span class="sw linked"></span> Pozzy task event
          <span class="sw task"></span> scheduled task (not yet on iCloud)
        </p>
      </div>
    </UiLoadGate>

    <UiModal :open="Boolean(panel)" :title="panel?.event ? 'Event' : 'New event'" size="md" @close="closePanel">
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
    </UiModal>
  </div>
</template>

<style scoped>
.nav { display: flex; align-items: center; gap: 4px; }
.nav input[type='date'] { margin-left: 4px; }
.status { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; margin: calc(var(--sp-5) * -1) 0 var(--sp-3); }
.gridwrap { min-width: 0; }
.gridpos { position: relative; }
.pop-enter-active { transition: opacity var(--dur-ui) var(--ease-out), transform var(--dur-ui) var(--ease-out); }
.pop-leave-active { transition: opacity var(--dur-hover) ease, transform var(--dur-hover) ease; }
.pop-enter-from, .pop-leave-to { opacity: 0; transform: scale(0.97); }
@media (prefers-reduced-motion: reduce) { .pop-enter-from, .pop-leave-to { transform: none; } }
.legend { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin: var(--sp-2) 0 0; }
.sw { display: inline-block; width: 12px; height: 12px; border-radius: 3px; margin-left: 6px; }
.sw.event { background: var(--info-soft); border: 1px solid color-mix(in srgb, var(--info) 35%, transparent); }
.sw.recurring { background: var(--surface-2); border: 1px solid color-mix(in srgb, var(--ink-3) 35%, transparent); }
.sw.linked { background: var(--ok-soft); border: 1px solid color-mix(in srgb, var(--ok) 35%, transparent); }
.sw.task { border: 1px dashed var(--ok); }
</style>
