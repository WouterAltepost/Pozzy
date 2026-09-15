<script setup>
import { computed } from 'vue'
import { formatTime, shortDay, today } from '../../lib/dates'

// Week and day views share this grid: one column per day, an all-day row on top,
// timed events absolutely positioned between HOUR_START and HOUR_END. Scheduled
// tasks are overlaid as dashed blocks. HOUR_PX and the click-to-create math are unchanged.
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
    <div v-for="c in columns" :key="c.day" class="head num" :class="{ today: c.isToday }">{{ shortDay(c.day) }}</div>

    <div class="gutter-label">all day</div>
    <div v-for="c in columns" :key="'ad-' + c.day" class="allday" :class="{ today: c.isToday }" @click="emit('create', { day: c.day, allDay: true })">
      <button v-for="e in c.allDay" :key="e.id" type="button" class="chip" :title="e.title" @click.stop="emit('select-event', e)">{{ e.title }}</button>
    </div>

    <div class="gutter" :style="{ height: gridHeight + 'px' }">
      <div v-for="h in hours" :key="h" class="hour-label num" :style="{ height: HOUR_PX + 'px' }">{{ timeLabel(h) }}</div>
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
          <span class="time num">{{ formatTime(b.item.start) }}</span>
          <span class="title">{{ b.item.title }}</span>
        </button>
        <RouterLink v-else :to="{ name: 'tasks' }" class="block task" :style="blockStyle(b)" :title="'Task: ' + b.item.title" @click.stop>
          <span class="time num">{{ formatTime(b.item.scheduled_start) }}</span>
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
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  background: var(--surface);
  overflow: hidden;
  font-size: var(--fs-md);
}
.grid.single { grid-template-columns: 52px minmax(0, 1fr); }
.corner, .head, .gutter-label, .allday { border-bottom: 1px solid var(--line); }
.head { padding: 8px 4px; font-weight: 500; font-size: var(--fs-sm); color: var(--ink-2); text-align: center; border-left: 1px solid var(--line); }
.head.today { color: var(--brand); background: var(--brand-soft); font-weight: 600; }
.gutter-label { font-size: var(--fs-xs); color: var(--ink-3); padding: 6px 4px; text-align: right; letter-spacing: 0.02em; }
.allday { min-height: 30px; padding: 2px; border-left: 1px solid var(--line); display: flex; flex-direction: column; gap: 2px; cursor: pointer; }
.allday.today { background: color-mix(in srgb, var(--brand-soft) 45%, transparent); }
.chip { font: inherit; font-size: var(--fs-xs); font-weight: 500; text-align: left; border: 0; border-radius: var(--r-sm); padding: 2px 6px; background: var(--surface-3); color: var(--ink); overflow: hidden; white-space: nowrap; text-overflow: ellipsis; cursor: pointer; }
.gutter { position: relative; }
.hour-label { font-size: var(--fs-xs); color: var(--ink-3); text-align: right; padding-right: 6px; transform: translateY(-0.5em); }
.col { position: relative; border-left: 1px solid var(--line); cursor: crosshair; }
.col.today { background: color-mix(in srgb, var(--brand-soft) 30%, transparent); }
.hour-line { position: absolute; left: 0; right: 0; border-top: 1px solid var(--line); opacity: 0.7; pointer-events: none; }
.now { position: absolute; left: 0; right: 0; border-top: 2px solid var(--brand); z-index: 3; pointer-events: none; }
.now::before { content: ''; position: absolute; left: -1px; top: -5px; width: 8px; height: 8px; border-radius: 50%; background: var(--brand); }
.block {
  position: absolute;
  box-sizing: border-box;
  margin: 1px;
  padding: 2px 6px 2px 8px;
  border-radius: var(--r-sm);
  overflow: hidden;
  text-align: left;
  font: inherit;
  font-size: var(--fs-sm);
  line-height: 1.25;
  cursor: pointer;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 1px;
  text-decoration: none;
  border: 1px solid color-mix(in srgb, var(--accent, var(--info)) 35%, transparent);
  transition: filter var(--dur-hover) ease;
}
@media (hover: hover) and (pointer: fine) { .block:hover { filter: brightness(0.96); } }
.block .time { font-size: var(--fs-xs); color: var(--accent, var(--info)); font-weight: 500; }
.block .title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 500; }
.event { --accent: var(--info); background: var(--info-soft); color: var(--ink); }
.event.recurring { --accent: var(--ink-3); background: var(--surface-2); }
.event.linked { --accent: var(--ok); background: var(--ok-soft); }
.task { --accent: var(--ok); background: transparent; color: var(--ok); border: 1px dashed var(--ok); }
@media (max-width: 720px) {
  .grid { font-size: var(--fs-sm); grid-template-columns: 40px repeat(7, minmax(0, 1fr)); }
  .grid.single { grid-template-columns: 40px minmax(0, 1fr); }
  .block { font-size: var(--fs-xs); padding: 1px 3px 1px 6px; }
  .block .time { display: none; }
}
</style>
