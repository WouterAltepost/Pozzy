<script setup>
import { ref } from 'vue'
import { daysUntil, formatDay } from '../../lib/dates'
import AreaDot from '../shared/AreaDot.vue'
import UiBadge from '../ui/UiBadge.vue'

const props = defineProps({ task: { type: Object, required: true }, selected: { type: Boolean, default: false }, draggable: { type: Boolean, default: true } })
const emit = defineEmits(['select', 'complete', 'dragstart'])
const lifting = ref(false)

function dueTone(t) {
  const d = daysUntil(t.due_date)
  if (d === null) return 'neutral'
  if (d < 0) return 'danger'
  if (d <= 1) return 'warn'
  return 'neutral'
}

function onDragStart(event) {
  lifting.value = true
  emit('dragstart', props.task, event)
}
</script>

<template>
  <div
    class="task-card"
    :class="{ selected, lifting, done: task.status === 'done', draggable }"
    :draggable="draggable"
    role="button"
    tabindex="0"
    @dragstart="onDragStart"
    @dragend="lifting = false"
    @click="emit('select', task)"
    @keydown.enter.self="emit('select', task)"
  >
    <label class="tick" @click.stop>
      <input type="checkbox" :checked="task.status === 'done'" :aria-label="'Complete ' + task.title" @change="emit('complete', task)" />
    </label>
    <div class="body">
      <div class="title-row">
        <div class="title">{{ task.title }}</div>
        <span v-if="task.due_date" class="due-right num" :class="dueTone(task)">{{ formatDay(task.due_date) }}</span>
      </div>
      <div class="meta">
        <AreaDot :area-id="task.area_id" label />
        <UiBadge v-if="task.due_date" :tone="dueTone(task)" class="num">{{ formatDay(task.due_date) }}</UiBadge>
        <span v-if="task.estimated_minutes" class="muted small num">{{ task.estimated_minutes }} min</span>
        <UiBadge v-if="task.urgent" tone="danger">urgent</UiBadge>
        <UiBadge v-if="task.important" tone="warn">important</UiBadge>
        <UiBadge v-if="task.status === 'scheduled'" tone="ok">scheduled</UiBadge>
        <UiBadge v-if="task.status === 'inbox'" tone="info">inbox</UiBadge>
        <span v-for="tag in task.tags" :key="tag" class="tag">{{ tag }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.task-card {
  display: flex;
  gap: var(--sp-2);
  align-items: flex-start;
  padding: var(--sp-2) var(--sp-3);
  border: 1px solid var(--line);
  border-radius: var(--r-md);
  background: var(--surface);
  cursor: pointer;
  transition: border-color var(--dur-hover) ease, box-shadow var(--dur-hover) var(--ease-out), transform var(--dur-hover) var(--ease-out), opacity var(--dur-hover) ease;
}
.task-card.draggable { cursor: grab; }
.task-card.draggable:active { cursor: grabbing; }
.task-card.selected { border-color: var(--ink); box-shadow: 0 0 0 1px var(--ink) inset; }
.task-card.lifting { box-shadow: var(--shadow-2); transform: rotate(1.5deg) scale(1.02); opacity: 0.9; }
.task-card.done .title { text-decoration: line-through; color: var(--ink-3); }
@media (hover: hover) and (pointer: fine) { .task-card:not(.selected):hover { border-color: var(--line-2); box-shadow: var(--shadow-1); } }
.tick { padding-top: 3px; display: flex; }
.body { flex: 1; min-width: 0; }
.title { font-size: var(--fs-base); line-height: 1.4; }
.title-row { display: flex; align-items: flex-start; gap: var(--sp-3); }
.title-row .title { flex: 1; min-width: 0; }
.due-right { display: none; font-size: var(--fs-sm); color: var(--ink-3); white-space: nowrap; margin-top: 2px; }
.due-right.danger { color: var(--danger); }
.due-right.warn { color: var(--warn); }
@media (max-width: 699px) {
  .task-card { border: 0; border-top: 1px solid var(--line); border-radius: 0; box-shadow: none; padding: 10px 0; }
  .task-card.selected { box-shadow: none; border-color: var(--line); }
  .due-right { display: inline; }
  .meta :deep(.badge.num) { display: none; }
  .tick input { width: 18px; height: 18px; }
}
.meta { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 4px; }
@media (prefers-reduced-motion: reduce) { .task-card.lifting { transform: none; } }
</style>
