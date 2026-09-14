<script setup>
import { onMounted, ref } from 'vue'
import { listEvents } from '../../api/calendar'
import { addDays, formatTime, today } from '../../lib/dates'
import { dayStartIso } from '../../stores/calendar'

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

onMounted(load)
</script>

<template>
  <section v-if="!failed && items" class="card widget">
    <h2>Today <RouterLink :to="{ name: 'agenda' }" class="muted small">agenda</RouterLink></h2>
    <ul>
      <li v-for="it in items" :key="it.id" :class="it.kind">
        <span class="when">{{ it.allDay ? 'all day' : formatTime(it.start) + ' - ' + formatTime(it.end) }}</span>
        <span class="title">{{ it.title }}</span>
        <span v-if="it.kind === 'task'" class="tag">task</span>
        <span v-else-if="it.location" class="muted loc">{{ it.location }}</span>
      </li>
      <li v-if="!items.length" class="muted">No events today.</li>
    </ul>
  </section>
</template>

<style scoped>
h2 { font-size: 1rem; margin: 0 0 0.5rem; display: flex; justify-content: space-between; align-items: baseline; }
.small { font-size: 0.78rem; font-weight: normal; }
ul { list-style: none; padding: 0; margin: 0; }
li { display: flex; align-items: baseline; gap: 0.5rem; padding: 0.25rem 0; font-size: 0.9rem; }
.when { font-variant-numeric: tabular-nums; color: #6b7280; font-size: 0.8rem; min-width: 92px; }
.title { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.loc { font-size: 0.8rem; }
.tag { font-size: 0.7rem; padding: 0 0.3rem; border-radius: 3px; background: #ecfdf5; color: #065f46; border: 1px dashed #34d399; }
li.linked .title { color: #4c1d95; }
</style>
