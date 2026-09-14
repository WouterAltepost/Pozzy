<script setup>
import { computed, onMounted, ref } from 'vue'
import { tickTracker, trackerWeek } from '../../api/trackers'
import { today } from '../../lib/dates'

const week = ref(null)
const failed = ref(false)

const quick = computed(() => (week.value?.trackers || []).filter((t) => t.type === 'daily_bool' || t.type === 'weekly_count'))

function todayCell(t) {
  return t.days.find((d) => d.date === today())
}

async function load() {
  try {
    week.value = await trackerWeek()
    failed.value = false
  } catch {
    failed.value = true
  }
}

async function tick(t) {
  try {
    await tickTracker(t.id, today())
    await load()
  } catch {
    failed.value = true
  }
}

onMounted(load)
</script>

<template>
  <section v-if="!failed && week && quick.length" class="card widget">
    <h2>Trackers today <RouterLink :to="{ name: 'trackers' }" class="muted small">tracking</RouterLink></h2>
    <div class="row">
      <button
        v-for="t in quick"
        :key="t.id"
        type="button"
        class="chip"
        :class="{ met: todayCell(t)?.met, some: todayCell(t)?.value && !todayCell(t)?.met }"
        :title="t.type === 'weekly_count' ? `${t.week_total} of ${t.target_value || '?'} this week` : `streak ${t.streak}`"
        @click="tick(t)"
      >
        <span class="dot" :style="{ background: t.area_color || '#9ca3af' }"></span>
        {{ t.name }}
        <span v-if="t.type === 'weekly_count'" class="count">{{ t.week_total }}<span v-if="t.target_value">/{{ t.target_value }}</span></span>
        <span v-else-if="todayCell(t)?.met">✓</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
h2 { font-size: 1rem; margin: 0 0 0.5rem; display: flex; justify-content: space-between; align-items: baseline; }
.small { font-size: 0.78rem; font-weight: normal; }
.row { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.chip { display: inline-flex; align-items: center; gap: 0.35rem; border-radius: 999px; padding: 0.3rem 0.7rem; font-size: 0.85rem; }
.chip.met { background: #d1fae5; border-color: #6ee7b7; color: #065f46; }
.chip.some { background: #fef3c7; border-color: #fcd34d; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.count { font-variant-numeric: tabular-nums; color: #6b7280; font-size: 0.78rem; }
</style>
