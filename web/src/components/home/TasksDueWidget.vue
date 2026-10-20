<script setup>
import { useLoadTask } from '../../composables/useReady'
import { useWidgetLink } from '../../composables/useWidgetLink'
import { onMounted, ref } from 'vue'
import { PhCheckSquare } from '@phosphor-icons/vue'
import { completeTask, listTasks } from '../../api/tasks'
import { daysUntil, formatDay } from '../../lib/dates'
import AreaDot from '../shared/AreaDot.vue'
import UiBadge from '../ui/UiBadge.vue'
import UiEmpty from '../ui/UiEmpty.vue'
import ShowAll from './ShowAll.vue'
import { tick } from '../../lib/haptics'

const settle = useLoadTask()

const tasks = ref(null)
const failed = ref(false)

async function load() {
  try {
    tasks.value = await listTasks({ due: 'today_or_overdue' })
    failed.value = false
  } catch {
    failed.value = true
  }
}

async function complete(t) {
  tick()
  try {
    await completeTask(t.id)
    tasks.value = tasks.value.filter((x) => x.id !== t.id)
  } catch {
    load()
  }
}

onMounted(() => load().finally(settle))
const link = useWidgetLink('tasks')
// Pull to refresh on the Overview reloads every widget through this.
defineExpose({ load })
</script>

<template>
  <section v-if="!failed && tasks" class="card widget clickable" tabindex="0" role="link" :aria-label="'Open tasks'" @click="link.onClick" @keydown="link.onKey">
    <div class="card-head">
      <h2>Due today or overdue</h2>
      <span class="meta"><ShowAll to="tasks">All tasks</ShowAll></span>
    </div>
    <ul v-if="tasks.length">
      <li v-for="t in tasks" :key="t.id" class="list-row">
        <input type="checkbox" :aria-label="'Complete ' + t.title" @change="complete(t)" />
        <span class="title truncate">{{ t.title }}</span>
        <AreaDot :area-id="t.area_id" />
        <UiBadge :tone="daysUntil(t.due_date) < 0 ? 'danger' : 'warn'" class="num">{{ daysUntil(t.due_date) < 0 ? 'overdue ' : '' }}{{ formatDay(t.due_date) }}</UiBadge>
      </li>
    </ul>
    <UiEmpty v-else compact title="Nothing due" hint="No tasks due today and nothing overdue.">
      <template #icon><PhCheckSquare /></template>
    </UiEmpty>
  </section>
</template>

<style scoped>
.title { flex: 1; min-width: 0; }
</style>
