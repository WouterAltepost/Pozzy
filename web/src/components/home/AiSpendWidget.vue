<script setup>
import { computed, onMounted, ref } from 'vue'
import { getSpend } from '../../api/ai'

const data = ref(null)
const failed = ref(false)
const open = ref(false)

const usd = (v) => '$' + Number(v || 0).toFixed(v >= 1 ? 2 : 3)
const budgetPct = computed(() => (data.value?.budget_usd ? Math.min(100, Math.round((data.value.month.cost / data.value.budget_usd) * 100)) : null))
const maxDay = computed(() => Math.max(0.0001, ...(data.value?.last_7_days || []).map((d) => d.cost)))

async function load() {
  try {
    data.value = await getSpend()
    failed.value = false
  } catch {
    failed.value = true
  }
}

onMounted(load)
</script>

<template>
  <section v-if="!failed && data" class="card widget">
    <h2>
      AI spend
      <span class="muted small">{{ usd(data.month.cost) }} this month<template v-if="data.budget_usd"> of {{ usd(data.budget_usd) }}</template> · {{ usd(data.today_cost) }} today</span>
    </h2>
    <div v-if="budgetPct !== null" class="bar"><div class="fill" :class="{ warn: budgetPct >= 80 }" :style="{ width: budgetPct + '%' }"></div></div>
    <div class="days">
      <div v-for="d in data.last_7_days" :key="d.date" class="day" :title="d.date + ': ' + usd(d.cost) + ', ' + d.calls + ' calls'">
        <div class="col" :style="{ height: Math.max(2, Math.round((d.cost / maxDay) * 28)) + 'px' }"></div>
        <span class="muted tiny">{{ d.date.slice(8) }}</span>
      </div>
    </div>
    <ul class="features">
      <li v-for="f in data.month.by_feature.slice(0, 5)" :key="f.feature">
        <span>{{ f.feature }}</span>
        <span class="muted small">{{ f.calls }} calls<template v-if="f.failed">, {{ f.failed }} failed</template></span>
        <span>{{ usd(f.cost) }}</span>
      </li>
      <li v-if="!data.month.by_feature.length" class="muted">No AI calls this month.</li>
    </ul>
    <button v-if="data.recent.length" type="button" class="link" @click="open = !open">{{ open ? 'Hide' : 'Show' }} recent calls</button>
    <ul v-if="open" class="recent">
      <li v-for="r in data.recent" :key="r.id" :class="{ bad: !r.ok }">
        <span>{{ r.feature }}</span><span class="muted small">{{ r.model }} · {{ r.input_tokens }}/{{ r.output_tokens }} tok</span><span>{{ usd(r.cost) }}</span>
        <div v-if="r.error" class="muted tiny err">{{ r.error }}</div>
      </li>
    </ul>
  </section>
</template>

<style scoped>
h2 { font-size: 1rem; margin: 0 0 0.5rem; display: flex; justify-content: space-between; align-items: baseline; gap: 0.5rem; }
.small { font-size: 0.78rem; font-weight: normal; }
.tiny { font-size: 0.65rem; }
.bar { height: 6px; background: #f3f4f6; border-radius: 3px; margin-bottom: 0.5rem; overflow: hidden; }
.fill { height: 100%; background: #2563eb; }
.fill.warn { background: #b91c1c; }
.days { display: flex; gap: 0.4rem; align-items: flex-end; margin-bottom: 0.5rem; }
.day { display: flex; flex-direction: column; align-items: center; gap: 0.15rem; flex: 1; }
.col { width: 100%; max-width: 28px; background: #93c5fd; border-radius: 2px 2px 0 0; }
ul { list-style: none; padding: 0; margin: 0; }
.features li, .recent li { display: grid; grid-template-columns: 1fr auto auto; gap: 0.5rem; font-size: 0.88rem; padding: 0.15rem 0; }
.recent li.bad { color: #b91c1c; }
.err { grid-column: 1 / -1; }
.link { border: none; background: none; padding: 0; color: #2563eb; font-size: 0.78rem; cursor: pointer; margin-top: 0.3rem; }
</style>
