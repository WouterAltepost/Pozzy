<script setup>
import { computed, ref } from 'vue'
import { useLongPress } from '../../composables/useLongPress'
import { useMediaQuery } from '../../composables/useMediaQuery'
import { daysUntil, formatDay } from '../../lib/dates'
import { useAreasStore } from '../../stores/areas'
import AreaDot from '../shared/AreaDot.vue'
import UiBadge from '../ui/UiBadge.vue'

const props = defineProps({ task: { type: Object, required: true }, selected: { type: Boolean, default: false }, draggable: { type: Boolean, default: true } })
const emit = defineEmits(['select', 'complete', 'dragstart', 'menu'])
const lifting = ref(false)
const areas = useAreasStore()
const root = ref(null)
// iOS layer: a long press opens the row's context menu. Only below 1024px, so a right-click on
// the desktop keeps the browser's own menu.
const ios = useMediaQuery('(max-width: 1023px)')
const press = useLongPress(() => emit('menu', root.value))
const pressHandlers = computed(() => (ios.value ? press.handlers(null) : {}))
function onClick() {
  if (press.consumed()) return
  emit('select', props.task)
}

// The phone's meta line reads like Reminders: plain text under the title, the due date in its
// tone, the flags, then area, estimate and tags, separated by middle dots, on one line that
// ends in an ellipsis when it runs out of room.
const iosMeta = computed(() => {
  const t = props.task
  const out = []
  if (t.due_date) out.push({ text: formatDay(t.due_date), tone: dueTone(t) })
  if (t.urgent) out.push({ text: 'Urgent', tone: 'danger' })
  if (t.important) out.push({ text: 'Important', tone: 'warn' })
  if (t.area_id && areas.name(t.area_id)) out.push({ text: areas.name(t.area_id), dot: areas.color(t.area_id) })
  if (t.estimated_minutes) out.push({ text: `${t.estimated_minutes} min` })
  if (t.status === 'scheduled') out.push({ text: 'Scheduled', tone: 'ok' })
  if (t.status === 'inbox') out.push({ text: 'Inbox', tone: 'info' })
  for (const tag of t.tags || []) out.push({ text: `#${tag}` })
  return out
})

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
    ref="root"
    class="task-card"
    :class="{ selected, lifting, done: task.status === 'done', draggable }"
    :draggable="draggable"
    role="button"
    tabindex="0"
    @dragstart="onDragStart"
    @dragend="lifting = false"
    v-bind="pressHandlers"
    @click="onClick"
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
      <div v-if="iosMeta.length" class="ios-meta num">
        <span v-for="(m, i) in iosMeta" :key="i" class="part" :class="m.tone"><span v-if="m.dot" class="dot" :style="{ background: m.dot }" aria-hidden="true"></span>{{ m.text }}</span>
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
.meta { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 4px; }
@media (prefers-reduced-motion: reduce) { .task-card.lifting { transform: none; } }
.ios-meta { display: none; }
/* iOS layer: a Reminders row inside an inset grouped plate. Circle on the left, the title at
   17pt, one line of plain meta under it; no card chrome, the plate and its separators do that. */
@media (max-width: 1023px) {
  .task-card { gap: 12px; padding: 11px 16px 11px 16px; border: 0; border-radius: 0; box-shadow: none; background: transparent; position: relative; min-height: 44px; transition: background-color 120ms ease; -webkit-user-select: none; user-select: none; -webkit-touch-callout: none; }
  .task-card.selected { box-shadow: none; }
  .task-card.done .title { text-decoration: none; }
  .tick { padding-top: 0; }
  .tick input { width: 22px; height: 22px; }
  .title { font-size: 1.0625rem; line-height: 22px; }
  .due-right, .meta { display: none; }
  .ios-meta { display: block; margin-top: 2px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; font-size: 0.9375rem; line-height: 20px; color: var(--ink-3); }
  .ios-meta .part + .part::before { content: '\00B7'; margin: 0 6px; color: var(--ink-4); }
  .ios-meta .dot { display: inline-block; width: 8px; height: 8px; margin-right: 5px; border-radius: 50%; vertical-align: 1px; }
  .ios-meta .danger { color: var(--danger); }
  .ios-meta .warn { color: var(--warn); }
  .ios-meta .ok { color: var(--ok); }
  .ios-meta .info { color: var(--brand); }
}
</style>
