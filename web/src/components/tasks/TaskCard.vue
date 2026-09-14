<script setup>
import { daysUntil, formatDay } from '../../lib/dates'
import AreaDot from '../shared/AreaDot.vue'

const props = defineProps({ task: { type: Object, required: true }, selected: { type: Boolean, default: false }, draggable: { type: Boolean, default: true } })
const emit = defineEmits(['select', 'complete', 'dragstart'])

function dueClass(t) {
  const d = daysUntil(t.due_date)
  if (d === null) return ''
  if (d < 0) return 'overdue'
  if (d <= 1) return 'soon'
  return ''
}
</script>

<template>
  <div
    class="task-card"
    :class="{ selected, done: task.status === 'done', scheduled: task.status === 'scheduled' }"
    :draggable="draggable"
    @dragstart="emit('dragstart', task, $event)"
    @click="emit('select', task)"
  >
    <label class="tick" @click.stop>
      <input type="checkbox" :checked="task.status === 'done'" @change="emit('complete', task)" />
    </label>
    <div class="body">
      <div class="title">{{ task.title }}</div>
      <div class="meta">
        <AreaDot :area-id="task.area_id" label />
        <span v-if="task.due_date" :class="dueClass(task)">due {{ formatDay(task.due_date) }}</span>
        <span v-if="task.estimated_minutes">{{ task.estimated_minutes }}m</span>
        <span v-if="task.status === 'scheduled'" class="badge">scheduled</span>
        <span v-if="task.status === 'inbox'" class="badge">inbox</span>
        <span v-for="tag in task.tags" :key="tag" class="tag">{{ tag }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.task-card { display: flex; gap: 0.5rem; align-items: flex-start; padding: 0.45rem 0.55rem; border: 1px solid #e5e7eb; border-radius: 4px; background: #fff; cursor: pointer; }
.task-card.selected { border-color: #2563eb; box-shadow: 0 0 0 1px #2563eb inset; }
.task-card.done .title { text-decoration: line-through; color: #9ca3af; }
.tick { padding-top: 0.15rem; }
.body { flex: 1; min-width: 0; }
.title { font-size: 0.92rem; }
.meta { display: flex; flex-wrap: wrap; gap: 0.4rem; font-size: 0.75rem; color: #6b7280; margin-top: 0.15rem; }
.overdue { color: #b91c1c; font-weight: 600; }
.soon { color: #d97706; font-weight: 600; }
.badge { background: #e0e7ff; color: #3730a3; padding: 0 0.35rem; border-radius: 3px; }
.tag { background: #f3f4f6; padding: 0 0.35rem; border-radius: 3px; }
</style>
