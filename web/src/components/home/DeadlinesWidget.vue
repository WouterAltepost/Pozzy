<script setup>
import { onMounted, ref } from 'vue'
import { upcoming } from '../../api/study'
import { daysUntil, formatDateTime, formatDay } from '../../lib/dates'

const data = ref(null)
const failed = ref(false)

onMounted(async () => {
  try {
    data.value = await upcoming(14)
  } catch {
    failed.value = true
  }
})

function urgency(day) {
  const d = daysUntil(day)
  if (d < 0) return 'overdue'
  if (d <= 3) return 'soon'
  return ''
}
</script>

<template>
  <section v-if="!failed && data && (data.deadlines.length || data.application_steps.length)" class="card widget">
    <h2>Next two weeks <RouterLink :to="{ name: 'study' }" class="muted small">study</RouterLink></h2>
    <ul>
      <li v-for="d in data.deadlines" :key="d.id">
        <span class="course">{{ d.course_code || d.course_name }}</span>
        <span class="title">{{ d.title }}</span>
        <span :class="urgency(d.due_at.slice(0, 10))">{{ formatDateTime(d.due_at) }}</span>
      </li>
      <li v-for="a in data.application_steps" :key="a.id">
        <span class="course app">{{ a.status }}</span>
        <span class="title">{{ a.company }}: {{ a.next_step || 'next step' }}</span>
        <span :class="urgency(a.next_step_date)">{{ formatDay(a.next_step_date) }}</span>
      </li>
    </ul>
  </section>
</template>

<style scoped>
h2 { font-size: 1rem; margin: 0 0 0.5rem; display: flex; justify-content: space-between; align-items: baseline; }
.small { font-size: 0.78rem; font-weight: normal; }
ul { list-style: none; padding: 0; margin: 0; }
li { display: flex; align-items: center; gap: 0.5rem; padding: 0.25rem 0; font-size: 0.88rem; }
.course { background: #e0e7ff; color: #3730a3; padding: 0 0.35rem; border-radius: 3px; font-size: 0.75rem; white-space: nowrap; }
.course.app { background: #fef3c7; color: #92400e; text-transform: capitalize; }
.title { flex: 1; }
.overdue { color: #b91c1c; font-weight: 600; font-size: 0.8rem; }
.soon { color: #d97706; font-weight: 600; font-size: 0.8rem; }
</style>
