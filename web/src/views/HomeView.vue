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
import PullToRefresh from '../components/ios/PullToRefresh.vue'
import UiLoadGate from '../components/ui/UiLoadGate.vue'
import { useMediaQuery } from '../composables/useMediaQuery'
import { useLoadGateHost } from '../composables/useReady'

const ready = useLoadGateHost()
// Phone: the Fitness summary. The date sits small above the large title, every widget is a
// plate with its headline and a Show all link, and a pull reloads every widget in place.
const phone = useMediaQuery('(max-width: 1023px)')
const widgets = new Set()
const keep = (el) => el && widgets.add(el)
async function refresh() {
  await Promise.all([...widgets].filter((w) => w.load).map((w) => w.load().catch(() => {})))
}

const now = new Date()
const weekday = now.toLocaleDateString('en-GB', { weekday: 'long' })
const date = now.toLocaleDateString('en-GB', { day: 'numeric', month: 'long' })
// ISO week number for the eyebrow.
const jan4 = new Date(now.getFullYear(), 0, 4)
const week = Math.ceil(((now - jan4) / 86400000 + ((jan4.getDay() + 6) % 7) + 1) / 7)
</script>

<template>
  <PullToRefresh :action="refresh">
  <div class="home">
    <div v-if="phone" class="display">
      <span class="dateline">{{ weekday }} {{ date }}, week {{ week }}</span>
      <h1>Overview</h1>
    </div>
    <div v-else class="display">
      <span class="eyebrow">{{ weekday }} · Week {{ week }}</span>
      <h1>{{ date }}</h1>
    </div>
    <UiLoadGate :ready="ready" label="Loading your day">
    <div class="widgets">
      <ThreeDosWidget :ref="keep" class="w-dos" />
      <TodayEventsWidget :ref="keep" class="w-today" />
      <TopEmailsWidget :ref="keep" class="w-mail" />
      <TasksDueWidget :ref="keep" class="w-due" />
      <TrackerRowWidget :ref="keep" class="span w-trackers" />
      <HoursWeekWidget :ref="keep" class="w-hours" />
      <WeeklyGoalsWidget :ref="keep" class="w-goals" />
      <DeadlinesWidget :ref="keep" class="w-deadlines" />
      <BriefingWidget :ref="keep" class="span w-briefing" />
      <AiSpendWidget :ref="keep" class="w-spend" />
    </div>
    </UiLoadGate>
  </div>
  </PullToRefresh>
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

/* iOS layer: summary plates, as in Health and Fitness. The headline sits in the plate with the
   Show all link on its right, rows are 44pt with separators from the text, no lift on press. */
@media (max-width: 1023px) {
  .display { gap: 0; margin: 4px 0 var(--sp-5); }
  .dateline { font-size: 0.8125rem; font-weight: 600; text-transform: uppercase; color: var(--ink-3); }
  .widgets { gap: var(--sp-4); }
  .widgets > * { animation: none; }
  .widgets :deep(.card.widget) { padding: 12px 16px 6px; }
  .widgets :deep(.card-head) { flex-wrap: nowrap; align-items: center; min-height: 32px; margin-bottom: 2px; }
  .widgets :deep(.card-head h2) { font-size: 1.0625rem; font-weight: 600; }
  .widgets :deep(.card-head .meta) { flex: none; }
  .widgets :deep(.headline) { margin: 0 0 6px; font-size: 1.75rem; font-weight: 700; line-height: 1.15; color: var(--ink); }
  .widgets :deep(.headline .unit) { font-size: 0.9375rem; font-weight: 400; color: var(--ink-3); }
  .widgets :deep(.list-row) { gap: 12px; padding: 8px 0; font-size: 1.0625rem; }
  .widgets :deep(.list-row + .list-row::before) { left: var(--sep, 0); right: -16px; background: var(--line-2); }
  .widgets :deep(.list-row:has(> input[type='checkbox']:first-child)) { --sep: 34px; }
  /* Status capsules read as coloured text in a row, the way Reminders shows a due date. */
  .widgets :deep(.list-row .badge) { height: auto; padding: 0; background: none; font-size: 0.9375rem; font-weight: 400; letter-spacing: 0; }
  .widgets :deep(.list-row .badge.tone-neutral) { color: var(--ink-3); }
  .widgets :deep(.empty.compact) { padding: 10px 0 12px; }
  .widgets :deep(.empty.compact .title) { font-size: 1.0625rem; color: var(--ink); font-weight: 400; }
  .widgets :deep(.empty.compact .hint) { font-size: 0.9375rem; }
}
</style>
