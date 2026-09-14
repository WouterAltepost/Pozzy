<script setup>
import { onMounted, ref } from 'vue'
import { completeTask, listTasks } from '../../api/tasks'
import { daysUntil, formatDay } from '../../lib/dates'
import AreaDot from '../shared/AreaDot.vue'

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
  try {
    await completeTask(t.id)
    tasks.value = tasks.value.filter((x) => x.id !== t.id)
  } catch {
    load()
  }
}

onMounted(load)
</script>

<template>
  <section v-if="!failed && tasks" class="card widget">
    <h2>Due today or overdue <RouterLink :to="{ name: 'tasks' }" class="muted small">all tasks</RouterLink></h2>
    <ul>
      <li v-for="t in tasks" :key="t.id">
        <input type="checkbox" @change="complete(t)" />
        <span class="title">{{ t.title }}</span>
        <AreaDot :area-id="t.area_id" />
        <span :class="daysUntil(t.due_date) < 0 ? 'overdue' : 'today'">{{ daysUntil(t.due_date) < 0 ? 'overdue ' : '' }}{{ formatDay(t.due_date) }}</span>
      </li>
      <li v-if="!tasks.length" class="muted">Nothing due. Nice.</li>
    </ul>
  </section>
</template>

<style scoped>
h2 { font-size: 1rem; margin: 0 0 0.5rem; display: flex; justify-content: space-between; align-items: baseline; }
.small { font-size: 0.78rem; font-weight: normal; }
ul { list-style: none; padding: 0; margin: 0; }
li { display: flex; align-items: center; gap: 0.5rem; padding: 0.25rem 0; font-size: 0.9rem; }
.title { flex: 1; }
.overdue { color: #b91c1c; font-size: 0.8rem; font-weight: 600; }
.today { color: #d97706; font-size: 0.8rem; }
</style>
