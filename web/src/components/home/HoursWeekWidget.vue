<script setup>
import { useLoadTask } from '../../composables/useReady'
import { useWidgetLink } from '../../composables/useWidgetLink'
import { onMounted, ref } from 'vue'
import { hoursSuggestions, hoursWeek } from '../../api/hours'
import { minutesToHours } from '../../lib/dates'

const settle = useLoadTask()

const summary = ref(null)
const suggestions = ref(null)
const failed = ref(false)

onMounted(async () => {
  try {
    summary.value = await hoursWeek()
  } catch {
    failed.value = true
  } finally {
    settle()
  }
  // Optional extra: the widget renders without it.
  try {
    suggestions.value = await hoursSuggestions()
  } catch {
    suggestions.value = null
  }
})

function pct(row) {
  return row.target_minutes ? Math.min(100, Math.round((row.minutes / row.target_minutes) * 100)) : null
}
const link = useWidgetLink('hours')
</script>

<template>
  <section v-if="!failed && summary" class="card widget clickable" tabindex="0" role="link" :aria-label="'Open hours'" @click="link.onClick" @keydown="link.onKey">
    <div class="card-head">
      <h2>Hours this week</h2>
      <span class="meta"><RouterLink :to="{ name: 'hours' }" class="num">{{ minutesToHours(summary.total_minutes) }} total</RouterLink></span>
    </div>
    <div v-for="row in summary.areas.filter((r) => r.area_id || r.minutes)" :key="row.area" class="hrow">
      <span class="label"><span class="dot" :style="{ background: row.color }" aria-hidden="true"></span>{{ row.area }}</span>
      <div class="bar"><div class="fill" :class="{ full: pct(row) >= 100 }" :style="{ width: (pct(row) ?? (row.minutes ? 100 : 0)) + '%' }"></div></div>
      <span class="num small val">{{ minutesToHours(row.minutes) }}<span v-if="row.target_minutes" class="muted"> / {{ minutesToHours(row.target_minutes) }}</span></span>
    </div>
    <RouterLink v-if="suggestions?.items.length" :to="{ name: 'hours' }" class="pending small" @click.stop>
      {{ suggestions.items.length }} {{ suggestions.items.length === 1 ? 'entry' : 'entries' }} to confirm from your agenda, {{ minutesToHours(suggestions.total_minutes) }}
    </RouterLink>
  </section>
</template>

<style scoped>
.hrow { display: grid; grid-template-columns: 92px 1fr auto; gap: var(--sp-3); align-items: center; font-size: var(--fs-md); padding: 5px 0; }
.label { display: flex; align-items: center; gap: 8px; color: var(--ink-2); }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; flex: none; }
.val { white-space: nowrap; color: var(--ink); }
.pending { display: block; margin-top: var(--sp-2); padding: 6px 10px; border-radius: var(--r-sm); background: var(--brand-soft); color: var(--brand); font-weight: 500; text-decoration: none; }
</style>
