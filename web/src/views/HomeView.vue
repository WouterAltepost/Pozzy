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

const today = new Date().toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' })
</script>

<template>
  <div class="home">
    <h1>{{ today }}</h1>
    <div class="widgets">
      <ThreeDosWidget />
      <TodayEventsWidget />
      <TopEmailsWidget />
      <TasksDueWidget />
      <TrackerRowWidget />
      <HoursWeekWidget />
      <WeeklyGoalsWidget />
      <DeadlinesWidget />
      <BriefingWidget />
      <AiSpendWidget />
    </div>
  </div>
</template>

<style scoped>
h1 { font-size: 1.3rem; margin: 0 0 1rem; }
.widgets { display: grid; grid-template-columns: 1fr; gap: 1rem; align-items: start; }
@media (min-width: 900px) { .widgets { grid-template-columns: 1fr 1fr; } }
.widgets :deep(.card) { margin-bottom: 0; }
</style>
