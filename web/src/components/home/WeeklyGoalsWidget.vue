<script setup>
import { useLoadTask } from '../../composables/useReady'
import { useWidgetLink } from '../../composables/useWidgetLink'
import { onMounted, ref } from 'vue'
import { PhTarget } from '@phosphor-icons/vue'
import { addGoalProgress, listGoals, updateGoal } from '../../api/goals'
import AreaDot from '../shared/AreaDot.vue'
import UiButton from '../ui/UiButton.vue'
import UiEmpty from '../ui/UiEmpty.vue'
import ShowAll from './ShowAll.vue'
import { tick } from '../../lib/haptics'
import { useMediaQuery } from '../../composables/useMediaQuery'

const settle = useLoadTask()

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
  tick()
  try {
    replace(await updateGoal(g.id, { done: !g.done }))
  } catch {
    load()
  }
}

async function bump(g) {
  tick()
  try {
    replace(await addGoalProgress(g.id, 1))
  } catch {
    load()
  }
}

onMounted(() => load().finally(settle))
const link = useWidgetLink('goals')
const phone = useMediaQuery('(max-width: 1023px)')
// Pull to refresh on the Overview reloads every widget through this.
defineExpose({ load })
</script>

<template>
  <section v-if="!failed && data" class="card widget clickable" tabindex="0" role="link" :aria-label="'Open goals'" @click="link.onClick" @keydown="link.onKey">
    <div class="card-head">
      <h2>Weekly goals</h2>
      <span class="meta"><ShowAll to="goals" class="num">{{ data.goals.filter((g) => g.done).length }} of {{ data.goals.length }} done</ShowAll></span>
    </div>
    <p v-if="phone && data.goals.length" class="headline num">{{ data.goals.filter((g) => g.done).length }}<span class="unit"> of {{ data.goals.length }} done</span></p>
    <ul v-if="data.goals.length">
      <li v-for="g in data.goals" :key="g.id" class="list-row" :class="{ done: g.done }">
        <input type="checkbox" :checked="g.done" :aria-label="g.title" @change="toggle(g)" />
        <span class="title truncate">{{ g.title }}</span>
        <AreaDot :area-id="g.area_id" />
        <template v-if="g.target_value">
          <span class="muted small num">{{ g.current_value }}/{{ g.target_value }}</span>
          <UiButton size="sm" variant="ghost" :aria-label="'Add one to ' + g.title" @click="bump(g)">+1</UiButton>
        </template>
      </li>
    </ul>
    <UiEmpty v-else compact title="No goals this week" hint="Set a few in Goals, or let the weekly review draft them.">
      <template #icon><PhTarget /></template>
    </UiEmpty>
  </section>
</template>

<style scoped>
.title { flex: 1; min-width: 0; }
</style>
