<script setup>
import { onMounted, ref } from 'vue'
import { upcoming } from '../../api/study'
import { daysUntil, formatDateTime, formatDay } from '../../lib/dates'
import UiBadge from '../ui/UiBadge.vue'

const data = ref(null)
const failed = ref(false)

onMounted(async () => {
  try {
    data.value = await upcoming(14)
  } catch {
    failed.value = true
  }
})

function tone(day) {
  const d = daysUntil(day)
  if (d < 0) return 'danger'
  if (d <= 3) return 'warn'
  return 'neutral'
}
</script>

<template>
  <section v-if="!failed && data && (data.deadlines.length || data.application_steps.length)" class="card widget">
    <div class="card-head">
      <h2>Next two weeks</h2>
      <span class="meta"><RouterLink :to="{ name: 'study' }">Study</RouterLink></span>
    </div>
    <ul>
      <li v-for="d in data.deadlines" :key="d.id" class="list-row">
        <UiBadge tone="info">{{ d.course_code || d.course_name }}</UiBadge>
        <span class="title truncate">{{ d.title }}</span>
        <UiBadge :tone="tone(d.due_at.slice(0, 10))" class="num">{{ formatDateTime(d.due_at) }}</UiBadge>
      </li>
      <li v-for="a in data.application_steps" :key="a.id" class="list-row">
        <UiBadge tone="warn">{{ a.status }}</UiBadge>
        <span class="title truncate">{{ a.company }}: {{ a.next_step || 'next step' }}</span>
        <UiBadge :tone="tone(a.next_step_date)" class="num">{{ formatDay(a.next_step_date) }}</UiBadge>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.title { flex: 1; min-width: 0; }
</style>
