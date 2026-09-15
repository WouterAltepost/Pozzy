<script setup>
import { useLoadTask } from '../../composables/useReady'
import { useWidgetLink } from '../../composables/useWidgetLink'
import { onMounted, ref } from 'vue'
import { PhCalendarBlank } from '@phosphor-icons/vue'
import { listEvents } from '../../api/calendar'
import { addDays, formatTime, today } from '../../lib/dates'
import { dayStartIso } from '../../stores/calendar'
import UiBadge from '../ui/UiBadge.vue'
import UiEmpty from '../ui/UiEmpty.vue'

const settle = useLoadTask()

// Today's calendar events plus scheduled tasks, from the local mirror only.
// Renders nothing when the API call fails (BUILD.md widget contract).
const items = ref(null)
const failed = ref(false)

async function load() {
  try {
    const day = today()
    const data = await listEvents({ start: dayStartIso(day), end: dayStartIso(addDays(day, 1)) })
    const events = data.events.map((e) => ({ id: 'e-' + e.id, title: e.title, start: e.start, end: e.end, allDay: e.all_day, kind: e.task_id ? 'linked' : 'event', location: e.location }))
    const linkedTaskIds = new Set(data.events.filter((e) => e.task_id).map((e) => e.task_id))
    const tasks = data.tasks
      .filter((t) => !linkedTaskIds.has(t.id))
      .map((t) => ({ id: 't-' + t.id, title: t.title, start: t.scheduled_start, end: t.scheduled_end, allDay: false, kind: 'task' }))
    items.value = [...events, ...tasks].sort((a, b) => (a.allDay === b.allDay ? new Date(a.start) - new Date(b.start) : a.allDay ? -1 : 1))
    failed.value = false
  } catch {
    failed.value = true
  }
}

onMounted(() => load().finally(settle))
const link = useWidgetLink('agenda')
</script>

<template>
  <section v-if="!failed && items" class="card widget clickable" tabindex="0" role="link" :aria-label="'Open agenda'" @click="link.onClick" @keydown="link.onKey">
    <div class="card-head">
      <h2>Today</h2>
      <span class="meta"><RouterLink :to="{ name: 'agenda' }">Agenda</RouterLink></span>
    </div>
    <ul v-if="items.length">
      <li v-for="it in items" :key="it.id" class="list-row" :class="it.kind">
        <span class="when num">{{ it.allDay ? 'all day' : formatTime(it.start) + ' to ' + formatTime(it.end) }}</span>
        <span class="title truncate">{{ it.title }}</span>
        <UiBadge v-if="it.kind === 'task'" tone="ok">task</UiBadge>
        <UiBadge v-else-if="it.kind === 'linked'" tone="info">linked</UiBadge>
        <span v-else-if="it.location" class="muted small truncate loc">{{ it.location }}</span>
      </li>
    </ul>
    <UiEmpty v-else compact title="No events today" hint="Nothing on the calendar mirror for today.">
      <template #icon><PhCalendarBlank /></template>
    </UiEmpty>
  </section>
</template>

<style scoped>
.when { color: var(--ink-3); font-size: var(--fs-sm); min-width: 96px; flex: none; }
.title { flex: 1; min-width: 0; }
.loc { max-width: 40%; }
</style>
