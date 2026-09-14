<script setup>
import { computed } from 'vue'
import { formatTime, shortDay, today } from '../../lib/dates'

// Week and day views share this grid: one column per day, an all-day row on top,
// timed events absolutely positioned between HOUR_START and HOUR_END. Scheduled
// tasks are overlaid as dashed blocks.
const props = defineProps({
  days: { type: Array, required: true },
  events: { type: Array, default: () => [] },
  tasks: { type: Array, default: () => [] },
  hourStart: { type: Number, default: 6 },
  hourEnd: { type: Number, default: 23 },
})
const emit = defineEmits(['select-event', 'create'])

const HOUR_PX = 44
const hours = computed(() => Array.from({ length: props.hourEnd - props.hourStart }, (_, i) => props.hourStart + i))
const gridHeight = computed(() => hours.value.length * HOUR_PX)

function dayBounds(day) {
  const [y, m, d] = day.split('-').map(Number)
  const start = new Date(y, m - 1, d)
  const end = new Date(y, m - 1, d + 1)
  return [start, end]
}

function minutesFromDayStart(date, dayStart) {
  return (date - dayStart) / 60000
}

// Clip an item to the visible part of the day and convert to pixel offsets.
function place(item, day) {
  const [dayStart, dayEnd] = dayBounds(day)
  const start = new Date(item.start)
  const end = new Date(item.end)
  if (end <= dayStart || start >= dayEnd) return null
  const from = Math.max(minutesFromDayStart(start, dayStart), props.hourStart * 60)
  const to = Math.min(minutesFromDayStart(end, dayStart), props.hourEnd * 60)
  if (to <= from) return null
  const top = ((from - props.hourStart * 60) / 60) * HOUR_PX
  const height = Math.max(((to - from) / 60) * HOUR_PX, 18)
  return { top, height, from, to }
}

// Simple lane assignment so overlapping blocks sit side by side.
function withLanes(blocks) {
  const sorted = [...blocks].sort((a, b) => a.from - b.from || b.to - a.to)
  const laneEnds = []
  for (const b of sorted) {
    let lane = laneEnds.findIndex((end) => end <= b.from)
    if (lane === -1) {
      lane = laneEnds.length
      laneEnds.push(b.to)
    } else {
      laneEnds[lane] = b.to
    }
    b.lane = lane
  }
  const lanes = Math.max(1, laneEnds.length)
  for (const b of sorted) b.lanes = lanes
  return sorted
}

const columns = computed(() =>
  props.days.map((day) => {
    const [dayStart, dayEnd] = dayBounds(day)
    const allDay = props.events.filter((e) => e.all_day && new Date(e.start) < dayEnd && new Date(e.end) > dayStart)
    const timed = []
    for (const e of props.events) {
      if (e.all_day) continue
      const pos = place(e, day)
      if (pos) timed.push({ ...pos, kind: 'event', item: e, key: `e-${e.id}` })
    }
    for (const t of props.tasks) {
      if (t.scheduled_start && t.scheduled_end) {
        const pos = place({ start: t.scheduled_start, end: t.scheduled_end }, day)
        if (pos) timed.push({ ...pos, kind: 'task', item: t, key: `t-${t.id}` })
      }
    }
    return { day, allDay, timed: withLanes(timed), isToday: day === today() }
  }),
)

const nowLine = computed(() => {
  const now = new Date()
  const minutes = now.getHours() * 60 + now.getMinutes()
  if (minutes < props.hourStart * 60 || minutes > props.hourEnd * 60) return null
  return ((minutes - props.hourStart * 60) / 60) * HOUR_PX
})

function blockStyle(b) {
  const width = 100 / b.lanes
  return { top: `${b.top}px`, height: `${b.height}px`, left: `${b.lane * width}%`, width: `calc(${width}% - 2px)` }
}

function onEmptyClick(evt, day) {
  if (evt.target !== evt.currentTarget) return
  const minutes = props.hourStart * 60 + (evt.offsetY / HOUR_PX) * 60
  const hour = Math.floor(minutes / 60)
  const minute = Math.floor((minutes % 60) / 30) * 30
  emit('create', { day, hour, minute })
}

function timeLabel(h) {
  return `${String(h).padStart(2, '0')}:00`
}
</script>

<template>
  <div class="grid" :class="{ single: days.length === 1 }">
    <div class="corner"></div>
    <div v-for="c in columns" :key="c.day" class="head" :class="{ today: c.isToday }">{{ shortDay(c.day) }}</div>

    <div class="gutter-label">all day</div>
    <div v-for="c in columns" :key="'ad-' + c.day" class="allday" @click="emit('create', { day: c.day, allDay: true })">
      <button v-for="e in c.allDay" :key="e.id" type="button" class="chip" :title="e.title" @click.stop="emit('select-event', e)">{{ e.title }}</button>
    </div>

    <div class="gutter" :style="{ height: gridHeight + 'px' }">
      <div v-for="h in hours" :key="h" class="hour-label" :style="{ height: HOUR_PX + 'px' }">{{ timeLabel(h) }}</div>
    </div>
    <div
      v-for="c in columns"
      :key="'col-' + c.day"
      class="col"
      :class="{ today: c.isToday }"
      :style="{ height: gridHeight + 'px' }"
      @click="onEmptyClick($event, c.day)"
    >
      <div v-for="h in hours" :key="h" class="hour-line" :style="{ top: (h - hourStart) * HOUR_PX + 'px' }"></div>
      <div v-if="c.isToday && nowLine !== null" class="now" :style="{ top: nowLine + 'px' }"></div>
      <template v-for="b in c.timed" :key="b.key">
        <button v-if="b.kind === 'event'" type="button" class="block event" :class="{ linked: b.item.task_id, recurring: b.item.recurrence_id }" :style="blockStyle(b)" :title="b.item.title" @click.stop="emit('select-event', b.item)">
          <span class="time">{{ formatTime(b.item.start) }}</span>
          <span class="title">{{ b.item.title }}</span>
        </button>
        <RouterLink v-else :to="{ name: 'tasks' }" class="block task" :style="blockStyle(b)" :title="'Task: ' + b.item.title" @click.stop>
          <span class="time">{{ formatTime(b.item.scheduled_start) }}</span>
          <span class="title">{{ b.item.title }}</span>
        </RouterLink>
      </template>
    </div>
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: 52px repeat(7, minmax(0, 1fr));
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  overflow: hidden;
  font-size: 0.8rem;
}
.grid.single { grid-template-columns: 52px minmax(0, 1fr); }
.corner, .head, .gutter-label, .allday { border-bottom: 1px solid #e5e7eb; }
.head { padding: 0.4rem 0.3rem; font-weight: 600; text-align: center; border-left: 1px solid #f3f4f6; }
.head.today { color: #2563eb; }
.gutter-label { font-size: 0.7rem; color: #9ca3af; padding: 0.3rem 0.2rem; text-align: right; }
.allday { min-height: 28px; padding: 0.15rem; border-left: 1px solid #f3f4f6; display: flex; flex-direction: column; gap: 2px; cursor: pointer; }
.chip { font: inherit; font-size: 0.72rem; text-align: left; border: none; border-radius: 3px; padding: 0.1rem 0.3rem; background: #fde68a; color: #78350f; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; cursor: pointer; }
.gutter { position: relative; }
.hour-label { font-size: 0.7rem; color: #9ca3af; text-align: right; padding-right: 0.3rem; transform: translateY(-0.5em); }
.col { position: relative; border-left: 1px solid #f3f4f6; cursor: crosshair; }
.col.today { background: #f8fafc; }
.hour-line { position: absolute; left: 0; right: 0; border-top: 1px solid #f3f4f6; pointer-events: none; }
.now { position: absolute; left: 0; right: 0; border-top: 2px solid #ef4444; z-index: 3; pointer-events: none; }
.block {
  position: absolute;
  box-sizing: border-box;
  margin: 1px;
  padding: 0.15rem 0.3rem;
  border-radius: 4px;
  overflow: hidden;
  text-align: left;
  font: inherit;
  font-size: 0.74rem;
  line-height: 1.2;
  cursor: pointer;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 1px;
  text-decoration: none;
}
.block .time { font-size: 0.66rem; opacity: 0.8; }
.block .title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.event { background: #dbeafe; color: #1e3a8a; border: 1px solid #bfdbfe; }
.event.recurring { border-left: 3px solid #60a5fa; }
.event.linked { background: #ede9fe; color: #4c1d95; border-color: #ddd6fe; }
.task { background: #ecfdf5; color: #065f46; border: 1px dashed #34d399; }
@media (max-width: 720px) {
  .grid { font-size: 0.7rem; }
  .block { font-size: 0.66rem; padding: 0.1rem 0.2rem; }
  .block .time { display: none; }
}
</style>
