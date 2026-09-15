<script setup>
import { onMounted, ref } from 'vue'
import { hoursWeek } from '../../api/hours'
import { minutesToHours } from '../../lib/dates'

const summary = ref(null)
const failed = ref(false)

onMounted(async () => {
  try {
    summary.value = await hoursWeek()
  } catch {
    failed.value = true
  }
})

function pct(row) {
  return row.target_minutes ? Math.min(100, Math.round((row.minutes / row.target_minutes) * 100)) : null
}
</script>

<template>
  <section v-if="!failed && summary" class="card widget">
    <div class="card-head">
      <h2>Hours this week</h2>
      <span class="meta"><RouterLink :to="{ name: 'hours' }" class="num">{{ minutesToHours(summary.total_minutes) }} total</RouterLink></span>
    </div>
    <div v-for="row in summary.areas.filter((r) => r.area_id || r.minutes)" :key="row.area" class="hrow">
      <span class="label"><span class="dot" :style="{ background: row.color }" aria-hidden="true"></span>{{ row.area }}</span>
      <div class="bar"><div class="fill" :class="{ full: pct(row) >= 100 }" :style="{ width: (pct(row) ?? (row.minutes ? 100 : 0)) + '%' }"></div></div>
      <span class="num small val">{{ minutesToHours(row.minutes) }}<span v-if="row.target_minutes" class="muted"> / {{ minutesToHours(row.target_minutes) }}</span></span>
    </div>
  </section>
</template>

<style scoped>
.hrow { display: grid; grid-template-columns: 92px 1fr auto; gap: var(--sp-3); align-items: center; font-size: var(--fs-md); padding: 5px 0; }
.label { display: flex; align-items: center; gap: 8px; color: var(--ink-2); }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; flex: none; }
.val { white-space: nowrap; color: var(--ink); }
</style>
