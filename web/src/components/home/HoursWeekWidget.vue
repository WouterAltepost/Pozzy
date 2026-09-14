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
    <h2>Hours this week <RouterLink :to="{ name: 'hours' }" class="muted small">{{ minutesToHours(summary.total_minutes) }} total</RouterLink></h2>
    <div v-for="row in summary.areas.filter((r) => r.area_id || r.minutes)" :key="row.area" class="row">
      <span class="label"><span class="dot" :style="{ background: row.color }"></span>{{ row.area }}</span>
      <div class="bar"><div class="fill" :class="{ full: pct(row) >= 100 }" :style="{ width: (pct(row) ?? (row.minutes ? 100 : 0)) + '%' }"></div></div>
      <span class="num">{{ minutesToHours(row.minutes) }}<span v-if="row.target_minutes" class="muted"> / {{ minutesToHours(row.target_minutes) }}</span></span>
    </div>
  </section>
</template>

<style scoped>
h2 { font-size: 1rem; margin: 0 0 0.5rem; display: flex; justify-content: space-between; align-items: baseline; }
.small { font-size: 0.78rem; font-weight: normal; }
.row { display: grid; grid-template-columns: 90px 1fr auto; gap: 0.5rem; align-items: center; font-size: 0.85rem; padding: 0.15rem 0; }
.label { display: flex; align-items: center; gap: 0.35rem; }
.dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.bar { height: 7px; background: #e5e7eb; border-radius: 4px; overflow: hidden; }
.fill { height: 100%; background: #2563eb; }
.fill.full { background: #059669; }
.num { font-variant-numeric: tabular-nums; white-space: nowrap; }
</style>
