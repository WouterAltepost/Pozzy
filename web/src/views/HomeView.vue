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
// ISO week number for the eyebrow.
const jan4 = new Date(now.getFullYear(), 0, 4)
const week = Math.ceil(((now - jan4) / 86400000 + ((jan4.getDay() + 6) % 7) + 1) / 7)
</script>

<template>
  <div class="home">
    <div class="display">
      <span class="eyebrow">{{ weekday }} · Week {{ week }}</span>
      <h1>{{ date }}</h1>
    </div>
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
.display { display: flex; flex-direction: column; gap: 6px; margin: 0 0 var(--sp-8); }
.widgets > * { animation: rise 600ms var(--ease-spring) both; }
.widgets > :nth-child(2) { animation-delay: 40ms; } .widgets > :nth-child(3) { animation-delay: 80ms; } .widgets > :nth-child(4) { animation-delay: 120ms; }
.widgets > :nth-child(5) { animation-delay: 160ms; } .widgets > :nth-child(6) { animation-delay: 200ms; } .widgets > :nth-child(7) { animation-delay: 240ms; }
.widgets > :nth-child(8) { animation-delay: 280ms; } .widgets > :nth-child(9) { animation-delay: 320ms; } .widgets > :nth-child(10) { animation-delay: 360ms; }
@keyframes rise { from { opacity: 0; transform: translateY(12px); } }
@media (prefers-reduced-motion: reduce) { .widgets > * { animation: none; } }
.widgets { display: grid; grid-template-columns: minmax(0, 1fr); gap: var(--sp-5); align-items: start; }
@media (min-width: 900px) {
  .widgets { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: var(--sp-6); }
  .widgets > .span { grid-column: 1 / -1; }
}
.widgets :deep(.card) { margin-bottom: 0; }
/* Phone order (design: Pozzy Phone, Home): briefing third, after Today. */
@media (max-width: 899px) {
  .widgets > .w-dos { order: 1; } .widgets > .w-today { order: 2; } .widgets > .w-briefing { order: 3; } .widgets > .w-due { order: 4; }
  .widgets > .w-trackers { order: 5; } .widgets > .w-hours { order: 6; } .widgets > .w-mail { order: 7; } .widgets > .w-goals { order: 8; }
  .widgets > .w-deadlines { order: 9; } .widgets > .w-spend { order: 10; }
  .display { margin-bottom: var(--sp-5); }
}
</style>
