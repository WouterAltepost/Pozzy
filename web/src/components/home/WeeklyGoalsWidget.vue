<script setup>
import { onMounted, ref } from 'vue'
import { addGoalProgress, listGoals, updateGoal } from '../../api/goals'
import AreaDot from '../shared/AreaDot.vue'

const data = ref(null)
const failed = ref(false)

async function load() {
  try {
    data.value = await listGoals()
    failed.value = false
  } catch {
    failed.value = true
  }
}

function replace(goal) {
  const i = data.value.goals.findIndex((g) => g.id === goal.id)
  if (i !== -1) data.value.goals[i] = goal
}

async function toggle(g) {
  try {
    replace(await updateGoal(g.id, { done: !g.done }))
  } catch {
    load()
  }
}

async function bump(g) {
  try {
    replace(await addGoalProgress(g.id, 1))
  } catch {
    load()
  }
}

onMounted(load)
</script>

<template>
  <section v-if="!failed && data" class="card widget">
    <h2>Weekly goals <RouterLink :to="{ name: 'goals' }" class="muted small">{{ data.goals.filter((g) => g.done).length }} / {{ data.goals.length }} done</RouterLink></h2>
    <ul>
      <li v-for="g in data.goals" :key="g.id" :class="{ done: g.done }">
        <input type="checkbox" :checked="g.done" @change="toggle(g)" />
        <span class="title">{{ g.title }}</span>
        <AreaDot :area-id="g.area_id" />
        <template v-if="g.target_value">
          <span class="muted small">{{ g.current_value }}/{{ g.target_value }}</span>
          <button type="button" class="plus" @click="bump(g)">+1</button>
        </template>
      </li>
      <li v-if="!data.goals.length" class="muted">No goals this week yet.</li>
    </ul>
  </section>
</template>

<style scoped>
h2 { font-size: 1rem; margin: 0 0 0.5rem; display: flex; justify-content: space-between; align-items: baseline; }
.small { font-size: 0.78rem; font-weight: normal; }
ul { list-style: none; padding: 0; margin: 0; }
li { display: flex; align-items: center; gap: 0.5rem; padding: 0.25rem 0; font-size: 0.9rem; }
li.done .title { text-decoration: line-through; color: #9ca3af; }
.title { flex: 1; }
.plus { padding: 0 0.4rem; font-size: 0.75rem; }
</style>
