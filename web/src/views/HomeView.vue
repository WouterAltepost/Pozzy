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
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import { useLoadGateHost } from '../composables/useReady'

const ready = useLoadGateHost()

const now = new Date()
const weekday = now.toLocaleDateString('en-GB', { weekday: 'long' })
const date = now.toLocaleDateString('en-GB', { day: 'numeric', month: 'long' })
</script>

<template>
  <div class="home">
    <h1 class="display"><span class="weekday">{{ weekday }}</span> <span class="date">{{ date }}</span></h1>
    <UiLoadGate :ready="ready" label="Loading your day">
    <div class="widgets">
      <ThreeDosWidget class="w-dos" />
      <TodayEventsWidget class="w-today" />
      <TopEmailsWidget class="w-mail" />
      <TasksDueWidget class="w-due" />
      <TrackerRowWidget class="span w-trackers" />
      <HoursWeekWidget class="w-hours" />
      <WeeklyGoalsWidget class="w-goals" />
      <DeadlinesWidget class="w-deadlines" />
      <BriefingWidget class="span w-briefing" />
      <AiSpendWidget class="w-spend" />
    </div>
    </UiLoadGate>
  </div>
</template>

<style scoped>
.display { font-size: var(--fs-title); letter-spacing: 0; line-height: 1.2; margin: 0 0 var(--sp-5); font-weight: 700; }
.display .date { color: var(--ink-3); font-weight: 500; }
.widgets { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--sp-4); align-items: start; }
@media (min-width: 900px) {
  .widgets { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: var(--sp-5); }
  .widgets > .span { grid-column: 1 / -1; }
}
.widgets :deep(.card) { margin-bottom: 0; }
/* Phone order (design: Pozzy Phone, Home): briefing third, after Today. */
@media (max-width: 899px) {
  .widgets > .w-dos { order: 1; } .widgets > .w-today { order: 2; } .widgets > .w-briefing { order: 3; } .widgets > .w-due { order: 4; }
  .widgets > .w-trackers { order: 5; } .widgets > .w-hours { order: 6; } .widgets > .w-mail { order: 7; } .widgets > .w-goals { order: 8; }
  .widgets > .w-deadlines { order: 9; } .widgets > .w-spend { order: 10; }
  .display { margin-bottom: var(--sp-4); display: flex; flex-direction: column; gap: 2px; }
  .display .date { font-size: var(--fs-2xl); font-weight: 600; }
}
</style>
