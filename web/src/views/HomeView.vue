<script setup>
// Assembled from docs/WIDGETS.md. Each widget fetches its own data and renders nothing on failure.
import AiSpendWidget from '../components/home/AiSpendWidget.vue'
import BriefingWidget from '../components/home/BriefingWidget.vue'
import DeadlinesWidget from '../components/home/DeadlinesWidget.vue'
import HoursWeekWidget from '../components/home/HoursWeekWidget.vue'
import TasksDueWidget from '../components/home/TasksDueWidget.vue'
import ThreeDosWidget from '../components/home/ThreeDosWidget.vue'
import TodayEventsWidget from '../components/home/TodayEventsWidget.vue'
import TopEmailsWidget from '../components/home/TopEmailsWidget.vue'
import TrackerRowWidget from '../components/home/TrackerRowWidget.vue'
import WeeklyGoalsWidget from '../components/home/WeeklyGoalsWidget.vue'

const now = new Date()
const weekday = now.toLocaleDateString('en-GB', { weekday: 'long' })
const date = now.toLocaleDateString('en-GB', { day: 'numeric', month: 'long' })
</script>

<template>
  <div class="home">
    <h1 class="display"><span class="weekday">{{ weekday }}</span> <span class="date">{{ date }}</span></h1>
    <div class="widgets">
      <ThreeDosWidget />
      <TodayEventsWidget />
      <TopEmailsWidget />
      <TasksDueWidget />
      <TrackerRowWidget class="span" />
      <HoursWeekWidget />
      <WeeklyGoalsWidget />
      <DeadlinesWidget />
      <BriefingWidget class="span" />
      <AiSpendWidget />
    </div>
  </div>
</template>

<style scoped>
.display { font-size: var(--fs-3xl); letter-spacing: -0.02em; line-height: 1.15; margin: 0 0 var(--sp-5); font-weight: 600; }
.display .date { color: var(--ink-3); font-weight: 500; }
.widgets { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--sp-4); align-items: start; }
@media (min-width: 900px) {
  .widgets { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: var(--sp-5); }
  .widgets > .span { grid-column: 1 / -1; }
}
.widgets :deep(.card) { margin-bottom: 0; }
</style>
