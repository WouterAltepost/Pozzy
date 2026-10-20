<script setup>
// A task in the phone list, with the iOS gestures around TaskCard: swipe right to complete it
// (or reopen it), swipe left to edit or delete, long press for the context menu. The list owns
// the writes; this only says what was asked.
import { computed } from 'vue'
import { PhArrowCounterClockwise, PhCalendarPlus, PhCheck, PhCheckCircle, PhPencilSimple, PhTrash } from '@phosphor-icons/vue'
import SwipeRow from '../ios/SwipeRow.vue'
import TaskCard from './TaskCard.vue'
import { useContextMenu } from '../../composables/useContextMenu'
import { tick } from '../../lib/haptics'

const props = defineProps({ task: { type: Object, required: true }, selected: { type: Boolean, default: false } })
const emit = defineEmits(['select', 'complete', 'remove', 'slots'])
const menu = useContextMenu()

const done = computed(() => props.task.status === 'done')
const leading = computed(() => [
  done.value
    ? { label: 'Reopen', icon: PhArrowCounterClockwise, color: '#8E8E93', action: () => emit('complete', props.task) }
    : { label: 'Done', icon: PhCheck, color: 'var(--ok)', action: () => emit('complete', props.task) },
])
// The outermost action runs on a full swipe, so Delete sits at the edge; it still asks first.
const trailing = computed(() => [
  { label: 'Delete', icon: PhTrash, color: 'var(--danger)', action: () => emit('remove', props.task) },
  { label: 'Edit', icon: PhPencilSimple, color: 'var(--warn)', action: () => emit('select', props.task) },
])

// The checkbox commits at once, so it ticks here; a swipe action ticks in SwipeRow.
function check() {
  tick()
  emit('complete', props.task)
}

function openMenu(el) {
  menu.open(el, [
    { label: done.value ? 'Mark not done' : 'Mark done', icon: done.value ? PhArrowCounterClockwise : PhCheckCircle, action: () => emit('complete', props.task) },
    { label: 'Edit', icon: PhPencilSimple, action: () => emit('select', props.task) },
    done.value ? null : { label: 'Suggest a slot', icon: PhCalendarPlus, action: () => emit('slots', props.task) },
    { label: 'Delete', icon: PhTrash, danger: true, action: () => emit('remove', props.task) },
  ])
}
</script>

<template>
  <SwipeRow :leading="leading" :trailing="trailing" class="task-item">
    <TaskCard :task="task" :selected="selected" :draggable="false" @select="emit('select', $event)" @complete="check" @menu="openMenu" />
  </SwipeRow>
</template>
