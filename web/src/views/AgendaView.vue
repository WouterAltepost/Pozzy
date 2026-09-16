<script setup>
import { computed, ref } from 'vue'
import { PhCaretLeft, PhCaretRight, PhCheck, PhSparkle, PhX } from '@phosphor-icons/vue'
import AgendaGrid from '../components/agenda/AgendaGrid.vue'
import AgendaMobile from '../components/agenda/AgendaMobile.vue'
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
import { useToast } from '../composables/useToast'
import { formatDay, mondayOf, today } from '../lib/dates'
import { useCalendarStore } from '../stores/calendar'
import { planWeek } from '../api/ai'
import { scheduleTask } from '../api/tasks'
import { formatDateTime } from '../lib/dates'

const store = useCalendarStore()
const toast = useToast()
const panel = ref(null) // null | { event } | { defaults }
const quick = ref(null) // { day, hour, minute, endHour, endMinute, anchor } for the popover
const saving = ref(false)
const formError = ref('')
const narrow = useMediaQuery('(max-width: 899px)')
const phone = useMediaQuery('(max-width: 699px)')
const suggestions = ref([]) // planner items still waiting for a decision
const planning = ref(false)
const planned = ref(false)
const deciding = ref({}) // id -> true while an accept is in flight
const trayOpen = ref(true)

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

// Plan: Pozzy proposes placements for the shown range. Nothing is written until accepted.
async function plan() {
  planning.value = true
  try {
    const data = await planWeek(store.days[0], store.days.length)
    suggestions.value = data.items
    planned.value = true
    trayOpen.value = true
    if (!data.items.length) toast.success('Nothing to place: no open tasks, deadlines or goals fit the free slots.')
  } catch (err) {
    toast.error(err.message)
  } finally {
    planning.value = false
  }
}
async function accept(item) {
  if (deciding.value[item.id]) return
  deciding.value[item.id] = true
  try {
    if (item.kind === 'task') await scheduleTask(item.task_id, { start: item.start, end: item.end })
    else await store.createEvent({ title: item.title, start: item.start, end: item.end, all_day: false, description: item.description || null })
    suggestions.value = suggestions.value.filter((s) => s.id !== item.id)
    if (item.kind === 'task') await store.load()
    toast.success(`Placed "${item.title}"`)
  } catch (err) {
    toast.error(err.message)
  } finally {
    delete deciding.value[item.id]
  }
}
function deny(item) {
  suggestions.value = suggestions.value.filter((s) => s.id !== item.id)
}
async function acceptAll() {
  for (const item of [...suggestions.value]) await accept(item)
}
function denyAll() {
  suggestions.value = []
}

// Dropped or resized on the grid: write the new times to iCloud through the API.
async function onMove({ event, day, from, to }) {
  const [y, m, d] = day.split('-').map(Number)
  const at = (minutes) => new Date(y, m - 1, d, Math.floor(minutes / 60), minutes % 60).toISOString()
  try {
    await store.updateEvent(event.id, { start: at(from), end: at(to) })
    toast.success(`Moved "${event.title}" to ${day}, ${String(Math.floor(from / 60)).padStart(2, '0')}:${String(from % 60).padStart(2, '0')}`)
  } catch (err) {
    toast.error(err.message)
  }
}

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
    <PageHeader v-if="!phone" title="Agenda">
      <template #meta>{{ title }}</template>
      <div class="nav">
        <button type="button" class="icon-btn" aria-label="Previous" @click="store.step(-1)"><PhCaretLeft /></button>
        <button type="button" class="icon-btn" aria-label="Next" @click="store.step(1)"><PhCaretRight /></button>
        <button v-if="store.anchor !== today()" type="button" class="link-btn" @click="store.goToday()">Today</button>
        <input type="date" :value="store.anchor" aria-label="Go to date" @change="pickDay" />
      </div>
      <UiSegmented v-model="view" :options="VIEWS" />
      <UiButton :loading="planning" title="Suggest where open tasks, deadline prep and goal work could go" @click="plan">
        <PhSparkle :size="16" weight="fill" aria-hidden="true" />
        Plan
      </UiButton>
      <UiButton variant="primary" @click="openNew({ day: store.anchor })">New event</UiButton>
    </PageHeader>

    <div v-if="!phone" class="status">
      <SyncBar />
      <p v-if="store.error" class="error">{{ store.error }}</p>
    </div>
    <p v-else-if="store.error" class="error">{{ store.error }}</p>

    <UiLoadGate :ready="ready" label="Loading your week">
      <Transition name="tray">
        <section v-if="suggestions.length" class="card tray">
          <div class="tray-head">
            <PhSparkle weight="fill" class="spark" aria-hidden="true" />
            <strong>Pozzy suggests {{ suggestions.length }} {{ suggestions.length === 1 ? 'placement' : 'placements' }}</strong>
            <span class="muted small">Dashed blocks on the grid. Accept or deny each one, or all at once.</span>
            <span class="tray-actions">
              <button type="button" class="link-btn" @click="trayOpen = !trayOpen">{{ trayOpen ? 'Hide list' : 'Show list' }}</button>
              <UiButton size="sm" variant="primary" @click="acceptAll">Accept all</UiButton>
              <UiButton size="sm" variant="ghost" @click="denyAll">Deny all</UiButton>
            </span>
          </div>
          <ul v-if="trayOpen" class="tray-list">
            <li v-for="s in suggestions" :key="s.id" class="tray-row" :class="s.kind">
              <span class="kind">{{ s.kind === 'task' ? 'task' : 'event' }}</span>
              <span class="t truncate">{{ s.title }}</span>
              <span class="when num">{{ formatDateTime(s.start) }}, {{ s.minutes }} min</span>
              <span class="why muted small truncate" :title="s.reason">{{ s.reason }}</span>
              <span class="row-actions">
                <button type="button" class="icon-btn ok" :aria-label="'Accept: ' + s.title" :disabled="deciding[s.id]" @click="accept(s)"><PhCheck weight="bold" /></button>
                <button type="button" class="icon-btn" :aria-label="'Deny: ' + s.title" @click="deny(s)"><PhX weight="bold" /></button>
              </span>
            </li>
          </ul>
        </section>
      </Transition>
      <AgendaMobile v-if="phone" :suggestions="suggestions" :planning="planning" @select-event="openEvent" @create="openNew" @plan="plan" @accept="accept" @deny="deny" />
      <div v-else class="gridwrap">
        <div class="gridpos">
          <AgendaGrid :days="store.days" :events="store.events" :tasks="store.tasks" :draft="draft" :suggestions="suggestions" @select-event="openEvent" @create="onSlot" @move="onMove" @accept="accept" @deny="deny" />
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
.tray { margin-bottom: var(--sp-4); border-style: dashed; }
.tray-head { display: flex; align-items: center; gap: var(--sp-3); flex-wrap: wrap; }
.spark { color: var(--brand); width: 18px; height: 18px; }
.tray-actions { display: inline-flex; align-items: center; gap: var(--sp-2); margin-left: auto; }
.tray-list { margin-top: var(--sp-3); display: flex; flex-direction: column; }
.tray-row { display: grid; grid-template-columns: auto minmax(0, 1.2fr) auto minmax(0, 1.6fr) auto; align-items: center; gap: var(--sp-3); padding: 6px 0; border-top: 1px solid var(--line); font-size: var(--fs-md); }
.tray-row .kind { font-size: var(--fs-xs); font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; padding: 1px 6px; border-radius: var(--r-sm); }
.tray-row.task .kind { color: var(--ok); background: var(--ok-soft); }
.tray-row.event .kind { color: var(--info); background: var(--info-soft); }
.tray-row .when { white-space: nowrap; color: var(--ink-2); }
.row-actions { display: inline-flex; gap: 2px; }
.icon-btn.ok { color: var(--ok); }
@media (max-width: 720px) { .tray-row { grid-template-columns: auto minmax(0, 1fr) auto; } .tray-row .why { display: none; } .tray-row .when { grid-column: 2; font-size: var(--fs-xs); } }
.tray-enter-active { transition: opacity var(--dur-ui) ease, transform var(--dur-modal) var(--ease-spring); }
.tray-leave-active { transition: opacity var(--dur-hover) ease; }
.tray-enter-from { opacity: 0; transform: translateY(-6px); }
.tray-leave-to { opacity: 0; }
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
