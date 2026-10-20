<script setup>
// A habit in a list, with the iOS gestures around HabitRow: swipe right to check it off (or
// take it back), swipe left to skip or write a note, long press for the context menu. The list
// owns the writes; this only says what was asked.
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { PhArrowCounterClockwise, PhChartLineUp, PhCheck, PhNotePencil, PhPlus, PhSkipForward } from '@phosphor-icons/vue'
import HabitRow from './HabitRow.vue'
import SwipeRow from '../ios/SwipeRow.vue'
import { useContextMenu } from '../../composables/useContextMenu'
import { cellOf, isBool, isCount, isWeekly } from '../../lib/habits'

const props = defineProps({
  tracker: { type: Object, required: true },
  day: { type: String, required: true },
  today: { type: String, required: true },
})
const emit = defineEmits(['act', 'open', 'skip'])
const router = useRouter()
const menu = useContextMenu()

const cell = computed(() => cellOf(props.tracker, props.day))
const skipped = computed(() => cell.value?.status === 'skipped')
const done = computed(() => (isWeekly(props.tracker) ? Boolean(props.tracker.week_met) : Boolean(cell.value?.met)))
const future = computed(() => props.day > props.today)

// The quick action: a check toggles, a count adds one, a value habit opens its sheet.
const primary = computed(() => {
  if (isBool(props.tracker)) return done.value ? { label: 'Undo', icon: PhArrowCounterClockwise, color: '#8E8E93' } : { label: 'Done', icon: PhCheck, color: 'var(--ok)' }
  if (isCount(props.tracker)) return { label: '+1', icon: PhPlus, color: 'var(--ok)' }
  return { label: 'Log', icon: PhPlus, color: 'var(--ok)' }
})
const leading = computed(() => (future.value ? [] : [{ ...primary.value, action: () => emit('act') }]))
const trailing = computed(() =>
  future.value
    ? []
    : [
        { label: skipped.value ? 'Unskip' : 'Skip', icon: PhSkipForward, color: '#8E8E93', action: () => emit('skip') },
        { label: 'Note', icon: PhNotePencil, color: '#FF9500', action: () => emit('open') },
      ],
)

function openMenu(el) {
  if (future.value) return
  menu.open(el, [
    { label: primary.value.label === '+1' ? 'Add one' : primary.value.label === 'Undo' ? 'Mark not done' : primary.value.label === 'Log' ? 'Log a value' : 'Mark done', icon: primary.value.icon, action: () => emit('act') },
    { label: skipped.value ? 'Unskip' : 'Skip this day', icon: PhSkipForward, action: () => emit('skip') },
    { label: cell.value?.note ? 'Edit note' : 'Add a note', icon: PhNotePencil, action: () => emit('open') },
    { label: 'Stats', icon: PhChartLineUp, action: () => router.push({ name: 'habit', params: { id: props.tracker.id } }) },
  ])
}
</script>

<template>
  <SwipeRow :leading="leading" :trailing="trailing" class="habit-item">
    <HabitRow :tracker="tracker" :day="day" :today="today" @act="emit('act')" @open="emit('open')" @menu="openMenu" />
  </SwipeRow>
</template>
